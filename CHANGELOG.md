# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Calendar Versioning](https://calver.org/).

The **first number** of the version is the year.
The **second number** is incremented with each release, starting at 1 for each year.
The **third number** is for emergencies when we need to start branches for older releases.

## 2025.1.0 (2025-11-28)

This is a major release that represents a complete rewrite of the library architecture. The package has been modernized with dataclass-based models, pure Python implementation, and enhanced GeoJSON support.

### ⚠️ Breaking Changes

#### Package Renamed

-   **The package has been renamed from "PyGPX" to "gpx"**. Update all imports:
    ```python
    # Old
    from pygpx import GPX

    # New
    from gpx import GPX
    ```

#### Complete Architecture Refactor

-   **Replaced Element-based classes with dataclass-based models**. All GPX elements (GPX, Waypoint, Track, Route, etc.) are now implemented as Python dataclasses with `slots=True` for memory efficiency.
-   **Removed the `Element` base class** and `mixins` module. All models now inherit from `GPXModel` which provides `from_xml()` and `to_xml()` methods.
-   **Models are now mutable** (changed from `frozen=True` to allow in-place modifications).
-   **Models with all-optional fields now use keyword-only arguments** for clarity. For example:
    ```python
    # Old (positional args allowed)
    track = Track("My Track", [segment])

    # New (keyword-only)
    track = Track(name="My Track", trkseg=[segment])
    ```

#### Field Name Changes

Several field names have been updated to exactly match GPX XML tag names (aliases still provided for convenience):

-   Waypoints list: prefer `wpt` (alias: `waypoints`)
-   Tracks list: prefer `trk` (alias: `tracks`)
-   Routes list: prefer `rte` (alias: `routes`)
-   Track segments: prefer `trkseg` (alias: `segments`)
-   Track points: prefer `trkpt` (alias: `points`)
-   Route points: prefer `rtept` (alias: `points`)
-   Links list: prefer `link` (alias: `links`)

#### Removed lxml Dependency

-   **The `lxml` dependency has been removed**. The library now uses Python's built-in `xml.etree.ElementTree` module, making it a **pure Python package with zero dependencies**.
-   **XML validation support has been removed**. Calling `GPX.from_file()` or `GPX.from_string()` with `validate=True` will raise `NotImplementedError`. The `gpx.xsd` schema file has been removed.

#### Removed errors Module

-   **The `gpx.errors` module has been removed** along with the `ParseError` exception. Standard Python exceptions (`ValueError`, `KeyError`, etc.) are now used for error handling.

#### Python Version Requirement

-   **Minimum Python version increased from 3.10 to 3.11**. Python 3.11, 3.12, 3.13, and 3.14 are now supported.

#### Build System and Dependencies

-   **Build backend changed from `flit` to `uv`**. The package is now built using `uv build` instead of `flit`.
-   **Changed from optional dependencies to dependency groups**. Install development dependencies with:
    ```bash
    # Old
    pip install gpx[dev]

    # New
    uv sync --group dev
    # or with pip
    pip install -e ".[dev]"
    ```

### Added

#### GeoJSON Support

-   **Added `__geo_interface__` protocol support** to all geographic models for GeoJSON interoperability:
    -   `Waypoint`: Returns GeoJSON Point geometry
    -   `Route`: Returns GeoJSON LineString geometry
    -   `Track`: Returns GeoJSON MultiLineString geometry
    -   `TrackSegment`: Returns GeoJSON LineString geometry
    -   `Bounds`: Returns GeoJSON Polygon geometry
    -   `GPX`: Returns GeoJSON FeatureCollection with all features

    Example usage:
    ```python
    waypoint = Waypoint(lat=Decimal("52.0"), lon=Decimal("4.0"))
    geo_json = waypoint.__geo_interface__
    # {"type": "Point", "coordinates": [4.0, 52.0]}
    ```

#### Enhanced Statistics and Calculations

-   **Added comprehensive statistics methods** to Track, TrackSegment, and Route:
    -   `total_distance`: Total distance in meters (Haversine formula)
    -   `total_duration`: Total time duration
    -   `avg_speed`, `max_speed`, `min_speed`: Speed statistics in m/s
    -   `avg_elevation`, `max_elevation`, `min_elevation`: Elevation statistics
    -   `total_ascent`, `total_descent`: Cumulative elevation changes
    -   `elevation_profile`: List of elevation values with distance
    -   `speed_profile`: List of speed values with distance
    -   `bounds`: Geographic bounding box

-   **Added waypoint-to-waypoint calculation methods**:
    -   `distance_to(other)`: Distance in meters using Haversine formula
    -   `duration_to(other)`: Time duration as `timedelta`
    -   `speed_to(other)`: Speed in m/s
    -   `gain_to(other)`: Elevation gain in meters
    -   `slope_to(other)`: Slope as percentage

#### Dataclass Improvements

-   **All dataclasses use `slots=True`** for memory-efficient attribute storage (approximately 40% memory reduction).
-   **Automatic XML parsing and serialization** based on type annotations via new utility functions in `utils.py`.
-   **Better type safety** with full type annotations and PEP 561 compliance (`py.typed` marker).

#### Testing

-   **Added comprehensive test suite** with 258 tests covering all modules.
-   **Added smoke tests** that validate package installation, basic GPX reading/writing, and core functionality.
-   **All tests now run on Python 3.11-3.14** via GitHub Actions.

### Changed

-   **Default `creator` attribute** for GPX objects is now `"gpx"` (previously `"PyGPX"`).
-   **Improved namespace handling** in XML parsing using XPath prefix approach for cleaner code.
-   **Documentation updated** to reflect the new dataclass-based API and pure Python implementation.

### Fixed

-   **Fixed `GPX.to_string()` encoding issues** when serializing to string format.
-   **Fixed statistics calculations** for tracks, routes, and segments.
-   **Fixed datetime to string conversion** in XML serialization.

### Migration Guide

For users upgrading from 0.2.x versions:

1. **Update package name**: `pip uninstall pygpx && pip install gpx`
2. **Update imports**: Change `from pygpx import ...` to `from gpx import ...`
3. **Update constructor calls**: Use keyword arguments for all optional parameters
4. **Update field names**: Use the GPX-standard field names (e.g., `trkseg` instead of `trksegs`)
5. **Remove validation calls**: Remove `validate=True` from `from_file()` and `from_string()` calls
6. **Update error handling**: Catch standard Python exceptions instead of `gpx.errors.ParseError`
7. **Check Python version**: Ensure you're using Python 3.11 or higher

Example migration:

```python
# Before (0.2.x)
from pygpx import GPX, Waypoint

gpx = GPX.from_file("track.gpx", validate=True)
waypoint = Waypoint()
waypoint.lat = Decimal("52.0")
waypoint.lon = Decimal("4.0")
waypoint.name = "Amsterdam"
gpx.waypoints.append(waypoint)

# After (2025.1.0)
from gpx import GPX, Waypoint
from decimal import Decimal

gpx = GPX.from_file("track.gpx")  # No validation parameter
waypoint = Waypoint(
    lat=Decimal("52.0"),
    lon=Decimal("4.0"),
    name="Amsterdam"
)
gpx.wpt.append(waypoint)  # or gpx.waypoints.append(waypoint)
```

## 0.2.1 (2023-04-09)

### Fixed

-   Serialization of route and track numbers. #10
-   Mutable default values. #11

## 0.2.0 (2023-04-06)

With this release, PyGPX is now fully [^spec-compat] compatible with the [GPX 1.1 specification](https://www.topografix.com/GPX/1/1/gpx.xsd).

### Changes

-   Added the following new modules and classes:
    -   {py:class}`gpx.bounds.Bounds`
    -   {py:class}`gpx.copyright.Copyright`
    -   {py:class}`gpx.element.Element`
    -   {py:class}`gpx.email.Email`
    -   {py:class}`gpx.link.Link`
    -   {py:class}`gpx.metadata.Metadata`
    -   {py:class}`gpx.mixins.AttributesMutableMappingMixin`
    -   {py:class}`gpx.mixins.PointsSequenceMixin`
    -   {py:class}`gpx.mixins.PointsMutableSequenceMixin`
    -   {py:class}`gpx.person.Person`
    -   {py:class}`gpx.track_segment.TrackSegment`
    -   {py:class}`gpx.types.Latitude`
    -   {py:class}`gpx.types.Longitude`
    -   {py:class}`gpx.types.Degrees`
    -   {py:class}`gpx.types.Fix`
    -   {py:class}`gpx.types.DGPSStation`
-   All element classes now inherit from the new {py:class}`gpx.element.Element` base class.
-   All element classes now make use of the new element / type classes (e.g. {py:class}`gpx.types.Latitude`), according to the GPX 1.1 specification.
-   Added the {py:class}`gpx.errors.ParseError` exception for when attempting to parse an XML element that does not exist.
-   All metadata attributes have been moved to the new {py:class}`gpx.metadata.Metadata` class, but are still accessible via the {py:class}`gpx.gpx.GPX` class via aliases for backwards compatibility and convenience.
-   Changed all `duration` attributes to {external:class}`datetime.timedelta` objects (instead of `float`s).

[^spec-compat]: PyGPX is not compatible with extensions from other schemas (e.g. the [Garmin GPX extensions](https://www8.garmin.com/xmlschemas/GpxExtensionsv3.xsd)), and ignores them.

## 0.1.1 (2023-03-31)

This release introduces a completely overhauled codebase. For this, I used my [cookiecutter-python-package](https://github.com/sgraaf/cookiecutter-python-package) Python package template. As such, this release comes with much higher code quality, documentation and automation.

The API itself has not changed (and as such, there is no minor version bump).

### Changes

-   Completely refactored codebase, with:
    -   Moved source code from `./gpx` to `./src/gpx`
    -   Fully typed and documented
-   Added documentation via [Read the Docs](https://readthedocs.org/)
-   Updated CI/CD via GitHub Actions
-   Added [pre-commit hooks](https://pre-commit.com) w/ CI-integration

## 0.1.0 (2021-06-08)

### Changes

-   Initial release of PyGPX
