"""Tests for gpx.bounds module."""

import xml.etree.ElementTree as ET
from decimal import Decimal
from typing import Any

import pytest

from gpx import Bounds, GPX
from gpx.types import Latitude, Longitude

#: GPX 1.1 namespace
GPX_NAMESPACE = "http://www.topografix.com/GPX/1/1"


class TestBoundsCreation:
    """Tests for creating bounds programmatically."""

    def test_create_bounds_with_valid_coordinates(self) -> None:
        """Test creating bounds with valid coordinates."""
        bounds = Bounds(
            minlat=Latitude("52.5"),
            minlon=Longitude("13.4"),
            maxlat=Latitude("52.6"),
            maxlon=Longitude("13.5"),
        )

        assert bounds.minlat == Latitude("52.5")
        assert bounds.minlon == Longitude("13.4")
        assert bounds.maxlat == Latitude("52.6")
        assert bounds.maxlon == Longitude("13.5")

    def test_create_bounds_with_decimal_strings(self) -> None:
        """Test creating bounds with decimal string values."""
        bounds = Bounds(
            minlat=Latitude("45.123456"),
            minlon=Longitude("-122.654321"),
            maxlat=Latitude("45.234567"),
            maxlon=Longitude("-122.543210"),
        )

        assert bounds.minlat == Latitude("45.123456")
        assert bounds.minlon == Longitude("-122.654321")
        assert bounds.maxlat == Latitude("45.234567")
        assert bounds.maxlon == Longitude("-122.543210")

    def test_create_bounds_with_integer_values(self) -> None:
        """Test creating bounds with integer values."""
        bounds = Bounds(
            minlat=Latitude("50"),
            minlon=Longitude("10"),
            maxlat=Latitude("51"),
            maxlon=Longitude("11"),
        )

        assert bounds.minlat == Latitude("50")
        assert bounds.minlon == Longitude("10")
        assert bounds.maxlat == Latitude("51")
        assert bounds.maxlon == Longitude("11")

    def test_create_bounds_with_negative_coordinates(self) -> None:
        """Test creating bounds with negative coordinates."""
        bounds = Bounds(
            minlat=Latitude("-45.5"),
            minlon=Longitude("-120.5"),
            maxlat=Latitude("-45.0"),
            maxlon=Longitude("-120.0"),
        )

        assert bounds.minlat == Latitude("-45.5")
        assert bounds.minlon == Longitude("-120.5")
        assert bounds.maxlat == Latitude("-45.0")
        assert bounds.maxlon == Longitude("-120.0")

    def test_create_bounds_world_extent(self) -> None:
        """Test creating bounds covering the entire world."""
        bounds = Bounds(
            minlat=Latitude("-90"),
            minlon=Longitude("-180"),
            maxlat=Latitude("90"),
            maxlon=Longitude("180"),
        )

        assert bounds.minlat == Latitude("-90")
        assert bounds.minlon == Longitude("-180")
        assert bounds.maxlat == Latitude("90")
        assert bounds.maxlon == Longitude("180")


class TestBoundsValidation:
    """Tests for bounds coordinate validation."""

    def test_invalid_latitude_too_high(self) -> None:
        """Test that latitude > 90 raises ValueError."""
        with pytest.raises(ValueError, match=r"Invalid latitude value.*Must be between"):
            Bounds(
                minlat=Latitude("52.5"),
                minlon=Longitude("13.4"),
                maxlat=Latitude("91.0"),
                maxlon=Longitude("13.5"),
            )

    def test_invalid_latitude_too_low(self) -> None:
        """Test that latitude < -90 raises ValueError."""
        with pytest.raises(ValueError, match=r"Invalid latitude value.*Must be between"):
            Bounds(
                minlat=Latitude("-91.0"),
                minlon=Longitude("13.4"),
                maxlat=Latitude("52.6"),
                maxlon=Longitude("13.5"),
            )

    def test_invalid_longitude_too_high(self) -> None:
        """Test that longitude > 180 raises ValueError."""
        with pytest.raises(ValueError, match=r"Invalid longitude value.*Must be between"):
            Bounds(
                minlat=Latitude("52.5"),
                minlon=Longitude("13.4"),
                maxlat=Latitude("52.6"),
                maxlon=Longitude("181.0"),
            )

    def test_invalid_longitude_too_low(self) -> None:
        """Test that longitude < -180 raises ValueError."""
        with pytest.raises(ValueError, match=r"Invalid longitude value.*Must be between"):
            Bounds(
                minlat=Latitude("52.5"),
                minlon=Longitude("-181.0"),
                maxlat=Latitude("52.6"),
                maxlon=Longitude("13.5"),
            )


class TestBoundsParsing:
    """Tests for parsing bounds from XML."""

    @pytest.fixture
    def gpx_with_bounds_string(self) -> str:
        """A GPX string with bounds in metadata."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
     version="1.1"
     creator="TestCreator">
  <metadata>
    <bounds minlat="52.5" minlon="13.4" maxlat="52.6" maxlon="13.5"/>
  </metadata>
</gpx>"""

    @pytest.fixture
    def gpx_with_precise_bounds_string(self) -> str:
        """A GPX string with high-precision bounds."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
     version="1.1"
     creator="TestCreator">
  <metadata>
    <bounds minlat="45.123456789" minlon="-122.987654321" maxlat="45.234567890" maxlon="-122.876543210"/>
  </metadata>
</gpx>"""

    def test_parse_bounds_basic(self, gpx_with_bounds_string: str) -> None:
        """Test parsing basic bounds from XML."""
        gpx = GPX.from_string(gpx_with_bounds_string)
        assert gpx.metadata is not None
        assert gpx.metadata.bounds is not None

        bounds = gpx.metadata.bounds
        assert bounds.minlat == Latitude("52.5")
        assert bounds.minlon == Longitude("13.4")
        assert bounds.maxlat == Latitude("52.6")
        assert bounds.maxlon == Longitude("13.5")

    def test_parse_bounds_precise(self, gpx_with_precise_bounds_string: str) -> None:
        """Test parsing high-precision bounds from XML."""
        gpx = GPX.from_string(gpx_with_precise_bounds_string)
        assert gpx.metadata is not None
        assert gpx.metadata.bounds is not None

        bounds = gpx.metadata.bounds
        assert bounds.minlat == Latitude("45.123456789")
        assert bounds.minlon == Longitude("-122.987654321")
        assert bounds.maxlat == Latitude("45.234567890")
        assert bounds.maxlon == Longitude("-122.876543210")

    def test_parse_bounds_directly_from_xml(self) -> None:
        """Test parsing bounds directly from XML element."""
        xml_string = """<bounds xmlns="http://www.topografix.com/GPX/1/1" minlat="52.5" minlon="13.4" maxlat="52.6" maxlon="13.5"/>"""
        element = ET.fromstring(xml_string)
        bounds = Bounds.from_xml(element)

        assert bounds.minlat == Latitude("52.5")
        assert bounds.minlon == Longitude("13.4")
        assert bounds.maxlat == Latitude("52.6")
        assert bounds.maxlon == Longitude("13.5")


class TestBoundsBuilding:
    """Tests for building bounds to XML."""

    def test_build_bounds_to_xml(self, sample_bounds: Bounds) -> None:
        """Test building bounds to XML element."""
        element = sample_bounds.to_xml()

        assert element.tag == f"{{{GPX_NAMESPACE}}}bounds"
        assert element.get("minlat") == "52.5"
        assert element.get("minlon") == "13.4"
        assert element.get("maxlat") == "52.6"
        assert element.get("maxlon") == "13.5"

    def test_build_bounds_with_precise_values(self) -> None:
        """Test building bounds with high-precision values."""
        bounds = Bounds(
            minlat=Latitude("45.123456789"),
            minlon=Longitude("-122.987654321"),
            maxlat=Latitude("45.234567890"),
            maxlon=Longitude("-122.876543210"),
        )
        element = bounds.to_xml()

        assert element.get("minlat") == "45.123456789"
        assert element.get("minlon") == "-122.987654321"
        assert element.get("maxlat") == "45.234567890"
        assert element.get("maxlon") == "-122.876543210"

    def test_build_bounds_with_negative_coordinates(self) -> None:
        """Test building bounds with negative coordinates."""
        bounds = Bounds(
            minlat=Latitude("-45.5"),
            minlon=Longitude("-120.5"),
            maxlat=Latitude("-45.0"),
            maxlon=Longitude("-120.0"),
        )
        element = bounds.to_xml()

        assert element.get("minlat") == "-45.5"
        assert element.get("minlon") == "-120.5"
        assert element.get("maxlat") == "-45.0"
        assert element.get("maxlon") == "-120.0"

    def test_build_bounds_no_child_elements(self, sample_bounds: Bounds) -> None:
        """Test that bounds XML has no child elements (all attributes)."""
        element = sample_bounds.to_xml()
        assert len(list(element)) == 0  # No child elements


class TestBoundsRoundtrip:
    """Tests for parsing and building bounds (roundtrip)."""

    def test_bounds_roundtrip_basic(self, sample_bounds: Bounds) -> None:
        """Test that bounds can be converted to XML and back."""
        element = sample_bounds.to_xml()
        bounds2 = Bounds.from_xml(element)

        assert bounds2.minlat == sample_bounds.minlat
        assert bounds2.minlon == sample_bounds.minlon
        assert bounds2.maxlat == sample_bounds.maxlat
        assert bounds2.maxlon == sample_bounds.maxlon

    def test_bounds_roundtrip_with_gpx(self) -> None:
        """Test bounds roundtrip through full GPX serialization."""
        gpx_string = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1"
     version="1.1"
     creator="TestCreator">
  <metadata>
    <bounds minlat="45.123" minlon="-122.987" maxlat="45.234" maxlon="-122.876"/>
  </metadata>
</gpx>"""

        gpx1 = GPX.from_string(gpx_string)
        gpx_output = gpx1.to_string()
        gpx2 = GPX.from_string(gpx_output)

        assert gpx2.metadata is not None
        assert gpx2.metadata.bounds is not None
        assert gpx1.metadata is not None
        assert gpx1.metadata.bounds is not None

        assert gpx2.metadata.bounds.minlat == gpx1.metadata.bounds.minlat
        assert gpx2.metadata.bounds.minlon == gpx1.metadata.bounds.minlon
        assert gpx2.metadata.bounds.maxlat == gpx1.metadata.bounds.maxlat
        assert gpx2.metadata.bounds.maxlon == gpx1.metadata.bounds.maxlon


class TestBoundsAsTuple:
    """Tests for the as_tuple() method."""

    def test_as_tuple_returns_correct_order(self, sample_bounds: Bounds) -> None:
        """Test that as_tuple returns coordinates in correct order."""
        result = sample_bounds.as_tuple()

        assert result == (
            Latitude("52.5"),
            Longitude("13.4"),
            Latitude("52.6"),
            Longitude("13.5"),
        )

    def test_as_tuple_returns_tuple_type(self, sample_bounds: Bounds) -> None:
        """Test that as_tuple returns a tuple."""
        result = sample_bounds.as_tuple()
        assert isinstance(result, tuple)
        assert len(result) == 4

    def test_as_tuple_preserves_precision(self) -> None:
        """Test that as_tuple preserves coordinate precision."""
        bounds = Bounds(
            minlat=Latitude("45.123456789"),
            minlon=Longitude("-122.987654321"),
            maxlat=Latitude("45.234567890"),
            maxlon=Longitude("-122.876543210"),
        )
        result = bounds.as_tuple()

        assert result[0] == Latitude("45.123456789")
        assert result[1] == Longitude("-122.987654321")
        assert result[2] == Latitude("45.234567890")
        assert result[3] == Longitude("-122.876543210")


class TestBoundsSequenceProtocol:
    """Tests for sequence protocol implementation (__getitem__, __iter__, __len__)."""

    def test_getitem_by_index(self, sample_bounds: Bounds) -> None:
        """Test accessing bounds coordinates by index."""
        assert sample_bounds[0] == Latitude("52.5")
        assert sample_bounds[1] == Longitude("13.4")
        assert sample_bounds[2] == Latitude("52.6")
        assert sample_bounds[3] == Longitude("13.5")

    def test_getitem_negative_index(self, sample_bounds: Bounds) -> None:
        """Test accessing bounds with negative indices."""
        assert sample_bounds[-1] == Longitude("13.5")
        assert sample_bounds[-2] == Latitude("52.6")
        assert sample_bounds[-3] == Longitude("13.4")
        assert sample_bounds[-4] == Latitude("52.5")

    def test_getitem_out_of_range(self, sample_bounds: Bounds) -> None:
        """Test that accessing out-of-range index raises IndexError."""
        with pytest.raises(IndexError):
            _ = sample_bounds[4]

        with pytest.raises(IndexError):
            _ = sample_bounds[-5]

    def test_len_returns_four(self, sample_bounds: Bounds) -> None:
        """Test that len() returns 4 for bounds."""
        assert len(sample_bounds) == 4

    def test_iter_yields_all_coordinates(self, sample_bounds: Bounds) -> None:
        """Test that iterating yields all coordinates in order."""
        coords = list(sample_bounds)

        assert len(coords) == 4
        assert coords[0] == Latitude("52.5")
        assert coords[1] == Longitude("13.4")
        assert coords[2] == Latitude("52.6")
        assert coords[3] == Longitude("13.5")

    def test_iter_with_unpacking(self, sample_bounds: Bounds) -> None:
        """Test unpacking bounds using iteration."""
        minlat, minlon, maxlat, maxlon = sample_bounds

        assert minlat == Latitude("52.5")
        assert minlon == Longitude("13.4")
        assert maxlat == Latitude("52.6")
        assert maxlon == Longitude("13.5")

    def test_iter_in_for_loop(self, sample_bounds: Bounds) -> None:
        """Test iterating over bounds in a for loop."""
        coords = []
        for coord in sample_bounds:
            coords.append(coord)

        assert len(coords) == 4
        assert coords == [
            Latitude("52.5"),
            Longitude("13.4"),
            Latitude("52.6"),
            Longitude("13.5"),
        ]

    def test_contains_not_supported(self, sample_bounds: Bounds) -> None:
        """Test that 'in' operator is not supported (no __contains__)."""
        # This will use the default iterator-based containment check
        # which is technically supported, but not the intended use case
        assert Latitude("52.5") in sample_bounds


class TestBoundsGeoInterface:
    """Tests for the __geo_interface__ property."""

    def test_geo_interface_returns_polygon(self, sample_bounds: Bounds) -> None:
        """Test that __geo_interface__ returns a Polygon geometry."""
        geo = sample_bounds.__geo_interface__

        assert geo["type"] == "Polygon"
        assert "coordinates" in geo

    def test_geo_interface_coordinates_structure(self, sample_bounds: Bounds) -> None:
        """Test the structure of coordinates in GeoJSON output."""
        geo = sample_bounds.__geo_interface__

        coords = geo["coordinates"]
        assert isinstance(coords, list)
        assert len(coords) == 1  # One ring (exterior)
        assert len(coords[0]) == 5  # Five points (closed ring)

    def test_geo_interface_coordinates_order(self, sample_bounds: Bounds) -> None:
        """Test that coordinates follow GeoJSON [lon, lat] order."""
        geo = sample_bounds.__geo_interface__

        ring = geo["coordinates"][0]
        # First point: bottom-left (minlon, minlat)
        assert ring[0] == [13.4, 52.5]
        # Second point: bottom-right (maxlon, minlat)
        assert ring[1] == [13.5, 52.5]
        # Third point: top-right (maxlon, maxlat)
        assert ring[2] == [13.5, 52.6]
        # Fourth point: top-left (minlon, maxlat)
        assert ring[3] == [13.4, 52.6]
        # Fifth point: close the ring (minlon, minlat)
        assert ring[4] == [13.4, 52.5]

    def test_geo_interface_ring_is_closed(self, sample_bounds: Bounds) -> None:
        """Test that the polygon ring is properly closed."""
        geo = sample_bounds.__geo_interface__

        ring = geo["coordinates"][0]
        # First and last points should be identical
        assert ring[0] == ring[-1]

    def test_geo_interface_with_negative_coordinates(self) -> None:
        """Test GeoJSON output with negative coordinates."""
        bounds = Bounds(
            minlat=Latitude("-45.5"),
            minlon=Longitude("-120.5"),
            maxlat=Latitude("-45.0"),
            maxlon=Longitude("-120.0"),
        )
        geo = bounds.__geo_interface__

        ring = geo["coordinates"][0]
        assert ring[0] == [-120.5, -45.5]
        assert ring[1] == [-120.0, -45.5]
        assert ring[2] == [-120.0, -45.0]
        assert ring[3] == [-120.5, -45.0]
        assert ring[4] == [-120.5, -45.5]

    def test_geo_interface_values_are_floats(self, sample_bounds: Bounds) -> None:
        """Test that coordinate values in GeoJSON are floats."""
        geo = sample_bounds.__geo_interface__

        ring = geo["coordinates"][0]
        for point in ring:
            assert isinstance(point[0], float)  # longitude
            assert isinstance(point[1], float)  # latitude

    def test_geo_interface_dict_structure(self, sample_bounds: Bounds) -> None:
        """Test the complete dictionary structure of __geo_interface__."""
        geo = sample_bounds.__geo_interface__

        # Should be a dict
        assert isinstance(geo, dict)
        # Should have exactly 2 keys
        assert set(geo.keys()) == {"type", "coordinates"}
        # Type should be Polygon
        assert geo["type"] == "Polygon"
        # Coordinates should be a list
        assert isinstance(geo["coordinates"], list)


class TestBoundsRepresentation:
    """Tests for bounds string representation."""

    def test_bounds_repr(self, sample_bounds: Bounds) -> None:
        """Test bounds __repr__ output."""
        repr_str = repr(sample_bounds)
        assert "Bounds" in repr_str
        assert "minlat=" in repr_str
        assert "minlon=" in repr_str
        assert "maxlat=" in repr_str
        assert "maxlon=" in repr_str

    def test_bounds_repr_contains_values(self, sample_bounds: Bounds) -> None:
        """Test that __repr__ contains coordinate values."""
        repr_str = repr(sample_bounds)
        assert "52.5" in repr_str
        assert "13.4" in repr_str
        assert "52.6" in repr_str
        assert "13.5" in repr_str


class TestBoundsEquality:
    """Tests for bounds equality comparison."""

    def test_bounds_equality_same_values(self) -> None:
        """Test that bounds with same values are equal."""
        bounds1 = Bounds(
            minlat=Latitude("52.5"),
            minlon=Longitude("13.4"),
            maxlat=Latitude("52.6"),
            maxlon=Longitude("13.5"),
        )
        bounds2 = Bounds(
            minlat=Latitude("52.5"),
            minlon=Longitude("13.4"),
            maxlat=Latitude("52.6"),
            maxlon=Longitude("13.5"),
        )

        assert bounds1 == bounds2

    def test_bounds_inequality_different_values(self) -> None:
        """Test that bounds with different values are not equal."""
        bounds1 = Bounds(
            minlat=Latitude("52.5"),
            minlon=Longitude("13.4"),
            maxlat=Latitude("52.6"),
            maxlon=Longitude("13.5"),
        )
        bounds2 = Bounds(
            minlat=Latitude("52.5"),
            minlon=Longitude("13.4"),
            maxlat=Latitude("52.7"),  # Different maxlat
            maxlon=Longitude("13.5"),
        )

        assert bounds1 != bounds2

    def test_bounds_equality_with_self(self, sample_bounds: Bounds) -> None:
        """Test that bounds is equal to itself."""
        assert sample_bounds == sample_bounds

    def test_bounds_inequality_with_none(self, sample_bounds: Bounds) -> None:
        """Test that bounds is not equal to None."""
        assert sample_bounds != None  # noqa: E711

    def test_bounds_inequality_with_different_type(
        self, sample_bounds: Bounds
    ) -> None:
        """Test that bounds is not equal to a different type."""
        assert sample_bounds != "not a bounds"
        assert sample_bounds != 42
        assert sample_bounds != [52.5, 13.4, 52.6, 13.5]


class TestBoundsEdgeCases:
    """Tests for bounds edge cases."""

    def test_bounds_with_zero_area(self) -> None:
        """Test bounds representing a single point (zero area)."""
        bounds = Bounds(
            minlat=Latitude("52.5"),
            minlon=Longitude("13.4"),
            maxlat=Latitude("52.5"),
            maxlon=Longitude("13.4"),
        )

        assert bounds.minlat == bounds.maxlat
        assert bounds.minlon == bounds.maxlon

    def test_bounds_crossing_prime_meridian(self) -> None:
        """Test bounds crossing the prime meridian."""
        bounds = Bounds(
            minlat=Latitude("50.0"),
            minlon=Longitude("-10.0"),
            maxlat=Latitude("55.0"),
            maxlon=Longitude("10.0"),
        )

        assert bounds.minlon < Longitude("0")
        assert bounds.maxlon > Longitude("0")

    def test_bounds_crossing_equator(self) -> None:
        """Test bounds crossing the equator."""
        bounds = Bounds(
            minlat=Latitude("-10.0"),
            minlon=Longitude("50.0"),
            maxlat=Latitude("10.0"),
            maxlon=Longitude("60.0"),
        )

        assert bounds.minlat < Latitude("0")
        assert bounds.maxlat > Latitude("0")

    def test_bounds_at_poles(self) -> None:
        """Test bounds at the north and south poles."""
        north_pole_bounds = Bounds(
            minlat=Latitude("89.9"),
            minlon=Longitude("-180"),
            maxlat=Latitude("90"),
            maxlon=Longitude("180"),
        )

        south_pole_bounds = Bounds(
            minlat=Latitude("-90"),
            minlon=Longitude("-180"),
            maxlat=Latitude("-89.9"),
            maxlon=Longitude("180"),
        )

        assert north_pole_bounds.maxlat == Latitude("90")
        assert south_pole_bounds.minlat == Latitude("-90")

    def test_bounds_at_international_date_line(self) -> None:
        """Test bounds at the international date line."""
        bounds = Bounds(
            minlat=Latitude("50.0"),
            minlon=Longitude("179.0"),
            maxlat=Latitude("55.0"),
            maxlon=Longitude("180.0"),
        )

        assert bounds.maxlon == Longitude("180")
