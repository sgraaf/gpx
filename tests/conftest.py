"""Pytest configuration and fixtures for GPX tests."""

import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from gpx import (
    Bounds,
    Email,
    Link,
    Metadata,
    Person,
    Route,
    Track,
    TrackSegment,
    Waypoint,
)
from gpx.types import Latitude, Longitude
from gpx.utils import from_isoformat

#: GPX 1.1 namespace
GPX_NAMESPACE = "http://www.topografix.com/GPX/1/1"

#: Path to test fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"
VALID_FIXTURES_DIR = FIXTURES_DIR / "valid"
INVALID_FIXTURES_DIR = FIXTURES_DIR / "invalid"


def find_gpx(element: ET.Element, tag: str) -> ET.Element | None:
    """Find a child element in the GPX namespace.

    Args:
        element: The parent element to search in.
        tag: The tag name (without namespace).

    Returns:
        The found element, or None if not found.

    """
    return element.find(f"{{{GPX_NAMESPACE}}}{tag}")


def findall_gpx(element: ET.Element, tag: str) -> list[ET.Element]:
    """Find all child elements in the GPX namespace.

    Args:
        element: The parent element to search in.
        tag: The tag name (without namespace).

    Returns:
        List of found elements.

    """
    return element.findall(f"{{{GPX_NAMESPACE}}}{tag}")


def load_fixture(fixture_path: Path) -> str:
    """Load a GPX fixture file as a string.

    Args:
        fixture_path: Path to the fixture file.

    Returns:
        The contents of the fixture file.

    """
    return fixture_path.read_text(encoding="utf-8")


# =============================================================================
# GPX string fixtures (loaded from files)
# =============================================================================


@pytest.fixture
def minimal_gpx_string() -> str:
    """A minimal valid GPX string."""
    return load_fixture(VALID_FIXTURES_DIR / "minimal.gpx")


@pytest.fixture
def gpx_with_waypoint_string() -> str:
    """A GPX string with a single waypoint."""
    return load_fixture(VALID_FIXTURES_DIR / "waypoint.gpx")


@pytest.fixture
def gpx_with_track_string() -> str:
    """A GPX string with a track containing multiple segments and points."""
    return load_fixture(VALID_FIXTURES_DIR / "track.gpx")


@pytest.fixture
def gpx_with_route_string() -> str:
    """A GPX string with a route."""
    return load_fixture(VALID_FIXTURES_DIR / "route.gpx")


@pytest.fixture
def gpx_with_metadata_string() -> str:
    """A GPX string with full metadata."""
    return load_fixture(VALID_FIXTURES_DIR / "metadata.gpx")


@pytest.fixture
def full_gpx_string() -> str:
    """A comprehensive GPX string with all element types."""
    return load_fixture(VALID_FIXTURES_DIR / "full.gpx")


@pytest.fixture
def invalid_gpx_string() -> str:
    """An invalid GPX string (missing required attributes)."""
    return load_fixture(INVALID_FIXTURES_DIR / "missing_lat_lon.gpx")


# =============================================================================
# GeoJSON interface fixtures
# =============================================================================


@pytest.fixture
def waypoint_geo_interface() -> dict[str, Any]:
    """A GeoJSON-like dict for a waypoint."""
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [13.405, 52.52, 34.5]},
        "properties": {
            "time": "2023-06-15T10:30:00Z",
            "name": "Berlin",
            "cmt": "A comment",
            "desc": "Capital of Germany",
            "src": "Manual",
            "sym": "City",
            "type": "City",
            "fix": "3d",
            "sat": 8.0,
            "hdop": 1.2,
            "vdop": 1.5,
            "pdop": 1.8,
        },
    }


@pytest.fixture
def track_geo_interface() -> dict[str, Any]:
    """A GeoJSON-like dict for a track."""
    return {
        "type": "Feature",
        "geometry": {
            "type": "MultiLineString",
            "coordinates": [
                [[13.405, 52.52, 34.5], [13.406, 52.521, 35.0], [13.407, 52.522, 36.5]],
                [[13.408, 52.523, 35.5], [13.409, 52.524, 34.0]],
            ],
            "bbox": [13.405, 52.52, 34.0, 13.409, 52.524, 36.5],
        },
        "properties": {
            "name": "Morning Run",
            "cmt": "Good weather",
            "desc": "A morning run through the park",
            "src": "Garmin",
            "number": 1.0,
            "type": "Running",
        },
    }


@pytest.fixture
def track_segment_geo_interface() -> dict[str, Any]:
    """A GeoJSON-like dict for a track segment."""
    return {
        "type": "LineString",
        "coordinates": [
            [13.405, 52.52, 34.5],
            [13.406, 52.521, 35.0],
            [13.407, 52.522, 36.5],
        ],
        "bbox": [13.405, 52.52, 34.5, 13.407, 52.522, 36.5],
    }


@pytest.fixture
def route_geo_interface() -> dict[str, Any]:
    """A GeoJSON-like dict for a route."""
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [13.405, 52.52, 34.5],
                [13.415, 52.53, 40.0],
                [13.425, 52.54, 38.0],
            ],
            "bbox": [13.405, 52.52, 34.5, 13.425, 52.54, 40.0],
        },
        "properties": {
            "name": "City Tour",
            "cmt": "Best route",
            "desc": "A tour of the city",
            "src": "Planned",
            "number": 1.0,
            "type": "Tourism",
        },
    }


@pytest.fixture
def full_gpx_geo_interface() -> dict[str, Any]:
    """A GeoJSON-like dict for a gpx."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [13.405, 52.52, 34.5]},
                "properties": {"name": "Waypoint 1"},
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [13.415, 52.53, 35.0]},
                "properties": {"name": "Waypoint 2"},
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[13.405, 52.52, 34.5], [13.415, 52.53, 35.0]],
                    "bbox": [13.405, 52.52, 34.5, 13.415, 52.53, 35.0],
                },
                "properties": {"name": "Test Route"},
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": [[[13.405, 52.52, 34.5], [13.406, 52.521, 35.0]]],
                    "bbox": [13.405, 52.52, 34.5, 13.406, 52.521, 35.0],
                },
                "properties": {"name": "Test Track"},
            },
        ],
    }


# =============================================================================
# Programmatically created fixtures
# =============================================================================


@pytest.fixture
def sample_waypoint() -> Waypoint:
    """Create a sample waypoint programmatically."""
    return Waypoint(
        lat=Latitude("52.5200"),
        lon=Longitude("13.4050"),
        ele=Decimal("34.5"),
        time=datetime(2023, 6, 15, 10, 30, 0, tzinfo=UTC),
        name="Berlin",
        desc="Capital of Germany",
    )


@pytest.fixture
def sample_waypoints_for_track() -> list[Waypoint]:
    """Create sample waypoints for track/route testing with timestamps."""
    coords = [
        ("52.5200", "13.4050", "34.5", "2023-06-15T06:00:00Z"),
        ("52.5210", "13.4060", "35.0", "2023-06-15T06:01:00Z"),
        ("52.5220", "13.4070", "36.5", "2023-06-15T06:02:00Z"),
        ("52.5230", "13.4080", "35.5", "2023-06-15T06:03:00Z"),
    ]
    return [
        Waypoint(
            lat=Latitude(lat),
            lon=Longitude(lon),
            ele=Decimal(ele),
            time=from_isoformat(time_str),
        )
        for lat, lon, ele, time_str in coords
    ]


@pytest.fixture
def sample_track_segment(sample_waypoints_for_track: list[Waypoint]) -> TrackSegment:
    """Create a sample track segment."""
    return TrackSegment(trkpt=sample_waypoints_for_track)


@pytest.fixture
def sample_track(sample_track_segment: TrackSegment) -> Track:
    """Create a sample track."""
    return Track(
        name="Test Track",
        desc="A test track",
        trkseg=[sample_track_segment],
    )


@pytest.fixture
def sample_route(sample_waypoints_for_track: list[Waypoint]) -> Route:
    """Create a sample route."""
    return Route(
        name="Test Route",
        desc="A test route",
        rtept=sample_waypoints_for_track,
    )


@pytest.fixture
def sample_metadata() -> Metadata:
    """Create a sample metadata object."""
    return Metadata(
        name="Test GPX",
        desc="A test GPX file",
        time=datetime(2023, 6, 15, 10, 0, 0, tzinfo=UTC),
        keywords="test, gpx",
    )


@pytest.fixture
def sample_link() -> Link:
    """Create a sample link object."""
    return Link(
        href="https://example.com",
        text="Example Link",
        type="text/html",
    )


@pytest.fixture
def sample_person() -> Person:
    """Create a sample person object."""
    return Person(
        name="Test Author",
        email=Email(id="test", domain="example.com"),
    )


@pytest.fixture
def sample_bounds() -> Bounds:
    """Create a sample bounds object."""
    return Bounds(
        minlat=Latitude("52.5"),
        minlon=Longitude("13.4"),
        maxlat=Latitude("52.6"),
        maxlon=Longitude("13.5"),
    )


# =============================================================================
# Edge case fixtures (valid)
# =============================================================================


@pytest.fixture
def waypoint_minimal_gpx_string() -> str:
    """A GPX string with a minimal waypoint (only lat/lon)."""
    return load_fixture(VALID_FIXTURES_DIR / "waypoint_minimal.gpx")


@pytest.fixture
def waypoint_all_fields_gpx_string() -> str:
    """A GPX string with a waypoint containing all possible fields."""
    return load_fixture(VALID_FIXTURES_DIR / "waypoint_all_fields.gpx")


@pytest.fixture
def multiple_waypoints_gpx_string() -> str:
    """A GPX string with many waypoints."""
    return load_fixture(VALID_FIXTURES_DIR / "multiple_waypoints.gpx")


@pytest.fixture
def multiple_tracks_gpx_string() -> str:
    """A GPX string with multiple tracks."""
    return load_fixture(VALID_FIXTURES_DIR / "multiple_tracks.gpx")


@pytest.fixture
def multiple_routes_gpx_string() -> str:
    """A GPX string with multiple routes."""
    return load_fixture(VALID_FIXTURES_DIR / "multiple_routes.gpx")


@pytest.fixture
def empty_track_segment_gpx_string() -> str:
    """A GPX string with a track containing an empty segment."""
    return load_fixture(VALID_FIXTURES_DIR / "empty_track_segment.gpx")


@pytest.fixture
def empty_track_gpx_string() -> str:
    """A GPX string with an empty track (no segments)."""
    return load_fixture(VALID_FIXTURES_DIR / "empty_track.gpx")


@pytest.fixture
def empty_route_gpx_string() -> str:
    """A GPX string with an empty route (no points)."""
    return load_fixture(VALID_FIXTURES_DIR / "empty_route.gpx")


@pytest.fixture
def boundary_coords_gpx_string() -> str:
    """A GPX string with boundary coordinate values."""
    return load_fixture(VALID_FIXTURES_DIR / "boundary_coords.gpx")


@pytest.fixture
def high_precision_coords_gpx_string() -> str:
    """A GPX string with high precision coordinates."""
    return load_fixture(VALID_FIXTURES_DIR / "high_precision_coords.gpx")


@pytest.fixture
def time_formats_gpx_string() -> str:
    """A GPX string with various time formats."""
    return load_fixture(VALID_FIXTURES_DIR / "time_formats.gpx")


@pytest.fixture
def unicode_content_gpx_string() -> str:
    """A GPX string with Unicode content."""
    return load_fixture(VALID_FIXTURES_DIR / "unicode_content.gpx")


@pytest.fixture
def extreme_elevations_gpx_string() -> str:
    """A GPX string with extreme elevation values."""
    return load_fixture(VALID_FIXTURES_DIR / "extreme_elevations.gpx")


@pytest.fixture
def waypoint_with_links_gpx_string() -> str:
    """A GPX string with a waypoint containing multiple links."""
    return load_fixture(VALID_FIXTURES_DIR / "waypoint_with_links.gpx")


@pytest.fixture
def track_single_point_gpx_string() -> str:
    """A GPX string with a track containing a single point."""
    return load_fixture(VALID_FIXTURES_DIR / "track_single_point.gpx")


@pytest.fixture
def metadata_minimal_gpx_string() -> str:
    """A GPX string with minimal metadata."""
    return load_fixture(VALID_FIXTURES_DIR / "metadata_minimal.gpx")


@pytest.fixture
def all_fix_types_gpx_string() -> str:
    """A GPX string with all valid fix types."""
    return load_fixture(VALID_FIXTURES_DIR / "all_fix_types.gpx")


@pytest.fixture
def dgps_station_values_gpx_string() -> str:
    """A GPX string with boundary DGPS station values."""
    return load_fixture(VALID_FIXTURES_DIR / "dgps_station_values.gpx")


@pytest.fixture
def degrees_values_gpx_string() -> str:
    """A GPX string with boundary degrees values."""
    return load_fixture(VALID_FIXTURES_DIR / "degrees_values.gpx")


@pytest.fixture
def whitespace_content_gpx_string() -> str:
    """A GPX string with various whitespace in content."""
    return load_fixture(VALID_FIXTURES_DIR / "whitespace_content.gpx")


@pytest.fixture
def special_characters_gpx_string() -> str:
    """A GPX string with special XML characters."""
    return load_fixture(VALID_FIXTURES_DIR / "special_characters.gpx")


@pytest.fixture
def track_with_links_gpx_string() -> str:
    """A GPX string with a track containing links."""
    return load_fixture(VALID_FIXTURES_DIR / "track_with_links.gpx")


@pytest.fixture
def route_with_links_gpx_string() -> str:
    """A GPX string with a route containing links."""
    return load_fixture(VALID_FIXTURES_DIR / "route_with_links.gpx")


@pytest.fixture
def no_xml_declaration_gpx_string() -> str:
    """A GPX string without an XML declaration."""
    return load_fixture(VALID_FIXTURES_DIR / "no_xml_declaration.gpx")


@pytest.fixture
def large_gpx_string() -> str:
    """A GPX string with many elements."""
    return load_fixture(VALID_FIXTURES_DIR / "large_gpx.gpx")


# =============================================================================
# Edge case fixtures (invalid)
# =============================================================================


@pytest.fixture
def missing_lat_gpx_string() -> str:
    """A GPX string with a waypoint missing latitude."""
    return load_fixture(INVALID_FIXTURES_DIR / "missing_lat.gpx")


@pytest.fixture
def missing_lon_gpx_string() -> str:
    """A GPX string with a waypoint missing longitude."""
    return load_fixture(INVALID_FIXTURES_DIR / "missing_lon.gpx")


@pytest.fixture
def lat_too_high_gpx_string() -> str:
    """A GPX string with latitude > 90."""
    return load_fixture(INVALID_FIXTURES_DIR / "lat_too_high.gpx")


@pytest.fixture
def lat_too_low_gpx_string() -> str:
    """A GPX string with latitude < -90."""
    return load_fixture(INVALID_FIXTURES_DIR / "lat_too_low.gpx")


@pytest.fixture
def lon_too_high_gpx_string() -> str:
    """A GPX string with longitude > 180."""
    return load_fixture(INVALID_FIXTURES_DIR / "lon_too_high.gpx")


@pytest.fixture
def lon_too_low_gpx_string() -> str:
    """A GPX string with longitude < -180."""
    return load_fixture(INVALID_FIXTURES_DIR / "lon_too_low.gpx")


@pytest.fixture
def invalid_fix_value_gpx_string() -> str:
    """A GPX string with an invalid fix value."""
    return load_fixture(INVALID_FIXTURES_DIR / "invalid_fix_value.gpx")


@pytest.fixture
def invalid_fix_uppercase_gpx_string() -> str:
    """A GPX string with an uppercase fix value."""
    return load_fixture(INVALID_FIXTURES_DIR / "invalid_fix_uppercase.gpx")


@pytest.fixture
def dgps_station_too_high_gpx_string() -> str:
    """A GPX string with DGPS station ID > 1023."""
    return load_fixture(INVALID_FIXTURES_DIR / "dgps_station_too_high.gpx")


@pytest.fixture
def dgps_station_negative_gpx_string() -> str:
    """A GPX string with negative DGPS station ID."""
    return load_fixture(INVALID_FIXTURES_DIR / "dgps_station_negative.gpx")


@pytest.fixture
def degrees_too_high_gpx_string() -> str:
    """A GPX string with degrees >= 360."""
    return load_fixture(INVALID_FIXTURES_DIR / "degrees_too_high.gpx")


@pytest.fixture
def degrees_negative_gpx_string() -> str:
    """A GPX string with negative degrees."""
    return load_fixture(INVALID_FIXTURES_DIR / "degrees_negative.gpx")


@pytest.fixture
def malformed_xml_gpx_string() -> str:
    """A GPX string with malformed XML."""
    return load_fixture(INVALID_FIXTURES_DIR / "malformed_xml.gpx")


@pytest.fixture
def missing_bounds_minlat_gpx_string() -> str:
    """A GPX string with bounds missing minlat."""
    return load_fixture(INVALID_FIXTURES_DIR / "missing_bounds_minlat.gpx")


@pytest.fixture
def missing_email_id_gpx_string() -> str:
    """A GPX string with email missing id."""
    return load_fixture(INVALID_FIXTURES_DIR / "missing_email_id.gpx")


@pytest.fixture
def missing_email_domain_gpx_string() -> str:
    """A GPX string with email missing domain."""
    return load_fixture(INVALID_FIXTURES_DIR / "missing_email_domain.gpx")


@pytest.fixture
def missing_link_href_gpx_string() -> str:
    """A GPX string with link missing href."""
    return load_fixture(INVALID_FIXTURES_DIR / "missing_link_href.gpx")


@pytest.fixture
def missing_copyright_author_gpx_string() -> str:
    """A GPX string with copyright missing author."""
    return load_fixture(INVALID_FIXTURES_DIR / "missing_copyright_author.gpx")


@pytest.fixture
def non_numeric_lat_gpx_string() -> str:
    """A GPX string with non-numeric latitude."""
    return load_fixture(INVALID_FIXTURES_DIR / "non_numeric_lat.gpx")


@pytest.fixture
def non_numeric_lon_gpx_string() -> str:
    """A GPX string with non-numeric longitude."""
    return load_fixture(INVALID_FIXTURES_DIR / "non_numeric_lon.gpx")


@pytest.fixture
def non_numeric_elevation_gpx_string() -> str:
    """A GPX string with non-numeric elevation."""
    return load_fixture(INVALID_FIXTURES_DIR / "non_numeric_elevation.gpx")


@pytest.fixture
def empty_file_gpx_string() -> str:
    """An empty GPX file."""
    return load_fixture(INVALID_FIXTURES_DIR / "empty_file.gpx")


@pytest.fixture
def not_gpx_root_gpx_string() -> str:
    """A GPX string with wrong root element."""
    return load_fixture(INVALID_FIXTURES_DIR / "not_gpx_root.gpx")


@pytest.fixture
def missing_trkpt_lat_gpx_string() -> str:
    """A GPX string with track point missing latitude."""
    return load_fixture(INVALID_FIXTURES_DIR / "missing_trkpt_lat.gpx")


@pytest.fixture
def missing_rtept_lat_gpx_string() -> str:
    """A GPX string with route point missing latitude."""
    return load_fixture(INVALID_FIXTURES_DIR / "missing_rtept_lat.gpx")
