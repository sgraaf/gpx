"""Utilities for GPX models.

This module provides utilities for automatic XML parsing and serialization
based on dataclass field types and metadata.

Key GPX specification pattern:
- XML attributes are always required → dataclass fields without | None
- XML child elements are always optional → dataclass fields with | None

This allows automatic determination of attributes vs elements based on type hints.
"""

from __future__ import annotations

import datetime as dt
import re
import xml.etree.ElementTree as ET
from dataclasses import fields
from typing import (
    TYPE_CHECKING,
    Any,
    SupportsFloat,
    SupportsInt,
    get_args,
    get_origin,
    get_type_hints,
)

if TYPE_CHECKING:
    from collections.abc import Iterable


def _get_namespace(element: ET.Element) -> str:
    """Extract the namespace from an element's tag.

    Args:
        element: The XML element.

    Returns:
        The namespace URI, or empty string if no namespace.

    """
    if element.tag.startswith("{"):
        return element.tag[1 : element.tag.index("}")]
    return ""


def _ns_tag(tag: str, element: ET.Element) -> str:
    """Return a namespaced tag in Clark notation based on the parent element's namespace.

    Args:
        tag: The tag name without namespace.
        element: The parent element to extract namespace from.

    Returns:
        The tag with namespace in Clark notation, or just the tag if no namespace.

    """
    namespace = _get_namespace(element)
    if namespace:
        return f"{{{namespace}}}{tag}"
    return tag


def remove_encoding_from_string(s: str) -> str:
    """Remove encoding declarations (e.g. encoding="utf-8") from the string, if any.

    Args:
        s: The string.

    Returns:
        The string with any encoding declarations removed.

    """
    return re.sub(r"(encoding=[\"\'].+[\"\'])", "", s)


def from_isoformat(dt_str: str) -> dt.datetime:
    """Convert a string in ISO 8601 format to a `datetime` object."""
    return dt.datetime.fromisoformat(dt_str)


def to_isoformat(dt: dt.datetime) -> str:
    """Convert a `datetime` object to a string in ISO 8601 format."""
    return dt.isoformat(
        timespec="milliseconds" if dt.microsecond else "seconds"
    ).replace("+00:00", "Z")


def is_optional(field_type: type) -> bool:
    """Check if a type annotation represents an optional field.

    Args:
        field_type: The type annotation to check.

    Returns:
        True if the type is Optional (Union[T, None]), False otherwise.

    """
    origin = get_origin(field_type)
    if origin is not None:
        # Check for Union types (which includes Optional)
        args = get_args(field_type)
        return type(None) in args
    return False


def get_inner_type(field_type: type) -> type:
    """Extract the inner type from an Optional type annotation.

    Args:
        field_type: The type annotation (possibly Optional).

    Returns:
        The inner type (without None).

    """
    if is_optional(field_type):
        args = get_args(field_type)
        # Filter out NoneType
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return non_none_args[0]
        # Handle Union with multiple non-None types (keep as is)
        return field_type
    return field_type


def is_list_type(field_type: type) -> bool:
    """Check if a type annotation represents a list.

    Args:
        field_type: The type annotation to check.

    Returns:
        True if the type is a list, False otherwise.

    """
    origin = get_origin(field_type)
    return origin is list


def get_list_item_type(field_type: type) -> type:
    """Extract the item type from a list type annotation.

    Args:
        field_type: The list type annotation.

    Returns:
        The item type.

    """
    args = get_args(field_type)
    if args:
        return args[0]
    return Any


def has_from_xml(obj_type: type) -> bool:
    """Check if a type has a from_xml classmethod.

    Args:
        obj_type: The type to check.

    Returns:
        True if the type has a from_xml method, False otherwise.

    """
    return hasattr(obj_type, "from_xml") and callable(obj_type.from_xml)


def has_to_xml(obj: Any) -> bool:  # noqa: ANN401
    """Check if an object has a to_xml method.

    Args:
        obj: The object to check.

    Returns:
        True if the object has a to_xml method, False otherwise.

    """
    return hasattr(obj, "to_xml") and callable(obj.to_xml)


def parse_from_xml(cls: type[Any], element: ET.Element) -> dict[str, Any]:  # noqa: C901, PLR0912
    """Parse XML element into dictionary by auto-detecting attributes vs elements.

    Uses the GPX specification pattern:
    - Required fields (no | None) are parsed as XML attributes
    - Optional fields (with | None) are parsed as XML child elements

    Supports:
    - Simple types (str, int, etc.)
    - Nested models (types with from_xml() method)
    - Lists of models (list[Model])
    - Extensions (special handling for GPX extensions)

    Args:
        cls: The dataclass type.
        element: The XML element to parse.

    Returns:
        A dictionary mapping field names to parsed values.

    Raises:
        ValueError: If a required attribute is missing.

    """
    type_hints = get_type_hints(cls)
    result: dict[str, Any] = {}

    for field in fields(cls):
        # Skip KW_ONLY marker
        if field.name == "_":
            continue

        field_type = type_hints.get(field.name, field.type)

        # Lists are always treated as optional child elements (even without | None)
        if is_list_type(field_type):
            item_type = get_list_item_type(field_type)
            items = []
            for child in element.findall(_ns_tag(field.name, element)):
                if has_from_xml(item_type):
                    items.append(item_type.from_xml(child))  # type: ignore[attr-defined]
                else:
                    items.append(item_type(child.text) if child.text else None)
            result[field.name] = items
        elif is_optional(field_type):
            # Optional field → parse as XML child element
            inner_type = get_inner_type(field_type)

            # Check if it's a list of models (Optional[list[T]])
            if is_list_type(inner_type):
                item_type = get_list_item_type(inner_type)
                items = []
                for child in element.findall(_ns_tag(field.name, element)):
                    if has_from_xml(item_type):
                        items.append(item_type.from_xml(child))  # type: ignore[attr-defined]
                    else:
                        items.append(item_type(child.text) if child.text else None)
                result[field.name] = items
            else:
                # Single optional element
                child = element.find(_ns_tag(field.name, element))  # type: ignore[assignment]
                if child is None:
                    result[field.name] = None
                elif has_from_xml(inner_type):
                    # Nested model
                    result[field.name] = inner_type.from_xml(child)  # type: ignore[attr-defined]
                elif child.text is None:
                    result[field.name] = None
                # Simple type - handle datetime specially
                elif inner_type is dt.datetime:
                    result[field.name] = from_isoformat(child.text)
                else:
                    result[field.name] = inner_type(child.text)
        else:
            # Required field → parse as XML attribute
            value = element.get(field.name)
            if value is None:
                msg = (
                    f"{cls.__name__} element missing required '{field.name}' attribute"
                )
                raise ValueError(msg)
            result[field.name] = field_type(value)

    return result


def build_to_xml(  # noqa: C901, PLR0912
    obj: Any,  # noqa: ANN401
    element: ET.Element,
    nsmap: dict[str | None, str] | None = None,
) -> None:
    """Serialize dataclass to XML by auto-detecting attributes vs elements.

    Uses the GPX specification pattern:
    - Required fields (no | None) are serialized as XML attributes
    - Optional fields (with | None) are serialized as XML child elements

    Supports:
    - Simple types (str, int, etc.)
    - Nested models (objects with to_xml() method)
    - Lists of models (list[Model])

    Args:
        obj: The dataclass instance.
        element: The XML element to populate.
        nsmap: Optional namespace mapping for child elements.

    """
    type_hints = get_type_hints(obj.__class__)

    for field in fields(obj):
        # Skip KW_ONLY marker
        if field.name == "_":
            continue

        field_type = type_hints.get(field.name, field.type)
        value = getattr(obj, field.name)

        if value is None:
            continue  # Skip None values

        # Lists are always treated as optional child elements (even without | None)
        if is_list_type(field_type) and isinstance(value, list):
            # List of items
            for item in value:
                if has_to_xml(item):
                    # Nested model with to_xml
                    child = item.to_xml(tag=field.name, nsmap=nsmap)
                    element.append(child)
                else:
                    # Simple type
                    child = ET.SubElement(element, _ns_tag(field.name, element))
                    child.text = str(item)
        elif is_optional(field_type):
            # Optional field → serialize as XML child element
            inner_type = get_inner_type(field_type)

            # Check if it's a list (Optional[list[T]])
            if is_list_type(inner_type) and isinstance(value, list):
                # List of items
                for item in value:
                    if has_to_xml(item):
                        # Nested model with to_xml
                        child = item.to_xml(tag=field.name, nsmap=nsmap)
                        element.append(child)
                    else:
                        # Simple type
                        child = ET.SubElement(element, _ns_tag(field.name, element))
                        child.text = str(item)
            elif has_to_xml(value):
                # Single nested model
                child = value.to_xml(tag=field.name, nsmap=nsmap)
                element.append(child)
            else:
                # Simple type - handle datetime specially
                child = ET.SubElement(element, _ns_tag(field.name, element))
                if isinstance(value, dt.datetime):
                    child.text = to_isoformat(value)
                else:
                    child.text = str(value)
        else:
            # Required field → serialize as XML attribute
            element.set(field.name, str(value))


def has_geo_properties(obj: Any, exclude_fields: Iterable[str] | None = None) -> bool:  # noqa: ANN401
    """Check if a dataclass instance has any optional fields set (for GeoJSON properties).

    This is used to determine whether a GeoJSON representation should be a pure
    geometry or a Feature with properties.

    Args:
        obj: The dataclass instance to check.
        exclude_fields: Field names to exclude from the check (e.g., coordinate fields).

    Returns:
        True if any optional fields (excluding specified ones) are set, False otherwise.

    """
    exclude_fields = set() if exclude_fields is None else set(exclude_fields)

    type_hints = get_type_hints(obj.__class__)

    for field in fields(obj):
        # Skip KW_ONLY marker and excluded fields
        if field.name == "_" or field.name in exclude_fields:
            continue

        field_type = type_hints.get(field.name, field.type)
        value = getattr(obj, field.name)

        # Check if this is an optional field with a value
        # Lists are considered optional and checked for non-empty
        if is_list_type(field_type):
            if value:  # Non-empty list
                return True
        elif is_optional(field_type) and value is not None:
            return True

    return False


def build_geo_properties(
    obj: Any,  # noqa: ANN401
    exclude_fields: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build a GeoJSON properties dictionary from a dataclass instance.

    Converts dataclass fields to JSON-serializable values for GeoJSON properties.
    Excludes specified fields (typically coordinate fields) and only includes
    optional fields that are set.

    Args:
        obj: The dataclass instance.
        exclude_fields: Field names to exclude (e.g., coordinate fields).

    Returns:
        A dictionary mapping field names to JSON-serializable values.

    """
    exclude_fields = set() if exclude_fields is None else set(exclude_fields)

    type_hints = get_type_hints(obj.__class__)
    properties: dict[str, Any] = {}

    for field in fields(obj):
        # Skip KW_ONLY marker and excluded fields
        if field.name == "_" or field.name in exclude_fields:
            continue

        field_type = type_hints.get(field.name, field.type)
        value = getattr(obj, field.name)

        # Skip None values
        if value is None:
            continue

        # Handle lists
        if is_list_type(field_type) and isinstance(value, list):
            if not value:
                continue  # Skip empty lists

            # Check if list items have __geo_interface__ property or to_dict-like behavior
            if hasattr(value[0], "href"):  # Link objects
                properties[field.name] = [
                    {
                        "href": item.href,
                        "text": item.text if hasattr(item, "text") else None,
                        "type": item.type if hasattr(item, "type") else None,
                    }
                    for item in value
                ]
            else:
                # Simple list - convert items to appropriate types
                properties[field.name] = [
                    _convert_value_to_json(item) for item in value
                ]
        elif is_optional(field_type):
            # Optional field with a value
            properties[field.name] = _convert_value_to_json(value)

    return properties


def _convert_value_to_json(value: Any) -> Any:  # noqa: ANN401
    """Convert a value to a JSON-serializable type.

    Args:
        value: The value to convert.

    Returns:
        The JSON-serializable value.

    """
    if isinstance(value, dt.datetime):
        return to_isoformat(value)
    if isinstance(value, SupportsFloat):  # Decimal and similar
        return float(value)
    if isinstance(value, SupportsInt) and not isinstance(value, bool):
        return int(value)
    return str(value)


def build_geo_feature(
    geometry: dict[str, Any],
    obj: Any,  # noqa: ANN401
    exclude_fields: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build a GeoJSON Feature or pure geometry based on whether properties exist.

    If the object has any optional fields set (excluding coordinate fields),
    returns a Feature with geometry and properties. Otherwise, returns the
    pure geometry.

    Args:
        geometry: The GeoJSON geometry dictionary.
        obj: The dataclass instance.
        exclude_fields: Field names to exclude from properties (e.g., coordinate fields).

    Returns:
        A GeoJSON Feature or pure geometry dictionary.

    """
    if not has_geo_properties(obj, exclude_fields):
        return geometry

    properties = build_geo_properties(obj, exclude_fields)

    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": properties,
    }
