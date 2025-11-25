"""Track model for GPX data.

This module provides the Track model representing an ordered list of points
describing a path, following the GPX 1.1 specification.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

from lxml import etree

from .link import Link  # noqa: TC001
from .track_segment import TrackSegment  # noqa: TC001
from .utils import build_to_xml, parse_from_xml

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

#: GPX 1.1 namespace
GPX_NAMESPACE = "http://www.topografix.com/GPX/1/1"


@dataclass(frozen=True)
class Track:
    """An ordered list of points describing a path.

    A track represents a GPS track consisting of track segments.

    Args:
        name: GPS name of track. Defaults to None.
        cmt: GPS comment for track. Defaults to None.
        desc: User description of track. Defaults to None.
        src: Source of data. Defaults to None.
        link: Links to external information about track. Defaults to empty list.
        number: GPS track number. Defaults to None.
        type: Type (classification) of track. Defaults to None.
        trkseg: List of track segments. Defaults to empty list.

    """

    name: str | None = None
    cmt: str | None = None
    desc: str | None = None
    src: str | None = None
    link: list[Link] = field(default_factory=list)
    number: int | None = None
    type: str | None = None
    trkseg: list[TrackSegment] = field(default_factory=list)

    @classmethod
    def from_xml(cls, element: etree._Element) -> Self:
        """Parse a Track from an XML element.

        Args:
            element: The XML element to parse.

        Returns:
            The parsed Track instance.

        """
        return cls(**parse_from_xml(cls, element))

    def to_xml(
        self, tag: str = "trk", nsmap: dict[str | None, str] | None = None
    ) -> etree._Element:
        """Convert the Track to an XML element.

        Args:
            tag: The XML tag name. Defaults to "trk".
            nsmap: Optional namespace mapping. Defaults to GPX 1.1 namespace.

        Returns:
            The XML element.

        """
        if nsmap is None:
            nsmap = {None: GPX_NAMESPACE}

        element = etree.Element(tag, nsmap=nsmap)
        build_to_xml(self, element, nsmap=nsmap)

        return element
