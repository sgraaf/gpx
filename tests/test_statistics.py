"""Tests for statistics and calculation properties."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from gpx import GPX

FIXTURES_DIR = Path(__file__).parent / "fixtures"
VALID_FIXTURES_DIR = FIXTURES_DIR / "valid"


def load_fixture(fixture_path: Path) -> str:
    """Load a GPX fixture file."""
    return fixture_path.read_text(encoding="utf-8")


class TestTrackStatistics:
    """Tests for Track statistics properties."""

    @pytest.fixture
    def track_gpx(self) -> GPX:
        """Load track with statistics data."""
        gpx_string = load_fixture(VALID_FIXTURES_DIR / "track_with_stats.gpx")
        return GPX.from_string(gpx_string)

    @pytest.fixture
    def multi_segment_gpx(self) -> GPX:
        """Load track with multiple segments."""
        gpx_string = load_fixture(VALID_FIXTURES_DIR / "track_multi_segment.gpx")
        return GPX.from_string(gpx_string)

    def test_track_total_distance(self, track_gpx: GPX) -> None:
        """Test track total distance calculation."""
        track = track_gpx.trk[0]
        distance = track.total_distance
        assert distance > 0
        assert isinstance(distance, float)

    def test_track_total_duration(self, track_gpx: GPX) -> None:
        """Test track total duration calculation."""
        track = track_gpx.trk[0]
        duration = track.total_duration
        # 15 minutes total
        assert duration == timedelta(minutes=15)

    def test_track_moving_duration(self, track_gpx: GPX) -> None:
        """Test track moving duration calculation."""
        track = track_gpx.trk[0]
        duration = track.moving_duration
        assert isinstance(duration, timedelta)
        # Should be greater than 0 since we have movement
        assert duration > timedelta()

    def test_track_avg_speed(self, track_gpx: GPX) -> None:
        """Test track average speed calculation."""
        track = track_gpx.trk[0]
        avg_speed = track.avg_speed
        assert avg_speed > 0
        assert isinstance(avg_speed, float)

    def test_track_avg_moving_speed(self, track_gpx: GPX) -> None:
        """Test track average moving speed calculation."""
        track = track_gpx.trk[0]
        avg_moving_speed = track.avg_moving_speed
        assert avg_moving_speed > 0
        assert isinstance(avg_moving_speed, float)

    def test_track_max_speed(self, track_gpx: GPX) -> None:
        """Test track maximum speed calculation."""
        track = track_gpx.trk[0]
        max_speed = track.max_speed
        assert max_speed >= 0
        assert isinstance(max_speed, float)

    def test_track_min_speed(self, track_gpx: GPX) -> None:
        """Test track minimum speed calculation."""
        track = track_gpx.trk[0]
        min_speed = track.min_speed
        assert min_speed >= 0
        assert isinstance(min_speed, float)

    def test_track_speed_profile(self, track_gpx: GPX) -> None:
        """Test track speed profile generation."""
        track = track_gpx.trk[0]
        profile = track.speed_profile
        assert isinstance(profile, list)
        # 4 points -> 3 speed entries
        assert len(profile) == 3
        for timestamp, speed in profile:
            assert timestamp is not None
            assert isinstance(speed, float)

    def test_track_avg_elevation(self, track_gpx: GPX) -> None:
        """Test track average elevation calculation."""
        track = track_gpx.trk[0]
        avg_ele = track.avg_elevation
        assert isinstance(avg_ele, Decimal)
        # (34 + 36 + 38 + 35) / 4 = 35.75
        assert avg_ele == Decimal("35.75")

    def test_track_max_elevation(self, track_gpx: GPX) -> None:
        """Test track maximum elevation calculation."""
        track = track_gpx.trk[0]
        max_ele = track.max_elevation
        assert max_ele == Decimal("38")

    def test_track_min_elevation(self, track_gpx: GPX) -> None:
        """Test track minimum elevation calculation."""
        track = track_gpx.trk[0]
        min_ele = track.min_elevation
        assert min_ele == Decimal("34")

    def test_track_diff_elevation(self, track_gpx: GPX) -> None:
        """Test track elevation difference calculation."""
        track = track_gpx.trk[0]
        diff_ele = track.diff_elevation
        # max (38) - min (34) = 4
        assert diff_ele == Decimal("4")

    def test_track_total_ascent(self, track_gpx: GPX) -> None:
        """Test track total ascent calculation."""
        track = track_gpx.trk[0]
        ascent = track.total_ascent
        assert isinstance(ascent, Decimal)
        # 34->36 (+2), 36->38 (+2), 38->35 (-3) = total ascent 4
        assert ascent == Decimal("4")

    def test_track_total_descent(self, track_gpx: GPX) -> None:
        """Test track total descent calculation."""
        track = track_gpx.trk[0]
        descent = track.total_descent
        assert isinstance(descent, Decimal)
        # 34->36 (+2), 36->38 (+2), 38->35 (-3) = total descent 3
        assert descent == Decimal("3")

    def test_track_elevation_profile(self, track_gpx: GPX) -> None:
        """Test track elevation profile generation."""
        track = track_gpx.trk[0]
        profile = track.elevation_profile
        assert isinstance(profile, list)
        assert len(profile) == 4  # 4 points with elevation
        # First point at distance 0
        assert profile[0][0] == 0.0
        assert profile[0][1] == Decimal("34")
        # Subsequent points have increasing distance
        for i in range(1, len(profile)):
            assert profile[i][0] > profile[i - 1][0]

    def test_track_bounds(self, track_gpx: GPX) -> None:
        """Test track bounds calculation."""
        track = track_gpx.trk[0]
        bounds = track.bounds
        assert len(bounds) == 4
        minlat, minlon, maxlat, maxlon = bounds
        assert minlat == Decimal("52.5200")
        assert minlon == Decimal("13.4050")
        assert maxlat == Decimal("52.5230")
        assert maxlon == Decimal("13.4080")

    def test_track_geo_interface(self, track_gpx: GPX) -> None:
        """Test track GeoJSON interface."""
        track = track_gpx.trk[0]
        geo = track.__geo_interface__
        assert geo["type"] == "Feature"
        assert geo["geometry"]["type"] == "MultiLineString"
        assert "bbox" in geo["geometry"]
        # With elevation data, bbox should have 6 elements
        assert len(geo["geometry"]["bbox"]) == 6

    def test_multi_segment_track_statistics(self, multi_segment_gpx: GPX) -> None:
        """Test statistics across multiple track segments."""
        track = multi_segment_gpx.trk[0]

        # Distance should sum across segments
        assert track.total_distance > 0

        # Duration should sum across segments
        duration = track.total_duration
        assert duration > timedelta()

        # Speed profile should combine segments
        profile = track.speed_profile
        assert len(profile) == 2  # 2 points per segment, 1 speed each

        # Elevation stats across segments
        assert track.max_elevation == Decimal("50")
        assert track.min_elevation == Decimal("34")


class TestTrackSegmentStatistics:
    """Tests for TrackSegment statistics properties."""

    @pytest.fixture
    def segment(self) -> GPX:
        """Load track with statistics data and return first segment."""
        gpx_string = load_fixture(VALID_FIXTURES_DIR / "track_with_stats.gpx")
        gpx = GPX.from_string(gpx_string)
        return gpx.trk[0].trkseg[0]

    def test_segment_total_distance(self, segment) -> None:
        """Test segment total distance calculation."""
        distance = segment.total_distance
        assert distance > 0
        assert isinstance(distance, float)

    def test_segment_total_duration(self, segment) -> None:
        """Test segment total duration calculation."""
        duration = segment.total_duration
        assert duration == timedelta(minutes=15)

    def test_segment_moving_duration(self, segment) -> None:
        """Test segment moving duration calculation."""
        duration = segment.moving_duration
        assert isinstance(duration, timedelta)
        assert duration > timedelta()

    def test_segment_avg_speed(self, segment) -> None:
        """Test segment average speed calculation."""
        avg_speed = segment.avg_speed
        assert avg_speed > 0
        assert isinstance(avg_speed, float)

    def test_segment_avg_moving_speed(self, segment) -> None:
        """Test segment average moving speed calculation."""
        avg_moving_speed = segment.avg_moving_speed
        assert avg_moving_speed > 0
        assert isinstance(avg_moving_speed, float)

    def test_segment_max_speed(self, segment) -> None:
        """Test segment maximum speed calculation."""
        max_speed = segment.max_speed
        assert max_speed >= 0
        assert isinstance(max_speed, float)

    def test_segment_min_speed(self, segment) -> None:
        """Test segment minimum speed calculation."""
        min_speed = segment.min_speed
        assert min_speed >= 0
        assert isinstance(min_speed, float)

    def test_segment_speed_profile(self, segment) -> None:
        """Test segment speed profile generation."""
        profile = segment.speed_profile
        assert isinstance(profile, list)
        assert len(profile) == 3  # 4 points -> 3 speeds

    def test_segment_avg_elevation(self, segment) -> None:
        """Test segment average elevation calculation."""
        avg_ele = segment.avg_elevation
        assert avg_ele == Decimal("35.75")

    def test_segment_max_elevation(self, segment) -> None:
        """Test segment maximum elevation calculation."""
        assert segment.max_elevation == Decimal("38")

    def test_segment_min_elevation(self, segment) -> None:
        """Test segment minimum elevation calculation."""
        assert segment.min_elevation == Decimal("34")

    def test_segment_diff_elevation(self, segment) -> None:
        """Test segment elevation difference calculation."""
        assert segment.diff_elevation == Decimal("4")

    def test_segment_total_ascent(self, segment) -> None:
        """Test segment total ascent calculation."""
        assert segment.total_ascent == Decimal("4")

    def test_segment_total_descent(self, segment) -> None:
        """Test segment total descent calculation."""
        assert segment.total_descent == Decimal("3")

    def test_segment_elevation_profile(self, segment) -> None:
        """Test segment elevation profile generation."""
        profile = segment.elevation_profile
        assert isinstance(profile, list)
        assert len(profile) == 4
        assert profile[0][0] == 0.0
        assert profile[0][1] == Decimal("34")

    def test_segment_bounds(self, segment) -> None:
        """Test segment bounds calculation."""
        bounds = segment.bounds
        assert len(bounds) == 4

    def test_segment_geo_interface(self, segment) -> None:
        """Test segment GeoJSON interface."""
        geo = segment.__geo_interface__
        # TrackSegment only has trkpt field which is excluded,
        # so it returns pure geometry, not a Feature
        assert geo["type"] == "LineString"
        assert "coordinates" in geo
        assert "bbox" in geo


class TestRouteStatistics:
    """Tests for Route statistics properties."""

    @pytest.fixture
    def route_gpx(self) -> GPX:
        """Load route with statistics data."""
        gpx_string = load_fixture(VALID_FIXTURES_DIR / "route_with_stats.gpx")
        return GPX.from_string(gpx_string)

    def test_route_total_distance(self, route_gpx: GPX) -> None:
        """Test route total distance calculation."""
        route = route_gpx.rte[0]
        distance = route.total_distance
        assert distance > 0
        assert isinstance(distance, float)

    def test_route_total_duration(self, route_gpx: GPX) -> None:
        """Test route total duration calculation."""
        route = route_gpx.rte[0]
        duration = route.total_duration
        assert duration == timedelta(minutes=15)

    def test_route_total_duration_single_point(self) -> None:
        """Test route duration with single point returns zero."""
        gpx_string = """<?xml version="1.0" encoding="UTF-8"?>
        <gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1" creator="Test">
          <rte>
            <rtept lat="52.5200" lon="13.4050">
              <time>2024-01-01T10:00:00Z</time>
            </rtept>
          </rte>
        </gpx>"""
        gpx = GPX.from_string(gpx_string)
        route = gpx.rte[0]
        assert route.total_duration == timedelta()

    def test_route_moving_duration(self, route_gpx: GPX) -> None:
        """Test route moving duration calculation."""
        route = route_gpx.rte[0]
        duration = route.moving_duration
        assert isinstance(duration, timedelta)
        assert duration > timedelta()

    def test_route_avg_speed(self, route_gpx: GPX) -> None:
        """Test route average speed calculation."""
        route = route_gpx.rte[0]
        avg_speed = route.avg_speed
        assert avg_speed > 0
        assert isinstance(avg_speed, float)

    def test_route_avg_moving_speed(self, route_gpx: GPX) -> None:
        """Test route average moving speed calculation."""
        route = route_gpx.rte[0]
        avg_moving_speed = route.avg_moving_speed
        assert avg_moving_speed > 0
        assert isinstance(avg_moving_speed, float)

    def test_route_max_speed(self, route_gpx: GPX) -> None:
        """Test route maximum speed calculation."""
        route = route_gpx.rte[0]
        max_speed = route.max_speed
        assert max_speed >= 0
        assert isinstance(max_speed, float)

    def test_route_min_speed(self, route_gpx: GPX) -> None:
        """Test route minimum speed calculation."""
        route = route_gpx.rte[0]
        min_speed = route.min_speed
        assert min_speed >= 0
        assert isinstance(min_speed, float)

    def test_route_speed_profile(self, route_gpx: GPX) -> None:
        """Test route speed profile generation."""
        route = route_gpx.rte[0]
        profile = route.speed_profile
        assert isinstance(profile, list)
        assert len(profile) == 3  # 4 points -> 3 speeds

    def test_route_avg_elevation(self, route_gpx: GPX) -> None:
        """Test route average elevation calculation."""
        route = route_gpx.rte[0]
        avg_ele = route.avg_elevation
        assert avg_ele == Decimal("35.75")

    def test_route_max_elevation(self, route_gpx: GPX) -> None:
        """Test route maximum elevation calculation."""
        route = route_gpx.rte[0]
        assert route.max_elevation == Decimal("38")

    def test_route_min_elevation(self, route_gpx: GPX) -> None:
        """Test route minimum elevation calculation."""
        route = route_gpx.rte[0]
        assert route.min_elevation == Decimal("34")

    def test_route_diff_elevation(self, route_gpx: GPX) -> None:
        """Test route elevation difference calculation."""
        route = route_gpx.rte[0]
        assert route.diff_elevation == Decimal("4")

    def test_route_total_ascent(self, route_gpx: GPX) -> None:
        """Test route total ascent calculation."""
        route = route_gpx.rte[0]
        assert route.total_ascent == Decimal("4")

    def test_route_total_descent(self, route_gpx: GPX) -> None:
        """Test route total descent calculation."""
        route = route_gpx.rte[0]
        assert route.total_descent == Decimal("3")

    def test_route_elevation_profile(self, route_gpx: GPX) -> None:
        """Test route elevation profile generation."""
        route = route_gpx.rte[0]
        profile = route.elevation_profile
        assert isinstance(profile, list)
        assert len(profile) == 4
        assert profile[0][0] == 0.0
        assert profile[0][1] == Decimal("34")

    def test_route_bounds(self, route_gpx: GPX) -> None:
        """Test route bounds calculation."""
        route = route_gpx.rte[0]
        bounds = route.bounds
        assert len(bounds) == 4

    def test_route_geo_interface(self, route_gpx: GPX) -> None:
        """Test route GeoJSON interface."""
        route = route_gpx.rte[0]
        geo = route.__geo_interface__
        assert geo["type"] == "Feature"
        assert geo["geometry"]["type"] == "LineString"
        assert "bbox" in geo["geometry"]


class TestBoundsProperties:
    """Tests for Bounds utility methods."""

    @pytest.fixture
    def bounds_gpx(self) -> GPX:
        """Load GPX with bounds."""
        gpx_string = load_fixture(VALID_FIXTURES_DIR / "metadata_with_bounds.gpx")
        return GPX.from_string(gpx_string)

    def test_bounds_geo_interface(self, bounds_gpx: GPX) -> None:
        """Test bounds GeoJSON interface returns Polygon."""
        bounds = bounds_gpx.metadata.bounds
        geo = bounds.__geo_interface__
        assert geo["type"] == "Polygon"
        assert "coordinates" in geo
        # Should be a closed ring (5 points)
        coords = geo["coordinates"][0]
        assert len(coords) == 5
        # First and last point should be same (closed ring)
        assert coords[0] == coords[4]
        # Check coordinate order [lon, lat]
        assert coords[0] == [float(bounds.minlon), float(bounds.minlat)]

    def test_bounds_as_tuple(self, bounds_gpx: GPX) -> None:
        """Test bounds as_tuple method."""
        bounds = bounds_gpx.metadata.bounds
        t = bounds.as_tuple()
        assert len(t) == 4
        assert t == (bounds.minlat, bounds.minlon, bounds.maxlat, bounds.maxlon)

    def test_bounds_getitem(self, bounds_gpx: GPX) -> None:
        """Test bounds index access."""
        bounds = bounds_gpx.metadata.bounds
        assert bounds[0] == bounds.minlat
        assert bounds[1] == bounds.minlon
        assert bounds[2] == bounds.maxlat
        assert bounds[3] == bounds.maxlon

    def test_bounds_iter(self, bounds_gpx: GPX) -> None:
        """Test bounds iteration."""
        bounds = bounds_gpx.metadata.bounds
        values = list(bounds)
        assert values == [bounds.minlat, bounds.minlon, bounds.maxlat, bounds.maxlon]

    def test_bounds_len(self, bounds_gpx: GPX) -> None:
        """Test bounds length."""
        bounds = bounds_gpx.metadata.bounds
        assert len(bounds) == 4


class TestEdgeCaseStatistics:
    """Tests for edge cases in statistics calculations."""

    def test_track_no_duration_avg_speed_zero(self) -> None:
        """Test average speed is zero when duration is zero."""
        gpx_string = """<?xml version="1.0" encoding="UTF-8"?>
        <gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1" creator="Test">
          <trk>
            <trkseg>
              <trkpt lat="52.5200" lon="13.4050">
                <time>2024-01-01T10:00:00Z</time>
              </trkpt>
              <trkpt lat="52.5200" lon="13.4050">
                <time>2024-01-01T10:00:00Z</time>
              </trkpt>
            </trkseg>
          </trk>
        </gpx>"""
        gpx = GPX.from_string(gpx_string)
        track = gpx.trk[0]
        # Duration is 0, so avg_speed should be 0
        assert track.avg_speed == 0.0

    def test_track_no_movement_avg_moving_speed_zero(self) -> None:
        """Test average moving speed is zero when no movement detected."""
        gpx_string = """<?xml version="1.0" encoding="UTF-8"?>
        <gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1" creator="Test">
          <trk>
            <trkseg>
              <trkpt lat="52.5200" lon="13.4050">
                <time>2024-01-01T10:00:00Z</time>
              </trkpt>
              <trkpt lat="52.5200" lon="13.4050">
                <time>2024-01-01T10:00:01Z</time>
              </trkpt>
            </trkseg>
          </trk>
        </gpx>"""
        gpx = GPX.from_string(gpx_string)
        track = gpx.trk[0]
        # Same location, so moving_duration should be 0 (speed < 0.5 km/h)
        # and avg_moving_speed should be 0
        assert track.avg_moving_speed == 0.0

    def test_segment_single_point_duration(self) -> None:
        """Test segment with single point has zero duration."""
        gpx_string = """<?xml version="1.0" encoding="UTF-8"?>
        <gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1" creator="Test">
          <trk>
            <trkseg>
              <trkpt lat="52.5200" lon="13.4050">
                <time>2024-01-01T10:00:00Z</time>
              </trkpt>
            </trkseg>
          </trk>
        </gpx>"""
        gpx = GPX.from_string(gpx_string)
        segment = gpx.trk[0].trkseg[0]
        assert segment.total_duration == timedelta()

    def test_route_no_movement_avg_moving_speed_zero(self) -> None:
        """Test route average moving speed is zero when no movement."""
        gpx_string = """<?xml version="1.0" encoding="UTF-8"?>
        <gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1" creator="Test">
          <rte>
            <rtept lat="52.5200" lon="13.4050">
              <time>2024-01-01T10:00:00Z</time>
            </rtept>
            <rtept lat="52.5200" lon="13.4050">
              <time>2024-01-01T10:00:01Z</time>
            </rtept>
          </rte>
        </gpx>"""
        gpx = GPX.from_string(gpx_string)
        route = gpx.rte[0]
        assert route.avg_moving_speed == 0.0

    def test_geo_interface_without_elevation(self) -> None:
        """Test GeoJSON interface without elevation data uses 4-element bbox."""
        gpx_string = """<?xml version="1.0" encoding="UTF-8"?>
        <gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1" creator="Test">
          <trk>
            <trkseg>
              <trkpt lat="52.5200" lon="13.4050"/>
              <trkpt lat="52.5210" lon="13.4060"/>
            </trkseg>
          </trk>
        </gpx>"""
        gpx = GPX.from_string(gpx_string)
        track = gpx.trk[0]
        geo = track.__geo_interface__
        # Without properties, returns pure geometry (no "geometry" key)
        # Without elevation, bbox should have 4 elements
        assert geo["type"] == "MultiLineString"
        assert len(geo["bbox"]) == 4

    def test_route_geo_interface_without_elevation(self) -> None:
        """Test route GeoJSON interface without elevation uses 4-element bbox."""
        gpx_string = """<?xml version="1.0" encoding="UTF-8"?>
        <gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1" creator="Test">
          <rte>
            <rtept lat="52.5200" lon="13.4050"/>
            <rtept lat="52.5210" lon="13.4060"/>
          </rte>
        </gpx>"""
        gpx = GPX.from_string(gpx_string)
        route = gpx.rte[0]
        geo = route.__geo_interface__
        # Without properties, returns pure geometry
        assert geo["type"] == "LineString"
        assert len(geo["bbox"]) == 4

    def test_segment_geo_interface_without_elevation(self) -> None:
        """Test segment GeoJSON interface without elevation uses 4-element bbox."""
        gpx_string = """<?xml version="1.0" encoding="UTF-8"?>
        <gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1" creator="Test">
          <trk>
            <trkseg>
              <trkpt lat="52.5200" lon="13.4050"/>
              <trkpt lat="52.5210" lon="13.4060"/>
            </trkseg>
          </trk>
        </gpx>"""
        gpx = GPX.from_string(gpx_string)
        segment = gpx.trk[0].trkseg[0]
        geo = segment.__geo_interface__
        # TrackSegment always returns pure geometry
        assert geo["type"] == "LineString"
        assert len(geo["bbox"]) == 4
