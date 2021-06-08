"""This module provides a Route object to contain GPX routes - ordered lists of waypoints representing a series of turn points leading to a destination."""
from typing import Dict, List, Optional, Tuple

from lxml import etree

from .waypoint import Waypoint
from ._parsers import parse_links


class Route:
    """A route class for the GPX data format.

    Args:
        rte (etree.Element, optional): The route XML element. Defaults to None.
    """

    def __init__(self, rte: Optional[etree._Element] = None) -> None:
        self._rte: etree._Element = rte
        self._nsmap: Optional[Dict[str, str]] = None
        self.name: Optional[str] = None
        self.cmt: Optional[str] = None
        self.desc: Optional[str] = None
        self.src: Optional[str] = None
        self.links: List[Dict[str, str]] = []
        self.number: Optional[int] = None
        self.type: Optional[str] = None
        self.points: List[Waypoint] = []

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

    def _build(self) -> etree._Element:
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
    def bounds(self) -> Tuple[float, float, float, float]:
        """Returns the bounds of the route."""
        return (
            min(point.lat for point in self.points),
            min(point.lon for point in self.points),
            max(point.lat for point in self.points),
            max(point.lon for point in self.points),
        )
