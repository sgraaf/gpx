"""Track model for GPX data.

This module provides the Track model representing an ordered list of points
describing a path, following the GPX 1.1 specification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, overload

from .base import GPXModel
from .link import Link  # noqa: TC001
from .track_segment import TrackSegment  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import Iterator

    from gpx.types import Latitude, Longitude


@dataclass(kw_only=True, slots=True)
class Track(GPXModel):
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
    trkseg: list[TrackSegment] = field(default_factory=list)

    @property
    def segments(self) -> list[TrackSegment]:
        """Alias for trkseg."""
        return self.trkseg

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
    def bounds(self) -> tuple[Latitude, Longitude, Latitude, Longitude]:
        """The bounds of the track."""
        return (
            min(trkpt.lat for trkseg in self.trkseg for trkpt in trkseg),
            min(trkpt.lon for trkseg in self.trkseg for trkpt in trkseg),
            max(trkpt.lat for trkseg in self.trkseg for trkpt in trkseg),
            max(trkpt.lon for trkseg in self.trkseg for trkpt in trkseg),
        )

    @property
    def total_distance(self) -> float:
        """The total distance of the track (in metres)."""
        return sum(trkseg.total_distance for trkseg in self.trkseg)

    @property
    def distance(self) -> float:
        """Alias of :attr:`total_distance`."""
        return self.total_distance

    @property
    def total_duration(self) -> timedelta:
        """The total duration of the track (in seconds)."""
        return sum([trkseg.total_duration for trkseg in self.trkseg], timedelta())

    @property
    def duration(self) -> timedelta:
        """Alias of :attr:`total_duration`."""
        return self.total_duration

    @property
    def moving_duration(self) -> timedelta:
        """The moving duration of the track.

        The moving duration is the total duration with a
        speed greater than 0.5 km/h.
        """
        return sum([trkseg.moving_duration for trkseg in self.trkseg], timedelta())

    @property
    def avg_speed(self) -> float:
        """The average speed of the track (in metres / second)."""
        return self.total_distance / self.total_duration.total_seconds()

    @property
    def speed(self) -> float:
        """Alias of :attr:`avg_speed`."""
        return self.avg_speed

    @property
    def avg_moving_speed(self) -> float:
        """The average moving speed of the track (in metres / second)."""
        return self.total_distance / self.moving_duration.total_seconds()

    @property
    def max_speed(self) -> float:
        """The maximum speed of the track (in metres / second)."""
        return max(trkseg.max_speed for trkseg in self.trkseg)

    @property
    def min_speed(self) -> float:
        """The minimum speed of the track (in metres / second)."""
        return min(trkseg.min_speed for trkseg in self.trkseg)

    @property
    def speed_profile(self) -> list[tuple[datetime, float]]:
        """The speed profile of the track.

        The speed profile is a list of (timestamp, speed) tuples.
        """
        profile = []
        for trkseg in self.trkseg:
            profile += trkseg.speed_profile
        return profile

    @property
    def avg_elevation(self) -> Decimal:
        """The average elevation (in metres)."""
        _eles = [
            trkpt.ele
            for trkseg in self.trkseg
            for trkpt in trkseg
            if trkpt.ele is not None
        ]
        return sum(_eles, Decimal(0)) / len(_eles)

    @property
    def elevation(self) -> Decimal:
        """Alias of :attr:`avg_elevation`."""
        return self.avg_elevation

    @property
    def max_elevation(self) -> Decimal:
        """The maximum elevation of the track (in metres)."""
        return max(trkseg.max_elevation for trkseg in self.trkseg)

    @property
    def min_elevation(self) -> Decimal:
        """The minimum elevation of the track (in metres)."""
        return min(trkseg.min_elevation for trkseg in self.trkseg)

    @property
    def diff_elevation(self) -> Decimal:
        """The difference in elevation of the track (in metres)."""
        return self.max_elevation - self.min_elevation

    @property
    def total_ascent(self) -> Decimal:
        """The total ascent of the track (in metres)."""
        return sum([trkseg.total_ascent for trkseg in self.trkseg], Decimal(0))

    @property
    def total_descent(self) -> Decimal:
        """The total descent of the track (in metres)."""
        return abs(sum([trkseg.total_descent for trkseg in self.trkseg], Decimal(0)))

    @property
    def elevation_profile(self) -> list[tuple[float, Decimal]]:
        """The elevation profile of the track.

        The elevation profile is a list of (distance, elevation) tuples.
        """
        distance = 0.0
        profile = []
        if self.trkseg[0]._points_with_ele[0].ele is not None:
            profile.append((distance, self.trkseg[0]._points_with_ele[0].ele))
        for trkseg in self.trkseg:
            for i, point in enumerate(trkseg._points_with_ele[1:], 1):
                if point.ele is not None:
                    distance += trkseg._points_with_ele[i - 1].distance_to(point)
                    profile.append((distance, point.ele))
        return profile
