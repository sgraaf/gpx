"""I/O functions for reading file formats into GPX.

This module provides functions for reading GPX, GeoJSON, and KML files from disk
and returning GPX objects.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path
from typing import Any

from .convert import from_geo_interface
from .gpx import GPX
from .metadata import Metadata
from .route import Route
from .track import Track
from .track_segment import TrackSegment
from .types import Latitude, Longitude
from .utils import extract_namespaces_from_string, remove_encoding_from_string
from .waypoint import Waypoint

#: KML namespace
KML_NAMESPACE = "http://www.opengis.net/kml/2.2"


def read_gpx(file_path: str | Path) -> GPX:
    """Read a GPX file and return a GPX object.

    Args:
        file_path: Path to the GPX file.

    Returns:
        A GPX object with namespace prefixes preserved.

    Example:
        >>> from gpx import read_gpx
        >>> gpx = read_gpx("path/to/file.gpx")

    """
    with Path(file_path).open(encoding="utf-8") as f:
        gpx_str = f.read()

    # Extract namespace prefixes before parsing (ElementTree loses this info)
    namespaces = extract_namespaces_from_string(gpx_str)

    # Remove encoding declaration if present
    gpx_str = remove_encoding_from_string(gpx_str)

    root = ET.fromstring(gpx_str)
    gpx = GPX.from_xml(root)

    # Preserve the extracted namespace prefixes
    gpx.nsmap = namespaces

    return gpx


def read_geojson(file_path: str | Path, *, creator: str | None = None) -> GPX:
    """Read a GeoJSON file and return a GPX object.

    Args:
        file_path: Path to the GeoJSON file.
        creator: The creator string for the GPX. Defaults to None (uses default).

    Returns:
        A GPX object.

    Example:
        >>> from gpx import read_geojson
        >>> gpx = read_geojson("path/to/file.geojson")

    """
    with Path(file_path).open(encoding="utf-8") as f:
        data = json.load(f)
    return from_geo_interface(data, creator=creator)


def read_kml(file_path: str | Path, *, creator: str | None = None) -> GPX:
    """Read a KML file and return a GPX object.

    Args:
        file_path: Path to the KML file.
        creator: The creator string for the GPX. Defaults to None (uses default).

    Returns:
        A GPX object.

    Example:
        >>> from gpx import read_kml
        >>> gpx = read_kml("path/to/file.kml")

    """
    with Path(file_path).open(encoding="utf-8") as f:
        kml_str = f.read()

    # Remove encoding declaration if present (ET.fromstring doesn't support it)
    if kml_str.startswith("<?xml"):
        end_decl = kml_str.find("?>")
        if end_decl != -1:
            # Check if there's encoding in declaration
            decl = kml_str[: end_decl + 2]
            if "encoding" in decl.lower():
                kml_str = kml_str[end_decl + 2 :].lstrip()

    root = ET.fromstring(kml_str)

    gpx_kwargs: dict[str, Any] = {}
    if creator:
        gpx_kwargs["creator"] = creator

    waypoints: list[Waypoint] = []
    routes: list[Route] = []
    tracks: list[Track] = []
    metadata_name: str | None = None
    metadata_desc: str | None = None

    # Get document name/description if present
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
