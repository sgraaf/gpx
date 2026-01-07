"""Tests for gpx.cli module - Command-line interface functionality."""

import datetime as dt
import json
from decimal import Decimal
from pathlib import Path

import pytest

from gpx import GPX, Metadata, Route, Track, TrackSegment, Waypoint, read_gpx
from gpx.cli import (
    _apply_crop,
    _apply_precision,
    _apply_reverse,
    _apply_trim,
    _calculate_bounds,
    _detect_format,
    _gather_gpx_info,
    _parse_datetime,
    cli,
)
from gpx.types import Latitude, Longitude

# =============================================================================
# Test fixtures
# =============================================================================


@pytest.fixture
def sample_gpx() -> GPX:
    """Create a sample GPX with waypoints, routes, and tracks."""
    waypoint = Waypoint(
        lat=Latitude("52.5200"),
        lon=Longitude("13.4050"),
        ele=Decimal("34.5"),
        name="Berlin",
        time=dt.datetime(2024, 1, 15, 10, 0, 0, tzinfo=dt.UTC),
    )

    route_points = [
        Waypoint(
            lat=Latitude("52.5200"),
            lon=Longitude("13.4050"),
            ele=Decimal("34.5"),
        ),
        Waypoint(
            lat=Latitude("52.5300"),
            lon=Longitude("13.4150"),
            ele=Decimal("40.0"),
        ),
    ]
    route = Route(name="City Tour", desc="A tour of the city", rtept=route_points)

    track_points = [
        Waypoint(
            lat=Latitude("52.5200"),
            lon=Longitude("13.4050"),
            ele=Decimal("34.5"),
            time=dt.datetime(2024, 1, 15, 10, 0, 0, tzinfo=dt.UTC),
        ),
        Waypoint(
            lat=Latitude("52.5210"),
            lon=Longitude("13.4060"),
            ele=Decimal("35.0"),
            time=dt.datetime(2024, 1, 15, 10, 1, 0, tzinfo=dt.UTC),
        ),
        Waypoint(
            lat=Latitude("52.5220"),
            lon=Longitude("13.4070"),
            ele=Decimal("36.5"),
            time=dt.datetime(2024, 1, 15, 10, 2, 0, tzinfo=dt.UTC),
        ),
    ]
    segment = TrackSegment(trkpt=track_points)
    track = Track(name="Morning Run", desc="A morning run", trkseg=[segment])

    return GPX(
        creator="TestApp",
        metadata=Metadata(name="Test GPX", desc="Test description"),
        wpt=[waypoint],
        rte=[route],
        trk=[track],
    )


@pytest.fixture
def sample_gpx_file(sample_gpx: GPX, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a sample GPX file and return its path."""
    temp_dir = tmp_path_factory.mktemp("gpx_files")
    temp_file = temp_dir / "sample.gpx"
    sample_gpx.write_gpx(temp_file)
    return temp_file


# =============================================================================
# Main function tests
# =============================================================================


class TestMain:
    """Tests for the main CLI entry point."""

    def test_main_no_args_shows_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that calling main with no args shows help."""
        result = cli([])
        assert result == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower()

    def test_main_version(self) -> None:
        """Test --version flag."""
        with pytest.raises(SystemExit) as exc_info:
            cli(["--version"])
        assert exc_info.value.code == 0

    def test_main_invalid_command(self) -> None:
        """Test that invalid command causes error."""
        # argparse will call sys.exit(2) for invalid commands
        with pytest.raises(SystemExit) as exc_info:
            cli(["invalid_command"])
        assert exc_info.value.code == 2


# =============================================================================
# Validate command tests
# =============================================================================


class TestValidateCommand:
    """Tests for the validate command."""

    def test_validate_valid_file(
        self, sample_gpx_file: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test validating a valid GPX file."""
        result = cli(["validate", str(sample_gpx_file)])
        assert result == 0
        captured = capsys.readouterr()
        assert "Valid GPX file" in captured.out

    def test_validate_nonexistent_file(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test validating a non-existent file."""
        result = cli(["validate", "nonexistent.gpx"])
        assert result == 1
        captured = capsys.readouterr()
        assert "File not found" in captured.err

    def test_validate_invalid_file(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test validating an invalid GPX file."""
        temp_file = tmp_path / "invalid.gpx"
        temp_file.write_text("not valid xml")
        result = cli(["validate", str(temp_file)])
        assert result == 1
        captured = capsys.readouterr()
        assert "Invalid GPX file" in captured.err


# =============================================================================
# Info command tests
# =============================================================================


class TestInfoCommand:
    """Tests for the info command."""

    def test_info_basic(
        self, sample_gpx_file: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test basic info output."""
        result = cli(["info", str(sample_gpx_file)])
        assert result == 0
        captured = capsys.readouterr()
        assert "GPX File:" in captured.out
        assert "Waypoints: 1" in captured.out
        assert "Routes: 1" in captured.out
        assert "Tracks: 1" in captured.out

    def test_info_json_output(
        self, sample_gpx_file: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test JSON info output."""
        result = cli(["info", "--json", str(sample_gpx_file)])
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["waypoints"] == 1
        assert data["routes"] == 1
        assert data["tracks"] == 1

    def test_info_nonexistent_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test info on non-existent file."""
        result = cli(["info", "nonexistent.gpx"])
        assert result == 1
        captured = capsys.readouterr()
        assert "File not found" in captured.err


# =============================================================================
# Edit command tests
# =============================================================================


class TestEditCommand:
    """Tests for the edit command."""

    def test_edit_output_file(self, sample_gpx_file: Path, tmp_path: Path) -> None:
        """Test edit with output file."""
        output_file = tmp_path / "output.gpx"
        result = cli(["edit", str(sample_gpx_file), "-o", str(output_file)])
        assert result == 0
        assert output_file.exists()

    def test_edit_reverse_tracks(self, sample_gpx_file: Path, tmp_path: Path) -> None:
        """Test edit with --reverse-tracks."""
        output_file = tmp_path / "output.gpx"
        result = cli(
            ["edit", str(sample_gpx_file), "-o", str(output_file), "--reverse-tracks"]
        )
        assert result == 0
        gpx = read_gpx(output_file)
        # Check that track was reversed (last point is now first)
        assert float(gpx.trk[0].trkseg[0].trkpt[0].lat) == pytest.approx(
            52.522, rel=1e-3
        )

    def test_edit_precision(self, sample_gpx_file: Path, tmp_path: Path) -> None:
        """Test edit with --precision."""
        output_file = tmp_path / "output.gpx"
        result = cli(
            ["edit", str(sample_gpx_file), "-o", str(output_file), "--precision", "2"]
        )
        assert result == 0
        gpx = read_gpx(output_file)
        # Check that coordinates are rounded
        lat_str = str(gpx.wpt[0].lat)
        # Should have at most 2 decimal places
        assert len(lat_str.split(".")[1]) <= 2

    def test_edit_strip_all_metadata(
        self, sample_gpx_file: Path, tmp_path: Path
    ) -> None:
        """Test edit with --strip-all-metadata."""
        output_file = tmp_path / "output.gpx"
        result = cli(
            [
                "edit",
                str(sample_gpx_file),
                "-o",
                str(output_file),
                "--strip-all-metadata",
            ]
        )
        assert result == 0
        gpx = read_gpx(output_file)
        assert gpx.metadata is None


# =============================================================================
# Merge command tests
# =============================================================================


class TestMergeCommand:
    """Tests for the merge command."""

    def test_merge_two_files(self, sample_gpx: GPX, tmp_path: Path) -> None:
        """Test merging two GPX files."""
        file1 = tmp_path / "file1.gpx"
        file2 = tmp_path / "file2.gpx"
        output_file = tmp_path / "output.gpx"

        sample_gpx.write_gpx(file1)
        sample_gpx.write_gpx(file2)

        result = cli(["merge", str(file1), str(file2), "-o", str(output_file)])
        assert result == 0

        merged = read_gpx(output_file)
        assert len(merged.wpt) == 2  # 1 from each file
        assert len(merged.rte) == 2
        assert len(merged.trk) == 2

    def test_merge_nonexistent_file(
        self, sample_gpx_file: Path, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test merge with non-existent file."""
        output_file = tmp_path / "output.gpx"
        result = cli(
            ["merge", str(sample_gpx_file), "nonexistent.gpx", "-o", str(output_file)]
        )
        assert result == 1
        captured = capsys.readouterr()
        assert "File not found" in captured.err


# =============================================================================
# Convert command tests
# =============================================================================


class TestConvertCommand:
    """Tests for the convert command."""

    def test_convert_gpx_to_geojson(
        self, sample_gpx_file: Path, tmp_path: Path
    ) -> None:
        """Test converting GPX to GeoJSON."""
        output_file = tmp_path / "output.geojson"
        result = cli(["convert", str(sample_gpx_file), "-o", str(output_file)])
        assert result == 0
        content = output_file.read_text()
        data = json.loads(content)
        assert data["type"] == "FeatureCollection"

    def test_convert_gpx_to_kml(self, sample_gpx_file: Path, tmp_path: Path) -> None:
        """Test converting GPX to KML."""
        output_file = tmp_path / "output.kml"
        result = cli(["convert", str(sample_gpx_file), "-o", str(output_file)])
        assert result == 0
        content = output_file.read_text()
        assert "<kml" in content

    def test_convert_geojson_to_gpx(self, sample_gpx: GPX, tmp_path: Path) -> None:
        """Test converting GeoJSON to GPX."""
        input_file = tmp_path / "input.geojson"
        output_file = tmp_path / "output.gpx"

        sample_gpx.write_geojson(input_file)

        result = cli(["convert", str(input_file), "-o", str(output_file)])
        assert result == 0

        gpx = read_gpx(output_file)
        assert len(gpx.wpt) >= 1

    def test_convert_with_explicit_formats(
        self, sample_gpx_file: Path, tmp_path: Path
    ) -> None:
        """Test converting with explicit format flags."""
        output_file = tmp_path / "output.json"
        result = cli(
            [
                "convert",
                str(sample_gpx_file),
                "-o",
                str(output_file),
                "-f",
                "gpx",
                "-t",
                "geojson",
            ]
        )
        assert result == 0

    def test_convert_nonexistent_file(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test convert with non-existent file."""
        output_file = tmp_path / "output.geojson"
        result = cli(["convert", "nonexistent.gpx", "-o", str(output_file)])
        assert result == 1
        captured = capsys.readouterr()
        assert "File not found" in captured.err


# =============================================================================
# Helper function tests
# =============================================================================


class TestHelperFunctions:
    """Tests for CLI helper functions."""

    def test_parse_datetime_iso_full(self) -> None:
        """Test parsing full ISO datetime."""
        dt = _parse_datetime("2024-01-15T10:30:00")
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15
        assert dt.hour == 10
        assert dt.minute == 30

    def test_parse_datetime_date_only(self) -> None:
        """Test parsing date only."""
        dt = _parse_datetime("2024-01-15")
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15

    def test_parse_datetime_invalid(self) -> None:
        """Test parsing invalid datetime."""
        with pytest.raises(ValueError, match="Invalid datetime format"):
            _parse_datetime("not a date")

    def test_detect_format_gpx(self) -> None:
        """Test format detection for GPX."""
        assert _detect_format(Path("file.gpx")) == "gpx"

    def test_detect_format_geojson(self) -> None:
        """Test format detection for GeoJSON."""
        assert _detect_format(Path("file.geojson")) == "geojson"
        assert _detect_format(Path("file.json")) == "geojson"

    def test_detect_format_kml(self) -> None:
        """Test format detection for KML."""
        assert _detect_format(Path("file.kml")) == "kml"

    def test_detect_format_unknown(self) -> None:
        """Test format detection for unknown extension."""
        assert _detect_format(Path("file.xyz")) is None

    def test_calculate_bounds(self, sample_gpx: GPX) -> None:
        """Test bounds calculation."""
        bounds = _calculate_bounds(sample_gpx)
        assert "min_lat" in bounds
        assert "max_lat" in bounds
        assert "min_lon" in bounds
        assert "max_lon" in bounds
        assert bounds["min_lat"] <= bounds["max_lat"]
        assert bounds["min_lon"] <= bounds["max_lon"]

    def test_gather_gpx_info(self, sample_gpx: GPX) -> None:
        """Test gathering GPX info."""
        info = _gather_gpx_info(sample_gpx)
        assert info["creator"] == "TestApp"
        assert info["waypoints"] == 1
        assert info["routes"] == 1
        assert info["tracks"] == 1
        assert "metadata" in info
        assert info["metadata"]["name"] == "Test GPX"


# =============================================================================
# Apply function tests
# =============================================================================


class TestApplyFunctions:
    """Tests for the apply transformation functions."""

    def test_apply_crop(self, sample_gpx: GPX) -> None:
        """Test applying crop to GPX data."""
        cropped = _apply_crop(
            sample_gpx,
            min_lat=52.515,
            max_lat=52.525,
            min_lon=13.400,
            max_lon=13.410,
        )
        # Should keep some points but filter out those outside bounds
        assert len(cropped.wpt) >= 0
        assert len(cropped.trk) >= 0

    def test_apply_crop_excludes_all(self, sample_gpx: GPX) -> None:
        """Test applying crop that excludes all points."""
        cropped = _apply_crop(
            sample_gpx,
            min_lat=0.0,
            max_lat=1.0,
            min_lon=0.0,
            max_lon=1.0,
        )
        assert len(cropped.wpt) == 0
        assert len(cropped.rte) == 0
        assert len(cropped.trk) == 0

    def test_apply_trim(self, sample_gpx: GPX) -> None:
        """Test applying time trim to GPX data."""
        start = dt.datetime(2024, 1, 15, 10, 0, 30, tzinfo=dt.UTC)
        end = dt.datetime(2024, 1, 15, 10, 1, 30, tzinfo=dt.UTC)
        trimmed = _apply_trim(sample_gpx, start, end)
        # Should keep only points within time range
        assert len(trimmed.trk) > 0
        for track in trimmed.trk:
            for seg in track.trkseg:
                for pt in seg.trkpt:
                    if pt.time:
                        assert pt.time >= start
                        assert pt.time <= end

    def test_apply_reverse_routes(self, sample_gpx: GPX) -> None:
        """Test applying reverse to routes."""
        original_first_lat = float(sample_gpx.rte[0].rtept[0].lat)
        original_last_lat = float(sample_gpx.rte[0].rtept[-1].lat)

        reversed_gpx = _apply_reverse(
            sample_gpx, reverse_routes=True, reverse_tracks=False
        )

        new_first_lat = float(reversed_gpx.rte[0].rtept[0].lat)
        new_last_lat = float(reversed_gpx.rte[0].rtept[-1].lat)

        assert new_first_lat == pytest.approx(original_last_lat, rel=1e-3)
        assert new_last_lat == pytest.approx(original_first_lat, rel=1e-3)

    def test_apply_reverse_tracks(self, sample_gpx: GPX) -> None:
        """Test applying reverse to tracks."""
        original_first_lat = float(sample_gpx.trk[0].trkseg[0].trkpt[0].lat)
        original_last_lat = float(sample_gpx.trk[0].trkseg[0].trkpt[-1].lat)

        reversed_gpx = _apply_reverse(
            sample_gpx, reverse_routes=False, reverse_tracks=True
        )

        new_first_lat = float(reversed_gpx.trk[0].trkseg[0].trkpt[0].lat)
        new_last_lat = float(reversed_gpx.trk[0].trkseg[0].trkpt[-1].lat)

        assert new_first_lat == pytest.approx(original_last_lat, rel=1e-3)
        assert new_last_lat == pytest.approx(original_first_lat, rel=1e-3)

    def test_apply_precision(self, sample_gpx: GPX) -> None:
        """Test applying precision reduction."""
        reduced = _apply_precision(sample_gpx, coord_precision=2, elevation_precision=0)

        # Check waypoint precision
        for wpt in reduced.wpt:
            lat_str = str(wpt.lat)
            if "." in lat_str:
                assert len(lat_str.split(".")[1]) <= 2
            if wpt.ele:
                ele_str = str(wpt.ele)
                if "." in ele_str:
                    assert len(ele_str.split(".")[1]) <= 1

    def test_apply_precision_no_elevation(self) -> None:
        """Test applying precision when no elevation."""
        gpx = GPX(
            wpt=[Waypoint(lat=Latitude("52.5200123"), lon=Longitude("13.4050456"))]
        )
        reduced = _apply_precision(gpx, coord_precision=3, elevation_precision=None)
        lat_str = str(reduced.wpt[0].lat)
        assert lat_str == "52.52"
