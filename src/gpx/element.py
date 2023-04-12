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
        self._nsmap: dict[str | None, str] | None = None

    def _parse(self) -> None:
        """Parses the XML element.

        Raises:
            ParseError: If the XML element is `None`.
        """
        # check if element exists before attempting to parse
        if self._element is None:
            raise ParseError("No element to parse.")

        # namespaces
        if (nsmap := self._element.nsmap) is not None:
            self._nsmap = nsmap

    def _filter_nsmap(self) -> None:
        """Filters the namespace mapping to only include the namespaces used
        by the element.
        """
        if self._element is None or self._nsmap is None:
            return None

        # get all namespaces used by the element and its children
        used_ns = set()
        for element in self._element.iter():
            ns_uri = etree.QName(element).namespace
            if ns_uri:
                used_ns.add(ns_uri)
            for attrib_name in element.attrib:
                ns_uri = etree.QName(attrib_name).namespace
                if ns_uri:
                    used_ns.add(ns_uri)

        # filter the namespace mapping to only include the namespaces used by
        # the element and its children
        self._nsmap = {
            prefix: uri
            for prefix, uri in self._nsmap.items()
            if uri in used_ns or prefix is None  # keep default namespace
        }

    def _build(self, tag: str) -> etree._Element:
        """Builds the XML element.

        Args:
            tag: The XML tag.

        Returns:
            The XML element.
        """
        self._filter_nsmap()
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
