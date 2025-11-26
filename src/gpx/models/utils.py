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
from datetime import datetime
from typing import Any, get_args, get_origin, get_type_hints

from dateutil.parser import isoparse
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


def parse_from_xml(cls: type[Any], element: etree._Element) -> dict[str, Any]:  # noqa: C901, PLR0912
    """Parse XML element into dictionary by auto-detecting attributes vs elements.

    Uses the GPX specification pattern:
    - Required fields (no | None) are parsed as XML attributes
    - Optional fields (with | None) are parsed as XML child elements

    Supports:
    - Simple types (str, int, etc.)
    - Nested models (types with from_xml() method)
    - Lists of models (list[Model])

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

    # Set up namespace mapping for XPath queries
    # This handles cases where XML has xmlns="..." declarations
    default_ns = element.nsmap.get(None)  # Default namespace
    if default_ns:
        namespaces = {"ns": default_ns}
        xpath_prefix = "ns:"
    else:
        namespaces = None
        xpath_prefix = ""

    for field in fields(cls):
        field_type = type_hints.get(field.name, field.type)

        # Lists are always treated as optional child elements (even without | None)
        if is_list_type(field_type):
            item_type = get_list_item_type(field_type)
            items = []
            for child in element.findall(f"{xpath_prefix}{field.name}", namespaces):
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
                for child in element.findall(f"{xpath_prefix}{field.name}", namespaces):
                    if has_from_xml(item_type):
                        items.append(item_type.from_xml(child))  # type: ignore[attr-defined]
                    else:
                        items.append(item_type(child.text) if child.text else None)
                result[field.name] = items
            else:
                # Single optional element
                child = element.find(f"{xpath_prefix}{field.name}", namespaces)
                if child is None:
                    result[field.name] = None
                elif has_from_xml(inner_type):
                    # Nested model
                    result[field.name] = inner_type.from_xml(child)  # type: ignore[attr-defined]
                elif child.text is None:
                    result[field.name] = None
                # Simple type - handle datetime specially
                elif inner_type is datetime:
                    result[field.name] = isoparse(child.text)
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
    element: etree._Element,
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
                    child = etree.SubElement(element, field.name, nsmap=nsmap)
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
                        child = etree.SubElement(element, field.name, nsmap=nsmap)
                        child.text = str(item)
            elif has_to_xml(value):
                # Single nested model
                child = value.to_xml(tag=field.name, nsmap=nsmap)
                element.append(child)
            else:
                # Simple type - handle datetime specially
                child = etree.SubElement(element, field.name, nsmap=nsmap)
                if isinstance(value, datetime):
                    child.text = value.isoformat()
                else:
                    child.text = str(value)
        else:
            # Required field → serialize as XML attribute
            element.set(field.name, str(value))
