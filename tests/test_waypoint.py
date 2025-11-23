"""Tests for gpx.waypoint module."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from gpx import GPX, Waypoint
from gpx.types import Degrees, DGPSStation, Fix, Latitude, Longitude


class TestWaypointParsing:
    """Tests for parsing waypoints from XML."""

    def test_parse_waypoint_lat_lon(self, gpx_with_waypoint_string: str) -> None:
        """Test parsing waypoint latitude and longitude."""
        gpx = GPX.from_string(gpx_with_waypoint_string)
        wpt = gpx.waypoints[0]
        assert wpt.lat == Latitude("52.5200")
        assert wpt.lon == Longitude("13.4050")

    def test_parse_waypoint_elevation(self, gpx_with_waypoint_string: str) -> None:
        """Test parsing waypoint elevation."""
        gpx = GPX.from_string(gpx_with_waypoint_string)
        wpt = gpx.waypoints[0]
        assert wpt.ele == Decimal("34.5")

    def test_parse_waypoint_time(self, gpx_with_waypoint_string: str) -> None:
        """Test parsing waypoint timestamp."""
        gpx = GPX.from_string(gpx_with_waypoint_string)
        wpt = gpx.waypoints[0]
        expected_time = datetime(2023, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert wpt.time == expected_time

    def test_parse_waypoint_name(self, gpx_with_waypoint_string: str) -> None:
        """Test parsing waypoint name."""
        gpx = GPX.from_string(gpx_with_waypoint_string)
        wpt = gpx.waypoints[0]
        assert wpt.name == "Berlin"

    def test_parse_waypoint_description(self, gpx_with_waypoint_string: str) -> None:
        """Test parsing waypoint description."""
        gpx = GPX.from_string(gpx_with_waypoint_string)
        wpt = gpx.waypoints[0]
        assert wpt.desc == "Capital of Germany"

    def test_parse_waypoint_comment(self, gpx_with_waypoint_string: str) -> None:
        """Test parsing waypoint comment."""
        gpx = GPX.from_string(gpx_with_waypoint_string)
        wpt = gpx.waypoints[0]
        assert wpt.cmt == "A comment"

    def test_parse_waypoint_source(self, gpx_with_waypoint_string: str) -> None:
        """Test parsing waypoint source."""
        gpx = GPX.from_string(gpx_with_waypoint_string)
        wpt = gpx.waypoints[0]
        assert wpt.src == "Manual"

    def test_parse_waypoint_symbol(self, gpx_with_waypoint_string: str) -> None:
        """Test parsing waypoint symbol."""
        gpx = GPX.from_string(gpx_with_waypoint_string)
        wpt = gpx.waypoints[0]
        assert wpt.sym == "City"

    def test_parse_waypoint_type(self, gpx_with_waypoint_string: str) -> None:
        """Test parsing waypoint type."""
        gpx = GPX.from_string(gpx_with_waypoint_string)
        wpt = gpx.waypoints[0]
        assert wpt.type == "City"

    def test_parse_waypoint_fix(self, gpx_with_waypoint_string: str) -> None:
        """Test parsing waypoint fix type."""
        gpx = GPX.from_string(gpx_with_waypoint_string)
        wpt = gpx.waypoints[0]
        assert wpt.fix == Fix("3d")

    def test_parse_waypoint_satellites(self, gpx_with_waypoint_string: str) -> None:
        """Test parsing waypoint satellite count."""
        gpx = GPX.from_string(gpx_with_waypoint_string)
        wpt = gpx.waypoints[0]
        assert wpt.sat == 8

    def test_parse_waypoint_hdop(self, gpx_with_waypoint_string: str) -> None:
        """Test parsing waypoint horizontal dilution of precision."""
        gpx = GPX.from_string(gpx_with_waypoint_string)
        wpt = gpx.waypoints[0]
        assert wpt.hdop == Decimal("1.2")

    def test_parse_waypoint_vdop(self, gpx_with_waypoint_string: str) -> None:
        """Test parsing waypoint vertical dilution of precision."""
        gpx = GPX.from_string(gpx_with_waypoint_string)
        wpt = gpx.waypoints[0]
        assert wpt.vdop == Decimal("1.5")

    def test_parse_waypoint_pdop(self, gpx_with_waypoint_string: str) -> None:
        """Test parsing waypoint position dilution of precision."""
        gpx = GPX.from_string(gpx_with_waypoint_string)
        wpt = gpx.waypoints[0]
        assert wpt.pdop == Decimal("1.8")


class TestWaypointBuilding:
    """Tests for building waypoint XML."""

    def test_build_waypoint_basic(self, sample_waypoint: Waypoint) -> None:
        """Test building basic waypoint XML."""
        element = sample_waypoint._build()
        assert element.get("lat") == "52.5200"
        assert element.get("lon") == "13.4050"

    def test_build_waypoint_elevation(self, sample_waypoint: Waypoint) -> None:
        """Test building waypoint with elevation."""
        element = sample_waypoint._build()
        ele = element.find("ele")
        assert ele is not None
        assert ele.text == "34.5"

    def test_build_waypoint_name(self, sample_waypoint: Waypoint) -> None:
        """Test building waypoint with name."""
        element = sample_waypoint._build()
        name = element.find("name")
        assert name is not None
        assert name.text == "Berlin"

    def test_build_waypoint_time_format(self, sample_waypoint: Waypoint) -> None:
        """Test that time is formatted correctly in XML."""
        element = sample_waypoint._build()
        time = element.find("time")
        assert time is not None
        assert "2023-06-15T10:30:00" in time.text
        assert time.text.endswith("Z")

    def test_build_waypoint_roundtrip(self, gpx_with_waypoint_string: str) -> None:
        """Test that parsing and building produces equivalent output."""
        gpx = GPX.from_string(gpx_with_waypoint_string)
        output = gpx.to_string()
        gpx2 = GPX.from_string(output)

        assert gpx2.waypoints[0].lat == gpx.waypoints[0].lat
        assert gpx2.waypoints[0].lon == gpx.waypoints[0].lon
        assert gpx2.waypoints[0].name == gpx.waypoints[0].name


class TestWaypointCalculations:
    """Tests for waypoint distance, duration, and speed calculations."""

    @pytest.fixture
    def berlin_waypoint(self) -> Waypoint:
        """Create a waypoint for Berlin."""
        wpt = Waypoint()
        wpt.lat = Latitude("52.5200")
        wpt.lon = Longitude("13.4050")
        wpt.ele = Decimal("34.0")
        wpt.time = datetime(2023, 6, 15, 10, 0, 0, tzinfo=timezone.utc)
        return wpt

    @pytest.fixture
    def munich_waypoint(self) -> Waypoint:
        """Create a waypoint for Munich."""
        wpt = Waypoint()
        wpt.lat = Latitude("48.1351")
        wpt.lon = Longitude("11.5820")
        wpt.ele = Decimal("520.0")
        wpt.time = datetime(2023, 6, 15, 14, 0, 0, tzinfo=timezone.utc)
        return wpt

    @pytest.fixture
    def nearby_waypoint(self) -> Waypoint:
        """Create a waypoint near Berlin."""
        wpt = Waypoint()
        wpt.lat = Latitude("52.5210")
        wpt.lon = Longitude("13.4060")
        wpt.ele = Decimal("35.0")
        wpt.time = datetime(2023, 6, 15, 10, 1, 0, tzinfo=timezone.utc)
        return wpt

    def test_distance_to_same_point(self, berlin_waypoint: Waypoint) -> None:
        """Test distance to same point is zero."""
        distance = berlin_waypoint.distance_to(berlin_waypoint)
        assert distance == pytest.approx(0.0, abs=0.01)

    def test_distance_to_nearby_point(
        self,
        berlin_waypoint: Waypoint,
        nearby_waypoint: Waypoint,
    ) -> None:
        """Test distance to nearby point is reasonable."""
        distance = berlin_waypoint.distance_to(nearby_waypoint)
        # Should be roughly 100-200 meters
        assert 50 < distance < 300

    def test_distance_to_distant_point(
        self,
        berlin_waypoint: Waypoint,
        munich_waypoint: Waypoint,
    ) -> None:
        """Test distance to distant point (Berlin to Munich ~500km)."""
        distance = berlin_waypoint.distance_to(munich_waypoint)
        # Berlin to Munich is approximately 500-520 km
        assert 480000 < distance < 540000

    def test_distance_is_symmetric(
        self,
        berlin_waypoint: Waypoint,
        munich_waypoint: Waypoint,
    ) -> None:
        """Test that distance calculation is symmetric."""
        d1 = berlin_waypoint.distance_to(munich_waypoint)
        d2 = munich_waypoint.distance_to(berlin_waypoint)
        assert d1 == pytest.approx(d2, rel=1e-9)

    def test_distance_with_custom_radius(
        self,
        berlin_waypoint: Waypoint,
        munich_waypoint: Waypoint,
    ) -> None:
        """Test distance calculation with custom earth radius."""
        # Default radius
        d1 = berlin_waypoint.distance_to(munich_waypoint)
        # Smaller radius should give smaller distance
        d2 = berlin_waypoint.distance_to(munich_waypoint, radius=6_000_000)
        assert d2 < d1

    def test_duration_to(
        self,
        berlin_waypoint: Waypoint,
        munich_waypoint: Waypoint,
    ) -> None:
        """Test duration calculation between waypoints."""
        duration = berlin_waypoint.duration_to(munich_waypoint)
        expected = timedelta(hours=4)
        assert duration == expected

    def test_duration_to_no_time(self, berlin_waypoint: Waypoint) -> None:
        """Test duration returns zero when timestamps are missing."""
        wpt2 = Waypoint()
        wpt2.lat = Latitude("52.5")
        wpt2.lon = Longitude("13.4")
        wpt2.time = None

        duration = berlin_waypoint.duration_to(wpt2)
        assert duration == timedelta()

    def test_speed_to(
        self,
        berlin_waypoint: Waypoint,
        nearby_waypoint: Waypoint,
    ) -> None:
        """Test speed calculation between waypoints."""
        speed = berlin_waypoint.speed_to(nearby_waypoint)
        # Distance ~130m in 60 seconds = ~2.2 m/s
        assert 1.0 < speed < 4.0

    def test_gain_to_uphill(
        self,
        berlin_waypoint: Waypoint,
        munich_waypoint: Waypoint,
    ) -> None:
        """Test elevation gain to higher point."""
        gain = berlin_waypoint.gain_to(munich_waypoint)
        expected = Decimal("520.0") - Decimal("34.0")
        assert gain == expected

    def test_gain_to_downhill(
        self,
        munich_waypoint: Waypoint,
        berlin_waypoint: Waypoint,
    ) -> None:
        """Test elevation gain to lower point (negative)."""
        gain = munich_waypoint.gain_to(berlin_waypoint)
        expected = Decimal("34.0") - Decimal("520.0")
        assert gain == expected

    def test_gain_to_no_elevation(self, berlin_waypoint: Waypoint) -> None:
        """Test elevation gain returns zero when elevation is missing."""
        wpt2 = Waypoint()
        wpt2.lat = Latitude("52.5")
        wpt2.lon = Longitude("13.4")
        wpt2.ele = None

        gain = berlin_waypoint.gain_to(wpt2)
        assert gain == Decimal("0.0")

    def test_slope_to(
        self,
        berlin_waypoint: Waypoint,
        nearby_waypoint: Waypoint,
    ) -> None:
        """Test slope calculation."""
        slope = berlin_waypoint.slope_to(nearby_waypoint)
        # Small elevation change over ~130m should be small slope
        assert -10 < slope < 10


class TestWaypointCreation:
    """Tests for creating waypoints programmatically."""

    def test_create_empty_waypoint(self) -> None:
        """Test creating an empty waypoint."""
        wpt = Waypoint()
        assert wpt.ele is None
        assert wpt.time is None
        assert wpt.name is None
        assert wpt.links == []

    def test_create_waypoint_with_attributes(self) -> None:
        """Test creating a waypoint with all attributes."""
        wpt = Waypoint()
        wpt.lat = Latitude("52.5200")
        wpt.lon = Longitude("13.4050")
        wpt.ele = Decimal("34.5")
        wpt.time = datetime(2023, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        wpt.magvar = Degrees("15.5")
        wpt.geoidheight = Decimal("10.0")
        wpt.name = "Test Point"
        wpt.cmt = "Comment"
        wpt.desc = "Description"
        wpt.src = "Source"
        wpt.sym = "Waypoint"
        wpt.type = "POI"
        wpt.fix = Fix("3d")
        wpt.sat = 12
        wpt.hdop = Decimal("0.8")
        wpt.vdop = Decimal("1.0")
        wpt.pdop = Decimal("1.2")
        wpt.ageofdgpsdata = Decimal("5.0")
        wpt.dgpsid = DGPSStation(100)

        # Verify all attributes are set
        assert wpt.lat == Latitude("52.5200")
        assert wpt.lon == Longitude("13.4050")
        assert wpt.ele == Decimal("34.5")
        assert wpt.name == "Test Point"
        assert wpt.fix == Fix("3d")
        assert wpt.sat == 12
        assert wpt.dgpsid == DGPSStation(100)


class TestWaypointRepresentation:
    """Tests for waypoint string representation."""

    def test_waypoint_repr(self, sample_waypoint: Waypoint) -> None:
        """Test waypoint __repr__ output."""
        repr_str = repr(sample_waypoint)
        assert "Waypoint" in repr_str
        assert "lat=" in repr_str
        assert "lon=" in repr_str
