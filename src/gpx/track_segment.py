"""TrackSegment model for GPX data.

This module provides the TrackSegment model representing a list of track points
which are logically connected in order, following the GPX 1.1 specification.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import GPXModel
from .extensions import Extensions  # noqa: TC001
from .mixins import PointsMixin
from .waypoint import Waypoint  # noqa: TC001


@dataclass(kw_only=True, slots=True)
class TrackSegment(GPXModel, PointsMixin):
    """A track segment holding a list of logically connected track points.

    A Track Segment holds a list of Track Points which are logically connected
    in order. To represent a single GPS track where GPS reception was lost, or
    the GPS receiver was turned off, start a new Track Segment for each
    continuous span of track data.

    Args:
        trkpt: List of track points. Defaults to empty list.
        extensions: Extension elements from other XML namespaces. Defaults to None.

    """

    _tag = "trkseg"

    trkpt: list[Waypoint] = field(default_factory=list)
    extensions: Extensions | None = None

    @property
    def _points(self) -> list[Waypoint]:
        return self.trkpt
