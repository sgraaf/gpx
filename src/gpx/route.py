"""Route model for GPX data.

This module provides the Route model representing an ordered list of waypoints
representing a series of turn points leading to a destination, following the
GPX 1.1 specification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, overload

from .base import GPXModel
from .extensions import Extensions  # noqa: TC001
from .link import Link  # noqa: TC001
from .mixins import PointsMixin
from .waypoint import Waypoint  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(kw_only=True, slots=True)
class Route(GPXModel, PointsMixin):
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
        extensions: Extension elements from other XML namespaces. Defaults to None.
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
    extensions: Extensions | None = None
    rtept: list[Waypoint] = field(default_factory=list)

    @property
    def _points(self) -> list[Waypoint]:
        return self.rtept

    @overload
    def __getitem__(self, index: int) -> Waypoint: ...

    @overload
    def __getitem__(self, index: slice) -> list[Waypoint]: ...

    def __getitem__(self, index: int | slice) -> Waypoint | list[Waypoint]:
        """Get a route point by index or slice."""
        return self.rtept[index]

    def __len__(self) -> int:
        """Return the number of route points."""
        return len(self.rtept)

    def __iter__(self) -> Iterator[Waypoint]:
        """Iterate over route points."""
        yield from self.rtept
