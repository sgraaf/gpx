"""Conversion functions for converting various formats to GPX.

This module provides functions for converting from GeoJSON, KML, WKB, and WKT
formats to GPX objects.
"""

from __future__ import annotations

import json
import re
import struct
import xml.etree.ElementTree as ET
from decimal import Decimal
from typing import Any

from .gpx import GPX
from .metadata import Metadata
from .route import Route
from .track import Track
from .track_segment import TrackSegment
from .types import Latitude, Longitude
from .waypoint import Waypoint

#: KML namespace
KML_NAMESPACE = "http://www.opengis.net/kml/2.2"

#: WKB geometry type codes
WKB_POINT = 1
WKB_LINESTRING = 2
WKB_POLYGON = 3
WKB_MULTIPOINT = 4
WKB_MULTILINESTRING = 5
WKB_MULTIPOLYGON = 6
WKB_GEOMETRYCOLLECTION = 7

#: Z dimension flag (add to base type for 3D)
WKB_Z_FLAG = 1000
#: EWKB Z flag (high bit)
EWKB_Z_FLAG = 0x80000000


def from_geo_interface(geo: dict[str, Any], *, creator: str | None = None) -> GPX:
    """Convert a GeoJSON-like object (with __geo_interface__) to GPX.

    Args:
        geo: A dictionary with GeoJSON structure or an object with __geo_interface__.
        creator: The creator string for the GPX. Defaults to None (uses default).

    Returns:
        A GPX object.

    Raises:
        ValueError: If the geometry type is not supported.

    """
    # Support objects with __geo_interface__
    if hasattr(geo, "__geo_interface__"):
        geo = geo.__geo_interface__

    gpx_kwargs: dict[str, Any] = {}
    if creator:
        gpx_kwargs["creator"] = creator

    geo_type = geo.get("type")

    if geo_type == "FeatureCollection":
        return _feature_collection_to_gpx(geo, gpx_kwargs)
    if geo_type == "Feature":
        return _feature_to_gpx(geo, gpx_kwargs)
    if geo_type in ("Point", "LineString", "MultiLineString", "MultiPoint"):
        return _geometry_to_gpx(geo, gpx_kwargs)
    if geo_type == "GeometryCollection":
        return _geometry_collection_to_gpx(geo, gpx_kwargs)

    msg = f"Unsupported GeoJSON type: {geo_type}"
    raise ValueError(msg)


def from_geojson(
    geojson: str | dict[str, Any], *, creator: str | None = None
) -> GPX:
    """Convert GeoJSON string or dict to GPX.

    Args:
        geojson: GeoJSON as a string or dictionary.
        creator: The creator string for the GPX. Defaults to None (uses default).

    Returns:
        A GPX object.

    """
    if isinstance(geojson, str):
        geojson = json.loads(geojson)
    return from_geo_interface(geojson, creator=creator)


def from_kml(kml: str | ET.Element, *, creator: str | None = None) -> GPX:  # noqa: C901
    """Convert KML string or Element to GPX.

    Args:
        kml: KML as a string or XML Element.
        creator: The creator string for the GPX. Defaults to None (uses default).

    Returns:
        A GPX object.

    """
    if isinstance(kml, str):
        # Remove encoding declaration if present (ET.fromstring doesn't support it)
        if kml.startswith("<?xml"):
            end_decl = kml.find("?>")
            if end_decl != -1:
                # Check if there's encoding in declaration
                decl = kml[: end_decl + 2]
                if "encoding" in decl.lower():
                    kml = kml[end_decl + 2 :].lstrip()
        root = ET.fromstring(kml)
    else:
        root = kml

    gpx_kwargs: dict[str, Any] = {}
    if creator:
        gpx_kwargs["creator"] = creator

    waypoints: list[Waypoint] = []
    routes: list[Route] = []
    tracks: list[Track] = []
    metadata_name: str | None = None
    metadata_desc: str | None = None

    # Get document name/description if present
    # Try with full namespace tag first, then without
    doc = _find_kml_element(root, "Document")
    if doc is not None:
        name_elem = _find_kml_element(doc, "name")
        if name_elem is not None and name_elem.text:
            metadata_name = name_elem.text
        desc_elem = _find_kml_element(doc, "description")
        if desc_elem is not None and desc_elem.text:
            metadata_desc = desc_elem.text

    # Find all placemarks
    placemarks = _find_all_kml_elements(root, "Placemark")

    for placemark in placemarks:
        _process_kml_placemark(placemark, waypoints, routes, tracks)

    if metadata_name or metadata_desc:
        gpx_kwargs["metadata"] = Metadata(name=metadata_name, desc=metadata_desc)

    return GPX(wpt=waypoints, rte=routes, trk=tracks, **gpx_kwargs)


def from_wkb(wkb: bytes, *, creator: str | None = None) -> GPX:
    """Convert Well-Known Binary (WKB) to GPX.

    Supports both standard WKB and EWKB (Extended WKB) with Z coordinates.

    Args:
        wkb: WKB as bytes.
        creator: The creator string for the GPX. Defaults to None (uses default).

    Returns:
        A GPX object.

    Raises:
        ValueError: If the WKB format is invalid or geometry type is unsupported.

    """
    gpx_kwargs: dict[str, Any] = {}
    if creator:
        gpx_kwargs["creator"] = creator

    geometry, _ = _parse_wkb_geometry(wkb, 0)
    return _wkb_geometry_to_gpx(geometry, gpx_kwargs)


def from_wkt(wkt: str, *, creator: str | None = None) -> GPX:
    """Convert Well-Known Text (WKT) to GPX.

    Args:
        wkt: WKT string.
        creator: The creator string for the GPX. Defaults to None (uses default).

    Returns:
        A GPX object.

    Raises:
        ValueError: If the WKT format is invalid or geometry type is unsupported.

    """
    gpx_kwargs: dict[str, Any] = {}
    if creator:
        gpx_kwargs["creator"] = creator

    geometry = _parse_wkt(wkt)
    return _wkt_geometry_to_gpx(geometry, gpx_kwargs)


# =============================================================================
# GeoJSON Helper Functions
# =============================================================================


def _feature_collection_to_gpx(
    fc: dict[str, Any], gpx_kwargs: dict[str, Any]
) -> GPX:
    """Convert a GeoJSON FeatureCollection to GPX."""
    waypoints: list[Waypoint] = []
    routes: list[Route] = []
    tracks: list[Track] = []

    for feature in fc.get("features", []):
        _process_geojson_feature(feature, waypoints, routes, tracks)

    return GPX(wpt=waypoints, rte=routes, trk=tracks, **gpx_kwargs)


def _feature_to_gpx(feature: dict[str, Any], gpx_kwargs: dict[str, Any]) -> GPX:
    """Convert a GeoJSON Feature to GPX."""
    waypoints: list[Waypoint] = []
    routes: list[Route] = []
    tracks: list[Track] = []

    _process_geojson_feature(feature, waypoints, routes, tracks)

    return GPX(wpt=waypoints, rte=routes, trk=tracks, **gpx_kwargs)


def _geometry_to_gpx(geometry: dict[str, Any], gpx_kwargs: dict[str, Any]) -> GPX:
    """Convert a GeoJSON geometry to GPX."""
    waypoints: list[Waypoint] = []
    routes: list[Route] = []
    tracks: list[Track] = []

    _process_geojson_geometry(geometry, None, waypoints, routes, tracks)

    return GPX(wpt=waypoints, rte=routes, trk=tracks, **gpx_kwargs)


def _geometry_collection_to_gpx(
    gc: dict[str, Any], gpx_kwargs: dict[str, Any]
) -> GPX:
    """Convert a GeoJSON GeometryCollection to GPX."""
    waypoints: list[Waypoint] = []
    routes: list[Route] = []
    tracks: list[Track] = []

    for geometry in gc.get("geometries", []):
        _process_geojson_geometry(geometry, None, waypoints, routes, tracks)

    return GPX(wpt=waypoints, rte=routes, trk=tracks, **gpx_kwargs)


def _process_geojson_feature(
    feature: dict[str, Any],
    waypoints: list[Waypoint],
    routes: list[Route],
    tracks: list[Track],
) -> None:
    """Process a GeoJSON Feature and add to appropriate list."""
    geometry = feature.get("geometry")
    properties = feature.get("properties") or {}
    if geometry:
        _process_geojson_geometry(geometry, properties, waypoints, routes, tracks)


def _process_geojson_geometry(
    geometry: dict[str, Any],
    properties: dict[str, Any] | None,
    waypoints: list[Waypoint],
    routes: list[Route],
    tracks: list[Track],
) -> None:
    """Process a GeoJSON geometry and add to appropriate list."""
    geo_type = geometry.get("type")
    coords = geometry.get("coordinates", [])

    if geo_type == "Point":
        waypoint = _coords_to_waypoint(coords, properties)
        waypoints.append(waypoint)
    elif geo_type == "MultiPoint":
        for coord in coords:
            waypoint = _coords_to_waypoint(coord, properties)
            waypoints.append(waypoint)
    elif geo_type == "LineString":
        route = _coords_to_route(coords, properties)
        routes.append(route)
    elif geo_type == "MultiLineString":
        track = _coords_to_track(coords, properties)
        tracks.append(track)
    elif geo_type == "GeometryCollection":
        for geom in geometry.get("geometries", []):
            _process_geojson_geometry(geom, properties, waypoints, routes, tracks)


def _coords_to_waypoint(
    coords: list[float], properties: dict[str, Any] | None
) -> Waypoint:
    """Convert GeoJSON coordinates to a Waypoint."""
    lon, lat = coords[0], coords[1]
    ele = Decimal(str(coords[2])) if len(coords) > 2 else None  # noqa: PLR2004

    kwargs: dict[str, Any] = {
        "lat": Latitude(str(lat)),
        "lon": Longitude(str(lon)),
    }
    if ele is not None:
        kwargs["ele"] = ele

    if properties:
        if "name" in properties:
            kwargs["name"] = str(properties["name"])
        if "desc" in properties:
            kwargs["desc"] = str(properties["desc"])
        if "cmt" in properties:
            kwargs["cmt"] = str(properties["cmt"])
        if "sym" in properties:
            kwargs["sym"] = str(properties["sym"])
        if "type" in properties:
            kwargs["type"] = str(properties["type"])

    return Waypoint(**kwargs)


def _coords_to_route(
    coords: list[list[float]], properties: dict[str, Any] | None
) -> Route:
    """Convert GeoJSON LineString coordinates to a Route."""
    route_points = [_coords_to_waypoint(coord, None) for coord in coords]

    kwargs: dict[str, Any] = {"rtept": route_points}

    if properties:
        if "name" in properties:
            kwargs["name"] = str(properties["name"])
        if "desc" in properties:
            kwargs["desc"] = str(properties["desc"])
        if "cmt" in properties:
            kwargs["cmt"] = str(properties["cmt"])
        if "type" in properties:
            kwargs["type"] = str(properties["type"])

    return Route(**kwargs)


def _coords_to_track(
    coords: list[list[list[float]]], properties: dict[str, Any] | None
) -> Track:
    """Convert GeoJSON MultiLineString coordinates to a Track."""
    segments = []
    for line_coords in coords:
        points = [_coords_to_waypoint(coord, None) for coord in line_coords]
        segments.append(TrackSegment(trkpt=points))

    kwargs: dict[str, Any] = {"trkseg": segments}

    if properties:
        if "name" in properties:
            kwargs["name"] = str(properties["name"])
        if "desc" in properties:
            kwargs["desc"] = str(properties["desc"])
        if "cmt" in properties:
            kwargs["cmt"] = str(properties["cmt"])
        if "type" in properties:
            kwargs["type"] = str(properties["type"])

    return Track(**kwargs)


# =============================================================================
# KML Helper Functions
# =============================================================================


def _find_kml_element(parent: ET.Element, tag: str) -> ET.Element | None:
    """Find a KML element, handling namespace variations.

    Tries to find the element with the KML namespace first, then without.
    """
    # Try with full namespace tag
    elem = parent.find(f"{{{KML_NAMESPACE}}}{tag}")
    if elem is not None:
        return elem

    # Try without namespace
    elem = parent.find(tag)
    if elem is not None:
        return elem

    return None


def _find_all_kml_elements(parent: ET.Element, tag: str) -> list[ET.Element]:
    """Find all KML elements with a given tag, handling namespace variations."""
    elements = []

    # Try with full namespace
    elements.extend(parent.findall(f".//{{{KML_NAMESPACE}}}{tag}"))

    # Try without namespace
    elements.extend(parent.findall(f".//{tag}"))

    return elements


def _process_kml_placemark(  # noqa: C901
    placemark: ET.Element,
    waypoints: list[Waypoint],
    routes: list[Route],
    tracks: list[Track],
) -> None:
    """Process a KML Placemark and add to appropriate list."""
    # Get name and description
    name_elem = _find_kml_element(placemark, "name")
    name = name_elem.text.strip() if name_elem is not None and name_elem.text else None
    desc_elem = _find_kml_element(placemark, "description")
    desc = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else None

    # Check for Point
    point = _find_kml_element(placemark, "Point")
    if point is not None:
        coords_elem = _find_kml_element(point, "coordinates")
        if coords_elem is not None and coords_elem.text:
            coords = _parse_kml_coordinates(coords_elem.text)
            if coords:
                waypoint = _kml_coords_to_waypoint(coords[0], name, desc)
                waypoints.append(waypoint)
        return

    # Check for LineString
    linestring = _find_kml_element(placemark, "LineString")
    if linestring is not None:
        coords_elem = _find_kml_element(linestring, "coordinates")
        if coords_elem is not None and coords_elem.text:
            coords = _parse_kml_coordinates(coords_elem.text)
            if coords:
                route = _kml_coords_to_route(coords, name, desc)
                routes.append(route)
        return

    # Check for MultiGeometry containing LineStrings (for tracks)
    multigeom = _find_kml_element(placemark, "MultiGeometry")
    if multigeom is not None:
        linestrings = _find_all_kml_elements(multigeom, "LineString")
        if linestrings:
            segments = []
            for ls in linestrings:
                coords_elem = _find_kml_element(ls, "coordinates")
                if coords_elem is not None and coords_elem.text:
                    coords = _parse_kml_coordinates(coords_elem.text)
                    if coords:
                        points = [
                            _kml_coords_to_waypoint(c, None, None) for c in coords
                        ]
                        segments.append(TrackSegment(trkpt=points))
            if segments:
                tracks.append(Track(name=name, desc=desc, trkseg=segments))


def _parse_kml_coordinates(coords_text: str) -> list[tuple[float, float, float | None]]:
    """Parse KML coordinates string.

    KML coordinates are in the format: lon,lat[,alt] lon,lat[,alt] ...
    """
    coords = []
    for coord_str in coords_text.strip().split():
        if not coord_str:
            continue
        parts = coord_str.split(",")
        if len(parts) >= 2:  # noqa: PLR2004
            lon = float(parts[0])
            lat = float(parts[1])
            alt = float(parts[2]) if len(parts) > 2 else None  # noqa: PLR2004
            coords.append((lon, lat, alt))
    return coords


def _kml_coords_to_waypoint(
    coords: tuple[float, float, float | None],
    name: str | None,
    desc: str | None,
) -> Waypoint:
    """Convert KML coordinates to a Waypoint."""
    lon, lat, alt = coords

    kwargs: dict[str, Any] = {
        "lat": Latitude(str(lat)),
        "lon": Longitude(str(lon)),
    }
    if alt is not None:
        kwargs["ele"] = Decimal(str(alt))
    if name:
        kwargs["name"] = name
    if desc:
        kwargs["desc"] = desc

    return Waypoint(**kwargs)


def _kml_coords_to_route(
    coords: list[tuple[float, float, float | None]],
    name: str | None,
    desc: str | None,
) -> Route:
    """Convert KML LineString coordinates to a Route."""
    route_points = [_kml_coords_to_waypoint(c, None, None) for c in coords]

    kwargs: dict[str, Any] = {"rtept": route_points}
    if name:
        kwargs["name"] = name
    if desc:
        kwargs["desc"] = desc

    return Route(**kwargs)


# =============================================================================
# WKB Helper Functions
# =============================================================================


def _parse_wkb_geometry(
    wkb: bytes, offset: int
) -> tuple[dict[str, Any], int]:
    """Parse a WKB geometry and return geometry dict and new offset."""
    if offset >= len(wkb):
        msg = "Invalid WKB: unexpected end of data"
        raise ValueError(msg)

    # Read byte order
    byte_order = wkb[offset]
    offset += 1

    # Determine endianness
    if byte_order == 0:
        endian = ">"  # Big endian (XDR)
    elif byte_order == 1:
        endian = "<"  # Little endian (NDR)
    else:
        msg = f"Invalid WKB byte order: {byte_order}"
        raise ValueError(msg)

    # Read geometry type
    (geom_type,) = struct.unpack(f"{endian}I", wkb[offset : offset + 4])
    offset += 4

    # Check for Z flag (ISO or EWKB style)
    has_z = False
    base_type = geom_type

    if geom_type >= WKB_Z_FLAG:
        # ISO style: type + 1000 for Z
        has_z = True
        base_type = geom_type - WKB_Z_FLAG
    elif geom_type & EWKB_Z_FLAG:
        # EWKB style: high bit set for Z
        has_z = True
        base_type = geom_type & 0x0FFFFFFF

    # Remove M flag if present (type + 2000 or 0x40000000)
    if base_type >= 2000:  # noqa: PLR2004
        base_type -= 2000

    return _parse_wkb_by_type(wkb, offset, endian, base_type, has_z)


def _parse_wkb_by_type(  # noqa: PLR0911
    wkb: bytes, offset: int, endian: str, base_type: int, has_z: bool  # noqa: FBT001
) -> tuple[dict[str, Any], int]:
    """Parse WKB geometry by type."""
    if base_type == WKB_POINT:
        return _parse_wkb_point(wkb, offset, endian, has_z)
    if base_type == WKB_LINESTRING:
        return _parse_wkb_linestring(wkb, offset, endian, has_z)
    if base_type == WKB_MULTIPOINT:
        return _parse_wkb_multipoint(wkb, offset, endian, has_z)
    if base_type == WKB_MULTILINESTRING:
        return _parse_wkb_multilinestring(wkb, offset, endian, has_z)
    if base_type == WKB_GEOMETRYCOLLECTION:
        return _parse_wkb_geometrycollection(wkb, offset, endian)
    if base_type == WKB_POLYGON:
        # Skip polygon - not directly convertible to GPX
        return _parse_wkb_polygon(wkb, offset, endian, has_z)
    if base_type == WKB_MULTIPOLYGON:
        return _parse_wkb_multipolygon(wkb, offset, endian, has_z)

    msg = f"Unsupported WKB geometry type: {base_type}"
    raise ValueError(msg)


def _parse_wkb_point(
    wkb: bytes, offset: int, endian: str, has_z: bool  # noqa: FBT001
) -> tuple[dict[str, Any], int]:
    """Parse WKB Point geometry."""
    coord_size = 24 if has_z else 16

    coords = struct.unpack(
        f"{endian}{'ddd' if has_z else 'dd'}", wkb[offset : offset + coord_size]
    )
    offset += coord_size

    geometry = {
        "type": "Point",
        "coordinates": list(coords),
    }
    return geometry, offset


def _parse_wkb_linestring(
    wkb: bytes, offset: int, endian: str, has_z: bool  # noqa: FBT001
) -> tuple[dict[str, Any], int]:
    """Parse WKB LineString geometry."""
    (num_points,) = struct.unpack(f"{endian}I", wkb[offset : offset + 4])
    offset += 4

    coords = []
    coord_format = f"{endian}{'ddd' if has_z else 'dd'}"
    coord_size = 24 if has_z else 16

    for _ in range(num_points):
        point_coords = struct.unpack(coord_format, wkb[offset : offset + coord_size])
        coords.append(list(point_coords))
        offset += coord_size

    geometry = {
        "type": "LineString",
        "coordinates": coords,
    }
    return geometry, offset


def _parse_wkb_polygon(
    wkb: bytes, offset: int, endian: str, has_z: bool  # noqa: FBT001
) -> tuple[dict[str, Any], int]:
    """Parse WKB Polygon geometry (skipped for GPX conversion)."""
    (num_rings,) = struct.unpack(f"{endian}I", wkb[offset : offset + 4])
    offset += 4

    rings = []
    coord_format = f"{endian}{'ddd' if has_z else 'dd'}"
    coord_size = 24 if has_z else 16

    for _ in range(num_rings):
        (num_points,) = struct.unpack(f"{endian}I", wkb[offset : offset + 4])
        offset += 4

        ring_coords = []
        for _ in range(num_points):
            point_coords = struct.unpack(coord_format, wkb[offset : offset + coord_size])
            ring_coords.append(list(point_coords))
            offset += coord_size
        rings.append(ring_coords)

    geometry = {
        "type": "Polygon",
        "coordinates": rings,
    }
    return geometry, offset


def _parse_wkb_multipoint(
    wkb: bytes, offset: int, endian: str, has_z: bool  # noqa: ARG001, FBT001
) -> tuple[dict[str, Any], int]:
    """Parse WKB MultiPoint geometry."""
    (num_points,) = struct.unpack(f"{endian}I", wkb[offset : offset + 4])
    offset += 4

    coords = []
    for _ in range(num_points):
        point_geom, offset = _parse_wkb_geometry(wkb, offset)
        coords.append(point_geom["coordinates"])

    geometry = {
        "type": "MultiPoint",
        "coordinates": coords,
    }
    return geometry, offset


def _parse_wkb_multilinestring(
    wkb: bytes, offset: int, endian: str, has_z: bool  # noqa: ARG001, FBT001
) -> tuple[dict[str, Any], int]:
    """Parse WKB MultiLineString geometry."""
    (num_lines,) = struct.unpack(f"{endian}I", wkb[offset : offset + 4])
    offset += 4

    coords = []
    for _ in range(num_lines):
        line_geom, offset = _parse_wkb_geometry(wkb, offset)
        coords.append(line_geom["coordinates"])

    geometry = {
        "type": "MultiLineString",
        "coordinates": coords,
    }
    return geometry, offset


def _parse_wkb_multipolygon(
    wkb: bytes, offset: int, endian: str, has_z: bool  # noqa: ARG001, FBT001
) -> tuple[dict[str, Any], int]:
    """Parse WKB MultiPolygon geometry (skipped for GPX conversion)."""
    (num_polys,) = struct.unpack(f"{endian}I", wkb[offset : offset + 4])
    offset += 4

    coords = []
    for _ in range(num_polys):
        poly_geom, offset = _parse_wkb_geometry(wkb, offset)
        coords.append(poly_geom["coordinates"])

    geometry = {
        "type": "MultiPolygon",
        "coordinates": coords,
    }
    return geometry, offset


def _parse_wkb_geometrycollection(
    wkb: bytes, offset: int, endian: str
) -> tuple[dict[str, Any], int]:
    """Parse WKB GeometryCollection."""
    (num_geoms,) = struct.unpack(f"{endian}I", wkb[offset : offset + 4])
    offset += 4

    geometries = []
    for _ in range(num_geoms):
        geom, offset = _parse_wkb_geometry(wkb, offset)
        geometries.append(geom)

    geometry = {
        "type": "GeometryCollection",
        "geometries": geometries,
    }
    return geometry, offset


def _wkb_geometry_to_gpx(
    geometry: dict[str, Any], gpx_kwargs: dict[str, Any]
) -> GPX:
    """Convert parsed WKB geometry to GPX."""
    return _geometry_to_gpx(geometry, gpx_kwargs)


# =============================================================================
# WKT Helper Functions
# =============================================================================


def _parse_wkt(wkt: str) -> dict[str, Any]:  # noqa: PLR0911
    """Parse WKT string into geometry dict."""
    wkt = wkt.strip()

    # Extract geometry type
    paren_idx = wkt.find("(")
    if paren_idx == -1:
        # Handle EMPTY geometries
        if "EMPTY" in wkt.upper():
            type_part = wkt.upper().replace("EMPTY", "").strip()
            type_part = type_part.replace(" Z", "").replace(" M", "").replace(" ZM", "")
            return {"type": _wkt_type_to_geojson(type_part), "coordinates": []}
        msg = f"Invalid WKT: {wkt}"
        raise ValueError(msg)

    type_part = wkt[:paren_idx].strip().upper()
    coords_part = wkt[paren_idx:]

    # Check for Z/M dimensions
    has_z = " Z" in type_part or type_part.endswith("Z")
    type_part = type_part.replace(" Z", "").replace(" M", "").replace(" ZM", "")
    type_part = type_part.rstrip("ZM")

    geojson_type = _wkt_type_to_geojson(type_part)

    if geojson_type == "Point":
        return _parse_wkt_point(coords_part, has_z)
    if geojson_type == "LineString":
        return _parse_wkt_linestring(coords_part, has_z)
    if geojson_type == "Polygon":
        return _parse_wkt_polygon(coords_part, has_z)
    if geojson_type == "MultiPoint":
        return _parse_wkt_multipoint(coords_part, has_z)
    if geojson_type == "MultiLineString":
        return _parse_wkt_multilinestring(coords_part, has_z)
    if geojson_type == "MultiPolygon":
        return _parse_wkt_multipolygon(coords_part, has_z)
    if geojson_type == "GeometryCollection":
        return _parse_wkt_geometrycollection(coords_part)

    msg = f"Unsupported WKT geometry type: {type_part}"
    raise ValueError(msg)


def _wkt_type_to_geojson(wkt_type: str) -> str:
    """Convert WKT type name to GeoJSON type name."""
    type_map = {
        "POINT": "Point",
        "LINESTRING": "LineString",
        "POLYGON": "Polygon",
        "MULTIPOINT": "MultiPoint",
        "MULTILINESTRING": "MultiLineString",
        "MULTIPOLYGON": "MultiPolygon",
        "GEOMETRYCOLLECTION": "GeometryCollection",
    }
    return type_map.get(wkt_type.strip(), wkt_type)


def _parse_wkt_coords(coords_str: str, has_z: bool) -> list[float]:  # noqa: FBT001
    """Parse a single coordinate tuple from WKT."""
    parts = coords_str.strip().split()
    coords = [float(parts[0]), float(parts[1])]
    if has_z and len(parts) > 2:  # noqa: PLR2004
        coords.append(float(parts[2]))
    return coords


def _parse_wkt_point(coords_part: str, has_z: bool) -> dict[str, Any]:  # noqa: FBT001
    """Parse WKT POINT."""
    # Remove outer parentheses
    inner = coords_part.strip()[1:-1].strip()
    coords = _parse_wkt_coords(inner, has_z)
    return {"type": "Point", "coordinates": coords}


def _parse_wkt_linestring(coords_part: str, has_z: bool) -> dict[str, Any]:  # noqa: FBT001
    """Parse WKT LINESTRING."""
    inner = coords_part.strip()[1:-1].strip()
    coords = [_parse_wkt_coords(c.strip(), has_z) for c in inner.split(",")]
    return {"type": "LineString", "coordinates": coords}


def _parse_wkt_polygon(coords_part: str, has_z: bool) -> dict[str, Any]:  # noqa: FBT001
    """Parse WKT POLYGON."""
    # Find all ring coordinates within nested parentheses
    rings = _extract_nested_coords(coords_part)
    parsed_rings = []
    for ring in rings:
        coords = [_parse_wkt_coords(c.strip(), has_z) for c in ring.split(",")]
        parsed_rings.append(coords)
    return {"type": "Polygon", "coordinates": parsed_rings}


def _parse_wkt_multipoint(coords_part: str, has_z: bool) -> dict[str, Any]:  # noqa: FBT001
    """Parse WKT MULTIPOINT."""
    inner = coords_part.strip()[1:-1].strip()
    # MultiPoint can have coords like (x y, x y) or ((x y), (x y))
    if inner.startswith("("):
        # Nested format: ((x y), (x y))
        points = _extract_nested_coords(coords_part)
        coords = [_parse_wkt_coords(p.strip(), has_z) for p in points]
    else:
        # Simple format: (x y, x y)
        coords = [_parse_wkt_coords(c.strip(), has_z) for c in inner.split(",")]
    return {"type": "MultiPoint", "coordinates": coords}


def _parse_wkt_multilinestring(coords_part: str, has_z: bool) -> dict[str, Any]:  # noqa: FBT001
    """Parse WKT MULTILINESTRING."""
    lines = _extract_nested_coords(coords_part)
    coords = []
    for line in lines:
        line_coords = [_parse_wkt_coords(c.strip(), has_z) for c in line.split(",")]
        coords.append(line_coords)
    return {"type": "MultiLineString", "coordinates": coords}


def _parse_wkt_multipolygon(coords_part: str, has_z: bool) -> dict[str, Any]:  # noqa: FBT001
    """Parse WKT MULTIPOLYGON."""
    # MultiPolygon has triple-nested parentheses
    # We need to extract polygon groups first
    inner = coords_part.strip()[1:-1].strip()
    polygons = []

    depth = 0
    current = []
    for char in inner:
        if char == "(":
            depth += 1
            if depth > 1:
                current.append(char)
        elif char == ")":
            depth -= 1
            if depth >= 1:
                current.append(char)
            if depth == 1:
                poly_str = "(" + "".join(current) + ")"
                rings = _extract_nested_coords(poly_str)
                parsed_rings = []
                for ring in rings:
                    coords = [
                        _parse_wkt_coords(c.strip(), has_z) for c in ring.split(",")
                    ]
                    parsed_rings.append(coords)
                polygons.append(parsed_rings)
                current = []
        elif depth > 1 or (depth == 1 and char not in ","):
            current.append(char)

    return {"type": "MultiPolygon", "coordinates": polygons}


def _parse_wkt_geometrycollection(coords_part: str) -> dict[str, Any]:
    """Parse WKT GEOMETRYCOLLECTION."""
    inner = coords_part.strip()[1:-1].strip()
    geometries = []

    # Split on geometry type keywords while preserving them
    pattern = r"(POINT|LINESTRING|POLYGON|MULTIPOINT|MULTILINESTRING|MULTIPOLYGON|GEOMETRYCOLLECTION)"
    parts = re.split(pattern, inner, flags=re.IGNORECASE)

    i = 1
    while i < len(parts):
        geom_type = parts[i]
        if i + 1 < len(parts):
            geom_coords = parts[i + 1].strip()
            if geom_coords.startswith(","):
                geom_coords = geom_coords[1:].strip()
            # Find the matching parentheses
            paren_start = geom_coords.find("(")
            if paren_start != -1:
                depth = 0
                end = paren_start
                for j, char in enumerate(geom_coords[paren_start:], paren_start):
                    if char == "(":
                        depth += 1
                    elif char == ")":
                        depth -= 1
                        if depth == 0:
                            end = j + 1
                            break
                geom_wkt = geom_type + geom_coords[:end]
                geometries.append(_parse_wkt(geom_wkt))
        i += 2

    return {"type": "GeometryCollection", "geometries": geometries}


def _extract_nested_coords(coords_part: str) -> list[str]:
    """Extract coordinate groups from nested parentheses."""
    inner = coords_part.strip()[1:-1].strip()
    groups = []
    depth = 0
    current = []

    for char in inner:
        if char == "(":
            depth += 1
            if depth > 1:
                current.append(char)
        elif char == ")":
            depth -= 1
            if depth >= 1:
                current.append(char)
            if depth == 0 and current:
                groups.append("".join(current).strip())
                current = []
        elif depth >= 1:
            current.append(char)

    # Handle case where there's no nested parens (e.g., simple linestring)
    if not groups and inner:
        groups = [inner]

    return groups


def _wkt_geometry_to_gpx(
    geometry: dict[str, Any], gpx_kwargs: dict[str, Any]
) -> GPX:
    """Convert parsed WKT geometry to GPX."""
    return _geometry_to_gpx(geometry, gpx_kwargs)
