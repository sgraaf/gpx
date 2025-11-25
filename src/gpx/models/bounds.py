"""Bounds model for GPX data.

This module provides the Bounds model representing two lat/lon pairs defining
the extent of an element, following the GPX 1.1 specification.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from lxml import etree

from gpx.types import Latitude, Longitude

if TYPE_CHECKING:
    from collections.abc import Iterator

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

#: GPX 1.1 namespace
GPX_NAMESPACE = "http://www.topografix.com/GPX/1/1"


@dataclass(frozen=True)
class Bounds:
    """Two lat/lon pairs defining the extent of an element.

    Args:
        minlat: The minimum latitude.
        minlon: The minimum longitude.
        maxlat: The maximum latitude.
        maxlon: The maximum longitude.

    """

    minlat: Latitude
    minlon: Longitude
    maxlat: Latitude
    maxlon: Longitude

    @classmethod
    def from_xml(cls, element: etree._Element) -> Self:
        """Parse a Bounds from an XML element.

        Args:
            element: The XML element to parse.

        Returns:
            The parsed Bounds instance.

        Raises:
            ValueError: If required attributes are missing or invalid.

        """
        minlat_value = element.get("minlat")
        minlon_value = element.get("minlon")
        maxlat_value = element.get("maxlat")
        maxlon_value = element.get("maxlon")

        if minlat_value is None:
            msg = "Bounds element missing required 'minlat' attribute"
            raise ValueError(msg)

        if minlon_value is None:
            msg = "Bounds element missing required 'minlon' attribute"
            raise ValueError(msg)

        if maxlat_value is None:
            msg = "Bounds element missing required 'maxlat' attribute"
            raise ValueError(msg)

        if maxlon_value is None:
            msg = "Bounds element missing required 'maxlon' attribute"
            raise ValueError(msg)

        return cls(
            minlat=Latitude(minlat_value),
            minlon=Longitude(minlon_value),
            maxlat=Latitude(maxlat_value),
            maxlon=Longitude(maxlon_value),
        )

    def to_xml(
        self, tag: str = "bounds", nsmap: dict[str | None, str] | None = None
    ) -> etree._Element:
        """Convert the Bounds to an XML element.

        Args:
            tag: The XML tag name. Defaults to "bounds".
            nsmap: Optional namespace mapping. Defaults to GPX 1.1 namespace.

        Returns:
            The XML element.

        """
        if nsmap is None:
            nsmap = {None: GPX_NAMESPACE}

        element = etree.Element(tag, nsmap=nsmap)
        element.set("minlat", str(self.minlat))
        element.set("minlon", str(self.minlon))
        element.set("maxlat", str(self.maxlat))
        element.set("maxlon", str(self.maxlon))

        return element

    @property
    def __geo_interface__(self) -> dict[str, Any]:
        """Return the Bounds as a GeoJSON-like Polygon.

        The bounds are represented as a rectangular Polygon following the
        GeoJSON specification.

        Returns:
            A dictionary with 'type' and 'coordinates' keys representing
            the bounds as a Polygon. Coordinates use [longitude, latitude]
            order as per GeoJSON convention.

        """
        return {
            "type": "Polygon",
            "coordinates": [
                [
                    [float(self.minlon), float(self.minlat)],
                    [float(self.maxlon), float(self.minlat)],
                    [float(self.maxlon), float(self.maxlat)],
                    [float(self.minlon), float(self.maxlat)],
                    [float(self.minlon), float(self.minlat)],  # Close the ring
                ],
            ],
        }

    def as_tuple(self) -> tuple[Latitude, Longitude, Latitude, Longitude]:
        """Return the bounds as a tuple.

        Returns:
            A tuple of (minlat, minlon, maxlat, maxlon).

        """
        return (self.minlat, self.minlon, self.maxlat, self.maxlon)

    def __getitem__(self, index: int) -> Latitude | Longitude:
        """Get a bound coordinate by index.

        Args:
            index: The index (0=minlat, 1=minlon, 2=maxlat, 3=maxlon).

        Returns:
            The coordinate at the given index.

        """
        return self.as_tuple()[index]

    def __iter__(self) -> Iterator[Latitude | Longitude]:
        """Iterate over the bounds coordinates.

        Yields:
            Each coordinate in order: minlat, minlon, maxlat, maxlon.

        """
        return iter(self.as_tuple())

    def __len__(self) -> int:
        """Return the number of coordinates.

        Returns:
            Always returns 4 (minlat, minlon, maxlat, maxlon).

        """
        return len(self.as_tuple())
