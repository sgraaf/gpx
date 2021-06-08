"""PyGPX is a python package that brings support for reading, writing and converting GPX files."""
from lxml import etree

gpx_schema = etree.XMLSchema(etree.parse("http://www.topografix.com/GPX/1/1/gpx.xsd"))

from .gpx import GPX  # noqa
from .waypoint import Waypoint  # noqa
from .route import Route  # noqa
from .track import Track  # noqa

__version__ = "0.1.0"
