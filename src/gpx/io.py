"""I/O functions for reading and converting file formats.

This module provides functions for reading GPX, GeoJSON, and KML files from disk
and returning GPX objects, as well as for converting files between these formats.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path
from typing import Any

from .convert import from_geo_interface, from_string
from .gpx import GPX
from .metadata import Metadata
from .route import Route
from .track import Track
from .track_segment import TrackSegment
from .types import Latitude, Longitude
from .waypoint import Waypoint

#: KML namespace
KML_NAMESPACE = "http://www.opengis.net/kml/2.2"
#: All supported KML namespaces: OGC KML 2.2 and the legacy Google Earth namespaces
KML_NAMESPACES = (
    KML_NAMESPACE,
    "http://earth.google.com/kml/2.2",
    "http://earth.google.com/kml/2.1",
    "http://earth.google.com/kml/2.0",
)


def read_gpx(file_path: str | Path, *, strict: bool = False) -> GPX:
    """Read a GPX file and return a GPX object.

    Args:
        file_path: Path to the GPX file.
        strict: If True, validate the file against the GPX 1.1 schema before
            parsing and raise :class:`~gpx.validation.InvalidGPXError` if any
            errors are found. Defaults to False (lenient parsing).

    Returns:
        A GPX object with namespace prefixes preserved.

    Raises:
        InvalidGPXError: If ``strict`` is True and the file has schema errors.

    Example:
        >>> from gpx import read_gpx
        >>> gpx = read_gpx("path/to/file.gpx")

    """
    # Pass bytes so the parser honors the encoding in the XML declaration
    return from_string(Path(file_path).read_bytes(), strict=strict)


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

    Raises:
        ValueError: If the root element is not a ``<kml>`` element in one of the
            supported KML namespaces (or in no namespace).

    Example:
        >>> from gpx import read_kml
        >>> gpx = read_kml("path/to/file.kml")

    """
    # ET.parse handles XML declarations (including encoding) natively.
    root = ET.parse(file_path).getroot()
    ns = _kml_namespace_prefix(root)

    gpx_kwargs: dict[str, Any] = {}
    if creator:
        gpx_kwargs["creator"] = creator

    waypoints: list[Waypoint] = []
    routes: list[Route] = []
    tracks: list[Track] = []
    metadata_name: str | None = None
    metadata_desc: str | None = None

    # Get document name/description if present
    doc = root.find(f"{ns}Document")
    if doc is not None:
        name_elem = doc.find(f"{ns}name")
        if name_elem is not None and name_elem.text:
            metadata_name = name_elem.text
        desc_elem = doc.find(f"{ns}description")
        if desc_elem is not None and desc_elem.text:
            metadata_desc = desc_elem.text

    # Find all placemarks
    for placemark in root.iterfind(f".//{ns}Placemark"):
        _process_kml_placemark(placemark, ns, waypoints, routes, tracks)

    if metadata_name or metadata_desc:
        gpx_kwargs["metadata"] = Metadata(name=metadata_name, desc=metadata_desc)

    return GPX(wpt=waypoints, rte=routes, trk=tracks, **gpx_kwargs)


def detect_format(file_path: str | Path) -> str | None:
    """Detect the file format from a file path's extension.

    Args:
        file_path: The file path to detect the format of.

    Returns:
        The detected format ("gpx", "geojson" or "kml"), or None if the
        extension is not recognized.

    Example:
        >>> from gpx import detect_format
        >>> detect_format("route.kml")
        'kml'

    """
    suffix = Path(file_path).suffix.lower()
    format_map = {
        ".gpx": "gpx",
        ".geojson": "geojson",
        ".json": "geojson",
        ".kml": "kml",
    }
    return format_map.get(suffix)


def convert_file(
    input_file: str | Path,
    output_file: str | Path,
    *,
    input_format: str | None = None,
    output_format: str | None = None,
) -> tuple[str, str]:
    """Convert a file between the GPX, GeoJSON and KML file formats.

    Args:
        input_file: Path to the input file.
        output_file: Path to the output file.
        input_format: The input format ("gpx", "geojson" or "kml").
            Defaults to None (auto-detect from the file extension).
        output_format: The output format ("gpx", "geojson" or "kml").
            Defaults to None (auto-detect from the file extension).

    Returns:
        A tuple of the input and output formats used.

    Raises:
        ValueError: If a format is not given and cannot be detected, or if
            a format is not supported.

    Example:
        >>> from gpx import convert_file
        >>> convert_file("input.gpx", "output.geojson")
        ('gpx', 'geojson')

    """
    input_path = Path(input_file)
    output_path = Path(output_file)

    input_format = input_format or detect_format(input_path)
    if not input_format:
        msg = f"Could not detect input format for: {input_path}"
        raise ValueError(msg)

    output_format = output_format or detect_format(output_path)
    if not output_format:
        msg = f"Could not detect output format for: {output_path}"
        raise ValueError(msg)

    gpx = _read_file(input_path, input_format)
    _write_file(gpx, output_path, output_format)

    return input_format, output_format


def _read_file(file_path: Path, file_format: str) -> GPX:
    """Read a file in the given format and return a GPX object."""
    if file_format == "gpx":
        return read_gpx(file_path)
    if file_format == "geojson":
        return read_geojson(file_path)
    if file_format == "kml":
        return read_kml(file_path)
    msg = f"Unsupported input format: {file_format}"
    raise ValueError(msg)


def _write_file(gpx: GPX, file_path: Path, file_format: str) -> None:
    """Write a GPX object to a file in the given format."""
    if file_format == "gpx":
        gpx.write_gpx(file_path)
    elif file_format == "geojson":
        gpx.write_geojson(file_path)
    elif file_format == "kml":
        gpx.write_kml(file_path)
    else:
        msg = f"Unsupported output format: {file_format}"
        raise ValueError(msg)


def _kml_namespace_prefix(root: ET.Element) -> str:
    """Return the Clark-notation namespace prefix (``"{namespace}"``) of a KML document.

    Args:
        root: The root element of the KML document.

    Returns:
        The namespace prefix, or an empty string for a KML document without a
        namespace.

    Raises:
        ValueError: If the root element is not a ``<kml>`` element in one of the
            supported KML namespaces (or in no namespace).

    """
    for namespace in KML_NAMESPACES:
        if root.tag == f"{{{namespace}}}kml":
            return f"{{{namespace}}}"
    if root.tag == "kml":
        return ""
    msg = f"Unsupported KML document: unexpected root element {root.tag!r}"
    raise ValueError(msg)


def _process_kml_placemark(  # noqa: C901
    placemark: ET.Element,
    ns: str,
    waypoints: list[Waypoint],
    routes: list[Route],
    tracks: list[Track],
) -> None:
    """Process a KML Placemark and add to appropriate list."""
    # Get name and description
    name_elem = placemark.find(f"{ns}name")
    name = name_elem.text.strip() if name_elem is not None and name_elem.text else None
    desc_elem = placemark.find(f"{ns}description")
    desc = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else None

    # Check for Point
    point = placemark.find(f"{ns}Point")
    if point is not None:
        coords_elem = point.find(f"{ns}coordinates")
        if coords_elem is not None and coords_elem.text:
            coords = _parse_kml_coordinates(coords_elem.text)
            if coords:
                waypoint = _kml_coords_to_waypoint(coords[0], name, desc)
                waypoints.append(waypoint)
        return

    # Check for LineString
    linestring = placemark.find(f"{ns}LineString")
    if linestring is not None:
        coords_elem = linestring.find(f"{ns}coordinates")
        if coords_elem is not None and coords_elem.text:
            coords = _parse_kml_coordinates(coords_elem.text)
            if coords:
                route = _kml_coords_to_route(coords, name, desc)
                routes.append(route)
        return

    # Check for MultiGeometry containing LineStrings (for tracks)
    multigeom = placemark.find(f"{ns}MultiGeometry")
    if multigeom is not None:
        linestrings = multigeom.findall(f".//{ns}LineString")
        if linestrings:
            segments = []
            for ls in linestrings:
                coords_elem = ls.find(f"{ns}coordinates")
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
