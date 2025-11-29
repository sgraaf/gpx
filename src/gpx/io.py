"""I/O functions for GPX data.

This module provides functions for reading and writing GPX data in various formats,
including GPX XML, GeoJSON, and KML.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from .gpx import GPX
from .metadata import Metadata
from .route import Route
from .track import Track
from .track_segment import TrackSegment
from .types import Latitude, Longitude
from .utils import from_isoformat, to_isoformat
from .waypoint import Waypoint

if TYPE_CHECKING:
    from pathlib import Path


#: KML 2.2 namespace
KML_NAMESPACE = "http://www.opengis.net/kml/2.2"


# ============================================================================
# GPX I/O Functions
# ============================================================================


def from_file(gpx_file: str | Path) -> GPX:
    """Create a GPX instance from a file.

    Args:
        gpx_file: The file path containing the GPX data.

    Returns:
        The GPX instance.

    Example:
        >>> from gpx.io import from_file
        >>> gpx = from_file("path/to/file.gpx")
        >>> print(gpx.creator)

    """
    return GPX.from_file(gpx_file)


def from_string(gpx_str: str) -> GPX:
    """Create a GPX instance from a string.

    Args:
        gpx_str: The string containing the GPX data.

    Returns:
        The GPX instance.

    Example:
        >>> from gpx.io import from_string
        >>> gpx = from_string('''<?xml version="1.0"?>
        ... <gpx version="1.1" creator="MyApp">
        ...     <metadata><name>My Track</name></metadata>
        ... </gpx>''')
        >>> print(gpx.creator)
        MyApp

    """
    return GPX.from_string(gpx_str)


def to_file(gpx: GPX, gpx_file: str | Path, *, pretty_print: bool = True) -> None:
    """Serialize a GPX instance to a file.

    Args:
        gpx: The GPX instance to serialize.
        gpx_file: The file path to write the GPX data to.
        pretty_print: Whether to format the output with indentation.
            Defaults to True.

    Example:
        >>> from gpx import GPX
        >>> from gpx.io import to_file
        >>> gpx = GPX(creator="MyApp")
        >>> to_file(gpx, "output.gpx")

    """
    gpx.to_file(gpx_file, pretty_print=pretty_print)


def to_string(gpx: GPX, *, pretty_print: bool = True) -> str:
    """Serialize a GPX instance to a string.

    Args:
        gpx: The GPX instance to serialize.
        pretty_print: Whether to format the output with indentation.
            Defaults to True.

    Returns:
        The GPX data as a string.

    Example:
        >>> from gpx import GPX
        >>> from gpx.io import to_string
        >>> gpx = GPX(creator="MyApp")
        >>> xml_string = to_string(gpx)
        >>> print(xml_string[:50])
        <?xml version='1.0' encoding='UTF-8'?>
        <gpx ve

    """
    return gpx.to_string(pretty_print=pretty_print)


# ============================================================================
# GeoJSON I/O Functions
# ============================================================================


def to_geojson_dict(gpx: GPX) -> dict[str, Any]:
    """Convert a GPX instance to a GeoJSON dictionary.

    Args:
        gpx: The GPX instance to convert.

    Returns:
        A dictionary representing a GeoJSON FeatureCollection.

    Example:
        >>> from gpx import GPX
        >>> from gpx.io import to_geojson_dict
        >>> gpx = GPX(creator="MyApp")
        >>> geojson = to_geojson_dict(gpx)
        >>> print(geojson["type"])
        FeatureCollection

    """
    return gpx.__geo_interface__


def to_geojson(gpx: GPX, *, pretty_print: bool = True, **kwargs: Any) -> str:  # noqa: ANN401
    """Convert a GPX instance to a GeoJSON string.

    Args:
        gpx: The GPX instance to convert.
        pretty_print: Whether to format the output with indentation.
            Defaults to True.
        **kwargs: Additional keyword arguments to pass to json.dumps().

    Returns:
        The GeoJSON data as a string.

    Example:
        >>> from gpx import GPX
        >>> from gpx.io import to_geojson
        >>> gpx = GPX(creator="MyApp")
        >>> geojson_string = to_geojson(gpx)

    """
    geojson_dict = to_geojson_dict(gpx)
    if pretty_print:
        kwargs.setdefault("indent", 2)
    return json.dumps(geojson_dict, **kwargs)


def from_geojson_dict(geojson_dict: dict[str, Any]) -> GPX:
    """Create a GPX instance from a GeoJSON dictionary.

    Args:
        geojson_dict: A dictionary representing a GeoJSON FeatureCollection.

    Returns:
        The GPX instance.

    Raises:
        ValueError: If the GeoJSON is not a FeatureCollection or contains
            invalid geometry types.

    Example:
        >>> from gpx.io import from_geojson_dict
        >>> geojson = {
        ...     "type": "FeatureCollection",
        ...     "features": [
        ...         {
        ...             "type": "Feature",
        ...             "geometry": {
        ...                 "type": "Point",
        ...                 "coordinates": [4.9041, 52.3676]
        ...             }
        ...         }
        ...     ]
        ... }
        >>> gpx = from_geojson_dict(geojson)

    """
    if geojson_dict.get("type") != "FeatureCollection":
        msg = "GeoJSON must be a FeatureCollection"
        raise ValueError(msg)

    features = geojson_dict.get("features", [])
    waypoints = []
    routes = []
    tracks = []

    for feature in features:
        # Handle both Feature and bare geometries
        if feature.get("type") == "Feature":
            geometry = feature.get("geometry", {})
            properties = feature.get("properties", {})
        else:
            # Bare geometry
            geometry = feature
            properties = {}

        geometry_type = geometry.get("type")
        coordinates = geometry.get("coordinates", [])

        if geometry_type == "Point":
            waypoint = _geojson_point_to_waypoint(coordinates, properties)
            waypoints.append(waypoint)
        elif geometry_type == "LineString":
            route = _geojson_linestring_to_route(coordinates, properties)
            routes.append(route)
        elif geometry_type == "MultiLineString":
            track = _geojson_multilinestring_to_track(coordinates, properties)
            tracks.append(track)

    return GPX(wpt=waypoints, rte=routes, trk=tracks)


def from_geojson(geojson_str: str) -> GPX:
    """Create a GPX instance from a GeoJSON string.

    Args:
        geojson_str: The string containing the GeoJSON data.

    Returns:
        The GPX instance.

    Raises:
        ValueError: If the GeoJSON is not a FeatureCollection or contains
            invalid geometry types.

    Example:
        >>> from gpx.io import from_geojson
        >>> geojson_str = '''
        ... {
        ...   "type": "FeatureCollection",
        ...   "features": []
        ... }
        ... '''
        >>> gpx = from_geojson(geojson_str)

    """
    geojson_dict = json.loads(geojson_str)
    return from_geojson_dict(geojson_dict)


def _geojson_point_to_waypoint(
    coordinates: list[float], properties: dict[str, Any]
) -> Waypoint:
    """Convert GeoJSON Point coordinates and properties to a Waypoint.

    Args:
        coordinates: List of [lon, lat] or [lon, lat, ele].
        properties: Dictionary of properties.

    Returns:
        A Waypoint instance.

    """
    lon = Longitude(str(coordinates[0]))
    lat = Latitude(str(coordinates[1]))
    ele = Decimal(str(coordinates[2])) if len(coordinates) > 2 else None  # noqa: PLR2004

    # Convert properties to waypoint fields
    waypoint_kwargs: dict[str, Any] = {"lon": lon, "lat": lat}
    if ele is not None:
        waypoint_kwargs["ele"] = ele

    # Map common properties
    if "name" in properties:
        waypoint_kwargs["name"] = properties["name"]
    if "desc" in properties:
        waypoint_kwargs["desc"] = properties["desc"]
    if "cmt" in properties:
        waypoint_kwargs["cmt"] = properties["cmt"]
    if "time" in properties:
        waypoint_kwargs["time"] = _parse_time_property(properties["time"])

    return Waypoint(**waypoint_kwargs)


def _geojson_linestring_to_route(
    coordinates: list[list[float]], properties: dict[str, Any]
) -> Route:
    """Convert GeoJSON LineString coordinates and properties to a Route.

    Args:
        coordinates: List of coordinate arrays.
        properties: Dictionary of properties.

    Returns:
        A Route instance.

    """
    route_points = []
    for coord in coordinates:
        lon = Longitude(str(coord[0]))
        lat = Latitude(str(coord[1]))
        ele = Decimal(str(coord[2])) if len(coord) > 2 else None  # noqa: PLR2004
        waypoint_kwargs: dict[str, Any] = {"lon": lon, "lat": lat}
        if ele is not None:
            waypoint_kwargs["ele"] = ele
        route_points.append(Waypoint(**waypoint_kwargs))

    # Convert properties to route fields
    route_kwargs: dict[str, Any] = {"rtept": route_points}
    if "name" in properties:
        route_kwargs["name"] = properties["name"]
    if "desc" in properties:
        route_kwargs["desc"] = properties["desc"]
    if "cmt" in properties:
        route_kwargs["cmt"] = properties["cmt"]

    return Route(**route_kwargs)


def _geojson_multilinestring_to_track(
    coordinates: list[list[list[float]]], properties: dict[str, Any]
) -> Track:
    """Convert GeoJSON MultiLineString coordinates and properties to a Track.

    Args:
        coordinates: List of LineString coordinate arrays.
        properties: Dictionary of properties.

    Returns:
        A Track instance.

    """
    track_segments = []
    for segment_coords in coordinates:
        track_points = []
        for coord in segment_coords:
            lon = Longitude(str(coord[0]))
            lat = Latitude(str(coord[1]))
            ele = Decimal(str(coord[2])) if len(coord) > 2 else None  # noqa: PLR2004
            waypoint_kwargs: dict[str, Any] = {"lon": lon, "lat": lat}
            if ele is not None:
                waypoint_kwargs["ele"] = ele
            track_points.append(Waypoint(**waypoint_kwargs))
        track_segments.append(TrackSegment(trkpt=track_points))

    # Convert properties to track fields
    track_kwargs: dict[str, Any] = {"trkseg": track_segments}
    if "name" in properties:
        track_kwargs["name"] = properties["name"]
    if "desc" in properties:
        track_kwargs["desc"] = properties["desc"]
    if "cmt" in properties:
        track_kwargs["cmt"] = properties["cmt"]

    return Track(**track_kwargs)


def _parse_time_property(time_value: Any) -> datetime | None:  # noqa: ANN401
    """Parse a time property value to a datetime object.

    Args:
        time_value: The time value (string, int, or datetime).

    Returns:
        A datetime object or None if parsing fails.

    """
    if isinstance(time_value, str):
        try:
            return from_isoformat(time_value)
        except (ValueError, AttributeError):
            return None
    if isinstance(time_value, int):
        try:
            return datetime.fromtimestamp(time_value, tz=None)
        except (ValueError, OSError):
            return None
    return None


# ============================================================================
# KML I/O Functions
# ============================================================================


def to_kml(gpx: GPX, *, pretty_print: bool = True) -> str:
    """Convert a GPX instance to a KML string.

    Args:
        gpx: The GPX instance to convert.
        pretty_print: Whether to format the output with indentation.
            Defaults to True.

    Returns:
        The KML data as a string.

    Example:
        >>> from gpx import GPX
        >>> from gpx.io import to_kml
        >>> gpx = GPX(creator="MyApp")
        >>> kml_string = to_kml(gpx)

    """
    # Register namespace
    ET.register_namespace("", KML_NAMESPACE)

    # Create KML root
    kml = ET.Element(f"{{{KML_NAMESPACE}}}kml")
    document = ET.SubElement(kml, f"{{{KML_NAMESPACE}}}Document")

    # Add metadata as Document name/description
    if gpx.metadata:
        if gpx.metadata.name:
            name_elem = ET.SubElement(document, f"{{{KML_NAMESPACE}}}name")
            name_elem.text = gpx.metadata.name
        if gpx.metadata.desc:
            desc_elem = ET.SubElement(document, f"{{{KML_NAMESPACE}}}description")
            desc_elem.text = gpx.metadata.desc

    # Add waypoints
    if gpx.wpt:
        folder = ET.SubElement(document, f"{{{KML_NAMESPACE}}}Folder")
        folder_name = ET.SubElement(folder, f"{{{KML_NAMESPACE}}}name")
        folder_name.text = "Waypoints"

        for waypoint in gpx.wpt:
            placemark = _waypoint_to_kml_placemark(waypoint)
            folder.append(placemark)

    # Add routes
    if gpx.rte:
        folder = ET.SubElement(document, f"{{{KML_NAMESPACE}}}Folder")
        folder_name = ET.SubElement(folder, f"{{{KML_NAMESPACE}}}name")
        folder_name.text = "Routes"

        for route in gpx.rte:
            placemark = _route_to_kml_placemark(route)
            folder.append(placemark)

    # Add tracks
    if gpx.trk:
        folder = ET.SubElement(document, f"{{{KML_NAMESPACE}}}Folder")
        folder_name = ET.SubElement(folder, f"{{{KML_NAMESPACE}}}name")
        folder_name.text = "Tracks"

        for track in gpx.trk:
            placemark = _track_to_kml_placemark(track)
            folder.append(placemark)

    # Serialize to string
    if pretty_print:
        ET.indent(kml, space="  ")

    xml_bytes = ET.tostring(kml, encoding="utf-8", xml_declaration=True)
    return xml_bytes.decode("utf-8")


def from_kml(kml_str: str) -> GPX:
    """Create a GPX instance from a KML string.

    Args:
        kml_str: The string containing the KML data.

    Returns:
        The GPX instance.

    Example:
        >>> from gpx.io import from_kml
        >>> kml_str = '''<?xml version="1.0" encoding="UTF-8"?>
        ... <kml xmlns="http://www.opengis.net/kml/2.2">
        ...   <Document>
        ...   </Document>
        ... </kml>'''
        >>> gpx = from_kml(kml_str)

    """
    root = ET.fromstring(kml_str)

    # Find the Document element
    document = root.find(f".//{{{KML_NAMESPACE}}}Document")
    if document is None:
        # Try without namespace
        document = root.find(".//Document")
    if document is None:
        msg = "KML must contain a Document element"
        raise ValueError(msg)

    waypoints = []
    routes = []
    tracks = []
    metadata_name = None
    metadata_desc = None

    # Get document-level name and description for metadata
    name_elem = document.find(f"{{{KML_NAMESPACE}}}name")
    if name_elem is not None and name_elem.text:
        metadata_name = name_elem.text

    desc_elem = document.find(f"{{{KML_NAMESPACE}}}description")
    if desc_elem is not None and desc_elem.text:
        metadata_desc = desc_elem.text

    # Parse all Placemarks in the document
    ns = {"kml": KML_NAMESPACE}
    for placemark in document.findall(".//kml:Placemark", ns):
        # Check for MultiGeometry first (track with multiple segments)
        multigeometry = placemark.find(".//kml:MultiGeometry", ns)
        if multigeometry is not None:
            track = _kml_placemark_to_track_multigeometry(placemark, ns)
            tracks.append(track)
            continue

        # Check for Point geometry (waypoint)
        point = placemark.find(".//kml:Point", ns)
        if point is not None:
            waypoint = _kml_placemark_to_waypoint(placemark, ns)
            waypoints.append(waypoint)
            continue

        # Check for LineString geometry (route)
        linestring = placemark.find(".//kml:LineString", ns)
        if linestring is not None:
            route = _kml_placemark_to_route(placemark, ns)
            routes.append(route)
            continue

    # Create metadata if we have name or description
    metadata = None
    if metadata_name or metadata_desc:
        metadata = Metadata(name=metadata_name, desc=metadata_desc)

    return GPX(metadata=metadata, wpt=waypoints, rte=routes, trk=tracks)


def _waypoint_to_kml_placemark(waypoint: Waypoint) -> ET.Element:
    """Convert a Waypoint to a KML Placemark element.

    Args:
        waypoint: The Waypoint instance.

    Returns:
        A KML Placemark element.

    """
    placemark = ET.Element(f"{{{KML_NAMESPACE}}}Placemark")

    # Add name
    if waypoint.name:
        name = ET.SubElement(placemark, f"{{{KML_NAMESPACE}}}name")
        name.text = waypoint.name

    # Add description
    if waypoint.desc:
        desc = ET.SubElement(placemark, f"{{{KML_NAMESPACE}}}description")
        desc.text = waypoint.desc

    # Add Point geometry
    point = ET.SubElement(placemark, f"{{{KML_NAMESPACE}}}Point")
    coordinates = ET.SubElement(point, f"{{{KML_NAMESPACE}}}coordinates")
    if waypoint.ele is not None:
        coordinates.text = f"{waypoint.lon},{waypoint.lat},{waypoint.ele}"
    else:
        coordinates.text = f"{waypoint.lon},{waypoint.lat}"

    # Add TimeStamp if time is present
    if waypoint.time:
        timestamp = ET.SubElement(placemark, f"{{{KML_NAMESPACE}}}TimeStamp")
        when = ET.SubElement(timestamp, f"{{{KML_NAMESPACE}}}when")
        when.text = to_isoformat(waypoint.time)

    return placemark


def _route_to_kml_placemark(route: Route) -> ET.Element:
    """Convert a Route to a KML Placemark element.

    Args:
        route: The Route instance.

    Returns:
        A KML Placemark element.

    """
    placemark = ET.Element(f"{{{KML_NAMESPACE}}}Placemark")

    # Add name
    if route.name:
        name = ET.SubElement(placemark, f"{{{KML_NAMESPACE}}}name")
        name.text = route.name

    # Add description
    if route.desc:
        desc = ET.SubElement(placemark, f"{{{KML_NAMESPACE}}}description")
        desc.text = route.desc

    # Add LineString geometry
    linestring = ET.SubElement(placemark, f"{{{KML_NAMESPACE}}}LineString")
    coordinates = ET.SubElement(linestring, f"{{{KML_NAMESPACE}}}coordinates")

    # Build coordinates string
    coord_strings = []
    for point in route.rtept:
        if point.ele is not None:
            coord_strings.append(f"{point.lon},{point.lat},{point.ele}")
        else:
            coord_strings.append(f"{point.lon},{point.lat}")

    coordinates.text = " ".join(coord_strings)

    return placemark


def _track_to_kml_placemark(track: Track) -> ET.Element:
    """Convert a Track to a KML Placemark element.

    Args:
        track: The Track instance.

    Returns:
        A KML Placemark element.

    """
    placemark = ET.Element(f"{{{KML_NAMESPACE}}}Placemark")

    # Add name
    if track.name:
        name = ET.SubElement(placemark, f"{{{KML_NAMESPACE}}}name")
        name.text = track.name

    # Add description
    if track.desc:
        desc = ET.SubElement(placemark, f"{{{KML_NAMESPACE}}}description")
        desc.text = track.desc

    # Always use MultiGeometry for tracks to distinguish from routes
    # This ensures proper roundtrip conversion
    multigeometry = ET.SubElement(placemark, f"{{{KML_NAMESPACE}}}MultiGeometry")
    for segment in track.trkseg:
        linestring = ET.SubElement(multigeometry, f"{{{KML_NAMESPACE}}}LineString")
        coordinates = ET.SubElement(linestring, f"{{{KML_NAMESPACE}}}coordinates")

        # Build coordinates string
        coord_strings = []
        for point in segment.trkpt:
            if point.ele is not None:
                coord_strings.append(f"{point.lon},{point.lat},{point.ele}")
            else:
                coord_strings.append(f"{point.lon},{point.lat}")

        coordinates.text = " ".join(coord_strings)

    return placemark


def _kml_placemark_to_waypoint(
    placemark: ET.Element, ns: dict[str, str]
) -> Waypoint:
    """Convert a KML Placemark with Point geometry to a Waypoint.

    Args:
        placemark: The Placemark element.
        ns: Namespace dictionary.

    Returns:
        A Waypoint instance.

    """
    # Get name
    name_elem = placemark.find("kml:name", ns)
    name = name_elem.text if name_elem is not None and name_elem.text else None

    # Get description
    desc_elem = placemark.find("kml:description", ns)
    desc = desc_elem.text if desc_elem is not None and desc_elem.text else None

    # Get time
    time = None
    timestamp_elem = placemark.find("kml:TimeStamp/kml:when", ns)
    if timestamp_elem is not None and timestamp_elem.text:
        time = from_isoformat(timestamp_elem.text)

    # Get coordinates
    point = placemark.find("kml:Point/kml:coordinates", ns)
    if point is None or not point.text:
        msg = "Placemark must contain Point coordinates"
        raise ValueError(msg)

    coords = point.text.strip().split(",")
    lon = Longitude(coords[0])
    lat = Latitude(coords[1])
    ele = Decimal(coords[2]) if len(coords) > 2 else None  # noqa: PLR2004

    waypoint_kwargs: dict[str, Any] = {"lon": lon, "lat": lat}
    if ele is not None:
        waypoint_kwargs["ele"] = ele
    if name is not None:
        waypoint_kwargs["name"] = name
    if desc is not None:
        waypoint_kwargs["desc"] = desc
    if time is not None:
        waypoint_kwargs["time"] = time

    return Waypoint(**waypoint_kwargs)


def _kml_placemark_to_route(placemark: ET.Element, ns: dict[str, str]) -> Route:
    """Convert a KML Placemark with LineString geometry to a Route.

    Args:
        placemark: The Placemark element.
        ns: Namespace dictionary.

    Returns:
        A Route instance.

    """
    # Get name
    name_elem = placemark.find("kml:name", ns)
    name = name_elem.text if name_elem is not None and name_elem.text else None

    # Get description
    desc_elem = placemark.find("kml:description", ns)
    desc = desc_elem.text if desc_elem is not None and desc_elem.text else None

    # Get coordinates
    linestring = placemark.find("kml:LineString/kml:coordinates", ns)
    if linestring is None or not linestring.text:
        msg = "Placemark must contain LineString coordinates"
        raise ValueError(msg)

    # Parse coordinates
    route_points = []
    for coord_str in linestring.text.strip().split():
        coords = coord_str.split(",")
        lon = Longitude(coords[0])
        lat = Latitude(coords[1])
        ele = Decimal(coords[2]) if len(coords) > 2 else None  # noqa: PLR2004

        waypoint_kwargs: dict[str, Any] = {"lon": lon, "lat": lat}
        if ele is not None:
            waypoint_kwargs["ele"] = ele
        route_points.append(Waypoint(**waypoint_kwargs))

    route_kwargs: dict[str, Any] = {"rtept": route_points}
    if name is not None:
        route_kwargs["name"] = name
    if desc is not None:
        route_kwargs["desc"] = desc

    return Route(**route_kwargs)


def _kml_placemark_to_track_multigeometry(
    placemark: ET.Element, ns: dict[str, str]
) -> Track:
    """Convert a KML Placemark with MultiGeometry to a Track.

    Args:
        placemark: The Placemark element.
        ns: Namespace dictionary.

    Returns:
        A Track instance.

    """
    # Get name
    name_elem = placemark.find("kml:name", ns)
    name = name_elem.text if name_elem is not None and name_elem.text else None

    # Get description
    desc_elem = placemark.find("kml:description", ns)
    desc = desc_elem.text if desc_elem is not None and desc_elem.text else None

    # Get all LineString elements within MultiGeometry
    multigeometry = placemark.find("kml:MultiGeometry", ns)
    if multigeometry is None:
        msg = "Placemark must contain MultiGeometry"
        raise ValueError(msg)

    track_segments = []
    for linestring_elem in multigeometry.findall("kml:LineString/kml:coordinates", ns):
        if linestring_elem.text:
            track_points = []
            for coord_str in linestring_elem.text.strip().split():
                coords = coord_str.split(",")
                lon = Longitude(coords[0])
                lat = Latitude(coords[1])
                ele = Decimal(coords[2]) if len(coords) > 2 else None  # noqa: PLR2004

                waypoint_kwargs: dict[str, Any] = {"lon": lon, "lat": lat}
                if ele is not None:
                    waypoint_kwargs["ele"] = ele
                track_points.append(Waypoint(**waypoint_kwargs))

            track_segments.append(TrackSegment(trkpt=track_points))

    track_kwargs: dict[str, Any] = {"trkseg": track_segments}
    if name is not None:
        track_kwargs["name"] = name
    if desc is not None:
        track_kwargs["desc"] = desc

    return Track(**track_kwargs)
