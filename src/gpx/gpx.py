"""
This module provides a GPX object to contain GPX files, consisting of waypoints,
routes and tracks.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from lxml import etree

from . import gpx_schema
from .bounds import Bounds
from .copyright import Copyright
from .element import Element
from .errors import InvalidGPXError
from .link import Link
from .metadata import Metadata
from .person import Person
from .route import Route
from .track import Track
from .utils import remove_encoding_from_string
from .waypoint import Waypoint


class GPX(Element):
    """A GPX class for the GPX data format.

    GPX documents contain a metadata header, followed by waypoints, routes, and
    tracks. You can add your own elements to the extensions section of the GPX
    document.

    Args:
        element: The GPX XML element. Defaults to `None`.
    """

    #: The name or URL of the software that created your GPX document. Defaults
    #: to "PyGPX".
    creator: str = "PyGPX"

    #: Metadata about the file.
    metadata: Metadata | None = None

    #: A list of waypoints.
    waypoints: list[Waypoint] = []

    #: A list of routes.
    routes: list[Route] = []

    #: A list of tracks.
    tracks: list[Track] = []

    @property
    def name(self) -> str | None:
        """The name of the GPX file.

        Alias of :attr:`gpx.metadata.Metadata.name`.
        """
        if self.metadata is not None:
            return self.metadata.name
        return None

    @name.setter
    def name(self, value: str):
        if self.metadata is None:
            self.metadata = Metadata()
        self.metadata.name = value

    @property
    def desc(self) -> str | None:
        """A description of the contents of the GPX file.

        Alias of :attr:`gpx.metadata.Metadata.desc`.
        """
        if self.metadata is not None:
            return self.metadata.desc
        return None

    @desc.setter
    def desc(self, value: str):
        if self.metadata is None:
            self.metadata = Metadata()
        self.metadata.desc = value

    @property
    def author(self) -> Person | None:
        """The person or organization who created the GPX file.

        Alias of :attr:`gpx.metadata.Metadata.author`.
        """
        if self.metadata is not None:
            return self.metadata.author
        return None

    @author.setter
    def author(self, value: Person):
        if self.metadata is None:
            self.metadata = Metadata()
        self.metadata.author = value

    @property
    def copyright(self) -> Copyright | None:
        """Copyright and license information governing use of the file.

        Alias of :attr:`gpx.metadata.Metadata.copyright`.
        """
        if self.metadata is not None:
            return self.metadata.copyright
        return None

    @copyright.setter
    def copyright(self, value: Copyright):
        if self.metadata is None:
            self.metadata = Metadata()
        self.metadata.copyright = value

    @property
    def links(self) -> list[Link] | None:
        """URLs associated with the location described in the file.

        Alias of :attr:`gpx.metadata.Metadata.links`.
        """
        if self.metadata is not None:
            return self.metadata.links
        return None

    @links.setter
    def links(self, value: list[Link]):
        if self.metadata is None:
            self.metadata = Metadata()
        self.metadata.links = value

    @property
    def time(self) -> datetime | None:
        """The creation date of the file.

        Alias of :attr:`gpx.metadata.Metadata.time`.
        """
        if self.metadata is not None:
            return self.metadata.time
        return None

    @time.setter
    def time(self, value: datetime):
        if self.metadata is None:
            self.metadata = Metadata()
        self.metadata.time = value

    @property
    def keywords(self) -> str | None:
        """Keywords associated with the file. Search engines or databases can
        use this information to classify the data.

        Alias of :attr:`gpx.metadata.Metadata.keywords`.
        """
        if self.metadata is not None:
            return self.metadata.keywords
        return None

    @keywords.setter
    def keywords(self, value: str):
        if self.metadata is None:
            self.metadata = Metadata()
        self.metadata.keywords = value

    @property
    def bounds(self) -> Bounds | None:
        """Minimum and maximum coordinates which describe the extent of the
        coordinates in the file.

        Alias of :attr:`gpx.metadata.Metadata.bounds`.
        """
        if self.metadata is not None:
            return self.metadata.bounds
        return None

    @bounds.setter
    def bounds(self, value: Bounds):
        if self.metadata is None:
            self.metadata = Metadata()
        self.metadata.bounds = value

    def _parse(self) -> None:
        super()._parse()

        # assertion to satisfy mypy
        assert self._element is not None

        # namespaces
        self._nsmap = self._element.nsmap

        # creator
        creator = self._element.get("creator")
        if creator is not None:
            self.creator = creator

        # metadata
        if (
            metadata := self._element.find("metadata", namespaces=self._nsmap)
        ) is not None:
            self.metadata = Metadata(metadata)

        # waypoints
        for wpt in self._element.iterfind("wpt", namespaces=self._nsmap):
            self.waypoints.append(Waypoint(wpt))

        # routes
        for rte in self._element.iterfind("rte", namespaces=self._nsmap):
            self.routes.append(Route(rte))

        # tracks
        for trk in self._element.iterfind("trk", namespaces=self._nsmap):
            self.tracks.append(Track(trk))

    def _build(self, tag: str = "gpx") -> etree._Element:
        gpx = super()._build(tag)

        # set version and creator attributes
        gpx.set("version", "1.1")
        gpx.set("creator", self.creator)

        # metadata
        if self.metadata:
            gpx.append(self.metadata._build())

        # waypoints
        for _waypoint in self.waypoints:
            gpx.append(_waypoint._build())

        # routes
        for _route in self.routes:
            gpx.append(_route._build())

        # tracks
        for _track in self.tracks:
            gpx.append(_track._build())

        return gpx

    @classmethod
    def from_string(cls, gpx_str: str, validate: bool = False) -> GPX:
        """Create an GPX instance from a string.

            >>> from gpx import GPX
            >>> gpx = GPX.from_str(\"\"\"<?xml version="1.0" encoding="UTF-8" ?>
            ... <gpx xmlns="http://www.topografix.com/GPX/1/1" creator="PyGPX" version="1.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
            ...     [...]
            ... </gpx>\"\"\")
            >>> print(gpx.bounds)

        Args:
            gpx_str: The string containing the GPX data.
            validate: Whether to validate the GPX data.

        Returns:
            The GPX instance.
        """
        # etree.fromstring() does not support encoding declarations in the string itself.
        gpx_str = remove_encoding_from_string(gpx_str)
        gpx = etree.fromstring(gpx_str)
        if validate:
            if not gpx_schema.validate(gpx):  # invalid GPX
                raise InvalidGPXError("The GPX data is invalid.")
        return cls(gpx)

    @classmethod
    def from_file(cls, gpx_file: str | Path, validate: bool = False) -> GPX:
        """Create an GPX instance from a file.

            >>> from gpx import GPX
            >>> gpx = GPX.from_file("path/to/file.gpx")
            >>> print(gpx.bounds)

        Args:
            gpx_file: The file containing the GPX data.
            validate: Whether to validate the GPX data.

        Returns:
            The GPX instance.
        """
        gpx_tree = etree.parse(str(gpx_file))
        gpx = gpx_tree.getroot()
        if validate:
            if not gpx_schema.validate(gpx):  # invalid GPX
                raise InvalidGPXError("The GPX data is invalid.")
        return cls(gpx)

    def to_string(self) -> str:
        """Serialize the GPX instance to a string.

        Returns:
            The GPX data as a string.
        """
        gpx = self._build()
        gpx_tree = etree.ElementTree(gpx)
        return etree.tostring(gpx_tree, encoding="unicode", pretty_print=True)

    def to_file(self, gpx_file: str | Path) -> None:
        """Serialize the GPX instance to a file.

        Args:
            gpx_file: The file to write the GPX data to.
        """
        gpx = self._build()
        gpx_tree = etree.ElementTree(gpx)
        gpx_tree.write(
            str(gpx_file), pretty_print=True, xml_declaration=True, encoding="utf-8"
        )
