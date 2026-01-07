"""Tests for gpx.gpx module - main GPX class and I/O operations."""

from pathlib import Path
from typing import Any

from gpx import GPX, Metadata, Route, Track, Waypoint, from_string, read_gpx


class TestGPXParsing:
    """Tests for parsing GPX from strings and files."""

    def test_parse_minimal_gpx(self, minimal_gpx_string: str) -> None:
        """Test parsing minimal valid GPX string."""
        gpx = from_string(minimal_gpx_string)
        assert gpx.creator == "TestCreator"
        assert gpx.wpt == []
        assert gpx.rte == []
        assert gpx.trk == []

    def test_parse_gpx_with_waypoints(self, gpx_with_waypoint_string: str) -> None:
        """Test parsing GPX with waypoints."""
        gpx = from_string(gpx_with_waypoint_string)
        assert len(gpx.wpt) == 1
        assert gpx.wpt[0].name == "Berlin"

    def test_parse_gpx_with_tracks(self, gpx_with_track_string: str) -> None:
        """Test parsing GPX with tracks."""
        gpx = from_string(gpx_with_track_string)
        assert len(gpx.trk) == 1
        assert gpx.trk[0].name == "Morning Run"

    def test_parse_gpx_with_routes(self, gpx_with_route_string: str) -> None:
        """Test parsing GPX with routes."""
        gpx = from_string(gpx_with_route_string)
        assert len(gpx.rte) == 1
        assert gpx.rte[0].name == "City Tour"

    def test_parse_gpx_with_metadata(self, gpx_with_metadata_string: str) -> None:
        """Test parsing GPX with metadata."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        assert gpx.metadata.name == "Test GPX File"

    def test_parse_full_gpx(self, full_gpx_string: str) -> None:
        """Test parsing GPX with all element types."""
        gpx = from_string(full_gpx_string)
        assert gpx.metadata is not None
        assert len(gpx.wpt) == 2
        assert len(gpx.rte) == 1
        assert len(gpx.trk) == 1

    def test_parse_gpx_from_file(self, full_gpx_string: str, tmp_path: Path) -> None:
        """Test parsing GPX from a file."""
        temp_file = tmp_path / "test.gpx"
        temp_file.write_text(full_gpx_string)

        gpx = read_gpx(temp_file)
        assert gpx.metadata is not None
        assert len(gpx.wpt) == 2

    def test_parse_gpx_from_path_object(
        self, full_gpx_string: str, tmp_path: Path
    ) -> None:
        """Test parsing GPX from a Path object."""
        temp_file = tmp_path / "test.gpx"
        temp_file.write_text(full_gpx_string)

        gpx = read_gpx(temp_file)
        assert gpx.metadata is not None


class TestGPXBuilding:
    """Tests for building GPX XML."""

    def test_build_empty_gpx(self) -> None:
        """Test building empty GPX."""
        gpx = GPX()
        output = gpx.to_string()
        assert (
            '<?xml version="1.0"' not in output
        )  # to_string doesn't include declaration
        assert "<gpx" in output
        assert 'version="1.1"' in output

    def test_build_gpx_preserves_creator(self) -> None:
        """Test that creator attribute is preserved."""
        gpx = GPX(creator="TestApp")
        output = gpx.to_string()
        assert 'creator="TestApp"' in output

    def test_build_gpx_default_creator(self) -> None:
        """Test default creator is "https://github.com/sgraaf/gpx"."""
        gpx = GPX()
        assert gpx.creator == "https://github.com/sgraaf/gpx"
        output = gpx.to_string()
        assert 'creator="https://github.com/sgraaf/gpx"' in output

    def test_build_gpx_with_waypoints(self, sample_waypoint: Waypoint) -> None:
        """Test building GPX with waypoints."""
        gpx = GPX(wpt=[sample_waypoint])
        output = gpx.to_string()
        assert "<wpt" in output
        assert 'lat="52.5200"' in output

    def test_build_gpx_with_tracks(self, sample_track: Track) -> None:
        """Test building GPX with tracks."""
        gpx = GPX(trk=[sample_track])
        output = gpx.to_string()
        assert "<trk>" in output
        assert "<trkseg>" in output

    def test_build_gpx_with_routes(self, sample_route: Route) -> None:
        """Test building GPX with routes."""
        gpx = GPX(rte=[sample_route])
        output = gpx.to_string()
        assert "<rte>" in output
        assert "<rtept" in output


class TestGPXFileIO:
    """Tests for GPX file I/O operations."""

    def test_to_file_creates_file(self, full_gpx_string: str, tmp_path: Path) -> None:
        """Test that to_file creates a file."""
        gpx = from_string(full_gpx_string)

        temp_file = tmp_path / "output.gpx"
        gpx.write_gpx(temp_file)
        assert temp_file.exists()

    def test_to_file_with_path_object(
        self, full_gpx_string: str, tmp_path: Path
    ) -> None:
        """Test to_file with Path object."""
        gpx = from_string(full_gpx_string)

        temp_file = tmp_path / "output.gpx"
        gpx.write_gpx(temp_file)
        assert temp_file.exists()

    def test_roundtrip_file_io(self, full_gpx_string: str, tmp_path: Path) -> None:
        """Test complete roundtrip: string -> file -> string."""
        gpx1 = from_string(full_gpx_string)

        temp_file = tmp_path / "roundtrip.gpx"
        gpx1.write_gpx(temp_file)
        gpx2 = read_gpx(temp_file)

        assert gpx1.metadata is not None
        assert gpx2.metadata is not None
        assert gpx2.metadata.name == gpx1.metadata.name
        assert len(gpx2.wpt) == len(gpx1.wpt)
        assert len(gpx2.trk) == len(gpx1.trk)
        assert len(gpx2.rte) == len(gpx1.rte)

    def test_file_has_xml_declaration(
        self, minimal_gpx_string: str, tmp_path: Path
    ) -> None:
        """Test that saved file has XML declaration."""
        gpx = from_string(minimal_gpx_string)

        temp_file = tmp_path / "output.gpx"
        gpx.write_gpx(temp_file)
        content = temp_file.read_text()
        assert '<?xml version="1.0"' in content or "<?xml version='1.0'" in content


class TestGPXCreation:
    """Tests for creating GPX programmatically."""

    def test_create_empty_gpx(self) -> None:
        """Test creating empty GPX."""
        gpx = GPX()
        assert gpx.creator == "https://github.com/sgraaf/gpx"
        assert gpx.metadata is None
        assert gpx.wpt == []
        assert gpx.rte == []
        assert gpx.trk == []

    def test_create_gpx_with_all_elements(
        self,
        sample_waypoint: Waypoint,
        sample_route: Route,
        sample_track: Track,
        sample_metadata: Metadata,
    ) -> None:
        """Test creating GPX with all elements."""
        gpx = GPX(
            creator="TestApp",
            metadata=sample_metadata,
            wpt=[sample_waypoint],
            rte=[sample_route],
            trk=[sample_track],
        )

        output = gpx.to_string()
        assert 'creator="TestApp"' in output
        assert "<metadata>" in output
        assert "<wpt" in output
        assert "<rte>" in output
        assert "<trk>" in output

    def test_gpx_roundtrip_preserves_data(
        self,
        sample_waypoint: Waypoint,
        sample_route: Route,
        sample_track: Track,
        sample_metadata: Metadata,
    ) -> None:
        """Test that roundtrip preserves all data."""
        gpx1 = GPX(
            creator="TestApp",
            metadata=sample_metadata,
            wpt=[sample_waypoint],
            rte=[sample_route],
            trk=[sample_track],
        )

        output = gpx1.to_string()
        gpx2 = from_string(output)

        assert gpx2.creator == "TestApp"
        assert gpx2.metadata is not None
        assert gpx2.metadata.name == sample_metadata.name
        assert len(gpx2.wpt) == 1
        assert gpx2.wpt[0].name == sample_waypoint.name


class TestGPXEncodingHandling:
    """Tests for GPX encoding handling."""

    def test_parse_string_with_utf8_encoding(self) -> None:
        """Test parsing string with UTF-8 encoding declaration."""
        gpx_str = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
     version="1.1"
     creator="Test">
</gpx>"""
        gpx = from_string(gpx_str)
        assert gpx.creator == "Test"

    def test_parse_string_without_encoding(self) -> None:
        """Test parsing string without encoding declaration."""
        gpx_str = """<?xml version="1.0"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
     version="1.1"
     creator="Test">
</gpx>"""
        gpx = from_string(gpx_str)
        assert gpx.creator == "Test"

    def test_unicode_content_preserved(self) -> None:
        """Test that Unicode content is preserved."""
        gpx_str = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
     version="1.1"
     creator="Test">
  <wpt lat="52.5200" lon="13.4050">
    <name>Cafe</name>
  </wpt>
</gpx>"""
        gpx = from_string(gpx_str)
        assert gpx.wpt[0].name == "Cafe"


class TestGPXGeoInterface:
    """Tests for the `__geo_interface__` property."""

    def test_gpx_geo_interface(
        self, full_gpx_string: str, full_gpx_geo_interface: dict[str, Any]
    ) -> None:
        gpx = from_string(full_gpx_string)

        assert gpx.__geo_interface__ == full_gpx_geo_interface
