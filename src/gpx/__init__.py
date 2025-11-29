"""gpx is a pure Python package that brings support for reading, manipulating, writing and converting GPX files."""

from .base import GPXModel
from .bounds import Bounds
from .copyright import Copyright
from .email import Email
from .gpx import GPX
from .io import (
    from_file,
    from_geojson,
    from_geojson_dict,
    from_kml,
    from_string,
    to_file,
    to_geojson,
    to_geojson_dict,
    to_kml,
    to_string,
)
from .link import Link
from .metadata import Metadata
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
    "Fix",
    "GPXModel",
    "Latitude",
    "Link",
    "Longitude",
    "Metadata",
    "Person",
    "Route",
    "Track",
    "TrackSegment",
    "Waypoint",
    "from_file",
    "from_geojson",
    "from_geojson_dict",
    "from_kml",
    "from_string",
    "to_file",
    "to_geojson",
    "to_geojson_dict",
    "to_kml",
    "to_string",
]
