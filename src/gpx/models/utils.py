"""Utilities for dataclass-based GPX models.

This module provides utilities for automatic XML parsing and serialization
based on dataclass field types and metadata.

Key GPX specification pattern:
- XML attributes are always required → dataclass fields without | None
- XML child elements are always optional → dataclass fields with | None

This allows automatic determination of attributes vs elements based on type hints.
"""

from __future__ import annotations

from dataclasses import fields
from typing import Any, get_args, get_origin, get_type_hints

from lxml import etree


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


def parse_from_xml(cls: type[Any], element: etree._Element) -> dict[str, Any]:
    """Parse XML element into dictionary by auto-detecting attributes vs elements.

    Uses the GPX specification pattern:
    - Required fields (no | None) are parsed as XML attributes
    - Optional fields (with | None) are parsed as XML child elements

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
        field_type = type_hints.get(field.name, field.type)

        if is_optional(field_type):
            # Optional field → parse as XML child element
            child = element.find(field.name)
            if child is None or child.text is None:
                result[field.name] = None
            else:
                inner_type = get_inner_type(field_type)
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


def build_to_xml(
    obj: Any,  # noqa: ANN401
    element: etree._Element,
    nsmap: dict[str | None, str] | None = None,
) -> None:
    """Serialize dataclass to XML by auto-detecting attributes vs elements.

    Uses the GPX specification pattern:
    - Required fields (no | None) are serialized as XML attributes
    - Optional fields (with | None) are serialized as XML child elements

    Args:
        obj: The dataclass instance.
        element: The XML element to populate.
        nsmap: Optional namespace mapping for child elements.

    """
    type_hints = get_type_hints(obj.__class__)

    for field in fields(obj):
        field_type = type_hints.get(field.name, field.type)
        value = getattr(obj, field.name)

        if value is None:
            continue  # Skip None values

        if is_optional(field_type):
            # Optional field → serialize as XML child element
            child = etree.SubElement(element, field.name, nsmap=nsmap)
            child.text = str(value)
        else:
            # Required field → serialize as XML attribute
            element.set(field.name, str(value))
