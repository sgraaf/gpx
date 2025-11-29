<!-- start docs-include-index -->

# gpx

[![PyPI](https://img.shields.io/pypi/v/gpx)](https://img.shields.io/pypi/v/gpx)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/gpx)](https://pypi.org/project/gpx/)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/sgraaf/gpx/main.svg)](https://results.pre-commit.ci/latest/github/sgraaf/gpx/main)
[![Test](https://github.com/sgraaf/gpx/actions/workflows/test.yml/badge.svg)](https://github.com/sgraaf/gpx/actions/workflows/test.yml)
[![Documentation Status](https://readthedocs.org/projects/gpx/badge/?version=latest)](https://gpx.readthedocs.io/en/latest/?badge=latest)
[![PyPI - License](https://img.shields.io/pypi/l/gpx)](https://img.shields.io/pypi/l/gpx)

*gpx* is a pure Python package that brings support for reading, manipulating, writing and converting GPX (GPS Exchange Format) files.

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
from gpx import GPX

# Read GPX data from file
gpx = GPX.from_file("path/to/file.gpx")

# Access basic properties
print(f"Creator: {gpx.creator}")
print(f"Bounds: {gpx.bounds}")
print(f"Number of waypoints: {len(gpx.wpt)}")
print(f"Number of tracks: {len(gpx.trk)}")
print(f"Number of routes: {len(gpx.rte)}")
```

### Working with waypoints

```python
from gpx import Waypoint
from decimal import Decimal

# Create a new waypoint
waypoint = Waypoint(
    lat=Decimal("52.3676"),
    lon=Decimal("4.9041"),
    name="Amsterdam",
    desc="Capital of the Netherlands",
    ele=Decimal("2.0"),
)

gpx.wpt.append(waypoint)

# Iterate over waypoints
for wpt in gpx.wpt:
    print(f"{wpt.name}: ({wpt.lat}, {wpt.lon})")
```

### Working with tracks and statistics

```python
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
    for segment in track.segments:
        print(f"  Segment with {len(segment.points)} points")
        for point in segment.points:
            print(f"    Point: ({point.lat}, {point.lon}) at {point.time}")
```

### Creating a GPX from scratch

```python
from gpx import GPX, Metadata, Track, TrackSegment, Waypoint
from datetime import datetime, timezone
from decimal import Decimal

# Create track points
points = []
for i in range(5):
    point = Waypoint(
        lat=Decimal("52.0") + Decimal(i) * Decimal("0.01"),
        lon=Decimal("4.0") + Decimal(i) * Decimal("0.01"),
        ele=Decimal("10.0") + Decimal(i) * Decimal("2.0"),
        time=datetime.now(timezone.utc),
    )
    points.append(point)

# Create a track with segments
segment = TrackSegment(trkpt=points)
track = Track(name="Morning Run", trkseg=[segment])

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
# Write GPX data to file
gpx.to_file("output.gpx")

# Convert to string
gpx_string = gpx.to_string()
print(gpx_string)

# Parse from string
gpx = GPX.from_string(gpx_string)
```

### Working with routes

```python
from gpx import Route

# Create route points (waypoints)
point1 = Waypoint(
    lat=Decimal("52.3676"),
    lon=Decimal("4.9041"),
    name="Start: Amsterdam Centraal",
)

point2 = Waypoint(
    lat=Decimal("52.3731"),
    lon=Decimal("4.8922"),
    name="Dam Square",
)

# Create a route
route = Route(name="City Tour", rtept=[point1, point2])
gpx.rte.append(route)

# Access route statistics
print(f"Route distance: {route.total_distance:.2f} meters")
```

<!-- end docs-include-usage -->
