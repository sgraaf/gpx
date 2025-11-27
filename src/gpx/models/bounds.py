"""Bounds model for GPX data.

This module provides the Bounds model representing two lat/lon pairs defining
the extent of an element, following the GPX 1.1 specification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from gpx.types import Latitude, Longitude  # noqa: TC001

from .base import GPXModel

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(slots=True)
class Bounds(GPXModel):
    """Two lat/lon pairs defining the extent of an element.

    Args:
        minlat: The minimum latitude.
        minlon: The minimum longitude.
        maxlat: The maximum latitude.
        maxlon: The maximum longitude.

    """

    _tag = "bounds"

    minlat: Latitude
    minlon: Longitude
    maxlat: Latitude
    maxlon: Longitude

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
