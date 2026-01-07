"""GPX model for GPX data.

This module provides the GPX model representing the root GPX document,
following the GPX 1.1 specification.
"""

from __future__ import annotations

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

    """

    _tag = "gpx"

    creator: str = "https://github.com/sgraaf/gpx"
    _: KW_ONLY
    metadata: Metadata | None = None
    wpt: list[Waypoint] = field(default_factory=list)
    rte: list[Route] = field(default_factory=list)
    trk: list[Track] = field(default_factory=list)
    extensions: Extensions | None = None

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

        # Register namespaces
        ET.register_namespace("", GPX_NAMESPACE)
        ET.register_namespace("xsi", XSI_NAMESPACE)

        # Create the element with namespace
        element = ET.Element(f"{{{GPX_NAMESPACE}}}{tag}")

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

    def write_kml(  # noqa: C901, PLR0912, PLR0915
        self, file_path: str | Path, *, pretty_print: bool = True
    ) -> None:
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

        # Add document name from metadata if present
        if self.metadata and self.metadata.name:
            name_elem = ET.SubElement(doc, f"{{{kml_ns}}}name")
            name_elem.text = self.metadata.name
        if self.metadata and self.metadata.desc:
            desc_elem = ET.SubElement(doc, f"{{{kml_ns}}}description")
            desc_elem.text = self.metadata.desc

        # Add waypoints as Point placemarks
        for waypoint in self.wpt:
            placemark = ET.SubElement(doc, f"{{{kml_ns}}}Placemark")
            if waypoint.name:
                name_elem = ET.SubElement(placemark, f"{{{kml_ns}}}name")
                name_elem.text = waypoint.name
            if waypoint.desc:
                desc_elem = ET.SubElement(placemark, f"{{{kml_ns}}}description")
                desc_elem.text = waypoint.desc
            point = ET.SubElement(placemark, f"{{{kml_ns}}}Point")
            coords = ET.SubElement(point, f"{{{kml_ns}}}coordinates")
            if waypoint.ele is not None:
                coords.text = f"{waypoint.lon},{waypoint.lat},{waypoint.ele}"
            else:
                coords.text = f"{waypoint.lon},{waypoint.lat}"

        # Add routes as LineString placemarks
        for route in self.rte:
            placemark = ET.SubElement(doc, f"{{{kml_ns}}}Placemark")
            if route.name:
                name_elem = ET.SubElement(placemark, f"{{{kml_ns}}}name")
                name_elem.text = route.name
            if route.desc:
                desc_elem = ET.SubElement(placemark, f"{{{kml_ns}}}description")
                desc_elem.text = route.desc
            linestring = ET.SubElement(placemark, f"{{{kml_ns}}}LineString")
            coords = ET.SubElement(linestring, f"{{{kml_ns}}}coordinates")
            coord_strs = []
            for rtept in route.rtept:
                if rtept.ele is not None:
                    coord_strs.append(f"{rtept.lon},{rtept.lat},{rtept.ele}")
                else:
                    coord_strs.append(f"{rtept.lon},{rtept.lat}")
            coords.text = " ".join(coord_strs)

        # Add tracks as MultiGeometry with LineStrings
        for track in self.trk:
            placemark = ET.SubElement(doc, f"{{{kml_ns}}}Placemark")
            if track.name:
                name_elem = ET.SubElement(placemark, f"{{{kml_ns}}}name")
                name_elem.text = track.name
            if track.desc:
                desc_elem = ET.SubElement(placemark, f"{{{kml_ns}}}description")
                desc_elem.text = track.desc

            if len(track.trkseg) == 1:
                # Single segment: use LineString directly
                linestring = ET.SubElement(placemark, f"{{{kml_ns}}}LineString")
                coords = ET.SubElement(linestring, f"{{{kml_ns}}}coordinates")
                coord_strs = []
                for trkpt in track.trkseg[0].trkpt:
                    if trkpt.ele is not None:
                        coord_strs.append(f"{trkpt.lon},{trkpt.lat},{trkpt.ele}")
                    else:
                        coord_strs.append(f"{trkpt.lon},{trkpt.lat}")
                coords.text = " ".join(coord_strs)
            else:
                # Multiple segments: use MultiGeometry
                multigeom = ET.SubElement(placemark, f"{{{kml_ns}}}MultiGeometry")
                for trkseg in track.trkseg:
                    linestring = ET.SubElement(multigeom, f"{{{kml_ns}}}LineString")
                    coords = ET.SubElement(linestring, f"{{{kml_ns}}}coordinates")
                    coord_strs = []
                    for trkpt in trkseg.trkpt:
                        if trkpt.ele is not None:
                            coord_strs.append(f"{trkpt.lon},{trkpt.lat},{trkpt.ele}")
                        else:
                            coord_strs.append(f"{trkpt.lon},{trkpt.lat}")
                    coords.text = " ".join(coord_strs)

        if pretty_print:
            ET.indent(root, space="  ")

        kml_str = ET.tostring(root, encoding="unicode", xml_declaration=True)
        with Path(file_path).open("w", encoding="utf-8") as f:
            f.write(kml_str)

    # =========================================================================
    # WKT conversion methods
    # =========================================================================

    def to_wkt(self) -> str:  # noqa: C901, PLR0912
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
        geometries = []

        # Add waypoints as POINTs
        for waypoint in self.wpt:
            if waypoint.ele is not None:
                geometries.append(
                    f"POINT Z ({waypoint.lon} {waypoint.lat} {waypoint.ele})"
                )
            else:
                geometries.append(f"POINT ({waypoint.lon} {waypoint.lat})")

        # Add routes as LINESTRINGs
        for route in self.rte:
            coords = []
            has_z = any(rtept.ele is not None for rtept in route.rtept)
            for rtept in route.rtept:
                if has_z:
                    ele = rtept.ele if rtept.ele is not None else 0
                    coords.append(f"{rtept.lon} {rtept.lat} {ele}")
                else:
                    coords.append(f"{rtept.lon} {rtept.lat}")
            if has_z:
                geometries.append(f"LINESTRING Z ({', '.join(coords)})")
            else:
                geometries.append(f"LINESTRING ({', '.join(coords)})")

        # Add tracks as MULTILINESTRINGs
        for track in self.trk:
            lines = []
            has_z = any(
                trkpt.ele is not None
                for trkseg in track.trkseg
                for trkpt in trkseg.trkpt
            )
            for trkseg in track.trkseg:
                coords = []
                for trkpt in trkseg.trkpt:
                    if has_z:
                        ele = trkpt.ele if trkpt.ele is not None else 0
                        coords.append(f"{trkpt.lon} {trkpt.lat} {ele}")
                    else:
                        coords.append(f"{trkpt.lon} {trkpt.lat}")
                lines.append(f"({', '.join(coords)})")
            if has_z:
                geometries.append(f"MULTILINESTRING Z ({', '.join(lines)})")
            else:
                geometries.append(f"MULTILINESTRING ({', '.join(lines)})")

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
        wkb = byte_order_marker

        if has_z:
            wkb += struct.pack(f"{endian}I", 1001)  # Point Z
            wkb += struct.pack(
                f"{endian}ddd",
                float(waypoint.lon),
                float(waypoint.lat),
                float(waypoint.ele),  # type: ignore[arg-type]
            )
        else:
            wkb += struct.pack(f"{endian}I", 1)  # Point
            wkb += struct.pack(f"{endian}dd", float(waypoint.lon), float(waypoint.lat))

        return wkb

    def _route_to_wkb(
        self, route: Route, endian: str, byte_order_marker: bytes
    ) -> bytes:
        """Convert a route to WKB LINESTRING."""
        has_z = any(rtept.ele is not None for rtept in route.rtept)
        wkb = byte_order_marker

        if has_z:
            wkb += struct.pack(f"{endian}I", 1002)  # LineString Z
            wkb += struct.pack(f"{endian}I", len(route.rtept))
            for rtept in route.rtept:
                ele = float(rtept.ele) if rtept.ele is not None else 0.0
                wkb += struct.pack(
                    f"{endian}ddd", float(rtept.lon), float(rtept.lat), ele
                )
        else:
            wkb += struct.pack(f"{endian}I", 2)  # LineString
            wkb += struct.pack(f"{endian}I", len(route.rtept))
            for rtept in route.rtept:
                wkb += struct.pack(f"{endian}dd", float(rtept.lon), float(rtept.lat))

        return wkb

    def _track_to_wkb(
        self, track: Track, endian: str, byte_order_marker: bytes
    ) -> bytes:
        """Convert a track to WKB MULTILINESTRING."""
        has_z = any(
            trkpt.ele is not None for trkseg in track.trkseg for trkpt in trkseg.trkpt
        )
        wkb = byte_order_marker

        if has_z:
            wkb += struct.pack(f"{endian}I", 1005)  # MultiLineString Z
        else:
            wkb += struct.pack(f"{endian}I", 5)  # MultiLineString

        wkb += struct.pack(f"{endian}I", len(track.trkseg))

        for trkseg in track.trkseg:
            # Each LineString in the MultiLineString
            wkb += byte_order_marker
            if has_z:
                wkb += struct.pack(f"{endian}I", 1002)  # LineString Z
                wkb += struct.pack(f"{endian}I", len(trkseg.trkpt))
                for trkpt in trkseg.trkpt:
                    ele = float(trkpt.ele) if trkpt.ele is not None else 0.0
                    wkb += struct.pack(
                        f"{endian}ddd", float(trkpt.lon), float(trkpt.lat), ele
                    )
            else:
                wkb += struct.pack(f"{endian}I", 2)  # LineString
                wkb += struct.pack(f"{endian}I", len(trkseg.trkpt))
                for trkpt in trkseg.trkpt:
                    wkb += struct.pack(
                        f"{endian}dd", float(trkpt.lon), float(trkpt.lat)
                    )

        return wkb
