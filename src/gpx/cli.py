"""Command-line interface for the gpx package.

This module provides a CLI for common GPX operations including validation,
information display, editing, merging, and format conversion.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import json
import sys
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING

from .io import convert_file, read_gpx
from .operations import (
    crop,
    reduce_precision,
    reverse,
    shift_time,
    simplify,
    smooth,
    split,
    strip_extensions,
    strip_metadata,
    trim,
)
from .operations import merge as merge_op
from .validation import ValidationResult
from .validation import validate as validate_gpx

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .gpx import GPX
    from .route import Route
    from .track import Track
    from .waypoint import Waypoint


def cli(argv: Sequence[str] | None = None) -> int:
    """Entry point for the gpx CLI.

    Args:
        argv: Command-line arguments. Defaults to `sys.argv[1:]`.

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
        version=f"gpx {metadata.version('gpx')}",
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


def _add_validate_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the validate subcommand parser."""
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a GPX file against the GPX 1.1 schema",
        description="Validate a GPX file against the GPX 1.1 schema, reporting "
        "all errors and warnings.",
    )
    validate_parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the input GPX file",
        metavar="<INPUT_FILE>",
    )
    validate_parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures (non-zero exit code)",
    )
    validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Output the validation report in JSON format",
    )
    validate_parser.set_defaults(func=validate)


def validate(args: argparse.Namespace) -> int:
    """Execute the validate command."""
    file_path: Path = args.input_file

    if not file_path.exists():
        if args.json:
            print(json.dumps({"file": str(file_path), "error": "file not found"}))
        else:
            print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    result = validate_gpx(file_path)

    # The file fails (exit 1) on any error, or on any warning in strict mode.
    failed = bool(result.errors) or (args.strict and bool(result.warnings))

    if args.json:
        return _validate_json_output(file_path, result, failed=failed)

    return _validate_text_output(file_path, result, failed=failed)


def _validate_json_output(
    file_path: Path, result: ValidationResult, *, failed: bool
) -> int:
    """Print the validation report as JSON and return the exit code."""
    # "valid" reflects schema validity (no errors); "passed" reflects the exit
    # status, which also fails on warnings in strict mode.
    report: dict = {
        "file": str(file_path),
        "valid": result.is_valid,
        "passed": not failed,
        "errors": len(result.errors),
        "warnings": len(result.warnings),
        "issues": [issue.to_dict() for issue in result.issues],
    }
    print(json.dumps(report, indent=2))
    return 1 if failed else 0


def _validate_text_output(
    file_path: Path, result: ValidationResult, *, failed: bool
) -> int:
    """Print a human-readable validation report and return the exit code."""
    n_errors = len(result.errors)
    n_warnings = len(result.warnings)

    if result.issues:
        mark = "✗" if failed else "⚠"
        error_label = "error" if n_errors == 1 else "errors"
        warning_label = "warning" if n_warnings == 1 else "warnings"
        print(
            f"{mark} {file_path}: {n_errors} {error_label}, "
            f"{n_warnings} {warning_label}"
        )
        print()
        for issue in result.issues:
            print(f"  {issue}")
        print()

    if result.is_valid:
        # The document is schema-valid, so it is guaranteed to parse; guard the
        # read anyway so the CLI reports cleanly instead of raising a traceback.
        try:
            gpx = read_gpx(file_path)
        except Exception as e:  # noqa: BLE001
            print(
                f"✗ {file_path}: passed schema validation but could not be parsed: {e}",
                file=sys.stderr,
            )
            return 1

        if failed:
            # Schema-valid but failing because warnings are errors in strict mode.
            print(f"✗ {file_path}: failed because warnings are present (--strict)")
        else:
            print(f"✓ Valid GPX file: {file_path}")
        print(f"  Creator: {gpx.creator}")
        print(f"  Waypoints: {len(gpx.wpt)}")
        print(f"  Routes: {len(gpx.rte)}")
        print(f"  Tracks: {len(gpx.trk)}")

    return 1 if failed else 0


def _add_info_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the info subcommand parser."""
    info_parser = subparsers.add_parser(
        "info",
        help="Show information and statistics about a GPX file",
        description="Display detailed information and statistics about a GPX file.",
    )
    info_parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the input GPX file",
        metavar="<INPUT_FILE>",
    )
    info_parser.add_argument(
        "--json",
        action="store_true",
        help="Output information in JSON format",
    )
    info_parser.set_defaults(func=info)


def info(args: argparse.Namespace) -> int:
    """Execute the info command."""
    file_path: Path = args.input_file

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


def _add_edit_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the edit subcommand parser."""
    edit_parser = subparsers.add_parser(
        "edit",
        help="Edit a GPX file with various transformations",
        description="Edit a GPX file with various transformations like cropping, "
        "trimming, reversing, and stripping metadata.",
    )
    edit_parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the input GPX file",
        metavar="<INPUT_FILE>",
    )
    edit_parser.add_argument(
        "-o",
        "--output-file",
        type=Path,
        required=True,
        help="Path to the output file",
        metavar="<OUTPUT_FILE>",
        dest="output_file",
    )

    # Crop options
    crop_group = edit_parser.add_argument_group(
        "crop options", "Crop to a geographic bounding box"
    )
    crop_group.add_argument(
        "--min-lat",
        type=float,
        metavar="LATITUDE",
        help="Minimum latitude for crop",
    )
    crop_group.add_argument(
        "--max-lat",
        type=float,
        metavar="LATITUDE",
        help="Maximum latitude for crop",
    )
    crop_group.add_argument(
        "--min-lon",
        type=float,
        metavar="LONGITUDE",
        help="Minimum longitude for crop",
    )
    crop_group.add_argument(
        "--max-lon",
        type=float,
        metavar="LONGITUDE",
        help="Maximum longitude for crop",
    )

    # Trim options
    trim_group = edit_parser.add_argument_group(
        "trim options", "Trim to a date/time range"
    )
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

    # Split options
    split_group = edit_parser.add_argument_group(
        "split options", "Split track segments at gaps"
    )
    split_group.add_argument(
        "--split-time-gap",
        type=float,
        metavar="SECONDS",
        help="Split track segments where the time between consecutive points "
        "exceeds this many seconds",
    )
    split_group.add_argument(
        "--split-distance-gap",
        type=float,
        metavar="METERS",
        help="Split track segments where the distance between consecutive points "
        "exceeds this many metres",
    )

    # Simplify options
    simplify_group = edit_parser.add_argument_group(
        "simplify options", "Simplify tracks and routes"
    )
    simplify_group.add_argument(
        "--simplify",
        type=float,
        metavar="TOLERANCE",
        help="Simplify tracks and routes with the Ramer-Douglas-Peucker algorithm "
        "using this tolerance (in metres)",
    )

    # Smooth options
    smooth_group = edit_parser.add_argument_group(
        "smooth options", "Smooth tracks and routes"
    )
    smooth_group.add_argument(
        "--smooth",
        type=int,
        metavar="WINDOW",
        help="Smooth track and route coordinates and elevations with a moving "
        "average over this many points (an odd integer of at least 3)",
    )

    # Time shift options
    shift_group = edit_parser.add_argument_group(
        "time shift options", "Shift timestamps"
    )
    shift_group.add_argument(
        "--shift-time",
        type=float,
        metavar="SECONDS",
        help="Shift all point timestamps by this many seconds (may be negative)",
    )

    # Reverse options
    reverse_group = edit_parser.add_argument_group(
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
    strip_group = edit_parser.add_argument_group(
        "strip options", "Strip metadata fields"
    )
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
    strip_group.add_argument(
        "--strip-extensions",
        action="store_true",
        help="Strip all extensions",
    )

    # Precision options
    precision_group = edit_parser.add_argument_group(
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

    edit_parser.set_defaults(func=edit)


def edit(args: argparse.Namespace) -> int:  # noqa: C901, PLR0912
    """Execute the edit command."""
    input_path: Path = args.input_file
    output_path: Path = args.output_file

    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return 1

    gpx = read_gpx(input_path)

    # Apply crop
    if any(
        v is not None for v in (args.min_lat, args.max_lat, args.min_lon, args.max_lon)
    ):
        gpx = crop(
            gpx,
            min_lat=args.min_lat,
            max_lat=args.max_lat,
            min_lon=args.min_lon,
            max_lon=args.max_lon,
        )

    # Apply trim
    if args.start or args.end:
        start_dt = _parse_datetime(args.start) if args.start else None
        end_dt = _parse_datetime(args.end) if args.end else None
        gpx = trim(gpx, start=start_dt, end=end_dt)

    # Apply split
    if args.split_time_gap is not None or args.split_distance_gap is not None:
        gpx = split(
            gpx,
            time_gap=dt.timedelta(seconds=args.split_time_gap)
            if args.split_time_gap is not None
            else None,
            distance_gap=args.split_distance_gap,
        )

    # Apply simplify
    if args.simplify is not None:
        gpx = simplify(gpx, args.simplify)

    # Apply smooth
    if args.smooth is not None:
        gpx = smooth(gpx, window=args.smooth)

    # Apply time shift
    if args.shift_time is not None:
        gpx = shift_time(gpx, dt.timedelta(seconds=args.shift_time))

    # Apply reverse
    if args.reverse:
        gpx = reverse(gpx, routes=True, tracks=True)
    else:
        if args.reverse_routes:
            gpx = reverse(gpx, routes=True, tracks=False)
        if args.reverse_tracks:
            gpx = reverse(gpx, routes=False, tracks=True)

    # Apply strip metadata
    gpx = _apply_strip_metadata(gpx, args)

    # Apply strip extensions
    if args.strip_extensions:
        gpx = strip_extensions(gpx)

    # Apply precision reduction
    if args.precision is not None or args.elevation_precision is not None:
        gpx = reduce_precision(
            gpx,
            coordinate_precision=args.precision,
            elevation_precision=args.elevation_precision,
        )

    # Write output
    gpx.write_gpx(output_path)
    print(f"Written to: {output_path}")
    return 0


def _apply_strip_metadata(gpx: GPX, args: argparse.Namespace) -> GPX:
    """Apply metadata stripping based on the command-line arguments."""
    if args.strip_all_metadata:
        return strip_metadata(gpx)

    fields = {
        "name": args.strip_name,
        "desc": args.strip_desc,
        "author": args.strip_author,
        "copyright": args.strip_copyright,
        "time": args.strip_time,
        "keywords": args.strip_keywords,
        "links": args.strip_links,
    }
    if not any(fields.values()):
        return gpx
    return strip_metadata(gpx, **fields)


def _parse_datetime(dt_str: str) -> dt.datetime:
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
            dt_ = dt.datetime.strptime(dt_str, fmt)  # noqa: DTZ007
            # Add dt.UTC timezone if none specified
            if dt_.tzinfo is None:
                dt_ = dt_.replace(tzinfo=dt.UTC)
        except ValueError:
            continue
        else:
            return dt_

    msg = (
        f"Invalid datetime format: {dt_str}. "
        "Use ISO 8601 format (e.g., 2024-01-01T10:00:00)"
    )
    raise ValueError(msg)


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
        "input_files",
        type=Path,
        nargs="+",
        help="Paths to the GPX files to merge",
        metavar="<INPUT_FILE>",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        type=Path,
        required=True,
        help="Path to the output file",
        metavar="<OUTPUT_FILE>",
        dest="output_file",
    )
    parser.set_defaults(func=merge)


def merge(args: argparse.Namespace) -> int:
    """Execute the merge command."""
    files: list[Path] = args.input_files
    output_path: Path = args.output_file

    # Verify all files exist
    for file_path in files:
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            return 1

    # Read and merge all GPX files
    merged_gpx = merge_op(read_gpx(file_path) for file_path in files)

    # Write output
    merged_gpx.write_gpx(output_path)
    print(f"Merged {len(files)} files into: {output_path}")
    print(f"  Waypoints: {len(merged_gpx.wpt)}")
    print(f"  Routes: {len(merged_gpx.rte)}")
    print(f"  Tracks: {len(merged_gpx.trk)}")
    return 0


def _add_convert_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the convert subcommand parser."""
    parser = subparsers.add_parser(
        "convert",
        help="Convert between GPX, GeoJSON, and KML file formats",
        description="Convert GPX files to other file formats or vice versa.",
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the input file",
        metavar="<INPUT_FILE>",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        type=Path,
        required=True,
        help="Path to the output file",
        metavar="<OUTPUT_FILE>",
        dest="output_file",
    )
    parser.add_argument(
        "-f",
        "--from-format",
        type=str,
        choices=["gpx", "geojson", "kml"],
        help="Input format (default: auto-detect from file extension)",
    )
    parser.add_argument(
        "-t",
        "--to-format",
        type=str,
        choices=["gpx", "geojson", "kml"],
        help="Output format (default: auto-detect from file extension)",
    )
    parser.set_defaults(func=convert)


def convert(args: argparse.Namespace) -> int:
    """Execute the convert command."""
    input_path: Path = args.input_file
    output_path: Path = args.output_file

    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return 1

    try:
        input_format, output_format = convert_file(
            input_path,
            output_path,
            input_format=args.from_format,
            output_format=args.to_format,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Converted {input_path} ({input_format}) to {output_path} ({output_format})")
    return 0


if __name__ == "__main__":
    sys.exit(cli())
