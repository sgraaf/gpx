"""Tests for gpx.track and gpx.track_segment modules."""
from datetime import timedelta
from decimal import Decimal

import pytest

from gpx import GPX, Track, TrackSegment, Waypoint
from gpx.types import Latitude, Longitude


class TestTrackSegmentParsing:
    """Tests for parsing track segments from XML."""

    def test_parse_track_segment_points(self, gpx_with_track_string):
        """Test parsing track segment track points."""
        gpx = GPX.from_string(gpx_with_track_string)
        trk = gpx.tracks[0]
        seg = trk.trksegs[0]
        assert len(seg.trkpts) == 3
        assert len(seg.points) == 3  # alias

    def test_parse_track_segment_point_coordinates(self, gpx_with_track_string):
        """Test parsing track point coordinates."""
        gpx = GPX.from_string(gpx_with_track_string)
        seg = gpx.tracks[0].trksegs[0]
        assert seg.trkpts[0].lat == Latitude("52.5200")
        assert seg.trkpts[0].lon == Longitude("13.4050")

    def test_parse_track_segment_point_elevation(self, gpx_with_track_string):
        """Test parsing track point elevation."""
        gpx = GPX.from_string(gpx_with_track_string)
        seg = gpx.tracks[0].trksegs[0]
        assert seg.trkpts[0].ele == Decimal("34.5")
        assert seg.trkpts[1].ele == Decimal("35.0")
        assert seg.trkpts[2].ele == Decimal("36.5")


class TestTrackSegmentBuilding:
    """Tests for building track segment XML."""

    def test_build_track_segment(self, sample_track_segment):
        """Test building track segment XML."""
        element = sample_track_segment._build()
        assert element.tag == "trkseg"
        trkpts = element.findall("trkpt")
        assert len(trkpts) == 4

    def test_build_track_segment_point_tag(self, sample_track_segment):
        """Test that track points use 'trkpt' tag."""
        element = sample_track_segment._build()
        trkpts = element.findall("trkpt")
        assert len(trkpts) > 0
        assert all(pt.tag == "trkpt" for pt in trkpts)


class TestTrackSegmentStatistics:
    """Tests for track segment statistics."""

    def test_track_segment_bounds(self, sample_track_segment):
        """Test track segment bounds calculation."""
        bounds = sample_track_segment.bounds
        min_lat, min_lon, max_lat, max_lon = bounds
        assert min_lat == Latitude("52.5200")
        assert max_lat == Latitude("52.5230")

    def test_track_segment_total_distance(self, sample_track_segment):
        """Test track segment total distance calculation."""
        distance = sample_track_segment.total_distance
        # Should be sum of distances between consecutive points
        assert distance > 0

    def test_track_segment_total_duration(self, sample_track_segment):
        """Test track segment total duration calculation."""
        duration = sample_track_segment.total_duration
        # 4 points with 1 minute intervals = 3 minutes
        assert duration == timedelta(minutes=3)

    def test_track_segment_avg_speed(self, sample_track_segment):
        """Test track segment average speed calculation."""
        speed = sample_track_segment.avg_speed
        # Speed should be positive
        assert speed > 0

    def test_track_segment_elevations(self, sample_track_segment):
        """Test track segment elevation statistics."""
        assert sample_track_segment.min_elevation == Decimal("34.5")
        assert sample_track_segment.max_elevation == Decimal("36.5")
        assert sample_track_segment.diff_elevation == Decimal("2.0")

    def test_track_segment_avg_elevation(self, sample_track_segment):
        """Test track segment average elevation."""
        avg = sample_track_segment.avg_elevation
        # Average of 34.5, 35.0, 36.5, 35.5 = 35.375
        expected = (Decimal("34.5") + Decimal("35.0") + Decimal("36.5") + Decimal("35.5")) / 4
        assert avg == expected

    def test_track_segment_total_ascent(self, sample_track_segment):
        """Test track segment total ascent calculation."""
        ascent = sample_track_segment.total_ascent
        # Points: 34.5 -> 35.0 (+0.5) -> 36.5 (+1.5) -> 35.5 (-1.0)
        # Total ascent = 0.5 + 1.5 = 2.0
        assert ascent == Decimal("2.0")

    def test_track_segment_total_descent(self, sample_track_segment):
        """Test track segment total descent calculation."""
        descent = sample_track_segment.total_descent
        # Points: 34.5 -> 35.0 -> 36.5 -> 35.5 (-1.0)
        # Total descent = 1.0
        assert descent == Decimal("1.0")


class TestTrackSegmentSequence:
    """Tests for track segment sequence behavior."""

    def test_track_segment_len(self, sample_track_segment):
        """Test track segment length."""
        assert len(sample_track_segment) == 4

    def test_track_segment_getitem(self, sample_track_segment):
        """Test track segment indexing."""
        point = sample_track_segment[0]
        assert isinstance(point, Waypoint)
        assert point.lat == Latitude("52.5200")

    def test_track_segment_iteration(self, sample_track_segment):
        """Test iterating over track segment."""
        points = list(sample_track_segment)
        assert len(points) == 4
        assert all(isinstance(p, Waypoint) for p in points)


class TestTrackParsing:
    """Tests for parsing tracks from XML."""

    def test_parse_track_name(self, gpx_with_track_string):
        """Test parsing track name."""
        gpx = GPX.from_string(gpx_with_track_string)
        trk = gpx.tracks[0]
        assert trk.name == "Morning Run"

    def test_parse_track_description(self, gpx_with_track_string):
        """Test parsing track description."""
        gpx = GPX.from_string(gpx_with_track_string)
        trk = gpx.tracks[0]
        assert trk.desc == "A morning run through the park"

    def test_parse_track_comment(self, gpx_with_track_string):
        """Test parsing track comment."""
        gpx = GPX.from_string(gpx_with_track_string)
        trk = gpx.tracks[0]
        assert trk.cmt == "Good weather"

    def test_parse_track_source(self, gpx_with_track_string):
        """Test parsing track source."""
        gpx = GPX.from_string(gpx_with_track_string)
        trk = gpx.tracks[0]
        assert trk.src == "Garmin"

    def test_parse_track_number(self, gpx_with_track_string):
        """Test parsing track number."""
        gpx = GPX.from_string(gpx_with_track_string)
        trk = gpx.tracks[0]
        assert trk.number == 1

    def test_parse_track_type(self, gpx_with_track_string):
        """Test parsing track type."""
        gpx = GPX.from_string(gpx_with_track_string)
        trk = gpx.tracks[0]
        assert trk.type == "Running"

    def test_parse_track_segments(self, gpx_with_track_string):
        """Test parsing track segments."""
        gpx = GPX.from_string(gpx_with_track_string)
        trk = gpx.tracks[0]
        assert len(trk.trksegs) == 2
        assert len(trk.segments) == 2  # alias


class TestTrackBuilding:
    """Tests for building track XML."""

    def test_build_track(self, sample_track):
        """Test building track XML."""
        element = sample_track._build()
        assert element.tag == "trk"

    def test_build_track_name(self, sample_track):
        """Test building track with name."""
        element = sample_track._build()
        name = element.find("name")
        assert name is not None
        assert name.text == "Test Track"

    def test_build_track_roundtrip(self, gpx_with_track_string):
        """Test track parsing and building roundtrip."""
        gpx = GPX.from_string(gpx_with_track_string)
        output = gpx.to_string()
        gpx2 = GPX.from_string(output)

        assert gpx2.tracks[0].name == gpx.tracks[0].name
        assert len(gpx2.tracks[0].trksegs) == len(gpx.tracks[0].trksegs)


class TestTrackStatistics:
    """Tests for track statistics aggregation."""

    def test_track_total_distance(self, gpx_with_track_string):
        """Test track total distance aggregation across segments."""
        gpx = GPX.from_string(gpx_with_track_string)
        trk = gpx.tracks[0]
        # Distance should be sum of all segment distances
        total = sum(seg.total_distance for seg in trk.trksegs)
        assert trk.total_distance == pytest.approx(total)

    def test_track_total_duration(self, gpx_with_track_string):
        """Test track total duration aggregation."""
        gpx = GPX.from_string(gpx_with_track_string)
        trk = gpx.tracks[0]
        # Duration should be sum of all segment durations
        total = sum([seg.total_duration for seg in trk.trksegs], timedelta())
        assert trk.total_duration == total

    def test_track_bounds(self, gpx_with_track_string):
        """Test track bounds span all segments."""
        gpx = GPX.from_string(gpx_with_track_string)
        trk = gpx.tracks[0]
        bounds = trk.bounds
        min_lat, min_lon, max_lat, max_lon = bounds
        # Should span all points in all segments
        assert min_lat == Latitude("52.5200")
        assert max_lat == Latitude("52.5240")

    def test_track_elevation_stats(self, gpx_with_track_string):
        """Test track elevation statistics."""
        gpx = GPX.from_string(gpx_with_track_string)
        trk = gpx.tracks[0]
        # Min/max should span all segments
        assert trk.min_elevation == Decimal("34.0")
        assert trk.max_elevation == Decimal("36.5")


class TestTrackSequence:
    """Tests for track sequence behavior."""

    def test_track_len(self, gpx_with_track_string):
        """Test track length (number of segments)."""
        gpx = GPX.from_string(gpx_with_track_string)
        trk = gpx.tracks[0]
        assert len(trk) == 2

    def test_track_getitem(self, gpx_with_track_string):
        """Test track indexing."""
        gpx = GPX.from_string(gpx_with_track_string)
        trk = gpx.tracks[0]
        seg = trk[0]
        assert isinstance(seg, TrackSegment)

    def test_track_iteration(self, gpx_with_track_string):
        """Test iterating over track."""
        gpx = GPX.from_string(gpx_with_track_string)
        trk = gpx.tracks[0]
        segments = list(trk)
        assert len(segments) == 2
        assert all(isinstance(s, TrackSegment) for s in segments)


class TestTrackCreation:
    """Tests for creating tracks programmatically."""

    def test_create_empty_track(self):
        """Test creating an empty track."""
        trk = Track()
        assert trk.name is None
        assert trk.desc is None
        assert trk.trksegs == []
        assert trk.links == []

    def test_create_track_with_segments(self, sample_waypoints_for_track):
        """Test creating a track with segments."""
        seg = TrackSegment()
        seg.trkpts = sample_waypoints_for_track
        seg.points = seg.trkpts

        trk = Track()
        trk.name = "Custom Track"
        trk.trksegs = [seg]
        trk.segments = trk.trksegs

        assert trk.name == "Custom Track"
        assert len(trk.trksegs) == 1
        assert len(trk.trksegs[0].trkpts) == 4
