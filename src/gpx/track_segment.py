"""
This module provides a Track object to contain GPX routes - an ordered list of
points describing a path.
"""
from __future__ import annotations

from datetime import timedelta

from lxml import etree

from .element import Element
from .mixins import PointsMutableSequenceMixin
from .types import Latitude, Longitude
from .waypoint import Waypoint


class TrackSegment(Element, PointsMutableSequenceMixin):
    """A track segment class for the GPX data format.

    A Track Segment holds a list of Track Points which are logically connected
    in order. To represent a single GPS track where GPS reception was lost, or
    the GPS receiver was turned off, start a new Track Segment for each
    continuous span of track data.

    Args:
        element: The track segment XML element. Defaults to `None`.
    """

    #: A Track Point holds the coordinates, elevation, timestamp, and
    #: metadata for a single point in a track.
    trkpts: list[Waypoint] = []
    points = trkpts  #: Alias of :attr:`trkpts`.

    def _parse(self) -> None:
        super()._parse()

        # assertion to satisfy mypy
        assert self._element is not None

        # track points
        for trkpt in self._element.iterfind("trkpt", namespaces=self._nsmap):
            self.trkpts.append(Waypoint(trkpt))

    def _build(self, tag: str = "trkseg") -> etree._Element:
        track_segment = super()._build(tag)

        for _trkpt in self.trkpts:
            track_segment.append(_trkpt._build(tag="trkpt"))

        return track_segment

    @property
    def bounds(self) -> tuple[Latitude, Longitude, Latitude, Longitude]:
        """The bounds of the track segment."""
        return (
            min(point.lat for point in self.trkpts),
            min(point.lon for point in self.trkpts),
            max(point.lat for point in self.trkpts),
            max(point.lon for point in self.trkpts),
        )

    @property
    def distance(self) -> float:
        """The distance of the track segment (in metres)."""
        _distance = 0.0
        for i, point in enumerate(self.trkpts[:-1]):
            _distance += point.distance_to(self.trkpts[i + 1])
        return round(_distance, 2)

    @property
    def duration(self) -> timedelta:
        """The total duration of the track segment."""
        _duration = timedelta()
        for i, point in enumerate(self.trkpts[:-1]):
            _duration += point.duration_to(self.trkpts[i + 1])
        return _duration
