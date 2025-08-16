import json
from datetime import datetime
from decimal import Decimal

from gpx.track_segment import TrackSegment
from gpx.types import Latitude, Longitude
from gpx.waypoint import Waypoint


def test_geo_interface():
    segment = TrackSegment()

    point1 = Waypoint()
    point1.lat = Latitude("48.2081743")
    point1.lon = Longitude("16.3738189")
    point1.ele = Decimal("151.0")
    point1.time = datetime(2023, 10, 1, 12, 0, 0)

    point2 = Waypoint()
    point2.lat = Latitude("48.2081744")
    point2.lon = Longitude("16.3738190")
    point2.ele = Decimal("152.0")
    point2.time = datetime(2023, 10, 1, 12, 5, 0)

    segment.trkpts.extend([point1, point2])

    geo_interface = segment.__geo_interface__
    geo_interface_json = json.dumps(geo_interface, default=str)

    expected_json = json.dumps(
        {
            "type": "LineString",
            "bbox": [
                16.3738189,
                48.2081743,
                16.373819,
                48.2081744,
            ],
            "coordinates": [
                [16.3738189, 48.2081743, 151.0],
                [16.3738190, 48.2081744, 152.0],
            ],
        },
        default=str,
    )

    assert geo_interface_json == expected_json
