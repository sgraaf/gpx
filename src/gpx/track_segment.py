"""TrackSegment model for GPX data.

This module provides the TrackSegment model representing a list of track points
which are logically connected in order, following the GPX 1.1 specification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any, overload

from .base import GPXModel
from .utils import build_geo_feature
from .waypoint import Waypoint  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import Iterator

    from gpx.types import Latitude, Longitude


@dataclass(kw_only=True, slots=True)
class TrackSegment(GPXModel):
    """A track segment holding a list of logically connected track points.

    A Track Segment holds a list of Track Points which are logically connected
    in order. To represent a single GPS track where GPS reception was lost, or
    the GPS receiver was turned off, start a new Track Segment for each
    continuous span of track data.

    Args:
        trkpt: List of track points. Defaults to empty list.

    """

    _tag = "trkseg"

    trkpt: list[Waypoint] = field(default_factory=list)

    @property
    def points(self) -> list[Waypoint]:
        """Alias for trkpt."""
        return self.trkpt

    @property
    def __geo_interface__(self) -> dict[str, Any]:
        """Return the track segment as a GeoJSON-like LineString geometry.

        Returns:
            A dictionary representing a GeoJSON LineString geometry.

        """
        geometry = {
            "type": "LineString",
            "coordinates": [
                [float(coordinate) for coordinate in point._coordinates]
                for point in self.trkpt
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

        # TrackSegment only has trkpt, so exclude it from properties
        return build_geo_feature(geometry, self, exclude_fields={"trkpt"})

    @overload
    def __getitem__(self, index: int) -> Waypoint: ...

    @overload
    def __getitem__(self, index: slice) -> list[Waypoint]: ...

    def __getitem__(self, index: int | slice) -> Waypoint | list[Waypoint]:
        """Get a track point by index or slice."""
        return self.trkpt[index]

    def __len__(self) -> int:
        """Return the number of track points."""
        return len(self.trkpt)

    def __iter__(self) -> Iterator[Waypoint]:
        """Iterate over track points."""
        yield from self.trkpt

    @property
    def bounds(self) -> tuple[Latitude, Longitude, Latitude, Longitude]:
        """The bounds of the track segment."""
        return (
            min(point.lat for point in self.trkpt),
            min(point.lon for point in self.trkpt),
            max(point.lat for point in self.trkpt),
            max(point.lon for point in self.trkpt),
        )

    @property
    def total_distance(self) -> float:
        """The total distance (in metres)."""
        return sum(
            point.distance_to(self.trkpt[i + 1])
            for i, point in enumerate(self.trkpt[:-1])
        )

    @property
    def distance(self) -> float:
        """Alias of :attr:`total_distance`."""
        return self.total_distance

    @property
    def total_duration(self) -> timedelta:
        """The total duration."""
        if len(self.trkpt) < 2:  # noqa: PLR2004
            return timedelta()
        return self.trkpt[0].duration_to(self.trkpt[-1])

    @property
    def duration(self) -> timedelta:
        """Alias of :attr:`total_duration`."""
        return self.total_duration

    @property
    def moving_duration(self) -> timedelta:
        """The moving duration.

        The moving duration is the total duration with a
        speed greater than 0.5 km/h.
        """
        duration = timedelta()
        for i, point in enumerate(self.trkpt[:-1]):
            if point.speed_to(self.trkpt[i + 1]) > 0.5 / 3.6:  # 0.5 km/h
                duration += point.duration_to(self.trkpt[i + 1])
        return duration

    @property
    def avg_speed(self) -> float:
        """The average speed (in metres / second)."""
        return (
            self.total_distance / self.total_duration.total_seconds()
            if self.total_duration
            else 0.0
        )

    @property
    def speed(self) -> float:
        """Alias of :attr:`avg_speed`."""
        return self.avg_speed

    @property
    def avg_moving_speed(self) -> float:
        """The average moving speed (in metres / second)."""
        return (
            self.total_distance / self.moving_duration.total_seconds()
            if self.moving_duration
            else 0.0
        )

    @property
    def _speeds(self) -> list[float]:
        return [
            point.speed_to(self.trkpt[i + 1]) for i, point in enumerate(self.trkpt[:-1])
        ]

    @property
    def max_speed(self) -> float:
        """The maximum speed (in metres / second)."""
        return max(self._speeds)

    @property
    def min_speed(self) -> float:
        """The minimum speed (in metres / second)."""
        return min(self._speeds)

    @property
    def speed_profile(self) -> list[tuple[datetime, float]]:
        """The speed profile.

        The speed profile is a list of (timestamp, speed) tuples.
        """
        return [
            (point.time, point.speed_to(self.trkpt[i + 1]))
            for i, point in enumerate(self.trkpt[:-1])
            if point.time is not None
        ]

    @property
    def _points_with_ele(self) -> list[Waypoint]:
        return [point for point in self.trkpt if point.ele is not None]

    @property
    def _eles(self) -> list[Decimal]:
        return [point.ele for point in self.trkpt if point.ele is not None]

    @property
    def avg_elevation(self) -> Decimal:
        """The average elevation (in metres)."""
        return sum(self._eles, Decimal(0)) / len(self._eles)

    @property
    def elevation(self) -> Decimal:
        """Alias of :attr:`avg_elevation`."""
        return self.avg_elevation

    @property
    def max_elevation(self) -> Decimal:
        """The maximum elevation (in metres)."""
        return max(self._eles)

    @property
    def min_elevation(self) -> Decimal:
        """The minimum elevation (in metres)."""
        return min(self._eles)

    @property
    def diff_elevation(self) -> Decimal:
        """The difference in elevation (in metres)."""
        return self.max_elevation - self.min_elevation

    @property
    def _gains(self) -> list[Decimal]:
        return [
            point.gain_to(self._points_with_ele[i + 1])
            for i, point in enumerate(self._points_with_ele[:-1])
        ]

    @property
    def total_ascent(self) -> Decimal:
        """The total ascent (in metres)."""
        return sum((gain for gain in self._gains if gain > 0), Decimal(0))

    @property
    def total_descent(self) -> Decimal:
        """The total descent (in metres)."""
        return abs(sum((gain for gain in self._gains if gain < 0), Decimal(0)))

    @property
    def elevation_profile(self) -> list[tuple[float, Decimal]]:
        """The elevation profile.

        The elevation profile is a list of (distance, elevation) tuples.
        """
        distance = 0.0
        profile = []
        if self._points_with_ele[0].ele is not None:
            profile.append((distance, self._points_with_ele[0].ele))
        for i, point in enumerate(self._points_with_ele[1:], 1):
            if point.ele is not None:
                distance += self._points_with_ele[i - 1].distance_to(point)
                profile.append((distance, point.ele))
        return profile
