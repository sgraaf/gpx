"""
This module provides a Route object to contain GPX routes - ordered lists of
waypoints representing a series of turn points leading to a destination.
"""
from __future__ import annotations

from typing import Any

from lxml import etree

from .element import Element
from .link import Link
from .mixins import PointsMutableSequenceMixin, PointsStatisticsMixin
from .waypoint import Waypoint


class Route(Element, PointsMutableSequenceMixin, PointsStatisticsMixin):
    """A route class for the GPX data format.

    A route represents an ordered list of waypoints representing a series of
    turn points leading to a destination.

    Args:
        element: The route XML element. Defaults to `None`.
    """

    def __init__(self, element: etree._Element | None = None) -> None:
        super().__init__(element)

        #: GPS name of route.
        self.name: str | None = None

        #: GPS comment for route.
        self.cmt: str | None = None

        #: Text description of route for user. Not sent to GPS.
        self.desc: str | None = None

        #: Source of data. Included to give user some idea of reliability and
        #: accuracy of data.
        self.src: str | None = None

        #: Links to external information about the route.
        self.links: list[Link] = []

        #: GPS route number.
        self.number: int | None = None

        #: Type (classification) of route.
        self.type: str | None = None

        #: A list of route points.
        self.rtepts: list[Waypoint] = []
        self.points = self.rtepts  #: Alias of :attr:`rtepts`.

        if self._element is not None:
            self._parse()

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
        # GPS route number
        if (number := self._element.find("number", namespaces=self._nsmap)) is not None:
            self.number = int(number.text)
        # track type (classification)
        if (_type := self._element.find("type", namespaces=self._nsmap)) is not None:
            self.type = _type.text

        # route points
        for rtept in self._element.iterfind("rtept", namespaces=self._nsmap):
            self.rtepts.append(Waypoint(rtept))

    def _build(self, tag: str = "rte") -> etree._Element:
        route = super()._build(tag)

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

        for link in self.links:
            route.append(link._build())

        if self.number is not None:
            number = etree.SubElement(route, "number", nsmap=self._nsmap)
            number.text = str(self.number)

        if self.type is not None:
            _type = etree.SubElement(route, "type", nsmap=self._nsmap)
            _type.text = self.type

        for _rtept in self.rtepts:
            route.append(_rtept._build(tag="rtept"))

        return route

    def to_geojson(self) -> dict[str, Any]:
        """Convert the route to a `GeoJSON <https://geojson.org/>`_ `Feature`."""
        # construct the coordinates
        coordinates = []
        for rtept in self.rtepts:
            coordinate = [rtept.lon, rtept.lat]
            if rtept.ele is not None:
                coordinate.append(rtept.ele)
            coordinates.append(coordinate)

        # construct the properties
        properties: dict[str, Any] = {
            "name": self.name,
            "cmt": self.cmt,
            "desc": self.desc,
            "src": self.src,
            "links": [link.to_dict() for link in self.links],
            "number": self.number,
            "type": self.type,
        }

        # filter out `None` values
        properties = {k: v for k, v in properties.items() if v is not None}

        # check for empty links
        if not properties["links"]:
            del properties["links"]

        coordinates_properties = [
            {
                "time": rtept.time,
                "magvar": rtept.magvar,
                "geoidheight": rtept.geoidheight,
                "name": rtept.name,
                "cmt": rtept.cmt,
                "desc": rtept.desc,
                "src": rtept.src,
                "links": [link.to_dict() for link in rtept.links],
                "sym": rtept.sym,
                "type": rtept.type,
                "fix": rtept.fix,
                "sat": rtept.sat,
                "hdop": rtept.hdop,
                "vdop": rtept.vdop,
                "pdop": rtept.pdop,
                "ageofdgpsdata": rtept.ageofdgpsdata,
                "dgpsid": rtept.dgpsid,
            }
            for rtept in self.rtepts
        ]

        # filter out `None` values
        coordinates_properties = [
            {k: v for k, v in coordinate_properties.items() if v is not None}
            for coordinate_properties in coordinates_properties
        ]

        # check for empty links
        for coordinate_properties in coordinates_properties:
            if not coordinate_properties["links"]:
                del coordinate_properties["links"]

        if any(coordinates_properties):
            properties["coordinatesProperties"] = coordinates_properties

        return {
            "type": "Feature",
            "properties": properties,
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates,
            },
        }
