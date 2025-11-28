"""Waypoint model for GPX data.

This module provides the Waypoint model representing a waypoint, point of interest,
or named feature on a map, following the GPX 1.1 specification.
"""

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from math import atan2, cos, radians, sin, sqrt
from typing import Any

from gpx.types import Degrees, DGPSStation, Fix, Latitude, Longitude  # noqa: TC001

from .base import GPXModel
from .link import Link  # noqa: TC001
from .utils import build_geo_feature


@dataclass(slots=True)
class Waypoint(GPXModel):
    """A waypoint, point of interest, or named feature on a map.

    Args:
        lat: Latitude of the point in decimal degrees, WGS84 datum.
        lon: Longitude of the point in decimal degrees, WGS84 datum.
        ele: Elevation (in meters) of the point. Defaults to None.
        time: Creation/modification timestamp for element (UTC). Defaults to None.
        magvar: Magnetic variation (in degrees) at the point. Defaults to None.
        geoidheight: Height (in meters) of geoid (mean sea level) above WGS84
            earth ellipsoid. Defaults to None.
        name: GPS name of the waypoint. Defaults to None.
        cmt: GPS waypoint comment. Defaults to None.
        desc: Text description of the element. Defaults to None.
        src: Source of data. Defaults to None.
        link: Links to additional information about the waypoint. Defaults to
            empty list.
        sym: Text of GPS symbol name. Defaults to None.
        type: Type (classification) of the waypoint. Defaults to None.
        fix: Type of GPX fix. Defaults to None.
        sat: Number of satellites used to calculate the GPX fix. Defaults to None.
        hdop: Horizontal dilution of precision. Defaults to None.
        vdop: Vertical dilution of precision. Defaults to None.
        pdop: Position dilution of precision. Defaults to None.
        ageofdgpsdata: Number of seconds since last DGPS update. Defaults to None.
        dgpsid: ID of DGPS station used in differential correction. Defaults to None.

    """

    _tag = "wpt"

    lat: Latitude
    lon: Longitude
    _: KW_ONLY
    ele: Decimal | None = None
    time: datetime | None = None
    magvar: Degrees | None = None
    geoidheight: Decimal | None = None
    name: str | None = None
    cmt: str | None = None
    desc: str | None = None
    src: str | None = None
    link: list[Link] = field(default_factory=list)
    sym: str | None = None
    type: str | None = None
    fix: Fix | None = None
    sat: int | None = None
    hdop: Decimal | None = None
    vdop: Decimal | None = None
    pdop: Decimal | None = None
    ageofdgpsdata: Decimal | None = None
    dgpsid: DGPSStation | None = None

    @property
    def _coordinates(
        self,
    ) -> tuple[Longitude, Latitude] | tuple[Longitude, Latitude, Decimal]:
        return (
            (self.lon, self.lat, self.ele)
            if self.ele is not None
            else (self.lon, self.lat)
        )

    @property
    def __geo_interface__(self) -> dict[str, Any]:
        """Return the waypoint as a GeoJSON-like Point geometry or Feature.

        Returns a Feature if any optional fields (excluding ele) are set,
        otherwise returns a pure Point geometry.

        Returns:
            A dictionary representing either a GeoJSON Point geometry or Feature.

        """
        geometry = {
            "type": "Point",
            "coordinates": [float(coordinate) for coordinate in self._coordinates],
        }

        # Exclude coordinate fields from properties
        return build_geo_feature(geometry, self, exclude_fields={"lat", "lon", "ele"})

    def distance_to(self, other: Waypoint, radius: int = 6_378_137) -> float:
        """Return the distance to another waypoint using the haversine formula.

        Uses a simple spherical earth model (haversine formula).

        Args:
            other: The other waypoint.
            radius: The radius of the earth. Defaults to 6,378,137 metres.

        Returns:
            The distance to the other waypoint (in metres).

        """
        R = radius  # noqa: N806
        φ1, λ1 = radians(self.lat), radians(self.lon)
        φ2, λ2 = radians(other.lat), radians(other.lon)
        Δφ = φ2 - φ1  # noqa: N806
        Δλ = λ2 - λ1  # noqa: N806
        a = sin(Δφ / 2) * sin(Δφ / 2) + cos(φ1) * cos(φ2) * sin(Δλ / 2) * sin(Δλ / 2)
        δ = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * δ

    def duration_to(self, other: Waypoint) -> timedelta:
        """Return the duration to another waypoint.

        Args:
            other: The other waypoint.

        Returns:
            The duration to the other waypoint. Returns zero timedelta if either
            waypoint lacks a timestamp.

        """
        if self.time is None or other.time is None:
            return timedelta()
        return other.time - self.time

    def speed_to(self, other: Waypoint) -> float:
        """Return the speed to another waypoint.

        Args:
            other: The other waypoint.

        Returns:
            The speed to the other waypoint (in metres per second).

        """
        return self.distance_to(other) / self.duration_to(other).total_seconds()

    def gain_to(self, other: Waypoint) -> Decimal:
        """Return the elevation gain to another waypoint.

        Args:
            other: The other waypoint.

        Returns:
            The elevation gain to the other waypoint (in metres). Returns zero
            if either waypoint lacks elevation data.

        """
        if self.ele is None or other.ele is None:
            return Decimal("0.0")
        return other.ele - self.ele

    def slope_to(self, other: Waypoint) -> Decimal:
        """Return the slope to another waypoint.

        Args:
            other: The other waypoint.

        Returns:
            The slope to the other waypoint (in percent).

        """
        return self.gain_to(other) / Decimal(self.distance_to(other)) * 100
