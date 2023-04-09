"""
This module provides a Track object to contain GPX routes - an ordered list of
points describing a path.
"""
from __future__ import annotations

from lxml import etree

from .element import Element
from .mixins import PointsMutableSequenceMixin, PointsStatisticsMixin
from .waypoint import Waypoint


class TrackSegment(Element, PointsMutableSequenceMixin, PointsStatisticsMixin):
    """A track segment class for the GPX data format.

    A Track Segment holds a list of Track Points which are logically connected
    in order. To represent a single GPS track where GPS reception was lost, or
    the GPS receiver was turned off, start a new Track Segment for each
    continuous span of track data.

    Args:
        element: The track segment XML element. Defaults to `None`.
    """

    def __init__(self, element: etree._Element | None = None) -> None:
        super().__init__(element)

        #: A Track Point holds the coordinates, elevation, timestamp, and
        #: metadata for a single point in a track.
        self.trkpts: list[Waypoint] = []
        self.points = self.trkpts  #: Alias of :attr:`trkpts`.

        if self._element is not None:
            self._parse()

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
