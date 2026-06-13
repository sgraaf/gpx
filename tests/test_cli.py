"""Tests for gpx.cli module - Command-line interface functionality."""

import datetime as dt
import json
from pathlib import Path

import pytest

from gpx import GPX, Track, TrackSegment, Waypoint, read_gpx
from gpx.cli import _calculate_bounds, _gather_gpx_info, _parse_datetime, cli
from gpx.types import Latitude, Longitude

from .conftest import (
    CUSTOM_NS,
    GARMIN_TPX_NS,
    create_custom_extension,
    create_track_point_extension,
)


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

    def test_validate_malformed_file(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test validating a not-well-formed XML file."""
        temp_file = tmp_path / "invalid.gpx"
        temp_file.write_text("not valid xml")
        result = cli(["validate", str(temp_file)])
        assert result == 1
        captured = capsys.readouterr()
        assert "not well-formed" in captured.out

    def test_validate_schema_error(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test validating a file with a schema error (unknown element)."""
        temp_file = tmp_path / "bad.gpx"
        temp_file.write_text(
            '<?xml version="1.0"?>\n'
            '<gpx xmlns="http://www.topografix.com/GPX/1/1" '
            'version="1.1" creator="Test">\n'
            '  <wpt lat="52.0" lon="4.0"><nmae>oops</nmae></wpt>\n'
            "</gpx>\n"
        )
        result = cli(["validate", str(temp_file)])
        assert result == 1
        captured = capsys.readouterr()
        assert "unknown element" in captured.out
        assert "ERROR" in captured.out

    def test_validate_warning_not_strict(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test that warnings alone do not fail validation."""
        temp_file = tmp_path / "warn.gpx"
        temp_file.write_text(
            '<?xml version="1.0"?>\n'
            '<gpx xmlns="http://www.topografix.com/GPX/1/1" '
            'version="1.0" creator="Test"/>\n'
        )
        result = cli(["validate", str(temp_file)])
        assert result == 0
        captured = capsys.readouterr()
        assert "WARNING" in captured.out
        assert "Valid GPX file" in captured.out

    def test_validate_strict_fails_on_warning(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test that --strict makes warnings fail."""
        temp_file = tmp_path / "warn.gpx"
        temp_file.write_text(
            '<?xml version="1.0"?>\n'
            '<gpx xmlns="http://www.topografix.com/GPX/1/1" '
            'version="1.0" creator="Test"/>\n'
        )
        result = cli(["validate", "--strict", str(temp_file)])
        assert result == 1
        captured = capsys.readouterr()
        assert "WARNING" in captured.out
        # A failing run must not claim the file is valid.
        assert "Valid GPX file" not in captured.out

    def test_validate_strict_json_reports_passed_false(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test that --strict --json reports valid=True but passed=False."""
        temp_file = tmp_path / "warn.gpx"
        temp_file.write_text(
            '<?xml version="1.0"?>\n'
            '<gpx xmlns="http://www.topografix.com/GPX/1/1" '
            'version="1.0" creator="Test"/>\n'
        )
        result = cli(["validate", "--strict", "--json", str(temp_file)])
        assert result == 1
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["valid"] is True
        assert data["passed"] is False
        assert data["warnings"] == 1

    def test_validate_json_output(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test JSON validation report output."""
        temp_file = tmp_path / "bad.gpx"
        temp_file.write_text(
            '<?xml version="1.0"?>\n'
            '<gpx xmlns="http://www.topografix.com/GPX/1/1" '
            'version="1.1" creator="Test">\n'
            '  <wpt lat="91.0" lon="4.0"/>\n'
            "</gpx>\n"
        )
        result = cli(["validate", "--json", str(temp_file)])
        assert result == 1
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["valid"] is False
        assert data["errors"] == 1
        assert data["issues"][0]["severity"] == "error"

    def test_validate_json_nonexistent_file(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test JSON output for a non-existent file."""
        result = cli(["validate", "--json", "nonexistent.gpx"])
        assert result == 1
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "error" in data


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

    def test_edit_split_time_gap(self, sample_gpx_file: Path, tmp_path: Path) -> None:
        """Test edit with --split-time-gap."""
        output_file = tmp_path / "output.gpx"
        # Sample track points are 1 minute apart; split at 30 seconds
        result = cli(
            [
                "edit",
                str(sample_gpx_file),
                "-o",
                str(output_file),
                "--split-time-gap",
                "30",
            ]
        )
        assert result == 0
        gpx = read_gpx(output_file)
        assert len(gpx.trk[0].trkseg) == 3

    def test_edit_split_distance_gap(
        self, sample_gpx_file: Path, tmp_path: Path
    ) -> None:
        """Test edit with --split-distance-gap."""
        output_file = tmp_path / "output.gpx"
        # Sample track points are ~130 m apart; split at 50 m
        result = cli(
            [
                "edit",
                str(sample_gpx_file),
                "-o",
                str(output_file),
                "--split-distance-gap",
                "50",
            ]
        )
        assert result == 0
        gpx = read_gpx(output_file)
        assert len(gpx.trk[0].trkseg) == 3

    def test_edit_simplify(self, sample_gpx_file: Path, tmp_path: Path) -> None:
        """Test edit with --simplify."""
        output_file = tmp_path / "output.gpx"
        result = cli(
            [
                "edit",
                str(sample_gpx_file),
                "-o",
                str(output_file),
                "--simplify",
                "1000",
            ]
        )
        assert result == 0
        gpx = read_gpx(output_file)
        # With a huge tolerance, only the endpoints of the track remain
        assert len(gpx.trk[0].trkseg[0].trkpt) == 2

    def test_edit_smooth(self, sample_gpx_file: Path, tmp_path: Path) -> None:
        """Test edit with --smooth."""
        output_file = tmp_path / "output.gpx"
        result = cli(
            ["edit", str(sample_gpx_file), "-o", str(output_file), "--smooth", "3"]
        )
        assert result == 0
        gpx = read_gpx(output_file)
        assert len(gpx.trk[0].trkseg[0].trkpt) == 3

    def test_edit_smooth_invalid_window(
        self, sample_gpx_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test edit with an invalid --smooth window."""
        output_file = tmp_path / "output.gpx"
        result = cli(
            ["edit", str(sample_gpx_file), "-o", str(output_file), "--smooth", "2"]
        )
        assert result == 1
        captured = capsys.readouterr()
        assert "window" in captured.err

    def test_edit_shift_time(self, sample_gpx_file: Path, tmp_path: Path) -> None:
        """Test edit with --shift-time."""
        output_file = tmp_path / "output.gpx"
        result = cli(
            [
                "edit",
                str(sample_gpx_file),
                "-o",
                str(output_file),
                "--shift-time",
                "3600",
            ]
        )
        assert result == 0
        original = read_gpx(sample_gpx_file)
        shifted = read_gpx(output_file)
        original_time = original.wpt[0].time
        assert original_time is not None
        assert shifted.wpt[0].time == original_time + dt.timedelta(hours=1)

    def test_edit_strip_extensions(self, tmp_path: Path) -> None:
        """Test edit with --strip-extensions."""
        input_file = tmp_path / "input.gpx"
        gpx = GPX(
            wpt=[
                Waypoint(
                    lat=Latitude("52.0"),
                    lon=Longitude("4.0"),
                    extensions=create_custom_extension("rating", "5"),
                )
            ],
            extensions=create_custom_extension("source", "TestApp"),
        )
        gpx.write_gpx(input_file)

        output_file = tmp_path / "output.gpx"
        result = cli(
            ["edit", str(input_file), "-o", str(output_file), "--strip-extensions"]
        )
        assert result == 0
        stripped = read_gpx(output_file)
        assert stripped.extensions is None
        assert stripped.wpt[0].extensions is None

    def test_edit_crop_with_zero_bound(
        self, sample_gpx_file: Path, tmp_path: Path
    ) -> None:
        """A bound of 0 must trigger the crop (regression: any() treated 0 as falsy).

        sample_gpx points are all near (52.5, 13.4); a min-lat of 0 must keep
        them while a min-lat of 53 must drop them.
        """
        out_keep = tmp_path / "keep.gpx"
        result = cli(
            [
                "edit",
                str(sample_gpx_file),
                "-o",
                str(out_keep),
                "--min-lat",
                "0",
            ]
        )
        assert result == 0
        kept = read_gpx(out_keep)
        assert len(kept.wpt) == 1

        out_drop = tmp_path / "drop.gpx"
        result = cli(
            [
                "edit",
                str(sample_gpx_file),
                "-o",
                str(out_drop),
                "--min-lat",
                "53",
            ]
        )
        assert result == 0
        dropped = read_gpx(out_drop)
        assert len(dropped.wpt) == 0

    def test_edit_strip_all_metadata_preserves_nsmap(self, tmp_path: Path) -> None:
        """`gpx edit --strip-all-metadata` must keep custom namespace prefixes.

        The prefix must survive an actual file round-trip, which means an
        element using that namespace has to be present (ElementTree drops
        unused xmlns declarations).
        """
        src = tmp_path / "with_ext.gpx"
        src.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<gpx xmlns="http://www.topografix.com/GPX/1/1" '
            f'xmlns:gpxtpx="{GARMIN_TPX_NS}" '
            'version="1.1" creator="TestApp">\n'
            "  <metadata><name>x</name></metadata>\n"
            '  <wpt lat="52.5" lon="13.4">\n'
            "    <extensions>\n"
            "      <gpxtpx:TrackPointExtension>\n"
            "        <gpxtpx:hr>120</gpxtpx:hr>\n"
            "      </gpxtpx:TrackPointExtension>\n"
            "    </extensions>\n"
            "  </wpt>\n"
            "</gpx>\n",
            encoding="utf-8",
        )

        out = tmp_path / "stripped.gpx"
        result = cli(
            [
                "edit",
                str(src),
                "-o",
                str(out),
                "--strip-all-metadata",
            ]
        )
        assert result == 0
        # Original prefix must survive the round-trip through `gpx edit`.
        assert f'xmlns:gpxtpx="{GARMIN_TPX_NS}"' in out.read_text(encoding="utf-8")


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


class TestExtensionsInCLI:
    """Tests for extensions handling in CLI commands."""

    def test_validate_file_with_extensions(
        self, gpx_with_extensions_file: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test validating a GPX file with extensions."""
        result = cli(["validate", str(gpx_with_extensions_file)])
        assert result == 0
        captured = capsys.readouterr()
        assert "Valid GPX file" in captured.out

    def test_info_file_with_extensions(
        self, gpx_with_extensions_file: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test info command on file with extensions."""
        result = cli(["info", str(gpx_with_extensions_file)])
        assert result == 0
        captured = capsys.readouterr()
        assert "GPX File:" in captured.out
        assert "Tracks: 1" in captured.out

    def test_edit_preserves_gpx_extensions(
        self, gpx_with_extensions_file: Path, tmp_path: Path
    ) -> None:
        """Test that edit command preserves GPX-level extensions."""
        output_file = tmp_path / "output.gpx"
        result = cli(["edit", str(gpx_with_extensions_file), "-o", str(output_file)])
        assert result == 0

        gpx = read_gpx(output_file)
        assert gpx.extensions is not None
        assert gpx.extensions.get_text("source", namespace=CUSTOM_NS) == "TestApp"

    def test_edit_preserves_metadata_extensions(
        self, gpx_with_extensions_file: Path, tmp_path: Path
    ) -> None:
        """Test that edit command preserves metadata extensions."""
        output_file = tmp_path / "output.gpx"
        result = cli(["edit", str(gpx_with_extensions_file), "-o", str(output_file)])
        assert result == 0

        gpx = read_gpx(output_file)
        assert gpx.metadata is not None
        assert gpx.metadata.extensions is not None
        assert gpx.metadata.extensions.get_text("version", namespace=CUSTOM_NS) == "1.0"

    def test_edit_preserves_track_point_extensions(
        self, gpx_with_extensions_file: Path, tmp_path: Path
    ) -> None:
        """Test that edit command preserves track point extensions."""
        output_file = tmp_path / "output.gpx"
        result = cli(["edit", str(gpx_with_extensions_file), "-o", str(output_file)])
        assert result == 0

        gpx = read_gpx(output_file)
        point = gpx.trk[0].trkseg[0].trkpt[0]
        assert point.extensions is not None
        assert point.extensions.get_text("hr", namespace=GARMIN_TPX_NS) == "140"

    def test_edit_reverse_preserves_extensions(
        self, gpx_with_extensions_file: Path, tmp_path: Path
    ) -> None:
        """Test that reverse operation preserves all extensions."""
        output_file = tmp_path / "output.gpx"
        result = cli(
            [
                "edit",
                str(gpx_with_extensions_file),
                "-o",
                str(output_file),
                "--reverse-tracks",
            ]
        )
        assert result == 0

        gpx = read_gpx(output_file)

        # Track extensions preserved
        assert gpx.trk[0].extensions is not None
        assert (
            gpx.trk[0].extensions.get_text("activity", namespace=CUSTOM_NS) == "running"
        )

        # Segment extensions preserved
        assert gpx.trk[0].trkseg[0].extensions is not None
        assert (
            gpx.trk[0].trkseg[0].extensions.get_text("lap", namespace=CUSTOM_NS) == "1"
        )

        # Point extensions preserved (reversed order, so last point is now first)
        first_point = gpx.trk[0].trkseg[0].trkpt[0]
        assert first_point.extensions is not None
        # After reverse, first point should have hr=150 (was last)
        assert first_point.extensions.get_text("hr", namespace=GARMIN_TPX_NS) == "150"

    def test_edit_precision_preserves_extensions(
        self, gpx_with_extensions_file: Path, tmp_path: Path
    ) -> None:
        """Test that precision reduction preserves extensions."""
        output_file = tmp_path / "output.gpx"
        result = cli(
            [
                "edit",
                str(gpx_with_extensions_file),
                "-o",
                str(output_file),
                "--precision",
                "4",
            ]
        )
        assert result == 0

        gpx = read_gpx(output_file)
        point = gpx.trk[0].trkseg[0].trkpt[0]
        assert point.extensions is not None
        assert point.extensions.get_text("hr", namespace=GARMIN_TPX_NS) == "140"

    def test_edit_crop_preserves_extensions(
        self, gpx_with_extensions: GPX, tmp_path: Path
    ) -> None:
        """Test that crop operation preserves extensions on remaining points."""
        gpx_file = tmp_path / "input.gpx"
        output_file = tmp_path / "output.gpx"
        gpx_with_extensions.write_gpx(gpx_file)

        result = cli(
            [
                "edit",
                str(gpx_file),
                "-o",
                str(output_file),
                "--min-lat",
                "52.0",
                "--max-lat",
                "53.0",
                "--min-lon",
                "13.0",
                "--max-lon",
                "14.0",
            ]
        )
        assert result == 0

        gpx = read_gpx(output_file)

        # GPX extensions preserved
        assert gpx.extensions is not None

        # Track points that remain should have extensions
        if gpx.trk and gpx.trk[0].trkseg and gpx.trk[0].trkseg[0].trkpt:
            point = gpx.trk[0].trkseg[0].trkpt[0]
            assert point.extensions is not None

    def test_edit_trim_preserves_extensions(
        self, gpx_with_extensions: GPX, tmp_path: Path
    ) -> None:
        """Test that time trim preserves extensions on remaining points."""
        gpx_file = tmp_path / "input.gpx"
        output_file = tmp_path / "output.gpx"
        gpx_with_extensions.write_gpx(gpx_file)

        result = cli(
            [
                "edit",
                str(gpx_file),
                "-o",
                str(output_file),
                "--start",
                "2024-01-15T10:00:30",
                "--end",
                "2024-01-15T10:01:30",
            ]
        )
        assert result == 0

        gpx = read_gpx(output_file)

        # GPX extensions preserved
        assert gpx.extensions is not None

        # Track points that remain should have extensions
        if gpx.trk and gpx.trk[0].trkseg and gpx.trk[0].trkseg[0].trkpt:
            point = gpx.trk[0].trkseg[0].trkpt[0]
            assert point.extensions is not None

    def test_edit_strip_metadata_preserves_gpx_extensions(
        self, gpx_with_extensions_file: Path, tmp_path: Path
    ) -> None:
        """Test that stripping metadata preserves GPX-level extensions."""
        output_file = tmp_path / "output.gpx"
        result = cli(
            [
                "edit",
                str(gpx_with_extensions_file),
                "-o",
                str(output_file),
                "--strip-all-metadata",
            ]
        )
        assert result == 0

        gpx = read_gpx(output_file)

        # Metadata is stripped
        assert gpx.metadata is None

        # But GPX-level extensions are preserved
        assert gpx.extensions is not None
        assert gpx.extensions.get_text("source", namespace=CUSTOM_NS) == "TestApp"

    def test_merge_preserves_extensions(
        self, gpx_with_extensions: GPX, tmp_path: Path
    ) -> None:
        """Test that merge command preserves extensions from all files."""
        file1 = tmp_path / "file1.gpx"
        file2 = tmp_path / "file2.gpx"
        output_file = tmp_path / "output.gpx"

        # Create two files with extensions
        gpx_with_extensions.write_gpx(file1)

        # Create second file with different extension values
        gpx2 = GPX(
            creator="TestApp2",
            trk=[
                Track(
                    name="Afternoon Run",
                    extensions=create_custom_extension("activity", "cycling"),
                    trkseg=[
                        TrackSegment(
                            trkpt=[
                                Waypoint(
                                    lat=Latitude("52.6000"),
                                    lon=Longitude("13.5000"),
                                    extensions=create_track_point_extension(
                                        "160", "95"
                                    ),
                                ),
                            ]
                        )
                    ],
                )
            ],
        )
        gpx2.write_gpx(file2)

        result = cli(["merge", str(file1), str(file2), "-o", str(output_file)])
        assert result == 0

        merged = read_gpx(output_file)

        # Should have 2 tracks
        assert len(merged.trk) == 2

        # First track should have original extensions
        assert merged.trk[0].extensions is not None
        assert (
            merged.trk[0].extensions.get_text("activity", namespace=CUSTOM_NS)
            == "running"
        )

        # Second track should have its extensions
        assert merged.trk[1].extensions is not None
        assert (
            merged.trk[1].extensions.get_text("activity", namespace=CUSTOM_NS)
            == "cycling"
        )

        # Track points should have extensions
        assert merged.trk[0].trkseg[0].trkpt[0].extensions is not None
        assert merged.trk[1].trkseg[0].trkpt[0].extensions is not None

    def test_convert_gpx_to_gpx_preserves_extensions(
        self, gpx_with_extensions_file: Path, tmp_path: Path
    ) -> None:
        """Test that GPX to GPX conversion preserves extensions."""
        output_file = tmp_path / "output.gpx"
        result = cli(["convert", str(gpx_with_extensions_file), "-o", str(output_file)])
        assert result == 0

        gpx = read_gpx(output_file)

        # GPX extensions preserved
        assert gpx.extensions is not None
        assert gpx.extensions.get_text("source", namespace=CUSTOM_NS) == "TestApp"

        # Track point extensions preserved
        assert gpx.trk[0].trkseg[0].trkpt[0].extensions is not None
