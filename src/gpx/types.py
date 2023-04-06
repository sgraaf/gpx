"""This module provides simple type objects to contain various GPX data."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation


class Latitude(Decimal):
    """A latitude class for the GPX data format.

    The latitude of the point. Decimal degrees, WGS84 datum.

    Args:
        value: The latitude value.
    """

    def __new__(cls, value: str | int | float | Decimal) -> Latitude:
        # try to convert value to Decimal (raises ValueError if not possible)
        try:
            decimal_value = Decimal(value)
        except InvalidOperation as e:
            raise ValueError(f"Invalid latitude value: '{value}'.") from e

        if not -90 <= decimal_value <= 90:
            raise ValueError(
                f"Invalid latitude value: '{value}'. Must be between [-90.0, 90.0]."
            )

        return super().__new__(cls, decimal_value)


class Longitude(Decimal):
    """A longitude class for the GPX data format.

    The longitude of the point. Decimal degrees, WGS84 datum.

    Args:
        value: The longitude value.
    """

    def __new__(cls, value: str | int | float | Decimal) -> Longitude:
        # try to convert value to Decimal (raises ValueError if not possible)
        try:
            decimal_value = Decimal(value)
        except InvalidOperation as e:
            raise ValueError(f"Invalid longitude value: '{value}'.") from e

        if not -180 <= decimal_value <= 180:
            raise ValueError(
                f"Invalid longitude value: '{value}'. Must be between [-180.0, 180.0]."
            )

        return super().__new__(cls, decimal_value)


class Degrees(Decimal):
    """A degrees class for the GPX data format.

    Used for bearing, heading, course. Units are decimal degrees, true (not
    magnetic).

    Args:
        value: The degrees value.
    """

    def __new__(cls, value: str | int | float | Decimal) -> Degrees:
        # try to convert value to Decimal (raises ValueError if not possible)
        try:
            decimal_value = Decimal(value)
        except InvalidOperation as e:
            raise ValueError(f"Invalid degrees value: '{value}'.") from e

        if not 0 <= decimal_value < 360:
            raise ValueError(
                f"Invalid degrees value: '{value}'. Must be between [0.0, 360.0)."
            )

        return super().__new__(cls, decimal_value)


class Fix(str):
    """A fix class for the GPX data format.

    Type of GPS fix. None means GPS had no fix. To signify "the fix info is
    unknown", leave out fix entirely. `pps` = military signal used.

    Args:
        value: The fix value.
    """

    ALLOWED_VALUES = ("none", "2d", "3d", "dgps", "pps")

    def __new__(cls, value: str) -> Fix:
        if value not in cls.ALLOWED_VALUES:
            raise ValueError(
                f"Invalid fix value: '{value}'. Must be one of {', '.join(cls.ALLOWED_VALUES)}."
            )

        return super().__new__(cls, value)


class DGPSStation(int):
    """A DGPS station class for the GPX data format.

    Represents a differential GPS station.

    Args:
        value: The DGPS station value.
    """

    def __new__(cls, value: int) -> DGPSStation:
        if not 0 <= value <= 1023:
            raise ValueError(
                f"Invalid DGPS station value: '{value}'. Must be between [0, 1023]."
            )

        return super().__new__(cls, value)
