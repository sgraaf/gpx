"""Smoke tests for the GPX package.

These tests verify that the most critical functionality of the package works.
They are designed to catch major breakage and ensure basic operations succeed.
"""

import datetime as dt
from decimal import Decimal
from pathlib import Path

from gpx import (
    GPX,
    Metadata,
    Route,
    Track,
    TrackSegment,
    Waypoint,
    from_string,
    read_gpx,
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
        gpx = from_string(minimal_gpx_string)
        assert gpx is not None
        assert gpx.creator == "TestCreator"

    def test_write_gpx_to_string(self) -> None:
        """Test writing GPX to string."""
        gpx = GPX(creator="SmokeTest")
        output = gpx.to_string()
        assert "<gpx" in output
        assert 'creator="SmokeTest"' in output
        assert 'version="1.1"' in output

    def test_write_gpx_to_file(self, tmp_path: Path) -> None:
        """Test writing GPX to file."""
        gpx = GPX(creator="SmokeTest")

        temp_file = tmp_path / "output.gpx"
        gpx.write_gpx(temp_file)
        assert temp_file.exists()
        content = temp_file.read_text()
        assert 'creator="SmokeTest"' in content

    def test_read_gpx_from_file(self, minimal_gpx_string: str, tmp_path: Path) -> None:
        """Test reading GPX from file."""
        temp_file = tmp_path / "input.gpx"
        temp_file.write_text(minimal_gpx_string)
        gpx = read_gpx(temp_file)
        assert gpx.creator == "TestCreator"


class TestRoundTrip:
    """Test round-trip operations (read -> modify -> write -> read)."""

    def test_roundtrip_preserves_data(self, full_gpx_string: str) -> None:
        """Test that data is preserved through read-write-read cycle."""
        # Read original
        gpx1 = from_string(full_gpx_string)

        # Write to string
        output = gpx1.to_string()

        # Read again
        gpx2 = from_string(output)

        # Verify data preserved
        assert gpx2.creator == gpx1.creator
        assert gpx1.metadata is not None
        assert gpx2.metadata is not None
        assert gpx2.metadata.name == gpx1.metadata.name
        assert len(gpx2.wpt) == len(gpx1.wpt)
        assert len(gpx2.trk) == len(gpx1.trk)
        assert len(gpx2.rte) == len(gpx1.rte)

    def test_roundtrip_file_io(self, full_gpx_string: str, tmp_path: Path) -> None:
        """Test round-trip through file I/O."""
        gpx1 = from_string(full_gpx_string)

        temp_file = tmp_path / "roundtrip.gpx"

        # Write to file
        gpx1.write_gpx(temp_file)

        # Read from file
        gpx2 = read_gpx(temp_file)

        # Verify data preserved
        assert len(gpx2.wpt) == len(gpx1.wpt)
        assert len(gpx2.trk) == len(gpx1.trk)
        assert len(gpx2.rte) == len(gpx1.rte)


class TestProgrammaticCreation:
    """Test creating GPX data programmatically."""

    def test_create_waypoint(self) -> None:
        """Test creating a waypoint programmatically."""
        wpt = Waypoint(
            lat=Latitude("52.5200"),
            lon=Longitude("13.4050"),
            ele=Decimal("100.5"),
            name="Test Point",
            time=dt.datetime(2024, 1, 1, 12, 0, 0, tzinfo=dt.UTC),
        )

        assert wpt.lat == Latitude("52.5200")
        assert wpt.lon == Longitude("13.4050")
        assert wpt.name == "Test Point"

    def test_create_track(self) -> None:
        """Test creating a track with segments and points."""
        # Create points
        pt1 = Waypoint(
            lat=Latitude("52.5200"),
            lon=Longitude("13.4050"),
            time=dt.datetime(2024, 1, 1, 12, 0, 0, tzinfo=dt.UTC),
        )

        pt2 = Waypoint(
            lat=Latitude("52.5210"),
            lon=Longitude("13.4060"),
            time=dt.datetime(2024, 1, 1, 12, 1, 0, tzinfo=dt.UTC),
        )

        # Create segment
        seg = TrackSegment(trkpt=[pt1, pt2])

        # Create track
        track = Track(name="Test Track", trkseg=[seg])

        assert track.name == "Test Track"
        assert len(track.trkseg) == 1
        assert len(track.trkseg[0].trkpt) == 2

    def test_create_complete_gpx(self) -> None:
        """Test creating a complete GPX structure programmatically."""
        # Create waypoint
        wpt = Waypoint(
            lat=Latitude("52.5200"),
            lon=Longitude("13.4050"),
            name="Start",
        )

        # Create track
        pt = Waypoint(
            lat=Latitude("52.5210"),
            lon=Longitude("13.4060"),
        )
        seg = TrackSegment(trkpt=[pt])
        track = Track(name="My Track", trkseg=[seg])

        # Create metadata
        metadata = Metadata(
            name="My GPX File",
            desc="Created for smoke testing",
            time=dt.datetime(2024, 1, 1, 12, 0, 0, tzinfo=dt.UTC),
        )

        # Create GPX
        gpx = GPX(
            creator="SmokeTest",
            metadata=metadata,
            wpt=[wpt],
            trk=[track],
        )

        # Verify structure
        assert gpx.creator == "SmokeTest"
        assert gpx.metadata is not None
        assert gpx.metadata.name == "My GPX File"
        assert len(gpx.wpt) == 1
        assert len(gpx.trk) == 1

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
        gpx = from_string(gpx_with_waypoint_string)
        assert len(gpx.wpt) == 1
        wpt = gpx.wpt[0]
        assert wpt.name == "Berlin"
        assert wpt.lat == Latitude("52.5200")
        assert wpt.lon == Longitude("13.4050")

    def test_tracks(self, gpx_with_track_string: str) -> None:
        """Test track parsing and access."""
        gpx = from_string(gpx_with_track_string)
        assert len(gpx.trk) == 1
        track = gpx.trk[0]
        assert track.name == "Morning Run"
        assert len(track.trkseg) == 2
        # First segment has 3 points
        assert len(track.trkseg[0].trkpt) == 3

    def test_routes(self, gpx_with_route_string: str) -> None:
        """Test route parsing and access."""
        gpx = from_string(gpx_with_route_string)
        assert len(gpx.rte) == 1
        route = gpx.rte[0]
        assert route.name == "City Tour"
        assert len(route.rtept) == 3

    def test_metadata(self, gpx_with_metadata_string: str) -> None:
        """Test metadata parsing and access."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        assert gpx.metadata.name == "Test GPX File"
        assert gpx.metadata.author is not None
        assert gpx.metadata.author.name == "Test Author"


class TestStatistics:
    """Test statistics functionality on tracks and routes."""

    def test_track_statistics(self, gpx_with_track_string: str) -> None:
        """Test that track statistics are available."""
        gpx = from_string(gpx_with_track_string)
        track = gpx.trk[0]

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
        gpx = from_string(gpx_with_route_string)
        route = gpx.rte[0]

        # Should have statistics methods/properties
        assert hasattr(route, "total_distance")
        assert hasattr(route, "bounds")

        # Bounds should work
        bounds = route.bounds
        assert bounds is not None


class TestEndToEnd:
    """End-to-end smoke test scenarios."""

    def test_complete_workflow(self, tmp_path: Path) -> None:
        """Test a complete workflow: create, modify, save, load, verify."""
        # 1. Create a GPX file programmatically
        # Add a waypoint
        wpt = Waypoint(
            lat=Latitude("52.5200"),
            lon=Longitude("13.4050"),
            name="Start Point",
        )

        # Add track points
        track_points = []
        for i in range(3):
            pt = Waypoint(
                lat=Latitude(f"52.{5200 + i}"),
                lon=Longitude(f"13.{4050 + i}"),
                time=dt.datetime(2024, 1, 1, 12, i, 0, tzinfo=dt.UTC),
            )
            track_points.append(pt)

        seg = TrackSegment(trkpt=track_points)
        track = Track(name="My Track", trkseg=[seg])

        gpx1 = GPX(
            creator="E2E Test",
            metadata=Metadata(name="My Activity"),
            wpt=[wpt],
            trk=[track],
        )

        # 2. Save to file
        temp_file = tmp_path / "workflow.gpx"
        gpx1.write_gpx(temp_file)

        # 3. Load from file
        gpx2 = read_gpx(temp_file)

        # 4. Verify data integrity
        assert gpx2.creator == "E2E Test"
        assert gpx2.metadata is not None
        assert gpx2.metadata.name == "My Activity"
        assert len(gpx2.wpt) == 1
        assert gpx2.wpt[0].name == "Start Point"
        assert len(gpx2.trk) == 1
        assert gpx2.trk[0].name == "My Track"
        assert len(gpx2.trk[0].trkseg[0].trkpt) == 3

        # 5. Modify and re-save
        # Note: GPX objects are immutable, so we need to create a new one
        modified_metadata = Metadata(name="Modified Activity")
        gpx_modified = GPX(
            creator=gpx2.creator,
            metadata=modified_metadata,
            wpt=gpx2.wpt,
            trk=gpx2.trk,
        )
        gpx_modified.write_gpx(temp_file)

        # 6. Load again and verify modification
        gpx3 = read_gpx(temp_file)
        assert gpx3.metadata
        assert gpx3.metadata.name == "Modified Activity"

    def test_mixed_content_file(self, full_gpx_string: str) -> None:
        """Test working with a GPX file containing all element types."""
        # Parse
        gpx = from_string(full_gpx_string)

        # Verify all elements present
        assert gpx.metadata is not None
        assert len(gpx.wpt) > 0
        assert len(gpx.rte) > 0
        assert len(gpx.trk) > 0

        # Modify each type
        gpx.metadata.name = "Modified"
        gpx.wpt[0].name = "Modified Waypoint"
        gpx.rte[0].name = "Modified Route"
        gpx.trk[0].name = "Modified Track"

        # Serialize and parse again
        output = gpx.to_string()
        gpx2 = from_string(output)

        # Verify modifications preserved
        assert gpx2.metadata is not None
        assert gpx2.metadata.name == "Modified"
        assert gpx2.wpt[0].name == "Modified Waypoint"
        assert gpx2.rte[0].name == "Modified Route"
        assert gpx2.trk[0].name == "Modified Track"
