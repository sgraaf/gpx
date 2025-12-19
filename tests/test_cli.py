"""Tests for the CLI module."""

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from click.testing import CliRunner

from gpx import GPX, Metadata, Route, Track, TrackSegment, Waypoint, read_gpx
from gpx.cli import main
from gpx.types import Latitude, Longitude


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def valid_fixtures_dir(fixtures_dir: Path) -> Path:
    return fixtures_dir / "valid"


@pytest.fixture
def invalid_fixtures_dir(fixtures_dir: Path) -> Path:
    return fixtures_dir / "invalid"


class TestValidateCommand:
    def test_validate_valid_file(
        self, runner: CliRunner, valid_fixtures_dir: Path
    ) -> None:
        result = runner.invoke(main, ["validate", str(valid_fixtures_dir / "full.gpx")])
        assert result.exit_code == 0
        assert "Valid:" in result.output

    def test_validate_invalid_file(
        self, runner: CliRunner, invalid_fixtures_dir: Path
    ) -> None:
        result = runner.invoke(
            main, ["validate", str(invalid_fixtures_dir / "malformed_xml.gpx")]
        )
        assert result.exit_code == 1
        assert "Invalid:" in result.output

    def test_validate_nonexistent_file(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["validate", "nonexistent.gpx"])
        assert result.exit_code != 0


class TestInfoCommand:
    def test_info_basic(
        self, runner: CliRunner, valid_fixtures_dir: Path
    ) -> None:
        result = runner.invoke(main, ["info", str(valid_fixtures_dir / "full.gpx")])
        assert result.exit_code == 0
        assert "File:" in result.output
        assert "Creator:" in result.output
        assert "Summary:" in result.output
        assert "Waypoints:" in result.output
        assert "Routes:" in result.output
        assert "Tracks:" in result.output

    def test_info_with_metadata(
        self, runner: CliRunner, valid_fixtures_dir: Path
    ) -> None:
        result = runner.invoke(main, ["info", str(valid_fixtures_dir / "metadata.gpx")])
        assert result.exit_code == 0
        assert "Metadata:" in result.output
        assert "Name:" in result.output
        assert "Description:" in result.output
        assert "Author:" in result.output

    def test_info_with_track_stats(
        self, runner: CliRunner, valid_fixtures_dir: Path
    ) -> None:
        result = runner.invoke(
            main, ["info", str(valid_fixtures_dir / "track_with_stats.gpx")]
        )
        assert result.exit_code == 0
        assert "Tracks:" in result.output
        assert "Distance:" in result.output

    def test_info_verbose(
        self, runner: CliRunner, valid_fixtures_dir: Path
    ) -> None:
        result = runner.invoke(
            main, ["info", "-v", str(valid_fixtures_dir / "full.gpx")]
        )
        assert result.exit_code == 0
        assert "Bounds:" in result.output


class TestCropCommand:
    def test_crop_basic(self, runner: CliRunner, valid_fixtures_dir: Path) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "crop",
                    str(valid_fixtures_dir / "track_with_stats.gpx"),
                    "output.gpx",
                    "--min-lat", "52.5",
                    "--min-lon", "13.4",
                    "--max-lat", "52.55",
                    "--max-lon", "13.45",
                ],
            )
            assert result.exit_code == 0
            assert "Cropped GPX written to" in result.output
            assert Path("output.gpx").exists()

            # Verify the cropped file
            gpx = read_gpx("output.gpx")
            for trk in gpx.trk:
                for seg in trk.trkseg:
                    for pt in seg.trkpt:
                        assert 52.5 <= float(pt.lat) <= 52.55
                        assert 13.4 <= float(pt.lon) <= 13.45

    def test_crop_filters_out_of_bounds(
        self, runner: CliRunner, valid_fixtures_dir: Path
    ) -> None:
        with runner.isolated_filesystem():
            # Use a bounding box that excludes all points
            result = runner.invoke(
                main,
                [
                    "crop",
                    str(valid_fixtures_dir / "track_with_stats.gpx"),
                    "output.gpx",
                    "--min-lat", "0.0",
                    "--min-lon", "0.0",
                    "--max-lat", "1.0",
                    "--max-lon", "1.0",
                ],
            )
            assert result.exit_code == 0
            gpx = read_gpx("output.gpx")
            assert len(gpx.trk) == 0


class TestTrimCommand:
    def test_trim_basic(self, runner: CliRunner, valid_fixtures_dir: Path) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "trim",
                    str(valid_fixtures_dir / "track_with_stats.gpx"),
                    "output.gpx",
                    "--start", "2024-01-01T10:00:00",
                    "--end", "2024-01-01T10:10:00",
                ],
            )
            assert result.exit_code == 0
            assert "Trimmed GPX written to" in result.output
            assert Path("output.gpx").exists()

    def test_trim_requires_at_least_one_option(
        self, runner: CliRunner, valid_fixtures_dir: Path
    ) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "trim",
                    str(valid_fixtures_dir / "track_with_stats.gpx"),
                    "output.gpx",
                ],
            )
            assert result.exit_code != 0
            assert "At least one of --start or --end must be specified" in result.output


class TestMergeCommand:
    def test_merge_basic(self, runner: CliRunner, valid_fixtures_dir: Path) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "merge",
                    str(valid_fixtures_dir / "waypoint.gpx"),
                    str(valid_fixtures_dir / "track.gpx"),
                    "output.gpx",
                ],
            )
            assert result.exit_code == 0
            assert "Merged 2 files" in result.output
            assert Path("output.gpx").exists()

    def test_merge_requires_at_least_two_files(
        self, runner: CliRunner, valid_fixtures_dir: Path
    ) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "merge",
                    str(valid_fixtures_dir / "waypoint.gpx"),
                    "output.gpx",
                ],
            )
            assert result.exit_code != 0
            assert "At least 2 files are required" in result.output

    def test_merge_combines_content(
        self, runner: CliRunner, valid_fixtures_dir: Path
    ) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "merge",
                    str(valid_fixtures_dir / "waypoint.gpx"),
                    str(valid_fixtures_dir / "route.gpx"),
                    str(valid_fixtures_dir / "track.gpx"),
                    "output.gpx",
                ],
            )
            assert result.exit_code == 0
            gpx = read_gpx("output.gpx")
            # Should have content from all files
            assert len(gpx.wpt) > 0 or len(gpx.rte) > 0 or len(gpx.trk) > 0


class TestReverseCommand:
    def test_reverse_basic(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            # Create a simple GPX file with a track
            gpx = GPX(
                trk=[
                    Track(
                        trkseg=[
                            TrackSegment(
                                trkpt=[
                                    Waypoint(Latitude("52.0"), Longitude("13.0")),
                                    Waypoint(Latitude("52.1"), Longitude("13.1")),
                                    Waypoint(Latitude("52.2"), Longitude("13.2")),
                                ]
                            )
                        ]
                    )
                ]
            )
            gpx.write_gpx("input.gpx")

            result = runner.invoke(main, ["reverse", "input.gpx", "output.gpx"])
            assert result.exit_code == 0
            assert "Reversed GPX written to" in result.output

            # Verify order is reversed
            output_gpx = read_gpx("output.gpx")
            points = output_gpx.trk[0].trkseg[0].trkpt
            assert float(points[0].lat) == pytest.approx(52.2, abs=0.01)
            assert float(points[-1].lat) == pytest.approx(52.0, abs=0.01)

    def test_reverse_routes_only(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            gpx = GPX(
                rte=[
                    Route(
                        rtept=[
                            Waypoint(Latitude("52.0"), Longitude("13.0")),
                            Waypoint(Latitude("52.1"), Longitude("13.1")),
                        ]
                    )
                ],
                trk=[
                    Track(
                        trkseg=[
                            TrackSegment(
                                trkpt=[
                                    Waypoint(Latitude("52.0"), Longitude("13.0")),
                                    Waypoint(Latitude("52.2"), Longitude("13.2")),
                                ]
                            )
                        ]
                    )
                ],
            )
            gpx.write_gpx("input.gpx")

            result = runner.invoke(
                main, ["reverse", "input.gpx", "output.gpx", "--no-tracks"]
            )
            assert result.exit_code == 0

            output_gpx = read_gpx("output.gpx")
            # Route should be reversed
            assert float(output_gpx.rte[0].rtept[0].lat) == pytest.approx(52.1, abs=0.01)
            # Track should NOT be reversed
            assert float(output_gpx.trk[0].trkseg[0].trkpt[0].lat) == pytest.approx(
                52.0, abs=0.01
            )


class TestConvertCommand:
    def test_convert_gpx_to_geojson(
        self, runner: CliRunner, valid_fixtures_dir: Path
    ) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "convert",
                    str(valid_fixtures_dir / "full.gpx"),
                    "output.geojson",
                ],
            )
            assert result.exit_code == 0
            assert "Converted" in result.output
            assert Path("output.geojson").exists()

    def test_convert_gpx_to_kml(
        self, runner: CliRunner, valid_fixtures_dir: Path
    ) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "convert",
                    str(valid_fixtures_dir / "full.gpx"),
                    "output.kml",
                ],
            )
            assert result.exit_code == 0
            assert "Converted" in result.output
            assert Path("output.kml").exists()

    def test_convert_with_explicit_format(
        self, runner: CliRunner, valid_fixtures_dir: Path
    ) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "convert",
                    str(valid_fixtures_dir / "full.gpx"),
                    "output.json",
                    "-o", "geojson",
                ],
            )
            assert result.exit_code == 0
            assert Path("output.json").exists()


class TestStripMetadataCommand:
    def test_strip_metadata_basic(
        self, runner: CliRunner, valid_fixtures_dir: Path
    ) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "strip-metadata",
                    str(valid_fixtures_dir / "metadata.gpx"),
                    "output.gpx",
                ],
            )
            assert result.exit_code == 0
            assert "Stripped metadata written to" in result.output

            gpx = read_gpx("output.gpx")
            # By default, name, desc, author, copyright are stripped
            assert gpx.metadata is None or gpx.metadata.name is None
            assert gpx.metadata is None or gpx.metadata.desc is None
            assert gpx.metadata is None or gpx.metadata.author is None
            assert gpx.metadata is None or gpx.metadata.copyright is None

    def test_strip_metadata_keep_name(
        self, runner: CliRunner, valid_fixtures_dir: Path
    ) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "strip-metadata",
                    str(valid_fixtures_dir / "metadata.gpx"),
                    "output.gpx",
                    "--keep-name",
                ],
            )
            assert result.exit_code == 0

            gpx = read_gpx("output.gpx")
            assert gpx.metadata is not None
            assert gpx.metadata.name == "Test GPX File"

    def test_strip_metadata_all(
        self, runner: CliRunner, valid_fixtures_dir: Path
    ) -> None:
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "strip-metadata",
                    str(valid_fixtures_dir / "metadata.gpx"),
                    "output.gpx",
                    "--all",
                ],
            )
            assert result.exit_code == 0

            gpx = read_gpx("output.gpx")
            # All metadata should be stripped except bounds
            if gpx.metadata:
                assert gpx.metadata.name is None
                assert gpx.metadata.desc is None
                assert gpx.metadata.author is None
                assert gpx.metadata.copyright is None
                assert gpx.metadata.time is None
                assert gpx.metadata.keywords is None
                assert len(gpx.metadata.link) == 0


class TestReducePrecisionCommand:
    def test_reduce_precision_basic(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            # Create a GPX with high-precision coordinates
            gpx = GPX(
                wpt=[
                    Waypoint(
                        Latitude("52.1234567890"),
                        Longitude("13.9876543210"),
                        ele=Decimal("123.456789"),
                    )
                ]
            )
            gpx.write_gpx("input.gpx")

            result = runner.invoke(
                main,
                ["reduce-precision", "input.gpx", "output.gpx", "-p", "3"],
            )
            assert result.exit_code == 0
            assert "Reduced precision GPX written to" in result.output
            assert "Coordinate precision: 3 decimal places" in result.output

            output_gpx = read_gpx("output.gpx")
            lat_str = str(output_gpx.wpt[0].lat)
            lon_str = str(output_gpx.wpt[0].lon)
            # Check that precision is reduced (3 decimal places)
            assert len(lat_str.split(".")[-1]) <= 3
            assert len(lon_str.split(".")[-1]) <= 3

    def test_reduce_precision_default(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            gpx = GPX(
                wpt=[
                    Waypoint(
                        Latitude("52.1234567890"),
                        Longitude("13.9876543210"),
                    )
                ]
            )
            gpx.write_gpx("input.gpx")

            result = runner.invoke(
                main,
                ["reduce-precision", "input.gpx", "output.gpx"],
            )
            assert result.exit_code == 0
            # Default is 3 decimal places
            assert "Coordinate precision: 3 decimal places" in result.output

    def test_reduce_precision_elevation(self, runner: CliRunner) -> None:
        with runner.isolated_filesystem():
            gpx = GPX(
                wpt=[
                    Waypoint(
                        Latitude("52.123"),
                        Longitude("13.987"),
                        ele=Decimal("123.456789"),
                    )
                ]
            )
            gpx.write_gpx("input.gpx")

            result = runner.invoke(
                main,
                ["reduce-precision", "input.gpx", "output.gpx", "-e", "1"],
            )
            assert result.exit_code == 0
            assert "Elevation precision: 1 decimal places" in result.output

            output_gpx = read_gpx("output.gpx")
            ele_str = str(output_gpx.wpt[0].ele)
            assert len(ele_str.split(".")[-1]) <= 1


class TestVersionOption:
    def test_version(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0


class TestHelpOption:
    def test_help(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "GPX file manipulation tool" in result.output

    def test_command_help(self, runner: CliRunner) -> None:
        for cmd in [
            "validate",
            "info",
            "crop",
            "trim",
            "merge",
            "reverse",
            "convert",
            "strip-metadata",
            "reduce-precision",
        ]:
            result = runner.invoke(main, [cmd, "--help"])
            assert result.exit_code == 0
