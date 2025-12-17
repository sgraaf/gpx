"""I/O functions for reading various file formats into GPX.

This module provides functions for reading GPX, GeoJSON, KML, WKB, and WKT
files from disk and returning GPX objects.
"""

from __future__ import annotations

import json
from pathlib import Path

from .convert import from_geojson, from_kml, from_wkb, from_wkt
from .gpx import GPX


def read_gpx(file_path: str | Path) -> GPX:
    """Read a GPX file and return a GPX object.

    This is an alias for GPX.from_file().

    Args:
        file_path: Path to the GPX file.

    Returns:
        A GPX object.

    Example:
        >>> from gpx.io import read_gpx
        >>> gpx = read_gpx("path/to/file.gpx")

    """
    return GPX.from_file(file_path)


def read_geojson(file_path: str | Path, *, creator: str | None = None) -> GPX:
    """Read a GeoJSON file and return a GPX object.

    Args:
        file_path: Path to the GeoJSON file.
        creator: The creator string for the GPX. Defaults to None (uses default).

    Returns:
        A GPX object.

    Example:
        >>> from gpx.io import read_geojson
        >>> gpx = read_geojson("path/to/file.geojson")

    """
    with Path(file_path).open(encoding="utf-8") as f:
        data = json.load(f)
    return from_geojson(data, creator=creator)


def read_kml(file_path: str | Path, *, creator: str | None = None) -> GPX:
    """Read a KML file and return a GPX object.

    Args:
        file_path: Path to the KML file.
        creator: The creator string for the GPX. Defaults to None (uses default).

    Returns:
        A GPX object.

    Example:
        >>> from gpx.io import read_kml
        >>> gpx = read_kml("path/to/file.kml")

    """
    with Path(file_path).open(encoding="utf-8") as f:
        kml_str = f.read()
    return from_kml(kml_str, creator=creator)


def read_wkb(file_path: str | Path, *, creator: str | None = None) -> GPX:
    """Read a WKB (Well-Known Binary) file and return a GPX object.

    Args:
        file_path: Path to the WKB file.
        creator: The creator string for the GPX. Defaults to None (uses default).

    Returns:
        A GPX object.

    Example:
        >>> from gpx.io import read_wkb
        >>> gpx = read_wkb("path/to/file.wkb")

    """
    with Path(file_path).open("rb") as f:
        wkb_data = f.read()
    return from_wkb(wkb_data, creator=creator)


def read_wkt(file_path: str | Path, *, creator: str | None = None) -> GPX:
    """Read a WKT (Well-Known Text) file and return a GPX object.

    Args:
        file_path: Path to the WKT file.
        creator: The creator string for the GPX. Defaults to None (uses default).

    Returns:
        A GPX object.

    Example:
        >>> from gpx.io import read_wkt
        >>> gpx = read_wkt("path/to/file.wkt")

    """
    with Path(file_path).open(encoding="utf-8") as f:
        wkt_str = f.read()
    return from_wkt(wkt_str, creator=creator)
