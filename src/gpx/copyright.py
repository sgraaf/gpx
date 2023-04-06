"""
This module provides a Copyright object to contain GPX copyright, containing
information about the copyright holder and any license governing use of the GPX
data.
"""
from __future__ import annotations

from lxml import etree

from .element import Element


class Copyright(Element):
    """A copyright class for the GPX data format.

    Information about the copyright holder and any license governing use of this
    file. By linking to an appropriate license, you may place your data into the
    public domain or grant additional usage rights.

    Args:
        element: The copyright XML element. Defaults to `None`.
    """

    #: Copyright holder (e.g. TopoSoft, Inc.).
    author: str

    #: Year of copyright.
    year: int | None = None

    #: Link to external file containing license text.
    license: str | None = None

    def _parse(self) -> None:
        super()._parse()

        # assertion to satisfy mypy
        assert self._element is not None

        # required
        self.author = self._element.get("author")

        # year
        if (year := self._element.find("year", namespaces=self._nsmap)) is not None:
            self.year = int(year.text)

        # license
        if (
            license := self._element.find("license", namespaces=self._nsmap)
        ) is not None:
            self.license = license.text

    def _build(self, tag: str = "copyright") -> etree._Element:
        copyright = super()._build(tag)
        copyright.set("author", self.author)

        if self.year is not None:
            year = etree.SubElement(copyright, "year", nsmap=self._nsmap)
            year.text = str(self.year)

        if self.license is not None:
            license = etree.SubElement(copyright, "license", nsmap=self._nsmap)
            license.text = self.license

        return copyright
