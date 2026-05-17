"""Track model for GPX data.

This module provides the Track model representing an ordered list of points
describing a path, following the GPX 1.1 specification.
"""

from __future__ import annotations

import datetime as dt
import itertools
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING, Any, overload

from .base import GeoGPXModel
from .extensions import Extensions  # noqa: TC001
from .link import Link  # noqa: TC001
from .mixins import PointsMixin
from .track_segment import TrackSegment  # noqa: TC001
from .utils import build_geo_feature

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .waypoint import Waypoint


@dataclass(kw_only=True, slots=True)
class Track(PointsMixin, GeoGPXModel):
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
        extensions: Extension elements from other XML namespaces. Defaults to None.
        trkseg: List of track segments. Defaults to empty list.

    """

    _tag = "trk"

    name: str | None = None
    cmt: str | None = None
    desc: str | None = None
    src: str | None = None
    link: list[Link] = field(default_factory=list)
    number: int | None = None
    type: str | None = None
    extensions: Extensions | None = None
    trkseg: list[TrackSegment] = field(default_factory=list)

    @property
    def _points(self) -> list[Waypoint]:
        """All track points across all segments, flattened."""
        return [trkpt for trkseg in self.trkseg for trkpt in trkseg.trkpt]

    @property
    def __geo_interface__(self) -> dict[str, Any]:
        """Return the track as a GeoJSON-like MultiLineString geometry or Feature.

        Returns a Feature if any optional fields are set, otherwise returns
        a pure MultiLineString geometry.

        Returns:
            A dictionary representing either a GeoJSON MultiLineString geometry or Feature.

        """
        # Build MultiLineString coordinates from all segments
        geometry = {
            "type": "MultiLineString",
            "coordinates": [
                [
                    [float(coordinate) for coordinate in trkpt._coordinates]
                    for trkpt in trkseg.trkpt
                ]
                for trkseg in self.trkseg
            ],
            "bbox": [
                float(self.bounds[1]),
                float(self.bounds[0]),
                float(self.min_elevation),
                float(self.bounds[3]),
                float(self.bounds[2]),
                float(self.max_elevation),
            ]
            if self._eles
            else [
                float(self.bounds[1]),
                float(self.bounds[0]),
                float(self.bounds[3]),
                float(self.bounds[2]),
            ],
        }

        # Exclude geometry fields from properties
        return build_geo_feature(geometry, self, exclude_fields={"trkseg"})

    @overload
    def __getitem__(self, index: int) -> TrackSegment: ...

    @overload
    def __getitem__(self, index: slice) -> list[TrackSegment]: ...

    def __getitem__(self, index: int | slice) -> TrackSegment | list[TrackSegment]:
        """Get a track segment by index or slice."""
        return self.trkseg[index]

    def __len__(self) -> int:
        """Return the number of track segments."""
        return len(self.trkseg)

    def __iter__(self) -> Iterator[TrackSegment]:
        """Iterate over track segments."""
        yield from self.trkseg

    @property
    def total_distance(self) -> float:
        """The total distance of the track (in metres)."""
        return sum(trkseg.total_distance for trkseg in self.trkseg)

    @property
    def total_duration(self) -> dt.timedelta:
        """The total duration of the track (in seconds)."""
        return sum((trkseg.total_duration for trkseg in self.trkseg), dt.timedelta())

    @property
    def moving_duration(self) -> dt.timedelta:
        """The moving duration of the track.

        The moving duration is the total duration with a
        speed greater than 0.5 km/h.
        """
        return sum((trkseg.moving_duration for trkseg in self.trkseg), dt.timedelta())

    @property
    def max_speed(self) -> float:
        """The maximum speed of the track (in metres / second)."""
        return max(trkseg.max_speed for trkseg in self.trkseg)

    @property
    def min_speed(self) -> float:
        """The minimum speed of the track (in metres / second)."""
        return min(trkseg.min_speed for trkseg in self.trkseg)

    @property
    def speed_profile(self) -> list[tuple[dt.datetime, float]]:
        """The speed profile of the track.

        The speed profile is a list of (timestamp, speed) tuples.
        """
        return [entry for trkseg in self.trkseg for entry in trkseg.speed_profile]

    @property
    def total_ascent(self) -> Decimal:
        """The total ascent of the track (in metres)."""
        return sum((trkseg.total_ascent for trkseg in self.trkseg), Decimal(0))

    @property
    def total_descent(self) -> Decimal:
        """The total descent of the track (in metres)."""
        return sum((trkseg.total_descent for trkseg in self.trkseg), Decimal(0))

    @property
    def elevation_profile(self) -> list[tuple[float, Decimal]]:
        """The elevation profile of the track.

        The elevation profile is a list of (distance, elevation) tuples.
        Distance accumulates within each segment but does not include the gap
        between consecutive segments.
        """
        profile: list[tuple[float, Decimal]] = []
        distance = 0.0
        for trkseg in self.trkseg:
            points = trkseg._points_with_ele
            if not points:
                continue
            if points[0].ele is not None:
                profile.append((distance, points[0].ele))
            for prev, point in itertools.pairwise(points):
                if point.ele is not None:
                    distance += prev.distance_to(point)
                    profile.append((distance, point.ele))
        return profile
