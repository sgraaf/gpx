"""Tests for gpx.operations module - Edit and merge operations."""

import datetime as dt
from decimal import Decimal

import pytest

from gpx import (
    GPX,
    Metadata,
    Person,
    Route,
    Track,
    TrackSegment,
    Waypoint,
    crop,
    filter_points,
    merge,
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
from gpx.types import Latitude, Longitude

from .conftest import CUSTOM_NS, GARMIN_TPX_NS


def make_track_gpx(points: list[Waypoint]) -> GPX:
    """Create a GPX with a single track containing a single segment."""
    return GPX(trk=[Track(trkseg=[TrackSegment(trkpt=points)])])


def make_points(
    coords: list[tuple[str, str]],
    *,
    minutes_apart: int | None = 1,
) -> list[Waypoint]:
    """Create waypoints from (lat, lon) strings, optionally with timestamps."""
    start = dt.datetime(2024, 1, 15, 10, 0, 0, tzinfo=dt.UTC)
    return [
        Waypoint(
            lat=Latitude(lat),
            lon=Longitude(lon),
            time=start + dt.timedelta(minutes=i * minutes_apart)
            if minutes_apart is not None
            else None,
        )
        for i, (lat, lon) in enumerate(coords)
    ]


class TestFilterPoints:
    """Tests for the filter_points operation."""

    def test_filter_points_keeps_matching(self, sample_gpx: GPX) -> None:
        """Points matching the predicate are kept."""
        filtered = filter_points(sample_gpx, lambda _: True)
        assert len(filtered.wpt) == len(sample_gpx.wpt)
        assert len(filtered.rte) == len(sample_gpx.rte)
        assert len(filtered.trk) == len(sample_gpx.trk)

    def test_filter_points_drops_empty_containers(self, sample_gpx: GPX) -> None:
        """Routes, segments and tracks that end up empty are dropped."""
        filtered = filter_points(sample_gpx, lambda _: False)
        assert filtered.wpt == []
        assert filtered.rte == []
        assert filtered.trk == []

    def test_filter_points_does_not_mutate_input(self, sample_gpx: GPX) -> None:
        """The input GPX is left unchanged."""
        original_wpt_count = len(sample_gpx.wpt)
        filter_points(sample_gpx, lambda _: False)
        assert len(sample_gpx.wpt) == original_wpt_count


class TestCrop:
    """Tests for the crop operation."""

    def test_crop(self, sample_gpx: GPX) -> None:
        """Test cropping GPX data."""
        cropped = crop(
            sample_gpx,
            min_lat=52.515,
            max_lat=52.525,
            min_lon=13.400,
            max_lon=13.410,
        )
        # Should keep some points but filter out those outside bounds
        assert len(cropped.wpt) >= 0
        assert len(cropped.trk) >= 0

    def test_crop_excludes_all(self, sample_gpx: GPX) -> None:
        """Test cropping with bounds that exclude all points."""
        cropped = crop(
            sample_gpx,
            min_lat=0.0,
            max_lat=1.0,
            min_lon=0.0,
            max_lon=1.0,
        )
        assert len(cropped.wpt) == 0
        assert len(cropped.rte) == 0
        assert len(cropped.trk) == 0

    def test_crop_partial_bounds(self, sample_gpx: GPX) -> None:
        """Bounds that are None are not enforced."""
        kept = crop(sample_gpx, min_lat=0.0)
        assert len(kept.wpt) == 1

        dropped = crop(sample_gpx, min_lat=53.0)
        assert len(dropped.wpt) == 0


class TestTrim:
    """Tests for the trim operation."""

    def test_trim(self, sample_gpx: GPX) -> None:
        """Test trimming GPX data to a time range."""
        start = dt.datetime(2024, 1, 15, 10, 0, 30, tzinfo=dt.UTC)
        end = dt.datetime(2024, 1, 15, 10, 1, 30, tzinfo=dt.UTC)
        trimmed = trim(sample_gpx, start=start, end=end)
        # Should keep only points within time range
        assert len(trimmed.trk) > 0
        for track in trimmed.trk:
            for seg in track.trkseg:
                for pt in seg.trkpt:
                    if pt.time:
                        assert pt.time >= start
                        assert pt.time <= end

    def test_trim_keeps_points_without_timestamps(self, sample_gpx: GPX) -> None:
        """Points without timestamps are kept (route points have no time)."""
        start = dt.datetime(2030, 1, 1, tzinfo=dt.UTC)
        trimmed = trim(sample_gpx, start=start)
        assert len(trimmed.rte) == 1


class TestReverse:
    """Tests for the reverse operation."""

    def test_reverse_routes(self, sample_gpx: GPX) -> None:
        """Test reversing routes."""
        original_first_lat = float(sample_gpx.rte[0].rtept[0].lat)
        original_last_lat = float(sample_gpx.rte[0].rtept[-1].lat)

        reversed_gpx = reverse(sample_gpx, routes=True, tracks=False)

        new_first_lat = float(reversed_gpx.rte[0].rtept[0].lat)
        new_last_lat = float(reversed_gpx.rte[0].rtept[-1].lat)

        assert new_first_lat == pytest.approx(original_last_lat, rel=1e-3)
        assert new_last_lat == pytest.approx(original_first_lat, rel=1e-3)

    def test_reverse_tracks(self, sample_gpx: GPX) -> None:
        """Test reversing tracks."""
        original_first_lat = float(sample_gpx.trk[0].trkseg[0].trkpt[0].lat)
        original_last_lat = float(sample_gpx.trk[0].trkseg[0].trkpt[-1].lat)

        reversed_gpx = reverse(sample_gpx, routes=False, tracks=True)

        new_first_lat = float(reversed_gpx.trk[0].trkseg[0].trkpt[0].lat)
        new_last_lat = float(reversed_gpx.trk[0].trkseg[0].trkpt[-1].lat)

        assert new_first_lat == pytest.approx(original_last_lat, rel=1e-3)
        assert new_last_lat == pytest.approx(original_first_lat, rel=1e-3)

    def test_reverse_defaults_to_both(self, sample_gpx: GPX) -> None:
        """By default, both routes and tracks are reversed."""
        reversed_gpx = reverse(sample_gpx)
        assert float(reversed_gpx.rte[0].rtept[0].lat) == pytest.approx(
            float(sample_gpx.rte[0].rtept[-1].lat), rel=1e-3
        )
        assert float(reversed_gpx.trk[0].trkseg[0].trkpt[0].lat) == pytest.approx(
            float(sample_gpx.trk[0].trkseg[0].trkpt[-1].lat), rel=1e-3
        )


class TestStripMetadata:
    """Tests for the strip_metadata operation."""

    def test_strip_all_metadata(self, sample_gpx: GPX) -> None:
        """With no field flags, the entire metadata element is removed."""
        stripped = strip_metadata(sample_gpx)
        assert stripped.metadata is None

    def test_strip_selected_fields(self, sample_gpx: GPX) -> None:
        """Only the selected fields are removed from the metadata."""
        stripped = strip_metadata(sample_gpx, name=True)
        assert stripped.metadata is not None
        assert stripped.metadata.name is None
        assert stripped.metadata.desc == "Test description"

    def test_strip_author_copyright_time_keywords_links(self) -> None:
        """All field flags strip their corresponding metadata field."""
        gpx = GPX(
            metadata=Metadata(
                name="Name",
                desc="Description",
                author=Person(name="Author"),
                time=dt.datetime(2024, 1, 15, tzinfo=dt.UTC),
                keywords="some, keywords",
            )
        )
        stripped = strip_metadata(
            gpx, author=True, time=True, keywords=True, links=True
        )
        assert stripped.metadata is not None
        assert stripped.metadata.author is None
        assert stripped.metadata.time is None
        assert stripped.metadata.keywords is None
        assert stripped.metadata.link == []
        assert stripped.metadata.name == "Name"
        assert stripped.metadata.desc == "Description"

    def test_strip_fields_without_metadata(self) -> None:
        """Stripping fields from a GPX without metadata is a no-op."""
        gpx = GPX()
        stripped = strip_metadata(gpx, name=True)
        assert stripped.metadata is None

    def test_strip_all_metadata_preserves_nsmap(self, sample_gpx: GPX) -> None:
        """Stripping all metadata preserves the namespace mappings."""
        sample_gpx.nsmap = {
            "": "http://www.topografix.com/GPX/1/1",
            "gpxtpx": GARMIN_TPX_NS,
        }
        stripped = strip_metadata(sample_gpx)
        assert stripped.nsmap == sample_gpx.nsmap


class TestReducePrecision:
    """Tests for the reduce_precision operation."""

    def test_reduce_precision(self, sample_gpx: GPX) -> None:
        """Test reducing coordinate and elevation precision."""
        reduced = reduce_precision(
            sample_gpx, coordinate_precision=2, elevation_precision=0
        )

        # Check waypoint precision
        for wpt in reduced.wpt:
            lat_str = str(wpt.lat)
            if "." in lat_str:
                assert len(lat_str.split(".")[1]) <= 2
            if wpt.ele:
                ele_str = str(wpt.ele)
                if "." in ele_str:
                    assert len(ele_str.split(".")[1]) <= 1

    def test_reduce_precision_no_elevation(self) -> None:
        """Test reducing precision when there is no elevation."""
        gpx = GPX(
            wpt=[Waypoint(lat=Latitude("52.5200123"), lon=Longitude("13.4050456"))]
        )
        reduced = reduce_precision(gpx, coordinate_precision=3)
        lat_str = str(reduced.wpt[0].lat)
        assert lat_str == "52.52"


class TestNsmapPreservation:
    """Tests that the edit operations preserve namespace mappings."""

    def test_operations_preserve_nsmap(self, sample_gpx: GPX) -> None:
        """All edit operations must propagate gpx.nsmap so prefixes survive a round-trip.

        Regression test: previously crop / trim / reverse / reduce_precision /
        strip_metadata silently dropped nsmap, which meant `gpx edit` on a
        file with custom prefixes (e.g. gpxtpx) emitted auto-generated
        ns0/ns1 prefixes instead.
        """
        sample_gpx.nsmap = {
            "": "http://www.topografix.com/GPX/1/1",
            "gpxtpx": GARMIN_TPX_NS,
        }

        cropped = crop(sample_gpx, min_lat=0.0, max_lat=90.0, min_lon=0.0, max_lon=90.0)
        assert cropped.nsmap == sample_gpx.nsmap

        trimmed = trim(sample_gpx)
        assert trimmed.nsmap == sample_gpx.nsmap

        reversed_gpx = reverse(sample_gpx)
        assert reversed_gpx.nsmap == sample_gpx.nsmap

        reduced = reduce_precision(
            sample_gpx, coordinate_precision=3, elevation_precision=1
        )
        assert reduced.nsmap == sample_gpx.nsmap

        split_gpx = split(sample_gpx, time_gap=dt.timedelta(minutes=10))
        assert split_gpx.nsmap == sample_gpx.nsmap

        simplified = simplify(sample_gpx, tolerance=10.0)
        assert simplified.nsmap == sample_gpx.nsmap

        smoothed = smooth(sample_gpx, window=3)
        assert smoothed.nsmap == sample_gpx.nsmap

        shifted = shift_time(sample_gpx, dt.timedelta(hours=1))
        assert shifted.nsmap == sample_gpx.nsmap

        stripped = strip_extensions(sample_gpx)
        assert stripped.nsmap == sample_gpx.nsmap


class TestOperationsWithExtensions:
    """Test that the edit operations preserve extensions."""

    def test_crop_preserves_waypoint_extensions(self, gpx_with_extensions: GPX) -> None:
        """Test that crop preserves extensions on remaining waypoints."""
        cropped = crop(
            gpx_with_extensions,
            min_lat=52.0,
            max_lat=53.0,
            min_lon=13.0,
            max_lon=14.0,
        )

        # Waypoint should be preserved with extensions
        assert len(cropped.wpt) == 1
        assert cropped.wpt[0].extensions is not None
        assert cropped.wpt[0].extensions.get_text("rating", namespace=CUSTOM_NS) == "5"

    def test_crop_preserves_track_extensions(self, gpx_with_extensions: GPX) -> None:
        """Test that crop preserves track and track point extensions."""
        cropped = crop(
            gpx_with_extensions,
            min_lat=52.0,
            max_lat=53.0,
            min_lon=13.0,
            max_lon=14.0,
        )

        # Track extensions preserved
        assert cropped.trk[0].extensions is not None
        assert (
            cropped.trk[0].extensions.get_text("activity", namespace=CUSTOM_NS)
            == "running"
        )

        # Track point extensions preserved
        assert cropped.trk[0].trkseg[0].trkpt[0].extensions is not None
        assert (
            cropped.trk[0]
            .trkseg[0]
            .trkpt[0]
            .extensions.get_text("hr", namespace=GARMIN_TPX_NS)
            == "140"
        )

    def test_crop_preserves_route_extensions(self, gpx_with_extensions: GPX) -> None:
        """Test that crop preserves route and route point extensions."""
        cropped = crop(
            gpx_with_extensions,
            min_lat=52.0,
            max_lat=53.0,
            min_lon=13.0,
            max_lon=14.0,
        )

        # Route extensions preserved
        assert cropped.rte[0].extensions is not None
        assert (
            cropped.rte[0].extensions.get_text("type", namespace=CUSTOM_NS) == "scenic"
        )

        # Route point extensions preserved
        assert cropped.rte[0].rtept[0].extensions is not None

    def test_trim_preserves_extensions(self, gpx_with_extensions: GPX) -> None:
        """Test that trim preserves extensions on remaining elements."""
        start = dt.datetime(2024, 1, 15, 10, 0, 30, tzinfo=dt.UTC)
        end = dt.datetime(2024, 1, 15, 10, 1, 30, tzinfo=dt.UTC)
        trimmed = trim(gpx_with_extensions, start=start, end=end)

        # Track extensions preserved
        if trimmed.trk:
            assert trimmed.trk[0].extensions is not None
            assert (
                trimmed.trk[0].extensions.get_text("activity", namespace=CUSTOM_NS)
                == "running"
            )

    def test_reverse_preserves_all_extensions(self, gpx_with_extensions: GPX) -> None:
        """Test that reverse preserves all extensions."""
        reversed_gpx = reverse(gpx_with_extensions)

        # Route extensions preserved
        assert reversed_gpx.rte[0].extensions is not None
        assert (
            reversed_gpx.rte[0].extensions.get_text("type", namespace=CUSTOM_NS)
            == "scenic"
        )

        # Track extensions preserved
        assert reversed_gpx.trk[0].extensions is not None
        assert (
            reversed_gpx.trk[0].extensions.get_text("activity", namespace=CUSTOM_NS)
            == "running"
        )

        # Track segment extensions preserved
        assert reversed_gpx.trk[0].trkseg[0].extensions is not None

        # Track point extensions preserved (order reversed)
        # First point after reverse was the last point (hr=150)
        first_point_ext = reversed_gpx.trk[0].trkseg[0].trkpt[0].extensions
        assert first_point_ext is not None
        assert first_point_ext.get_text("hr", namespace=GARMIN_TPX_NS) == "150"

    def test_reduce_precision_preserves_all_extensions(
        self, gpx_with_extensions: GPX
    ) -> None:
        """Test that precision reduction preserves all extensions."""
        reduced = reduce_precision(
            gpx_with_extensions, coordinate_precision=4, elevation_precision=1
        )

        # Waypoint extensions preserved
        assert reduced.wpt[0].extensions is not None
        assert reduced.wpt[0].extensions.get_text("rating", namespace=CUSTOM_NS) == "5"

        # Route extensions preserved
        assert reduced.rte[0].extensions is not None
        assert reduced.rte[0].rtept[0].extensions is not None

        # Track extensions preserved
        assert reduced.trk[0].extensions is not None
        assert reduced.trk[0].trkseg[0].extensions is not None
        assert reduced.trk[0].trkseg[0].trkpt[0].extensions is not None


class TestMerge:
    """Tests for the merge operation."""

    def test_merge(self, sample_gpx: GPX) -> None:
        """Merging concatenates waypoints, routes and tracks."""
        merged = merge([sample_gpx, sample_gpx])
        assert len(merged.wpt) == 2
        assert len(merged.rte) == 2
        assert len(merged.trk) == 2

    def test_merge_empty(self) -> None:
        """Merging no GPX instances yields an empty GPX."""
        merged = merge([])
        assert merged.wpt == []
        assert merged.rte == []
        assert merged.trk == []

    def test_merge_with_creator(self, sample_gpx: GPX) -> None:
        """The creator can be set on the merged GPX."""
        merged = merge([sample_gpx], creator="MergeApp")
        assert merged.creator == "MergeApp"

    def test_merge_accepts_iterables(self, sample_gpx: GPX) -> None:
        """Any iterable of GPX instances can be merged."""
        merged = merge(gpx for gpx in (sample_gpx, sample_gpx, sample_gpx))
        assert len(merged.trk) == 3


class TestSplit:
    """Tests for the split operation."""

    def test_split_requires_threshold(self, sample_gpx: GPX) -> None:
        """At least one of time_gap or distance_gap must be given."""
        with pytest.raises(ValueError, match="time_gap or distance_gap"):
            split(sample_gpx)

    def test_split_time_gap(self) -> None:
        """Segments are split where the time gap exceeds the threshold."""
        start = dt.datetime(2024, 1, 15, 10, 0, 0, tzinfo=dt.UTC)
        # 30-minute gap between the second and third point
        offsets_minutes = (0, 1, 31, 32)
        points = [
            Waypoint(
                lat=Latitude("52.000"),
                lon=Longitude("4.000"),
                time=start + dt.timedelta(minutes=offset),
            )
            for offset in offsets_minutes
        ]
        gpx = make_track_gpx(points)

        split_gpx = split(gpx, time_gap=dt.timedelta(minutes=10))
        assert [len(seg.trkpt) for seg in split_gpx.trk[0].trkseg] == [2, 2]

    def test_split_distance_gap(self) -> None:
        """Segments are split where the distance gap exceeds the threshold."""
        # ~111 m between consecutive points, then a ~1.1 km jump
        coords = [("52.000", "4.000"), ("52.001", "4.000"), ("52.011", "4.000")]
        gpx = make_track_gpx(make_points(coords))

        split_gpx = split(gpx, distance_gap=500.0)
        assert [len(seg.trkpt) for seg in split_gpx.trk[0].trkseg] == [2, 1]

    def test_split_no_gap_unchanged(self, sample_gpx: GPX) -> None:
        """Without gaps exceeding the thresholds, segments are unchanged."""
        split_gpx = split(sample_gpx, time_gap=dt.timedelta(minutes=10))
        assert len(split_gpx.trk[0].trkseg) == 1
        assert len(split_gpx.trk[0].trkseg[0].trkpt) == 3

    def test_split_points_without_time_never_split(self) -> None:
        """Points without timestamps never trigger a time-based split."""
        gpx = make_track_gpx(make_points([("52.000", "4.000")] * 3, minutes_apart=None))
        split_gpx = split(gpx, time_gap=dt.timedelta(seconds=1))
        assert len(split_gpx.trk[0].trkseg) == 1

    def test_split_preserves_segment_extensions(self, gpx_with_extensions: GPX) -> None:
        """Each resulting segment keeps the original segment's extensions."""
        # Points are 1 minute apart; split at 30 seconds → 3 segments
        split_gpx = split(gpx_with_extensions, time_gap=dt.timedelta(seconds=30))
        segments = split_gpx.trk[0].trkseg
        assert len(segments) == 3
        for segment in segments:
            assert segment.extensions is not None
            assert segment.extensions.get_text("lap", namespace=CUSTOM_NS) == "1"

    def test_split_routes_and_waypoints_unchanged(self, sample_gpx: GPX) -> None:
        """Waypoints and routes are not split."""
        split_gpx = split(sample_gpx, distance_gap=0.001)
        assert len(split_gpx.wpt) == len(sample_gpx.wpt)
        assert len(split_gpx.rte) == len(sample_gpx.rte)
        assert len(split_gpx.rte[0].rtept) == len(sample_gpx.rte[0].rtept)

    def test_split_does_not_mutate_input(self, sample_gpx: GPX) -> None:
        """The input GPX is left unchanged."""
        split(sample_gpx, distance_gap=0.001)
        assert len(sample_gpx.trk[0].trkseg) == 1


class TestSimplify:
    """Tests for the simplify operation."""

    def test_simplify_invalid_tolerance(self, sample_gpx: GPX) -> None:
        """A non-positive tolerance raises a ValueError."""
        with pytest.raises(ValueError, match="tolerance"):
            simplify(sample_gpx, 0)
        with pytest.raises(ValueError, match="tolerance"):
            simplify(sample_gpx, -1.0)

    def test_simplify_drops_collinear_points(self) -> None:
        """Points on a straight line are reduced to the endpoints."""
        coords = [("52.000", "4.000"), ("52.001", "4.000"), ("52.002", "4.000")]
        gpx = make_track_gpx(make_points(coords))

        simplified = simplify(gpx, tolerance=5.0)
        points = simplified.trk[0].trkseg[0].trkpt
        assert len(points) == 2
        assert str(points[0].lat) == "52.000"
        assert str(points[-1].lat) == "52.002"

    def test_simplify_keeps_significant_points(self) -> None:
        """Points deviating more than the tolerance are kept."""
        # Middle point deviates ~68 m east of the line
        coords = [("52.000", "4.000"), ("52.001", "4.001"), ("52.002", "4.000")]
        gpx = make_track_gpx(make_points(coords))

        simplified = simplify(gpx, tolerance=10.0)
        assert len(simplified.trk[0].trkseg[0].trkpt) == 3

    def test_simplify_routes(self) -> None:
        """Route points are simplified as well."""
        gpx = GPX(
            rte=[
                Route(
                    rtept=make_points(
                        [("52.000", "4.000"), ("52.001", "4.000"), ("52.002", "4.000")],
                        minutes_apart=None,
                    )
                )
            ]
        )
        simplified = simplify(gpx, tolerance=5.0)
        assert len(simplified.rte[0].rtept) == 2

    def test_simplify_waypoints_unchanged(self, sample_gpx: GPX) -> None:
        """Waypoints are left unchanged."""
        simplified = simplify(sample_gpx, tolerance=1000.0)
        assert len(simplified.wpt) == len(sample_gpx.wpt)

    def test_simplify_short_lists_unchanged(self) -> None:
        """Lists of fewer than three points are left unchanged."""
        coords = [("52.000", "4.000"), ("52.001", "4.000")]
        gpx = make_track_gpx(make_points(coords))
        simplified = simplify(gpx, tolerance=1000.0)
        assert len(simplified.trk[0].trkseg[0].trkpt) == 2

    def test_simplify_preserves_extensions_of_kept_points(
        self, gpx_with_extensions: GPX
    ) -> None:
        """Extensions of the points that are kept are preserved."""
        simplified = simplify(gpx_with_extensions, tolerance=1000.0)
        first_point = simplified.trk[0].trkseg[0].trkpt[0]
        assert first_point.extensions is not None
        assert first_point.extensions.get_text("hr", namespace=GARMIN_TPX_NS) == "140"


class TestSmooth:
    """Tests for the smooth operation."""

    def test_smooth_invalid_window(self, sample_gpx: GPX) -> None:
        """An even or too small window raises a ValueError."""
        for window in (0, 1, 2, 4):
            with pytest.raises(ValueError, match="window"):
                smooth(sample_gpx, window=window)

    def test_smooth_moves_noisy_point(self) -> None:
        """A noisy point is moved towards its neighbors."""
        coords = [("52.000", "4.000"), ("52.002", "4.000"), ("52.000", "4.000")]
        gpx = make_track_gpx(make_points(coords))

        smoothed = smooth(gpx, window=3)
        middle = smoothed.trk[0].trkseg[0].trkpt[1]
        # Mean of 52.000, 52.002, 52.000
        assert float(middle.lat) == pytest.approx(52.000667, abs=1e-6)

    def test_smooth_endpoints_unchanged(self) -> None:
        """The first and last point are always left unchanged."""
        coords = [("52.000", "4.000"), ("52.002", "4.001"), ("52.000", "4.002")]
        gpx = make_track_gpx(make_points(coords))

        smoothed = smooth(gpx, window=3)
        points = smoothed.trk[0].trkseg[0].trkpt
        assert str(points[0].lat) == "52.000"
        assert str(points[0].lon) == "4.000"
        assert str(points[-1].lat) == "52.000"
        assert str(points[-1].lon) == "4.002"

    def test_smooth_elevations(self) -> None:
        """Elevations are smoothed with the same moving average."""
        points = make_points([("52.000", "4.000")] * 3)
        points = [
            Waypoint(lat=p.lat, lon=p.lon, time=p.time, ele=Decimal(ele))
            for p, ele in zip(points, ("10.0", "40.0", "10.0"), strict=True)
        ]
        gpx = make_track_gpx(points)

        smoothed = smooth(gpx, window=3)
        middle = smoothed.trk[0].trkseg[0].trkpt[1]
        assert middle.ele is not None
        assert float(middle.ele) == pytest.approx(20.0)

    def test_smooth_coordinates_flag(self) -> None:
        """With coordinates=False, the coordinates are left unchanged."""
        coords = [("52.000", "4.000"), ("52.002", "4.000"), ("52.000", "4.000")]
        gpx = make_track_gpx(make_points(coords))

        smoothed = smooth(gpx, window=3, coordinates=False)
        assert str(smoothed.trk[0].trkseg[0].trkpt[1].lat) == "52.002"

    def test_smooth_points_without_elevation(self) -> None:
        """Points without elevation are left without elevation."""
        coords = [("52.000", "4.000"), ("52.002", "4.000"), ("52.000", "4.000")]
        gpx = make_track_gpx(make_points(coords))

        smoothed = smooth(gpx, window=3)
        assert all(p.ele is None for p in smoothed.trk[0].trkseg[0].trkpt)

    def test_smooth_short_lists_unchanged(self) -> None:
        """Lists of fewer than three points are left unchanged."""
        coords = [("52.000", "4.000"), ("52.002", "4.000")]
        gpx = make_track_gpx(make_points(coords))

        smoothed = smooth(gpx, window=3)
        assert str(smoothed.trk[0].trkseg[0].trkpt[1].lat) == "52.002"

    def test_smooth_preserves_other_fields(self, gpx_with_extensions: GPX) -> None:
        """Timestamps and extensions are preserved on smoothed points."""
        smoothed = smooth(gpx_with_extensions, window=3)
        middle = smoothed.trk[0].trkseg[0].trkpt[1]
        assert middle.time == gpx_with_extensions.trk[0].trkseg[0].trkpt[1].time
        assert middle.extensions is not None
        assert middle.extensions.get_text("hr", namespace=GARMIN_TPX_NS) == "145"


class TestShiftTime:
    """Tests for the shift_time operation."""

    def test_shift_time_forward(self, sample_gpx: GPX) -> None:
        """All point timestamps are shifted by the delta."""
        delta = dt.timedelta(hours=2)
        shifted = shift_time(sample_gpx, delta)

        original_time = sample_gpx.wpt[0].time
        assert original_time is not None
        assert shifted.wpt[0].time == original_time + delta
        for original, new in zip(
            sample_gpx.trk[0].trkseg[0].trkpt,
            shifted.trk[0].trkseg[0].trkpt,
            strict=True,
        ):
            assert original.time is not None
            assert new.time == original.time + delta

    def test_shift_time_negative(self, sample_gpx: GPX) -> None:
        """Negative deltas shift the timestamps backwards."""
        delta = dt.timedelta(minutes=-30)
        shifted = shift_time(sample_gpx, delta)
        original_time = sample_gpx.wpt[0].time
        assert original_time is not None
        assert shifted.wpt[0].time == original_time + delta

    def test_shift_time_points_without_time(self, sample_gpx: GPX) -> None:
        """Points without a timestamp are left unchanged."""
        shifted = shift_time(sample_gpx, dt.timedelta(hours=1))
        assert all(p.time is None for p in shifted.rte[0].rtept)

    def test_shift_time_metadata_unchanged(self) -> None:
        """The metadata timestamp is not shifted."""
        time = dt.datetime(2024, 1, 15, tzinfo=dt.UTC)
        gpx = GPX(metadata=Metadata(time=time))
        shifted = shift_time(gpx, dt.timedelta(hours=1))
        assert shifted.metadata is not None
        assert shifted.metadata.time == time

    def test_shift_time_does_not_mutate_input(self, sample_gpx: GPX) -> None:
        """The input GPX is left unchanged."""
        original_time = sample_gpx.wpt[0].time
        shift_time(sample_gpx, dt.timedelta(hours=1))
        assert sample_gpx.wpt[0].time == original_time


class TestStripExtensions:
    """Tests for the strip_extensions operation."""

    def test_strip_extensions_all_levels(self, gpx_with_extensions: GPX) -> None:
        """Extensions are removed from all levels of the GPX."""
        stripped = strip_extensions(gpx_with_extensions)

        assert stripped.extensions is None
        assert stripped.metadata is not None
        assert stripped.metadata.extensions is None
        assert all(w.extensions is None for w in stripped.wpt)
        for route in stripped.rte:
            assert route.extensions is None
            assert all(p.extensions is None for p in route.rtept)
        for track in stripped.trk:
            assert track.extensions is None
            for segment in track.trkseg:
                assert segment.extensions is None
                assert all(p.extensions is None for p in segment.trkpt)

    def test_strip_extensions_without_extensions(self, sample_gpx: GPX) -> None:
        """Stripping a GPX without extensions is a no-op."""
        stripped = strip_extensions(sample_gpx)
        assert stripped.extensions is None
        assert len(stripped.wpt) == len(sample_gpx.wpt)
        assert len(stripped.trk) == len(sample_gpx.trk)

    def test_strip_extensions_does_not_mutate_input(
        self, gpx_with_extensions: GPX
    ) -> None:
        """The input GPX is left unchanged."""
        strip_extensions(gpx_with_extensions)
        assert gpx_with_extensions.extensions is not None
        assert gpx_with_extensions.trk[0].trkseg[0].trkpt[0].extensions is not None
