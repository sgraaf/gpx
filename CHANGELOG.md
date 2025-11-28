# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Calendar Versioning](https://calver.org/).

The **first number** of the version is the year.
The **second number** is incremented with each release, starting at 1 for each year.
The **third number** is for emergencies when we need to start branches for older releases.

## [2025.1.0] - 2025-11-28

This is a major release that represents a complete rewrite of the library architecture. The package has been modernized with dataclass-based models, pure Python implementation, and enhanced GeoJSON support.

**This release contains multiple breaking changes. Please review the Changed and Removed sections carefully and see the migration notes at the end of this entry.**

### Added

-   `__geo_interface__` property to all geographic models for GeoJSON interoperability following the geo interface protocol.
-   `__geo_interface__` for `Waypoint` returns GeoJSON Point geometry.
-   `__geo_interface__` for `Route` returns GeoJSON LineString geometry.
-   `__geo_interface__` for `Track` returns GeoJSON MultiLineString geometry.
-   `__geo_interface__` for `TrackSegment` returns GeoJSON LineString geometry.
-   `__geo_interface__` for `Bounds` returns GeoJSON Polygon geometry.
-   `__geo_interface__` for `GPX` returns GeoJSON FeatureCollection with all features.
-   Statistics properties to `Track`, `TrackSegment`, and `Route`: `total_distance`, `total_duration`, `avg_speed`, `max_speed`, `min_speed`, `avg_elevation`, `max_elevation`, `min_elevation`, `total_ascent`, `total_descent`, `elevation_profile`, `speed_profile`, and `bounds`.
-   Calculation methods to `Waypoint`: `distance_to()`, `duration_to()`, `speed_to()`, `gain_to()`, and `slope_to()` for waypoint-to-waypoint calculations.
-   Memory-efficient `slots=True` to all dataclass models (approximately 40% memory reduction).
-   Automatic XML parsing and serialization based on type annotations via new utility functions in `utils.py`.
-   Comprehensive test suite with 258 tests covering all modules.
-   Smoke tests that validate package installation, basic GPX reading/writing, and core functionality.
-   Python 3.14 support.
-   Test workflow running on Python 3.11-3.14 via GitHub Actions.

### Changed

-   **BREAKING:** Package name changed from `PyGPX` to `gpx`. All imports must be updated from `from pygpx import ...` to `from gpx import ...`.
-   **BREAKING:** Replaced Element-based classes with dataclass-based models. All GPX elements (GPX, Waypoint, Track, Route, etc.) are now implemented as Python dataclasses.
-   **BREAKING:** All models now inherit from `GPXModel` base class instead of `Element` class.
-   **BREAKING:** Models are now mutable (changed from `frozen=True` to allow in-place modifications).
-   **BREAKING:** Models with all-optional fields now use keyword-only arguments. For example, `Track(name="My Track", trkseg=[segment])` instead of `Track("My Track", [segment])`.
-   **BREAKING:** Field names updated to exactly match GPX XML tag names. Prefer `wpt`, `trk`, `rte`, `trkseg`, `trkpt`, `rtept`, and `link` (aliases `waypoints`, `tracks`, `routes`, `segments`, `points`, and `links` still available for convenience).
-   **BREAKING:** XML parsing now uses Python's built-in `xml.etree.ElementTree` module instead of `lxml`.
-   **BREAKING:** `validate` parameter in `GPX.from_file()` and `GPX.from_string()` now raises `NotImplementedError` when set to `True`. XML validation is no longer supported.
-   **BREAKING:** Minimum Python version increased from 3.10 to 3.11. Python 3.11, 3.12, 3.13, and 3.14 are now supported.
-   **BREAKING:** Build backend changed from `flit` to `uv`. Package is now built using `uv build`.
-   **BREAKING:** Optional dependencies changed to dependency groups. Install with `uv sync --group dev` or `pip install -e ".[dev]"` instead of `pip install gpx[dev]`.
-   Default `creator` attribute for GPX objects is now `"gpx"` (previously `"PyGPX"`).
-   Namespace handling in XML parsing now uses XPath prefix approach for cleaner code.
-   Documentation updated to reflect the new dataclass-based API and pure Python implementation.

### Removed

-   **BREAKING:** `lxml` dependency. The library is now a pure Python package with zero runtime dependencies.
-   **BREAKING:** `gpx.xsd` schema file and all XML validation functionality.
-   **BREAKING:** `gpx.errors` module and `ParseError` exception. Standard Python exceptions (`ValueError`, `KeyError`, etc.) are now used for error handling.
-   **BREAKING:** `Element` base class.
-   **BREAKING:** `mixins` module (`AttributesMutableMappingMixin`, `PointsSequenceMixin`, `PointsMutableSequenceMixin`).
-   Python 3.10 support.

### Fixed

-   `GPX.to_string()` encoding issues when serializing to string format.
-   Statistics calculations for tracks, routes, and segments.
-   Datetime to string conversion in XML serialization.

---

**Migration notes for users upgrading from 0.2.x:**

1. Update package name: `pip uninstall pygpx && pip install gpx`
2. Update imports: `from pygpx import ...` → `from gpx import ...`
3. Update constructor calls to use keyword arguments for optional parameters
4. Update field names to use GPX-standard names (e.g., `trkseg` instead of `trksegs`)
5. Remove `validate=True` from `from_file()` and `from_string()` calls
6. Update error handling to catch standard Python exceptions instead of `gpx.errors.ParseError`
7. Ensure Python 3.11 or higher is installed

Example:
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
gpx = GPX.from_file("track.gpx")
waypoint = Waypoint(lat=Decimal("52.0"), lon=Decimal("4.0"), name="Amsterdam")
gpx.wpt.append(waypoint)
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
