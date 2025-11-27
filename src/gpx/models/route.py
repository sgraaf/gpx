"""Route model for GPX data.

This module provides the Route model representing an ordered list of waypoints
representing a series of turn points leading to a destination, following the
GPX 1.1 specification.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import GPXModel
from .link import Link  # noqa: TC001
from .waypoint import Waypoint  # noqa: TC001


@dataclass(kw_only=True, slots=True)
class Route(GPXModel):
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

    _tag = "rte"

    name: str | None = None
    cmt: str | None = None
    desc: str | None = None
    src: str | None = None
    link: list[Link] = field(default_factory=list)
    number: int | None = None
    type: str | None = None
    rtept: list[Waypoint] = field(default_factory=list)
