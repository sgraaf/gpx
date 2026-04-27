"""GPX model for GPX data.

This module provides the GPX model representing the root GPX document,
following the GPX 1.1 specification.
"""

from __future__ import annotations

import contextlib
import json
import struct
import xml.etree.ElementTree as ET
from dataclasses import KW_ONLY, dataclass, field
from pathlib import Path
from typing import Any

from .base import GPXModel
from .extensions import Extensions  # noqa: TC001
from .metadata import Metadata  # noqa: TC001
from .route import Route  # noqa: TC001
from .track import Track  # noqa: TC001
from .utils import build_to_xml
from .waypoint import Waypoint  # noqa: TC001

#: GPX 1.1 namespace
GPX_NAMESPACE = "http://www.topografix.com/GPX/1/1"
#: XML Schema instance namespace
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"


def _kml_add_name_desc(
    parent: ET.Element, ns: str, name: str | None, desc: str | None
) -> None:
    """Append optional <name> / <description> children in the KML namespace."""
    if name:
        ET.SubElement(parent, f"{{{ns}}}name").text = name
    if desc:
        ET.SubElement(parent, f"{{{ns}}}description").text = desc


def _kml_set_coords(parent: ET.Element, ns: str, points: list[Waypoint]) -> None:
    """Append a <coordinates> child rendering ``points`` as KML coordinate text.

    Each point becomes ``"lon,lat"`` or ``"lon,lat,ele"``; multiple points are
    space-separated (KML's expected format).
    """
    coords = ET.SubElement(parent, f"{{{ns}}}coordinates")
    coords.text = " ".join(
        f"{p.lon},{p.lat},{p.ele}" if p.ele is not None else f"{p.lon},{p.lat}"
        for p in points
    )


def _wkt_type(base: str, has_z: bool) -> str:  # noqa: FBT001
    """Append the ``Z`` dimension suffix to a WKT type name when needed."""
    return f"{base} Z" if has_z else base


def _wkt_coord(point: Waypoint, *, has_z: bool) -> str:
    """Render a single waypoint as a WKT coordinate (``"lon lat"`` or ``"lon lat ele"``).

    When ``has_z`` is True and the point has no elevation, ``0`` is emitted
    so all coordinates in a geometry have matching dimensionality.
    """
    if has_z:
        ele = point.ele if point.ele is not None else 0
        return f"{point.lon} {point.lat} {ele}"
    return f"{point.lon} {point.lat}"


def _wkb_pack_point(endian: str, point: Waypoint, *, has_z: bool) -> bytes:
    """Pack a single waypoint's coordinates as little/big-endian doubles.

    When ``has_z`` is True and the point has no elevation, ``0.0`` is packed
    so all coordinates in a geometry share the same dimensionality.
    """
    if has_z:
        ele = float(point.ele) if point.ele is not None else 0.0
        return struct.pack(f"{endian}ddd", float(point.lon), float(point.lat), ele)
    return struct.pack(f"{endian}dd", float(point.lon), float(point.lat))


def _wkb_linestring_body(endian: str, points: list[Waypoint], *, has_z: bool) -> bytes:
    """Build a WKB LINESTRING body (type code + count + packed points).

    The leading byte-order marker is left to the caller, since LineStrings
    appear both as standalone geometries and as members of MultiLineStrings.
    """
    body = struct.pack(f"{endian}I", 1002 if has_z else 2)
    body += struct.pack(f"{endian}I", len(points))
    for point in points:
        body += _wkb_pack_point(endian, point, has_z=has_z)
    return body


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
            Defaults to "https://github.com/sgraaf/gpx".
        metadata: Metadata about the file. Defaults to None.
        wpt: List of waypoints. Defaults to empty list.
        rte: List of routes. Defaults to empty list.
        trk: List of tracks. Defaults to empty list.
        extensions: Extension elements from other XML namespaces. Defaults to None.
        nsmap: Namespace prefix mappings from the original XML. Defaults to None.
            This is used internally to preserve namespace prefixes during
            round-trip parsing. Users typically don't need to set this.

    """

    _tag = "gpx"

    creator: str = "https://github.com/sgraaf/gpx"
    _: KW_ONLY
    metadata: Metadata | None = None
    wpt: list[Waypoint] = field(default_factory=list)
    rte: list[Route] = field(default_factory=list)
    trk: list[Track] = field(default_factory=list)
    extensions: Extensions | None = None
    nsmap: dict[str, str] | None = field(default=None, repr=False)

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
    ) -> ET.Element:
        """Convert the GPX to an XML element.

        Args:
            tag: The XML tag name. Defaults to "gpx".
            nsmap: Optional namespace mapping. Defaults to GPX 1.1 namespace
                with XML Schema instance namespace. If the GPX instance has
                stored namespace mappings (from parsing), those will be used
                to preserve original namespace prefixes.

        Returns:
            The XML element.

        """
        if tag is None:
            tag = self._tag

        # Use stored namespace mappings if available to preserve prefixes
        if nsmap is None:
            if self.nsmap:
                # Build nsmap from stored prefixes, converting to the format
                # expected by build_to_xml (prefix -> URI, with None for default)
                nsmap = {}
                for prefix, uri in self.nsmap.items():
                    # Empty string prefix means default namespace
                    key: str | None = None if prefix == "" else prefix
                    nsmap[key] = uri

                # Ensure xsi namespace is included if not already present
                if "xsi" not in self.nsmap:
                    nsmap["xsi"] = XSI_NAMESPACE
            else:
                # No stored namespaces, use defaults
                nsmap = {
                    None: GPX_NAMESPACE,
                    "xsi": XSI_NAMESPACE,
                }

        # Register namespaces with their original prefixes
        for prefix_key, uri in nsmap.items():
            if prefix_key is None:
                # Register default namespace
                ET.register_namespace("", uri)
            elif isinstance(prefix_key, str) and not prefix_key.startswith("xml"):
                # Only register non-reserved prefixes
                # Skip prefixes starting with "xml" (reserved by XML spec)
                with contextlib.suppress(ValueError):
                    # If registration fails, ElementTree will generate a prefix automatically
                    ET.register_namespace(prefix_key, uri)

        # Create the element with namespace
        default_ns = nsmap.get(None, GPX_NAMESPACE)
        element = ET.Element(f"{{{default_ns}}}{tag}")

        # Add GPX-specific attributes
        element.set("version", "1.1")
        element.set(
            f"{{{XSI_NAMESPACE}}}schemaLocation",
            f"{GPX_NAMESPACE} {GPX_NAMESPACE}/gpx.xsd",
        )

        # Use parent's build_to_xml for fields
        build_to_xml(self, element, nsmap=nsmap)

        return element

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
        if pretty_print:
            ET.indent(element, space="  ")
        xml_bytes = ET.tostring(element, encoding="utf-8", xml_declaration=True)
        return xml_bytes.decode("utf-8")

    # =========================================================================
    # GPX file methods
    # =========================================================================

    def write_gpx(self, file_path: str | Path, *, pretty_print: bool = True) -> None:
        """Write the GPX to a file.

        Args:
            file_path: The file path to write the GPX data to.
            pretty_print: Whether to format the output with indentation.
                Defaults to True.

        Example:
            >>> from gpx import GPX
            >>> gpx = GPX(creator="MyApp")
            >>> gpx.write_gpx("output.gpx")

        """
        element = self.to_xml()
        if pretty_print:
            ET.indent(element, space="  ")
        tree = ET.ElementTree(element)
        tree.write(str(file_path), xml_declaration=True, encoding="utf-8")

    # =========================================================================
    # GeoJSON file methods
    # =========================================================================

    def write_geojson(self, file_path: str | Path, *, indent: int | None = 2) -> None:
        """Write the GPX to a GeoJSON file.

        Args:
            file_path: The file path to write the GeoJSON data to.
            indent: Indentation level for pretty printing. Defaults to 2.

        Example:
            >>> from gpx import GPX
            >>> gpx = GPX()
            >>> gpx.write_geojson("output.geojson")

        """
        with Path(file_path).open("w", encoding="utf-8") as f:
            json.dump(self.__geo_interface__, f, indent=indent)

    # =========================================================================
    # KML file methods
    # =========================================================================

    def write_kml(self, file_path: str | Path, *, pretty_print: bool = True) -> None:
        """Write the GPX to a KML file.

        Args:
            file_path: The file path to write the KML data to.
            pretty_print: Whether to format the output with indentation.
                Defaults to True.

        Example:
            >>> from gpx import GPX
            >>> gpx = GPX()
            >>> gpx.write_kml("output.kml")

        """
        kml_ns = "http://www.opengis.net/kml/2.2"
        ET.register_namespace("", kml_ns)

        root = ET.Element(f"{{{kml_ns}}}kml")
        doc = ET.SubElement(root, f"{{{kml_ns}}}Document")

        if self.metadata:
            _kml_add_name_desc(doc, kml_ns, self.metadata.name, self.metadata.desc)

        for waypoint in self.wpt:
            placemark = ET.SubElement(doc, f"{{{kml_ns}}}Placemark")
            _kml_add_name_desc(placemark, kml_ns, waypoint.name, waypoint.desc)
            point = ET.SubElement(placemark, f"{{{kml_ns}}}Point")
            _kml_set_coords(point, kml_ns, [waypoint])

        for route in self.rte:
            placemark = ET.SubElement(doc, f"{{{kml_ns}}}Placemark")
            _kml_add_name_desc(placemark, kml_ns, route.name, route.desc)
            linestring = ET.SubElement(placemark, f"{{{kml_ns}}}LineString")
            _kml_set_coords(linestring, kml_ns, route.rtept)

        for track in self.trk:
            placemark = ET.SubElement(doc, f"{{{kml_ns}}}Placemark")
            _kml_add_name_desc(placemark, kml_ns, track.name, track.desc)

            if len(track.trkseg) == 1:
                linestring = ET.SubElement(placemark, f"{{{kml_ns}}}LineString")
                _kml_set_coords(linestring, kml_ns, track.trkseg[0].trkpt)
            else:
                multigeom = ET.SubElement(placemark, f"{{{kml_ns}}}MultiGeometry")
                for trkseg in track.trkseg:
                    linestring = ET.SubElement(multigeom, f"{{{kml_ns}}}LineString")
                    _kml_set_coords(linestring, kml_ns, trkseg.trkpt)

        if pretty_print:
            ET.indent(root, space="  ")

        kml_str = ET.tostring(root, encoding="unicode", xml_declaration=True)
        with Path(file_path).open("w", encoding="utf-8") as f:
            f.write(kml_str)

    # =========================================================================
    # WKT conversion methods
    # =========================================================================

    def to_wkt(self) -> str:
        """Convert the GPX to a WKT (Well-Known Text) string.

        Returns a GeometryCollection containing all waypoints, routes, and tracks.

        Returns:
            A WKT string representation of the GPX data.

        Example:
            >>> from gpx import GPX, Waypoint
            >>> from decimal import Decimal
            >>> gpx = GPX(wpt=[Waypoint(Decimal("52.0"), Decimal("4.0"))])
            >>> print(gpx.to_wkt())
            GEOMETRYCOLLECTION (POINT (4.0 52.0))

        """
        geometries: list[str] = []

        for waypoint in self.wpt:
            has_z = waypoint.ele is not None
            geometries.append(
                f"{_wkt_type('POINT', has_z)} ({_wkt_coord(waypoint, has_z=has_z)})"
            )

        for route in self.rte:
            has_z = any(p.ele is not None for p in route.rtept)
            coords = ", ".join(_wkt_coord(p, has_z=has_z) for p in route.rtept)
            geometries.append(f"{_wkt_type('LINESTRING', has_z)} ({coords})")

        for track in self.trk:
            has_z = any(p.ele is not None for seg in track.trkseg for p in seg.trkpt)
            lines = ", ".join(
                f"({', '.join(_wkt_coord(p, has_z=has_z) for p in seg.trkpt)})"
                for seg in track.trkseg
            )
            geometries.append(f"{_wkt_type('MULTILINESTRING', has_z)} ({lines})")

        if len(geometries) == 1:
            return geometries[0]
        return f"GEOMETRYCOLLECTION ({', '.join(geometries)})"

    # =========================================================================
    # WKB conversion methods
    # =========================================================================

    def to_wkb(self, *, byte_order: str = "little") -> bytes:
        """Convert the GPX to WKB (Well-Known Binary).

        Returns a GeometryCollection containing all waypoints, routes, and tracks.

        Args:
            byte_order: Byte order for the binary data. Either "little" (NDR)
                or "big" (XDR). Defaults to "little".

        Returns:
            WKB bytes representation of the GPX data.

        Example:
            >>> from gpx import GPX, Waypoint
            >>> from decimal import Decimal
            >>> gpx = GPX(wpt=[Waypoint(Decimal("52.0"), Decimal("4.0"))])
            >>> wkb = gpx.to_wkb()

        """
        endian = "<" if byte_order == "little" else ">"
        byte_order_marker = b"\x01" if byte_order == "little" else b"\x00"

        geometries_wkb = []

        # Convert waypoints to WKB POINTs
        for waypoint in self.wpt:
            geom_wkb = self._waypoint_to_wkb(waypoint, endian, byte_order_marker)
            geometries_wkb.append(geom_wkb)

        # Convert routes to WKB LINESTRINGs
        for route in self.rte:
            geom_wkb = self._route_to_wkb(route, endian, byte_order_marker)
            geometries_wkb.append(geom_wkb)

        # Convert tracks to WKB MULTILINESTRINGs
        for track in self.trk:
            geom_wkb = self._track_to_wkb(track, endian, byte_order_marker)
            geometries_wkb.append(geom_wkb)

        if len(geometries_wkb) == 1:
            return geometries_wkb[0]

        # Build GeometryCollection
        wkb = byte_order_marker
        wkb += struct.pack(f"{endian}I", 7)  # GeometryCollection type
        wkb += struct.pack(f"{endian}I", len(geometries_wkb))
        for geom in geometries_wkb:
            wkb += geom

        return wkb

    def _waypoint_to_wkb(
        self, waypoint: Waypoint, endian: str, byte_order_marker: bytes
    ) -> bytes:
        """Convert a waypoint to WKB POINT."""
        has_z = waypoint.ele is not None
        return (
            byte_order_marker
            + struct.pack(f"{endian}I", 1001 if has_z else 1)
            + _wkb_pack_point(endian, waypoint, has_z=has_z)
        )

    def _route_to_wkb(
        self, route: Route, endian: str, byte_order_marker: bytes
    ) -> bytes:
        """Convert a route to WKB LINESTRING."""
        has_z = any(p.ele is not None for p in route.rtept)
        return byte_order_marker + _wkb_linestring_body(
            endian, route.rtept, has_z=has_z
        )

    def _track_to_wkb(
        self, track: Track, endian: str, byte_order_marker: bytes
    ) -> bytes:
        """Convert a track to WKB MULTILINESTRING."""
        has_z = any(p.ele is not None for seg in track.trkseg for p in seg.trkpt)
        wkb = (
            byte_order_marker
            + struct.pack(f"{endian}I", 1005 if has_z else 5)
            + struct.pack(f"{endian}I", len(track.trkseg))
        )
        for trkseg in track.trkseg:
            wkb += byte_order_marker + _wkb_linestring_body(
                endian, trkseg.trkpt, has_z=has_z
            )
        return wkb
