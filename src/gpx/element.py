"""
This module provides an Element object to serve as a base class for other GPX
objects.
"""
from __future__ import annotations

from lxml import etree

from .errors import ParseError


class Element:
    """Element base class for GPX elements.

    Args:
        element: The XML element. Defaults to `None`.
    """

    def __init__(self, element: etree._Element | None = None) -> None:
        #: The XML element.
        self._element: etree._Element | None = element

        #: The XML namespace mapping from prefix -> URI.
        self._nsmap: dict[str, str] | None = None

        if self._element is not None:
            self._parse()

    def _parse(self) -> None:
        """Parses the XML element.

        Raises:
            ParseError: If the XML element is `None`.
        """
        # check if element exists before attempting to parse
        if self._element is None:
            raise ParseError("No element to parse.")

        # namespaces
        self._nsmap = self._element.nsmap

    def _build(self, tag: str) -> etree._Element:
        """Builds the XML element.

        Args:
            tag: The XML tag.

        Returns:
            The XML element.
        """
        element = etree.Element(tag, nsmap=self._nsmap)
        return element

    def __repr__(self) -> str:
        attributes = ", ".join(
            [
                f"{attr}={getattr(self, attr)!r}"
                for attr in vars(self)
                if not attr.startswith("_")
            ]
        )
        return f"{self.__class__.__name__}({attributes})"
