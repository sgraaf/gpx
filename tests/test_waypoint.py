import json
from datetime import datetime
from decimal import Decimal

from gpx.waypoint import Waypoint


def test_geo_interface():
    waypoint = Waypoint()
    waypoint.lat = Decimal("48.2081743")
    waypoint.lon = Decimal("16.3738189")
    waypoint.ele = Decimal("151.0")
    waypoint.time = datetime(2023, 10, 1, 12, 0, 0)
    waypoint.magvar = Decimal("0.0")
    waypoint.geoidheight = Decimal("0.0")
    waypoint.name = "Test Waypoint"
    waypoint.cmt = "Test Comment"
    waypoint.desc = "Test Description"
    waypoint.src = "Test Source"
    waypoint.sym = "Test Symbol"
    waypoint.type = "Test Type"
    waypoint.fix = "3d"
    waypoint.sat = 5
    waypoint.hdop = Decimal("0.9")
    waypoint.vdop = Decimal("1.1")
    waypoint.pdop = Decimal("1.5")
    waypoint.ageofdgpsdata = Decimal("0.0")
    waypoint.dgpsid = "0000"
    waypoint.links = {}

    geo_interface = waypoint.__geo_interface__
    geo_interface_json = json.dumps(geo_interface, default=str)

    expected_json = json.dumps(
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [16.3738189, 48.2081743, 151.0],
            },
            "properties": {
                "time": "2023-10-01T12:00:00",
                "magvar": 0.0,
                "geoidheight": 0.0,
                "name": "Test Waypoint",
                "cmt": "Test Comment",
                "desc": "Test Description",
                "src": "Test Source",
                "links": {},
                "sym": "Test Symbol",
                "type": "Test Type",
                "fix": "3d",
                "sat": 5,
                "hdop": 0.9,
                "vdop": 1.1,
                "pdop": 1.5,
                "ageofdgpsdata": 0.0,
                "dgpsid": "0000",
            },
        },
        default=str,
    )

    assert geo_interface_json == expected_json
