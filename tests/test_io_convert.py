"""Tests for gpx.io and gpx.convert modules - I/O and conversion operations."""

import json
import struct
import tempfile
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from gpx import (
    GPX,
    Metadata,
    Route,
    Track,
    TrackSegment,
    Waypoint,
    from_geo_interface,
    from_geojson,
    from_kml,
    from_wkb,
    from_wkt,
    read_geojson,
    read_gpx,
    read_kml,
    read_wkb,
    read_wkt,
)
from gpx.types import Latitude, Longitude

# =============================================================================
# Test fixtures
# =============================================================================


@pytest.fixture
def sample_gpx() -> GPX:
    """Create a sample GPX with waypoints, routes, and tracks."""
    waypoint = Waypoint(
        lat=Latitude("52.5200"),
        lon=Longitude("13.4050"),
        ele=Decimal("34.5"),
        name="Berlin",
    )

    route_points = [
        Waypoint(lat=Latitude("52.5200"), lon=Longitude("13.4050"), ele=Decimal("34.5")),
        Waypoint(lat=Latitude("52.5300"), lon=Longitude("13.4150"), ele=Decimal("40.0")),
    ]
    route = Route(name="City Tour", desc="A tour of the city", rtept=route_points)

    track_points = [
        Waypoint(lat=Latitude("52.5200"), lon=Longitude("13.4050"), ele=Decimal("34.5")),
        Waypoint(lat=Latitude("52.5210"), lon=Longitude("13.4060"), ele=Decimal("35.0")),
        Waypoint(lat=Latitude("52.5220"), lon=Longitude("13.4070"), ele=Decimal("36.5")),
    ]
    segment = TrackSegment(trkpt=track_points)
    track = Track(name="Morning Run", desc="A morning run", trkseg=[segment])

    return GPX(
        creator="TestApp",
        metadata=Metadata(name="Test GPX", desc="Test description"),
        wpt=[waypoint],
        rte=[route],
        trk=[track],
    )


@pytest.fixture
def sample_geojson_feature_collection() -> dict[str, Any]:
    """Create a sample GeoJSON FeatureCollection."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [13.405, 52.52, 34.5]},
                "properties": {"name": "Berlin"},
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [13.405, 52.52, 34.5],
                        [13.415, 52.53, 40.0],
                    ],
                },
                "properties": {"name": "City Tour"},
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": [
                        [
                            [13.405, 52.52, 34.5],
                            [13.406, 52.521, 35.0],
                            [13.407, 52.522, 36.5],
                        ]
                    ],
                },
                "properties": {"name": "Morning Run"},
            },
        ],
    }


@pytest.fixture
def sample_kml() -> str:
    """Create a sample KML string."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Test KML</name>
    <description>Test description</description>
    <Placemark>
      <name>Berlin</name>
      <description>Capital of Germany</description>
      <Point>
        <coordinates>13.405,52.52,34.5</coordinates>
      </Point>
    </Placemark>
    <Placemark>
      <name>City Tour</name>
      <LineString>
        <coordinates>13.405,52.52,34.5 13.415,52.53,40.0</coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>"""


# =============================================================================
# GeoJSON conversion tests
# =============================================================================


class TestGeoJSONConversion:
    """Tests for GeoJSON conversion functionality."""

    def test_gpx_to_geojson_string(self, sample_gpx: GPX) -> None:
        """Test converting GPX to GeoJSON string."""
        geojson_str = sample_gpx.to_geojson()
        data = json.loads(geojson_str)
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 3  # 1 waypoint + 1 route + 1 track

    def test_gpx_to_geojson_with_indent(self, sample_gpx: GPX) -> None:
        """Test converting GPX to GeoJSON with indentation."""
        geojson_str = sample_gpx.to_geojson(indent=2)
        assert "\n" in geojson_str
        assert "  " in geojson_str

    def test_gpx_write_geojson(self, sample_gpx: GPX) -> None:
        """Test writing GPX to GeoJSON file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".geojson", delete=False
        ) as f:
            sample_gpx.write_geojson(f.name)
            content = Path(f.name).read_text()
            data = json.loads(content)
            assert data["type"] == "FeatureCollection"
            Path(f.name).unlink()

    def test_from_geojson_feature_collection(
        self, sample_geojson_feature_collection: dict[str, Any]
    ) -> None:
        """Test converting GeoJSON FeatureCollection to GPX."""
        gpx = from_geojson(sample_geojson_feature_collection)
        assert len(gpx.wpt) == 1
        assert gpx.wpt[0].name == "Berlin"
        assert len(gpx.rte) == 1
        assert gpx.rte[0].name == "City Tour"
        assert len(gpx.trk) == 1
        assert gpx.trk[0].name == "Morning Run"

    def test_from_geojson_string(
        self, sample_geojson_feature_collection: dict[str, Any]
    ) -> None:
        """Test converting GeoJSON string to GPX."""
        geojson_str = json.dumps(sample_geojson_feature_collection)
        gpx = from_geojson(geojson_str)
        assert len(gpx.wpt) == 1
        assert len(gpx.rte) == 1
        assert len(gpx.trk) == 1

    def test_from_geojson_with_creator(
        self, sample_geojson_feature_collection: dict[str, Any]
    ) -> None:
        """Test converting GeoJSON with custom creator."""
        gpx = from_geojson(sample_geojson_feature_collection, creator="MyApp")
        assert gpx.creator == "MyApp"

    def test_from_geo_interface(
        self, sample_geojson_feature_collection: dict[str, Any]
    ) -> None:
        """Test converting object with __geo_interface__."""
        gpx = from_geo_interface(sample_geojson_feature_collection)
        assert len(gpx.wpt) == 1

    def test_from_geojson_point(self) -> None:
        """Test converting single GeoJSON Point to GPX."""
        geojson = {"type": "Point", "coordinates": [13.405, 52.52, 34.5]}
        gpx = from_geojson(geojson)
        assert len(gpx.wpt) == 1
        assert float(gpx.wpt[0].lon) == pytest.approx(13.405, rel=1e-3)
        assert float(gpx.wpt[0].lat) == pytest.approx(52.52, rel=1e-3)

    def test_from_geojson_linestring(self) -> None:
        """Test converting GeoJSON LineString to GPX route."""
        geojson = {
            "type": "LineString",
            "coordinates": [[13.405, 52.52], [13.415, 52.53]],
        }
        gpx = from_geojson(geojson)
        assert len(gpx.rte) == 1
        assert len(gpx.rte[0].rtept) == 2

    def test_from_geojson_multilinestring(self) -> None:
        """Test converting GeoJSON MultiLineString to GPX track."""
        geojson = {
            "type": "MultiLineString",
            "coordinates": [
                [[13.405, 52.52], [13.406, 52.521]],
                [[13.407, 52.522], [13.408, 52.523]],
            ],
        }
        gpx = from_geojson(geojson)
        assert len(gpx.trk) == 1
        assert len(gpx.trk[0].trkseg) == 2

    def test_from_geojson_multipoint(self) -> None:
        """Test converting GeoJSON MultiPoint to GPX waypoints."""
        geojson = {
            "type": "MultiPoint",
            "coordinates": [[13.405, 52.52], [13.415, 52.53]],
        }
        gpx = from_geojson(geojson)
        assert len(gpx.wpt) == 2

    def test_read_geojson_file(
        self, sample_geojson_feature_collection: dict[str, Any]
    ) -> None:
        """Test reading GeoJSON from file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".geojson", delete=False
        ) as f:
            json.dump(sample_geojson_feature_collection, f)
            f.flush()
            gpx = read_geojson(f.name)
            assert len(gpx.wpt) == 1
            Path(f.name).unlink()

    def test_geojson_roundtrip(self, sample_gpx: GPX) -> None:
        """Test GeoJSON roundtrip conversion."""
        geojson_str = sample_gpx.to_geojson()
        gpx2 = from_geojson(geojson_str)
        assert len(gpx2.wpt) == len(sample_gpx.wpt)
        assert len(gpx2.rte) == len(sample_gpx.rte)
        assert len(gpx2.trk) == len(sample_gpx.trk)


# =============================================================================
# KML conversion tests
# =============================================================================


class TestKMLConversion:
    """Tests for KML conversion functionality."""

    def test_gpx_to_kml_string(self, sample_gpx: GPX) -> None:
        """Test converting GPX to KML string."""
        kml_str = sample_gpx.to_kml()
        assert "<?xml" in kml_str
        assert "<kml" in kml_str
        assert "<Document>" in kml_str
        assert "<Placemark>" in kml_str

    def test_gpx_to_kml_with_metadata(self, sample_gpx: GPX) -> None:
        """Test that KML includes metadata name and description."""
        kml_str = sample_gpx.to_kml()
        assert "<name>Test GPX</name>" in kml_str
        assert "<description>Test description</description>" in kml_str

    def test_gpx_to_kml_with_waypoints(self, sample_gpx: GPX) -> None:
        """Test that KML includes waypoints as Point placemarks."""
        kml_str = sample_gpx.to_kml()
        assert "<Point>" in kml_str
        assert "<coordinates>13.4050,52.5200,34.5</coordinates>" in kml_str

    def test_gpx_to_kml_with_routes(self, sample_gpx: GPX) -> None:
        """Test that KML includes routes as LineString placemarks."""
        kml_str = sample_gpx.to_kml()
        assert "<LineString>" in kml_str
        assert "<name>City Tour</name>" in kml_str

    def test_gpx_to_kml_with_tracks(self, sample_gpx: GPX) -> None:
        """Test that KML includes tracks as LineString/MultiGeometry."""
        kml_str = sample_gpx.to_kml()
        assert "<name>Morning Run</name>" in kml_str

    def test_gpx_write_kml(self, sample_gpx: GPX) -> None:
        """Test writing GPX to KML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".kml", delete=False) as f:
            sample_gpx.write_kml(f.name)
            content = Path(f.name).read_text()
            assert "<kml" in content
            Path(f.name).unlink()

    def test_from_kml_string(self, sample_kml: str) -> None:
        """Test converting KML string to GPX."""
        gpx = from_kml(sample_kml)
        assert gpx.metadata is not None
        assert gpx.metadata.name == "Test KML"
        assert gpx.metadata.desc == "Test description"
        assert len(gpx.wpt) == 1
        assert gpx.wpt[0].name == "Berlin"
        assert len(gpx.rte) == 1
        assert gpx.rte[0].name == "City Tour"

    def test_from_kml_with_creator(self, sample_kml: str) -> None:
        """Test converting KML with custom creator."""
        gpx = from_kml(sample_kml, creator="MyApp")
        assert gpx.creator == "MyApp"

    def test_read_kml_file(self, sample_kml: str) -> None:
        """Test reading KML from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".kml", delete=False) as f:
            f.write(sample_kml)
            f.flush()
            gpx = read_kml(f.name)
            assert gpx.metadata is not None
            assert gpx.metadata.name == "Test KML"
            Path(f.name).unlink()

    def test_kml_roundtrip(self, sample_gpx: GPX) -> None:
        """Test KML roundtrip conversion."""
        kml_str = sample_gpx.to_kml()
        gpx2 = from_kml(kml_str)
        assert len(gpx2.wpt) == len(sample_gpx.wpt)
        # Note: Track with single segment becomes a LineString in KML,
        # which converts back to a route. Total LineStrings = routes + tracks
        total_linestrings = len(sample_gpx.rte) + len(sample_gpx.trk)
        assert len(gpx2.rte) == total_linestrings
        # Only MultiGeometry tracks remain as tracks
        assert len(gpx2.trk) == 0

    def test_kml_multigeometry_for_multi_segment_track(self) -> None:
        """Test that multi-segment tracks use MultiGeometry in KML."""
        track_points1 = [
            Waypoint(lat=Latitude("52.52"), lon=Longitude("13.405")),
            Waypoint(lat=Latitude("52.521"), lon=Longitude("13.406")),
        ]
        track_points2 = [
            Waypoint(lat=Latitude("52.522"), lon=Longitude("13.407")),
            Waypoint(lat=Latitude("52.523"), lon=Longitude("13.408")),
        ]
        segment1 = TrackSegment(trkpt=track_points1)
        segment2 = TrackSegment(trkpt=track_points2)
        track = Track(name="Multi-segment", trkseg=[segment1, segment2])
        gpx = GPX(trk=[track])

        kml_str = gpx.to_kml()
        assert "<MultiGeometry>" in kml_str


# =============================================================================
# WKT conversion tests
# =============================================================================


class TestWKTConversion:
    """Tests for WKT conversion functionality."""

    def test_gpx_to_wkt_single_waypoint(self) -> None:
        """Test converting GPX with single waypoint to WKT."""
        waypoint = Waypoint(
            lat=Latitude("52.52"), lon=Longitude("13.405"), ele=Decimal("34.5")
        )
        gpx = GPX(wpt=[waypoint])
        wkt = gpx.to_wkt()
        assert wkt.startswith("POINT Z (")
        assert "13.405" in wkt
        assert "52.52" in wkt
        assert "34.5" in wkt

    def test_gpx_to_wkt_waypoint_no_elevation(self) -> None:
        """Test converting waypoint without elevation to WKT."""
        waypoint = Waypoint(lat=Latitude("52.52"), lon=Longitude("13.405"))
        gpx = GPX(wpt=[waypoint])
        wkt = gpx.to_wkt()
        assert wkt.startswith("POINT (")
        assert " Z " not in wkt

    def test_gpx_to_wkt_route(self) -> None:
        """Test converting GPX with route to WKT."""
        route_points = [
            Waypoint(lat=Latitude("52.52"), lon=Longitude("13.405")),
            Waypoint(lat=Latitude("52.53"), lon=Longitude("13.415")),
        ]
        route = Route(rtept=route_points)
        gpx = GPX(rte=[route])
        wkt = gpx.to_wkt()
        assert "LINESTRING" in wkt

    def test_gpx_to_wkt_track(self) -> None:
        """Test converting GPX with track to WKT."""
        track_points = [
            Waypoint(lat=Latitude("52.52"), lon=Longitude("13.405")),
            Waypoint(lat=Latitude("52.521"), lon=Longitude("13.406")),
        ]
        segment = TrackSegment(trkpt=track_points)
        track = Track(trkseg=[segment])
        gpx = GPX(trk=[track])
        wkt = gpx.to_wkt()
        assert "MULTILINESTRING" in wkt

    def test_gpx_to_wkt_geometry_collection(self, sample_gpx: GPX) -> None:
        """Test converting GPX with multiple elements to WKT GEOMETRYCOLLECTION."""
        wkt = sample_gpx.to_wkt()
        assert wkt.startswith("GEOMETRYCOLLECTION (")
        assert "POINT" in wkt
        assert "LINESTRING" in wkt
        assert "MULTILINESTRING" in wkt

    def test_gpx_write_wkt(self, sample_gpx: GPX) -> None:
        """Test writing GPX to WKT file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".wkt", delete=False) as f:
            sample_gpx.write_wkt(f.name)
            content = Path(f.name).read_text()
            assert "GEOMETRYCOLLECTION" in content
            Path(f.name).unlink()

    def test_from_wkt_point(self) -> None:
        """Test converting WKT POINT to GPX."""
        wkt = "POINT (13.405 52.52)"
        gpx = from_wkt(wkt)
        assert len(gpx.wpt) == 1
        assert float(gpx.wpt[0].lon) == pytest.approx(13.405, rel=1e-3)
        assert float(gpx.wpt[0].lat) == pytest.approx(52.52, rel=1e-3)

    def test_from_wkt_point_z(self) -> None:
        """Test converting WKT POINT Z to GPX."""
        wkt = "POINT Z (13.405 52.52 34.5)"
        gpx = from_wkt(wkt)
        assert len(gpx.wpt) == 1
        assert gpx.wpt[0].ele == Decimal("34.5")

    def test_from_wkt_linestring(self) -> None:
        """Test converting WKT LINESTRING to GPX."""
        wkt = "LINESTRING (13.405 52.52, 13.415 52.53)"
        gpx = from_wkt(wkt)
        assert len(gpx.rte) == 1
        assert len(gpx.rte[0].rtept) == 2

    def test_from_wkt_multilinestring(self) -> None:
        """Test converting WKT MULTILINESTRING to GPX."""
        wkt = "MULTILINESTRING ((13.405 52.52, 13.406 52.521), (13.407 52.522, 13.408 52.523))"
        gpx = from_wkt(wkt)
        assert len(gpx.trk) == 1
        assert len(gpx.trk[0].trkseg) == 2

    def test_from_wkt_multipoint(self) -> None:
        """Test converting WKT MULTIPOINT to GPX."""
        wkt = "MULTIPOINT (13.405 52.52, 13.415 52.53)"
        gpx = from_wkt(wkt)
        assert len(gpx.wpt) == 2

    def test_from_wkt_geometry_collection(self) -> None:
        """Test converting WKT GEOMETRYCOLLECTION to GPX."""
        wkt = "GEOMETRYCOLLECTION (POINT (13.405 52.52), LINESTRING (13.405 52.52, 13.415 52.53))"
        gpx = from_wkt(wkt)
        assert len(gpx.wpt) == 1
        assert len(gpx.rte) == 1

    def test_from_wkt_with_creator(self) -> None:
        """Test converting WKT with custom creator."""
        wkt = "POINT (13.405 52.52)"
        gpx = from_wkt(wkt, creator="MyApp")
        assert gpx.creator == "MyApp"

    def test_read_wkt_file(self) -> None:
        """Test reading WKT from file."""
        wkt = "POINT (13.405 52.52)"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".wkt", delete=False) as f:
            f.write(wkt)
            f.flush()
            gpx = read_wkt(f.name)
            assert len(gpx.wpt) == 1
            Path(f.name).unlink()

    def test_wkt_roundtrip(self) -> None:
        """Test WKT roundtrip conversion for a single point."""
        waypoint = Waypoint(lat=Latitude("52.52"), lon=Longitude("13.405"))
        gpx1 = GPX(wpt=[waypoint])
        wkt = gpx1.to_wkt()
        gpx2 = from_wkt(wkt)
        assert len(gpx2.wpt) == 1
        assert float(gpx2.wpt[0].lat) == pytest.approx(float(gpx1.wpt[0].lat), rel=1e-3)


# =============================================================================
# WKB conversion tests
# =============================================================================


class TestWKBConversion:
    """Tests for WKB conversion functionality."""

    def test_gpx_to_wkb_single_waypoint(self) -> None:
        """Test converting GPX with single waypoint to WKB."""
        waypoint = Waypoint(lat=Latitude("52.52"), lon=Longitude("13.405"))
        gpx = GPX(wpt=[waypoint])
        wkb = gpx.to_wkb()
        assert isinstance(wkb, bytes)
        assert len(wkb) > 0
        # Check byte order marker (little endian)
        assert wkb[0] == 1

    def test_gpx_to_wkb_big_endian(self) -> None:
        """Test converting GPX to WKB with big endian byte order."""
        waypoint = Waypoint(lat=Latitude("52.52"), lon=Longitude("13.405"))
        gpx = GPX(wpt=[waypoint])
        wkb = gpx.to_wkb(byte_order="big")
        # Check byte order marker (big endian)
        assert wkb[0] == 0

    def test_gpx_to_wkb_waypoint_with_elevation(self) -> None:
        """Test converting waypoint with elevation to WKB."""
        waypoint = Waypoint(
            lat=Latitude("52.52"), lon=Longitude("13.405"), ele=Decimal("34.5")
        )
        gpx = GPX(wpt=[waypoint])
        wkb = gpx.to_wkb()
        # Read geometry type (should be Point Z = 1001)
        geom_type = struct.unpack("<I", wkb[1:5])[0]
        assert geom_type == 1001

    def test_gpx_to_wkb_route(self) -> None:
        """Test converting GPX with route to WKB."""
        route_points = [
            Waypoint(lat=Latitude("52.52"), lon=Longitude("13.405")),
            Waypoint(lat=Latitude("52.53"), lon=Longitude("13.415")),
        ]
        route = Route(rtept=route_points)
        gpx = GPX(rte=[route])
        wkb = gpx.to_wkb()
        # Read geometry type (should be LineString = 2)
        geom_type = struct.unpack("<I", wkb[1:5])[0]
        assert geom_type == 2

    def test_gpx_to_wkb_track(self) -> None:
        """Test converting GPX with track to WKB."""
        track_points = [
            Waypoint(lat=Latitude("52.52"), lon=Longitude("13.405")),
            Waypoint(lat=Latitude("52.521"), lon=Longitude("13.406")),
        ]
        segment = TrackSegment(trkpt=track_points)
        track = Track(trkseg=[segment])
        gpx = GPX(trk=[track])
        wkb = gpx.to_wkb()
        # Read geometry type (should be MultiLineString = 5)
        geom_type = struct.unpack("<I", wkb[1:5])[0]
        assert geom_type == 5

    def test_gpx_to_wkb_geometry_collection(self, sample_gpx: GPX) -> None:
        """Test converting GPX with multiple elements to WKB GeometryCollection."""
        wkb = sample_gpx.to_wkb()
        # Read geometry type (should be GeometryCollection = 7)
        geom_type = struct.unpack("<I", wkb[1:5])[0]
        assert geom_type == 7

    def test_gpx_write_wkb(self, sample_gpx: GPX) -> None:
        """Test writing GPX to WKB file."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".wkb", delete=False) as f:
            sample_gpx.write_wkb(f.name)
            content = Path(f.name).read_bytes()
            assert len(content) > 0
            Path(f.name).unlink()

    def test_from_wkb_point(self) -> None:
        """Test converting WKB POINT to GPX."""
        # Build WKB Point: byte order (1) + type (1) + x + y
        wkb = b"\x01"  # Little endian
        wkb += struct.pack("<I", 1)  # Point type
        wkb += struct.pack("<dd", 13.405, 52.52)  # lon, lat
        gpx = from_wkb(wkb)
        assert len(gpx.wpt) == 1
        assert float(gpx.wpt[0].lon) == pytest.approx(13.405, rel=1e-3)
        assert float(gpx.wpt[0].lat) == pytest.approx(52.52, rel=1e-3)

    def test_from_wkb_point_z(self) -> None:
        """Test converting WKB POINT Z to GPX."""
        # Build WKB Point Z: byte order (1) + type (1001) + x + y + z
        wkb = b"\x01"  # Little endian
        wkb += struct.pack("<I", 1001)  # Point Z type
        wkb += struct.pack("<ddd", 13.405, 52.52, 34.5)  # lon, lat, ele
        gpx = from_wkb(wkb)
        assert len(gpx.wpt) == 1
        assert gpx.wpt[0].ele == Decimal("34.5")

    def test_from_wkb_linestring(self) -> None:
        """Test converting WKB LINESTRING to GPX."""
        wkb = b"\x01"  # Little endian
        wkb += struct.pack("<I", 2)  # LineString type
        wkb += struct.pack("<I", 2)  # Number of points
        wkb += struct.pack("<dd", 13.405, 52.52)
        wkb += struct.pack("<dd", 13.415, 52.53)
        gpx = from_wkb(wkb)
        assert len(gpx.rte) == 1
        assert len(gpx.rte[0].rtept) == 2

    def test_from_wkb_multilinestring(self) -> None:
        """Test converting WKB MULTILINESTRING to GPX."""
        wkb = b"\x01"  # Little endian
        wkb += struct.pack("<I", 5)  # MultiLineString type
        wkb += struct.pack("<I", 2)  # Number of linestrings

        # First linestring
        wkb += b"\x01"
        wkb += struct.pack("<I", 2)  # LineString type
        wkb += struct.pack("<I", 2)  # Number of points
        wkb += struct.pack("<dd", 13.405, 52.52)
        wkb += struct.pack("<dd", 13.406, 52.521)

        # Second linestring
        wkb += b"\x01"
        wkb += struct.pack("<I", 2)  # LineString type
        wkb += struct.pack("<I", 2)  # Number of points
        wkb += struct.pack("<dd", 13.407, 52.522)
        wkb += struct.pack("<dd", 13.408, 52.523)

        gpx = from_wkb(wkb)
        assert len(gpx.trk) == 1
        assert len(gpx.trk[0].trkseg) == 2

    def test_from_wkb_multipoint(self) -> None:
        """Test converting WKB MULTIPOINT to GPX."""
        wkb = b"\x01"  # Little endian
        wkb += struct.pack("<I", 4)  # MultiPoint type
        wkb += struct.pack("<I", 2)  # Number of points

        # First point
        wkb += b"\x01"
        wkb += struct.pack("<I", 1)  # Point type
        wkb += struct.pack("<dd", 13.405, 52.52)

        # Second point
        wkb += b"\x01"
        wkb += struct.pack("<I", 1)  # Point type
        wkb += struct.pack("<dd", 13.415, 52.53)

        gpx = from_wkb(wkb)
        assert len(gpx.wpt) == 2

    def test_from_wkb_with_creator(self) -> None:
        """Test converting WKB with custom creator."""
        wkb = b"\x01"
        wkb += struct.pack("<I", 1)
        wkb += struct.pack("<dd", 13.405, 52.52)
        gpx = from_wkb(wkb, creator="MyApp")
        assert gpx.creator == "MyApp"

    def test_read_wkb_file(self) -> None:
        """Test reading WKB from file."""
        wkb = b"\x01"
        wkb += struct.pack("<I", 1)
        wkb += struct.pack("<dd", 13.405, 52.52)
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".wkb", delete=False) as f:
            f.write(wkb)
            f.flush()
            gpx = read_wkb(f.name)
            assert len(gpx.wpt) == 1
            Path(f.name).unlink()

    def test_wkb_roundtrip(self) -> None:
        """Test WKB roundtrip conversion for a single point."""
        waypoint = Waypoint(lat=Latitude("52.52"), lon=Longitude("13.405"))
        gpx1 = GPX(wpt=[waypoint])
        wkb = gpx1.to_wkb()
        gpx2 = from_wkb(wkb)
        assert len(gpx2.wpt) == 1
        assert float(gpx2.wpt[0].lat) == pytest.approx(float(gpx1.wpt[0].lat), rel=1e-3)


# =============================================================================
# GPX file I/O tests
# =============================================================================


class TestGPXFileIO:
    """Tests for GPX file reading."""

    def test_read_gpx_function(self, full_gpx_string: str) -> None:
        """Test read_gpx function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False) as f:
            f.write(full_gpx_string)
            f.flush()
            gpx = read_gpx(f.name)
            assert gpx.metadata is not None
            assert len(gpx.wpt) >= 1
            Path(f.name).unlink()


# =============================================================================
# Error handling tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling in conversion functions."""

    def test_from_geojson_unsupported_type(self) -> None:
        """Test that unsupported GeoJSON types raise ValueError."""
        geojson = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
        # Polygon is not directly convertible to GPX elements
        with pytest.raises(ValueError, match="Unsupported GeoJSON type"):
            from_geojson(geojson)

    def test_from_wkt_invalid_format(self) -> None:
        """Test that invalid WKT raises ValueError."""
        with pytest.raises(ValueError, match="Invalid WKT"):
            from_wkt("INVALID GEOMETRY")

    def test_from_wkb_invalid_byte_order(self) -> None:
        """Test that invalid WKB byte order raises ValueError."""
        wkb = b"\x02"  # Invalid byte order marker
        with pytest.raises(ValueError, match="Invalid WKB byte order"):
            from_wkb(wkb)

    def test_from_wkb_unexpected_end(self) -> None:
        """Test that truncated WKB raises ValueError."""
        wkb = b"\x01"  # Only byte order, no geometry type
        with pytest.raises((ValueError, struct.error)):
            from_wkb(wkb)
