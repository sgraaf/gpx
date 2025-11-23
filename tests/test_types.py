"""Tests for gpx.types module."""

from decimal import Decimal

import pytest

from gpx.types import Degrees, DGPSStation, Fix, Latitude, Longitude


class TestLatitude:
    """Tests for the Latitude type."""

    def test_valid_latitude_from_string(self):
        """Test creating Latitude from valid string values."""
        lat = Latitude("45.5")
        assert lat == Decimal("45.5")

    def test_valid_latitude_from_int(self):
        """Test creating Latitude from valid int values."""
        lat = Latitude(45)
        assert lat == Decimal("45")

    def test_valid_latitude_from_float(self):
        """Test creating Latitude from valid float values."""
        lat = Latitude(45.5)
        assert float(lat) == pytest.approx(45.5)

    def test_valid_latitude_from_decimal(self):
        """Test creating Latitude from Decimal."""
        lat = Latitude(Decimal("45.5"))
        assert lat == Decimal("45.5")

    def test_latitude_boundary_min(self):
        """Test Latitude at minimum boundary (-90)."""
        lat = Latitude(-90)
        assert lat == Decimal("-90")

    def test_latitude_boundary_max(self):
        """Test Latitude at maximum boundary (90)."""
        lat = Latitude(90)
        assert lat == Decimal("90")

    def test_latitude_zero(self):
        """Test Latitude at zero (equator)."""
        lat = Latitude(0)
        assert lat == Decimal("0")

    def test_invalid_latitude_below_min(self):
        """Test that Latitude below -90 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid latitude value"):
            Latitude(-90.1)

    def test_invalid_latitude_above_max(self):
        """Test that Latitude above 90 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid latitude value"):
            Latitude(90.1)

    def test_invalid_latitude_non_numeric(self):
        """Test that non-numeric string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid latitude value"):
            Latitude("not_a_number")

    def test_latitude_is_decimal_subclass(self):
        """Test that Latitude is a Decimal subclass."""
        lat = Latitude(45)
        assert isinstance(lat, Decimal)


class TestLongitude:
    """Tests for the Longitude type."""

    def test_valid_longitude_from_string(self):
        """Test creating Longitude from valid string values."""
        lon = Longitude("90.5")
        assert lon == Decimal("90.5")

    def test_valid_longitude_from_int(self):
        """Test creating Longitude from valid int values."""
        lon = Longitude(90)
        assert lon == Decimal("90")

    def test_valid_longitude_from_float(self):
        """Test creating Longitude from valid float values."""
        lon = Longitude(90.5)
        assert float(lon) == pytest.approx(90.5)

    def test_longitude_boundary_min(self):
        """Test Longitude at minimum boundary (-180)."""
        lon = Longitude(-180)
        assert lon == Decimal("-180")

    def test_longitude_boundary_max(self):
        """Test Longitude at maximum boundary (180)."""
        lon = Longitude(180)
        assert lon == Decimal("180")

    def test_longitude_zero(self):
        """Test Longitude at zero (prime meridian)."""
        lon = Longitude(0)
        assert lon == Decimal("0")

    def test_invalid_longitude_below_min(self):
        """Test that Longitude below -180 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid longitude value"):
            Longitude(-180.1)

    def test_invalid_longitude_above_max(self):
        """Test that Longitude above 180 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid longitude value"):
            Longitude(180.1)

    def test_invalid_longitude_non_numeric(self):
        """Test that non-numeric string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid longitude value"):
            Longitude("not_a_number")

    def test_longitude_is_decimal_subclass(self):
        """Test that Longitude is a Decimal subclass."""
        lon = Longitude(90)
        assert isinstance(lon, Decimal)


class TestDegrees:
    """Tests for the Degrees type."""

    def test_valid_degrees_from_string(self):
        """Test creating Degrees from valid string values."""
        deg = Degrees("180.5")
        assert deg == Decimal("180.5")

    def test_valid_degrees_from_int(self):
        """Test creating Degrees from valid int values."""
        deg = Degrees(180)
        assert deg == Decimal("180")

    def test_valid_degrees_from_float(self):
        """Test creating Degrees from valid float values."""
        deg = Degrees(180.5)
        assert float(deg) == pytest.approx(180.5)

    def test_degrees_boundary_min(self):
        """Test Degrees at minimum boundary (0)."""
        deg = Degrees(0)
        assert deg == Decimal("0")

    def test_degrees_boundary_almost_max(self):
        """Test Degrees just below maximum (359.999)."""
        deg = Degrees("359.999")
        assert deg == Decimal("359.999")

    def test_invalid_degrees_negative(self):
        """Test that negative Degrees raises ValueError."""
        with pytest.raises(ValueError, match="Invalid degrees value"):
            Degrees(-0.1)

    def test_invalid_degrees_at_360(self):
        """Test that Degrees at 360 raises ValueError (exclusive upper bound)."""
        with pytest.raises(ValueError, match="Invalid degrees value"):
            Degrees(360)

    def test_invalid_degrees_above_360(self):
        """Test that Degrees above 360 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid degrees value"):
            Degrees(360.1)

    def test_invalid_degrees_non_numeric(self):
        """Test that non-numeric string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid degrees value"):
            Degrees("north")

    def test_degrees_is_decimal_subclass(self):
        """Test that Degrees is a Decimal subclass."""
        deg = Degrees(180)
        assert isinstance(deg, Decimal)


class TestFix:
    """Tests for the Fix type."""

    def test_valid_fix_none(self):
        """Test creating Fix with 'none' value."""
        fix = Fix("none")
        assert fix == "none"

    def test_valid_fix_2d(self):
        """Test creating Fix with '2d' value."""
        fix = Fix("2d")
        assert fix == "2d"

    def test_valid_fix_3d(self):
        """Test creating Fix with '3d' value."""
        fix = Fix("3d")
        assert fix == "3d"

    def test_valid_fix_dgps(self):
        """Test creating Fix with 'dgps' value."""
        fix = Fix("dgps")
        assert fix == "dgps"

    def test_valid_fix_pps(self):
        """Test creating Fix with 'pps' value."""
        fix = Fix("pps")
        assert fix == "pps"

    def test_invalid_fix_unknown(self):
        """Test that unknown fix value raises ValueError."""
        with pytest.raises(ValueError, match="Invalid fix value"):
            Fix("unknown")

    def test_invalid_fix_uppercase(self):
        """Test that uppercase fix values are rejected."""
        with pytest.raises(ValueError, match="Invalid fix value"):
            Fix("3D")

    def test_invalid_fix_empty(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid fix value"):
            Fix("")

    def test_fix_is_str_subclass(self):
        """Test that Fix is a str subclass."""
        fix = Fix("3d")
        assert isinstance(fix, str)

    def test_fix_allowed_values(self):
        """Test that ALLOWED_VALUES contains expected values."""
        assert Fix.ALLOWED_VALUES == ("none", "2d", "3d", "dgps", "pps")


class TestDGPSStation:
    """Tests for the DGPSStation type."""

    def test_valid_dgps_station_min(self):
        """Test creating DGPSStation at minimum (0)."""
        station = DGPSStation(0)
        assert station == 0

    def test_valid_dgps_station_max(self):
        """Test creating DGPSStation at maximum (1023)."""
        station = DGPSStation(1023)
        assert station == 1023

    def test_valid_dgps_station_mid(self):
        """Test creating DGPSStation with middle value."""
        station = DGPSStation(512)
        assert station == 512

    def test_invalid_dgps_station_negative(self):
        """Test that negative DGPSStation raises ValueError."""
        with pytest.raises(ValueError, match="Invalid DGPS station value"):
            DGPSStation(-1)

    def test_invalid_dgps_station_above_max(self):
        """Test that DGPSStation above 1023 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid DGPS station value"):
            DGPSStation(1024)

    def test_dgps_station_is_int_subclass(self):
        """Test that DGPSStation is an int subclass."""
        station = DGPSStation(100)
        assert isinstance(station, int)
