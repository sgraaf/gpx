"""This module provides a Person object to contain a person or organization."""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, overload

from .waypoint import Waypoint

if TYPE_CHECKING:
    from .types import Latitude, Longitude


class AttributesMutableMappingMixin(MutableMapping):
    """A mixin class to provide a `MutableMapping` interface to an object's defined attributes."""

    #: A tuple of attribute names that are to be treated as keys.
    __keys__: tuple[str, ...]

    def __getitem__(self, key: str) -> object | None:
        if key not in self.__keys__:
            msg = f"Key not found: {key}"
            raise KeyError(msg)
        return getattr(self, key)

    def __setitem__(self, key: str, value: object | None) -> None:
        if key not in self.__keys__:
            msg = f"Key not found: {key}"
            raise KeyError(msg)
        setattr(self, key, value)

    def __delitem__(self, key: str) -> None:
        if key not in self.__keys__:
            msg = f"Key not found: {key}"
            raise KeyError(msg)
        setattr(self, key, None)

    def __iter__(self) -> Iterator[str]:
        return iter(self.__keys__)

    def __len__(self) -> int:
        return len(self.__keys__)


class PointsSequenceMixin(Sequence):
    """A mixin class to provide a `Sequence` interface to an object's `points`."""

    #: A list of points.
    points: list[Waypoint]

    @overload
    def __getitem__(self, index: int) -> Waypoint: ...

    @overload
    def __getitem__(self, index: slice) -> MutableSequence[Waypoint]: ...

    def __getitem__(self, index: int | slice) -> Waypoint | MutableSequence[Waypoint]:
        return self.points[index]

    def __iter__(self) -> Iterator[Waypoint]:
        yield from self.points

    def __len__(self) -> int:
        return len(self.points)


class PointsMutableSequenceMixin(PointsSequenceMixin, MutableSequence):
    """A mixin class to provide a `MutableSequence` interface to an object's `points`."""

    @overload
    def __setitem__(self, index: int, value: Waypoint) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[Waypoint]) -> None: ...

    def __setitem__(
        self,
        index: int | slice,
        value: Waypoint | Iterable[Waypoint],
    ) -> None:
        if isinstance(index, int) and isinstance(value, Waypoint):
            self.points[index] = value
            return
        if isinstance(index, slice) and isinstance(value, Iterable):
            self.points[index] = value
            return
        msg = "Invalid type of index or value."
        raise TypeError(msg)

    @overload
    def __delitem__(self, index: int) -> None: ...

    @overload
    def __delitem__(self, index: slice) -> None: ...

    def __delitem__(self, index: int | slice) -> None:
        del self.points[index]

    def insert(self, index: int, value: Waypoint) -> None:
        self.points.insert(index, value)


class PointsStatisticsMixin:
    """A mixin class to provide various statistics to an object's `points`."""

    #: A list of points.
    points: list[Waypoint]

    @property
    def bounds(self) -> tuple[Latitude, Longitude, Latitude, Longitude]:
        """The bounds."""
        return (
            min(point.lat for point in self.points),
            min(point.lon for point in self.points),
            max(point.lat for point in self.points),
            max(point.lon for point in self.points),
        )

    @property
    def total_distance(self) -> float:
        """The total distance (in metres)."""
        return sum(
            point.distance_to(self.points[i + 1])
            for i, point in enumerate(self.points[:-1])
        )

    distance = total_distance  #: Alias of :attr:`total_distance`.

    @property
    def total_duration(self) -> timedelta:
        """The total duration."""
        return self.points[0].duration_to(self.points[-1])

    duration = total_duration  #: Alias of :attr:`total_duration`.

    @property
    def moving_duration(self) -> timedelta:
        """The moving duration.

        The moving duration is the total duration with a
        speed greater than 0.5 km/h.
        """
        duration = timedelta()
        for i, point in enumerate(self.points[:-1]):
            if point.speed_to(self.points[i + 1]) > 0.5 / 3.6:  # 0.5 km/h
                duration += point.duration_to(self.points[i + 1])
        return duration

    @property
    def avg_speed(self) -> float:
        """The average speed (in metres / second)."""
        return self.total_distance / self.total_duration.total_seconds()

    speed = avg_speed  #: Alias of :attr:`avg_speed`.

    @property
    def avg_moving_speed(self) -> float:
        """The average moving speed (in metres / second)."""
        return self.total_distance / self.moving_duration.total_seconds()

    @property
    def _speeds(self) -> list[float]:
        return [
            point.speed_to(self.points[i + 1])
            for i, point in enumerate(self.points[:-1])
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
            (point.time, point.speed_to(self.points[i + 1]))
            for i, point in enumerate(self.points[:-1])
            if point.time is not None
        ]

    @property
    def _points_with_ele(self) -> list[Waypoint]:
        return [point for point in self.points if point.ele is not None]

    @property
    def _eles(self) -> list[Decimal]:
        return [point.ele for point in self.points if point.ele is not None]

    @property
    def avg_elevation(self) -> Decimal:
        """The average elevation (in metres)."""
        return sum(self._eles, Decimal(0)) / len(self._eles)

    elevation = avg_elevation  #: Alias of :attr:`avg_elevation`.

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
        return sum([gain for gain in self._gains if gain > 0], Decimal(0))

    @property
    def total_descent(self) -> Decimal:
        """The total descent (in metres)."""
        return abs(sum([gain for gain in self._gains if gain < 0], Decimal(0)))

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
