"""gpx is a zero-dependency, pure Python package for reading, manipulating, writing and converting GPX files."""

from .base import GeoGPXModel, GPXModel
from .bounds import Bounds
from .convert import from_geo_interface, from_string, from_wkb, from_wkt
from .copyright import Copyright
from .email import Email
from .extensions import Extensions
from .gpx import GPX
from .io import convert_file, detect_format, read_geojson, read_gpx, read_kml
from .link import Link
from .metadata import Metadata
from .operations import (
    crop,
    filter_points,
    merge,
    reduce_precision,
    reverse,
    shift_time,
    simplify,
    smooth,
    split,
    strip_extensions,
    strip_metadata,
    trim,
)
from .person import Person
from .route import Route
from .track import Track
from .track_segment import TrackSegment
from .types import Degrees, DGPSStation, Fix, Latitude, Longitude
from .waypoint import Waypoint

__all__ = [
    "GPX",
    "Bounds",
    "Copyright",
    "DGPSStation",
    "Degrees",
    "Email",
    "Extensions",
    "Fix",
    "GPXModel",
    "GeoGPXModel",
    "Latitude",
    "Link",
    "Longitude",
    "Metadata",
    "Person",
    "Route",
    "Track",
    "TrackSegment",
    "Waypoint",
    "convert_file",
    "crop",
    "detect_format",
    "filter_points",
    "from_geo_interface",
    "from_string",
    "from_wkb",
    "from_wkt",
    "merge",
    "read_geojson",
    "read_gpx",
    "read_kml",
    "reduce_precision",
    "reverse",
    "shift_time",
    "simplify",
    "smooth",
    "split",
    "strip_extensions",
    "strip_metadata",
    "trim",
]
