"""Operations for editing and merging GPX models.

This module provides the operations behind the ``gpx edit`` and ``gpx merge``
CLI commands as a reusable, importable API.

All operations are pure: they never mutate the input, but return a new
:class:`~gpx.gpx.GPX` instance instead. Namespace mappings (``nsmap``) and
extensions are preserved.
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from math import cos, radians, sqrt
from statistics import fmean
from typing import TYPE_CHECKING

from .gpx import GPX
from .types import Latitude, Longitude

if TYPE_CHECKING:
    import datetime as dt
    from collections.abc import Callable, Iterable

    from .route import Route
    from .track import Track
    from .track_segment import TrackSegment
    from .waypoint import Waypoint


def filter_points(gpx: GPX, predicate: Callable[[Waypoint], bool]) -> GPX:
    """Return a new GPX with each point list filtered by ``predicate``.

    Waypoints, route points and track points for which ``predicate`` returns
    False are dropped. Routes, track segments and tracks that end up empty
    are dropped as well.

    Args:
        gpx: The GPX instance to filter.
        predicate: A callable that returns True for points to keep.

    Returns:
        A new GPX instance with the filtered points.

    Example:
        >>> from gpx import filter_points, read_gpx
        >>> gpx = read_gpx("path/to/file.gpx")
        >>> with_ele = filter_points(gpx, lambda point: point.ele is not None)

    """
    new_wpt = [w for w in gpx.wpt if predicate(w)]

    new_rte: list[Route] = []
    for route in gpx.rte:
        kept = [p for p in route.rtept if predicate(p)]
        if kept:
            new_rte.append(replace(route, rtept=kept))

    new_trk: list[Track] = []
    for track in gpx.trk:
        new_trkseg = [
            replace(segment, trkpt=kept)
            for segment in track.trkseg
            if (kept := [p for p in segment.trkpt if predicate(p)])
        ]
        if new_trkseg:
            new_trk.append(replace(track, trkseg=new_trkseg))

    return replace(gpx, wpt=new_wpt, rte=new_rte, trk=new_trk)


def _map_points(gpx: GPX, transform: Callable[[Waypoint], Waypoint]) -> GPX:
    """Return a new GPX with ``transform`` applied to every point.

    Waypoints, route points and track points are all transformed. The
    structure of the GPX (routes, tracks, segments) is left unchanged.
    """
    new_wpt = [transform(w) for w in gpx.wpt]
    new_rte = [
        replace(route, rtept=[transform(p) for p in route.rtept]) for route in gpx.rte
    ]
    new_trk = [
        replace(
            track,
            trkseg=[
                replace(segment, trkpt=[transform(p) for p in segment.trkpt])
                for segment in track.trkseg
            ],
        )
        for track in gpx.trk
    ]
    return replace(gpx, wpt=new_wpt, rte=new_rte, trk=new_trk)


def crop(
    gpx: GPX,
    *,
    min_lat: float | None = None,
    max_lat: float | None = None,
    min_lon: float | None = None,
    max_lon: float | None = None,
) -> GPX:
    """Crop a GPX to a geographic bounding box.

    Points outside the given bounds are dropped. Bounds that are None are
    not enforced. Routes, track segments and tracks that end up empty are
    dropped as well.

    Args:
        gpx: The GPX instance to crop.
        min_lat: Minimum latitude. Defaults to None (no minimum).
        max_lat: Maximum latitude. Defaults to None (no maximum).
        min_lon: Minimum longitude. Defaults to None (no minimum).
        max_lon: Maximum longitude. Defaults to None (no maximum).

    Returns:
        A new GPX instance cropped to the given bounds.

    Example:
        >>> from gpx import crop, read_gpx
        >>> gpx = read_gpx("path/to/file.gpx")
        >>> cropped = crop(gpx, min_lat=52.0, max_lat=53.0)

    """

    def is_in_bounds(point: Waypoint) -> bool:
        lat, lon = float(point.lat), float(point.lon)
        if min_lat is not None and lat < min_lat:
            return False
        if max_lat is not None and lat > max_lat:
            return False
        if min_lon is not None and lon < min_lon:
            return False
        return not (max_lon is not None and lon > max_lon)

    return filter_points(gpx, is_in_bounds)


def trim(
    gpx: GPX,
    *,
    start: dt.datetime | None = None,
    end: dt.datetime | None = None,
) -> GPX:
    """Trim a GPX to a date/time range.

    Points with a timestamp outside the given range are dropped; points
    without a timestamp are kept. Routes, track segments and tracks that
    end up empty are dropped as well.

    Args:
        gpx: The GPX instance to trim.
        start: Start of the time range. Defaults to None (no start).
        end: End of the time range. Defaults to None (no end).

    Returns:
        A new GPX instance trimmed to the given time range.

    Example:
        >>> import datetime as dt
        >>> from gpx import read_gpx, trim
        >>> gpx = read_gpx("path/to/file.gpx")
        >>> trimmed = trim(gpx, start=dt.datetime(2024, 1, 1, tzinfo=dt.UTC))

    """

    def is_in_time_range(point: Waypoint) -> bool:
        if point.time is None:
            return True  # Keep points without timestamps
        if start is not None and point.time < start:
            return False
        return not (end is not None and point.time > end)

    return filter_points(gpx, is_in_time_range)


def reverse(gpx: GPX, *, routes: bool = True, tracks: bool = True) -> GPX:
    """Reverse the routes and/or tracks of a GPX.

    For tracks, both the order of the segments and the order of the points
    within each segment are reversed.

    Args:
        gpx: The GPX instance to reverse.
        routes: Whether to reverse the routes. Defaults to True.
        tracks: Whether to reverse the tracks. Defaults to True.

    Returns:
        A new GPX instance with the routes and/or tracks reversed.

    Example:
        >>> from gpx import read_gpx, reverse
        >>> gpx = read_gpx("path/to/file.gpx")
        >>> reversed_gpx = reverse(gpx)

    """
    new_rte = gpx.rte
    new_trk = gpx.trk

    if routes:
        new_rte = [
            replace(route, rtept=list(reversed(route.rtept))) for route in gpx.rte
        ]

    if tracks:
        new_trk = [
            replace(
                track,
                trkseg=[
                    replace(segment, trkpt=list(reversed(segment.trkpt)))
                    for segment in reversed(track.trkseg)
                ],
            )
            for track in gpx.trk
        ]

    return replace(gpx, rte=new_rte, trk=new_trk)


def strip_metadata(  # noqa: PLR0913
    gpx: GPX,
    *,
    name: bool = False,
    desc: bool = False,
    author: bool = False,
    copyright: bool = False,  # noqa: A002
    time: bool = False,
    keywords: bool = False,
    links: bool = False,
) -> GPX:
    """Strip metadata (fields) from a GPX.

    When no field flags are given, the entire metadata element is removed.
    Otherwise, only the selected fields are removed from the metadata.

    Args:
        gpx: The GPX instance to strip metadata from.
        name: Whether to strip the metadata name. Defaults to False.
        desc: Whether to strip the metadata description. Defaults to False.
        author: Whether to strip the metadata author. Defaults to False.
        copyright: Whether to strip the metadata copyright. Defaults to False.
        time: Whether to strip the metadata time. Defaults to False.
        keywords: Whether to strip the metadata keywords. Defaults to False.
        links: Whether to strip the metadata links. Defaults to False.

    Returns:
        A new GPX instance with the metadata (fields) stripped.

    Example:
        >>> from gpx import read_gpx, strip_metadata
        >>> gpx = read_gpx("path/to/file.gpx")
        >>> anonymous = strip_metadata(gpx, author=True, copyright=True)
        >>> bare = strip_metadata(gpx)  # removes all metadata

    """
    if not any((name, desc, author, copyright, time, keywords, links)):
        return replace(gpx, metadata=None)

    metadata = gpx.metadata
    if metadata is None:
        return gpx

    if name:
        metadata = replace(metadata, name=None)
    if desc:
        metadata = replace(metadata, desc=None)
    if author:
        metadata = replace(metadata, author=None)
    if copyright:
        metadata = replace(metadata, copyright=None)
    if time:
        metadata = replace(metadata, time=None)
    if keywords:
        metadata = replace(metadata, keywords=None)
    if links:
        metadata = replace(metadata, link=[])
    return replace(gpx, metadata=metadata)


def reduce_precision(
    gpx: GPX,
    *,
    coordinate_precision: int | None = None,
    elevation_precision: int | None = None,
) -> GPX:
    """Reduce the precision of the coordinates and/or elevations of a GPX.

    Args:
        gpx: The GPX instance to reduce the precision of.
        coordinate_precision: Number of decimal places for lat/lon
            coordinates. Defaults to None (unchanged).
        elevation_precision: Number of decimal places for elevations.
            Defaults to None (unchanged).

    Returns:
        A new GPX instance with the precision reduced.

    Example:
        >>> from gpx import read_gpx, reduce_precision
        >>> gpx = read_gpx("path/to/file.gpx")
        >>> reduced = reduce_precision(gpx, coordinate_precision=6)

    """

    def round_point(point: Waypoint) -> Waypoint:
        if coordinate_precision is None and elevation_precision is None:
            return point
        new_lat = (
            Latitude(str(round(float(point.lat), coordinate_precision)))
            if coordinate_precision is not None
            else point.lat
        )
        new_lon = (
            Longitude(str(round(float(point.lon), coordinate_precision)))
            if coordinate_precision is not None
            else point.lon
        )
        new_ele = (
            Decimal(str(round(float(point.ele), elevation_precision)))
            if elevation_precision is not None and point.ele is not None
            else point.ele
        )
        return replace(point, lat=new_lat, lon=new_lon, ele=new_ele)

    return _map_points(gpx, round_point)


def split(
    gpx: GPX,
    *,
    time_gap: dt.timedelta | None = None,
    distance_gap: float | None = None,
) -> GPX:
    """Split track segments at time and/or distance gaps.

    Each track segment is split into multiple segments wherever the gap
    between two consecutive track points exceeds ``time_gap`` and/or
    ``distance_gap``. This is useful when a GPS device kept recording
    across a pause or signal loss, since the GPX 1.1 specification calls
    for a new track segment for each continuous span of track data.

    Points without a timestamp never trigger a time-based split. Each
    resulting segment keeps the original segment's extensions. Waypoints
    and routes are left unchanged.

    Args:
        gpx: The GPX instance to split.
        time_gap: Split where the time between consecutive points exceeds
            this duration. Defaults to None (no time-based splitting).
        distance_gap: Split where the distance between consecutive points
            exceeds this many metres. Defaults to None (no distance-based
            splitting).

    Returns:
        A new GPX instance with the track segments split.

    Raises:
        ValueError: If neither ``time_gap`` nor ``distance_gap`` is given.

    Example:
        >>> import datetime as dt
        >>> from gpx import read_gpx, split
        >>> gpx = read_gpx("path/to/file.gpx")
        >>> split_gpx = split(gpx, time_gap=dt.timedelta(minutes=10))

    """
    if time_gap is None and distance_gap is None:
        msg = "At least one of time_gap or distance_gap must be given"
        raise ValueError(msg)

    def is_gap(prev: Waypoint, point: Waypoint) -> bool:
        if (
            time_gap is not None
            and prev.time is not None
            and point.time is not None
            and point.time - prev.time > time_gap
        ):
            return True
        return distance_gap is not None and prev.distance_to(point) > distance_gap

    new_trk: list[Track] = []
    for track in gpx.trk:
        new_trkseg: list[TrackSegment] = []
        for segment in track.trkseg:
            if not segment.trkpt:
                new_trkseg.append(segment)
                continue
            parts: list[list[Waypoint]] = [[]]
            for point in segment.trkpt:
                if parts[-1] and is_gap(parts[-1][-1], point):
                    parts.append([])
                parts[-1].append(point)
            new_trkseg.extend(replace(segment, trkpt=part) for part in parts)
        new_trk.append(replace(track, trkseg=new_trkseg))

    return replace(gpx, trk=new_trk)


#: Earth radius (in metres) used for planar projections, matching
#: :meth:`~gpx.waypoint.Waypoint.distance_to`.
_EARTH_RADIUS = 6_378_137


def _perpendicular_distance(point: Waypoint, start: Waypoint, end: Waypoint) -> float:
    """Return the distance (in metres) from ``point`` to the ``start``-``end`` segment.

    Uses a local equirectangular projection centered on ``start``, which is
    accurate for the small extents typical of GPS tracks.
    """
    lat0 = radians(float(start.lat))
    lon0 = radians(float(start.lon))
    cos_lat0 = cos(lat0)

    def project(p: Waypoint) -> tuple[float, float]:
        x = (radians(float(p.lon)) - lon0) * cos_lat0 * _EARTH_RADIUS
        y = (radians(float(p.lat)) - lat0) * _EARTH_RADIUS
        return x, y

    px, py = project(point)
    ex, ey = project(end)  # start projects to (0, 0)

    segment_length_sq = ex * ex + ey * ey
    if segment_length_sq == 0:
        return sqrt(px * px + py * py)

    # Clamp the projection of the point onto the segment to its endpoints
    t = max(0.0, min(1.0, (px * ex + py * ey) / segment_length_sq))
    dx = px - t * ex
    dy = py - t * ey
    return sqrt(dx * dx + dy * dy)


def _ramer_douglas_peucker(points: list[Waypoint], tolerance: float) -> list[Waypoint]:
    """Simplify a list of points with the Ramer-Douglas-Peucker algorithm.

    Uses an explicit stack instead of recursion to handle long tracks.
    """
    if len(points) < 3:  # noqa: PLR2004
        return list(points)

    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        start, end = stack.pop()
        max_distance = 0.0
        index = start
        for i in range(start + 1, end):
            distance = _perpendicular_distance(points[i], points[start], points[end])
            if distance > max_distance:
                max_distance = distance
                index = i
        if max_distance > tolerance:
            keep[index] = True
            stack.append((start, index))
            stack.append((index, end))

    return [point for point, kept in zip(points, keep, strict=True) if kept]


def simplify(gpx: GPX, tolerance: float) -> GPX:
    """Simplify the tracks and routes of a GPX.

    Reduces the number of route points and track points using the
    Ramer-Douglas-Peucker algorithm: points closer than ``tolerance`` to the
    line between their surviving neighbors are dropped, while the overall
    shape is preserved. The first and last point of each route and track
    segment are always kept. Waypoints are left unchanged.

    Args:
        gpx: The GPX instance to simplify.
        tolerance: The maximum allowed deviation (in metres) of a dropped
            point from the simplified line.

    Returns:
        A new GPX instance with the tracks and routes simplified.

    Raises:
        ValueError: If ``tolerance`` is not positive.

    Example:
        >>> from gpx import read_gpx, simplify
        >>> gpx = read_gpx("path/to/file.gpx")
        >>> simplified = simplify(gpx, tolerance=10.0)

    """
    if tolerance <= 0:
        msg = f"tolerance must be positive, got {tolerance}"
        raise ValueError(msg)

    new_rte = [
        replace(route, rtept=_ramer_douglas_peucker(route.rtept, tolerance))
        for route in gpx.rte
    ]
    new_trk = [
        replace(
            track,
            trkseg=[
                replace(segment, trkpt=_ramer_douglas_peucker(segment.trkpt, tolerance))
                for segment in track.trkseg
            ],
        )
        for track in gpx.trk
    ]

    return replace(gpx, rte=new_rte, trk=new_trk)


def smooth(
    gpx: GPX,
    *,
    window: int = 5,
    coordinates: bool = True,
    elevations: bool = True,
) -> GPX:
    """Smooth the tracks and routes of a GPX with a moving average.

    Applies a centered moving average to the coordinates and/or elevations
    of route points and track points, reducing GPS noise. The window
    shrinks symmetrically near the start and end of each route and track
    segment, so the first and last point are always left unchanged. Points
    without elevation are skipped during elevation smoothing (and do not
    contribute to their neighbors' averages). Waypoints are left unchanged.

    Args:
        gpx: The GPX instance to smooth.
        window: The size of the moving average window (an odd integer of at
            least 3). Defaults to 5.
        coordinates: Whether to smooth the lat/lon coordinates. Defaults to
            True.
        elevations: Whether to smooth the elevations. Defaults to True.

    Returns:
        A new GPX instance with the tracks and routes smoothed.

    Raises:
        ValueError: If ``window`` is not an odd integer of at least 3.

    Example:
        >>> from gpx import read_gpx, smooth
        >>> gpx = read_gpx("path/to/file.gpx")
        >>> smoothed = smooth(gpx, window=5)

    """
    if window < 3 or window % 2 == 0:  # noqa: PLR2004
        msg = f"window must be an odd integer of at least 3, got {window}"
        raise ValueError(msg)
    half = window // 2

    def smooth_points(points: list[Waypoint]) -> list[Waypoint]:
        n = len(points)
        if n < 3:  # noqa: PLR2004
            return list(points)
        new_points: list[Waypoint] = []
        for i, point in enumerate(points):
            # Shrink the window symmetrically near the ends
            k = min(half, i, n - 1 - i)
            if k == 0:
                new_points.append(point)
                continue
            neighbors = points[i - k : i + k + 1]
            new_lat, new_lon = point.lat, point.lon
            if coordinates:
                new_lat = Latitude(str(fmean(float(p.lat) for p in neighbors)))
                new_lon = Longitude(str(fmean(float(p.lon) for p in neighbors)))
            new_ele = point.ele
            if elevations and point.ele is not None:
                ele_values = [float(p.ele) for p in neighbors if p.ele is not None]
                new_ele = Decimal(str(fmean(ele_values)))
            new_points.append(replace(point, lat=new_lat, lon=new_lon, ele=new_ele))
        return new_points

    new_rte = [replace(route, rtept=smooth_points(route.rtept)) for route in gpx.rte]
    new_trk = [
        replace(
            track,
            trkseg=[
                replace(segment, trkpt=smooth_points(segment.trkpt))
                for segment in track.trkseg
            ],
        )
        for track in gpx.trk
    ]

    return replace(gpx, rte=new_rte, trk=new_trk)


def shift_time(gpx: GPX, delta: dt.timedelta) -> GPX:
    """Shift all point timestamps of a GPX by a time delta.

    The timestamps of all waypoints, route points and track points are
    shifted by ``delta``; points without a timestamp are left unchanged.
    This is useful for fixing timezone mistakes or GPS clock drift. The
    metadata timestamp (the file creation time) is not shifted.

    Args:
        gpx: The GPX instance to shift the timestamps of.
        delta: The time delta to shift by (may be negative).

    Returns:
        A new GPX instance with the timestamps shifted.

    Example:
        >>> import datetime as dt
        >>> from gpx import read_gpx, shift_time
        >>> gpx = read_gpx("path/to/file.gpx")
        >>> shifted = shift_time(gpx, dt.timedelta(hours=-2))

    """

    def shift_point(point: Waypoint) -> Waypoint:
        if point.time is None:
            return point
        return replace(point, time=point.time + delta)

    return _map_points(gpx, shift_point)


def strip_extensions(gpx: GPX) -> GPX:
    """Strip all extensions from a GPX.

    Removes the extension elements from the GPX itself, its metadata, and
    all waypoints, routes, route points, tracks, track segments and track
    points. This is useful for removing vendor-specific data (e.g. heart
    rate, cadence, temperature) for privacy or to reduce file size.

    Args:
        gpx: The GPX instance to strip the extensions from.

    Returns:
        A new GPX instance without extensions.

    Example:
        >>> from gpx import read_gpx, strip_extensions
        >>> gpx = read_gpx("path/to/file.gpx")
        >>> stripped = strip_extensions(gpx)

    """

    def strip_point(point: Waypoint) -> Waypoint:
        if point.extensions is None:
            return point
        return replace(point, extensions=None)

    stripped = _map_points(gpx, strip_point)

    new_metadata = (
        replace(stripped.metadata, extensions=None)
        if stripped.metadata is not None
        else None
    )
    new_rte = [replace(route, extensions=None) for route in stripped.rte]
    new_trk = [
        replace(
            track,
            extensions=None,
            trkseg=[replace(segment, extensions=None) for segment in track.trkseg],
        )
        for track in stripped.trk
    ]

    return replace(
        stripped, metadata=new_metadata, rte=new_rte, trk=new_trk, extensions=None
    )


def merge(gpxs: Iterable[GPX], *, creator: str | None = None) -> GPX:
    """Merge multiple GPX instances into one.

    The waypoints, routes and tracks of all instances are concatenated, in
    order, into a single new GPX instance.

    Args:
        gpxs: The GPX instances to merge.
        creator: The creator string for the merged GPX. Defaults to None
            (uses default).

    Returns:
        A new GPX instance with the merged contents.

    Example:
        >>> from gpx import merge, read_gpx
        >>> merged = merge([read_gpx("one.gpx"), read_gpx("two.gpx")])

    """
    merged_wpt: list[Waypoint] = []
    merged_rte: list[Route] = []
    merged_trk: list[Track] = []

    for gpx in gpxs:
        merged_wpt.extend(gpx.wpt)
        merged_rte.extend(gpx.rte)
        merged_trk.extend(gpx.trk)

    merged = GPX(wpt=merged_wpt, rte=merged_rte, trk=merged_trk)
    if creator is not None:
        merged = replace(merged, creator=creator)
    return merged
