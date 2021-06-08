"""This module provides a Wapoint object to contain GPX waypoints."""
from __future__ import annotations

import datetime
from math import atan2, cos, radians, sin, sqrt
from typing import Dict, List, Optional

from dateutil.parser import isoparse
from lxml import etree

from ._parsers import parse_links


class Waypoint:
    """A waypoint class for the GPX data format.

    Args:
        wpt (etree.Element, optional): The waypoint XML element. Defaults to None.
    """

    def __init__(self, wpt: Optional[etree._Element] = None) -> None:
        self._wpt: etree._Element = wpt
        self._nsmap: Optional[Dict[str, str]] = None
        self.lat: float
        self.lon: float
        self.ele: Optional[float] = None
        self.time: Optional[datetime.datetime] = None
        self.magvar: Optional[float] = None
        self.geoidheight: Optional[float] = None
        self.name: Optional[str] = None
        self.cmt: Optional[str] = None
        self.desc: Optional[str] = None
        self.src: Optional[str] = None
        self.links: List[Dict[str, str]] = []
        self.sym: Optional[str] = None
        self.type: Optional[str] = None
        self.fix: Optional[str] = None
        self.sat: Optional[int] = None
        self.hdop: Optional[float] = None
        self.vdop: Optional[float] = None
        self.pdop: Optional[float] = None
        self.ageofdgpsdata: Optional[float] = None
        self.dgpsid: Optional[int] = None

        if self._wpt is not None:
            self._parse()

    def _parse(self) -> None:
        # namespaces
        self._nsmap = self._wpt.nsmap

        # required
        self.lat = float(self._wpt.get("lat"))
        self.lon = float(self._wpt.get("lon"))

        # position info
        # elevation
        if (ele := self._wpt.find("ele", namespaces=self._nsmap)) is not None:
            self.ele = float(ele.text)
        # time
        if (time := self._wpt.find("time", namespaces=self._nsmap)) is not None:
            self.time = isoparse(time.text)
        # magnetic variation
        if (magvar := self._wpt.find("magvar", namespaces=self._nsmap)) is not None:
            self.magvar = float(magvar.text)
        # geoid height
        if (
            geoidheight := self._wpt.find("geoidheight", namespaces=self._nsmap)
        ) is not None:
            self.geoidheight = float(geoidheight.text)

        # description info
        # name
        if (name := self._wpt.find("name", namespaces=self._nsmap)) is not None:
            self.name = name.text
        # comment
        if (cmt := self._wpt.find("cmt", namespaces=self._nsmap)) is not None:
            self.cmt = cmt.text
        # description
        if (desc := self._wpt.find("desc", namespaces=self._nsmap)) is not None:
            self.desc = desc.text
        # source of data
        if (src := self._wpt.find("src", namespaces=self._nsmap)) is not None:
            self.src = src.text
        # links to additional info
        self.links = parse_links(self._wpt)
        # GPS symbol name
        if (sym := self._wpt.find("sym", namespaces=self._nsmap)) is not None:
            self.sym = sym.text
        # waypoint type (classification)
        if (_type := self._wpt.find("type", namespaces=self._nsmap)) is not None:
            self.type = _type.text

        # accuracy info
        # GPX fix type
        if (fix := self._wpt.find("fix", namespaces=self._nsmap)) is not None:
            self.fix = fix.text
        # number of satellites used to calculate the GPX fix
        if (sat := self._wpt.find("sat", namespaces=self._nsmap)) is not None:
            self.sat = int(sat.text)
        # horizontal dilution of precision
        if (hdop := self._wpt.find("hdop", namespaces=self._nsmap)) is not None:
            self.hdop = float(hdop.text)
        # vertical dilution of precision
        if (vdop := self._wpt.find("vdop", namespaces=self._nsmap)) is not None:
            self.vdop = float(vdop.text)
        # position dilution of precision
        if (pdop := self._wpt.find("pdop", namespaces=self._nsmap)) is not None:
            self.pdop = float(pdop.text)
        # number of seconds since last DGPS update
        if (
            ageofdgpsdata := self._wpt.find("ageofdgpsdata", namespaces=self._nsmap)
        ) is not None:
            self.ageofdgpsdata = float(ageofdgpsdata.text)
        # DGPS station id used in differential correction
        if (dgpsid := self._wpt.find("dgpsid", namespaces=self._nsmap)) is not None:
            self.dgpsid = int(dgpsid.text)

    def _build(self, tag: Optional[str] = "wpt") -> etree._Element:
        waypoint = etree.Element(tag, nsmap=self._nsmap)
        waypoint.set("lat", str(self.lat))
        waypoint.set("lon", str(self.lon))

        if self.ele is not None:
            ele = etree.SubElement(waypoint, "ele", nsmap=self._nsmap)
            ele.text = str(self.ele)

        if self.time is not None:
            time = etree.SubElement(waypoint, "time", nsmap=self._nsmap)
            time.text = self.time.isoformat().replace("+00:00", "Z")

        if self.magvar is not None:
            magvar = etree.SubElement(waypoint, "magvar", nsmap=self._nsmap)
            magvar.text = str(self.magvar)

        if self.geoidheight is not None:
            geoidheight = etree.SubElement(waypoint, "geoidheight", nsmap=self._nsmap)
            geoidheight.text = str(self.geoidheight)

        if self.name is not None:
            name = etree.SubElement(waypoint, "name", nsmap=self._nsmap)
            name.text = self.name

        if self.cmt is not None:
            cmt = etree.SubElement(waypoint, "cmt", nsmap=self._nsmap)
            cmt.text = self.cmt

        if self.desc is not None:
            desc = etree.SubElement(waypoint, "desc", nsmap=self._nsmap)
            desc.text = self.desc

        if self.src is not None:
            src = etree.SubElement(waypoint, "src", nsmap=self._nsmap)
            src.text = self.src

        for _link in self.links:
            link = etree.SubElement(waypoint, "link", nsmap=self._nsmap)
            link.set("href", _link["href"])
            if (tag := "text") in _link:
                text = etree.SubElement(link, tag, nsmap=self._nsmap)
                text.text = _link[tag]
            if (tag := "type") in _link:
                _type = etree.SubElement(link, tag, nsmap=self._nsmap)
                _type.text = _link[tag]

        if self.sym is not None:
            sym = etree.SubElement(waypoint, "sym", nsmap=self._nsmap)
            sym.text = self.sym

        if self.type is not None:
            _type = etree.SubElement(waypoint, "type", nsmap=self._nsmap)
            _type.text = self.type

        if self.fix is not None:
            fix = etree.SubElement(waypoint, "fix", nsmap=self._nsmap)
            fix.text = self.fix

        if self.sat is not None:
            sat = etree.SubElement(waypoint, "sat", nsmap=self._nsmap)
            sat.text = str(self.sat)

        if self.hdop is not None:
            hdop = etree.SubElement(waypoint, "hdop", nsmap=self._nsmap)
            hdop.text = str(self.hdop)

        if self.vdop is not None:
            vdop = etree.SubElement(waypoint, "vdop", nsmap=self._nsmap)
            vdop.text = str(self.vdop)

        if self.pdop is not None:
            pdop = etree.SubElement(waypoint, "pdop", nsmap=self._nsmap)
            pdop.text = str(self.pdop)

        if self.ageofdgpsdata is not None:
            ageofdgpsdata = etree.SubElement(
                waypoint, "ageofdgpsdata", nsmap=self._nsmap
            )
            ageofdgpsdata.text = str(self.ageofdgpsdata)

        if self.dgpsid is not None:
            dgpsid = etree.SubElement(waypoint, "dgpsid", nsmap=self._nsmap)
            dgpsid.text = str(self.dgpsid)

        return waypoint

    def distance_to(self, other: Waypoint, radius: int = 6_378_137) -> float:
        """Returns the distance to the other waypoint (in metres) using a simple spherical earth model.

        Adapted from: https://github.com/chrisveness/geodesy/blob/33d1bf53c069cd7dd83c6bf8531f5f3e0955c16e/latlon-spherical.js#L187
        """
        R = radius
        φ1, λ1 = radians(self.lat), radians(self.lon)
        φ2, λ2 = radians(other.lat), radians(other.lon)
        Δφ = φ2 - φ1
        Δλ = λ2 - λ1
        a = sin(Δφ / 2) * sin(Δφ / 2) + cos(φ1) * cos(φ2) * sin(Δλ / 2) * sin(Δλ / 2)
        δ = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * δ

    def duration_to(self, other: Waypoint) -> float:
        """Returns the duration to the other waypoint (in seconds)."""
        if self.time is None or other.time is None:
            return 0
        return (other.time - self.time).total_seconds()
