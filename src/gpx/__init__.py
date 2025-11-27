"""PyGPX is a Python package that brings support for reading, writing and converting GPX files."""

# ruff: noqa: E402
from pathlib import Path

from lxml import etree

# initialize the GPX schema
gpx_schema = etree.XMLSchema(etree.parse(Path(__file__).parent / "gpx.xsd"))

from .base import GPXModel
from .bounds import Bounds
from .copyright import Copyright
from .email import Email
from .gpx import GPX
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
]
