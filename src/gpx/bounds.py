"""
This module provides a Bounds object to contain two lat/lon pairs defining
the extent of an element.
"""
from __future__ import annotations

from lxml import etree

from .element import Element
from .types import Latitude, Longitude


class Bounds(Element):
    """A bounds class for the GPX data format.

    Two lat/lon pairs defining the extent of an element.

    Args:
        element: The bounds XML element. Defaults to `None`.
    """

    #: The minimum latitude.
    minlat: Latitude

    #: The minimum longitude.
    minlon: Longitude

    #: The maximum latitude.
    maxlat: Latitude

    #: The maximum longitude.
    maxlon: Longitude

    def as_tuple(self) -> tuple[Latitude, Longitude, Latitude, Longitude]:
        """Return the bounds as a tuple."""
        return (self.minlat, self.minlon, self.maxlat, self.maxlon)

    def __getitem__(self, index: int) -> Latitude | Longitude:
        return self.as_tuple()[index]

    def __iter__(self):
        return iter(self.as_tuple())

    def __len__(self):
        return len(self.as_tuple())

    def _parse(self) -> None:
        super()._parse()

        # assertion to satisfy mypy
        assert self._element is not None

        # required
        self.minlat = Latitude(self._element.get("minlat"))
        self.minlon = Longitude(self._element.get("minlon"))
        self.maxlat = Latitude(self._element.get("maxlat"))
        self.maxlon = Longitude(self._element.get("maxlon"))

    def _build(self, tag: str = "bounds") -> etree._Element:
        bounds = super()._build(tag)
        bounds.set("minlat", str(self.minlat))
        bounds.set("minlon", str(self.minlon))
        bounds.set("maxlat", str(self.maxlat))
        bounds.set("maxlon", str(self.maxlon))

        return bounds
