"""Tests for gpx.route module."""

from datetime import timedelta
from decimal import Decimal
from typing import Any

from gpx import GPX, Link, Route, Waypoint
from gpx.types import Latitude, Longitude

#: GPX 1.1 namespace
GPX_NS = "http://www.topografix.com/GPX/1/1"


class TestRouteParsing:
    """Tests for parsing routes from XML."""

    def test_parse_route_name(self, gpx_with_route_string: str) -> None:
        """Test parsing route name."""
        gpx = GPX.from_string(gpx_with_route_string)
        rte = gpx.routes[0]
        assert rte.name == "City Tour"

    def test_parse_route_description(self, gpx_with_route_string: str) -> None:
        """Test parsing route description."""
        gpx = GPX.from_string(gpx_with_route_string)
        rte = gpx.routes[0]
        assert rte.desc == "A tour of the city"

    def test_parse_route_comment(self, gpx_with_route_string: str) -> None:
        """Test parsing route comment."""
        gpx = GPX.from_string(gpx_with_route_string)
        rte = gpx.routes[0]
        assert rte.cmt == "Best route"

    def test_parse_route_source(self, gpx_with_route_string: str) -> None:
        """Test parsing route source."""
        gpx = GPX.from_string(gpx_with_route_string)
        rte = gpx.routes[0]
        assert rte.src == "Planned"

    def test_parse_route_number(self, gpx_with_route_string: str) -> None:
        """Test parsing route number."""
        gpx = GPX.from_string(gpx_with_route_string)
        rte = gpx.routes[0]
        assert rte.number == 1

    def test_parse_route_type(self, gpx_with_route_string: str) -> None:
        """Test parsing route type."""
        gpx = GPX.from_string(gpx_with_route_string)
        rte = gpx.routes[0]
        assert rte.type == "Tourism"

    def test_parse_route_points(self, gpx_with_route_string: str) -> None:
        """Test parsing route points."""
        gpx = GPX.from_string(gpx_with_route_string)
        rte = gpx.routes[0]
        assert len(rte.rtept) == 3
        assert len(rte.points) == 3  # alias

    def test_parse_route_point_coordinates(self, gpx_with_route_string: str) -> None:
        """Test parsing route point coordinates."""
        gpx = GPX.from_string(gpx_with_route_string)
        rte = gpx.routes[0]
        assert rte.rtept[0].lat == Latitude("52.5200")
        assert rte.rtept[0].lon == Longitude("13.4050")

    def test_parse_route_point_names(self, gpx_with_route_string: str) -> None:
        """Test parsing route point names."""
        gpx = GPX.from_string(gpx_with_route_string)
        rte = gpx.routes[0]
        assert rte.rtept[0].name == "Start"
        assert rte.rtept[1].name == "Checkpoint"
        assert rte.rtept[2].name == "End"



class TestRouteBuilding:
    """Tests for building route XML."""

    def test_build_route(self, sample_route: Route) -> None:
        """Test building route XML."""
        element = sample_route.to_xml()
        assert element.tag.endswith("}rte")

    def test_build_route_name(self, sample_route: Route) -> None:
        """Test building route with name."""

        element = sample_route.to_xml()
        name = element.find(f"{{{GPX_NS}}}name")
        assert name is not None
        assert name.text == "Test Route"

    def test_build_route_points_tag(self, sample_route: Route) -> None:
        """Test that route points use 'rtept' tag."""

        element = sample_route.to_xml()
        rtepts = element.findall(f"{{{GPX_NS}}}rtept")
        assert len(rtepts) == 4
        # Tags include namespace, so check that they end with }rtept
        assert all(pt.tag.endswith("}rtept") for pt in rtepts)

    def test_build_route_roundtrip(self, gpx_with_route_string: str) -> None:
        """Test route parsing and building roundtrip."""
        gpx = GPX.from_string(gpx_with_route_string)
        output = gpx.to_string()
        gpx2 = GPX.from_string(output)

        assert gpx2.routes[0].name == gpx.routes[0].name
        assert len(gpx2.routes[0].rtept) == len(gpx.routes[0].rtept)
        assert gpx2.routes[0].rtept[0].name == gpx.routes[0].rtept[0].name



class TestRouteStatistics:
    """Tests for route statistics (via PointsStatisticsMixin)."""

    def test_route_bounds(self, sample_route: Route) -> None:
        """Test route bounds calculation."""
        bounds = sample_route.bounds
        min_lat, _min_lon, max_lat, _max_lon = bounds
        assert min_lat == Latitude("52.5200")
        assert max_lat == Latitude("52.5230")

    def test_route_total_distance(self, sample_route: Route) -> None:
        """Test route total distance calculation."""
        distance = sample_route.total_distance
        assert distance > 0

    def test_route_total_duration(self, sample_route: Route) -> None:
        """Test route total duration calculation."""
        duration = sample_route.total_duration
        # 4 points with 1 minute intervals = 3 minutes
        assert duration == timedelta(minutes=3)

    def test_route_avg_speed(self, sample_route: Route) -> None:
        """Test route average speed calculation."""
        speed = sample_route.avg_speed
        assert speed > 0

    def test_route_elevations(self, sample_route: Route) -> None:
        """Test route elevation statistics."""
        assert sample_route.min_elevation == Decimal("34.5")
        assert sample_route.max_elevation == Decimal("36.5")

    def test_route_total_ascent(self, sample_route: Route) -> None:
        """Test route total ascent."""
        ascent = sample_route.total_ascent
        assert ascent >= Decimal(0)

    def test_route_total_descent(self, sample_route: Route) -> None:
        """Test route total descent."""
        descent = sample_route.total_descent
        assert descent >= Decimal(0)



class TestRouteSequence:
    """Tests for route sequence behavior (via PointsMutableSequenceMixin)."""

    def test_route_len(self, sample_route: Route) -> None:
        """Test route length."""
        assert len(sample_route) == 4

    def test_route_getitem(self, sample_route: Route) -> None:
        """Test route indexing."""
        point = sample_route[0]
        assert isinstance(point, Waypoint)
        assert point.lat == Latitude("52.5200")

    def test_route_getitem_negative_index(self, sample_route: Route) -> None:
        """Test route negative indexing."""
        point = sample_route[-1]
        assert isinstance(point, Waypoint)
        assert point.lat == Latitude("52.5230")

    def test_route_getitem_slice(self, sample_route: Route) -> None:
        """Test route slicing."""
        points = sample_route[1:3]
        assert len(points) == 2

    def test_route_iteration(self, sample_route: Route) -> None:
        """Test iterating over route."""
        points = list(sample_route)
        assert len(points) == 4
        assert all(isinstance(p, Waypoint) for p in points)



class TestRouteCreation:
    """Tests for creating routes programmatically."""

    def test_create_empty_route(self) -> None:
        """Test creating an empty route."""
        rte = Route()
        assert rte.name is None
        assert rte.desc is None
        assert rte.rtept == []
        assert rte.points == []
        assert rte.link == []

    def test_create_route_with_points(
        self,
        sample_waypoints_for_track: list[Waypoint],
    ) -> None:
        """Test creating a route with points."""
        rte = Route(
            name="Custom Route",
            desc="A custom route",
            number=1,
            type="Cycling",
            rtept=sample_waypoints_for_track,
        )

        assert rte.name == "Custom Route"
        assert rte.number == 1
        assert len(rte.rtept) == 4

    def test_route_with_links(self, sample_route: Route, sample_link: Link) -> None:
        """Test route with links."""

        sample_route.link = [sample_link]
        element = sample_route.to_xml()
        links = element.findall(f"{{{GPX_NS}}}link")
        assert len(links) == 1



class TestRouteGeoInterface:
    """Tests for the `__geo_interface__` property."""

    def test_route_geo_interface(
        self, gpx_with_route_string: str, route_geo_interface: dict[str, Any]
    ) -> None:
        gpx = GPX.from_string(gpx_with_route_string)
        rte = gpx.routes[0]

        assert rte.__geo_interface__ == route_geo_interface
