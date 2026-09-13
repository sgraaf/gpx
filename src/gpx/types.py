"""This module provides simple type objects to contain various GPX data."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol, Self, runtime_checkable

#: The lexical space of ``xsd:gYear``: a (possibly negative) year of at least
#: four digits, with an optional timezone.
_GYEAR_PATTERN = re.compile(r"(?P<year>-?\d{4,})(?P<timezone>Z|[+-]\d{2}:\d{2})?")


@runtime_checkable
class SupportsGeoInterface(Protocol):  # noqa: D101
    @property
    def __geo_interface__(self) -> dict[str, Any]: ...


class Latitude(Decimal):
    """A latitude class for the GPX data format.

    The latitude of the point. Decimal degrees, WGS84 datum.

    Args:
        value: The latitude value.

    Raises:
        ValueError: If the value is not a valid latitude (i.e. between `[-90.0, 90.0]`).

    """

    def __new__(cls, value: str | float | Decimal) -> Self:
        # try to convert value to Decimal (raises ValueError if not possible)
        try:
            decimal_value = Decimal(value)
        except InvalidOperation as e:
            msg = f"Invalid latitude value: '{value}'."
            raise ValueError(msg) from e

        # Check finiteness first: comparing NaN raises decimal.InvalidOperation
        if not decimal_value.is_finite() or not -90 <= decimal_value <= 90:  # noqa: PLR2004
            msg = f"Invalid latitude value: '{value}'. Must be between [-90.0, 90.0]."
            raise ValueError(
                msg,
            )

        return super().__new__(cls, decimal_value)


class Longitude(Decimal):
    """A longitude class for the GPX data format.

    The longitude of the point. Decimal degrees, WGS84 datum.

    Args:
        value: The longitude value.

    Raises:
        ValueError: If the value is not a valid latitude (i.e. between `[-180.0, 180.0]`).

    """

    def __new__(cls, value: str | float | Decimal) -> Self:
        # try to convert value to Decimal (raises ValueError if not possible)
        try:
            decimal_value = Decimal(value)
        except InvalidOperation as e:
            msg = f"Invalid longitude value: '{value}'."
            raise ValueError(msg) from e

        # Check finiteness first: comparing NaN raises decimal.InvalidOperation
        if not decimal_value.is_finite() or not -180 <= decimal_value <= 180:  # noqa: PLR2004
            msg = (
                f"Invalid longitude value: '{value}'. Must be between [-180.0, 180.0]."
            )
            raise ValueError(
                msg,
            )

        return super().__new__(cls, decimal_value)


class Degrees(Decimal):
    """A degrees class for the GPX data format.

    Used for bearing, heading, course. Units are decimal degrees, true (not
    magnetic).

    Args:
        value: The degrees value.

    Raises:
        ValueError: If the value is not a valid latitude (i.e. between `[0.0, 360.0)`).

    """

    def __new__(cls, value: str | float | Decimal) -> Self:
        # try to convert value to Decimal (raises ValueError if not possible)
        try:
            decimal_value = Decimal(value)
        except InvalidOperation as e:
            msg = f"Invalid degrees value: '{value}'."
            raise ValueError(msg) from e

        # Check finiteness first: comparing NaN raises decimal.InvalidOperation
        if not decimal_value.is_finite() or not 0 <= decimal_value < 360:  # noqa: PLR2004
            msg = f"Invalid degrees value: '{value}'. Must be between [0.0, 360.0)."
            raise ValueError(
                msg,
            )

        return super().__new__(cls, decimal_value)


class Fix(str):
    """A fix class for the GPX data format.

    Type of GPS fix. None means GPS had no fix. To signify "the fix info is
    unknown", leave out fix entirely. `pps` = military signal used.

    Args:
        value: The fix value.

    Raises:
        ValueError: If the value is not a valid fix (i.e. one of `none`, `2d`, `3d`, `dgps`, `pps`).

    """

    __slots__ = ()

    ALLOWED_VALUES = ("none", "2d", "3d", "dgps", "pps")

    def __new__(cls, value: str) -> Self:
        if value not in cls.ALLOWED_VALUES:
            msg = f"Invalid fix value: '{value}'. Must be one of {', '.join(cls.ALLOWED_VALUES)}."
            raise ValueError(
                msg,
            )

        return super().__new__(cls, value)


class DGPSStation(int):
    """A DGPS station class for the GPX data format.

    Represents a differential GPS station.

    Args:
        value: The DGPS station value.

    Raises:
        ValueError: If the value is not a valid DGPS station (i.e. between `[0, 1023]`).

    """

    def __new__(cls, value: int | str) -> Self:
        # Convert string to int if necessary (from XML parsing)
        try:
            int_value = int(value)
        except (ValueError, TypeError) as e:
            msg = f"Invalid DGPS station value: '{value}'."
            raise ValueError(msg) from e

        if not 0 <= int_value <= 1023:  # noqa: PLR2004
            msg = f"Invalid DGPS station value: '{value}'. Must be between [0, 1023]."
            raise ValueError(
                msg,
            )

        return super().__new__(cls, int_value)


class Year(int):
    """A year class for the GPX data format.

    Represents an ``xsd:gYear`` value, e.g. ``2004``, ``2004Z`` or
    ``2004+02:00``. The optional timezone is preserved (as :attr:`timezone`) so
    the year is written back as it was read. Comparisons use the year only.

    Args:
        value: The year, as an integer or as ``xsd:gYear`` text.

    Raises:
        ValueError: If the value is not a valid year (e.g. ``2004``, ``2004Z``
            or ``2004+02:00``).

    """

    #: The timezone suffix (``Z`` or ``±hh:mm``), or None if there is none.
    timezone: str | None

    def __new__(cls, value: int | str) -> Self:
        if isinstance(value, str):
            match = _GYEAR_PATTERN.fullmatch(value.strip())
            if match is None:
                msg = f"Invalid year value: '{value}'. Must be a year, e.g. 2004, 2004Z or 2004+02:00."
                raise ValueError(msg)
            year = super().__new__(cls, match["year"])
            year.timezone = match["timezone"]
        else:
            year = super().__new__(cls, value)
            year.timezone = value.timezone if isinstance(value, Year) else None
        return year

    def __str__(self) -> str:
        """Return the year as ``xsd:gYear`` text (at least four digits)."""
        sign = "-" if self < 0 else ""
        return f"{sign}{abs(self):04d}{self.timezone or ''}"
