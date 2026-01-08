"""This module provides mixin classes."""

from __future__ import annotations

import datetime as dt
from abc import abstractmethod
from decimal import Decimal
from typing import TYPE_CHECKING, Any, overload

from .utils import build_geo_feature
from .waypoint import Waypoint

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .types import Latitude, Longitude
    from .waypoint import Waypoint


class PointsMixin:
    """A mixin class to provide various statistics to an object's `points`."""

    @property
    @abstractmethod
    def _points(self) -> list[Waypoint]: ...

    @property
    def __geo_interface__(self) -> dict[str, Any]:
        """Return the route/track segment as a GeoJSON-like LineString geometry or Feature.

        Returns a Feature if any optional fields are set, otherwise returns
        a pure LineString geometry.

        Returns:
            A dictionary representing either a GeoJSON LineString geometry or Feature.

        """
        # Build LineString coordinates from all route/track segment points
        geometry = {
            "type": "LineString",
            "coordinates": [
                [float(coordinate) for coordinate in point._coordinates]
                for point in self._points
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
        return build_geo_feature(geometry, self, exclude_fields={"rtept", "trkpt"})

    @overload
    def __getitem__(self, index: int) -> Waypoint: ...

    @overload
    def __getitem__(self, index: slice) -> list[Waypoint]: ...

    def __getitem__(self, index: int | slice) -> Waypoint | list[Waypoint]:
        """Get a route/track segment point by index or slice."""
        return self._points[index]

    def __len__(self) -> int:
        """Return the number of route/track segment points."""
        return len(self._points)

    def __iter__(self) -> Iterator[Waypoint]:
        """Iterate over route/track segment points."""
        yield from self._points

    @property
    def bounds(self) -> tuple[Latitude, Longitude, Latitude, Longitude]:
        """The bounds of the route/track segment."""
        return (
            min(point.lat for point in self._points),
            min(point.lon for point in self._points),
            max(point.lat for point in self._points),
            max(point.lon for point in self._points),
        )

    @property
    def total_distance(self) -> float:
        """The total distance (in metres)."""
        return sum(
            point.distance_to(self._points[i + 1])
            for i, point in enumerate(self._points[:-1])
        )

    @property
    def total_duration(self) -> dt.timedelta:
        """The total duration."""
        if len(self._points) < 2:  # noqa: PLR2004
            return dt.timedelta()
        return self._points[0].duration_to(self._points[-1])

    @property
    def moving_duration(self) -> dt.timedelta:
        """The moving duration.

        The moving duration is the total duration with a
        speed greater than 0.5 km/h.
        """
        duration = dt.timedelta()
        for i, point in enumerate(self._points[:-1]):
            if point.speed_to(self._points[i + 1]) > 0.5 / 3.6:  # 0.5 km/h
                duration += point.duration_to(self._points[i + 1])
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
            point.speed_to(self._points[i + 1])
            for i, point in enumerate(self._points[:-1])
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
    def speed_profile(self) -> list[tuple[dt.datetime, float]]:
        """The speed profile.

        The speed profile is a list of (timestamp, speed) tuples.
        """
        return [
            (point.time, point.speed_to(self._points[i + 1]))
            for i, point in enumerate(self._points[:-1])
            if point.time is not None
        ]

    @property
    def _points_with_ele(self) -> list[Waypoint]:
        return [point for point in self._points if point.ele is not None]

    @property
    def _eles(self) -> list[Decimal]:
        return [point.ele for point in self._points if point.ele is not None]

    @property
    def avg_elevation(self) -> Decimal:
        """The average elevation (in metres)."""
        return sum(self._eles, Decimal(0)) / len(self._eles)

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
