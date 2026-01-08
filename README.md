<!-- start docs-include-index -->

# gpx

[![PyPI](https://img.shields.io/pypi/v/gpx)](https://img.shields.io/pypi/v/gpx)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/gpx)](https://pypi.org/project/gpx/)
[![CI](https://github.com/sgraaf/gpx/actions/workflows/ci.yml/badge.svg)](https://github.com/sgraaf/gpx/actions/workflows/ci.yml)
[![Test](https://github.com/sgraaf/gpx/actions/workflows/test.yml/badge.svg)](https://github.com/sgraaf/gpx/actions/workflows/test.yml)
[![Documentation Status](https://readthedocs.org/projects/gpx/badge/?version=latest)](https://gpx.readthedocs.io/en/latest/?badge=latest)
[![PyPI - License](https://img.shields.io/pypi/l/gpx)](https://img.shields.io/pypi/l/gpx)

*gpx* is a zero-dependency, pure Python package for reading, manipulating, writing and converting GPX (GPS Exchange Format) files.

<!-- end docs-include-index -->

## Installation

<!-- start docs-include-installation -->

*gpx* is available on [PyPI](https://pypi.org/project/gpx/). Install with [uv](https://docs.astral.sh/uv/) or your package manager of choice:

```sh
uv add gpx
```

<!-- end docs-include-installation -->

## Documentation

Check out the [*gpx* documentation](https://gpx.readthedocs.io/en/stable/) for the [User's Guide](https://gpx.readthedocs.io/en/stable/usage.html) and [API Reference](https://gpx.readthedocs.io/en/stable/api.html).

## Usage

<!-- start docs-include-usage -->

### Reading a GPX file

```python
from gpx import read_gpx

# Read GPX data from file
gpx = read_gpx("path/to/file.gpx")

# Access basic properties
print(f"Creator: {gpx.creator}")
print(f"Number of waypoints: {len(gpx.wpt)}")
print(f"Number of tracks: {len(gpx.trk)}")
print(f"Number of routes: {len(gpx.rte)}")
```

### Working with waypoints

```python
from gpx import Latitude, Longitude, Waypoint, read_gpx
from decimal import Decimal

# Read GPX data from file
gpx = read_gpx("path/to/file.gpx")

# Create a new waypoint
waypoint = Waypoint(
    lat=Latitude("52.3676"),
    lon=Longitude("4.9041"),
    name="Amsterdam",
    desc="Capital of the Netherlands",
    ele=Decimal("2.0"),
)

# Add waypoint to GPX data
gpx.wpt.append(waypoint)

# Iterate over waypoints
for idx, wpt in enumerate(gpx.wpt):
    print(f"{idx}: ({wpt.lat}, {wpt.lon})")
```

### Working with tracks and statistics

```python
from gpx import read_gpx

# Read GPX data from file
gpx = read_gpx("path/to/file.gpx")

# Access track data
for track in gpx.trk:
    print(f"Track: {track.name}")

    # Get statistics from the track
    print(f"  Total distance: {track.total_distance:.2f} meters")
    print(f"  Total duration: {track.total_duration}")
    print(f"  Average speed: {track.avg_speed:.2f} m/s")
    print(f"  Max elevation: {track.max_elevation} meters")
    print(f"  Total ascent: {track.total_ascent} meters")

    # Iterate over track segments and points
    for track_segment in track.trkseg:
        print(f"  Segment with {len(track_segment.trkpt)} points")
        for track_point in track_segment.trkpt:
            print(
                f"    Point: ({track_point.lat}, {track_point.lon}) at {track_point.time}"
            )
```

### Creating a GPX from scratch

```python
from gpx import (
    GPX,
    Latitude,
    Longitude,
    Metadata,
    Track,
    TrackSegment,
    Waypoint,
)
from datetime import datetime, timezone
from decimal import Decimal

# Create track points
track_points = []
for i in range(5):
    point = Waypoint(
        lat=Latitude(Decimal("52.0") + i * Decimal("0.01")),
        lon=Longitude(Decimal("4.0") + i * Decimal("0.01")),
        ele=Decimal("10.0") + Decimal(i) * Decimal("2.0"),
        time=datetime.now(timezone.utc),
    )
    track_points.append(point)

# Create a track with segments
track_segment = TrackSegment(trkpt=track_points)
track = Track(name="Morning Run", trkseg=[track_segment])

# Create metadata
metadata = Metadata(
    name="My GPS Track",
    desc="A sample track",
    time=datetime.now(timezone.utc),
)

# Create GPX object (creator defaults to "*gpx*")
gpx = GPX(
    creator="My Application",
    metadata=metadata,
    trk=[track],
)
```

### Writing GPX files

```python
from gpx import from_string

# Write GPX data to file
gpx.write_gpx("output.gpx")

# Convert to string
gpx_string = gpx.to_string()
print(gpx_string)

# Parse from string
gpx = from_string(gpx_string)
```

### Working with routes

```python
from gpx import Latitude, Longitude, Route, Waypoint

# Create route points (waypoints)
route_point_1 = Waypoint(
    lat=Latitude("52.3676"),
    lon=Longitude("4.9041"),
    name="Start: Amsterdam Centraal",
)

route_point_2 = Waypoint(
    lat=Latitude("52.3731"),
    lon=Longitude("4.8922"),
    name="Dam Square",
)

# Create a route
route = Route(name="City Tour", rtept=[route_point_1, route_point_2])
gpx.rte.append(route)

# Access route statistics
print(f"Route distance: {route.total_distance:.2f} meters")
```

### Working with GPX Extensions

*gpx* supports reading and writing GPX extensions from any namespace, enabling lossless round-trip handling of vendor-specific data like Garmin's `TrackPointExtension`:

```python
from gpx import read_gpx

# Define extension namespace
GARMIN_TPX = "http://www.garmin.com/xmlschemas/TrackPointExtension/v2"

# Read GPX file with extensions
gpx = read_gpx("activity.gpx")

# Access extension data from track points
for track in gpx.trk:
    for track_segment in track.trkseg:
        for track_point in track_segment.trkpt:
            if track_point.extensions:
                if (
                    hr := track_point.extensions.get_int("hr", namespace=GARMIN_TPX)
                ) is not None:
                    print(f"Heart rate: {hr} bpm")
```

Creating GPX files with extensions:

```python
import xml.etree.ElementTree as ET
from gpx import (
    Extensions,
    GPX,
    Latitude,
    Longitude,
    Track,
    TrackSegment,
    Waypoint,
)
from decimal import Decimal

# Register namespace prefix for cleaner XML output
GARMIN_TPX = "http://www.garmin.com/xmlschemas/TrackPointExtension/v2"
ET.register_namespace("gpxtpx", GARMIN_TPX)

# Create extension element
tpx = ET.Element(f"{{{GARMIN_TPX}}}TrackPointExtension")
hr = ET.SubElement(tpx, f"{{{GARMIN_TPX}}}hr")
hr.text = "145"

# Create waypoint with extensions
point = Waypoint(
    lat=Latitude("52.0"),
    lon=Longitude("4.0"),
    extensions=Extensions(elements=[tpx]),
)

# Build GPX with the point
gpx = GPX(trk=[Track(trkseg=[TrackSegment(trkpt=[point])])])
gpx.write_gpx("with_extensions.gpx")
```

### Converting to other formats

*gpx* supports converting GPX data to various formats:

```python
from gpx import GPX, read_gpx

gpx = read_gpx("path/to/file.gpx")

# Write to file formats
gpx.write_gpx("output.gpx")  # GPX file
gpx.write_geojson("output.geojson")  # GeoJSON file
gpx.write_kml("output.kml")  # KML file (Google Earth)

# Convert to data formats (strings/bytes)
wkt_string = gpx.to_wkt()  # Well-Known Text
wkb_bytes = gpx.to_wkb()  # Well-Known Binary

# Access GeoJSON-compatible data via the __geo_interface__ property
geojson_dict = gpx.__geo_interface__
```

### Reading from other file formats

*gpx* can read data from various file formats:

```python
from gpx import read_gpx, read_geojson, read_kml

# Read from files
gpx = read_gpx("path/to/file.gpx")
gpx = read_geojson("path/to/file.geojson")
gpx = read_kml("path/to/file.kml")
```

### Converting from data formats

*gpx* can convert from data formats (strings, bytes, objects):

```python
from gpx import from_geo_interface, from_wkt, from_wkb

# Convert from WKT (Well-Known Text)
gpx = from_wkt("POINT (4.9041 52.3676)")
gpx = from_wkt("LINESTRING (4.9 52.3, 4.91 52.31, 4.92 52.32)")

# Convert from WKB (Well-Known Binary)
gpx = from_wkb(wkb_bytes)

# Convert from any object that implements the __geo_interface__ protocol (e.g., Shapely)
from shapely.geometry import Point, LineString

point = Point(4.9041, 52.3676)
gpx = from_geo_interface(point)

line = LineString([(4.9, 52.3), (4.91, 52.31), (4.92, 52.32)])
gpx = from_geo_interface(line)

# Or convert from a GeoJSON dict directly
geojson = {"type": "Point", "coordinates": [4.9041, 52.3676]}
gpx = from_geo_interface(geojson)
```

### Command-Line Interface

*gpx* provides a command-line interface (CLI) for common GPX operations:

```sh
# Validate a GPX file
gpx validate path/to/file.gpx

# Show information and statistics about a GPX file
gpx info path/to/file.gpx
gpx info --json path/to/file.gpx  # Output as JSON

# Edit a GPX file
gpx edit input.gpx -o output.gpx --reverse-tracks
gpx edit input.gpx -o output.gpx --min-lat 52.0 --max-lat 53.0
gpx edit input.gpx -o output.gpx --start 2024-01-01T10:00:00 --end 2024-01-01T12:00:00
gpx edit input.gpx -o output.gpx --precision 5 --elevation-precision 1
gpx edit input.gpx -o output.gpx --strip-all-metadata

# Merge multiple GPX files
gpx merge file1.gpx file2.gpx file3.gpx -o merged.gpx

# Convert between formats
gpx convert input.gpx -o output.geojson
gpx convert input.gpx -o output.kml
gpx convert input.geojson -o output.gpx
```

<!-- end docs-include-usage -->
