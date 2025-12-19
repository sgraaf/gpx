"""gpx is a pure Python package that brings support for reading, manipulating, writing and converting GPX files."""

from .base import GPXModel
from .bounds import Bounds
from .convert import from_geo_interface, from_string, from_wkb, from_wkt
from .copyright import Copyright
from .email import Email
from .gpx import GPX
from .io import read_geojson, read_gpx, read_kml
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
    "from_geo_interface",
    "from_string",
    "from_wkb",
    "from_wkt",
    "read_geojson",
    "read_gpx",
    "read_kml",
]
