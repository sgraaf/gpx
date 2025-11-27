"""Pytest configuration and fixtures for GPX tests."""

from datetime import UTC, datetime
from decimal import Decimal

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


@pytest.fixture
def minimal_gpx_string() -> str:
    """A minimal valid GPX string."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
     version="1.1"
     creator="TestCreator">
</gpx>"""


@pytest.fixture
def gpx_with_waypoint_string() -> str:
    """A GPX string with a single waypoint."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
     version="1.1"
     creator="TestCreator">
  <wpt lat="52.5200" lon="13.4050">
    <ele>34.5</ele>
    <time>2023-06-15T10:30:00Z</time>
    <name>Berlin</name>
    <desc>Capital of Germany</desc>
    <cmt>A comment</cmt>
    <src>Manual</src>
    <sym>City</sym>
    <type>City</type>
    <fix>3d</fix>
    <sat>8</sat>
    <hdop>1.2</hdop>
    <vdop>1.5</vdop>
    <pdop>1.8</pdop>
  </wpt>
</gpx>"""


@pytest.fixture
def gpx_with_track_string() -> str:
    """A GPX string with a track containing multiple segments and points."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
     version="1.1"
     creator="TestCreator">
  <trk>
    <name>Morning Run</name>
    <desc>A morning run through the park</desc>
    <cmt>Good weather</cmt>
    <src>Garmin</src>
    <number>1</number>
    <type>Running</type>
    <trkseg>
      <trkpt lat="52.5200" lon="13.4050">
        <ele>34.5</ele>
        <time>2023-06-15T06:00:00Z</time>
      </trkpt>
      <trkpt lat="52.5210" lon="13.4060">
        <ele>35.0</ele>
        <time>2023-06-15T06:01:00Z</time>
      </trkpt>
      <trkpt lat="52.5220" lon="13.4070">
        <ele>36.5</ele>
        <time>2023-06-15T06:02:00Z</time>
      </trkpt>
    </trkseg>
    <trkseg>
      <trkpt lat="52.5230" lon="13.4080">
        <ele>35.5</ele>
        <time>2023-06-15T06:05:00Z</time>
      </trkpt>
      <trkpt lat="52.5240" lon="13.4090">
        <ele>34.0</ele>
        <time>2023-06-15T06:06:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""


@pytest.fixture
def gpx_with_route_string() -> str:
    """A GPX string with a route."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
     version="1.1"
     creator="TestCreator">
  <rte>
    <name>City Tour</name>
    <desc>A tour of the city</desc>
    <cmt>Best route</cmt>
    <src>Planned</src>
    <number>1</number>
    <type>Tourism</type>
    <rtept lat="52.5200" lon="13.4050">
      <ele>34.5</ele>
      <time>2023-06-15T10:00:00Z</time>
      <name>Start</name>
    </rtept>
    <rtept lat="52.5300" lon="13.4150">
      <ele>40.0</ele>
      <time>2023-06-15T11:00:00Z</time>
      <name>Checkpoint</name>
    </rtept>
    <rtept lat="52.5400" lon="13.4250">
      <ele>38.0</ele>
      <time>2023-06-15T12:00:00Z</time>
      <name>End</name>
    </rtept>
  </rte>
</gpx>"""


@pytest.fixture
def gpx_with_metadata_string() -> str:
    """A GPX string with full metadata."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
     version="1.1"
     creator="TestCreator">
  <metadata>
    <name>Test GPX File</name>
    <desc>A test GPX file for unit testing</desc>
    <author>
      <name>Test Author</name>
      <email id="test" domain="example.com"/>
      <link href="https://example.com">
        <text>Author Website</text>
        <type>text/html</type>
      </link>
    </author>
    <copyright author="Test Author">
      <year>2023</year>
      <license>https://creativecommons.org/licenses/by/4.0/</license>
    </copyright>
    <link href="https://example.com/gpx">
      <text>GPX File Link</text>
      <type>text/html</type>
    </link>
    <time>2023-06-15T10:00:00Z</time>
    <keywords>test, gpx, example</keywords>
    <bounds minlat="52.5" minlon="13.4" maxlat="52.6" maxlon="13.5"/>
  </metadata>
</gpx>"""


@pytest.fixture
def full_gpx_string() -> str:
    """A comprehensive GPX string with all element types."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
     version="1.1"
     creator="TestCreator">
  <metadata>
    <name>Full Test GPX</name>
    <desc>A comprehensive test file</desc>
    <time>2023-06-15T10:00:00Z</time>
  </metadata>
  <wpt lat="52.5200" lon="13.4050">
    <ele>34.5</ele>
    <name>Waypoint 1</name>
  </wpt>
  <wpt lat="52.5300" lon="13.4150">
    <ele>35.0</ele>
    <name>Waypoint 2</name>
  </wpt>
  <rte>
    <name>Test Route</name>
    <rtept lat="52.5200" lon="13.4050">
      <ele>34.5</ele>
      <time>2023-06-15T10:00:00Z</time>
    </rtept>
    <rtept lat="52.5300" lon="13.4150">
      <ele>35.0</ele>
      <time>2023-06-15T11:00:00Z</time>
    </rtept>
  </rte>
  <trk>
    <name>Test Track</name>
    <trkseg>
      <trkpt lat="52.5200" lon="13.4050">
        <ele>34.5</ele>
        <time>2023-06-15T06:00:00Z</time>
      </trkpt>
      <trkpt lat="52.5210" lon="13.4060">
        <ele>35.0</ele>
        <time>2023-06-15T06:01:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""


@pytest.fixture
def invalid_gpx_string() -> str:
    """An invalid GPX string (missing required attributes)."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1">
  <wpt>
    <name>Missing lat/lon</name>
  </wpt>
</gpx>"""


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
            time=datetime.fromisoformat(time_str),
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
