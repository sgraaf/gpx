"""GPX model for GPX data.

This module provides the GPX model representing the root GPX document,
following the GPX 1.1 specification.
"""

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass, field

from lxml import etree

from .base import GPXModel
from .metadata import Metadata  # noqa: TC001
from .route import Route  # noqa: TC001
from .track import Track  # noqa: TC001
from .utils import build_to_xml
from .waypoint import Waypoint  # noqa: TC001

#: GPX 1.1 namespace
GPX_NAMESPACE = "http://www.topografix.com/GPX/1/1"
#: XML Schema instance namespace
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"


@dataclass(slots=True)
class GPX(GPXModel):
    """The root GPX document.

    GPX documents contain a metadata header, followed by waypoints, routes, and
    tracks. You can add your own elements to the extensions section of the GPX
    document.

    Note: The GPX version is always "1.1" per the specification and is
    automatically set during XML serialization.

    Args:
        creator: The name or URL of the software that created the GPX document.
        metadata: Metadata about the file. Defaults to None.
        wpt: List of waypoints. Defaults to empty list.
        rte: List of routes. Defaults to empty list.
        trk: List of tracks. Defaults to empty list.

    """

    _tag = "gpx"

    creator: str
    _: KW_ONLY
    metadata: Metadata | None = None
    wpt: list[Waypoint] = field(default_factory=list)
    rte: list[Route] = field(default_factory=list)
    trk: list[Track] = field(default_factory=list)

    def to_xml(
        self, tag: str | None = None, nsmap: dict[str | None, str] | None = None
    ) -> etree._Element:
        """Convert the GPX to an XML element.

        Args:
            tag: The XML tag name. Defaults to "gpx".
            nsmap: Optional namespace mapping. Defaults to GPX 1.1 namespace
                with XML Schema instance namespace.

        Returns:
            The XML element.

        """
        if tag is None:
            tag = self._tag

        if nsmap is None:
            nsmap = {
                None: GPX_NAMESPACE,
                "xsi": XSI_NAMESPACE,
            }

        # Create the element with namespaces
        element = etree.Element(tag, nsmap=nsmap)

        # Add GPX-specific attributes
        element.set("version", "1.1")
        element.set(
            f"{{{XSI_NAMESPACE}}}schemaLocation",
            f"{GPX_NAMESPACE} {GPX_NAMESPACE}/gpx.xsd",
        )

        # Use parent's build_to_xml for fields
        build_to_xml(self, element, nsmap=nsmap)

        return element
