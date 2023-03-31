"""PyGPX is a Python package that brings support for reading, writing and converting GPX files."""
# ruff: noqa: E402
from pathlib import Path

from lxml import etree

# initialize the GPX schema
gpx_schema = etree.XMLSchema(etree.parse(Path(__file__).parent / "gpx.xsd"))

from .gpx import GPX
from .route import Route
from .track import Track
from .waypoint import Waypoint

__version__ = "0.1.1"
