import json
from datetime import datetime
from decimal import Decimal

from gpx.types import Degrees, DGPSStation, Fix, Latitude, Longitude
from gpx.waypoint import Waypoint


def test_geo_interface():
    waypoint = Waypoint()
    waypoint.lat = Latitude(48.2082)
    waypoint.lon = Longitude(16.3738)
    waypoint.ele = Decimal("180.0")
    waypoint.time = datetime(2023, 10, 1, 12, 0, 0)
    waypoint.magvar = Degrees(1.2)
    waypoint.geoidheight = Decimal("45.0")
    waypoint.name = "Stephansplatz"
    waypoint.cmt = "Start of walk"
    waypoint.desc = "Starting point at Stephansplatz, Vienna"
    waypoint.src = "Field GPS"
    waypoint.sym = "Walking"
    waypoint.type = "walk"
    waypoint.fix = Fix("3d")
    waypoint.sat = 10
    waypoint.hdop = Decimal("2.5")
    waypoint.vdop = Decimal("3.0")
    waypoint.pdop = Decimal("4.0")
    waypoint.ageofdgpsdata = Decimal("0.2")
    waypoint.dgpsid = DGPSStation(23)

    geo_interface = waypoint.__geo_interface__
    geo_interface_json = json.dumps(geo_interface, default=str)

    expected_json = json.dumps(
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [16.3738, 48.2082, 180.0],
            },
            "properties": {
                "time": "2023-10-01T12:00:00",
                "magvar": 1.2,
                "geoidheight": 45.0,
                "name": "Stephansplatz",
                "cmt": "Start of walk",
                "desc": "Starting point at Stephansplatz, Vienna",
                "src": "Field GPS",
                "links": {},
                "sym": "Walking",
                "type": "walk",
                "fix": "3d",
                "sat": 10,
                "hdop": 2.5,
                "vdop": 3.0,
                "pdop": 4.0,
                "ageofdgpsdata": 0.2,
                "dgpsid": "23",
            },
        },
        default=str,
    )

    assert geo_interface_json == expected_json
