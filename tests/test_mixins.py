"""Tests for gpx.mixins module."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from gpx import Route, TrackSegment, Waypoint
from gpx.mixins import (
    AttributesMutableMappingMixin,
    PointsMutableSequenceMixin,
    PointsSequenceMixin,
    PointsStatisticsMixin,
)
from gpx.types import Latitude, Longitude


class TestAttributesMutableMappingMixin:
    """Tests for AttributesMutableMappingMixin."""

    class MockMappingClass(AttributesMutableMappingMixin):
        """A mock class for testing the mixin."""

        __keys__ = ("name", "value", "count")

        def __init__(self):
            self.name = None
            self.value = None
            self.count = None

    def test_getitem(self):
        """Test getting item by key."""
        obj = self.MockMappingClass()
        obj.name = "test"
        assert obj["name"] == "test"

    def test_getitem_invalid_key(self):
        """Test getting item with invalid key raises KeyError."""
        obj = self.MockMappingClass()
        with pytest.raises(KeyError, match="Key not found"):
            _ = obj["invalid"]

    def test_setitem(self):
        """Test setting item by key."""
        obj = self.MockMappingClass()
        obj["name"] = "new_name"
        assert obj.name == "new_name"

    def test_setitem_invalid_key(self):
        """Test setting item with invalid key raises KeyError."""
        obj = self.MockMappingClass()
        with pytest.raises(KeyError, match="Key not found"):
            obj["invalid"] = "value"

    def test_delitem(self):
        """Test deleting item sets it to None."""
        obj = self.MockMappingClass()
        obj.name = "test"
        del obj["name"]
        assert obj.name is None

    def test_delitem_invalid_key(self):
        """Test deleting item with invalid key raises KeyError."""
        obj = self.MockMappingClass()
        with pytest.raises(KeyError, match="Key not found"):
            del obj["invalid"]

    def test_iter(self):
        """Test iteration over keys."""
        obj = self.MockMappingClass()
        keys = list(obj)
        assert keys == ["name", "value", "count"]

    def test_len(self):
        """Test length equals number of keys."""
        obj = self.MockMappingClass()
        assert len(obj) == 3


class TestPointsSequenceMixin:
    """Tests for PointsSequenceMixin."""

    @pytest.fixture
    def segment_with_points(self, sample_waypoints_for_track):
        """Create a track segment with points."""
        seg = TrackSegment()
        seg.trkpts = sample_waypoints_for_track
        seg.points = seg.trkpts
        return seg

    def test_getitem_int(self, segment_with_points):
        """Test getting item by integer index."""
        point = segment_with_points[0]
        assert isinstance(point, Waypoint)

    def test_getitem_negative(self, segment_with_points):
        """Test getting item by negative index."""
        point = segment_with_points[-1]
        assert isinstance(point, Waypoint)
        assert point.lat == Latitude("52.5230")

    def test_getitem_slice(self, segment_with_points):
        """Test getting items by slice."""
        points = segment_with_points[1:3]
        assert len(points) == 2

    def test_iter(self, segment_with_points):
        """Test iteration."""
        points = list(segment_with_points)
        assert len(points) == 4

    def test_len(self, segment_with_points):
        """Test length."""
        assert len(segment_with_points) == 4


class TestPointsMutableSequenceMixin:
    """Tests for PointsMutableSequenceMixin."""

    @pytest.fixture
    def route_with_points(self, sample_waypoints_for_track):
        """Create a route with points."""
        route = Route()
        route.rtepts = list(sample_waypoints_for_track)  # copy the list
        route.points = route.rtepts
        return route

    def test_delitem_int(self, route_with_points):
        """Test deleting item by integer index."""
        original_len = len(route_with_points)
        del route_with_points[0]
        assert len(route_with_points) == original_len - 1

    def test_delitem_slice(self, route_with_points):
        """Test deleting items by slice."""
        del route_with_points[1:3]
        assert len(route_with_points) == 2

    def test_insert(self, route_with_points):
        """Test inserting item."""
        new_point = Waypoint()
        new_point.lat = Latitude("52.5")
        new_point.lon = Longitude("13.4")

        route_with_points.insert(1, new_point)
        assert len(route_with_points) == 5
        assert route_with_points[1] == new_point

    def test_append_via_insert(self, route_with_points):
        """Test appending by inserting at end."""
        new_point = Waypoint()
        new_point.lat = Latitude("52.5")
        new_point.lon = Longitude("13.4")

        route_with_points.insert(len(route_with_points), new_point)
        assert route_with_points[-1] == new_point

    def test_setitem_int(self, route_with_points):
        """Test setting item by integer index."""
        new_point = Waypoint()
        new_point.lat = Latitude("52.55")
        new_point.lon = Longitude("13.45")

        route_with_points[1] = new_point
        assert route_with_points[1] == new_point
        assert route_with_points[1].lat == Latitude("52.55")

    def test_setitem_slice(self, route_with_points):
        """Test setting items by slice."""
        new_point1 = Waypoint()
        new_point1.lat = Latitude("52.55")
        new_point1.lon = Longitude("13.45")

        new_point2 = Waypoint()
        new_point2.lat = Latitude("52.56")
        new_point2.lon = Longitude("13.46")

        route_with_points[1:3] = [new_point1, new_point2]
        assert route_with_points[1] == new_point1
        assert route_with_points[2] == new_point2


class TestPointsStatisticsMixin:
    """Tests for PointsStatisticsMixin."""

    @pytest.fixture
    def segment_with_elevation(self):
        """Create a track segment with elevation data."""
        seg = TrackSegment()
        points = []

        # Create points with known values for predictable statistics
        data = [
            ("52.5200", "13.4050", "100.0", "2023-06-15T06:00:00Z"),
            ("52.5210", "13.4060", "110.0", "2023-06-15T06:01:00Z"),
            ("52.5220", "13.4070", "105.0", "2023-06-15T06:02:00Z"),
            ("52.5230", "13.4080", "120.0", "2023-06-15T06:03:00Z"),
        ]

        for lat, lon, ele, time_str in data:
            wpt = Waypoint()
            wpt.lat = Latitude(lat)
            wpt.lon = Longitude(lon)
            wpt.ele = Decimal(ele)
            wpt.time = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            points.append(wpt)

        seg.trkpts = points
        seg.points = seg.trkpts
        return seg

    def test_bounds(self, segment_with_elevation):
        """Test bounds calculation."""
        bounds = segment_with_elevation.bounds
        min_lat, min_lon, max_lat, max_lon = bounds
        assert min_lat == Latitude("52.5200")
        assert max_lat == Latitude("52.5230")
        assert min_lon == Longitude("13.4050")
        assert max_lon == Longitude("13.4080")

    def test_total_distance(self, segment_with_elevation):
        """Test total distance calculation."""
        distance = segment_with_elevation.total_distance
        assert distance > 0
        # Should be roughly 3 * ~130m = ~390m
        assert 300 < distance < 500

    def test_distance_alias(self, segment_with_elevation):
        """Test distance alias."""
        assert segment_with_elevation.distance == segment_with_elevation.total_distance

    def test_total_duration(self, segment_with_elevation):
        """Test total duration calculation."""
        duration = segment_with_elevation.total_duration
        assert duration == timedelta(minutes=3)

    def test_duration_alias(self, segment_with_elevation):
        """Test duration alias."""
        assert segment_with_elevation.duration == segment_with_elevation.total_duration

    def test_avg_speed(self, segment_with_elevation):
        """Test average speed calculation."""
        speed = segment_with_elevation.avg_speed
        # distance / time
        expected = segment_with_elevation.total_distance / 180  # 3 minutes = 180 seconds
        assert speed == pytest.approx(expected)

    def test_speed_alias(self, segment_with_elevation):
        """Test speed alias."""
        assert segment_with_elevation.speed == segment_with_elevation.avg_speed

    def test_max_speed(self, segment_with_elevation):
        """Test maximum speed calculation."""
        max_speed = segment_with_elevation.max_speed
        assert max_speed > 0
        assert max_speed >= segment_with_elevation.avg_speed

    def test_min_speed(self, segment_with_elevation):
        """Test minimum speed calculation."""
        min_speed = segment_with_elevation.min_speed
        assert min_speed > 0
        assert min_speed <= segment_with_elevation.avg_speed

    def test_speed_profile(self, segment_with_elevation):
        """Test speed profile generation."""
        profile = segment_with_elevation.speed_profile
        # Should have 3 entries (between 4 points)
        assert len(profile) == 3
        # Each entry should be (datetime, speed)
        for timestamp, speed in profile:
            assert isinstance(timestamp, datetime)
            assert isinstance(speed, float)

    def test_avg_elevation(self, segment_with_elevation):
        """Test average elevation calculation."""
        avg = segment_with_elevation.avg_elevation
        # (100 + 110 + 105 + 120) / 4 = 108.75
        expected = Decimal("108.75")
        assert avg == expected

    def test_elevation_alias(self, segment_with_elevation):
        """Test elevation alias."""
        assert segment_with_elevation.elevation == segment_with_elevation.avg_elevation

    def test_max_elevation(self, segment_with_elevation):
        """Test maximum elevation."""
        assert segment_with_elevation.max_elevation == Decimal("120.0")

    def test_min_elevation(self, segment_with_elevation):
        """Test minimum elevation."""
        assert segment_with_elevation.min_elevation == Decimal("100.0")

    def test_diff_elevation(self, segment_with_elevation):
        """Test elevation difference."""
        diff = segment_with_elevation.diff_elevation
        assert diff == Decimal("20.0")

    def test_total_ascent(self, segment_with_elevation):
        """Test total ascent calculation."""
        ascent = segment_with_elevation.total_ascent
        # 100 -> 110 (+10), 110 -> 105 (-5), 105 -> 120 (+15)
        # Total ascent = 10 + 15 = 25
        assert ascent == Decimal("25.0")

    def test_total_descent(self, segment_with_elevation):
        """Test total descent calculation."""
        descent = segment_with_elevation.total_descent
        # 100 -> 110 (+10), 110 -> 105 (-5), 105 -> 120 (+15)
        # Total descent = 5
        assert descent == Decimal("5.0")

    def test_elevation_profile(self, segment_with_elevation):
        """Test elevation profile generation."""
        profile = segment_with_elevation.elevation_profile
        # Should have 4 entries (one per point)
        assert len(profile) == 4
        # First entry should be at distance 0
        assert profile[0][0] == 0.0
        assert profile[0][1] == Decimal("100.0")
        # Each subsequent distance should increase
        for i in range(1, len(profile)):
            assert profile[i][0] > profile[i - 1][0]

    def test_moving_duration(self, segment_with_elevation):
        """Test moving duration calculation."""
        duration = segment_with_elevation.moving_duration
        # All segments should have speed > 0.5 km/h
        assert duration > timedelta(0)

    def test_avg_moving_speed(self, segment_with_elevation):
        """Test average moving speed calculation."""
        speed = segment_with_elevation.avg_moving_speed
        assert speed > 0


class TestPointsStatisticsMixinEdgeCases:
    """Tests for edge cases in statistics calculations."""

    @pytest.fixture
    def segment_no_elevation(self):
        """Create a track segment without elevation data."""
        seg = TrackSegment()
        points = []

        for i in range(3):
            wpt = Waypoint()
            wpt.lat = Latitude(f"52.52{i}0")
            wpt.lon = Longitude(f"13.40{i}0")
            wpt.ele = None
            wpt.time = datetime(2023, 6, 15, 6, i, 0, tzinfo=timezone.utc)
            points.append(wpt)

        seg.trkpts = points
        seg.points = seg.trkpts
        return seg

    def test_elevation_stats_with_no_elevation(self, segment_no_elevation):
        """Test elevation statistics when no elevation data exists."""
        from decimal import InvalidOperation

        # Should raise when no elevation data (division by zero in Decimal)
        with pytest.raises((ValueError, ZeroDivisionError, InvalidOperation)):
            _ = segment_no_elevation.avg_elevation

    @pytest.fixture
    def segment_partial_elevation(self):
        """Create a track segment with partial elevation data."""
        seg = TrackSegment()
        points = []

        data = [
            ("52.5200", "13.4050", "100.0"),
            ("52.5210", "13.4060", None),
            ("52.5220", "13.4070", "105.0"),
        ]

        for i, (lat, lon, ele) in enumerate(data):
            wpt = Waypoint()
            wpt.lat = Latitude(lat)
            wpt.lon = Longitude(lon)
            wpt.ele = Decimal(ele) if ele else None
            wpt.time = datetime(2023, 6, 15, 6, i, 0, tzinfo=timezone.utc)
            points.append(wpt)

        seg.trkpts = points
        seg.points = seg.trkpts
        return seg

    def test_elevation_stats_with_partial_elevation(self, segment_partial_elevation):
        """Test elevation statistics with partial elevation data."""
        # Should only consider points with elevation
        avg = segment_partial_elevation.avg_elevation
        expected = (Decimal("100.0") + Decimal("105.0")) / 2
        assert avg == expected
