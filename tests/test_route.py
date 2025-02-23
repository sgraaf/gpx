import json
from datetime import datetime
from decimal import Decimal

from gpx.route import Route
from gpx.waypoint import Waypoint


def test_geo_interface():
    route = Route()
    route.name = "Test Route"
    route.cmt = "Test Comment"
    route.desc = "Test Description"
    route.src = "Test Source"
    route.number = 1
    route.type = "Test Type"
    route.links = []

    point1 = Waypoint()
    point1.lat = Decimal("48.2081743")
    point1.lon = Decimal("16.3738189")
    point1.ele = Decimal("151.0")
    point1.time = datetime(2023, 10, 1, 12, 0, 0)

    point2 = Waypoint()
    point2.lat = Decimal("48.2081744")
    point2.lon = Decimal("16.3738190")
    point2.ele = Decimal("152.0")
    point2.time = datetime(2023, 10, 1, 12, 5, 0)

    route.rtepts = [point1, point2]

    geo_interface = route.__geo_interface__
    geo_interface_json = json.dumps(geo_interface, default=str)

    expected_json = json.dumps(
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [16.3738189, 48.2081743, 151.0],
                    [16.3738190, 48.2081744, 152.0],
                ],
            },
            "properties": {
                "name": "Test Route",
                "cmt": "Test Comment",
                "desc": "Test Description",
                "src": "Test Source",
                "links": [],
                "number": 1,
                "type": "Test Type",
            },
        },
        default=str,
    )

    assert geo_interface_json == expected_json
