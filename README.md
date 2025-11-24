<!-- start docs-include-index -->

# PyGPX

[![PyPI](https://img.shields.io/pypi/v/gpx)](https://img.shields.io/pypi/v/gpx)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/gpx)](https://pypi.org/project/gpx/)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/sgraaf/gpx/main.svg)](https://results.pre-commit.ci/latest/github/sgraaf/gpx/main)
[![Documentation Status](https://readthedocs.org/projects/gpx/badge/?version=latest)](https://gpx.readthedocs.io/en/latest/?badge=latest)
[![PyPI - License](https://img.shields.io/pypi/l/gpx)](https://img.shields.io/pypi/l/gpx)

PyGPX is a Python package that brings support for reading, writing and converting GPX files.

<!-- end docs-include-index -->

## Installation

<!-- start docs-include-installation -->

### From PyPI

PyGPX is available on [PyPI](https://pypi.org/project/gpx/). Install with `pip` or your package manager of choice:

```bash
pip install gpx
```

### From source

If you'd like, you can also install PyGPX from source (with [`uv`](https://docs.astral.sh/uv/)):

```bash
git clone https://github.com/sgraaf/gpx.git
cd gpx
python3 -m pip install uv
uv sync
```

<!-- end docs-include-installation -->

## Documentation

Check out the [PyGPX documentation](https://gpx.readthedocs.io/en/stable/) for the [User's Guide](https://gpx.readthedocs.io/en/stable/usage.html) and [API Reference](https://gpx.readthedocs.io/en/stable/api.html).

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
print(f"Number of waypoints: {len(gpx.waypoints)}")
print(f"Number of tracks: {len(gpx.tracks)}")
print(f"Number of routes: {len(gpx.routes)}")
```

### Working with waypoints

```python
from gpx import Waypoint
from decimal import Decimal

# Add a new waypoint
waypoint = Waypoint()
waypoint.latitude = Decimal("52.3676")
waypoint.longitude = Decimal("4.9041")
waypoint.name = "Amsterdam"
waypoint.description = "Capital of the Netherlands"
waypoint.elevation = Decimal("2.0")

gpx.waypoints.append(waypoint)

# Iterate over waypoints
for wpt in gpx.waypoints:
    print(f"{wpt.name}: ({wpt.latitude}, {wpt.longitude})")
```

### Working with tracks and statistics

```python
# Access track data
for track in gpx.tracks:
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
            print(f"    Point: ({point.latitude}, {point.longitude}) at {point.time}")
```

### Creating a GPX from scratch

```python
from gpx import GPX, Metadata, Track, TrackSegment, Waypoint
from datetime import datetime, timezone
from decimal import Decimal

# Create a new GPX object
gpx = GPX()
gpx.creator = "My Application"

# Add metadata
metadata = Metadata()
metadata.name = "My GPS Track"
metadata.description = "A sample track"
metadata.time = datetime.now(timezone.utc)
gpx.metadata = metadata

# Create a track with segments
track = Track()
track.name = "Morning Run"

segment = TrackSegment()

# Add track points
for i in range(5):
    point = Waypoint()
    point.latitude = Decimal("52.0") + Decimal(i) * Decimal("0.01")
    point.longitude = Decimal("4.0") + Decimal(i) * Decimal("0.01")
    point.elevation = Decimal("10.0") + Decimal(i) * Decimal("2.0")
    point.time = datetime.now(timezone.utc)
    segment.points.append(point)

track.segments.append(segment)
gpx.tracks.append(track)
```

### Writing and validating GPX files

```python
# Write GPX data to file
gpx.to_file("output.gpx")

# Convert to string
gpx_string = gpx.to_string()
print(gpx_string)

# Parse from string with validation
gpx = GPX.from_string(gpx_string, validate=True)
```

### Working with routes

```python
from gpx import Route

# Create a route
route = Route()
route.name = "City Tour"

# Add route points (waypoints)
point1 = Waypoint()
point1.latitude = Decimal("52.3676")
point1.longitude = Decimal("4.9041")
point1.name = "Start: Amsterdam Centraal"

point2 = Waypoint()
point2.latitude = Decimal("52.3731")
point2.longitude = Decimal("4.8922")
point2.name = "Dam Square"

route.points.extend([point1, point2])
gpx.routes.append(route)

# Access route statistics
print(f"Route distance: {route.total_distance:.2f} meters")
```

<!-- end docs-include-usage -->
