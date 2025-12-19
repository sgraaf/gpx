"""Command-line interface for GPX operations.

This module provides a CLI for common GPX file operations including validation,
information display, cropping, trimming, merging, reversing, converting,
stripping metadata, and reducing coordinate precision.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

import click

from .gpx import GPX
from .io import read_geojson, read_gpx, read_kml
from .metadata import Metadata
from .route import Route
from .track import Track
from .track_segment import TrackSegment
from .types import Latitude, Longitude
from .waypoint import Waypoint


def _detect_format(file_path: Path) -> str:
    """Detect file format from extension.

    Args:
        file_path: Path to the file.

    Returns:
        The detected format: 'gpx', 'geojson', or 'kml'.

    Raises:
        click.ClickException: If the format is not supported.

    """
    suffix = file_path.suffix.lower()
    if suffix == ".gpx":
        return "gpx"
    if suffix in {".geojson", ".json"}:
        return "geojson"
    if suffix == ".kml":
        return "kml"
    msg = f"Unsupported file format: {suffix}"
    raise click.ClickException(msg)


def _read_file(file_path: Path, fmt: str | None = None) -> GPX:
    """Read a file and return a GPX object.

    Args:
        file_path: Path to the file.
        fmt: Optional format override. If None, detects from extension.

    Returns:
        A GPX object.

    """
    if fmt is None:
        fmt = _detect_format(file_path)

    if fmt == "gpx":
        return read_gpx(file_path)
    if fmt == "geojson":
        return read_geojson(file_path)
    if fmt == "kml":
        return read_kml(file_path)

    msg = f"Unsupported format: {fmt}"
    raise click.ClickException(msg)


def _write_file(gpx: GPX, file_path: Path, fmt: str | None = None) -> None:
    """Write a GPX object to a file.

    Args:
        gpx: The GPX object to write.
        file_path: Path to the output file.
        fmt: Optional format override. If None, detects from extension.

    """
    if fmt is None:
        fmt = _detect_format(file_path)

    if fmt == "gpx":
        gpx.write_gpx(file_path)
    elif fmt == "geojson":
        gpx.write_geojson(file_path)
    elif fmt == "kml":
        gpx.write_kml(file_path)
    else:
        msg = f"Unsupported format: {fmt}"
        raise click.ClickException(msg)


def _format_duration(total_seconds: float) -> str:
    """Format duration in human-readable format.

    Args:
        total_seconds: Duration in seconds.

    Returns:
        Formatted duration string.

    """
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)

    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def _format_distance(meters: float) -> str:
    """Format distance in human-readable format.

    Args:
        meters: Distance in meters.

    Returns:
        Formatted distance string.

    """
    if meters >= 1000:  # noqa: PLR2004
        return f"{meters / 1000:.2f} km"
    return f"{meters:.0f} m"


@click.group()
@click.version_option()
def main() -> None:
    """GPX file manipulation tool.

    A command-line interface for working with GPX (GPS Exchange Format) files.
    Supports validation, information display, cropping, trimming, merging,
    reversing, format conversion, metadata stripping, and precision reduction.
    """


@main.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
def validate(file: Path) -> None:
    """Validate a GPX file.

    Attempts to parse the GPX file and reports whether it is valid.

    FILE: Path to the GPX file to validate.
    """
    try:
        _read_file(file)
        click.echo(f"Valid: {file}")
    except Exception as e:  # noqa: BLE001
        click.echo(f"Invalid: {file}", err=True)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information.")
def info(file: Path, *, verbose: bool) -> None:
    """Show information and statistics about a GPX file.

    Displays metadata, waypoints, routes, and tracks with their statistics.

    FILE: Path to the GPX file to analyze.
    """
    gpx = _read_file(file)

    click.echo(f"File: {file}")
    click.echo(f"Creator: {gpx.creator}")

    # Metadata
    if gpx.metadata:
        click.echo("\nMetadata:")
        if gpx.metadata.name:
            click.echo(f"  Name: {gpx.metadata.name}")
        if gpx.metadata.desc:
            click.echo(f"  Description: {gpx.metadata.desc}")
        if gpx.metadata.author:
            if gpx.metadata.author.name:
                click.echo(f"  Author: {gpx.metadata.author.name}")
        if gpx.metadata.time:
            click.echo(f"  Time: {gpx.metadata.time.isoformat()}")
        if gpx.metadata.keywords:
            click.echo(f"  Keywords: {gpx.metadata.keywords}")

    # Summary
    click.echo("\nSummary:")
    click.echo(f"  Waypoints: {len(gpx.wpt)}")
    click.echo(f"  Routes: {len(gpx.rte)}")
    click.echo(f"  Tracks: {len(gpx.trk)}")

    # Waypoints
    if gpx.wpt and verbose:
        click.echo("\nWaypoints:")
        for i, wpt in enumerate(gpx.wpt, 1):
            name = wpt.name or f"Waypoint {i}"
            click.echo(f"  {i}. {name} ({wpt.lat}, {wpt.lon})")
            if wpt.ele is not None:
                click.echo(f"     Elevation: {wpt.ele} m")

    # Routes
    if gpx.rte:
        click.echo("\nRoutes:")
        for i, rte in enumerate(gpx.rte, 1):
            name = rte.name or f"Route {i}"
            click.echo(f"  {i}. {name}")
            click.echo(f"     Points: {len(rte.rtept)}")
            if rte.rtept:
                distance = rte.total_distance
                click.echo(f"     Distance: {_format_distance(distance)}")
                if verbose:
                    bounds = rte.bounds
                    click.echo(
                        f"     Bounds: ({bounds[0]}, {bounds[1]}) to "
                        f"({bounds[2]}, {bounds[3]})"
                    )

    # Tracks
    if gpx.trk:
        click.echo("\nTracks:")
        for i, trk in enumerate(gpx.trk, 1):
            name = trk.name or f"Track {i}"
            click.echo(f"  {i}. {name}")
            click.echo(f"     Segments: {len(trk.trkseg)}")
            total_points = sum(len(seg.trkpt) for seg in trk.trkseg)
            click.echo(f"     Points: {total_points}")

            if trk.trkseg and any(seg.trkpt for seg in trk.trkseg):
                # Distance and duration
                distance = trk.total_distance
                click.echo(f"     Distance: {_format_distance(distance)}")

                duration = trk.total_duration
                if duration.total_seconds() > 0:
                    click.echo(f"     Duration: {_format_duration(duration.total_seconds())}")
                    click.echo(f"     Avg Speed: {trk.avg_speed * 3.6:.1f} km/h")

                # Elevation
                try:
                    click.echo(f"     Min Elevation: {trk.min_elevation} m")
                    click.echo(f"     Max Elevation: {trk.max_elevation} m")
                    click.echo(f"     Total Ascent: {trk.total_ascent} m")
                    click.echo(f"     Total Descent: {trk.total_descent} m")
                except (ValueError, ZeroDivisionError):
                    pass

                if verbose:
                    bounds = trk.bounds
                    click.echo(
                        f"     Bounds: ({bounds[0]}, {bounds[1]}) to "
                        f"({bounds[2]}, {bounds[3]})"
                    )


@main.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
@click.option("--min-lat", type=float, required=True, help="Minimum latitude.")
@click.option("--min-lon", type=float, required=True, help="Minimum longitude.")
@click.option("--max-lat", type=float, required=True, help="Maximum latitude.")
@click.option("--max-lon", type=float, required=True, help="Maximum longitude.")
def crop(
    file: Path,
    output: Path,
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
) -> None:
    """Crop a GPX file to a geographic bounding box.

    Filters waypoints, routes, and tracks to only include points within
    the specified bounding box.

    FILE: Path to the input GPX file.
    OUTPUT: Path to the output file.
    """
    gpx = _read_file(file)

    def in_bounds(lat: Decimal, lon: Decimal) -> bool:
        return (
            min_lat <= float(lat) <= max_lat and min_lon <= float(lon) <= max_lon
        )

    # Filter waypoints
    filtered_wpt = [wpt for wpt in gpx.wpt if in_bounds(wpt.lat, wpt.lon)]

    # Filter routes
    filtered_rte = []
    for rte in gpx.rte:
        filtered_points = [pt for pt in rte.rtept if in_bounds(pt.lat, pt.lon)]
        if filtered_points:
            filtered_rte.append(replace(rte, rtept=filtered_points))

    # Filter tracks
    filtered_trk = []
    for trk in gpx.trk:
        filtered_segs = []
        for seg in trk.trkseg:
            filtered_points = [pt for pt in seg.trkpt if in_bounds(pt.lat, pt.lon)]
            if filtered_points:
                filtered_segs.append(TrackSegment(trkpt=filtered_points))
        if filtered_segs:
            filtered_trk.append(replace(trk, trkseg=filtered_segs))

    new_gpx = GPX(
        creator=gpx.creator,
        metadata=gpx.metadata,
        wpt=filtered_wpt,
        rte=filtered_rte,
        trk=filtered_trk,
    )

    _write_file(new_gpx, output)
    click.echo(f"Cropped GPX written to {output}")
    click.echo(f"  Waypoints: {len(gpx.wpt)} -> {len(filtered_wpt)}")
    click.echo(f"  Routes: {len(gpx.rte)} -> {len(filtered_rte)}")
    click.echo(f"  Tracks: {len(gpx.trk)} -> {len(filtered_trk)}")


@main.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
@click.option(
    "--start",
    type=click.DateTime(),
    help="Start time (ISO format, e.g. 2024-01-15T08:00:00).",
)
@click.option(
    "--end",
    type=click.DateTime(),
    help="End time (ISO format, e.g. 2024-01-15T18:00:00).",
)
def trim(
    file: Path,
    output: Path,
    start: datetime | None,
    end: datetime | None,
) -> None:
    """Trim a GPX file to a date/time range.

    Filters waypoints, routes, and tracks to only include points within
    the specified time range. Points without timestamps are excluded.

    FILE: Path to the input GPX file.
    OUTPUT: Path to the output file.
    """
    if start is None and end is None:
        msg = "At least one of --start or --end must be specified"
        raise click.ClickException(msg)

    gpx = _read_file(file)

    # Make start/end timezone-aware (assume UTC if naive) for comparison
    from datetime import timezone

    start_aware = start.replace(tzinfo=timezone.utc) if start and start.tzinfo is None else start
    end_aware = end.replace(tzinfo=timezone.utc) if end and end.tzinfo is None else end

    def in_time_range(time: datetime | None) -> bool:
        if time is None:
            return False
        # Handle comparison between timezone-aware and naive datetimes
        if time.tzinfo is None:
            time = time.replace(tzinfo=timezone.utc)
        if start_aware is not None and time < start_aware:
            return False
        if end_aware is not None and time > end_aware:
            return False
        return True

    # Filter waypoints
    filtered_wpt = [wpt for wpt in gpx.wpt if in_time_range(wpt.time)]

    # Filter routes
    filtered_rte = []
    for rte in gpx.rte:
        filtered_points = [pt for pt in rte.rtept if in_time_range(pt.time)]
        if filtered_points:
            filtered_rte.append(replace(rte, rtept=filtered_points))

    # Filter tracks
    filtered_trk = []
    for trk in gpx.trk:
        filtered_segs = []
        for seg in trk.trkseg:
            filtered_points = [pt for pt in seg.trkpt if in_time_range(pt.time)]
            if filtered_points:
                filtered_segs.append(TrackSegment(trkpt=filtered_points))
        if filtered_segs:
            filtered_trk.append(replace(trk, trkseg=filtered_segs))

    new_gpx = GPX(
        creator=gpx.creator,
        metadata=gpx.metadata,
        wpt=filtered_wpt,
        rte=filtered_rte,
        trk=filtered_trk,
    )

    _write_file(new_gpx, output)
    click.echo(f"Trimmed GPX written to {output}")
    click.echo(f"  Waypoints: {len(gpx.wpt)} -> {len(filtered_wpt)}")
    click.echo(f"  Routes: {len(gpx.rte)} -> {len(filtered_rte)}")
    click.echo(f"  Tracks: {len(gpx.trk)} -> {len(filtered_trk)}")


@main.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
def merge(files: tuple[Path, ...], output: Path) -> None:
    """Merge multiple GPX files into one.

    Combines waypoints, routes, and tracks from all input files.

    FILES: Paths to the input GPX files (at least 2).
    OUTPUT: Path to the output file.
    """
    if len(files) < 2:  # noqa: PLR2004
        msg = "At least 2 files are required for merging"
        raise click.ClickException(msg)

    all_wpt: list[Waypoint] = []
    all_rte: list[Route] = []
    all_trk: list[Track] = []
    creator = None

    for file_path in files:
        gpx = _read_file(file_path)
        if creator is None:
            creator = gpx.creator
        all_wpt.extend(gpx.wpt)
        all_rte.extend(gpx.rte)
        all_trk.extend(gpx.trk)

    new_gpx = GPX(
        creator=creator or "gpx",
        wpt=all_wpt,
        rte=all_rte,
        trk=all_trk,
    )

    _write_file(new_gpx, output)
    click.echo(f"Merged {len(files)} files into {output}")
    click.echo(f"  Waypoints: {len(all_wpt)}")
    click.echo(f"  Routes: {len(all_rte)}")
    click.echo(f"  Tracks: {len(all_trk)}")


@main.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
@click.option(
    "--routes/--no-routes",
    default=True,
    help="Reverse routes (default: yes).",
)
@click.option(
    "--tracks/--no-tracks",
    default=True,
    help="Reverse tracks (default: yes).",
)
def reverse(file: Path, output: Path, *, routes: bool, tracks: bool) -> None:
    """Reverse the direction of routes and/or tracks.

    Reverses the order of points in routes and track segments.
    Waypoints are not affected.

    FILE: Path to the input GPX file.
    OUTPUT: Path to the output file.
    """
    gpx = _read_file(file)

    # Reverse routes
    if routes:
        reversed_rte = [replace(rte, rtept=list(reversed(rte.rtept))) for rte in gpx.rte]
    else:
        reversed_rte = gpx.rte

    # Reverse tracks
    if tracks:
        reversed_trk = []
        for trk in gpx.trk:
            reversed_segs = [
                TrackSegment(trkpt=list(reversed(seg.trkpt)))
                for seg in reversed(trk.trkseg)
            ]
            reversed_trk.append(replace(trk, trkseg=reversed_segs))
    else:
        reversed_trk = gpx.trk

    new_gpx = GPX(
        creator=gpx.creator,
        metadata=gpx.metadata,
        wpt=gpx.wpt,
        rte=reversed_rte,
        trk=reversed_trk,
    )

    _write_file(new_gpx, output)
    click.echo(f"Reversed GPX written to {output}")
    if routes:
        click.echo(f"  Reversed {len(gpx.rte)} route(s)")
    if tracks:
        click.echo(f"  Reversed {len(gpx.trk)} track(s)")


@main.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.argument("output_file", type=click.Path(path_type=Path))
@click.option(
    "--input-format",
    "-i",
    type=click.Choice(["gpx", "geojson", "kml"]),
    help="Input format (auto-detected from extension if not specified).",
)
@click.option(
    "--output-format",
    "-o",
    type=click.Choice(["gpx", "geojson", "kml"]),
    help="Output format (auto-detected from extension if not specified).",
)
def convert(
    input_file: Path,
    output_file: Path,
    input_format: str | None,
    output_format: str | None,
) -> None:
    """Convert between GPX, GeoJSON, and KML formats.

    INPUT_FILE: Path to the input file.
    OUTPUT_FILE: Path to the output file.
    """
    gpx = _read_file(input_file, input_format)
    _write_file(gpx, output_file, output_format)
    click.echo(f"Converted {input_file} to {output_file}")


@main.command("strip-metadata")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
@click.option("--name/--keep-name", default=True, help="Strip name (default: yes).")
@click.option("--desc/--keep-desc", default=True, help="Strip description (default: yes).")
@click.option("--author/--keep-author", default=True, help="Strip author (default: yes).")
@click.option(
    "--copyright/--keep-copyright",
    "strip_copyright",
    default=True,
    help="Strip copyright (default: yes).",
)
@click.option("--time/--keep-time", default=False, help="Strip time (default: no).")
@click.option("--keywords/--keep-keywords", default=False, help="Strip keywords (default: no).")
@click.option("--links/--keep-links", default=False, help="Strip links (default: no).")
@click.option("--all", "strip_all", is_flag=True, help="Strip all metadata fields.")
def strip_metadata(
    file: Path,
    output: Path,
    *,
    name: bool,
    desc: bool,
    author: bool,
    strip_copyright: bool,
    time: bool,
    keywords: bool,
    links: bool,
    strip_all: bool,
) -> None:
    """Remove metadata from a GPX file.

    Strips name, description, author, and copyright from the metadata.
    Optionally also strips time, keywords, and links.

    FILE: Path to the input GPX file.
    OUTPUT: Path to the output file.
    """
    gpx = _read_file(file)

    if strip_all:
        name = desc = author = strip_copyright = time = keywords = links = True

    if gpx.metadata:
        metadata_kwargs: dict[str, Any] = {}

        if not name and gpx.metadata.name:
            metadata_kwargs["name"] = gpx.metadata.name
        if not desc and gpx.metadata.desc:
            metadata_kwargs["desc"] = gpx.metadata.desc
        if not author and gpx.metadata.author:
            metadata_kwargs["author"] = gpx.metadata.author
        if not strip_copyright and gpx.metadata.copyright:
            metadata_kwargs["copyright"] = gpx.metadata.copyright
        if not time and gpx.metadata.time:
            metadata_kwargs["time"] = gpx.metadata.time
        if not keywords and gpx.metadata.keywords:
            metadata_kwargs["keywords"] = gpx.metadata.keywords
        if not links and gpx.metadata.link:
            metadata_kwargs["link"] = gpx.metadata.link
        if gpx.metadata.bounds:
            metadata_kwargs["bounds"] = gpx.metadata.bounds

        new_metadata = Metadata(**metadata_kwargs) if metadata_kwargs else None
    else:
        new_metadata = None

    new_gpx = GPX(
        creator=gpx.creator,
        metadata=new_metadata,
        wpt=gpx.wpt,
        rte=gpx.rte,
        trk=gpx.trk,
    )

    _write_file(new_gpx, output)
    click.echo(f"Stripped metadata written to {output}")


@main.command("reduce-precision")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
@click.option(
    "--precision",
    "-p",
    type=int,
    default=3,
    help="Number of decimal places for coordinates (default: 3, ~111m accuracy).",
)
@click.option(
    "--elevation-precision",
    "-e",
    type=int,
    default=0,
    help="Number of decimal places for elevation (default: 0).",
)
def reduce_precision(
    file: Path,
    output: Path,
    precision: int,
    elevation_precision: int,
) -> None:
    """Reduce the precision of coordinates to obscure exact locations.

    Rounds latitude and longitude to the specified number of decimal places.
    This can be used to protect privacy by obscuring exact locations.

    Precision reference:
    - 1 decimal place: ~11 km
    - 2 decimal places: ~1.1 km
    - 3 decimal places: ~111 m
    - 4 decimal places: ~11 m
    - 5 decimal places: ~1.1 m

    FILE: Path to the input GPX file.
    OUTPUT: Path to the output file.
    """
    gpx = _read_file(file)

    def round_coordinate(value: Decimal, places: int) -> Decimal:
        quantize_str = "1." + "0" * places if places > 0 else "1"
        return value.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)

    def round_waypoint(wpt: Waypoint) -> Waypoint:
        new_lat = round_coordinate(wpt.lat, precision)
        new_lon = round_coordinate(wpt.lon, precision)
        new_ele = (
            round_coordinate(wpt.ele, elevation_precision)
            if wpt.ele is not None
            else None
        )
        return replace(wpt, lat=Latitude(new_lat), lon=Longitude(new_lon), ele=new_ele)

    # Round waypoints
    rounded_wpt = [round_waypoint(wpt) for wpt in gpx.wpt]

    # Round routes
    rounded_rte = [
        replace(rte, rtept=[round_waypoint(pt) for pt in rte.rtept])
        for rte in gpx.rte
    ]

    # Round tracks
    rounded_trk = []
    for trk in gpx.trk:
        rounded_segs = [
            TrackSegment(trkpt=[round_waypoint(pt) for pt in seg.trkpt])
            for seg in trk.trkseg
        ]
        rounded_trk.append(replace(trk, trkseg=rounded_segs))

    new_gpx = GPX(
        creator=gpx.creator,
        metadata=gpx.metadata,
        wpt=rounded_wpt,
        rte=rounded_rte,
        trk=rounded_trk,
    )

    _write_file(new_gpx, output)
    click.echo(f"Reduced precision GPX written to {output}")
    click.echo(f"  Coordinate precision: {precision} decimal places")
    click.echo(f"  Elevation precision: {elevation_precision} decimal places")


if __name__ == "__main__":
    main()
