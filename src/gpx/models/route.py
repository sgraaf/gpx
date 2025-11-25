"""Route model for GPX data.

This module provides the Route model representing an ordered list of waypoints
representing a series of turn points leading to a destination, following the
GPX 1.1 specification.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

from lxml import etree

from .link import Link  # noqa: TC001
from .utils import build_to_xml, parse_from_xml
from .waypoint import Waypoint  # noqa: TC001

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

#: GPX 1.1 namespace
GPX_NAMESPACE = "http://www.topografix.com/GPX/1/1"


@dataclass(frozen=True)
class Route:
    """An ordered list of waypoints representing a series of turn points.

    A route represents waypoints leading to a destination.

    Args:
        name: GPS name of route. Defaults to None.
        cmt: GPS comment for route. Defaults to None.
        desc: Text description of route for user. Defaults to None.
        src: Source of data. Defaults to None.
        link: Links to external information about the route. Defaults to
            empty list.
        number: GPS route number. Defaults to None.
        type: Type (classification) of route. Defaults to None.
        rtept: List of route points. Defaults to empty list.

    """

    name: str | None = None
    cmt: str | None = None
    desc: str | None = None
    src: str | None = None
    link: list[Link] = field(default_factory=list)
    number: int | None = None
    type: str | None = None
    rtept: list[Waypoint] = field(default_factory=list)

    @classmethod
    def from_xml(cls, element: etree._Element) -> Self:
        """Parse a Route from an XML element.

        Args:
            element: The XML element to parse.

        Returns:
            The parsed Route instance.

        """
        return cls(**parse_from_xml(cls, element))

    def to_xml(
        self, tag: str = "rte", nsmap: dict[str | None, str] | None = None
    ) -> etree._Element:
        """Convert the Route to an XML element.

        Args:
            tag: The XML tag name. Defaults to "rte".
            nsmap: Optional namespace mapping. Defaults to GPX 1.1 namespace.

        Returns:
            The XML element.

        """
        if nsmap is None:
            nsmap = {None: GPX_NAMESPACE}

        element = etree.Element(tag, nsmap=nsmap)
        build_to_xml(self, element, nsmap=nsmap)

        return element
