"""
This module provides a Track object to contain GPX routes - an ordered list of
points describing a path.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Iterator

from lxml import etree

from .element import Element
from .link import Link
from .track_segment import TrackSegment
from .types import Latitude, Longitude


class Track(Element):
    """A track class for the GPX data format.

    A track represents an ordered list of points describing a path.

    Args:
        element: The track XML element. Defaults to `None`.
    """

    #: GPS name of track.
    name: str | None = None

    #: GPS comment for track.
    cmt: str | None = None

    #: User description of track.
    desc: str | None = None

    #: Source of data. Included to give user some idea of reliability and
    #: accuracy of data.
    src: str | None = None

    #: Links to external information about track.
    links: list[Link] = []

    #: GPS track number.
    number: int | None = None

    #: Type (classification) of track.
    type: str | None = None

    #: A Track Segment holds a list of Track Points which are logically
    #: connected in order. To represent a single GPS track where GPS
    #: reception was lost, or the GPS receiver was turned off, start a new
    #: Track Segment for each continuous span of track data.
    trksegs: list[TrackSegment] = []
    segments = trksegs  #: Alias of :attr:`trksegs`.

    def __getitem__(self, index: int) -> TrackSegment:
        """Returns the track segment at the given index."""
        return self.trksegs[index]

    def __len__(self) -> int:
        """Returns the number of track segments."""
        return len(self.trksegs)

    def __iter__(self) -> Iterator[TrackSegment]:
        """Iterates over the track segments."""
        yield from self.trksegs

    def _parse(self) -> None:
        super()._parse()

        # assertion to satisfy mypy
        assert self._element is not None

        # name
        if (name := self._element.find("name", namespaces=self._nsmap)) is not None:
            self.name = name.text
        # comment
        if (cmt := self._element.find("cmt", namespaces=self._nsmap)) is not None:
            self.cmt = cmt.text
        # description
        if (desc := self._element.find("desc", namespaces=self._nsmap)) is not None:
            self.desc = desc.text
        # source of data
        if (src := self._element.find("src", namespaces=self._nsmap)) is not None:
            self.src = src.text
        # links
        for link in self._element.iterfind("link", namespaces=self._nsmap):
            self.links.append(Link(link))
        # GPS track number
        if (number := self._element.find("number", namespaces=self._nsmap)) is not None:
            self.number = int(number.text)
        # track type (classification)
        if (_type := self._element.find("type", namespaces=self._nsmap)) is not None:
            self.type = _type.text

        # segments
        for trkseg in self._element.iterfind("trkseg", namespaces=self._nsmap):
            self.trksegs.append(TrackSegment(trkseg))

    def _build(self, tag: str = "trk") -> etree._Element:
        track = super()._build(tag)

        if self.name is not None:
            name = etree.SubElement(track, "name", nsmap=self._nsmap)
            name.text = self.name

        if self.cmt is not None:
            cmt = etree.SubElement(track, "cmt", nsmap=self._nsmap)
            cmt.text = self.cmt

        if self.desc is not None:
            desc = etree.SubElement(track, "desc", nsmap=self._nsmap)
            desc.text = self.desc

        if self.src is not None:
            src = etree.SubElement(track, "src", nsmap=self._nsmap)
            src.text = self.src

        for link in self.links:
            track.append(link._build())

        if self.number is not None:
            number = etree.SubElement(track, "number", nsmap=self._nsmap)
            number.text = self.number

        if self.type is not None:
            _type = etree.SubElement(track, "type", nsmap=self._nsmap)
            _type.text = self.type

        for segment in self.trksegs:
            track.append(segment._build())

        return track

    @property
    def bounds(self) -> tuple[Latitude, Longitude, Latitude, Longitude]:
        """The bounds of the track."""
        return (
            min(trkpt.lat for trkseg in self.trksegs for trkpt in trkseg),
            min(trkpt.lon for trkseg in self.trksegs for trkpt in trkseg),
            max(trkpt.lat for trkseg in self.trksegs for trkpt in trkseg),
            max(trkpt.lon for trkseg in self.trksegs for trkpt in trkseg),
        )

    @property
    def distance(self) -> float:
        """The distance of the track (in metres)."""
        return round(sum(trkseg.distance for trkseg in self.trksegs), 2)

    @property
    def duration(self) -> timedelta:
        """The duration of the track (in seconds)."""
        return sum([trkseg.duration for trkseg in self.trksegs], timedelta())
