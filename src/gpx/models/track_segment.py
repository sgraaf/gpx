"""TrackSegment model for GPX data.

This module provides the TrackSegment model representing a list of track points
which are logically connected in order, following the GPX 1.1 specification.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

from lxml import etree

from .utils import build_to_xml, parse_from_xml
from .waypoint import Waypoint  # noqa: TC001

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

#: GPX 1.1 namespace
GPX_NAMESPACE = "http://www.topografix.com/GPX/1/1"


@dataclass(frozen=True)
class TrackSegment:
    """A track segment holding a list of logically connected track points.

    A Track Segment holds a list of Track Points which are logically connected
    in order. To represent a single GPS track where GPS reception was lost, or
    the GPS receiver was turned off, start a new Track Segment for each
    continuous span of track data.

    Args:
        trkpt: List of track points. Defaults to empty list.

    """

    trkpt: list[Waypoint] = field(default_factory=list)

    @classmethod
    def from_xml(cls, element: etree._Element) -> Self:
        """Parse a TrackSegment from an XML element.

        Args:
            element: The XML element to parse.

        Returns:
            The parsed TrackSegment instance.

        """
        return cls(**parse_from_xml(cls, element))

    def to_xml(
        self, tag: str = "trkseg", nsmap: dict[str | None, str] | None = None
    ) -> etree._Element:
        """Convert the TrackSegment to an XML element.

        Args:
            tag: The XML tag name. Defaults to "trkseg".
            nsmap: Optional namespace mapping. Defaults to GPX 1.1 namespace.

        Returns:
            The XML element.

        """
        if nsmap is None:
            nsmap = {None: GPX_NAMESPACE}

        element = etree.Element(tag, nsmap=nsmap)
        build_to_xml(self, element, nsmap=nsmap)

        return element
