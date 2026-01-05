"""Command-line interface for the gpx package.

This module provides a CLI for common GPX operations including validation,
information display, editing, merging, and format conversion.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

from .gpx import GPX
from .io import read_geojson, read_gpx, read_kml
from .metadata import Metadata
from .route import Route
from .track import Track
from .track_segment import TrackSegment
from .types import Latitude, Longitude
from .waypoint import Waypoint

if TYPE_CHECKING:
    from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the gpx CLI.

    Args:
        argv: Command-line arguments. Defaults to sys.argv[1:].

    Returns:
        Exit code (0 for success, non-zero for failure).

    """
    parser = _create_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 0

    try:
        return args.func(args)
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="gpx",
        description="A command-line tool for working with GPX files.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="gpx 2025.1.0",
    )

    subparsers = parser.add_subparsers(
        title="commands",
        description="Available commands",
        dest="command",
    )

    # Validate command
    _add_validate_parser(subparsers)

    # Info command
    _add_info_parser(subparsers)

    # Edit command
    _add_edit_parser(subparsers)

    # Merge command
    _add_merge_parser(subparsers)

    # Convert command
    _add_convert_parser(subparsers)

    return parser


# =============================================================================
# Validate command
# =============================================================================


def _add_validate_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the validate subcommand parser."""
    parser = subparsers.add_parser(
        "validate",
        help="Validate a GPX file",
        description="Validate a GPX file by attempting to parse it.",
    )
    parser.add_argument(
        "file",
        type=Path,
        help="Path to the GPX file to validate",
    )
    parser.set_defaults(func=_cmd_validate)


def _cmd_validate(args: argparse.Namespace) -> int:
    """Execute the validate command."""
    file_path: Path = args.file

    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    try:
        gpx = read_gpx(file_path)
    except Exception as e:  # noqa: BLE001
        print(f"✗ Invalid GPX file: {file_path}", file=sys.stderr)
        print(f"  Error: {e}", file=sys.stderr)
        return 1

    print(f"✓ Valid GPX file: {file_path}")
    print(f"  Creator: {gpx.creator}")
    print(f"  Waypoints: {len(gpx.wpt)}")
    print(f"  Routes: {len(gpx.rte)}")
    print(f"  Tracks: {len(gpx.trk)}")
    return 0


# =============================================================================
# Info command
# =============================================================================


def _add_info_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the info subcommand parser."""
    parser = subparsers.add_parser(
        "info",
        help="Show information and statistics about a GPX file",
        description="Display detailed information and statistics about a GPX file.",
    )
    parser.add_argument(
        "file",
        type=Path,
        help="Path to the GPX file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output information in JSON format",
    )
    parser.set_defaults(func=_cmd_info)


def _cmd_info(args: argparse.Namespace) -> int:
    """Execute the info command."""
    file_path: Path = args.file

    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    gpx = read_gpx(file_path)

    info = _gather_gpx_info(gpx)

    if args.json:
        print(json.dumps(info, indent=2, default=str))
    else:
        _print_gpx_info(file_path, info)

    return 0


def _gather_gpx_info(gpx: GPX) -> dict:  # noqa: C901
    """Gather information about a GPX object."""
    info: dict = {
        "creator": gpx.creator,
        "waypoints": len(gpx.wpt),
        "routes": len(gpx.rte),
        "tracks": len(gpx.trk),
    }

    # Metadata
    if gpx.metadata:
        info["metadata"] = {}
        if gpx.metadata.name:
            info["metadata"]["name"] = gpx.metadata.name
        if gpx.metadata.desc:
            info["metadata"]["description"] = gpx.metadata.desc
        if gpx.metadata.author:
            info["metadata"]["author"] = gpx.metadata.author.name
        if gpx.metadata.time:
            info["metadata"]["time"] = gpx.metadata.time.isoformat()
        if gpx.metadata.keywords:
            info["metadata"]["keywords"] = gpx.metadata.keywords

    # Track statistics
    if gpx.trk:
        track_stats = []
        for i, track in enumerate(gpx.trk):
            track_info = _gather_track_info(track, i)
            track_stats.append(track_info)
        info["track_statistics"] = track_stats

        # Overall statistics
        info["total_distance_m"] = sum(t.total_distance for t in gpx.trk)
        info["total_duration_s"] = sum(
            t.total_duration.total_seconds() for t in gpx.trk
        )

    # Route statistics
    if gpx.rte:
        route_stats = []
        for i, route in enumerate(gpx.rte):
            route_info = _gather_route_info(route, i)
            route_stats.append(route_info)
        info["route_statistics"] = route_stats

    # Bounds
    if gpx.trk or gpx.rte or gpx.wpt:
        info["bounds"] = _calculate_bounds(gpx)

    return info


def _gather_track_info(track: Track, index: int) -> dict:
    """Gather information about a track."""
    track_info: dict = {
        "index": index,
        "name": track.name,
        "segments": len(track.trkseg),
        "points": sum(len(seg.trkpt) for seg in track.trkseg),
        "distance_m": track.total_distance,
        "duration_s": track.total_duration.total_seconds(),
    }

    # Speed stats
    if track.total_duration.total_seconds() > 0:
        track_info["avg_speed_ms"] = track.avg_speed
        track_info["avg_speed_kmh"] = track.avg_speed * 3.6

    # Elevation stats
    with contextlib.suppress(ValueError, ZeroDivisionError):
        track_info["elevation"] = {
            "min_m": float(track.min_elevation),
            "max_m": float(track.max_elevation),
            "avg_m": float(track.avg_elevation),
            "total_ascent_m": float(track.total_ascent),
            "total_descent_m": float(track.total_descent),
        }

    return track_info


def _gather_route_info(route: Route, index: int) -> dict:
    """Gather information about a route."""
    route_info: dict = {
        "index": index,
        "name": route.name,
        "points": len(route.rtept),
        "distance_m": route.total_distance,
    }

    # Elevation stats
    with contextlib.suppress(ValueError, ZeroDivisionError):
        route_info["elevation"] = {
            "min_m": float(route.min_elevation),
            "max_m": float(route.max_elevation),
            "total_ascent_m": float(route.total_ascent),
            "total_descent_m": float(route.total_descent),
        }

    return route_info


def _calculate_bounds(gpx: GPX) -> dict:
    """Calculate the geographic bounds of the GPX data."""
    all_points: list[Waypoint] = list(gpx.wpt)

    for route in gpx.rte:
        all_points.extend(route.rtept)

    for track in gpx.trk:
        for segment in track.trkseg:
            all_points.extend(segment.trkpt)

    if not all_points:
        return {}

    min_lat = min(float(p.lat) for p in all_points)
    max_lat = max(float(p.lat) for p in all_points)
    min_lon = min(float(p.lon) for p in all_points)
    max_lon = max(float(p.lon) for p in all_points)

    return {
        "min_lat": min_lat,
        "max_lat": max_lat,
        "min_lon": min_lon,
        "max_lon": max_lon,
    }


def _print_gpx_info(  # noqa: C901, PLR0912, PLR0915
    file_path: Path, info: dict
) -> None:
    """Print GPX information in a human-readable format."""
    print(f"GPX File: {file_path}")
    print(f"Creator: {info['creator']}")
    print()

    # Metadata
    if "metadata" in info:
        print("Metadata:")
        meta = info["metadata"]
        if "name" in meta:
            print(f"  Name: {meta['name']}")
        if "description" in meta:
            print(f"  Description: {meta['description']}")
        if "author" in meta:
            print(f"  Author: {meta['author']}")
        if "time" in meta:
            print(f"  Time: {meta['time']}")
        if "keywords" in meta:
            print(f"  Keywords: {meta['keywords']}")
        print()

    # Summary
    print("Contents:")
    print(f"  Waypoints: {info['waypoints']}")
    print(f"  Routes: {info['routes']}")
    print(f"  Tracks: {info['tracks']}")
    print()

    # Track statistics
    if "track_statistics" in info:
        print("Track Statistics:")
        for track in info["track_statistics"]:
            name = track["name"] or f"Track {track['index'] + 1}"
            print(f"  {name}:")
            print(f"    Segments: {track['segments']}")
            print(f"    Points: {track['points']}")
            distance_km = track["distance_m"] / 1000
            print(f"    Distance: {track['distance_m']:.2f} m ({distance_km:.2f} km)")
            if track["duration_s"] > 0:
                hours = int(track["duration_s"] // 3600)
                minutes = int((track["duration_s"] % 3600) // 60)
                seconds = int(track["duration_s"] % 60)
                print(f"    Duration: {hours:02d}:{minutes:02d}:{seconds:02d}")
            if "avg_speed_kmh" in track:
                print(f"    Avg Speed: {track['avg_speed_kmh']:.2f} km/h")
            if "elevation" in track:
                ele = track["elevation"]
                avg_ele = ele["avg_m"]
                print(
                    f"    Elevation: {ele['min_m']:.1f}m - {ele['max_m']:.1f}m (avg: {avg_ele:.1f}m)"
                )
                print(
                    f"    Ascent/Descent: +{ele['total_ascent_m']:.1f}m / -{ele['total_descent_m']:.1f}m"
                )
        print()

    # Route statistics
    if "route_statistics" in info:
        print("Route Statistics:")
        for route in info["route_statistics"]:
            name = route["name"] or f"Route {route['index'] + 1}"
            print(f"  {name}:")
            print(f"    Points: {route['points']}")
            distance_km = route["distance_m"] / 1000
            print(f"    Distance: {route['distance_m']:.2f} m ({distance_km:.2f} km)")
            if "elevation" in route:
                ele = route["elevation"]
                print(f"    Elevation: {ele['min_m']:.1f}m - {ele['max_m']:.1f}m")
                print(
                    f"    Ascent/Descent: +{ele['total_ascent_m']:.1f}m / -{ele['total_descent_m']:.1f}m"
                )
        print()

    # Bounds
    if info.get("bounds"):
        bounds = info["bounds"]
        print("Bounds:")
        print(f"  Latitude: {bounds['min_lat']:.6f} to {bounds['max_lat']:.6f}")
        print(f"  Longitude: {bounds['min_lon']:.6f} to {bounds['max_lon']:.6f}")

    # Overall statistics
    if "total_distance_m" in info:
        print()
        print("Overall:")
        total_km = info["total_distance_m"] / 1000
        print(f"  Total Distance: {info['total_distance_m']:.2f} m ({total_km:.2f} km)")
        if info["total_duration_s"] > 0:
            hours = int(info["total_duration_s"] // 3600)
            minutes = int((info["total_duration_s"] % 3600) // 60)
            seconds = int(info["total_duration_s"] % 60)
            print(f"  Total Duration: {hours:02d}:{minutes:02d}:{seconds:02d}")


# =============================================================================
# Edit command
# =============================================================================


def _add_edit_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the edit subcommand parser."""
    parser = subparsers.add_parser(
        "edit",
        help="Edit a GPX file with various transformations",
        description="Edit a GPX file with various transformations like cropping, "
        "trimming, reversing, and stripping metadata.",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to the input GPX file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to the output file (default: overwrite input)",
    )

    # Crop options
    crop_group = parser.add_argument_group(
        "crop options", "Crop to a geographic bounding box"
    )
    crop_group.add_argument(
        "--min-lat",
        type=float,
        metavar="LAT",
        help="Minimum latitude for crop",
    )
    crop_group.add_argument(
        "--max-lat",
        type=float,
        metavar="LAT",
        help="Maximum latitude for crop",
    )
    crop_group.add_argument(
        "--min-lon",
        type=float,
        metavar="LON",
        help="Minimum longitude for crop",
    )
    crop_group.add_argument(
        "--max-lon",
        type=float,
        metavar="LON",
        help="Maximum longitude for crop",
    )

    # Trim options
    trim_group = parser.add_argument_group("trim options", "Trim to a date/time range")
    trim_group.add_argument(
        "--start",
        type=str,
        metavar="DATETIME",
        help="Start datetime (ISO 8601 format, e.g., 2024-01-01T10:00:00)",
    )
    trim_group.add_argument(
        "--end",
        type=str,
        metavar="DATETIME",
        help="End datetime (ISO 8601 format, e.g., 2024-01-01T12:00:00)",
    )

    # Reverse options
    reverse_group = parser.add_argument_group(
        "reverse options", "Reverse routes and/or tracks"
    )
    reverse_group.add_argument(
        "--reverse",
        action="store_true",
        help="Reverse all routes and tracks",
    )
    reverse_group.add_argument(
        "--reverse-routes",
        action="store_true",
        help="Reverse only routes",
    )
    reverse_group.add_argument(
        "--reverse-tracks",
        action="store_true",
        help="Reverse only tracks",
    )

    # Strip metadata options
    strip_group = parser.add_argument_group("strip options", "Strip metadata fields")
    strip_group.add_argument(
        "--strip-name",
        action="store_true",
        help="Strip metadata name",
    )
    strip_group.add_argument(
        "--strip-desc",
        action="store_true",
        help="Strip metadata description",
    )
    strip_group.add_argument(
        "--strip-author",
        action="store_true",
        help="Strip metadata author",
    )
    strip_group.add_argument(
        "--strip-copyright",
        action="store_true",
        help="Strip metadata copyright",
    )
    strip_group.add_argument(
        "--strip-time",
        action="store_true",
        help="Strip metadata time",
    )
    strip_group.add_argument(
        "--strip-keywords",
        action="store_true",
        help="Strip metadata keywords",
    )
    strip_group.add_argument(
        "--strip-links",
        action="store_true",
        help="Strip metadata links",
    )
    strip_group.add_argument(
        "--strip-all-metadata",
        action="store_true",
        help="Strip all metadata",
    )

    # Precision options
    precision_group = parser.add_argument_group(
        "precision options", "Reduce coordinate precision"
    )
    precision_group.add_argument(
        "--precision",
        type=int,
        metavar="DIGITS",
        help="Number of decimal places for lat/lon coordinates (e.g., 6)",
    )
    precision_group.add_argument(
        "--elevation-precision",
        type=int,
        metavar="DIGITS",
        help="Number of decimal places for elevation (e.g., 1)",
    )

    parser.set_defaults(func=_cmd_edit)


def _cmd_edit(args: argparse.Namespace) -> int:
    """Execute the edit command."""
    input_path: Path = args.input
    output_path: Path = args.output if args.output else input_path

    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return 1

    gpx = read_gpx(input_path)

    # Apply crop
    if any([args.min_lat, args.max_lat, args.min_lon, args.max_lon]):
        gpx = _apply_crop(gpx, args.min_lat, args.max_lat, args.min_lon, args.max_lon)

    # Apply trim
    if args.start or args.end:
        start_dt = _parse_datetime(args.start) if args.start else None
        end_dt = _parse_datetime(args.end) if args.end else None
        gpx = _apply_trim(gpx, start_dt, end_dt)

    # Apply reverse
    if args.reverse:
        gpx = _apply_reverse(gpx, reverse_routes=True, reverse_tracks=True)
    else:
        if args.reverse_routes:
            gpx = _apply_reverse(gpx, reverse_routes=True, reverse_tracks=False)
        if args.reverse_tracks:
            gpx = _apply_reverse(gpx, reverse_routes=False, reverse_tracks=True)

    # Apply strip metadata
    if args.strip_all_metadata:
        gpx = GPX(
            creator=gpx.creator,
            wpt=gpx.wpt,
            rte=gpx.rte,
            trk=gpx.trk,
        )
    elif gpx.metadata:
        gpx = _apply_strip_metadata(gpx, args)

    # Apply precision reduction
    if args.precision is not None or args.elevation_precision is not None:
        gpx = _apply_precision(gpx, args.precision, args.elevation_precision)

    # Write output
    gpx.write_gpx(output_path)
    print(f"Written to: {output_path}")
    return 0


def _apply_strip_metadata(gpx: GPX, args: argparse.Namespace) -> GPX:
    """Apply metadata stripping based on args."""
    metadata = gpx.metadata
    if not metadata:
        return gpx

    if args.strip_name:
        metadata = Metadata(
            desc=metadata.desc,
            author=metadata.author,
            copyright=metadata.copyright,
            link=metadata.link,
            time=metadata.time,
            keywords=metadata.keywords,
            bounds=metadata.bounds,
        )
    if args.strip_desc:
        metadata = Metadata(
            name=metadata.name,
            author=metadata.author,
            copyright=metadata.copyright,
            link=metadata.link,
            time=metadata.time,
            keywords=metadata.keywords,
            bounds=metadata.bounds,
        )
    if args.strip_author:
        metadata = Metadata(
            name=metadata.name,
            desc=metadata.desc,
            copyright=metadata.copyright,
            link=metadata.link,
            time=metadata.time,
            keywords=metadata.keywords,
            bounds=metadata.bounds,
        )
    if args.strip_copyright:
        metadata = Metadata(
            name=metadata.name,
            desc=metadata.desc,
            author=metadata.author,
            link=metadata.link,
            time=metadata.time,
            keywords=metadata.keywords,
            bounds=metadata.bounds,
        )
    if args.strip_time:
        metadata = Metadata(
            name=metadata.name,
            desc=metadata.desc,
            author=metadata.author,
            copyright=metadata.copyright,
            link=metadata.link,
            keywords=metadata.keywords,
            bounds=metadata.bounds,
        )
    if args.strip_keywords:
        metadata = Metadata(
            name=metadata.name,
            desc=metadata.desc,
            author=metadata.author,
            copyright=metadata.copyright,
            link=metadata.link,
            time=metadata.time,
            bounds=metadata.bounds,
        )
    if args.strip_links:
        metadata = Metadata(
            name=metadata.name,
            desc=metadata.desc,
            author=metadata.author,
            copyright=metadata.copyright,
            time=metadata.time,
            keywords=metadata.keywords,
            bounds=metadata.bounds,
        )
    return GPX(
        creator=gpx.creator,
        metadata=metadata,
        wpt=gpx.wpt,
        rte=gpx.rte,
        trk=gpx.trk,
    )


def _parse_datetime(dt_str: str) -> datetime:
    """Parse an ISO 8601 datetime string."""
    # Try various ISO 8601 formats
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(dt_str, fmt)  # noqa: DTZ007
            # Add UTC timezone if none specified
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
        except ValueError:
            continue
        else:
            return dt

    msg = (
        f"Invalid datetime format: {dt_str}. "
        "Use ISO 8601 format (e.g., 2024-01-01T10:00:00)"
    )
    raise ValueError(msg)


def _apply_crop(  # noqa: C901
    gpx: GPX,
    min_lat: float | None,
    max_lat: float | None,
    min_lon: float | None,
    max_lon: float | None,
) -> GPX:
    """Apply geographic crop to GPX data."""

    def is_in_bounds(point: Waypoint) -> bool:
        lat, lon = float(point.lat), float(point.lon)
        if min_lat is not None and lat < min_lat:
            return False
        if max_lat is not None and lat > max_lat:
            return False
        if min_lon is not None and lon < min_lon:
            return False
        return not (max_lon is not None and lon > max_lon)

    # Filter waypoints
    new_wpt = [w for w in gpx.wpt if is_in_bounds(w)]

    # Filter routes
    new_rte = []
    for route in gpx.rte:
        new_rtept = [p for p in route.rtept if is_in_bounds(p)]
        if new_rtept:
            new_rte.append(
                Route(
                    name=route.name,
                    cmt=route.cmt,
                    desc=route.desc,
                    src=route.src,
                    link=route.link,
                    number=route.number,
                    type=route.type,
                    rtept=new_rtept,
                )
            )

    # Filter tracks
    new_trk = []
    for track in gpx.trk:
        new_trkseg = []
        for segment in track.trkseg:
            new_trkpt = [p for p in segment.trkpt if is_in_bounds(p)]
            if new_trkpt:
                new_trkseg.append(TrackSegment(trkpt=new_trkpt))
        if new_trkseg:
            new_trk.append(
                Track(
                    name=track.name,
                    cmt=track.cmt,
                    desc=track.desc,
                    src=track.src,
                    link=track.link,
                    number=track.number,
                    type=track.type,
                    trkseg=new_trkseg,
                )
            )

    return GPX(
        creator=gpx.creator,
        metadata=gpx.metadata,
        wpt=new_wpt,
        rte=new_rte,
        trk=new_trk,
    )


def _apply_trim(
    gpx: GPX,
    start_dt: datetime | None,
    end_dt: datetime | None,
) -> GPX:
    """Apply time-based trim to GPX data."""

    def is_in_time_range(point: Waypoint) -> bool:
        if point.time is None:
            return True  # Keep points without timestamps
        if start_dt is not None and point.time < start_dt:
            return False
        return not (end_dt is not None and point.time > end_dt)

    # Filter waypoints
    new_wpt = [w for w in gpx.wpt if is_in_time_range(w)]

    # Filter routes (routes usually don't have timestamps, but check anyway)
    new_rte = []
    for route in gpx.rte:
        new_rtept = [p for p in route.rtept if is_in_time_range(p)]
        if new_rtept:
            new_rte.append(
                Route(
                    name=route.name,
                    cmt=route.cmt,
                    desc=route.desc,
                    src=route.src,
                    link=route.link,
                    number=route.number,
                    type=route.type,
                    rtept=new_rtept,
                )
            )

    # Filter tracks
    new_trk = []
    for track in gpx.trk:
        new_trkseg = []
        for segment in track.trkseg:
            new_trkpt = [p for p in segment.trkpt if is_in_time_range(p)]
            if new_trkpt:
                new_trkseg.append(TrackSegment(trkpt=new_trkpt))
        if new_trkseg:
            new_trk.append(
                Track(
                    name=track.name,
                    cmt=track.cmt,
                    desc=track.desc,
                    src=track.src,
                    link=track.link,
                    number=track.number,
                    type=track.type,
                    trkseg=new_trkseg,
                )
            )

    return GPX(
        creator=gpx.creator,
        metadata=gpx.metadata,
        wpt=new_wpt,
        rte=new_rte,
        trk=new_trk,
    )


def _apply_reverse(
    gpx: GPX,
    *,
    reverse_routes: bool,
    reverse_tracks: bool,
) -> GPX:
    """Apply reversal to routes and/or tracks."""
    new_rte = gpx.rte
    new_trk = gpx.trk

    if reverse_routes:
        new_rte = [
            Route(
                name=route.name,
                cmt=route.cmt,
                desc=route.desc,
                src=route.src,
                link=route.link,
                number=route.number,
                type=route.type,
                rtept=list(reversed(route.rtept)),
            )
            for route in gpx.rte
        ]

    if reverse_tracks:
        new_trk = []
        for track in gpx.trk:
            new_trkseg = [
                TrackSegment(trkpt=list(reversed(segment.trkpt)))
                for segment in reversed(track.trkseg)
            ]
            new_trk.append(
                Track(
                    name=track.name,
                    cmt=track.cmt,
                    desc=track.desc,
                    src=track.src,
                    link=track.link,
                    number=track.number,
                    type=track.type,
                    trkseg=new_trkseg,
                )
            )

    return GPX(
        creator=gpx.creator,
        metadata=gpx.metadata,
        wpt=gpx.wpt,
        rte=new_rte,
        trk=new_trk,
    )


def _apply_precision(
    gpx: GPX,
    coord_precision: int | None,
    elevation_precision: int | None,
) -> GPX:
    """Apply precision reduction to coordinates and elevations."""

    def round_point(point: Waypoint) -> Waypoint:
        lat = point.lat
        lon = point.lon
        ele = point.ele

        if coord_precision is not None:
            lat = Latitude(str(round(float(lat), coord_precision)))
            lon = Longitude(str(round(float(lon), coord_precision)))

        if elevation_precision is not None and ele is not None:
            ele = Decimal(str(round(float(ele), elevation_precision)))

        return Waypoint(
            lat=lat,
            lon=lon,
            ele=ele,
            time=point.time,
            magvar=point.magvar,
            geoidheight=point.geoidheight,
            name=point.name,
            cmt=point.cmt,
            desc=point.desc,
            src=point.src,
            link=point.link,
            sym=point.sym,
            type=point.type,
            fix=point.fix,
            sat=point.sat,
            hdop=point.hdop,
            vdop=point.vdop,
            pdop=point.pdop,
            ageofdgpsdata=point.ageofdgpsdata,
            dgpsid=point.dgpsid,
        )

    # Round waypoints
    new_wpt = [round_point(w) for w in gpx.wpt]

    # Round routes
    new_rte = [
        Route(
            name=route.name,
            cmt=route.cmt,
            desc=route.desc,
            src=route.src,
            link=route.link,
            number=route.number,
            type=route.type,
            rtept=[round_point(p) for p in route.rtept],
        )
        for route in gpx.rte
    ]

    # Round tracks
    new_trk = []
    for track in gpx.trk:
        new_trkseg = [
            TrackSegment(trkpt=[round_point(p) for p in segment.trkpt])
            for segment in track.trkseg
        ]
        new_trk.append(
            Track(
                name=track.name,
                cmt=track.cmt,
                desc=track.desc,
                src=track.src,
                link=track.link,
                number=track.number,
                type=track.type,
                trkseg=new_trkseg,
            )
        )

    return GPX(
        creator=gpx.creator,
        metadata=gpx.metadata,
        wpt=new_wpt,
        rte=new_rte,
        trk=new_trk,
    )


# =============================================================================
# Merge command
# =============================================================================


def _add_merge_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the merge subcommand parser."""
    parser = subparsers.add_parser(
        "merge",
        help="Merge multiple GPX files into one",
        description="Merge multiple GPX files into a single GPX file.",
    )
    parser.add_argument(
        "files",
        type=Path,
        nargs="+",
        help="Paths to the GPX files to merge",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path to the output GPX file",
    )
    parser.add_argument(
        "--creator",
        type=str,
        default="gpx-cli",
        help="Creator string for the merged file (default: gpx-cli)",
    )
    parser.set_defaults(func=_cmd_merge)


def _cmd_merge(args: argparse.Namespace) -> int:
    """Execute the merge command."""
    files: list[Path] = args.files
    output_path: Path = args.output
    creator: str = args.creator

    # Verify all files exist
    for file_path in files:
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            return 1

    # Read all GPX files
    gpx_files = [read_gpx(file_path) for file_path in files]

    # Merge
    merged_wpt: list[Waypoint] = []
    merged_rte: list[Route] = []
    merged_trk: list[Track] = []

    for gpx in gpx_files:
        merged_wpt.extend(gpx.wpt)
        merged_rte.extend(gpx.rte)
        merged_trk.extend(gpx.trk)

    merged_gpx = GPX(
        creator=creator,
        wpt=merged_wpt,
        rte=merged_rte,
        trk=merged_trk,
    )

    # Write output
    merged_gpx.write_gpx(output_path)
    print(f"Merged {len(files)} files into: {output_path}")
    print(f"  Waypoints: {len(merged_wpt)}")
    print(f"  Routes: {len(merged_rte)}")
    print(f"  Tracks: {len(merged_trk)}")
    return 0


# =============================================================================
# Convert command
# =============================================================================


def _add_convert_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the convert subcommand parser."""
    parser = subparsers.add_parser(
        "convert",
        help="Convert between GPX, GeoJSON, and KML formats",
        description="Convert GPX files to other formats or vice versa.",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to the input file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path to the output file",
    )
    parser.add_argument(
        "-f",
        "--from-format",
        type=str,
        choices=["gpx", "geojson", "kml"],
        help="Input format (default: auto-detect from extension)",
    )
    parser.add_argument(
        "-t",
        "--to-format",
        type=str,
        choices=["gpx", "geojson", "kml"],
        help="Output format (default: auto-detect from extension)",
    )
    parser.set_defaults(func=_cmd_convert)


def _cmd_convert(args: argparse.Namespace) -> int:
    """Execute the convert command."""
    input_path: Path = args.input
    output_path: Path = args.output

    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return 1

    # Determine input format
    input_format = args.from_format or _detect_format(input_path)
    if not input_format:
        print(
            f"Error: Could not detect input format for: {input_path}", file=sys.stderr
        )
        return 1

    # Determine output format
    output_format = args.to_format or _detect_format(output_path)
    if not output_format:
        print(
            f"Error: Could not detect output format for: {output_path}", file=sys.stderr
        )
        return 1

    # Read input
    gpx = _read_input(input_path, input_format)
    if gpx is None:
        print(f"Error: Unsupported input format: {input_format}", file=sys.stderr)
        return 1

    # Write output
    if not _write_output(gpx, output_path, output_format):
        print(f"Error: Unsupported output format: {output_format}", file=sys.stderr)
        return 1

    print(f"Converted {input_path} ({input_format}) to {output_path} ({output_format})")
    return 0


def _read_input(input_path: Path, input_format: str) -> GPX | None:
    """Read input file based on format."""
    if input_format == "gpx":
        return read_gpx(input_path)
    if input_format == "geojson":
        return read_geojson(input_path)
    if input_format == "kml":
        return read_kml(input_path)
    return None


def _write_output(gpx: GPX, output_path: Path, output_format: str) -> bool:
    """Write output file based on format."""
    if output_format == "gpx":
        gpx.write_gpx(output_path)
    elif output_format == "geojson":
        gpx.write_geojson(output_path)
    elif output_format == "kml":
        gpx.write_kml(output_path)
    else:
        return False
    return True


def _detect_format(path: Path) -> str | None:
    """Detect file format from extension."""
    suffix = path.suffix.lower()
    format_map = {
        ".gpx": "gpx",
        ".geojson": "geojson",
        ".json": "geojson",
        ".kml": "kml",
    }
    return format_map.get(suffix)


if __name__ == "__main__":
    sys.exit(main())
