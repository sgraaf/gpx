"""GPX model for GPX data.

This module provides the GPX model representing the root GPX document,
following the GPX 1.1 specification.
"""

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass, field
from typing import TYPE_CHECKING, Any, Self

from lxml import etree

from gpx import gpx_schema
from gpx.errors import InvalidGPXError
from gpx.utils import remove_encoding_from_string

from .base import GPXModel
from .metadata import Metadata  # noqa: TC001
from .route import Route  # noqa: TC001
from .track import Track  # noqa: TC001
from .utils import build_to_xml
from .waypoint import Waypoint  # noqa: TC001

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from .bounds import Bounds
    from .copyright import Copyright
    from .link import Link
    from .person import Person

#: GPX 1.1 namespace
GPX_NAMESPACE = "http://www.topografix.com/GPX/1/1"
#: XML Schema instance namespace
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"


@dataclass(slots=True)
class GPX(GPXModel):
    """The root GPX document.

    GPX documents contain a metadata header, followed by waypoints, routes, and
    tracks. You can add your own elements to the extensions section of the GPX
    document.

    Note: The GPX version is always "1.1" per the specification and is
    automatically set during XML serialization.

    Args:
        creator: The name or URL of the software that created the GPX document.
            Defaults to "PyGPX".
        metadata: Metadata about the file. Defaults to None.
        wpt: List of waypoints. Defaults to empty list.
        rte: List of routes. Defaults to empty list.
        trk: List of tracks. Defaults to empty list.

    """

    _tag = "gpx"

    creator: str = "PyGPX"
    _: KW_ONLY
    metadata: Metadata | None = None
    wpt: list[Waypoint] = field(default_factory=list)
    rte: list[Route] = field(default_factory=list)
    trk: list[Track] = field(default_factory=list)

    @property
    def waypoints(self) -> list[Waypoint]:
        """Alias for wpt."""
        return self.wpt

    @property
    def routes(self) -> list[Route]:
        """Alias for rte."""
        return self.rte

    @property
    def tracks(self) -> list[Track]:
        """Alias for trk."""
        return self.trk

    @property
    def name(self) -> str | None:
        """The name of the GPX file.

        Proxy of :attr:`gpx.models.metadata.Metadata.name`.
        """
        if self.metadata is not None:
            return self.metadata.name
        return None

    @property
    def desc(self) -> str | None:
        """A description of the contents of the GPX file.

        Proxy of :attr:`gpx.models.metadata.Metadata.desc`.
        """
        if self.metadata is not None:
            return self.metadata.desc
        return None

    @property
    def author(self) -> Person | None:
        """The person or organization who created the GPX file.

        Proxy of :attr:`gpx.models.metadata.Metadata.author`.
        """
        if self.metadata is not None:
            return self.metadata.author
        return None

    @property
    def copyright(self) -> Copyright | None:
        """Copyright and license information governing use of the file.

        Proxy of :attr:`gpx.models.metadata.Metadata.copyright`.
        """
        if self.metadata is not None:
            return self.metadata.copyright
        return None

    @property
    def links(self) -> list[Link] | None:
        """URLs associated with the location described in the file.

        Proxy of :attr:`gpx.models.metadata.Metadata.link`.
        """
        if self.metadata is not None:
            return self.metadata.link
        return None

    @property
    def time(self) -> datetime | None:
        """The creation date of the file.

        Proxy of :attr:`gpx.models.metadata.Metadata.time`.
        """
        if self.metadata is not None:
            return self.metadata.time
        return None

    @property
    def keywords(self) -> str | None:
        """Keywords associated with the file.

        Search engines or databases can use this information to classify the data.

        Proxy of :attr:`gpx.models.metadata.Metadata.keywords`.
        """
        if self.metadata is not None:
            return self.metadata.keywords
        return None

    @property
    def bounds(self) -> Bounds | None:
        """Minimum and maximum coordinates which describe the extent of the coordinates in the file.

        Proxy of :attr:`gpx.models.metadata.Metadata.bounds`.
        """
        if self.metadata is not None:
            return self.metadata.bounds
        return None

    @property
    def __geo_interface__(self) -> dict[str, Any]:
        """Return the GPX as a GeoJSON-like FeatureCollection.

        Returns:
            A dictionary representing a GeoJSON FeatureCollection containing
            all waypoints, routes, and tracks.

        """
        features = []

        # Add waypoints
        for waypoint in self.wpt:
            geo = waypoint.__geo_interface__
            # If waypoint returned a pure geometry, wrap it in a Feature
            if geo.get("type") == "Point":
                features.append(
                    {
                        "type": "Feature",
                        "geometry": geo,
                    }
                )
            else:
                # Already a Feature
                features.append(geo)

        # Add routes
        for route in self.rte:
            geo = route.__geo_interface__
            # If route returned a pure geometry, wrap it in a Feature
            if geo.get("type") == "LineString":
                features.append(
                    {
                        "type": "Feature",
                        "geometry": geo,
                    }
                )
            else:
                # Already a Feature
                features.append(geo)

        # Add tracks
        for track in self.trk:
            geo = track.__geo_interface__
            # If track returned a pure geometry, wrap it in a Feature
            if geo.get("type") == "MultiLineString":
                features.append(
                    {
                        "type": "Feature",
                        "geometry": geo,
                    }
                )
            else:
                # Already a Feature
                features.append(geo)

        return {
            "type": "FeatureCollection",
            "features": features,
        }

    def to_xml(
        self, tag: str | None = None, nsmap: dict[str | None, str] | None = None
    ) -> etree._Element:
        """Convert the GPX to an XML element.

        Args:
            tag: The XML tag name. Defaults to "gpx".
            nsmap: Optional namespace mapping. Defaults to GPX 1.1 namespace
                with XML Schema instance namespace.

        Returns:
            The XML element.

        """
        if tag is None:
            tag = self._tag

        if nsmap is None:
            nsmap = {
                None: GPX_NAMESPACE,
                "xsi": XSI_NAMESPACE,
            }

        # Create the element with namespaces
        element = etree.Element(tag, nsmap=nsmap)

        # Add GPX-specific attributes
        element.set("version", "1.1")
        element.set(
            f"{{{XSI_NAMESPACE}}}schemaLocation",
            f"{GPX_NAMESPACE} {GPX_NAMESPACE}/gpx.xsd",
        )

        # Use parent's build_to_xml for fields
        build_to_xml(self, element, nsmap=nsmap)

        return element

    @classmethod
    def from_string(cls, gpx_str: str, *, validate: bool = False) -> Self:
        """Create a GPX instance from a string.

        Args:
            gpx_str: The string containing the GPX data.
            validate: Whether to validate the GPX data against the GPX 1.1 schema.
                Defaults to False.

        Returns:
            The GPX instance.

        Raises:
            InvalidGPXError: If validation is enabled and the GPX data is invalid.

        Example:
            >>> from gpx import GPX
            >>> gpx = GPX.from_string('''<?xml version="1.0"?>
            ... <gpx version="1.1" creator="MyApp">
            ...     <metadata><name>My Track</name></metadata>
            ... </gpx>''')
            >>> print(gpx.creator)
            MyApp

        """
        # etree.fromstring() does not support encoding declarations in the string
        gpx_str = remove_encoding_from_string(gpx_str)
        element = etree.fromstring(gpx_str)

        if validate and not gpx_schema.validate(element):
            msg = "The GPX data is invalid."
            raise InvalidGPXError(msg)

        return cls.from_xml(element)

    @classmethod
    def from_file(cls, gpx_file: str | Path, *, validate: bool = False) -> Self:
        """Create a GPX instance from a file.

        Args:
            gpx_file: The file path containing the GPX data.
            validate: Whether to validate the GPX data against the GPX 1.1 schema.
                Defaults to False.

        Returns:
            The GPX instance.

        Raises:
            InvalidGPXError: If validation is enabled and the GPX data is invalid.

        Example:
            >>> from gpx import GPX
            >>> gpx = GPX.from_file("path/to/file.gpx")
            >>> print(gpx.creator)

        """
        gpx_tree = etree.parse(str(gpx_file))
        element = gpx_tree.getroot()

        if validate and not gpx_schema.validate(element):
            msg = "The GPX data is invalid."
            raise InvalidGPXError(msg)

        return cls.from_xml(element)

    def to_string(self, *, pretty_print: bool = True) -> str:
        """Serialize the GPX instance to a string.

        Args:
            pretty_print: Whether to format the output with indentation.
                Defaults to True.

        Returns:
            The GPX data as a string.

        Example:
            >>> from gpx import GPX
            >>> gpx = GPX(creator="MyApp")
            >>> xml_string = gpx.to_string()
            >>> print(xml_string[:50])
            <?xml version='1.0' encoding='UTF-8'?>
            <gpx ve

        """
        element = self.to_xml()
        xml_bytes = etree.tostring(
            element,
            encoding="utf-8",
            pretty_print=pretty_print,
            xml_declaration=True,
        )
        return xml_bytes.decode("utf-8")

    def to_file(self, gpx_file: str | Path, *, pretty_print: bool = True) -> None:
        """Serialize the GPX instance to a file.

        Args:
            gpx_file: The file path to write the GPX data to.
            pretty_print: Whether to format the output with indentation.
                Defaults to True.

        Example:
            >>> from gpx import GPX
            >>> gpx = GPX(creator="MyApp")
            >>> gpx.to_file("output.gpx")

        """
        element = self.to_xml()
        tree = etree.ElementTree(element)
        tree.write(
            str(gpx_file),
            pretty_print=pretty_print,
            xml_declaration=True,
            encoding="utf-8",
        )
