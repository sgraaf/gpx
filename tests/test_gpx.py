"""Tests for gpx.gpx module - main GPX class and I/O operations."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from gpx import GPX, Person
from gpx.errors import InvalidGPXError
from gpx.types import Latitude


class TestGPXParsing:
    """Tests for parsing GPX from strings and files."""

    def test_parse_minimal_gpx(self, minimal_gpx_string):
        """Test parsing minimal valid GPX string."""
        gpx = GPX.from_string(minimal_gpx_string)
        assert gpx.creator == "TestCreator"
        assert gpx.waypoints == []
        assert gpx.routes == []
        assert gpx.tracks == []

    def test_parse_gpx_with_waypoints(self, gpx_with_waypoint_string):
        """Test parsing GPX with waypoints."""
        gpx = GPX.from_string(gpx_with_waypoint_string)
        assert len(gpx.waypoints) == 1
        assert gpx.waypoints[0].name == "Berlin"

    def test_parse_gpx_with_tracks(self, gpx_with_track_string):
        """Test parsing GPX with tracks."""
        gpx = GPX.from_string(gpx_with_track_string)
        assert len(gpx.tracks) == 1
        assert gpx.tracks[0].name == "Morning Run"

    def test_parse_gpx_with_routes(self, gpx_with_route_string):
        """Test parsing GPX with routes."""
        gpx = GPX.from_string(gpx_with_route_string)
        assert len(gpx.routes) == 1
        assert gpx.routes[0].name == "City Tour"

    def test_parse_gpx_with_metadata(self, gpx_with_metadata_string):
        """Test parsing GPX with metadata."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        assert gpx.metadata.name == "Test GPX File"

    def test_parse_full_gpx(self, full_gpx_string):
        """Test parsing GPX with all element types."""
        gpx = GPX.from_string(full_gpx_string)
        assert gpx.metadata is not None
        assert len(gpx.waypoints) == 2
        assert len(gpx.routes) == 1
        assert len(gpx.tracks) == 1

    def test_parse_gpx_from_file(self, full_gpx_string):
        """Test parsing GPX from a file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False) as f:
            f.write(full_gpx_string)
            f.flush()

            gpx = GPX.from_file(f.name)
            assert gpx.metadata is not None
            assert len(gpx.waypoints) == 2

            # Cleanup
            Path(f.name).unlink()

    def test_parse_gpx_from_path_object(self, full_gpx_string):
        """Test parsing GPX from a Path object."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False) as f:
            f.write(full_gpx_string)
            f.flush()

            gpx = GPX.from_file(Path(f.name))
            assert gpx.metadata is not None

            # Cleanup
            Path(f.name).unlink()


class TestGPXValidation:
    """Tests for GPX validation."""

    def test_parse_valid_gpx_with_validation(self, minimal_gpx_string):
        """Test parsing valid GPX with validation enabled."""
        gpx = GPX.from_string(minimal_gpx_string, validate=True)
        assert gpx is not None

    def test_parse_invalid_gpx_with_validation(self, invalid_gpx_string):
        """Test that invalid GPX raises error when validation is enabled."""
        with pytest.raises(InvalidGPXError, match="The GPX data is invalid"):
            GPX.from_string(invalid_gpx_string, validate=True)

    def test_parse_invalid_gpx_without_validation(self, invalid_gpx_string):
        """Test that invalid GPX can be parsed when validation is disabled."""
        # This may raise a different error due to missing lat/lon attributes
        with pytest.raises(KeyError):
            GPX.from_string(invalid_gpx_string, validate=False)


class TestGPXBuilding:
    """Tests for building GPX XML."""

    def test_build_empty_gpx(self):
        """Test building empty GPX."""
        gpx = GPX()
        output = gpx.to_string()
        assert (
            '<?xml version="1.0"' not in output
        )  # to_string doesn't include declaration
        assert "<gpx" in output
        assert 'version="1.1"' in output

    def test_build_gpx_preserves_creator(self):
        """Test that creator attribute is preserved."""
        gpx = GPX()
        gpx.creator = "TestApp"
        output = gpx.to_string()
        assert 'creator="TestApp"' in output

    def test_build_gpx_default_creator(self):
        """Test default creator is PyGPX."""
        gpx = GPX()
        assert gpx.creator == "PyGPX"
        output = gpx.to_string()
        assert 'creator="PyGPX"' in output

    def test_build_gpx_with_waypoints(self, sample_waypoint):
        """Test building GPX with waypoints."""
        gpx = GPX()
        gpx.waypoints = [sample_waypoint]
        output = gpx.to_string()
        assert "<wpt" in output
        assert 'lat="52.5200"' in output

    def test_build_gpx_with_tracks(self, sample_track):
        """Test building GPX with tracks."""
        gpx = GPX()
        gpx.tracks = [sample_track]
        output = gpx.to_string()
        assert "<trk>" in output
        assert "<trkseg>" in output

    def test_build_gpx_with_routes(self, sample_route):
        """Test building GPX with routes."""
        gpx = GPX()
        gpx.routes = [sample_route]
        output = gpx.to_string()
        assert "<rte>" in output
        assert "<rtept" in output


class TestGPXFileIO:
    """Tests for GPX file I/O operations."""

    def test_to_file_creates_file(self, full_gpx_string):
        """Test that to_file creates a file."""
        gpx = GPX.from_string(full_gpx_string)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False) as f:
            gpx.to_file(f.name)
            assert Path(f.name).exists()
            Path(f.name).unlink()

    def test_to_file_with_path_object(self, full_gpx_string):
        """Test to_file with Path object."""
        gpx = GPX.from_string(full_gpx_string)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False) as f:
            gpx.to_file(Path(f.name))
            assert Path(f.name).exists()
            Path(f.name).unlink()

    def test_roundtrip_file_io(self, full_gpx_string):
        """Test complete roundtrip: string -> file -> string."""
        gpx1 = GPX.from_string(full_gpx_string)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False) as f:
            gpx1.to_file(f.name)
            gpx2 = GPX.from_file(f.name)

            assert gpx2.metadata.name == gpx1.metadata.name
            assert len(gpx2.waypoints) == len(gpx1.waypoints)
            assert len(gpx2.tracks) == len(gpx1.tracks)
            assert len(gpx2.routes) == len(gpx1.routes)

            Path(f.name).unlink()

    def test_file_has_xml_declaration(self, minimal_gpx_string):
        """Test that saved file has XML declaration."""
        gpx = GPX.from_string(minimal_gpx_string)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False) as f:
            gpx.to_file(f.name)
            content = Path(f.name).read_text()
            assert '<?xml version="1.0"' in content or "<?xml version='1.0'" in content
            Path(f.name).unlink()


class TestGPXMetadataProxies:
    """Tests for GPX metadata property proxies."""

    def test_name_proxy_get(self, gpx_with_metadata_string):
        """Test getting name via proxy."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        assert gpx.name == "Test GPX File"

    def test_name_proxy_get_no_metadata(self, minimal_gpx_string):
        """Test getting name when no metadata exists."""
        gpx = GPX.from_string(minimal_gpx_string)
        assert gpx.name is None

    def test_name_proxy_set_creates_metadata(self, minimal_gpx_string):
        """Test setting name creates metadata if needed."""
        gpx = GPX.from_string(minimal_gpx_string)
        gpx.name = "New Name"
        assert gpx.metadata is not None
        assert gpx.name == "New Name"

    def test_desc_proxy(self, gpx_with_metadata_string):
        """Test description proxy."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        assert gpx.desc == "A test GPX file for unit testing"

    def test_desc_proxy_set(self, minimal_gpx_string):
        """Test setting description via proxy."""
        gpx = GPX.from_string(minimal_gpx_string)
        gpx.desc = "New Description"
        assert gpx.desc == "New Description"

    def test_author_proxy(self, gpx_with_metadata_string):
        """Test author proxy."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        assert gpx.author is not None
        assert gpx.author.name == "Test Author"

    def test_author_proxy_set(self, minimal_gpx_string):
        """Test setting author via proxy."""
        gpx = GPX.from_string(minimal_gpx_string)
        person = Person()
        person.name = "New Author"
        gpx.author = person
        assert gpx.author.name == "New Author"

    def test_time_proxy(self, gpx_with_metadata_string):
        """Test time proxy."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        expected = datetime(2023, 6, 15, 10, 0, 0, tzinfo=timezone.utc)
        assert gpx.time == expected

    def test_time_proxy_set(self, minimal_gpx_string):
        """Test setting time via proxy."""
        gpx = GPX.from_string(minimal_gpx_string)
        new_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        gpx.time = new_time
        assert gpx.time == new_time

    def test_keywords_proxy(self, gpx_with_metadata_string):
        """Test keywords proxy."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        assert gpx.keywords == "test, gpx, example"

    def test_bounds_proxy(self, gpx_with_metadata_string):
        """Test bounds proxy."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        assert gpx.bounds is not None
        assert gpx.bounds.minlat == Latitude("52.5")

    def test_links_proxy(self, gpx_with_metadata_string):
        """Test links proxy."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        assert gpx.links is not None
        assert len(gpx.links) == 1

    def test_copyright_proxy(self, gpx_with_metadata_string):
        """Test copyright proxy."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        assert gpx.copyright is not None
        assert gpx.copyright.author == "Test Author"


class TestGPXCreation:
    """Tests for creating GPX programmatically."""

    def test_create_empty_gpx(self):
        """Test creating empty GPX."""
        gpx = GPX()
        assert gpx.creator == "PyGPX"
        assert gpx.metadata is None
        assert gpx.waypoints == []
        assert gpx.routes == []
        assert gpx.tracks == []

    def test_create_gpx_with_all_elements(
        self, sample_waypoint, sample_route, sample_track, sample_metadata
    ):
        """Test creating GPX with all elements."""
        gpx = GPX()
        gpx.creator = "TestApp"
        gpx.metadata = sample_metadata
        gpx.waypoints = [sample_waypoint]
        gpx.routes = [sample_route]
        gpx.tracks = [sample_track]

        output = gpx.to_string()
        assert 'creator="TestApp"' in output
        assert "<metadata>" in output
        assert "<wpt" in output
        assert "<rte>" in output
        assert "<trk>" in output

    def test_gpx_roundtrip_preserves_data(
        self, sample_waypoint, sample_route, sample_track, sample_metadata
    ):
        """Test that roundtrip preserves all data."""
        gpx1 = GPX()
        gpx1.creator = "TestApp"
        gpx1.metadata = sample_metadata
        gpx1.waypoints = [sample_waypoint]
        gpx1.routes = [sample_route]
        gpx1.tracks = [sample_track]

        output = gpx1.to_string()
        gpx2 = GPX.from_string(output)

        assert gpx2.creator == "TestApp"
        assert gpx2.metadata.name == sample_metadata.name
        assert len(gpx2.waypoints) == 1
        assert gpx2.waypoints[0].name == sample_waypoint.name


class TestGPXEncodingHandling:
    """Tests for GPX encoding handling."""

    def test_parse_string_with_utf8_encoding(self):
        """Test parsing string with UTF-8 encoding declaration."""
        gpx_str = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
     version="1.1"
     creator="Test">
</gpx>"""
        gpx = GPX.from_string(gpx_str)
        assert gpx.creator == "Test"

    def test_parse_string_without_encoding(self):
        """Test parsing string without encoding declaration."""
        gpx_str = """<?xml version="1.0"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
     version="1.1"
     creator="Test">
</gpx>"""
        gpx = GPX.from_string(gpx_str)
        assert gpx.creator == "Test"

    def test_unicode_content_preserved(self):
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
        gpx = GPX.from_string(gpx_str)
        assert gpx.waypoints[0].name == "Cafe"
