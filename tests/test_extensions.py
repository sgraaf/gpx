"""Tests for GPX extensions support."""

from __future__ import annotations

import copy
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

import pytest

from gpx import (
    GPX,
    Extensions,
    Latitude,
    Longitude,
    Metadata,
    Route,
    Track,
    TrackSegment,
    Waypoint,
    read_gpx,
)

if TYPE_CHECKING:
    from pathlib import Path

# Common extension namespaces for testing
GARMIN_TPX_NS = "http://www.garmin.com/xmlschemas/TrackPointExtension/v2"
GARMIN_GPX_EXT_NS = "http://www.garmin.com/xmlschemas/GpxExtensions/v3"
CUSTOM_NS = "http://example.com/custom/v1"


class TestExtensionsBasic:
    """Test basic Extensions functionality."""

    def test_empty_extensions(self) -> None:
        """Test creating empty Extensions."""
        ext = Extensions()
        assert len(ext) == 0
        assert not ext
        assert list(ext) == []

    def test_extensions_with_elements(self) -> None:
        """Test creating Extensions with elements."""
        elem1 = ET.Element(f"{{{CUSTOM_NS}}}custom1")
        elem1.text = "value1"
        elem2 = ET.Element(f"{{{CUSTOM_NS}}}custom2")
        elem2.text = "value2"

        ext = Extensions(elements=[elem1, elem2])
        assert len(ext) == 2
        assert ext
        assert list(ext) == [elem1, elem2]

    def test_extensions_bool(self) -> None:
        """Test Extensions truthiness."""
        assert not Extensions()
        assert Extensions(elements=[ET.Element("test")])

    def test_extensions_iter(self) -> None:
        """Test iterating over Extensions."""
        elem1 = ET.Element("elem1")
        elem2 = ET.Element("elem2")
        ext = Extensions(elements=[elem1, elem2])

        result = list(ext)
        assert result == [elem1, elem2]


class TestExtensionsAccessors:
    """Test Extensions accessor methods."""

    @pytest.fixture
    def garmin_tpx_extensions(self) -> Extensions:
        """Create extensions with Garmin TrackPointExtension data."""
        ET.register_namespace("gpxtpx", GARMIN_TPX_NS)
        tpx = ET.Element(f"{{{GARMIN_TPX_NS}}}TrackPointExtension")
        hr = ET.SubElement(tpx, f"{{{GARMIN_TPX_NS}}}hr")
        hr.text = "142"
        cad = ET.SubElement(tpx, f"{{{GARMIN_TPX_NS}}}cad")
        cad.text = "85"
        atemp = ET.SubElement(tpx, f"{{{GARMIN_TPX_NS}}}atemp")
        atemp.text = "22.5"
        return Extensions(elements=[tpx])

    def test_get_text_with_namespace(self, garmin_tpx_extensions: Extensions) -> None:
        """Test getting text with specific namespace."""
        hr = garmin_tpx_extensions.get_text("hr", namespace=GARMIN_TPX_NS)
        assert hr == "142"

        cad = garmin_tpx_extensions.get_text("cad", namespace=GARMIN_TPX_NS)
        assert cad == "85"

    def test_get_text_without_namespace(
        self, garmin_tpx_extensions: Extensions
    ) -> None:
        """Test getting text without namespace (searches all)."""
        hr = garmin_tpx_extensions.get_text("hr")
        assert hr == "142"

    def test_get_text_not_found(self, garmin_tpx_extensions: Extensions) -> None:
        """Test getting text for non-existent element."""
        result = garmin_tpx_extensions.get_text("nonexistent")
        assert result is None

        result = garmin_tpx_extensions.get_text("nonexistent", default="default")
        assert result == "default"

    def test_get_int(self, garmin_tpx_extensions: Extensions) -> None:
        """Test getting integer value."""
        hr = garmin_tpx_extensions.get_int("hr", namespace=GARMIN_TPX_NS)
        assert hr == 142
        assert isinstance(hr, int)

    def test_get_int_invalid(self, garmin_tpx_extensions: Extensions) -> None:
        """Test getting integer for non-numeric value."""
        result = garmin_tpx_extensions.get_int("atemp", namespace=GARMIN_TPX_NS)
        assert result is None  # "22.5" is not a valid int

    def test_get_int_default(self, garmin_tpx_extensions: Extensions) -> None:
        """Test get_int with default value."""
        result = garmin_tpx_extensions.get_int("nonexistent", default=0)
        assert result == 0

    def test_get_float(self, garmin_tpx_extensions: Extensions) -> None:
        """Test getting float value."""
        temp = garmin_tpx_extensions.get_float("atemp", namespace=GARMIN_TPX_NS)
        assert temp == 22.5
        assert isinstance(temp, float)

    def test_get_float_from_int(self, garmin_tpx_extensions: Extensions) -> None:
        """Test getting float from integer text."""
        hr = garmin_tpx_extensions.get_float("hr", namespace=GARMIN_TPX_NS)
        assert hr == 142.0

    def test_get_float_default(self, garmin_tpx_extensions: Extensions) -> None:
        """Test get_float with default value."""
        result = garmin_tpx_extensions.get_float("nonexistent", default=0.0)
        assert result == 0.0

    def test_contains_with_tag(self, garmin_tpx_extensions: Extensions) -> None:
        """Test __contains__ with tag name."""
        assert "hr" in garmin_tpx_extensions
        assert "cad" in garmin_tpx_extensions
        assert "nonexistent" not in garmin_tpx_extensions

    def test_contains_with_namespace_tuple(
        self, garmin_tpx_extensions: Extensions
    ) -> None:
        """Test __contains__ with (namespace, tag) tuple."""
        assert (GARMIN_TPX_NS, "hr") in garmin_tpx_extensions
        assert (CUSTOM_NS, "hr") not in garmin_tpx_extensions


class TestExtensionsMutation:
    """Test Extensions mutation methods."""

    def test_set_text_new_element(self) -> None:
        """Test setting text creates new element."""
        ext = Extensions()
        ext.set_text("custom", "value", namespace=CUSTOM_NS)

        assert len(ext) == 1
        assert ext.get_text("custom", namespace=CUSTOM_NS) == "value"

    def test_set_text_update_existing(self) -> None:
        """Test setting text updates existing element."""
        elem = ET.Element(f"{{{CUSTOM_NS}}}custom")
        elem.text = "old_value"
        ext = Extensions(elements=[elem])

        ext.set_text("custom", "new_value", namespace=CUSTOM_NS)
        assert ext.get_text("custom", namespace=CUSTOM_NS) == "new_value"
        assert len(ext) == 1  # No new element created

    def test_set_text_with_parent(self) -> None:
        """Test setting text with parent element."""
        ext = Extensions()
        ext.set_text(
            "hr", "142", namespace=GARMIN_TPX_NS, parent_tag="TrackPointExtension"
        )

        assert len(ext) == 1
        assert ext.get_text("hr", namespace=GARMIN_TPX_NS) == "142"

    def test_remove_element(self) -> None:
        """Test removing an element."""
        elem = ET.Element(f"{{{CUSTOM_NS}}}custom")
        ext = Extensions(elements=[elem])

        result = ext.remove("custom", namespace=CUSTOM_NS)
        assert result is True
        assert len(ext) == 0

    def test_remove_nonexistent(self) -> None:
        """Test removing non-existent element."""
        ext = Extensions()
        result = ext.remove("nonexistent")
        assert result is False

    def test_clear(self) -> None:
        """Test clearing all elements."""
        elem1 = ET.Element("elem1")
        elem2 = ET.Element("elem2")
        ext = Extensions(elements=[elem1, elem2])

        ext.clear()
        assert len(ext) == 0

    def test_append(self) -> None:
        """Test appending an element."""
        ext = Extensions()
        elem = ET.Element(f"{{{CUSTOM_NS}}}custom")
        ext.append(elem)

        assert len(ext) == 1
        assert ext.elements[0] is elem

    def test_extend(self) -> None:
        """Test extending with multiple elements."""
        ext = Extensions()
        elems = [
            ET.Element(f"{{{CUSTOM_NS}}}elem1"),
            ET.Element(f"{{{CUSTOM_NS}}}elem2"),
        ]
        ext.extend(elems)

        assert len(ext) == 2


class TestExtensionsXPath:
    """Test Extensions XPath-like methods."""

    @pytest.fixture
    def nested_extensions(self) -> Extensions:
        """Create extensions with nested structure."""
        ET.register_namespace("gpxtpx", GARMIN_TPX_NS)
        tpx = ET.Element(f"{{{GARMIN_TPX_NS}}}TrackPointExtension")
        hr = ET.SubElement(tpx, f"{{{GARMIN_TPX_NS}}}hr")
        hr.text = "142"
        return Extensions(elements=[tpx])

    def test_find_with_namespace(self, nested_extensions: Extensions) -> None:
        """Test finding element with namespace mapping."""
        ns = {"gpxtpx": GARMIN_TPX_NS}
        hr = nested_extensions.find("gpxtpx:hr", namespaces=ns)
        assert hr is not None
        assert hr.text == "142"

    def test_findall(self, nested_extensions: Extensions) -> None:
        """Test finding all matching elements."""
        ns = {"gpxtpx": GARMIN_TPX_NS}
        results = nested_extensions.findall("gpxtpx:hr", namespaces=ns)
        assert len(results) == 1
        assert results[0].text == "142"


class TestExtensionsNamespaces:
    """Test Extensions namespace handling."""

    def test_get_namespaces(self) -> None:
        """Test getting all namespaces used in extensions."""
        elem1 = ET.Element(f"{{{GARMIN_TPX_NS}}}tpx")
        elem2 = ET.Element(f"{{{CUSTOM_NS}}}custom")
        ext = Extensions(elements=[elem1, elem2])

        namespaces = ext.get_namespaces()
        assert GARMIN_TPX_NS in namespaces
        assert CUSTOM_NS in namespaces
        assert len(namespaces) == 2

    def test_get_namespaces_nested(self) -> None:
        """Test getting namespaces from nested elements."""
        parent = ET.Element(f"{{{GARMIN_TPX_NS}}}parent")
        ET.SubElement(parent, f"{{{CUSTOM_NS}}}child")
        ext = Extensions(elements=[parent])

        namespaces = ext.get_namespaces()
        assert GARMIN_TPX_NS in namespaces
        assert CUSTOM_NS in namespaces


class TestExtensionsCopy:
    """Test Extensions copying."""

    def test_copy(self) -> None:
        """Test deep copying Extensions."""
        elem = ET.Element(f"{{{CUSTOM_NS}}}custom")
        elem.text = "value"
        ext = Extensions(elements=[elem])

        copied = ext.copy()

        # Modify original
        elem.text = "modified"

        # Copy should be independent
        assert copied.get_text("custom", namespace=CUSTOM_NS) == "value"
        assert ext.get_text("custom", namespace=CUSTOM_NS) == "modified"


class TestExtensionsXMLSerialization:
    """Test Extensions XML parsing and serialization."""

    def test_from_xml(self) -> None:
        """Test parsing Extensions from XML element."""
        xml_str = f"""
        <extensions xmlns="http://www.topografix.com/GPX/1/1">
            <TrackPointExtension xmlns="{GARMIN_TPX_NS}">
                <hr>142</hr>
            </TrackPointExtension>
        </extensions>
        """
        element = ET.fromstring(xml_str)
        ext = Extensions.from_xml(element)

        assert len(ext) == 1
        assert ext.get_text("hr", namespace=GARMIN_TPX_NS) == "142"

    def test_to_xml(self) -> None:
        """Test serializing Extensions to XML."""
        ET.register_namespace("gpxtpx", GARMIN_TPX_NS)
        tpx = ET.Element(f"{{{GARMIN_TPX_NS}}}TrackPointExtension")
        hr = ET.SubElement(tpx, f"{{{GARMIN_TPX_NS}}}hr")
        hr.text = "142"
        ext = Extensions(elements=[tpx])

        element = ext.to_xml()

        assert element.tag.endswith("}extensions")
        assert len(element) == 1

    def test_round_trip_preserves_content(self) -> None:
        """Test that round-trip preserves extension content."""
        # Create original extensions
        ET.register_namespace("gpxtpx", GARMIN_TPX_NS)
        tpx = ET.Element(f"{{{GARMIN_TPX_NS}}}TrackPointExtension")
        hr = ET.SubElement(tpx, f"{{{GARMIN_TPX_NS}}}hr")
        hr.text = "142"
        cad = ET.SubElement(tpx, f"{{{GARMIN_TPX_NS}}}cad")
        cad.text = "85"

        original_ext = Extensions(elements=[tpx])

        # Serialize to XML
        xml_element = original_ext.to_xml()

        # Parse back
        parsed_ext = Extensions.from_xml(xml_element)

        # Verify content preserved
        assert parsed_ext.get_text("hr", namespace=GARMIN_TPX_NS) == "142"
        assert parsed_ext.get_text("cad", namespace=GARMIN_TPX_NS) == "85"


class TestExtensionsInModels:
    """Test Extensions integration with GPX models."""

    def test_waypoint_with_extensions(self) -> None:
        """Test creating Waypoint with extensions."""
        ET.register_namespace("gpxtpx", GARMIN_TPX_NS)
        tpx = ET.Element(f"{{{GARMIN_TPX_NS}}}TrackPointExtension")
        hr = ET.SubElement(tpx, f"{{{GARMIN_TPX_NS}}}hr")
        hr.text = "142"

        wpt = Waypoint(
            lat=Latitude("52.0"),
            lon=Longitude("4.0"),
            extensions=Extensions(elements=[tpx]),
        )

        assert wpt.extensions is not None
        assert wpt.extensions.get_text("hr", namespace=GARMIN_TPX_NS) == "142"

    def test_track_segment_with_extensions(self) -> None:
        """Test creating TrackSegment with extensions."""
        ext_elem = ET.Element(f"{{{CUSTOM_NS}}}custom")
        ext_elem.text = "segment_data"

        segment = TrackSegment(
            trkpt=[],
            extensions=Extensions(elements=[ext_elem]),
        )

        assert segment.extensions is not None
        assert (
            segment.extensions.get_text("custom", namespace=CUSTOM_NS) == "segment_data"
        )

    def test_track_with_extensions(self) -> None:
        """Test creating Track with extensions."""
        ext_elem = ET.Element(f"{{{CUSTOM_NS}}}custom")
        ext_elem.text = "track_data"

        track = Track(
            name="Test Track",
            extensions=Extensions(elements=[ext_elem]),
        )

        assert track.extensions is not None
        assert track.extensions.get_text("custom", namespace=CUSTOM_NS) == "track_data"

    def test_route_with_extensions(self) -> None:
        """Test creating Route with extensions."""
        ext_elem = ET.Element(f"{{{CUSTOM_NS}}}custom")
        ext_elem.text = "route_data"

        route = Route(
            name="Test Route",
            extensions=Extensions(elements=[ext_elem]),
        )

        assert route.extensions is not None
        assert route.extensions.get_text("custom", namespace=CUSTOM_NS) == "route_data"

    def test_metadata_with_extensions(self) -> None:
        """Test creating Metadata with extensions."""
        ext_elem = ET.Element(f"{{{CUSTOM_NS}}}custom")
        ext_elem.text = "metadata_data"

        metadata = Metadata(
            name="Test",
            extensions=Extensions(elements=[ext_elem]),
        )

        assert metadata.extensions is not None
        assert (
            metadata.extensions.get_text("custom", namespace=CUSTOM_NS)
            == "metadata_data"
        )

    def test_gpx_with_extensions(self) -> None:
        """Test creating GPX with extensions."""
        ext_elem = ET.Element(f"{{{CUSTOM_NS}}}custom")
        ext_elem.text = "gpx_data"

        gpx = GPX(
            creator="test",
            extensions=Extensions(elements=[ext_elem]),
        )

        assert gpx.extensions is not None
        assert gpx.extensions.get_text("custom", namespace=CUSTOM_NS) == "gpx_data"


class TestExtensionsGPXRoundTrip:
    """Test full GPX round-trip with extensions."""

    def test_gpx_round_trip_with_extensions(self, tmp_path: Path) -> None:
        """Test full GPX read/write round-trip preserves extensions."""
        # Create GPX with extensions at multiple levels
        ET.register_namespace("gpxtpx", GARMIN_TPX_NS)
        ET.register_namespace("custom", CUSTOM_NS)

        # Track point extension
        tpx = ET.Element(f"{{{GARMIN_TPX_NS}}}TrackPointExtension")
        hr = ET.SubElement(tpx, f"{{{GARMIN_TPX_NS}}}hr")
        hr.text = "145"
        cad = ET.SubElement(tpx, f"{{{GARMIN_TPX_NS}}}cad")
        cad.text = "90"

        # GPX level extension
        gpx_ext_elem = ET.Element(f"{{{CUSTOM_NS}}}metadata")
        gpx_ext_elem.text = "custom_gpx_data"

        # Create GPX structure
        gpx = GPX(
            creator="test",
            extensions=Extensions(elements=[gpx_ext_elem]),
            trk=[
                Track(
                    name="Test Track",
                    trkseg=[
                        TrackSegment(
                            trkpt=[
                                Waypoint(
                                    lat=Latitude("52.0"),
                                    lon=Longitude("4.0"),
                                    extensions=Extensions(
                                        elements=[copy.deepcopy(tpx)]
                                    ),
                                ),
                                Waypoint(
                                    lat=Latitude("52.1"),
                                    lon=Longitude("4.1"),
                                    extensions=Extensions(
                                        elements=[copy.deepcopy(tpx)]
                                    ),
                                ),
                            ]
                        )
                    ],
                )
            ],
        )

        # Write to file
        gpx_file = tmp_path / "test_extensions.gpx"
        gpx.write_gpx(gpx_file)

        # Read back
        gpx_read = read_gpx(gpx_file)

        # Verify GPX level extensions
        assert gpx_read.extensions is not None
        assert (
            gpx_read.extensions.get_text("metadata", namespace=CUSTOM_NS)
            == "custom_gpx_data"
        )

        # Verify track point extensions
        trkpt = gpx_read.trk[0].trkseg[0].trkpt[0]
        assert trkpt.extensions is not None
        assert trkpt.extensions.get_text("hr", namespace=GARMIN_TPX_NS) == "145"
        assert trkpt.extensions.get_text("cad", namespace=GARMIN_TPX_NS) == "90"

    def test_parse_gpx_with_garmin_extensions(self, tmp_path: Path) -> None:
        """Test parsing a GPX file with Garmin-style extensions."""
        gpx_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test"
     xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:gpxtpx="{GARMIN_TPX_NS}">
  <trk>
    <name>Morning Run</name>
    <trkseg>
      <trkpt lat="52.0" lon="4.0">
        <ele>10</ele>
        <extensions>
          <gpxtpx:TrackPointExtension>
            <gpxtpx:hr>142</gpxtpx:hr>
            <gpxtpx:cad>85</gpxtpx:cad>
            <gpxtpx:atemp>22.5</gpxtpx:atemp>
          </gpxtpx:TrackPointExtension>
        </extensions>
      </trkpt>
      <trkpt lat="52.1" lon="4.1">
        <ele>12</ele>
        <extensions>
          <gpxtpx:TrackPointExtension>
            <gpxtpx:hr>145</gpxtpx:hr>
            <gpxtpx:cad>87</gpxtpx:cad>
          </gpxtpx:TrackPointExtension>
        </extensions>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
"""
        gpx_file = tmp_path / "garmin_extensions.gpx"
        gpx_file.write_text(gpx_content)

        gpx = read_gpx(gpx_file)

        # Verify first track point
        trkpt1 = gpx.trk[0].trkseg[0].trkpt[0]
        assert trkpt1.extensions is not None
        assert trkpt1.extensions.get_int("hr", namespace=GARMIN_TPX_NS) == 142
        assert trkpt1.extensions.get_int("cad", namespace=GARMIN_TPX_NS) == 85
        assert trkpt1.extensions.get_float("atemp", namespace=GARMIN_TPX_NS) == 22.5

        # Verify second track point
        trkpt2 = gpx.trk[0].trkseg[0].trkpt[1]
        assert trkpt2.extensions is not None
        assert trkpt2.extensions.get_int("hr", namespace=GARMIN_TPX_NS) == 145
        assert trkpt2.extensions.get_int("cad", namespace=GARMIN_TPX_NS) == 87

    def test_parse_gpx_with_multiple_extension_namespaces(self, tmp_path: Path) -> None:
        """Test parsing GPX with extensions from multiple namespaces."""
        gpx_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test"
     xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:gpxtpx="{GARMIN_TPX_NS}"
     xmlns:custom="{CUSTOM_NS}">
  <extensions>
    <custom:source>MyApp</custom:source>
    <custom:version>1.0</custom:version>
  </extensions>
  <wpt lat="52.0" lon="4.0">
    <name>Test Point</name>
    <extensions>
      <gpxtpx:TrackPointExtension>
        <gpxtpx:hr>120</gpxtpx:hr>
      </gpxtpx:TrackPointExtension>
      <custom:rating>5</custom:rating>
    </extensions>
  </wpt>
</gpx>
"""
        gpx_file = tmp_path / "multi_ns.gpx"
        gpx_file.write_text(gpx_content)

        gpx = read_gpx(gpx_file)

        # Verify GPX-level extensions
        assert gpx.extensions is not None
        assert gpx.extensions.get_text("source", namespace=CUSTOM_NS) == "MyApp"
        assert gpx.extensions.get_text("version", namespace=CUSTOM_NS) == "1.0"

        # Verify waypoint extensions from both namespaces
        wpt = gpx.wpt[0]
        assert wpt.extensions is not None
        assert wpt.extensions.get_int("hr", namespace=GARMIN_TPX_NS) == 120
        assert wpt.extensions.get_text("rating", namespace=CUSTOM_NS) == "5"

        # Verify namespaces are detected
        namespaces = wpt.extensions.get_namespaces()
        assert GARMIN_TPX_NS in namespaces
        assert CUSTOM_NS in namespaces


class TestExtensionsNamespacePreservation:
    """Test that namespace prefixes are preserved during round-trip."""

    def test_namespace_prefix_preservation(self, tmp_path: Path) -> None:
        """Test that namespace prefixes are preserved during read/write."""
        # Create GPX with specific namespace prefix
        gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v2" version="1.1" creator="Test">
  <trk>
    <name>Single point track</name>
    <trkseg>
        <trkpt lat="42.0405540" lon="-87.6936190">
            <ele>126.2</ele>
            <time>2026-01-02T19:42:54Z</time>
            <extensions>
            <gpxtpx:TrackPointExtension>
            <gpxtpx:atemp>17</gpxtpx:atemp>
            <gpxtpx:hr>137</gpxtpx:hr>
            <gpxtpx:cad>81</gpxtpx:cad>
            </gpxtpx:TrackPointExtension>
            </extensions>
        </trkpt>
    </trkseg>
  </trk>
</gpx>
"""
        # Write input file
        input_file = tmp_path / "example_in.gpx"
        input_file.write_text(gpx_content)

        # Read and write back
        gpx = read_gpx(input_file)
        output_file = tmp_path / "example_out.gpx"
        gpx.write_gpx(output_file)

        # Read output file
        output_content = output_file.read_text()

        # Verify namespace prefix is preserved as "gpxtpx" not "ns0", "ns1", etc.
        assert "xmlns:gpxtpx=" in output_content
        assert "gpxtpx:TrackPointExtension" in output_content
        assert "gpxtpx:atemp" in output_content
        assert "gpxtpx:hr" in output_content
        assert "gpxtpx:cad" in output_content

        # Verify no generic namespace prefixes like ns0, ns1, ns2
        assert "xmlns:ns0=" not in output_content
        assert "xmlns:ns1=" not in output_content
        assert "xmlns:ns2=" not in output_content
        assert "ns2:" not in output_content

    def test_namespace_prefix_preservation_multiple_namespaces(
        self, tmp_path: Path
    ) -> None:
        """Test preserving multiple custom namespace prefixes."""
        gpx_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:gpxtpx="{GARMIN_TPX_NS}"
     xmlns:garmin="{GARMIN_GPX_EXT_NS}"
     xmlns:custom="{CUSTOM_NS}"
     version="1.1" creator="Test">
  <extensions>
    <custom:data>test</custom:data>
  </extensions>
  <wpt lat="52.0" lon="4.0">
    <extensions>
      <garmin:WaypointExtension>
        <garmin:DisplayMode>SymbolAndName</garmin:DisplayMode>
      </garmin:WaypointExtension>
    </extensions>
  </wpt>
  <trk>
    <trkseg>
      <trkpt lat="52.1" lon="4.1">
        <extensions>
          <gpxtpx:TrackPointExtension>
            <gpxtpx:hr>140</gpxtpx:hr>
          </gpxtpx:TrackPointExtension>
        </extensions>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
"""
        input_file = tmp_path / "multi_ns_in.gpx"
        input_file.write_text(gpx_content)

        # Read and write back
        gpx = read_gpx(input_file)
        output_file = tmp_path / "multi_ns_out.gpx"
        gpx.write_gpx(output_file)

        # Read output file
        output_content = output_file.read_text()

        # Verify all namespace prefixes are preserved
        assert "xmlns:gpxtpx=" in output_content
        assert "xmlns:garmin=" in output_content
        assert "xmlns:custom=" in output_content

        # Verify prefixes are used in elements
        assert "gpxtpx:TrackPointExtension" in output_content
        assert "garmin:WaypointExtension" in output_content
        assert "custom:data" in output_content


class TestExtensionsWithoutExtensions:
    """Test that GPX files without extensions still work."""

    def test_gpx_without_extensions(self, tmp_path: Path) -> None:
        """Test parsing GPX without any extensions."""
        gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="52.0" lon="4.0">
    <name>Test Point</name>
  </wpt>
</gpx>
"""
        gpx_file = tmp_path / "no_extensions.gpx"
        gpx_file.write_text(gpx_content)

        gpx = read_gpx(gpx_file)

        assert gpx.extensions is None
        assert gpx.wpt[0].extensions is None

    def test_create_gpx_without_extensions(self) -> None:
        """Test creating GPX without extensions."""
        gpx = GPX(
            creator="test",
            wpt=[
                Waypoint(lat=Latitude("52.0"), lon=Longitude("4.0")),
            ],
        )

        assert gpx.extensions is None
        assert gpx.wpt[0].extensions is None

        # Should serialize without extensions element
        xml_str = gpx.to_string()
        assert "<extensions>" not in xml_str
