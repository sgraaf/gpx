import json
from datetime import datetime
from decimal import Decimal

from gpx.track import Track
from gpx.track_segment import TrackSegment
from gpx.types import Latitude, Longitude
from gpx.waypoint import Waypoint


def test_geo_interface():
    track = Track()
    track.name = "Test Track"
    track.cmt = "Test Comment"
    track.desc = "Test Description"
    track.src = "Test Source"
    track.number = 1
    track.type = "Test Type"
    track.links = {}

    segment = TrackSegment()
    point1 = Waypoint()
    point1.lat = Latitude("48.2081743")
    point1.lon = Longitude("16.3739189")
    point1.ele = Decimal("151.0")
    point1.time = datetime(2023, 10, 1, 12, 0, 0)

    point2 = Waypoint()
    point2.lat = Latitude("48.2081744")
    point2.lon = Longitude("16.3738190")
    point2.ele = Decimal("152.0")
    point2.time = datetime(2023, 10, 1, 12, 5, 0)

    segment.trkpts = [point1, point2]
    track.trksegs = [segment]

    geo_interface = track.__geo_interface__
    geo_interface_json = json.dumps(geo_interface, default=str)

    expected_geo_interface = {
        "type": "Feature",
        "geometry": {
            "type": "MultiLineString",
            "coordinates": [
                [
                    [16.3739189, 48.2081743, 151.0],
                    [16.3738190, 48.2081744, 152.0],
                ]
            ],
        },
        "properties": {
            "name": "Test Track",
            "cmt": "Test Comment",
            "desc": "Test Description",
            "src": "Test Source",
            "links": {},
            "number": 1,
            "type": "Test Type",
            # "total_distance": track.total_distance,
            # "total_duration": track.total_duration.total_seconds(),
            # "moving_duration": track.moving_duration.total_seconds(),
            # "avg_speed": track.avg_speed,
            # "avg_moving_speed": track.avg_moving_speed,
            # "max_speed": track.max_speed,
            # "min_speed": track.min_speed,
            # "speed_profile": [
            #     [timestamp.isoformat(), speed]
            #     for (timestamp, speed) in track.speed_profile
            # ],
            # "avg_elevation": float(track.avg_elevation),
            # "max_elevation": float(track.max_elevation),
            # "min_elevation": float(track.min_elevation),
            # "diff_elevation": float(track.diff_elevation),
            # "total_ascent": float(track.total_ascent),
            # "total_descent": float(track.total_descent),
            # "elevation_profile": [
            #     [distance, float(elevation)]
            #     for (distance, elevation) in track.elevation_profile
            # ],
        },
    }
    expected_json = json.dumps(
        expected_geo_interface,
        default=str,
    )

    assert geo_interface_json == expected_json
