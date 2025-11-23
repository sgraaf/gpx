"""Pytest configuration and fixtures for GPX tests."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from gpx import (
    GPX,
    Bounds,
    Copyright,
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
def minimal_gpx_string():
    """A minimal valid GPX string."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
     version="1.1"
     creator="TestCreator">
</gpx>"""


@pytest.fixture
def gpx_with_waypoint_string():
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
def gpx_with_track_string():
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
def gpx_with_route_string():
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
def gpx_with_metadata_string():
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
def full_gpx_string():
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
def invalid_gpx_string():
    """An invalid GPX string (missing required attributes)."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1">
  <wpt>
    <name>Missing lat/lon</name>
  </wpt>
</gpx>"""


@pytest.fixture
def sample_waypoint():
    """Create a sample waypoint programmatically."""
    wpt = Waypoint()
    wpt.lat = Latitude("52.5200")
    wpt.lon = Longitude("13.4050")
    wpt.ele = Decimal("34.5")
    wpt.time = datetime(2023, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
    wpt.name = "Berlin"
    wpt.desc = "Capital of Germany"
    return wpt


@pytest.fixture
def sample_waypoints_for_track():
    """Create sample waypoints for track/route testing with timestamps."""
    waypoints = []
    coords = [
        ("52.5200", "13.4050", "34.5", "2023-06-15T06:00:00Z"),
        ("52.5210", "13.4060", "35.0", "2023-06-15T06:01:00Z"),
        ("52.5220", "13.4070", "36.5", "2023-06-15T06:02:00Z"),
        ("52.5230", "13.4080", "35.5", "2023-06-15T06:03:00Z"),
    ]
    for lat, lon, ele, time_str in coords:
        wpt = Waypoint()
        wpt.lat = Latitude(lat)
        wpt.lon = Longitude(lon)
        wpt.ele = Decimal(ele)
        wpt.time = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        waypoints.append(wpt)
    return waypoints


@pytest.fixture
def sample_track_segment(sample_waypoints_for_track):
    """Create a sample track segment."""
    seg = TrackSegment()
    seg.trkpts = sample_waypoints_for_track
    seg.points = seg.trkpts
    return seg


@pytest.fixture
def sample_track(sample_track_segment):
    """Create a sample track."""
    track = Track()
    track.name = "Test Track"
    track.desc = "A test track"
    track.trksegs = [sample_track_segment]
    track.segments = track.trksegs
    return track


@pytest.fixture
def sample_route(sample_waypoints_for_track):
    """Create a sample route."""
    route = Route()
    route.name = "Test Route"
    route.desc = "A test route"
    route.rtepts = sample_waypoints_for_track
    route.points = route.rtepts
    return route


@pytest.fixture
def sample_metadata():
    """Create a sample metadata object."""
    metadata = Metadata()
    metadata.name = "Test GPX"
    metadata.desc = "A test GPX file"
    metadata.time = datetime(2023, 6, 15, 10, 0, 0, tzinfo=timezone.utc)
    metadata.keywords = "test, gpx"
    return metadata


@pytest.fixture
def sample_link():
    """Create a sample link object."""
    link = Link()
    link.href = "https://example.com"
    link.text = "Example Link"
    link.type = "text/html"
    return link


@pytest.fixture
def sample_person():
    """Create a sample person object."""
    person = Person()
    person.name = "Test Author"
    email = Email()
    email.id = "test"
    email.domain = "example.com"
    person.email = email
    return person


@pytest.fixture
def sample_bounds():
    """Create a sample bounds object."""
    bounds = Bounds()
    bounds.minlat = Latitude("52.5")
    bounds.minlon = Longitude("13.4")
    bounds.maxlat = Latitude("52.6")
    bounds.maxlon = Longitude("13.5")
    return bounds
