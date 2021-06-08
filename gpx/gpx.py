"""This module provides a GPX object to contain GPX files, consisting of waypoints, routes and tracks."""
from __future__ import annotations

import datetime
import pathlib
from typing import Any, Dict, List, Optional, Tuple, Union

from dateutil.parser import isoparse
from lxml import etree

from . import gpx_schema
from .errors import InvalidGPXError
from .route import Route
from .track import Track
from .utils import remove_encoding_from_string
from .waypoint import Waypoint
from ._parsers import parse_links


class GPX:
    """A GPX class for the GPX data format.

    Args:
        gpx (etree.Element, optional): The GPX XML element. Defaults to None.
    """

    def __init__(self, gpx: Optional[etree._Element] = None) -> None:
        self._gpx: etree._Element = gpx
        self._nsmap: Optional[Dict[str, str]] = None
        self.creator: Optional[str] = "PyGPX"
        self.name: Optional[str] = None
        self.desc: Optional[str] = None
        self.author: Dict[str, Any] = {}
        self.copyright: Dict[str, Union[str, int]] = {}
        self.links: List[Dict[str, str]] = []
        self.time: Optional[datetime.datetime] = None
        self.keywords: Optional[str] = None
        self.bounds: Optional[Tuple[float, float, float, float]] = None
        self.waypoints: List[Waypoint] = []
        self.routes: List[Route] = []
        self.tracks: List[Track] = []

        if self._gpx is not None:
            self._parse()

    @property
    def _has_metadata(self) -> bool:
        return (
            self.name is not None
            or self.desc is not None
            or bool(self.author)
            or bool(self.copyright)
            or bool(self.links)
            or self.time is not None
            or self.keywords is not None
            or self.bounds is not None
        )

    def _parse(self) -> None:
        # namespaces
        self._nsmap = self._gpx.nsmap

        # creator
        self.creator = self._gpx.get("creator")

        # metadata
        if (metadata := self._gpx.find("metadata", namespaces=self._nsmap)) is not None:
            # name
            if (name := metadata.find("name", namespaces=self._nsmap)) is not None:
                self.name = name.text
            # description
            if (desc := metadata.find("desc", namespaces=self._nsmap)) is not None:
                self.desc = desc.text
            # author
            if (author := metadata.find("author", namespaces=self._nsmap)) is not None:
                if (name := author.find("name", namespaces=self._nsmap)) is not None:
                    self.author["name"] = name.text
                # email
                if (email := author.find("email", namespaces=self._nsmap)) is not None:
                    self.author["email"] = f'{email.get("id")}@{email.get("domain")}'
                # link
                if (link := author.find("link", namespaces=self._nsmap)) is not None:
                    self.author["link"] = {"href": link.get("href")}
                    if (text := link.find("text", namespaces=self._nsmap)) is not None:
                        self.author["link"]["text"] = text.text
                    if (_type := link.find("type", namespaces=self._nsmap)) is not None:
                        self.author["link"]["type"] = _type.text
            # copyright
            if (
                _copyright := metadata.find("copyright", namespaces=self._nsmap)
            ) is not None:
                # author
                self.copyright["author"] = _copyright.get("author")
                # year
                if (
                    year := _copyright.find("year", namespaces=self._nsmap)
                ) is not None:
                    self.copyright["year"] = int(year.text)
                # license
                if (
                    _license := _copyright.find("license", namespaces=self._nsmap)
                ) is not None:
                    self.copyright["license"] = _license.text
            # links to locations associated with the GPX file
            self.links = parse_links(metadata)
            # creation date of the GPX file
            if (time := metadata.find("time", namespaces=self._nsmap)) is not None:
                self.time = isoparse(time.text)
            if (
                keywords := metadata.find("keywords", namespaces=self._nsmap)
            ) is not None:
                self.keywords = keywords.text
            if (bounds := metadata.find("bounds", namespaces=self._nsmap)) is not None:
                self.bounds = (
                    float(bounds.get("minlat")),
                    float(bounds.get("minlon")),
                    float(bounds.get("maxlat")),
                    float(bounds.get("maxlon")),
                )

        # waypoints
        for wpt in self._gpx.iterfind("wpt", namespaces=self._nsmap):
            self.waypoints.append(Waypoint(wpt))

        # routes
        for rte in self._gpx.iterfind("rte", namespaces=self._nsmap):
            self.routes.append(Route(rte))

        # tracks
        for trk in self._gpx.iterfind("trk", namespaces=self._nsmap):
            self.tracks.append(Track(trk))

    def _build(self) -> etree._Element:
        gpx = etree.Element("gpx", nsmap=self._nsmap)

        # set version and creator attributes
        gpx.set("version", "1.1")
        gpx.set("creator", self.creator)

        # metadata
        if self._has_metadata:
            metadata = etree.SubElement(gpx, "metadata", nsmap=self._nsmap)

            if self.name is not None:
                name = etree.SubElement(metadata, "name", nsmap=self._nsmap)
                name.text = self.name

            if self.desc is not None:
                desc = etree.SubElement(metadata, "desc", nsmap=self._nsmap)
                desc.text = self.desc

            if self.author:
                author = etree.SubElement(metadata, "author", nsmap=self._nsmap)
                if (tag := "name") in self.author:
                    name = etree.SubElement(author, tag, nsmap=self._nsmap)
                    name.text = self.author[tag]
                if (tag := "email") in self.author:
                    email = etree.SubElement(author, tag, nsmap=self._nsmap)
                    id, domain = self.author[tag].split("@")
                    email.set("id", id)
                    email.set("domain", domain)
                if (tag := "link") in self.author:
                    link = etree.SubElement(author, tag, nsmap=self._nsmap)
                    link.set("href", self.author[tag]["href"])
                    if (_tag := "text") in self.author[tag]:
                        _text = etree.SubElement(link, _tag, nsmap=self._nsmap)
                        _text.text = self.author[tag][_tag]
                    if (_tag := "type") in self.author[tag]:
                        _type = etree.SubElement(link, _tag, nsmap=self._nsmap)
                        _type.text = self.author[tag][_tag]

            if self.copyright:
                copyright = etree.SubElement(metadata, "copyright", nsmap=self._nsmap)
                copyright.set("author", self.copyright["author"])

                if (tag := "year") in self.copyright:
                    year = etree.SubElement(copyright, tag, nsmap=self._nsmap)
                    year.text = self.copyright[tag]

                if (tag := "license") in self.copyright:
                    license = etree.SubElement(copyright, tag, nsmap=self._nsmap)
                    license.text = self.copyright[tag]

            for _link in self.links:
                link = etree.SubElement(metadata, "link", nsmap=self._nsmap)
                link.set("href", _link["href"])
                if (tag := "text") in _link:
                    text = etree.SubElement(link, tag, nsmap=self._nsmap)
                    text.text = _link[tag]
                if (tag := "type") in _link:
                    _type = etree.SubElement(link, tag, nsmap=self._nsmap)
                    _type.text = _link[tag]

            if self.time is not None:
                time = etree.SubElement(metadata, "time", nsmap=self._nsmap)
                time.text = self.time.isoformat().replace("+00:00", "Z")

            if self.keywords is not None:
                keywords = etree.SubElement(metadata, "keywords", nsmap=self._nsmap)
                keywords.text = self.keywords

            if self.bounds is not None:
                bounds = etree.SubElement(metadata, "bounds", nsmap=self._nsmap)
                bounds.set("minlat", self.bounds[0])
                bounds.set("minlon", self.bounds[1])
                bounds.set("maxlat", self.bounds[2])
                bounds.set("maxlon", self.bounds[3])

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
    def from_string(cls, gpx_str: str, validate: Optional[bool] = False) -> GPX:
        """Create an GPX instance from a string.

        Args:
            gpx_str (str). The string containing the GPX data.

        Returns:
            GPX: the GPX instance.
        """
        # etree.fromstring() does not support encoding declarations in the string itself.
        gpx_str = remove_encoding_from_string(gpx_str)
        gpx = etree.fromstring(gpx_str)
        if validate:
            if not gpx_schema.validate(gpx):  # invalid GPX
                raise InvalidGPXError("The GPX data is invalid.")
        return cls(gpx)

    @classmethod
    def from_file(
        cls, gpx_file: Union[str, pathlib.Path], validate: Optional[bool] = False
    ) -> GPX:
        """Create an GPX instance from a file.

        Args:
            gpx_file (Union[str, pathlib.Path]). The file containing the GPX data.

        Returns:
            GPX: the GPX instance.
        """
        gpx_tree = etree.parse(str(gpx_file))
        gpx = gpx_tree.getroot()
        if validate:
            if not gpx_schema.validate(gpx):  # invalid GPX
                raise InvalidGPXError("The GPX data is invalid.")
        return cls(gpx)

    def to_string(self) -> str:
        """Serialize the GPX instance to a string."""
        gpx = self._build()
        gpx_tree = etree.ElementTree(gpx)
        return etree.tostring(gpx_tree, encoding="unicode", pretty_print=True)

    def to_file(self, gpx_file: Union[str, pathlib.Path]) -> None:
        """Serialize the GPX instance to a file."""
        gpx = self._build()
        gpx_tree = etree.ElementTree(gpx)
        gpx_tree.write(
            str(gpx_file), pretty_print=True, xml_declaration=True, encoding="utf-8"
        )
