"""GPX 1.1 schema validation.

This module validates GPX data against the GPX 1.1 schema (``gpx.xsd``) using a
pure-Python, declarative rule table (no XSD engine, no extra dependencies).

Validation operates on the raw XML tree, before and independent of dataclass
parsing. This is essential: most schema violations (unknown elements,
duplicates, ordering) are invisible after parsing, because the dataclass parser
only looks for known fields and silently ignores the rest.

The public entry point is :func:`validate`, which accepts a file path, a string
of GPX content, or a :class:`~gpx.gpx.GPX` instance and returns a
:class:`ValidationResult`.

Example:
    >>> from gpx import validate
    >>> result = validate("track.gpx")
    >>> result.is_valid
    True

"""

from __future__ import annotations

import datetime as dt
import difflib
import re
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path
from typing import Any
from xml.parsers import expat

from .base import GPX_NAMESPACE
from .types import Fix

#: GPX 1.0 namespace (unsupported; only used to give a helpful hint).
GPX_10_NAMESPACE = "http://www.topografix.com/GPX/1/0"

#: A content validator takes element text and returns an issue tuple or ``None``.
ContentValidator = Callable[[str], "tuple[Severity, str] | None"]


class Severity(StrEnum):
    """The severity of a validation issue."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(slots=True, frozen=True)
class ValidationIssue:
    """A single GPX schema validation issue.

    Args:
        severity: Whether the issue is an error or a warning.
        message: A human-readable description of the issue.
        path: A breadcrumb path to the offending element
            (e.g. ``gpx > trk[0] > trkseg[2] > trkpt[14]``).
        line: The 1-based source line number, when available. Defaults to None.

    """

    severity: Severity
    message: str
    path: str
    line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the issue."""
        return {
            "severity": self.severity.value,
            "line": self.line,
            "path": self.path,
            "message": self.message,
        }

    def __str__(self) -> str:
        location = f"line {self.line}  " if self.line is not None else ""
        return f"{self.severity.value.upper():<7} {location}{self.path}: {self.message}"


@dataclass(slots=True)
class ValidationResult:
    """The result of validating GPX data against the GPX 1.1 schema.

    Args:
        issues: All issues found during validation. Defaults to empty list.

    """

    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        """All issues with error severity."""
        return [i for i in self.issues if i.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """All issues with warning severity."""
        return [i for i in self.issues if i.severity is Severity.WARNING]

    @property
    def is_valid(self) -> bool:
        """True if there are no errors (warnings are allowed)."""
        return not self.errors

    def __bool__(self) -> bool:
        """Return :attr:`is_valid`."""
        return self.is_valid


class InvalidGPXError(ValueError):
    """Raised when strict parsing encounters an invalid GPX document.

    Args:
        result: The validation result carrying all errors and warnings.

    Attributes:
        result: The :class:`ValidationResult` with all issues.
        issues: Shortcut for ``result.errors``.

    """

    def __init__(self, result: ValidationResult) -> None:
        self.result = result
        self.issues = result.errors
        errors = result.errors
        summary = "\n".join(f"  {issue}" for issue in errors)
        count = len(errors)
        noun = "error" if count == 1 else "errors"
        super().__init__(f"Invalid GPX ({count} {noun}):\n{summary}")


# --------------------------------------------------------------------------- #
# Content validators (leaf element text / attribute values)
# --------------------------------------------------------------------------- #


def _decimal(text: str) -> tuple[Severity, str] | None:
    try:
        Decimal(text)
    except InvalidOperation:
        return Severity.ERROR, f"'{text}' is not a valid decimal number"
    return None


def _latitude(text: str) -> tuple[Severity, str] | None:
    try:
        value = Decimal(text)
    except InvalidOperation:
        return Severity.ERROR, f"invalid latitude '{text}' (not a number)"
    if not -90 <= value <= 90:  # noqa: PLR2004
        return Severity.ERROR, f"invalid latitude '{text}' (must be in [-90, 90])"
    return None


def _longitude(text: str) -> tuple[Severity, str] | None:
    try:
        value = Decimal(text)
    except InvalidOperation:
        return Severity.ERROR, f"invalid longitude '{text}' (not a number)"
    if not -180 <= value <= 180:  # noqa: PLR2004
        return Severity.ERROR, f"invalid longitude '{text}' (must be in [-180, 180])"
    if value == 180:  # noqa: PLR2004
        return (
            Severity.WARNING,
            f"longitude {text} equals 180.0 "
            "(the GPX 1.1 schema upper bound is exclusive)",
        )
    return None


def _degrees(text: str) -> tuple[Severity, str] | None:
    try:
        value = Decimal(text)
    except InvalidOperation:
        return Severity.ERROR, f"invalid degrees value '{text}' (not a number)"
    if not 0 <= value < 360:  # noqa: PLR2004
        return Severity.ERROR, f"invalid degrees value '{text}' (must be in [0, 360))"
    return None


def _fix(text: str) -> tuple[Severity, str] | None:
    if text not in Fix.ALLOWED_VALUES:
        allowed = ", ".join(Fix.ALLOWED_VALUES)
        return Severity.ERROR, f"invalid fix '{text}' (must be one of {allowed})"
    return None


def _dgpsid(text: str) -> tuple[Severity, str] | None:
    try:
        value = int(text)
    except ValueError:
        return Severity.ERROR, f"invalid dgpsid '{text}' (not an integer)"
    if not 0 <= value <= 1023:  # noqa: PLR2004
        return Severity.ERROR, f"invalid dgpsid '{text}' (must be in [0, 1023])"
    return None


def _non_negative_int(text: str) -> tuple[Severity, str] | None:
    try:
        value = int(text)
    except ValueError:
        return Severity.ERROR, f"'{text}' is not a valid integer"
    if value < 0:
        return Severity.ERROR, f"'{text}' must be a non-negative integer"
    return None


def _gyear(text: str) -> tuple[Severity, str] | None:
    # xsd:gYear, e.g. "2004" with an optional timezone suffix.
    if not re.fullmatch(r"-?\d{4,}(?:Z|[+-]\d{2}:\d{2})?", text):
        return Severity.ERROR, f"invalid year '{text}' (must be a year, e.g. 2004)"
    return None


def _time(text: str) -> tuple[Severity, str] | None:
    try:
        value = dt.datetime.fromisoformat(text)
    except ValueError:
        return (
            Severity.ERROR,
            f"invalid time '{text}' (must be an ISO 8601 / xsd:dateTime value)",
        )
    if value.tzinfo is None:
        return (
            Severity.WARNING,
            f"time '{text}' has no timezone (GPX timestamps should be in UTC)",
        )
    return None


def _version(text: str) -> tuple[Severity, str] | None:
    if text != "1.1":
        return (
            Severity.WARNING,
            f"version is '{text}' but only '1.1' is supported by this library",
        )
    return None


# --------------------------------------------------------------------------- #
# Schema definition (mirrors gpx.xsd)
# --------------------------------------------------------------------------- #


@dataclass(slots=True, frozen=True)
class AttrRule:
    """A required XML attribute and its optional content validator."""

    name: str
    validator: ContentValidator | None = None


@dataclass(slots=True, frozen=True)
class ChildRule:
    """A child element rule within an ``xsd:sequence``.

    Args:
        tag: The local element name.
        max_occurs: Maximum occurrences (``None`` means unbounded). Defaults to 1.
        content: Validator for a leaf element's text. Defaults to None.
        type_name: Complex type to recurse into for this child. Defaults to None.

    """

    tag: str
    max_occurs: int | None = 1
    content: ContentValidator | None = None
    type_name: str | None = None


@dataclass(slots=True, frozen=True)
class ComplexType:
    """A GPX complex type: its required attributes and ordered children."""

    attrs: tuple[AttrRule, ...] = ()
    children: tuple[ChildRule, ...] = ()


#: The name of the synthetic complex type used for the ``<extensions>`` element.
#: Its content is intentionally not validated (foreign namespaces, lax content).
_EXTENSIONS = "extensions"

#: Declarative GPX 1.1 schema, keyed by complex type name.
SCHEMA: dict[str, ComplexType] = {
    "gpx": ComplexType(
        attrs=(AttrRule("version", _version), AttrRule("creator")),
        children=(
            ChildRule("metadata", type_name="metadata"),
            ChildRule("wpt", max_occurs=None, type_name="wpt"),
            ChildRule("rte", max_occurs=None, type_name="rte"),
            ChildRule("trk", max_occurs=None, type_name="trk"),
            ChildRule("extensions", type_name=_EXTENSIONS),
        ),
    ),
    "metadata": ComplexType(
        children=(
            ChildRule("name"),
            ChildRule("desc"),
            ChildRule("author", type_name="person"),
            ChildRule("copyright", type_name="copyright"),
            ChildRule("link", max_occurs=None, type_name="link"),
            ChildRule("time", content=_time),
            ChildRule("keywords"),
            ChildRule("bounds", type_name="bounds"),
            ChildRule("extensions", type_name=_EXTENSIONS),
        ),
    ),
    "wpt": ComplexType(
        attrs=(AttrRule("lat", _latitude), AttrRule("lon", _longitude)),
        children=(
            ChildRule("ele", content=_decimal),
            ChildRule("time", content=_time),
            ChildRule("magvar", content=_degrees),
            ChildRule("geoidheight", content=_decimal),
            ChildRule("name"),
            ChildRule("cmt"),
            ChildRule("desc"),
            ChildRule("src"),
            ChildRule("link", max_occurs=None, type_name="link"),
            ChildRule("sym"),
            ChildRule("type"),
            ChildRule("fix", content=_fix),
            ChildRule("sat", content=_non_negative_int),
            ChildRule("hdop", content=_decimal),
            ChildRule("vdop", content=_decimal),
            ChildRule("pdop", content=_decimal),
            ChildRule("ageofdgpsdata", content=_decimal),
            ChildRule("dgpsid", content=_dgpsid),
            ChildRule("extensions", type_name=_EXTENSIONS),
        ),
    ),
    "rte": ComplexType(
        children=(
            ChildRule("name"),
            ChildRule("cmt"),
            ChildRule("desc"),
            ChildRule("src"),
            ChildRule("link", max_occurs=None, type_name="link"),
            ChildRule("number", content=_non_negative_int),
            ChildRule("type"),
            ChildRule("extensions", type_name=_EXTENSIONS),
            ChildRule("rtept", max_occurs=None, type_name="wpt"),
        ),
    ),
    "trk": ComplexType(
        children=(
            ChildRule("name"),
            ChildRule("cmt"),
            ChildRule("desc"),
            ChildRule("src"),
            ChildRule("link", max_occurs=None, type_name="link"),
            ChildRule("number", content=_non_negative_int),
            ChildRule("type"),
            ChildRule("extensions", type_name=_EXTENSIONS),
            ChildRule("trkseg", max_occurs=None, type_name="trkseg"),
        ),
    ),
    "trkseg": ComplexType(
        children=(
            ChildRule("trkpt", max_occurs=None, type_name="wpt"),
            ChildRule("extensions", type_name=_EXTENSIONS),
        ),
    ),
    "person": ComplexType(
        children=(
            ChildRule("name"),
            ChildRule("email", type_name="email"),
            ChildRule("link", type_name="link"),
        ),
    ),
    "copyright": ComplexType(
        attrs=(AttrRule("author"),),
        children=(
            ChildRule("year", content=_gyear),
            ChildRule("license"),
        ),
    ),
    "link": ComplexType(
        attrs=(AttrRule("href"),),
        children=(
            ChildRule("text"),
            ChildRule("type"),
        ),
    ),
    "email": ComplexType(attrs=(AttrRule("id"), AttrRule("domain"))),
    "bounds": ComplexType(
        attrs=(
            AttrRule("minlat", _latitude),
            AttrRule("minlon", _longitude),
            AttrRule("maxlat", _latitude),
            AttrRule("maxlon", _longitude),
        ),
    ),
}


# --------------------------------------------------------------------------- #
# Parsing with source line numbers
# --------------------------------------------------------------------------- #


def _split_tag(tag: str) -> tuple[str, str]:
    """Split a Clark-notation tag into ``(namespace, local_name)``."""
    if tag.startswith("{"):
        namespace, local = tag[1:].split("}", 1)
        return namespace, local
    return "", tag


def _parse_with_lines(text: str) -> tuple[ET.Element, dict[int, int]]:
    """Parse XML into an element tree, recording each element's source line.

    Args:
        text: The XML content.

    Returns:
        A tuple of the root element and a mapping from ``id(element)`` to the
        1-based source line number where the element starts.

    Raises:
        expat.ExpatError: If the XML is not well-formed.

    """
    builder = ET.TreeBuilder()
    line_map: dict[int, int] = {}
    parser = expat.ParserCreate(namespace_separator="}")

    def _fixname(name: str) -> str:
        return f"{{{name}" if "}" in name else name

    def _start(tag: str, attrs: dict[str, str]) -> None:
        elem = builder.start(_fixname(tag), {_fixname(k): v for k, v in attrs.items()})
        line_map[id(elem)] = parser.CurrentLineNumber

    parser.StartElementHandler = _start
    parser.EndElementHandler = lambda tag: builder.end(_fixname(tag))
    parser.CharacterDataHandler = builder.data
    parser.Parse(text, True)  # noqa: FBT003

    return builder.close(), line_map


# --------------------------------------------------------------------------- #
# Tree validation
# --------------------------------------------------------------------------- #


class _Validator:
    """Walks an element tree and collects schema validation issues."""

    def __init__(self, line_map: dict[int, int]) -> None:
        self._line_map = line_map
        self.issues: list[ValidationIssue] = []

    def _line(self, elem: ET.Element) -> int | None:
        return self._line_map.get(id(elem))

    def _add(
        self, severity: Severity, message: str, path: str, line: int | None
    ) -> None:
        self.issues.append(ValidationIssue(severity, message, path, line))

    def validate_root(self, root: ET.Element) -> None:
        """Validate the document root element, then its full subtree."""
        namespace, local = _split_tag(root.tag)
        line = self._line(root)

        if local != "gpx":
            self._add(
                Severity.ERROR,
                f"root element is <{local}>, expected <gpx>",
                "gpx",
                line,
            )

        if namespace != GPX_NAMESPACE:
            if namespace == GPX_10_NAMESPACE:
                self._add(
                    Severity.ERROR,
                    "document uses the GPX 1.0 namespace; only GPX 1.1 is supported",
                    "gpx",
                    line,
                )
            elif namespace:
                self._add(
                    Severity.ERROR,
                    f"unexpected namespace '{namespace}' (expected '{GPX_NAMESPACE}')",
                    "gpx",
                    line,
                )
            else:
                self._add(
                    Severity.ERROR,
                    f"missing GPX namespace (expected '{GPX_NAMESPACE}')",
                    "gpx",
                    line,
                )

        self._validate_complex(root, "gpx", "gpx")

    def _validate_complex(self, elem: ET.Element, type_name: str, path: str) -> None:
        # The contents of <extensions> are only checked for the namespace of
        # their direct children (foreign namespaces); the rest is lax.
        if type_name == _EXTENSIONS:
            self._validate_extensions(elem, path)
            return

        complex_type = SCHEMA[type_name]
        self._validate_attributes(elem, complex_type, path)

        rules_by_tag = {
            rule.tag: (index, rule) for index, rule in enumerate(complex_type.children)
        }
        allowed_tags = list(rules_by_tag)

        counts: dict[str, int] = {}
        last_index = -1
        last_tag = ""

        for child in elem:
            namespace, local = _split_tag(child.tag)
            child_line = self._line(child)

            # Foreign-namespace elements are only allowed inside <extensions>.
            if namespace not in {GPX_NAMESPACE, ""}:
                self._add(
                    Severity.WARNING,
                    f"foreign-namespace element <{local}> outside <extensions>",
                    path,
                    child_line,
                )
                continue

            if local not in rules_by_tag:
                self._add(
                    Severity.ERROR,
                    self._unknown_element_message(local, allowed_tags),
                    path,
                    child_line,
                )
                continue

            index, rule = rules_by_tag[local]
            occurrence = counts.get(local, 0)
            counts[local] = occurrence + 1

            # Ordering: children must appear in xsd:sequence order.
            if index < last_index:
                self._add(
                    Severity.WARNING,
                    f"<{local}> appears after <{last_tag}> "
                    "(out of order per GPX 1.1 schema)",
                    path,
                    child_line,
                )
            else:
                last_index = index
                last_tag = local

            child_path = self._child_path(path, rule, occurrence)

            if rule.content is not None:
                self._validate_content(child, rule, child_path)
            if rule.type_name is not None:
                self._validate_complex(child, rule.type_name, child_path)

        self._validate_cardinality(complex_type, counts, elem, path)

    def _validate_extensions(self, elem: ET.Element, path: str) -> None:
        """Check the namespaces of an ``<extensions>`` element's children.

        The GPX 1.1 schema declares extension content as
        ``<xsd:any namespace="##other" processContents="lax">``, meaning each
        direct child must come from a *foreign* namespace. Children in the GPX
        namespace, or in no namespace at all (e.g. unprefixed elements that
        inherit the default GPX namespace), violate the schema. Their own
        contents are otherwise not validated.
        """
        for child in elem:
            namespace, local = _split_tag(child.tag)
            if namespace == GPX_NAMESPACE:
                qualifier = "the GPX namespace"
            elif not namespace:
                qualifier = "no namespace"
            else:
                continue
            self._add(
                Severity.WARNING,
                f"<extensions> child <{local}> is in {qualifier} "
                "(extension content must use a foreign namespace per GPX 1.1)",
                f"{path} > {local}",
                self._line(child),
            )

    def _validate_attributes(
        self, elem: ET.Element, complex_type: ComplexType, path: str
    ) -> None:
        line = self._line(elem)
        for attr in complex_type.attrs:
            value = elem.get(attr.name)
            if value is None:
                self._add(
                    Severity.ERROR,
                    f"missing required '{attr.name}' attribute",
                    path,
                    line,
                )
                continue
            if attr.validator is not None:
                result = attr.validator(value)
                if result is not None:
                    severity, message = result
                    self._add(severity, message, path, line)

    def _validate_content(
        self, child: ET.Element, rule: ChildRule, child_path: str
    ) -> None:
        if rule.content is None:
            return
        text = (child.text or "").strip()
        if not text:
            return
        result = rule.content(text)
        if result is not None:
            severity, message = result
            self._add(severity, message, child_path, self._line(child))

    def _validate_cardinality(
        self,
        complex_type: ComplexType,
        counts: dict[str, int],
        elem: ET.Element,
        path: str,
    ) -> None:
        line = self._line(elem)
        for rule in complex_type.children:
            if rule.max_occurs is None:
                continue
            count = counts.get(rule.tag, 0)
            if count > rule.max_occurs:
                self._add(
                    Severity.ERROR,
                    f"duplicate <{rule.tag}> element "
                    f"(at most {rule.max_occurs} allowed per GPX 1.1 schema)",
                    path,
                    line,
                )

    @staticmethod
    def _child_path(path: str, rule: ChildRule, occurrence: int) -> str:
        if rule.max_occurs == 1:
            return f"{path} > {rule.tag}"
        return f"{path} > {rule.tag}[{occurrence}]"

    @staticmethod
    def _unknown_element_message(local: str, allowed_tags: list[str]) -> str:
        matches = difflib.get_close_matches(local, allowed_tags, n=1)
        if matches:
            return f"unknown element <{local}> (did you mean <{matches[0]}>?)"
        return f"unknown element <{local}>"


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def _resolve_source(source: str | Path | Any) -> str:  # noqa: ANN401
    """Resolve a validation source to a string of GPX XML content.

    Args:
        source: A file path, a string of GPX content, or a GPX instance.

    Returns:
        The GPX XML content as a string.

    """
    if isinstance(source, Path):
        return source.read_text("utf-8")
    if isinstance(source, str):
        # A string that looks like XML is treated as content; otherwise it is
        # treated as a file path.
        if source.lstrip().startswith("<"):
            return source
        return Path(source).read_text("utf-8")
    # Assume a GPX instance (or anything serializable to a GPX string).
    if hasattr(source, "to_string"):
        return source.to_string()
    msg = f"Cannot validate object of type {type(source).__name__}"
    raise TypeError(msg)


def validate(source: str | Path | Any) -> ValidationResult:  # noqa: ANN401
    """Validate GPX data against the GPX 1.1 schema.

    Args:
        source: The GPX data to validate. May be a file path (``str`` or
            ``Path``), a string of GPX content, or a
            :class:`~gpx.gpx.GPX` instance (which is serialized first).

    Returns:
        A :class:`ValidationResult` holding all errors and warnings found.

    Example:
        >>> from gpx import validate
        >>> result = validate("track.gpx")
        >>> if not result.is_valid:
        ...     for issue in result.errors:
        ...         print(issue)

    """
    text = _resolve_source(source)

    try:
        root, line_map = _parse_with_lines(text)
    except expat.ExpatError as e:
        return ValidationResult(
            [
                ValidationIssue(
                    Severity.ERROR,
                    f"not well-formed XML: {e}",
                    "gpx",
                    getattr(e, "lineno", None),
                )
            ]
        )

    validator = _Validator(line_map)
    validator.validate_root(root)
    return ValidationResult(validator.issues)
