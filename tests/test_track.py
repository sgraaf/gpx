from datetime import datetime
from decimal import Decimal

import pytest

from gpx.track import Track
from gpx.track_segment import TrackSegment
from gpx.types import Latitude, Longitude
from gpx.waypoint import Waypoint


@pytest.mark.parametrize(
    "track_name,track_cmt,track_desc,track_src,track_number,track_type,points,expected_geo_interface",
    [
        # Test case 1: Walking track with movement
        (
            "Morning Walk",
            "Daily walking exercise",
            "A pleasant morning walk through the neighborhood",
            "GPS Watch",
            1,
            "walking",
            [
                (
                    Latitude("48.2081743"),
                    Longitude("16.3739189"),
                    Decimal("151.0"),
                    datetime(2023, 10, 1, 8, 0, 0),
                ),
                (
                    Latitude("48.2086243"),
                    Longitude("16.3739289"),
                    Decimal("151.5"),
                    datetime(2023, 10, 1, 8, 2, 0),
                ),
                (
                    Latitude("48.2090743"),
                    Longitude("16.3739389"),
                    Decimal("152.0"),
                    datetime(2023, 10, 1, 8, 4, 0),
                ),
                (
                    Latitude("48.2091143"),
                    Longitude("16.3744389"),
                    Decimal("152.2"),
                    datetime(2023, 10, 1, 8, 6, 0),
                ),
                (
                    Latitude("48.2091543"),
                    Longitude("16.3749389"),
                    Decimal("152.8"),
                    datetime(2023, 10, 1, 8, 8, 0),
                ),
                (
                    Latitude("48.2087043"),
                    Longitude("16.3749889"),
                    Decimal("153.1"),
                    datetime(2023, 10, 1, 8, 10, 0),
                ),
                (
                    Latitude("48.2082543"),
                    Longitude("16.3750389"),
                    Decimal("152.5"),
                    datetime(2023, 10, 1, 8, 12, 0),
                ),
                (
                    Latitude("48.2082143"),
                    Longitude("16.3745389"),
                    Decimal("152.0"),
                    datetime(2023, 10, 1, 8, 14, 0),
                ),
                (
                    Latitude("48.2081843"),
                    Longitude("16.3740189"),
                    Decimal("151.2"),
                    datetime(2023, 10, 1, 8, 15, 0),
                ),
            ],
            {
                "type": "Feature",
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": [
                        [
                            [16.3739189, 48.2081743, 151.0],
                            [16.3739289, 48.2086243, 151.5],
                            [16.3739389, 48.2090743, 152.0],
                            [16.3744389, 48.2091143, 152.2],
                            [16.3749389, 48.2091543, 152.8],
                            [16.3749889, 48.2087043, 153.1],
                            [16.3750389, 48.2082543, 152.5],
                            [16.3745389, 48.2082143, 152.0],
                            [16.3740189, 48.2081843, 151.2],
                        ]
                    ],
                },
                "bbox": [
                    16.3739189,
                    48.2081743,
                    16.3750389,
                    48.2091543,
                ],
                "properties": {
                    "name": "Morning Walk",
                    "cmt": "Daily walking exercise",
                    "desc": "A pleasant morning walk through the neighborhood",
                    "src": "GPS Watch",
                    "links": {},
                    "number": 1,
                    "type": "walking",
                    "total_distance": 351.4582983708985,
                    "total_duration": 900.0,
                    "moving_duration": 900.0,
                    "avg_speed": 0.39050922041210945,
                    "avg_moving_speed": 0.39050922041210945,
                    "max_speed": 0.6453516101816278,
                    "min_speed": 0.3113227030279154,
                    "speed_profile": [
                        ["2023-10-01T08:00:00", 0.41749386499092545],
                        ["2023-10-01T08:02:00", 0.4174938641983193],
                        ["2023-10-01T08:04:00", 0.3113229427384215],
                        ["2023-10-01T08:06:00", 0.3113227030279154],
                        ["2023-10-01T08:08:00", 0.4185909282663682],
                        ["2023-10-01T08:10:00", 0.4185909483170693],
                        ["2023-10-01T08:12:00", 0.31132809646098775],
                        ["2023-10-01T08:14:00", 0.6453516101816278],
                    ],
                    "avg_elevation": 152.03333333333333,
                    "max_elevation": 153.1,
                    "min_elevation": 151.0,
                    "diff_elevation": 2.1,
                    "total_ascent": 2.1,
                    "total_descent": 1.9,
                    "elevation_profile": [
                        [0.0, 151.0],
                        [50.09926379891105, 151.5],
                        [100.19852750270937, 152.0],
                        [137.55728063131994, 152.2],
                        [174.91600499466978, 152.8],
                        [225.14691638663396, 153.1],
                        [275.3778301846823, 152.5],
                        [312.7372017600008, 152.0],
                        [351.4582983708985, 151.2],
                    ],
                },
            },
        ),
        # Test case 2: Stationary track with no movement
        (
            "Rest Stop",
            "Stationary break",
            "Taking a break at the same location",
            "GPS Watch",
            2,
            "stationary",
            [
                (
                    Latitude("48.2081743"),
                    Longitude("16.3739189"),
                    Decimal("151.0"),
                    datetime(2023, 10, 1, 9, 0, 0),
                ),
                (
                    Latitude("48.2081743"),
                    Longitude("16.3739189"),
                    Decimal("151.0"),
                    datetime(2023, 10, 1, 9, 5, 0),
                ),
                (
                    Latitude("48.2081743"),
                    Longitude("16.3739189"),
                    Decimal("151.0"),
                    datetime(2023, 10, 1, 9, 10, 0),
                ),
            ],
            {
                "type": "Feature",
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": [
                        [
                            [16.3739189, 48.2081743, 151.0],
                            [16.3739189, 48.2081743, 151.0],
                            [16.3739189, 48.2081743, 151.0],
                        ]
                    ],
                },
                "bbox": [
                    16.3739189,
                    48.2081743,
                    16.3739189,
                    48.2081743,
                ],
                "properties": {
                    "name": "Rest Stop",
                    "cmt": "Stationary break",
                    "desc": "Taking a break at the same location",
                    "src": "GPS Watch",
                    "links": {},
                    "number": 2,
                    "type": "stationary",
                    "total_distance": 0.0,
                    "total_duration": 600.0,
                    "moving_duration": 0.0,
                    "avg_speed": 0.0,
                    "avg_moving_speed": 0.0,
                    "max_speed": 0.0,
                    "min_speed": 0.0,
                    "speed_profile": [
                        ["2023-10-01T09:00:00", 0.0],
                        ["2023-10-01T09:05:00", 0.0],
                    ],
                    "avg_elevation": 151.0,
                    "max_elevation": 151.0,
                    "min_elevation": 151.0,
                    "diff_elevation": 0.0,
                    "total_ascent": 0.0,
                    "total_descent": 0.0,
                    "elevation_profile": [
                        [0.0, 151.0],
                        [0.0, 151.0],
                        [0.0, 151.0],
                    ],
                },
            },
        ),
        # Test case 3: Edge case - single point (no duration, no distance)
        (
            "Single Point",
            "Just one point",
            "A track with only one point",
            "GPS Watch",
            3,
            "point",
            [
                (
                    Latitude("48.2081743"),
                    Longitude("16.3739189"),
                    Decimal("151.0"),
                    datetime(2023, 10, 1, 10, 0, 0),
                ),
            ],
            {
                "type": "Feature",
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": [
                        [
                            [16.3739189, 48.2081743, 151.0],
                        ]
                    ],
                },
                "bbox": [
                    16.3739189,
                    48.2081743,
                    16.3739189,
                    48.2081743,
                ],
                "properties": {
                    "name": "Single Point",
                    "cmt": "Just one point",
                    "desc": "A track with only one point",
                    "src": "GPS Watch",
                    "links": {},
                    "number": 3,
                    "type": "point",
                    "total_distance": 0,
                    "total_duration": 0.0,
                    "moving_duration": 0.0,
                    "avg_speed": 0.0,
                    "avg_moving_speed": 0.0,
                    "max_speed": 0.0,
                    "min_speed": 0.0,
                    "speed_profile": [],
                    "avg_elevation": 151.0,
                    "max_elevation": 151.0,
                    "min_elevation": 151.0,
                    "diff_elevation": 0.0,
                    "total_ascent": 0.0,
                    "total_descent": 0.0,
                    "elevation_profile": [
                        [0.0, 151.0],
                    ],
                },
            },
        ),
        # Test case 4: Edge case - points with same timestamp (zero duration)
        (
            "Same Time Points",
            "Points at same time",
            "Multiple points recorded at exactly the same time",
            "GPS Watch",
            4,
            "synchronized",
            [
                (
                    Latitude("48.2081743"),
                    Longitude("16.3739189"),
                    Decimal("151.0"),
                    datetime(2023, 10, 1, 11, 0, 0),
                ),
                (
                    Latitude("48.2086243"),
                    Longitude("16.3739289"),
                    Decimal("151.5"),
                    datetime(2023, 10, 1, 11, 0, 0),  # Same timestamp
                ),
                (
                    Latitude("48.2090743"),
                    Longitude("16.3739389"),
                    Decimal("152.0"),
                    datetime(2023, 10, 1, 11, 0, 0),  # Same timestamp
                ),
            ],
            {
                "type": "Feature",
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": [
                        [
                            [16.3739189, 48.2081743, 151.0],
                            [16.3739289, 48.2086243, 151.5],
                            [16.3739389, 48.2090743, 152.0],
                        ]
                    ],
                },
                "bbox": [
                    16.3739189,
                    48.2081743,
                    16.3739389,
                    48.2090743,
                ],
                "properties": {
                    "name": "Same Time Points",
                    "cmt": "Points at same time",
                    "desc": "Multiple points recorded at exactly the same time",
                    "src": "GPS Watch",
                    "links": {},
                    "number": 4,
                    "type": "synchronized",
                    "total_distance": 100.19852750270937,
                    "total_duration": 0.0,
                    "moving_duration": 0.0,
                    "avg_speed": 0.0,
                    "avg_moving_speed": 0.0,
                    "max_speed": 0.0,
                    "min_speed": 0.0,
                    "speed_profile": [
                        ["2023-10-01T11:00:00", 0.0],
                        ["2023-10-01T11:00:00", 0.0],
                    ],
                    "avg_elevation": 151.5,
                    "max_elevation": 152.0,
                    "min_elevation": 151.0,
                    "diff_elevation": 1.0,
                    "total_ascent": 1.0,
                    "total_descent": 0.0,
                    "elevation_profile": [
                        [0.0, 151.0],
                        [50.09926379891105, 151.5],
                        [100.19852750270937, 152.0],
                    ],
                },
            },
        ),
    ],
)
def test_geo_interface(
    track_name,
    track_cmt,
    track_desc,
    track_src,
    track_number,
    track_type,
    points,
    expected_geo_interface,
):
    track = Track()
    track.name = track_name
    track.cmt = track_cmt
    track.desc = track_desc
    track.src = track_src
    track.number = track_number
    track.type = track_type

    segment = TrackSegment()

    for lat, lon, ele, time in points:
        point = Waypoint()
        point.lat = lat
        point.lon = lon
        point.ele = ele
        point.time = time
        segment.trkpts.append(point)

    track.trksegs.extend([segment])

    geo_interface = track.__geo_interface__

    assert geo_interface["type"] == expected_geo_interface["type"]
    assert geo_interface["geometry"] == expected_geo_interface["geometry"]

    if "bbox" in expected_geo_interface:
        assert "bbox" in geo_interface
        assert geo_interface["bbox"] == expected_geo_interface["bbox"]

    actual_props = geo_interface["properties"]
    expected_props = expected_geo_interface["properties"]

    for key, expected_value in expected_props.items():
        if key in actual_props:
            assert actual_props[key] == expected_value, (
                f"Property {key} mismatch: got {actual_props[key]}, expected {expected_value}"
            )

    for key in actual_props:
        if key not in expected_props:
            print(
                f"Note: Additional property {key} present in actual output: {actual_props[key]}"
            )
