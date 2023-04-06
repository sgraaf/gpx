"""
This module provides a Metadata object to contain GPX metadata, containing
information about the GPX file, author, and copyright restrictions.
"""
from __future__ import annotations

import datetime

from dateutil.parser import isoparse
from lxml import etree

from .bounds import Bounds
from .copyright import Copyright
from .element import Element
from .link import Link
from .person import Person


class Metadata(Element):
    """A metadata class for the GPX data format.

    Information about the GPX file, author, and copyright restrictions goes in
    the metadata section. Providing rich, meaningful information about your GPX
    files allows others to search for and use your GPS data.

    Args:
        element: The metadata XML element. Defaults to `None`.
    """

    #: The name of the GPX file.
    name: str | None = None

    #: A description of the contents of the GPX file.
    desc: str | None = None

    #: The person or organization who created the GPX file.
    author: Person | None = None

    #: Copyright and license information governing use of the file.
    copyright: Copyright | None = None

    #: URLs associated with the location described in the file.
    links: list[Link] = []

    #: The creation date of the file.
    time: datetime.datetime | None = None

    #: Keywords associated with the file. Search engines or databases can use
    #: this information to classify the data.
    keywords: str | None = None

    #: Minimum and maximum coordinates which describe the extent of the
    #: coordinates in the file.
    bounds: Bounds | None = None

    def _parse(self) -> None:
        super()._parse()

        # assertion to satisfy mypy
        assert self._element is not None

        # name
        if (name := self._element.find("name", namespaces=self._nsmap)) is not None:
            self.name = name.text

        # description
        if (desc := self._element.find("desc", namespaces=self._nsmap)) is not None:
            self.desc = desc.text

        # author
        if (author := self._element.find("author", namespaces=self._nsmap)) is not None:
            self.author = Person(author)

        # copyright
        if (
            _copyright := self._element.find("copyright", namespaces=self._nsmap)
        ) is not None:
            self.copyright = Copyright(_copyright)

        # links
        for link in self._element.iterfind("link", namespaces=self._nsmap):
            self.links.append(Link(link))

        # creation date of the GPX file
        if (time := self._element.find("time", namespaces=self._nsmap)) is not None:
            self.time = isoparse(time.text)

        # keywords
        if (
            keywords := self._element.find("keywords", namespaces=self._nsmap)
        ) is not None:
            self.keywords = keywords.text

        # bounds
        if (bounds := self._element.find("bounds", namespaces=self._nsmap)) is not None:
            self.bounds = Bounds(bounds)

    def _build(self, tag: str = "metadata") -> etree._Element:
        metadata = super()._build(tag)

        if self.name is not None:
            name = etree.SubElement(metadata, "name", nsmap=self._nsmap)
            name.text = self.name

        if self.desc is not None:
            desc = etree.SubElement(metadata, "desc", nsmap=self._nsmap)
            desc.text = self.desc

        if self.author:
            metadata.append(self.author._build())

        if self.copyright:
            metadata.append(self.copyright._build())

        for link in self.links:
            metadata.append(link._build())

        if self.time is not None:
            time = etree.SubElement(metadata, "time", nsmap=self._nsmap)
            time.text = self.time.isoformat(
                timespec="milliseconds" if self.time.microsecond else "seconds"
            ).replace("+00:00", "Z")

        if self.keywords is not None:
            keywords = etree.SubElement(metadata, "keywords", nsmap=self._nsmap)
            keywords.text = self.keywords

        if self.bounds is not None:
            metadata.append(self.bounds._build())

        return metadata
