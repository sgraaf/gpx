"""Utilities for dataclass-based GPX models.

This module provides utilities for automatic XML parsing and serialization
based on dataclass field types and metadata.
"""

from __future__ import annotations

import sys
from dataclasses import fields
from typing import Any, get_args, get_origin

from lxml import etree

if sys.version_info < (3, 11):
    from typing_extensions import get_type_hints
else:
    from typing import get_type_hints


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


def parse_xml_attributes(
    cls: type[Any],
    element: etree._Element,
    attribute_names: set[str] | None = None,
) -> dict[str, Any]:
    """Parse XML attributes into a dictionary based on dataclass field types.

    Args:
        cls: The dataclass type.
        element: The XML element to parse.
        attribute_names: Optional set of field names that should be parsed as
            XML attributes. If None, all fields are considered.

    Returns:
        A dictionary mapping field names to parsed values.

    Raises:
        ValueError: If a required attribute is missing.

    """
    type_hints = get_type_hints(cls)
    result: dict[str, Any] = {}

    for field in fields(cls):
        # Skip if not in attribute_names (if provided)
        if attribute_names is not None and field.name not in attribute_names:
            continue

        field_type = type_hints.get(field.name, field.type)
        value = element.get(field.name)

        # Check if required
        if value is None:
            if not is_optional(field_type):
                msg = (
                    f"{cls.__name__} element missing required '{field.name}' attribute"
                )
                raise ValueError(msg)
            # Optional field with no value
            result[field.name] = None
            continue

        # Convert to appropriate type
        inner_type = get_inner_type(field_type)
        result[field.name] = inner_type(value)

    return result


def parse_xml_elements(
    cls: type[Any],
    element: etree._Element,
    element_names: set[str] | None = None,
) -> dict[str, Any]:
    """Parse XML child elements into a dictionary based on dataclass field types.

    Args:
        cls: The dataclass type.
        element: The XML element to parse.
        element_names: Optional set of field names that should be parsed as
            XML child elements. If None, all fields are considered.

    Returns:
        A dictionary mapping field names to parsed values.

    Raises:
        ValueError: If a required element is missing.

    """
    type_hints = get_type_hints(cls)
    result: dict[str, Any] = {}

    for field in fields(cls):
        # Skip if not in element_names (if provided)
        if element_names is not None and field.name not in element_names:
            continue

        field_type = type_hints.get(field.name, field.type)
        child = element.find(field.name)

        # Check if required
        if child is None or child.text is None:
            if not is_optional(field_type):
                msg = f"{cls.__name__} missing required '{field.name}' child element"
                raise ValueError(msg)
            # Optional field with no value
            result[field.name] = None
            continue

        # Convert to appropriate type
        inner_type = get_inner_type(field_type)
        result[field.name] = inner_type(child.text)

    return result


def build_xml_attributes(
    obj: Any,  # noqa: ANN401
    element: etree._Element,
    attribute_names: set[str] | None = None,
) -> None:
    """Set XML attributes from dataclass fields.

    Args:
        obj: The dataclass instance.
        element: The XML element to modify.
        attribute_names: Optional set of field names that should be serialized
            as XML attributes. If None, all fields are considered.

    """
    for field in fields(obj):
        # Skip if not in attribute_names (if provided)
        if attribute_names is not None and field.name not in attribute_names:
            continue

        value = getattr(obj, field.name)
        if value is not None:
            element.set(field.name, str(value))


def build_xml_elements(
    obj: Any,  # noqa: ANN401
    element: etree._Element,
    element_names: set[str] | None = None,
    nsmap: dict[str | None, str] | None = None,
) -> None:
    """Create XML child elements from dataclass fields.

    Args:
        obj: The dataclass instance.
        element: The parent XML element.
        element_names: Optional set of field names that should be serialized
            as XML child elements. If None, all fields are considered.
        nsmap: Optional namespace mapping for child elements.

    """
    for field in fields(obj):
        # Skip if not in element_names (if provided)
        if element_names is not None and field.name not in element_names:
            continue

        value = getattr(obj, field.name)
        if value is not None:
            child = etree.SubElement(element, field.name, nsmap=nsmap)
            child.text = str(value)
