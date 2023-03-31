"""This module provides a Route object to contain GPX routes - ordered lists of waypoints representing a series of turn points leading to a destination."""
from __future__ import annotations

from lxml import etree

from ._parsers import parse_links
from .waypoint import Waypoint


class Route:
    """A route class for the GPX data format.

    Args:
        rte: The route XML element. Defaults to `None`.
    """

    def __init__(self, rte: etree._Element | None = None) -> None:
        self._rte: etree._Element = rte
        self._nsmap: dict[str, str] | None = None

        #: GPS name of route.
        self.name: str | None = None

        #: GPS comment for route.
        self.cmt: str | None = None

        #: Text description of route for user. Not sent to GPS.
        self.desc: str | None = None

        #: Source of data. Included to give user some idea of reliability and accuracy of data.
        self.src: str | None = None

        #: Links to external information about the route.
        self.links: list[dict[str, str]] = []

        #: GPS route number.
        self.number: int | None = None

        #: Type (classification) of route.
        self.type: str | None = None

        #: A list of route points.
        self.points: list[Waypoint] = []

        if self._rte is not None:
            self._parse()

    def _parse(self) -> None:
        # namespaces
        self._nsmap = self._rte.nsmap

        # name
        if (name := self._rte.find("name", namespaces=self._nsmap)) is not None:
            self.name = name.text
        # comment
        if (cmt := self._rte.find("cmt", namespaces=self._nsmap)) is not None:
            self.cmt = cmt.text
        # description
        if (desc := self._rte.find("desc", namespaces=self._nsmap)) is not None:
            self.desc = desc.text
        # source of data
        if (src := self._rte.find("src", namespaces=self._nsmap)) is not None:
            self.src = src.text
        # links to additional info
        self.links = parse_links(self._rte)
        # GPS route number
        if (number := self._rte.find("number", namespaces=self._nsmap)) is not None:
            self.number = int(number.text)
        # track type (classification)
        if (_type := self._rte.find("type", namespaces=self._nsmap)) is not None:
            self.type = _type.text

        # route points
        for rtept in self._rte.iterfind("rtept", namespaces=self._nsmap):
            self.points.append(Waypoint(rtept))

    def _build(self) -> etree._Element:  # noqa: C901
        route = etree.Element("rte", nsmap=self._nsmap)

        if self.name is not None:
            name = etree.SubElement(route, "name", nsmap=self._nsmap)
            name.text = self.name

        if self.cmt is not None:
            cmt = etree.SubElement(route, "cmt", nsmap=self._nsmap)
            cmt.text = self.cmt

        if self.desc is not None:
            desc = etree.SubElement(route, "desc", nsmap=self._nsmap)
            desc.text = self.desc

        if self.src is not None:
            src = etree.SubElement(route, "src", nsmap=self._nsmap)
            src.text = self.src

        for _link in self.links:
            link = etree.SubElement(route, "link", nsmap=self._nsmap)
            link.set("href", _link["href"])
            if (tag := "text") in _link:
                text = etree.SubElement(link, tag, nsmap=self._nsmap)
                text.text = _link[tag]
            if (tag := "type") in _link:
                _type = etree.SubElement(link, tag, nsmap=self._nsmap)
                _type.text = _link[tag]

        if self.number is not None:
            number = etree.SubElement(route, "number", nsmap=self._nsmap)
            number.text = self.number

        if self.type is not None:
            _type = etree.SubElement(route, "type", nsmap=self._nsmap)
            _type.text = self.type

        for _rtept in self.points:
            route.append(_rtept._build(tag="rtept"))

        return route

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """Returns the bounds of the route."""
        return (
            min(point.lat for point in self.points),
            min(point.lon for point in self.points),
            max(point.lat for point in self.points),
            max(point.lon for point in self.points),
        )
