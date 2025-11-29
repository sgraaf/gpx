"""Tests for the io module."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from gpx import GPX, Metadata, Route, Track, TrackSegment, Waypoint
from gpx.io import (
    from_file,
    from_geojson,
    from_geojson_dict,
    from_kml,
    from_string,
    to_file,
    to_geojson,
    to_geojson_dict,
    to_kml,
    to_string,
)
from gpx.types import Latitude, Longitude


def test_from_string():
    """Test from_string function."""
    gpx_str = """<?xml version="1.0"?>
    <gpx version="1.1" creator="MyApp"
         xmlns="http://www.topografix.com/GPX/1/1">
        <metadata><name>My Track</name></metadata>
    </gpx>"""

    gpx = from_string(gpx_str)
    assert gpx.creator == "MyApp"
    assert gpx.metadata is not None
    assert gpx.metadata.name == "My Track"


def test_to_string():
    """Test to_string function."""
    gpx = GPX(creator="MyApp", metadata=Metadata(name="Test"))
    gpx_str = to_string(gpx)

    assert '<?xml version' in gpx_str
    assert 'creator="MyApp"' in gpx_str
    assert "<name>Test</name>" in gpx_str


def test_from_file_to_file(tmp_path: Path):
    """Test from_file and to_file functions."""
    # Create a GPX file
    gpx = GPX(creator="TestApp", metadata=Metadata(name="Test Track"))
    test_file = tmp_path / "test.gpx"

    to_file(gpx, test_file)
    assert test_file.exists()

    # Read it back
    gpx2 = from_file(test_file)
    assert gpx2.creator == "TestApp"
    assert gpx2.metadata is not None
    assert gpx2.metadata.name == "Test Track"


def test_to_geojson_dict_empty():
    """Test to_geojson_dict with empty GPX."""
    gpx = GPX(creator="Test")
    geojson = to_geojson_dict(gpx)

    assert geojson["type"] == "FeatureCollection"
    assert geojson["features"] == []


def test_to_geojson_dict_waypoint():
    """Test to_geojson_dict with a waypoint."""
    waypoint = Waypoint(
        lat=Latitude("52.3676"),
        lon=Longitude("4.9041"),
        name="Amsterdam",
        ele=Decimal("2.0"),
    )
    gpx = GPX(creator="Test", wpt=[waypoint])
    geojson = to_geojson_dict(gpx)

    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 1

    feature = geojson["features"][0]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Point"
    assert feature["geometry"]["coordinates"] == [4.9041, 52.3676, 2.0]
    assert feature["properties"]["name"] == "Amsterdam"


def test_to_geojson_dict_route():
    """Test to_geojson_dict with a route."""
    route = Route(
        name="Test Route",
        rtept=[
            Waypoint(lat=Latitude("52.0"), lon=Longitude("4.0"), ele=Decimal("10.0")),
            Waypoint(lat=Latitude("52.1"), lon=Longitude("4.1"), ele=Decimal("15.0")),
        ],
    )
    gpx = GPX(creator="Test", rte=[route])
    geojson = to_geojson_dict(gpx)

    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 1

    feature = geojson["features"][0]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "LineString"
    assert len(feature["geometry"]["coordinates"]) == 2
    assert feature["properties"]["name"] == "Test Route"


def test_to_geojson_dict_track():
    """Test to_geojson_dict with a track."""
    track = Track(
        name="Test Track",
        trkseg=[
            TrackSegment(
                trkpt=[
                    Waypoint(
                        lat=Latitude("52.0"), lon=Longitude("4.0"), ele=Decimal("10.0")
                    ),
                    Waypoint(
                        lat=Latitude("52.1"), lon=Longitude("4.1"), ele=Decimal("15.0")
                    ),
                ]
            )
        ],
    )
    gpx = GPX(creator="Test", trk=[track])
    geojson = to_geojson_dict(gpx)

    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 1

    feature = geojson["features"][0]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "MultiLineString"
    assert len(feature["geometry"]["coordinates"]) == 1
    assert len(feature["geometry"]["coordinates"][0]) == 2
    assert feature["properties"]["name"] == "Test Track"


def test_to_geojson():
    """Test to_geojson function."""
    waypoint = Waypoint(
        lat=Latitude("52.3676"), lon=Longitude("4.9041"), name="Amsterdam"
    )
    gpx = GPX(creator="Test", wpt=[waypoint])
    geojson_str = to_geojson(gpx)

    # Verify it's valid JSON
    data = json.loads(geojson_str)
    assert data["type"] == "FeatureCollection"

    # Test with pretty_print=False
    geojson_str_compact = to_geojson(gpx, pretty_print=False)
    assert "\n" not in geojson_str_compact.strip()


def test_from_geojson_dict_waypoint():
    """Test from_geojson_dict with a waypoint."""
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [4.9041, 52.3676, 2.0]},
                "properties": {"name": "Amsterdam", "desc": "Capital of Netherlands"},
            }
        ],
    }

    gpx = from_geojson_dict(geojson)
    assert len(gpx.wpt) == 1

    waypoint = gpx.wpt[0]
    assert float(waypoint.lon) == 4.9041
    assert float(waypoint.lat) == 52.3676
    assert float(waypoint.ele) == 2.0
    assert waypoint.name == "Amsterdam"
    assert waypoint.desc == "Capital of Netherlands"


def test_from_geojson_dict_route():
    """Test from_geojson_dict with a route."""
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[4.0, 52.0, 10.0], [4.1, 52.1, 15.0]],
                },
                "properties": {"name": "Test Route"},
            }
        ],
    }

    gpx = from_geojson_dict(geojson)
    assert len(gpx.rte) == 1

    route = gpx.rte[0]
    assert route.name == "Test Route"
    assert len(route.rtept) == 2
    assert float(route.rtept[0].lon) == 4.0
    assert float(route.rtept[0].lat) == 52.0
    assert float(route.rtept[0].ele) == 10.0


def test_from_geojson_dict_track():
    """Test from_geojson_dict with a track."""
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": [[[4.0, 52.0, 10.0], [4.1, 52.1, 15.0]]],
                },
                "properties": {"name": "Test Track"},
            }
        ],
    }

    gpx = from_geojson_dict(geojson)
    assert len(gpx.trk) == 1

    track = gpx.trk[0]
    assert track.name == "Test Track"
    assert len(track.trkseg) == 1
    assert len(track.trkseg[0].trkpt) == 2


def test_from_geojson_dict_invalid():
    """Test from_geojson_dict with invalid data."""
    # Not a FeatureCollection
    with pytest.raises(ValueError, match="GeoJSON must be a FeatureCollection"):
        from_geojson_dict({"type": "Feature"})


def test_from_geojson():
    """Test from_geojson function."""
    geojson_str = """
    {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [4.9041, 52.3676]
                },
                "properties": {
                    "name": "Amsterdam"
                }
            }
        ]
    }
    """

    gpx = from_geojson(geojson_str)
    assert len(gpx.wpt) == 1
    assert gpx.wpt[0].name == "Amsterdam"


def test_geojson_roundtrip():
    """Test roundtrip conversion GPX -> GeoJSON -> GPX."""
    # Create a GPX with various features
    gpx1 = GPX(
        creator="Test",
        wpt=[
            Waypoint(
                lat=Latitude("52.3676"),
                lon=Longitude("4.9041"),
                name="Amsterdam",
                ele=Decimal("2.0"),
            )
        ],
        rte=[
            Route(
                name="Test Route",
                rtept=[
                    Waypoint(
                        lat=Latitude("52.0"), lon=Longitude("4.0"), ele=Decimal("10.0")
                    ),
                    Waypoint(
                        lat=Latitude("52.1"), lon=Longitude("4.1"), ele=Decimal("15.0")
                    ),
                ],
            )
        ],
    )

    # Convert to GeoJSON and back
    geojson_str = to_geojson(gpx1)
    gpx2 = from_geojson(geojson_str)

    # Verify waypoints
    assert len(gpx2.wpt) == 1
    assert gpx2.wpt[0].name == "Amsterdam"
    assert float(gpx2.wpt[0].lat) == 52.3676
    assert float(gpx2.wpt[0].lon) == 4.9041

    # Verify routes
    assert len(gpx2.rte) == 1
    assert gpx2.rte[0].name == "Test Route"
    assert len(gpx2.rte[0].rtept) == 2


def test_to_kml_empty():
    """Test to_kml with empty GPX."""
    gpx = GPX(creator="Test")
    kml_str = to_kml(gpx)

    assert '<?xml version' in kml_str
    assert 'xmlns="http://www.opengis.net/kml/2.2"' in kml_str
    assert "<Document" in kml_str  # Can be <Document> or <Document />


def test_to_kml_waypoint():
    """Test to_kml with a waypoint."""
    waypoint = Waypoint(
        lat=Latitude("52.3676"),
        lon=Longitude("4.9041"),
        name="Amsterdam",
        desc="Capital of Netherlands",
        ele=Decimal("2.0"),
        time=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )
    gpx = GPX(creator="Test", wpt=[waypoint])
    kml_str = to_kml(gpx)

    assert "<Folder>" in kml_str
    assert "<name>Waypoints</name>" in kml_str
    assert "<Placemark>" in kml_str
    assert "<name>Amsterdam</name>" in kml_str
    assert "<description>Capital of Netherlands</description>" in kml_str
    assert "<Point>" in kml_str
    assert "<coordinates>4.9041,52.3676,2.0</coordinates>" in kml_str
    assert "<TimeStamp>" in kml_str


def test_to_kml_route():
    """Test to_kml with a route."""
    route = Route(
        name="Test Route",
        desc="A test route",
        rtept=[
            Waypoint(lat=Latitude("52.0"), lon=Longitude("4.0"), ele=Decimal("10.0")),
            Waypoint(lat=Latitude("52.1"), lon=Longitude("4.1"), ele=Decimal("15.0")),
        ],
    )
    gpx = GPX(creator="Test", rte=[route])
    kml_str = to_kml(gpx)

    assert "<name>Routes</name>" in kml_str
    assert "<name>Test Route</name>" in kml_str
    assert "<description>A test route</description>" in kml_str
    assert "<LineString>" in kml_str
    assert "4.0,52.0,10.0 4.1,52.1,15.0" in kml_str


def test_to_kml_track():
    """Test to_kml with a track."""
    track = Track(
        name="Test Track",
        desc="A test track",
        trkseg=[
            TrackSegment(
                trkpt=[
                    Waypoint(
                        lat=Latitude("52.0"), lon=Longitude("4.0"), ele=Decimal("10.0")
                    ),
                    Waypoint(
                        lat=Latitude("52.1"), lon=Longitude("4.1"), ele=Decimal("15.0")
                    ),
                ]
            )
        ],
    )
    gpx = GPX(creator="Test", trk=[track])
    kml_str = to_kml(gpx)

    assert "<name>Tracks</name>" in kml_str
    assert "<name>Test Track</name>" in kml_str
    assert "<description>A test track</description>" in kml_str
    # Tracks always use MultiGeometry, even with single segment
    assert "<MultiGeometry>" in kml_str
    assert "<LineString>" in kml_str


def test_to_kml_track_multisegment():
    """Test to_kml with a multi-segment track."""
    track = Track(
        name="Multi-segment Track",
        trkseg=[
            TrackSegment(
                trkpt=[
                    Waypoint(
                        lat=Latitude("52.0"), lon=Longitude("4.0"), ele=Decimal("10.0")
                    ),
                    Waypoint(
                        lat=Latitude("52.1"), lon=Longitude("4.1"), ele=Decimal("15.0")
                    ),
                ]
            ),
            TrackSegment(
                trkpt=[
                    Waypoint(
                        lat=Latitude("52.2"), lon=Longitude("4.2"), ele=Decimal("20.0")
                    ),
                    Waypoint(
                        lat=Latitude("52.3"), lon=Longitude("4.3"), ele=Decimal("25.0")
                    ),
                ]
            ),
        ],
    )
    gpx = GPX(creator="Test", trk=[track])
    kml_str = to_kml(gpx)

    assert "<MultiGeometry>" in kml_str
    assert kml_str.count("<LineString>") == 2


def test_to_kml_with_metadata():
    """Test to_kml with metadata."""
    gpx = GPX(
        creator="Test",
        metadata=Metadata(name="My GPS Data", desc="Collected on a hike"),
    )
    kml_str = to_kml(gpx)

    # Document-level name and description
    assert "<name>My GPS Data</name>" in kml_str
    assert "<description>Collected on a hike</description>" in kml_str


def test_from_kml_waypoint():
    """Test from_kml with a waypoint."""
    kml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2">
      <Document>
        <Folder>
          <name>Waypoints</name>
          <Placemark>
            <name>Amsterdam</name>
            <description>Capital</description>
            <Point>
              <coordinates>4.9041,52.3676,2.0</coordinates>
            </Point>
          </Placemark>
        </Folder>
      </Document>
    </kml>"""

    gpx = from_kml(kml_str)
    assert len(gpx.wpt) == 1

    waypoint = gpx.wpt[0]
    assert waypoint.name == "Amsterdam"
    assert waypoint.desc == "Capital"
    assert float(waypoint.lon) == 4.9041
    assert float(waypoint.lat) == 52.3676
    assert float(waypoint.ele) == 2.0


def test_from_kml_route():
    """Test from_kml with a route."""
    kml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2">
      <Document>
        <Placemark>
          <name>Test Route</name>
          <LineString>
            <coordinates>4.0,52.0,10.0 4.1,52.1,15.0</coordinates>
          </LineString>
        </Placemark>
      </Document>
    </kml>"""

    gpx = from_kml(kml_str)
    assert len(gpx.rte) == 1

    route = gpx.rte[0]
    assert route.name == "Test Route"
    assert len(route.rtept) == 2
    assert float(route.rtept[0].lon) == 4.0
    assert float(route.rtept[0].lat) == 52.0


def test_from_kml_track():
    """Test from_kml with a multi-segment track."""
    kml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2">
      <Document>
        <Placemark>
          <name>Test Track</name>
          <MultiGeometry>
            <LineString>
              <coordinates>4.0,52.0,10.0 4.1,52.1,15.0</coordinates>
            </LineString>
            <LineString>
              <coordinates>4.2,52.2,20.0 4.3,52.3,25.0</coordinates>
            </LineString>
          </MultiGeometry>
        </Placemark>
      </Document>
    </kml>"""

    gpx = from_kml(kml_str)
    assert len(gpx.trk) == 1

    track = gpx.trk[0]
    assert track.name == "Test Track"
    assert len(track.trkseg) == 2
    assert len(track.trkseg[0].trkpt) == 2
    assert len(track.trkseg[1].trkpt) == 2


def test_from_kml_invalid():
    """Test from_kml with invalid KML."""
    kml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2">
      <Folder>
      </Folder>
    </kml>"""

    with pytest.raises(ValueError, match="KML must contain a Document element"):
        from_kml(kml_str)


def test_kml_roundtrip():
    """Test roundtrip conversion GPX -> KML -> GPX."""
    # Create a GPX with various features
    gpx1 = GPX(
        creator="Test",
        metadata=Metadata(name="Test Data", desc="Test description"),
        wpt=[
            Waypoint(
                lat=Latitude("52.3676"),
                lon=Longitude("4.9041"),
                name="Amsterdam",
                ele=Decimal("2.0"),
            )
        ],
        rte=[
            Route(
                name="Test Route",
                rtept=[
                    Waypoint(
                        lat=Latitude("52.0"), lon=Longitude("4.0"), ele=Decimal("10.0")
                    ),
                    Waypoint(
                        lat=Latitude("52.1"), lon=Longitude("4.1"), ele=Decimal("15.0")
                    ),
                ],
            )
        ],
        trk=[
            Track(
                name="Test Track",
                trkseg=[
                    TrackSegment(
                        trkpt=[
                            Waypoint(
                                lat=Latitude("52.2"),
                                lon=Longitude("4.2"),
                                ele=Decimal("20.0"),
                            ),
                            Waypoint(
                                lat=Latitude("52.3"),
                                lon=Longitude("4.3"),
                                ele=Decimal("25.0"),
                            ),
                        ]
                    )
                ],
            )
        ],
    )

    # Convert to KML and back
    kml_str = to_kml(gpx1)
    gpx2 = from_kml(kml_str)

    # Verify metadata
    assert gpx2.metadata is not None
    assert gpx2.metadata.name == "Test Data"
    assert gpx2.metadata.desc == "Test description"

    # Verify waypoints
    assert len(gpx2.wpt) == 1
    assert gpx2.wpt[0].name == "Amsterdam"

    # Verify routes
    assert len(gpx2.rte) == 1
    assert gpx2.rte[0].name == "Test Route"
    assert len(gpx2.rte[0].rtept) == 2

    # Verify tracks
    assert len(gpx2.trk) == 1
    assert gpx2.trk[0].name == "Test Track"
    assert len(gpx2.trk[0].trkseg) == 1
