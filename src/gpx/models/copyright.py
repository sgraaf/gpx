"""Copyright model for GPX data.

This module provides the Copyright model containing information about the
copyright holder and any license governing use of the GPX data, following the
GPX 1.1 specification.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from lxml import etree

from .utils import (
    build_xml_attributes,
    build_xml_elements,
    parse_xml_attributes,
    parse_xml_elements,
)

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

#: GPX 1.1 namespace
GPX_NAMESPACE = "http://www.topografix.com/GPX/1/1"


@dataclass(frozen=True)
class Copyright:
    """Information about the copyright holder and any license.

    By linking to an appropriate license, you may place your data into the
    public domain or grant additional usage rights.

    Args:
        author: Copyright holder (e.g. TopoSoft, Inc.)
        year: Year of copyright. Defaults to None.
        license: Link to external file containing license text. Defaults to None.

    """

    author: str
    year: int | None = None
    license: str | None = None

    @classmethod
    def from_xml(cls, element: etree._Element) -> Self:
        """Parse a Copyright from an XML element.

        Args:
            element: The XML element to parse.

        Returns:
            The parsed Copyright instance.

        Raises:
            ValueError: If required attributes are missing.

        """
        # Parse attributes
        kwargs = parse_xml_attributes(cls, element, attribute_names={"author"})
        # Parse child elements
        kwargs.update(
            parse_xml_elements(cls, element, element_names={"year", "license"})
        )
        return cls(**kwargs)

    def to_xml(
        self, tag: str = "copyright", nsmap: dict[str | None, str] | None = None
    ) -> etree._Element:
        """Convert the Copyright to an XML element.

        Args:
            tag: The XML tag name. Defaults to "copyright".
            nsmap: Optional namespace mapping. Defaults to GPX 1.1 namespace.

        Returns:
            The XML element.

        """
        if nsmap is None:
            nsmap = {None: GPX_NAMESPACE}

        element = etree.Element(tag, nsmap=nsmap)
        build_xml_attributes(self, element, attribute_names={"author"})
        build_xml_elements(
            self, element, element_names={"year", "license"}, nsmap=nsmap
        )

        return element
