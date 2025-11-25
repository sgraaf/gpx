"""Copyright model for GPX data.

This module provides the Copyright model containing information about the
copyright holder and any license governing use of the GPX data, following the
GPX 1.1 specification.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from lxml import etree

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
        author_value = element.get("author")

        if author_value is None:
            msg = "Copyright element missing required 'author' attribute"
            raise ValueError(msg)

        # Parse optional year element
        year_value = None
        year_element = element.find("year")
        if year_element is not None and year_element.text is not None:
            year_value = int(year_element.text)

        # Parse optional license element
        license_value = None
        license_element = element.find("license")
        if license_element is not None:
            license_value = license_element.text

        return cls(author=author_value, year=year_value, license=license_value)

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
        element.set("author", self.author)

        if self.year is not None:
            year_element = etree.SubElement(element, "year", nsmap=nsmap)
            year_element.text = str(self.year)

        if self.license is not None:
            license_element = etree.SubElement(element, "license", nsmap=nsmap)
            license_element.text = self.license

        return element
