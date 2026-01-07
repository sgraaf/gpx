"""GPX Extensions container for arbitrary namespace extensions.

This module provides the Extensions class that stores raw XML elements from
any namespace, enabling lossless round-trip parsing while providing convenient
accessor methods for reading and writing extension data.
"""

from __future__ import annotations

import copy
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(slots=True)
class Extensions:
    """Container for GPX extension elements from any namespace.

    Stores raw XML elements from extension namespaces (non-GPX namespaces),
    enabling lossless round-trip parsing. Provides convenient accessor methods
    for reading and writing extension data without requiring knowledge of
    specific extension schemas.

    This class is schema-agnostic and works with ANY GPX extension, including
    but not limited to Garmin, Strava, Cluetrust, and custom extensions.

    Args:
        elements: List of XML elements from extension namespaces.

    Example:
        Reading extension data::

            from gpx import read_gpx

            gpx = read_gpx("activity.gpx")

            # Define namespace for the extension you're looking for
            GARMIN_TPX = "http://www.garmin.com/xmlschemas/TrackPointExtension/v2"

            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        if point.extensions:
                            hr = point.extensions.get_text("hr", namespace=GARMIN_TPX)
                            if hr:
                                print(f"Heart rate: {hr} bpm")

        Creating extension data::

            import xml.etree.ElementTree as ET
            from gpx import Waypoint, Extensions

            # Register namespace prefix
            GARMIN_TPX = "http://www.garmin.com/xmlschemas/TrackPointExtension/v2"
            ET.register_namespace("gpxtpx", GARMIN_TPX)

            # Create extension element
            tpx = ET.Element(f"{{{GARMIN_TPX}}}TrackPointExtension")
            hr = ET.SubElement(tpx, f"{{{GARMIN_TPX}}}hr")
            hr.text = "142"

            # Attach to waypoint
            point = Waypoint(lat=..., lon=..., extensions=Extensions(elements=[tpx]))

    """

    _tag = "extensions"

    elements: list[ET.Element] = field(default_factory=list)

    def __bool__(self) -> bool:
        """Return True if there are any extension elements."""
        return bool(self.elements)

    def __len__(self) -> int:
        """Return the number of top-level extension elements."""
        return len(self.elements)

    def __iter__(self) -> Iterator[ET.Element]:
        """Iterate over top-level extension elements."""
        return iter(self.elements)

    def __contains__(self, item: str | tuple[str, str]) -> bool:
        """Check if an extension element exists.

        Args:
            item: Either a tag name (searches all namespaces) or a tuple of
                (namespace, tag) for namespace-specific lookup.

        Returns:
            True if the element exists, False otherwise.

        Example:
            >>> "hr" in extensions  # Any namespace
            True
            >>> (GARMIN_NS, "hr") in extensions  # Specific namespace
            True

        """
        if isinstance(item, tuple):
            namespace, tag = item
            return self.get_text(tag, namespace=namespace) is not None
        return self.get_text(item) is not None

    def copy(self) -> Extensions:
        """Create a deep copy of this Extensions instance.

        Returns:
            A new Extensions instance with copies of all elements.

        """
        return Extensions(elements=[copy.deepcopy(elem) for elem in self.elements])

    def find(
        self,
        path: str,
        namespaces: dict[str, str] | None = None,
    ) -> ET.Element | None:
        """Find a child element using XPath.

        Searches through all top-level extension elements for a matching
        descendant.

        Args:
            path: XPath expression (e.g., "gpxtpx:TrackPointExtension/gpxtpx:hr").
            namespaces: Namespace prefix mapping (e.g., {"gpxtpx": "http://..."}).

        Returns:
            The first matching element, or None if not found.

        Example:
            >>> ns = {"gpxtpx": "http://www.garmin.com/xmlschemas/TrackPointExtension/v2"}
            >>> hr_elem = extensions.find("gpxtpx:TrackPointExtension/gpxtpx:hr", ns)

        """
        for elem in self.elements:
            # Check the element itself
            if namespaces:
                # Try to match against the element tag
                for prefix, uri in namespaces.items():
                    if path.startswith(f"{prefix}:"):
                        local_name = path.split(":")[1].split("/")[0]
                        if elem.tag == f"{{{uri}}}{local_name}":
                            # If there's more path, continue searching
                            remaining = "/".join(path.split("/")[1:])
                            if remaining:
                                result = elem.find(remaining, namespaces)
                                if result is not None:
                                    return result
                            else:
                                return elem
            # Search descendants
            result = elem.find(path, namespaces)  # type: ignore[arg-type]
            if result is not None:
                return result
        return None

    def findall(
        self,
        path: str,
        namespaces: dict[str, str] | None = None,
    ) -> list[ET.Element]:
        """Find all matching child elements using XPath.

        Args:
            path: XPath expression.
            namespaces: Namespace prefix mapping.

        Returns:
            List of all matching elements.

        """
        results: list[ET.Element] = []
        for elem in self.elements:
            results.extend(elem.findall(path, namespaces))  # type: ignore[arg-type]
        return results

    def get_text(
        self,
        tag: str,
        namespace: str | None = None,
        default: str | None = None,
    ) -> str | None:
        """Get text content of an extension element.

        Searches through all extension elements and their descendants for
        an element with the specified tag name.

        Args:
            tag: The element tag name (local name, without namespace prefix).
            namespace: The namespace URI. If None, searches all namespaces.
            default: Default value if element not found or has no text.

        Returns:
            The text content of the element, or the default value.

        Example:
            >>> # Get heart rate from Garmin extension
            >>> GARMIN_TPX = "http://www.garmin.com/xmlschemas/TrackPointExtension/v2"
            >>> hr = extensions.get_text("hr", namespace=GARMIN_TPX)
            >>> print(f"Heart rate: {hr} bpm")

            >>> # Search any namespace
            >>> hr = extensions.get_text("hr")

        """
        ns_tag = f"{{{namespace}}}{tag}" if namespace else None

        for elem in self.elements:
            # Check the element itself
            if ns_tag:
                if elem.tag == ns_tag:
                    return elem.text if elem.text else default
            elif elem.tag.endswith(f"}}{tag}") or elem.tag == tag:
                return elem.text if elem.text else default

            # Search descendants
            for child in elem.iter():
                if ns_tag:
                    if child.tag == ns_tag:
                        return child.text if child.text else default
                elif child.tag.endswith(f"}}{tag}") or child.tag == tag:
                    return child.text if child.text else default

        return default

    def get_int(
        self,
        tag: str,
        namespace: str | None = None,
        default: int | None = None,
    ) -> int | None:
        """Get integer value of an extension element.

        Args:
            tag: The element tag name.
            namespace: The namespace URI. If None, searches all namespaces.
            default: Default value if element not found or conversion fails.

        Returns:
            The integer value, or the default value.

        Example:
            >>> hr = extensions.get_int("hr", namespace=GARMIN_TPX)
            >>> print(f"Heart rate: {hr} bpm")

        """
        text = self.get_text(tag, namespace=namespace)
        if text is None:
            return default
        try:
            return int(text)
        except ValueError:
            return default

    def get_float(
        self,
        tag: str,
        namespace: str | None = None,
        default: float | None = None,
    ) -> float | None:
        """Get float value of an extension element.

        Args:
            tag: The element tag name.
            namespace: The namespace URI. If None, searches all namespaces.
            default: Default value if element not found or conversion fails.

        Returns:
            The float value, or the default value.

        Example:
            >>> temp = extensions.get_float("atemp", namespace=GARMIN_TPX)
            >>> print(f"Temperature: {temp}C")

        """
        text = self.get_text(tag, namespace=namespace)
        if text is None:
            return default
        try:
            return float(text)
        except ValueError:
            return default

    def set_text(
        self,
        tag: str,
        value: str,
        namespace: str,
        parent_tag: str | None = None,
    ) -> None:
        """Set text content of an extension element, creating it if needed.

        If the element exists, updates its text content. If it doesn't exist,
        creates a new element with the specified namespace.

        Args:
            tag: The element tag name (local name).
            value: The text content to set.
            namespace: The namespace URI (required for creation).
            parent_tag: Optional parent element tag. If specified and the parent
                exists, the new element is added as a child of the parent.
                Otherwise, a new top-level element is created.

        Example:
            >>> GARMIN_TPX = "http://www.garmin.com/xmlschemas/TrackPointExtension/v2"
            >>> extensions.set_text("hr", "145", namespace=GARMIN_TPX,
            ...                     parent_tag="TrackPointExtension")

        """
        ns_tag = f"{{{namespace}}}{tag}"

        # Try to find and update existing element
        for elem in self.elements:
            # Check the element itself
            if elem.tag == ns_tag:
                elem.text = value
                return

            # Search descendants
            for child in elem.iter():
                if child.tag == ns_tag:
                    child.text = value
                    return

        # Element doesn't exist, create it
        if parent_tag:
            parent_ns_tag = f"{{{namespace}}}{parent_tag}"
            # Look for existing parent
            for elem in self.elements:
                if elem.tag == parent_ns_tag:
                    new_elem = ET.SubElement(elem, ns_tag)
                    new_elem.text = value
                    return

            # Create parent and child
            parent = ET.Element(parent_ns_tag)
            child = ET.SubElement(parent, ns_tag)
            child.text = value
            self.elements.append(parent)
        else:
            # Create top-level element
            new_elem = ET.Element(ns_tag)
            new_elem.text = value
            self.elements.append(new_elem)

    def remove(self, tag: str, namespace: str | None = None) -> bool:
        """Remove an extension element.

        Removes the first matching element with the specified tag.

        Args:
            tag: The element tag name.
            namespace: The namespace URI. If None, matches any namespace.

        Returns:
            True if an element was removed, False otherwise.

        """
        ns_tag = f"{{{namespace}}}{tag}" if namespace else None

        # Check top-level elements
        for i, elem in enumerate(self.elements):
            if ns_tag:
                if elem.tag == ns_tag:
                    del self.elements[i]
                    return True
            elif elem.tag.endswith(f"}}{tag}") or elem.tag == tag:
                del self.elements[i]
                return True

        # Check descendants
        for elem in self.elements:
            for child in list(elem):
                if ns_tag:
                    if child.tag == ns_tag:
                        elem.remove(child)
                        return True
                elif child.tag.endswith(f"}}{tag}") or child.tag == tag:
                    elem.remove(child)
                    return True

        return False

    def clear(self) -> None:
        """Remove all extension elements."""
        self.elements.clear()

    def append(self, element: ET.Element) -> None:
        """Append an extension element.

        Args:
            element: The XML element to append.

        """
        self.elements.append(element)

    def extend(self, elements: list[ET.Element]) -> None:
        """Extend with multiple extension elements.

        Args:
            elements: List of XML elements to append.

        """
        self.elements.extend(elements)

    def get_namespaces(self) -> set[str]:
        """Get all namespaces used in extension elements.

        Returns:
            Set of namespace URIs.

        Example:
            >>> namespaces = extensions.get_namespaces()
            >>> for ns in namespaces:
            ...     print(f"Found extension namespace: {ns}")

        """
        namespaces: set[str] = set()
        for elem in self.elements:
            for e in elem.iter():
                if e.tag.startswith("{"):
                    ns = e.tag[1 : e.tag.index("}")]
                    namespaces.add(ns)
        return namespaces

    @classmethod
    def from_xml(cls, element: ET.Element) -> Extensions:
        """Parse extensions from an XML <extensions> element.

        Creates deep copies of all child elements to ensure the parsed
        extensions are independent of the source XML tree.

        Args:
            element: The <extensions> XML element.

        Returns:
            An Extensions instance containing copies of all child elements.

        """
        # Deep copy elements to ensure independence from source tree
        elements = [copy.deepcopy(child) for child in element]
        return cls(elements=elements)

    def to_xml(
        self,
        tag: str | None = None,
        nsmap: dict[str | None, str] | None = None,
    ) -> ET.Element:
        """Convert to an XML <extensions> element.

        Args:
            tag: The XML tag name. Defaults to "extensions".
            nsmap: Namespace mapping. Defaults to GPX 1.1 namespace.

        Returns:
            The XML element containing all extension elements.

        """
        from .base import GPX_NAMESPACE  # noqa: PLC0415

        if tag is None:
            tag = self._tag

        if nsmap is None:
            nsmap = {None: GPX_NAMESPACE}

        namespace = nsmap.get(None, GPX_NAMESPACE)
        ET.register_namespace("", namespace)
        element = ET.Element(f"{{{namespace}}}{tag}")

        # Append copies of extension elements to preserve originals
        for ext_elem in self.elements:
            element.append(copy.deepcopy(ext_elem))

        return element
