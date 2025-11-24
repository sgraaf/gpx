"""Smoke tests for the GPX package.

These tests verify that the most critical functionality of the package works.
They are designed to catch major breakage and ensure basic operations succeed.
"""

import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from gpx import (
    GPX,
    Bounds,
    Email,
    Link,
    Metadata,
    Person,
    Route,
    Track,
    TrackSegment,
    Waypoint,
)
from gpx.types import Latitude, Longitude


class TestPackageImport:
    """Test that the package and key classes can be imported."""

    def test_import_main_classes(self) -> None:
        """Test importing main classes from gpx package."""
        # If we got here, imports succeeded
        assert GPX is not None
        assert Waypoint is not None
        assert Track is not None
        assert Route is not None
        assert Metadata is not None

    def test_import_types(self) -> None:
        """Test importing custom types."""
        assert Latitude is not None
        assert Longitude is not None


class TestBasicReadWrite:
    """Test basic read and write operations."""

    def test_read_minimal_gpx(self, minimal_gpx_string: str) -> None:
        """Test reading a minimal GPX string."""
        gpx = GPX.from_string(minimal_gpx_string)
        assert gpx is not None
        assert gpx.creator == "TestCreator"

    def test_write_gpx_to_string(self) -> None:
        """Test writing GPX to string."""
        gpx = GPX()
        gpx.creator = "SmokeTest"
        output = gpx.to_string()
        assert "<gpx" in output
        assert 'creator="SmokeTest"' in output
        assert 'version="1.1"' in output

    def test_write_gpx_to_file(self) -> None:
        """Test writing GPX to file."""
        gpx = GPX()
        gpx.creator = "SmokeTest"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False) as f:
            temp_path = Path(f.name)

        try:
            gpx.to_file(temp_path)
            assert temp_path.exists()
            content = temp_path.read_text()
            assert 'creator="SmokeTest"' in content
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_read_gpx_from_file(self, minimal_gpx_string: str) -> None:
        """Test reading GPX from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False) as f:
            f.write(minimal_gpx_string)
            temp_path = Path(f.name)

        try:
            gpx = GPX.from_file(temp_path)
            assert gpx.creator == "TestCreator"
        finally:
            if temp_path.exists():
                temp_path.unlink()


class TestRoundTrip:
    """Test round-trip operations (read -> modify -> write -> read)."""

    def test_roundtrip_preserves_data(self, full_gpx_string: str) -> None:
        """Test that data is preserved through read-write-read cycle."""
        # Read original
        gpx1 = GPX.from_string(full_gpx_string)

        # Write to string
        output = gpx1.to_string()

        # Read again
        gpx2 = GPX.from_string(output)

        # Verify data preserved
        assert gpx2.creator == gpx1.creator
        assert gpx2.metadata is not None
        assert gpx2.metadata.name == gpx1.metadata.name
        assert len(gpx2.waypoints) == len(gpx1.waypoints)
        assert len(gpx2.tracks) == len(gpx1.tracks)
        assert len(gpx2.routes) == len(gpx1.routes)

    def test_roundtrip_file_io(self, full_gpx_string: str) -> None:
        """Test round-trip through file I/O."""
        gpx1 = GPX.from_string(full_gpx_string)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Write to file
            gpx1.to_file(temp_path)

            # Read from file
            gpx2 = GPX.from_file(temp_path)

            # Verify data preserved
            assert len(gpx2.waypoints) == len(gpx1.waypoints)
            assert len(gpx2.tracks) == len(gpx1.tracks)
            assert len(gpx2.routes) == len(gpx1.routes)
        finally:
            if temp_path.exists():
                temp_path.unlink()


class TestProgrammaticCreation:
    """Test creating GPX data programmatically."""

    def test_create_waypoint(self) -> None:
        """Test creating a waypoint programmatically."""
        wpt = Waypoint()
        wpt.lat = Latitude("52.5200")
        wpt.lon = Longitude("13.4050")
        wpt.ele = Decimal("100.5")
        wpt.name = "Test Point"
        wpt.time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        assert wpt.lat == Latitude("52.5200")
        assert wpt.lon == Longitude("13.4050")
        assert wpt.name == "Test Point"

    def test_create_track(self) -> None:
        """Test creating a track with segments and points."""
        # Create points
        pt1 = Waypoint()
        pt1.lat = Latitude("52.5200")
        pt1.lon = Longitude("13.4050")
        pt1.time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        pt2 = Waypoint()
        pt2.lat = Latitude("52.5210")
        pt2.lon = Longitude("13.4060")
        pt2.time = datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc)

        # Create segment
        seg = TrackSegment()
        seg.trkpts = [pt1, pt2]

        # Create track
        track = Track()
        track.name = "Test Track"
        track.trksegs = [seg]

        assert track.name == "Test Track"
        assert len(track.trksegs) == 1
        assert len(track.trksegs[0].trkpts) == 2

    def test_create_complete_gpx(self) -> None:
        """Test creating a complete GPX structure programmatically."""
        # Create waypoint
        wpt = Waypoint()
        wpt.lat = Latitude("52.5200")
        wpt.lon = Longitude("13.4050")
        wpt.name = "Start"

        # Create track
        track = Track()
        track.name = "My Track"
        seg = TrackSegment()
        pt = Waypoint()
        pt.lat = Latitude("52.5210")
        pt.lon = Longitude("13.4060")
        seg.trkpts = [pt]
        track.trksegs = [seg]

        # Create metadata
        metadata = Metadata()
        metadata.name = "My GPX File"
        metadata.desc = "Created for smoke testing"
        metadata.time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Create GPX
        gpx = GPX()
        gpx.creator = "SmokeTest"
        gpx.metadata = metadata
        gpx.waypoints = [wpt]
        gpx.tracks = [track]

        # Verify structure
        assert gpx.creator == "SmokeTest"
        assert gpx.metadata.name == "My GPX File"
        assert len(gpx.waypoints) == 1
        assert len(gpx.tracks) == 1

        # Verify it can be serialized
        output = gpx.to_string()
        assert "<gpx" in output
        assert "<metadata>" in output
        assert "<wpt" in output
        assert "<trk>" in output


class TestKeyFeatures:
    """Test key features of the package."""

    def test_waypoints(self, gpx_with_waypoint_string: str) -> None:
        """Test waypoint parsing and access."""
        gpx = GPX.from_string(gpx_with_waypoint_string)
        assert len(gpx.waypoints) == 1
        wpt = gpx.waypoints[0]
        assert wpt.name == "Berlin"
        assert wpt.lat == Latitude("52.5200")
        assert wpt.lon == Longitude("13.4050")

    def test_tracks(self, gpx_with_track_string: str) -> None:
        """Test track parsing and access."""
        gpx = GPX.from_string(gpx_with_track_string)
        assert len(gpx.tracks) == 1
        track = gpx.tracks[0]
        assert track.name == "Morning Run"
        assert len(track.trksegs) == 2
        # First segment has 3 points
        assert len(track.trksegs[0].trkpts) == 3

    def test_routes(self, gpx_with_route_string: str) -> None:
        """Test route parsing and access."""
        gpx = GPX.from_string(gpx_with_route_string)
        assert len(gpx.routes) == 1
        route = gpx.routes[0]
        assert route.name == "City Tour"
        assert len(route.rtepts) == 3

    def test_metadata(self, gpx_with_metadata_string: str) -> None:
        """Test metadata parsing and access."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        assert gpx.metadata.name == "Test GPX File"
        assert gpx.metadata.author is not None
        assert gpx.metadata.author.name == "Test Author"

    def test_metadata_proxies(self, gpx_with_metadata_string: str) -> None:
        """Test convenient metadata access via GPX proxies."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        # Test proxies work
        assert gpx.name == "Test GPX File"
        assert gpx.desc == "A test GPX file for unit testing"
        assert gpx.author is not None
        assert gpx.author.name == "Test Author"


class TestValidation:
    """Test GPX validation functionality."""

    def test_validation_passes_for_valid_gpx(self, minimal_gpx_string: str) -> None:
        """Test that valid GPX passes validation."""
        # Should not raise
        gpx = GPX.from_string(minimal_gpx_string, validate=True)
        assert gpx is not None

    def test_validation_disabled_by_default(self, minimal_gpx_string: str) -> None:
        """Test that validation is disabled by default."""
        # Should not raise even with malformed content (if parseable)
        gpx = GPX.from_string(minimal_gpx_string)
        assert gpx is not None


class TestStatistics:
    """Test statistics functionality on tracks and routes."""

    def test_track_statistics(self, gpx_with_track_string: str) -> None:
        """Test that track statistics are available."""
        gpx = GPX.from_string(gpx_with_track_string)
        track = gpx.tracks[0]

        # Should have statistics methods/properties
        assert hasattr(track, "total_distance")
        assert hasattr(track, "bounds")
        assert hasattr(track, "total_duration")

        # Bounds should work - returns tuple of (minlat, minlon, maxlat, maxlon)
        bounds = track.bounds
        assert bounds is not None
        assert len(bounds) == 4
        assert bounds[0] is not None  # minlat
        assert bounds[2] is not None  # maxlat

    def test_route_statistics(self, gpx_with_route_string: str) -> None:
        """Test that route statistics are available."""
        gpx = GPX.from_string(gpx_with_route_string)
        route = gpx.routes[0]

        # Should have statistics methods/properties
        assert hasattr(route, "total_distance")
        assert hasattr(route, "bounds")

        # Bounds should work
        bounds = route.bounds
        assert bounds is not None


class TestEndToEnd:
    """End-to-end smoke test scenarios."""

    def test_complete_workflow(self) -> None:
        """Test a complete workflow: create, modify, save, load, verify."""
        # 1. Create a GPX file programmatically
        gpx1 = GPX()
        gpx1.creator = "E2E Test"
        gpx1.name = "My Activity"

        # Add a waypoint
        wpt = Waypoint()
        wpt.lat = Latitude("52.5200")
        wpt.lon = Longitude("13.4050")
        wpt.name = "Start Point"
        gpx1.waypoints = [wpt]

        # Add a track
        track = Track()
        track.name = "My Track"
        seg = TrackSegment()

        # Add track points
        for i in range(3):
            pt = Waypoint()
            pt.lat = Latitude(f"52.{5200 + i}")
            pt.lon = Longitude(f"13.{4050 + i}")
            pt.time = datetime(2024, 1, 1, 12, i, 0, tzinfo=timezone.utc)
            seg.trkpts.append(pt)

        track.trksegs = [seg]
        gpx1.tracks = [track]

        # 2. Save to file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False) as f:
            temp_path = Path(f.name)

        try:
            gpx1.to_file(temp_path)

            # 3. Load from file
            gpx2 = GPX.from_file(temp_path)

            # 4. Verify data integrity
            assert gpx2.creator == "E2E Test"
            assert gpx2.name == "My Activity"
            assert len(gpx2.waypoints) == 1
            assert gpx2.waypoints[0].name == "Start Point"
            assert len(gpx2.tracks) == 1
            assert gpx2.tracks[0].name == "My Track"
            assert len(gpx2.tracks[0].trksegs[0].trkpts) == 3

            # 5. Modify and re-save
            gpx2.name = "Modified Activity"
            gpx2.to_file(temp_path)

            # 6. Load again and verify modification
            gpx3 = GPX.from_file(temp_path)
            assert gpx3.name == "Modified Activity"

        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_mixed_content_file(self, full_gpx_string: str) -> None:
        """Test working with a GPX file containing all element types."""
        # Parse
        gpx = GPX.from_string(full_gpx_string)

        # Verify all elements present
        assert gpx.metadata is not None
        assert len(gpx.waypoints) > 0
        assert len(gpx.routes) > 0
        assert len(gpx.tracks) > 0

        # Modify each type
        gpx.metadata.name = "Modified"
        gpx.waypoints[0].name = "Modified Waypoint"
        gpx.routes[0].name = "Modified Route"
        gpx.tracks[0].name = "Modified Track"

        # Serialize and parse again
        output = gpx.to_string()
        gpx2 = GPX.from_string(output)

        # Verify modifications preserved
        assert gpx2.metadata.name == "Modified"
        assert gpx2.waypoints[0].name == "Modified Waypoint"
        assert gpx2.routes[0].name == "Modified Route"
        assert gpx2.tracks[0].name == "Modified Track"
