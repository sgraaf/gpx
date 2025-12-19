"""Tests for edge cases in GPX parsing and validation.

This module tests valid and invalid edge cases to ensure robust handling
of all possible GPX file variations.
"""

import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation

import pytest

from gpx import from_string
from gpx.types import Degrees, DGPSStation, Fix, Latitude, Longitude


class TestValidEdgeCases:
    """Tests for valid edge cases that should parse successfully."""

    def test_waypoint_minimal(self, waypoint_minimal_gpx_string: str) -> None:
        """Test parsing a waypoint with only required lat/lon attributes."""
        gpx = from_string(waypoint_minimal_gpx_string)
        assert len(gpx.wpt) == 1
        assert gpx.wpt[0].lat == Latitude("0")
        assert gpx.wpt[0].lon == Longitude("0")
        assert gpx.wpt[0].ele is None
        assert gpx.wpt[0].name is None

    def test_waypoint_all_fields(self, waypoint_all_fields_gpx_string: str) -> None:
        """Test parsing a waypoint with all possible fields populated."""
        gpx = from_string(waypoint_all_fields_gpx_string)
        wpt = gpx.wpt[0]
        assert wpt.lat == Latitude("52.5200")
        assert wpt.lon == Longitude("13.4050")
        assert wpt.ele == Decimal("34.5")
        assert wpt.magvar == Degrees("15.5")
        assert wpt.geoidheight == Decimal("47.2")
        assert wpt.name == "Complete Waypoint"
        assert wpt.cmt == "This is a comment"
        assert wpt.desc == "This is a description with all fields populated"
        assert wpt.src == "GPS Device"
        assert len(wpt.link) == 2
        assert wpt.sym == "Flag"
        assert wpt.type == "Point of Interest"
        assert wpt.fix == Fix("dgps")
        assert wpt.sat == 12
        assert wpt.hdop == Decimal("0.8")
        assert wpt.vdop == Decimal("1.2")
        assert wpt.pdop == Decimal("1.4")
        assert wpt.ageofdgpsdata == Decimal("5.0")
        assert wpt.dgpsid == DGPSStation(100)

    def test_multiple_waypoints(self, multiple_waypoints_gpx_string: str) -> None:
        """Test parsing GPX with many waypoints."""
        gpx = from_string(multiple_waypoints_gpx_string)
        assert len(gpx.wpt) == 10
        for i, wpt in enumerate(gpx.wpt, 1):
            assert wpt.name == f"Waypoint {i}"

    def test_multiple_tracks(self, multiple_tracks_gpx_string: str) -> None:
        """Test parsing GPX with multiple tracks."""
        gpx = from_string(multiple_tracks_gpx_string)
        assert len(gpx.trk) == 3
        for i, trk in enumerate(gpx.trk, 1):
            assert trk.name == f"Track {i}"

    def test_multiple_routes(self, multiple_routes_gpx_string: str) -> None:
        """Test parsing GPX with multiple routes."""
        gpx = from_string(multiple_routes_gpx_string)
        assert len(gpx.rte) == 3
        for i, rte in enumerate(gpx.rte, 1):
            assert rte.name == f"Route {i}"

    def test_empty_track_segment(self, empty_track_segment_gpx_string: str) -> None:
        """Test parsing track with empty segment."""
        gpx = from_string(empty_track_segment_gpx_string)
        trk = gpx.trk[0]
        assert len(trk.trkseg) == 3
        assert len(trk.trkseg[0].trkpt) == 1
        assert len(trk.trkseg[1].trkpt) == 0  # Empty segment
        assert len(trk.trkseg[2].trkpt) == 1

    def test_empty_track(self, empty_track_gpx_string: str) -> None:
        """Test parsing track with no segments."""
        gpx = from_string(empty_track_gpx_string)
        trk = gpx.trk[0]
        assert trk.name == "Empty track"
        assert len(trk.trkseg) == 0

    def test_empty_route(self, empty_route_gpx_string: str) -> None:
        """Test parsing route with no points."""
        gpx = from_string(empty_route_gpx_string)
        rte = gpx.rte[0]
        assert rte.name == "Empty route"
        assert len(rte.rtept) == 0

    def test_boundary_coordinates(self, boundary_coords_gpx_string: str) -> None:
        """Test parsing waypoints at coordinate boundaries."""
        gpx = from_string(boundary_coords_gpx_string)
        assert len(gpx.wpt) == 7

        # North Pole, Antimeridian
        assert gpx.wpt[0].lat == Latitude("90")
        assert gpx.wpt[0].lon == Longitude("180")

        # South Pole, Antimeridian
        assert gpx.wpt[1].lat == Latitude("-90")
        assert gpx.wpt[1].lon == Longitude("-180")

        # Equator, Prime Meridian
        assert gpx.wpt[2].lat == Latitude("0")
        assert gpx.wpt[2].lon == Longitude("0")

    def test_high_precision_coordinates(
        self, high_precision_coords_gpx_string: str
    ) -> None:
        """Test parsing coordinates with many decimal places."""
        gpx = from_string(high_precision_coords_gpx_string)
        wpt = gpx.wpt[0]
        # The exact precision depends on Decimal implementation
        assert float(wpt.lat) == pytest.approx(52.520008123456789, rel=1e-15)
        assert float(wpt.lon) == pytest.approx(13.404953987654321, rel=1e-15)
        assert wpt.ele is not None
        assert float(wpt.ele) == pytest.approx(34.123456789, rel=1e-9)

    def test_time_formats(self, time_formats_gpx_string: str) -> None:
        """Test parsing various ISO 8601 time formats."""
        gpx = from_string(time_formats_gpx_string)
        # All waypoints should have valid times
        for wpt in gpx.wpt:
            assert wpt.time is not None

    def test_unicode_content(self, unicode_content_gpx_string: str) -> None:
        """Test parsing Unicode content in names and descriptions."""
        gpx = from_string(unicode_content_gpx_string)
        assert gpx.metadata is not None
        assert gpx.metadata.name is not None
        assert "internacional" in gpx.metadata.name

        # Check various scripts
        wpt_names = [wpt.name for wpt in gpx.wpt]
        assert "Tokyo" in wpt_names
        assert "Berlin" in wpt_names

    def test_extreme_elevations(self, extreme_elevations_gpx_string: str) -> None:
        """Test parsing extreme elevation values."""
        gpx = from_string(extreme_elevations_gpx_string)

        # Mount Everest
        everest = next(w for w in gpx.wpt if "Everest" in (w.name or ""))
        assert everest.ele == Decimal("8848.86")

        # Dead Sea
        dead_sea = next(w for w in gpx.wpt if "Dead Sea" in (w.name or ""))
        assert dead_sea.ele == Decimal("-430.5")

        # Challenger Deep
        challenger = next(w for w in gpx.wpt if "Challenger" in (w.name or ""))
        assert challenger.ele == Decimal(-10994)

    def test_waypoint_with_links(self, waypoint_with_links_gpx_string: str) -> None:
        """Test parsing waypoint with multiple links."""
        gpx = from_string(waypoint_with_links_gpx_string)
        wpt = gpx.wpt[0]
        assert len(wpt.link) == 4
        assert wpt.link[0].href == "https://example.com/page1"
        assert wpt.link[0].text == "Main Website"
        assert wpt.link[0].type == "text/html"

    def test_track_single_point(self, track_single_point_gpx_string: str) -> None:
        """Test parsing track with single point in segment."""
        gpx = from_string(track_single_point_gpx_string)
        trk = gpx.trk[0]
        assert len(trk.trkseg) == 1
        assert len(trk.trkseg[0].trkpt) == 1

    def test_metadata_minimal(self, metadata_minimal_gpx_string: str) -> None:
        """Test parsing minimal metadata with only name."""
        gpx = from_string(metadata_minimal_gpx_string)
        assert gpx.metadata is not None
        assert gpx.metadata.name == "Minimal metadata"
        assert gpx.metadata.desc is None
        assert gpx.metadata.author is None

    def test_all_fix_types(self, all_fix_types_gpx_string: str) -> None:
        """Test parsing all valid fix types."""
        gpx = from_string(all_fix_types_gpx_string)
        fixes = [wpt.fix for wpt in gpx.wpt]
        assert Fix("none") in fixes
        assert Fix("2d") in fixes
        assert Fix("3d") in fixes
        assert Fix("dgps") in fixes
        assert Fix("pps") in fixes

    def test_dgps_station_boundary_values(
        self, dgps_station_values_gpx_string: str
    ) -> None:
        """Test parsing boundary DGPS station values."""
        gpx = from_string(dgps_station_values_gpx_string)
        dgps_ids = [wpt.dgpsid for wpt in gpx.wpt]
        assert DGPSStation(0) in dgps_ids
        assert DGPSStation(512) in dgps_ids
        assert DGPSStation(1023) in dgps_ids

    def test_degrees_boundary_values(self, degrees_values_gpx_string: str) -> None:
        """Test parsing boundary degrees values."""
        gpx = from_string(degrees_values_gpx_string)
        magvars = [wpt.magvar for wpt in gpx.wpt]
        assert Degrees("0") in magvars
        assert Degrees("180") in magvars
        assert Degrees("359.999") in magvars
        assert Degrees("0.001") in magvars

    def test_whitespace_content(self, whitespace_content_gpx_string: str) -> None:
        """Test parsing content with various whitespace."""
        gpx = from_string(whitespace_content_gpx_string)
        # Should parse without error
        assert gpx.metadata is not None
        assert gpx.metadata.name is not None
        assert "spaces" in gpx.metadata.name

    def test_special_characters(self, special_characters_gpx_string: str) -> None:
        """Test parsing content with XML special characters."""
        gpx = from_string(special_characters_gpx_string)
        wpt = gpx.wpt[0]
        assert wpt.name is not None
        assert wpt.desc is not None
        assert "&" in wpt.name
        assert "<" in wpt.name
        assert ">" in wpt.name
        assert '"' in wpt.desc
        assert "'" in wpt.desc

    def test_track_with_links(self, track_with_links_gpx_string: str) -> None:
        """Test parsing track with links."""
        gpx = from_string(track_with_links_gpx_string)
        trk = gpx.trk[0]
        assert len(trk.link) == 2
        assert trk.link[0].href == "https://example.com/track"

    def test_route_with_links(self, route_with_links_gpx_string: str) -> None:
        """Test parsing route with links."""
        gpx = from_string(route_with_links_gpx_string)
        rte = gpx.rte[0]
        assert len(rte.link) == 1
        assert rte.rtept[0].link[0].href == "https://example.com/start"

    def test_no_xml_declaration(self, no_xml_declaration_gpx_string: str) -> None:
        """Test parsing GPX without XML declaration."""
        gpx = from_string(no_xml_declaration_gpx_string)
        assert len(gpx.wpt) == 1
        assert gpx.wpt[0].name == "No XML declaration"

    def test_large_gpx(self, large_gpx_string: str) -> None:
        """Test parsing large GPX file."""
        gpx = from_string(large_gpx_string)
        assert gpx.metadata is not None
        trk = gpx.trk[0]
        assert len(trk.trkseg[0].trkpt) == 21


class TestInvalidEdgeCases:
    """Tests for invalid edge cases that should raise exceptions."""

    def test_missing_lat_raises_error(self, missing_lat_gpx_string: str) -> None:
        """Test that missing latitude raises ValueError."""
        with pytest.raises(ValueError, match="missing required 'lat' attribute"):
            from_string(missing_lat_gpx_string)

    def test_missing_lon_raises_error(self, missing_lon_gpx_string: str) -> None:
        """Test that missing longitude raises ValueError."""
        with pytest.raises(ValueError, match="missing required 'lon' attribute"):
            from_string(missing_lon_gpx_string)

    def test_invalid_gpx_string_raises_error(self, invalid_gpx_string: str) -> None:
        """Test that invalid GPX (missing lat/lon) raises error."""
        with pytest.raises(ValueError, match="missing required"):
            from_string(invalid_gpx_string)

    def test_lat_too_high_raises_error(self, lat_too_high_gpx_string: str) -> None:
        """Test that latitude > 90 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid latitude"):
            from_string(lat_too_high_gpx_string)

    def test_lat_too_low_raises_error(self, lat_too_low_gpx_string: str) -> None:
        """Test that latitude < -90 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid latitude"):
            from_string(lat_too_low_gpx_string)

    def test_lon_too_high_raises_error(self, lon_too_high_gpx_string: str) -> None:
        """Test that longitude > 180 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid longitude"):
            from_string(lon_too_high_gpx_string)

    def test_lon_too_low_raises_error(self, lon_too_low_gpx_string: str) -> None:
        """Test that longitude < -180 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid longitude"):
            from_string(lon_too_low_gpx_string)

    def test_invalid_fix_value_raises_error(
        self, invalid_fix_value_gpx_string: str
    ) -> None:
        """Test that invalid fix value raises ValueError."""
        with pytest.raises(ValueError, match="Invalid fix"):
            from_string(invalid_fix_value_gpx_string)

    def test_invalid_fix_uppercase_raises_error(
        self, invalid_fix_uppercase_gpx_string: str
    ) -> None:
        """Test that uppercase fix value raises ValueError."""
        with pytest.raises(ValueError, match="Invalid fix"):
            from_string(invalid_fix_uppercase_gpx_string)

    def test_dgps_station_too_high_raises_error(
        self, dgps_station_too_high_gpx_string: str
    ) -> None:
        """Test that DGPS station ID > 1023 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid DGPS station"):
            from_string(dgps_station_too_high_gpx_string)

    def test_dgps_station_negative_raises_error(
        self, dgps_station_negative_gpx_string: str
    ) -> None:
        """Test that negative DGPS station ID raises ValueError."""
        with pytest.raises(ValueError, match="Invalid DGPS station"):
            from_string(dgps_station_negative_gpx_string)

    def test_degrees_too_high_raises_error(
        self, degrees_too_high_gpx_string: str
    ) -> None:
        """Test that degrees >= 360 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid degrees"):
            from_string(degrees_too_high_gpx_string)

    def test_degrees_negative_raises_error(
        self, degrees_negative_gpx_string: str
    ) -> None:
        """Test that negative degrees raises ValueError."""
        with pytest.raises(ValueError, match="Invalid degrees"):
            from_string(degrees_negative_gpx_string)

    def test_malformed_xml_raises_error(self, malformed_xml_gpx_string: str) -> None:
        """Test that malformed XML raises ParseError."""
        with pytest.raises(ET.ParseError):
            from_string(malformed_xml_gpx_string)

    def test_missing_bounds_minlat_raises_error(
        self, missing_bounds_minlat_gpx_string: str
    ) -> None:
        """Test that bounds missing minlat raises ValueError."""
        with pytest.raises(ValueError, match="missing required 'minlat' attribute"):
            from_string(missing_bounds_minlat_gpx_string)

    def test_missing_email_id_raises_error(
        self, missing_email_id_gpx_string: str
    ) -> None:
        """Test that email missing id raises ValueError."""
        with pytest.raises(ValueError, match="missing required 'id' attribute"):
            from_string(missing_email_id_gpx_string)

    def test_missing_email_domain_raises_error(
        self, missing_email_domain_gpx_string: str
    ) -> None:
        """Test that email missing domain raises ValueError."""
        with pytest.raises(ValueError, match="missing required 'domain' attribute"):
            from_string(missing_email_domain_gpx_string)

    def test_missing_link_href_raises_error(
        self, missing_link_href_gpx_string: str
    ) -> None:
        """Test that link missing href raises ValueError."""
        with pytest.raises(ValueError, match="missing required 'href' attribute"):
            from_string(missing_link_href_gpx_string)

    def test_missing_copyright_author_raises_error(
        self, missing_copyright_author_gpx_string: str
    ) -> None:
        """Test that copyright missing author raises ValueError."""
        with pytest.raises(ValueError, match="missing required 'author' attribute"):
            from_string(missing_copyright_author_gpx_string)

    def test_non_numeric_lat_raises_error(
        self, non_numeric_lat_gpx_string: str
    ) -> None:
        """Test that non-numeric latitude raises ValueError."""
        with pytest.raises(ValueError, match="Invalid latitude"):
            from_string(non_numeric_lat_gpx_string)

    def test_non_numeric_lon_raises_error(
        self, non_numeric_lon_gpx_string: str
    ) -> None:
        """Test that non-numeric longitude raises ValueError."""
        with pytest.raises(ValueError, match="Invalid longitude"):
            from_string(non_numeric_lon_gpx_string)

    def test_non_numeric_elevation_raises_error(
        self, non_numeric_elevation_gpx_string: str
    ) -> None:
        """Test that non-numeric elevation raises error."""
        with pytest.raises(InvalidOperation):
            from_string(non_numeric_elevation_gpx_string)

    def test_empty_file_raises_error(self, empty_file_gpx_string: str) -> None:
        """Test that empty file raises ParseError."""
        with pytest.raises(ET.ParseError):
            from_string(empty_file_gpx_string)

    def test_missing_trkpt_lat_raises_error(
        self, missing_trkpt_lat_gpx_string: str
    ) -> None:
        """Test that track point missing latitude raises ValueError."""
        with pytest.raises(ValueError, match="missing required 'lat' attribute"):
            from_string(missing_trkpt_lat_gpx_string)

    def test_missing_rtept_lat_raises_error(
        self, missing_rtept_lat_gpx_string: str
    ) -> None:
        """Test that route point missing latitude raises ValueError."""
        with pytest.raises(ValueError, match="missing required 'lat' attribute"):
            from_string(missing_rtept_lat_gpx_string)


class TestRoundtripEdgeCases:
    """Tests for roundtrip (parse -> serialize -> parse) edge cases."""

    def test_roundtrip_preserves_high_precision(
        self, high_precision_coords_gpx_string: str
    ) -> None:
        """Test that roundtrip preserves high precision coordinates."""
        gpx1 = from_string(high_precision_coords_gpx_string)
        output = gpx1.to_string()
        gpx2 = from_string(output)

        assert gpx2.wpt[0].lat == gpx1.wpt[0].lat
        assert gpx2.wpt[0].lon == gpx1.wpt[0].lon
        assert gpx2.wpt[0].ele == gpx1.wpt[0].ele

    def test_roundtrip_preserves_unicode(self, unicode_content_gpx_string: str) -> None:
        """Test that roundtrip preserves Unicode content."""
        gpx1 = from_string(unicode_content_gpx_string)
        output = gpx1.to_string()
        gpx2 = from_string(output)

        assert gpx2.metadata is not None
        assert gpx1.metadata is not None
        assert gpx2.metadata.name == gpx1.metadata.name

        for i, wpt in enumerate(gpx2.wpt):
            assert wpt.name == gpx1.wpt[i].name
            assert wpt.desc == gpx1.wpt[i].desc

    def test_roundtrip_preserves_special_characters(
        self, special_characters_gpx_string: str
    ) -> None:
        """Test that roundtrip preserves special XML characters."""
        gpx1 = from_string(special_characters_gpx_string)
        output = gpx1.to_string()
        gpx2 = from_string(output)

        assert gpx2.wpt[0].name == gpx1.wpt[0].name
        assert gpx2.wpt[0].desc == gpx1.wpt[0].desc
        assert gpx2.wpt[0].cmt == gpx1.wpt[0].cmt

    def test_roundtrip_preserves_all_waypoint_fields(
        self, waypoint_all_fields_gpx_string: str
    ) -> None:
        """Test that roundtrip preserves all waypoint fields."""
        gpx1 = from_string(waypoint_all_fields_gpx_string)
        output = gpx1.to_string()
        gpx2 = from_string(output)

        wpt1 = gpx1.wpt[0]
        wpt2 = gpx2.wpt[0]

        assert wpt2.lat == wpt1.lat
        assert wpt2.lon == wpt1.lon
        assert wpt2.ele == wpt1.ele
        assert wpt2.magvar == wpt1.magvar
        assert wpt2.geoidheight == wpt1.geoidheight
        assert wpt2.name == wpt1.name
        assert wpt2.cmt == wpt1.cmt
        assert wpt2.desc == wpt1.desc
        assert wpt2.src == wpt1.src
        assert len(wpt2.link) == len(wpt1.link)
        assert wpt2.sym == wpt1.sym
        assert wpt2.type == wpt1.type
        assert wpt2.fix == wpt1.fix
        assert wpt2.sat == wpt1.sat
        assert wpt2.hdop == wpt1.hdop
        assert wpt2.vdop == wpt1.vdop
        assert wpt2.pdop == wpt1.pdop
        assert wpt2.ageofdgpsdata == wpt1.ageofdgpsdata
        assert wpt2.dgpsid == wpt1.dgpsid

    def test_roundtrip_preserves_empty_structures(
        self, empty_track_gpx_string: str
    ) -> None:
        """Test that roundtrip preserves empty tracks/routes."""
        gpx1 = from_string(empty_track_gpx_string)
        output = gpx1.to_string()
        gpx2 = from_string(output)

        assert len(gpx2.trk) == 1
        assert gpx2.trk[0].name == gpx1.trk[0].name
        assert len(gpx2.trk[0].trkseg) == 0

    def test_roundtrip_preserves_extreme_elevations(
        self, extreme_elevations_gpx_string: str
    ) -> None:
        """Test that roundtrip preserves extreme elevation values."""
        gpx1 = from_string(extreme_elevations_gpx_string)
        output = gpx1.to_string()
        gpx2 = from_string(output)

        for i, wpt in enumerate(gpx2.wpt):
            assert wpt.ele == gpx1.wpt[i].ele
