"""This module provides a Waypoint object to contain GPX waypoints."""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from math import atan2, cos, radians, sin, sqrt

from dateutil.parser import isoparse
from lxml import etree

from .element import Element
from .link import Link
from .types import Degrees, DGPSStation, Fix, Latitude, Longitude


class Waypoint(Element):
    """A waypoint class for the GPX data format.

    A waypoint represents a waypoint, point of interest, or named feature on a
    map.

    Args:
        element: The waypoint XML element. Defaults to `None`.
    """

    #: The latitude of the point. Decimal degrees, WGS84 datum.
    lat: Latitude

    #: The longitude of the point. Decimal degrees, WGS84 datum.
    lon: Longitude

    #: Elevation (in meters) of the point.
    ele: Decimal | None = None

    #: Creation/modification timestamp for element. Date and time in are in
    #: Universal Coordinated Time (UTC), not local time! Conforms to ISO 8601
    #: specification for date/time representation. Fractional seconds are
    #: allowed for millisecond timing in tracklogs.
    time: datetime | None = None

    #: Magnetic variation (in degrees) at the point
    magvar: Degrees | None = None

    #: Height (in meters) of geoid (mean sea level) above WGS84 earth
    #: ellipsoid. As defined in NMEA GGA message.
    geoidheight: Decimal | None = None

    #: The GPS name of the waypoint. This field will be transferred to and
    #: from the GPS. GPX does not place restrictions on the length of this
    #: field or the characters contained in it. It is up to the receiving
    #: application to validate the field before sending it to the GPS.
    name: str | None = None

    #: GPS waypoint comment. Sent to GPS as comment.
    cmt: str | None = None

    #: A text description of the element. Holds additional information about
    #: the element intended for the user, not the GPS.
    desc: str | None = None

    #: Source of data. Included to give user some idea of reliability and
    #: accuracy of data. "Garmin eTrex", "USGS quad Boston North", e.g.
    src: str | None = None

    #: Link to additional information about the waypoint.
    links: list[Link] = []

    #: Text of GPS symbol name. For interchange with other programs, use the
    #: exact spelling of the symbol as displayed on the GPS. If the GPS
    #: abbreviates words, spell them out.
    sym: str | None = None

    #: Type (classification) of the waypoint.
    type: str | None = None

    #: Type of GPX fix.
    fix: Fix | None = None

    #: Number of satellites used to calculate the GPX fix.
    sat: int | None = None

    #: Horizontal dilution of precision.
    hdop: Decimal | None = None

    #: Vertical dilution of precision.
    vdop: Decimal | None = None

    #: Position dilution of precision.
    pdop: Decimal | None = None

    #: Number of seconds since last DGPS update.
    ageofdgpsdata: Decimal | None = None

    #: ID of DGPS station used in differential correction.
    dgpsid: DGPSStation | None = None

    def _parse(self) -> None:  # noqa: C901
        super()._parse()

        # assertion to satisfy mypy
        assert self._element is not None

        # required
        self.lat = Latitude(self._element.get("lat"))
        self.lon = Longitude(self._element.get("lon"))

        # position info
        # elevation
        if (ele := self._element.find("ele", namespaces=self._nsmap)) is not None:
            self.ele = Decimal(ele.text)
        # time
        if (time := self._element.find("time", namespaces=self._nsmap)) is not None:
            self.time = isoparse(time.text)
        # magnetic variation
        if (magvar := self._element.find("magvar", namespaces=self._nsmap)) is not None:
            self.magvar = Degrees(magvar.text)
        # geoid height
        if (
            geoidheight := self._element.find("geoidheight", namespaces=self._nsmap)
        ) is not None:
            self.geoidheight = Decimal(geoidheight.text)

        # description info
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
        # GPS symbol name
        if (sym := self._element.find("sym", namespaces=self._nsmap)) is not None:
            self.sym = sym.text
        # waypoint type (classification)
        if (_type := self._element.find("type", namespaces=self._nsmap)) is not None:
            self.type = _type.text

        # accuracy info
        # GPX fix type
        if (fix := self._element.find("fix", namespaces=self._nsmap)) is not None:
            self.fix = Fix(fix.text)
        # number of satellites used to calculate the GPX fix
        if (sat := self._element.find("sat", namespaces=self._nsmap)) is not None:
            self.sat = int(sat.text)
        # horizontal dilution of precision
        if (hdop := self._element.find("hdop", namespaces=self._nsmap)) is not None:
            self.hdop = Decimal(hdop.text)
        # vertical dilution of precision
        if (vdop := self._element.find("vdop", namespaces=self._nsmap)) is not None:
            self.vdop = Decimal(vdop.text)
        # position dilution of precision
        if (pdop := self._element.find("pdop", namespaces=self._nsmap)) is not None:
            self.pdop = Decimal(pdop.text)
        # number of seconds since last DGPS update
        if (
            ageofdgpsdata := self._element.find("ageofdgpsdata", namespaces=self._nsmap)
        ) is not None:
            self.ageofdgpsdata = Decimal(ageofdgpsdata.text)
        # DGPS station id used in differential correction
        if (dgpsid := self._element.find("dgpsid", namespaces=self._nsmap)) is not None:
            self.dgpsid = DGPSStation(dgpsid.text)

    def _build(self, tag: str = "wpt") -> etree._Element:  # noqa: C901
        waypoint = super()._build(tag)
        waypoint.set("lat", str(self.lat))
        waypoint.set("lon", str(self.lon))

        if self.ele is not None:
            ele = etree.SubElement(waypoint, "ele", nsmap=self._nsmap)
            ele.text = str(self.ele)

        if self.time is not None:
            time = etree.SubElement(waypoint, "time", nsmap=self._nsmap)
            time.text = self.time.isoformat(
                timespec="milliseconds" if self.time.microsecond else "seconds"
            ).replace("+00:00", "Z")

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

        for link in self.links:
            waypoint.append(link._build())

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
        """Returns the distance to the other waypoint (in metres) using a simple
        spherical earth model (haversine formula).

        Args:
            other: The other waypoint.
            radius: The radius of the earth (defaults to 6,378,137 metres).

        Returns:
            The distance to the other waypoint (in metres).

        Adapted from: https://github.com/chrisveness/geodesy/blob/33d1bf53c069cd7dd83c6bf8531f5f3e0955c16e/latlon-spherical.js#L187-L205
        """
        R = radius
        φ1, λ1 = radians(self.lat), radians(self.lon)
        φ2, λ2 = radians(other.lat), radians(other.lon)
        Δφ = φ2 - φ1
        Δλ = λ2 - λ1
        a = sin(Δφ / 2) * sin(Δφ / 2) + cos(φ1) * cos(φ2) * sin(Δλ / 2) * sin(Δλ / 2)
        δ = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * δ

    def duration_to(self, other: Waypoint) -> timedelta:
        """Returns the duration to the other waypoint.

        Args:
            other: The other waypoint.

        Returns:
            The duration to the other waypoint.
        """
        if self.time is None or other.time is None:
            return timedelta()
        return other.time - self.time
