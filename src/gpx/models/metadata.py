"""Metadata model for GPX data.

This module provides the Metadata model containing information about the GPX
file, author, and copyright restrictions, following the GPX 1.1 specification.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime  # noqa: TC003

from lxml import etree

from .bounds import Bounds  # noqa: TC001
from .copyright import Copyright  # noqa: TC001
from .link import Link  # noqa: TC001
from .person import Person  # noqa: TC001
from .utils import build_to_xml, parse_from_xml

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

#: GPX 1.1 namespace
GPX_NAMESPACE = "http://www.topografix.com/GPX/1/1"


@dataclass(frozen=True)
class Metadata:
    """Information about the GPX file, author, and copyright restrictions.

    Providing rich, meaningful information about your GPX files allows others
    to search for and use your GPS data.

    Args:
        name: The name of the GPX file. Defaults to None.
        desc: A description of the contents of the GPX file. Defaults to None.
        author: The person or organization who created the GPX file.
            Defaults to None.
        copyright: Copyright and license information governing use of the file.
            Defaults to None.
        link: URLs associated with the location described in the file.
            Defaults to empty list.
        time: The creation date of the file. Defaults to None.
        keywords: Keywords associated with the file. Search engines or
            databases can use this information to classify the data.
            Defaults to None.
        bounds: Minimum and maximum coordinates which describe the extent
            of the coordinates in the file. Defaults to None.

    """

    name: str | None = None
    desc: str | None = None
    author: Person | None = None
    copyright: Copyright | None = None
    link: list[Link] = field(default_factory=list)
    time: datetime | None = None
    keywords: str | None = None
    bounds: Bounds | None = None

    @classmethod
    def from_xml(cls, element: etree._Element) -> Self:
        """Parse a Metadata from an XML element.

        Args:
            element: The XML element to parse.

        Returns:
            The parsed Metadata instance.

        """
        return cls(**parse_from_xml(cls, element))

    def to_xml(
        self, tag: str = "metadata", nsmap: dict[str | None, str] | None = None
    ) -> etree._Element:
        """Convert the Metadata to an XML element.

        Args:
            tag: The XML tag name. Defaults to "metadata".
            nsmap: Optional namespace mapping. Defaults to GPX 1.1 namespace.

        Returns:
            The XML element.

        """
        if nsmap is None:
            nsmap = {None: GPX_NAMESPACE}

        element = etree.Element(tag, nsmap=nsmap)
        build_to_xml(self, element, nsmap=nsmap)

        return element
