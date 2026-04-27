"""This module provides mixin classes."""

from __future__ import annotations

import datetime as dt
from abc import abstractmethod
from decimal import Decimal
from itertools import pairwise
from typing import TYPE_CHECKING, Any

from .utils import build_geo_feature
from .waypoint import Waypoint

if TYPE_CHECKING:
    from .types import Latitude, Longitude
    from .waypoint import Waypoint


class PointsMixin:
    """A mixin class to provide various statistics to an object's `points`.

    Implementing classes must provide ``_points``, returning a flat list of
    waypoints to aggregate over. The mixin intentionally does not define
    ``__iter__``, ``__getitem__`` or ``__len__`` — those depend on the
    semantics of the host class (e.g. ``Track`` iterates segments while
    ``Route`` / ``TrackSegment`` iterate points) and belong on the host.
    """

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

    @property
    def bounds(self) -> tuple[Latitude, Longitude, Latitude, Longitude]:
        """The bounds of the route/track segment."""
        points = self._points
        return (
            min(point.lat for point in points),
            min(point.lon for point in points),
            max(point.lat for point in points),
            max(point.lon for point in points),
        )

    @property
    def total_distance(self) -> float:
        """The total distance (in metres)."""
        return sum(prev.distance_to(point) for prev, point in pairwise(self._points))

    @property
    def total_duration(self) -> dt.timedelta:
        """The total duration."""
        points = self._points
        if len(points) < 2:  # noqa: PLR2004
            return dt.timedelta()
        return points[0].duration_to(points[-1])

    @property
    def moving_duration(self) -> dt.timedelta:
        """The moving duration.

        The moving duration is the total duration with a
        speed greater than 0.5 km/h.
        """
        duration = dt.timedelta()
        for prev, point in pairwise(self._points):
            if prev.speed_to(point) > 0.5 / 3.6:  # 0.5 km/h
                duration += prev.duration_to(point)
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
        return [prev.speed_to(point) for prev, point in pairwise(self._points)]

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
            (prev.time, prev.speed_to(point))
            for prev, point in pairwise(self._points)
            if prev.time is not None
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
        return [prev.gain_to(point) for prev, point in pairwise(self._points_with_ele)]

    @property
    def total_ascent(self) -> Decimal:
        """The total ascent (in metres)."""
        return sum((gain for gain in self._gains if gain > 0), Decimal(0))

    @property
    def total_descent(self) -> Decimal:
        """The total descent (in metres)."""
        return -sum((gain for gain in self._gains if gain < 0), Decimal(0))

    @property
    def elevation_profile(self) -> list[tuple[float, Decimal]]:
        """The elevation profile.

        The elevation profile is a list of (distance, elevation) tuples.
        """
        points = self._points_with_ele
        if not points:
            return []
        profile: list[tuple[float, Decimal]] = []
        distance = 0.0
        if points[0].ele is not None:
            profile.append((distance, points[0].ele))
        for prev, point in pairwise(points):
            if point.ele is not None:
                distance += prev.distance_to(point)
                profile.append((distance, point.ele))
        return profile
