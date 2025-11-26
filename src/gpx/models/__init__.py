"""GPX dataclass-based models.

This package provides dataclass-based models for GPX elements following the
GPX 1.1 specification as closely as possible.
"""

from __future__ import annotations

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
from .waypoint import Waypoint

__all__ = [
    "Bounds",
    "Copyright",
    "Email",
    "GPX",
    "GPXModel",
    "Link",
    "Metadata",
    "Person",
    "Route",
    "Track",
    "TrackSegment",
    "Waypoint",
]
