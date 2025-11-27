"""Track model for GPX data.

This module provides the Track model representing an ordered list of points
describing a path, following the GPX 1.1 specification.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import GPXModel
from .link import Link  # noqa: TC001
from .track_segment import TrackSegment  # noqa: TC001


@dataclass(frozen=True)
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
