# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Calendar Versioning](https://calver.org/).

The **first number** of the version is the year.
The **second number** is incremented with each release, starting at 1 for each year.
The **third number** is for emergencies when we need to start branches for older releases.

## [Unreleased](https://github.com/sgraaf/gpx/compare/2026.1.0...HEAD)

### Added

- GPX Extensions support: Added `Extensions` class for handling GPX extension elements from any XML namespace (e.g., Garmin's `TrackPointExtension`). Extensions are now parsed, preserved, and serialized during round-trip processing, enabling lossless handling of vendor-specific data like heart rate, cadence, temperature, etc.
- New `extensions` field on all models that support extensions per the GPX 1.1 spec: `GPX`, `Metadata`, `Waypoint`, `Track`, `TrackSegment`, and `Route`.

### Fixed

- Namespace prefix preservation: GPX files with extension namespaces now preserve their original namespace prefixes (e.g., `gpxtpx`) during round-trip read/write operations, instead of being rewritten with generic prefixes (e.g., `ns0`, `ns1`, `ns2`). This ensures lossless round-tripping of GPX files with extensions.

## [2026.1.0](https://github.com/sgraaf/gpx/compare/2025.1.0...2026.1.0) - 2026-01-07

### Added

- New `cli` module with command-line interface (CLI) for common GPX operations:
  - `gpx validate`: Validate a GPX file
  - `gpx info`: Show information and statistics about a GPX file
  - `gpx edit`: Edit a GPX file with various transformations:
    - Crop to a geographic bounding box (`--min-lat`, `--min-lon`, `--max-lat`, `--max-lon`)
    - Trim to a date/time range (`--start`, `--end`)
    - Reverse routes and/or tracks (`--reverse`, `--reverse-routes`, `--reverse-tracks`)
    - Strip metadata fields (`--strip-name`, `--strip-desc`, `--strip-author`, `--strip-copyright`, `--strip-time`, `--strip-keywords`, `--strip-links`, `--strip-all-metadata`)
    - Reduce coordinate precision (`--precision`, `--elevation-precision`)
  - `gpx merge`: Merge multiple GPX files into one
  - `gpx convert`: Convert between GPX, GeoJSON, and KML formats
- New CLI reference documentation page with auto-generated help output using `cog`
- New `io` module with `read_*()` functions for reading file formats:
  - `read_gpx()`: Read GPX files
  - `read_geojson()`: Read GeoJSON files
  - `read_kml()`: Read KML files
- New `convert` module with `from_*()` functions for converting from data formats:
  - `from_string()`: Convert from a GPX string
  - `from_geo_interface()`: Convert from objects that implement the `__geo_interface__` protocol (e.g., Shapely)
  - `from_wkb()`: Convert from Well-Known Binary bytes
  - `from_wkt()`: Convert from Well-Known Text strings
- New `write_*()` methods on the `GPX` class for writing to file formats:
  - `write_gpx()`: Write to GPX file (renamed from `to_file()`)
  - `write_geojson()`: Write to GeoJSON file
  - `write_kml()`: Write to KML file (Google Earth format)
- New `to_*()` methods on the `GPX` class for converting to data formats:
  - `to_wkt()`: Convert to Well-Known Text (OGC standard)
  - `to_wkb()`: Convert to Well-Known Binary (OGC standard)

### Changed

- Renamed `GPX.to_file()` to `GPX.write_gpx()` for consistency with other write methods.
- Replaced built-in `tempfile` module usage with pytest's `tmp_path` and `tmp_path_factory` fixtures in the test suite for better test isolation and automatic cleanup.

### Removed

- All aliases and proxies.
- `GPX.from_file()` method in favor of `io.read_gpx()`.
- `GPX.from_string()` method in favor of `convert.from_string()`.

## [2025.1.0](https://github.com/sgraaf/gpx/compare/0.2.1...2025.1.0) - 2025-11-29

This is a major release with a lot of breaking changes, primarily due to a complete rewrite of the architecture, and a general modernization of the package. Besides the change in architecture, this release adds comprehensive unit tests, enforces strict linting rules, and drops support folder older versions of Python. Finally, this release implements the `__geo_interface__` protocol for all GPX elements that contain geopgraphic information, thus adding support for converting to GeoJSON.

**Migration notes for users upgrading from 0.2.x:**

1. Ensure you are using Python 3.11 or higher
1. Update constructor calls to use keyword arguments for optional parameters
1. Update field names to use GPX-standard names (e.g., `trkseg` instead of `trksegs`)
1. Remove `validate=True` from `from_file()` and `from_string()` calls
1. Update error handling to catch standard Python exceptions instead of `gpx.errors.ParseError`

Example:

```python
# Before (0.2.x)
from gpx import GPX, Waypoint

gpx = GPX.from_file("path/to/track.gpx", validate=True)
waypoint = Waypoint()
waypoint.lat = Decimal("52.0")
waypoint.lon = Decimal("4.0")
waypoint.name = "Amsterdam"
gpx.waypoints.append(waypoint)

# After (2025.1.0)
from gpx import GPX, Waypoint
from decimal import Decimal

gpx = GPX.from_file("path/to/track.gpx")
waypoint = Waypoint(Decimal("52.0"), Decimal("4.0"), name="Amsterdam")
gpx.wpt.append(waypoint)
```

### Added

- `CLAUDE.md` for easier interoperability with Claude Code.
- Comprehensive unit tests.
- Smoke test.
- Testing workflow via GitHub Actions.
- Support for Python 3.12, 3.13 and 3.14.
- More usage examples in `README.md`.
- `__geo_interface__` protocol for all GPX elements that contain geographic information.

### Changed

- Upgraded the `pre-commit` hooks.
- Enabled ALL rules for the `ruff` linter by default.
- Use the `uv` build backend instead of `flit`.
- Updated the installation instructions to make use of `uv` instead of `pip`.
- Switched the versioning scheme from semantic versioning to [Calendar Versioning](https://calver.org/).
- Refactored the GPX element classes into `dataclass`-based models.
- Replaced `lxml` with the built-in `ElementTree` module.
- Optional dependencies to dependency groups.
- Renamed `PyGPX` to `gpx` (purely aesthetically, no changes in installation or usage required).

### Removed

- Support for Python 3.7, 3.8, 3.9 and 3.10.
- The errors module.

### Fixed

- Erroneous examples in the usage examples in `README.md`.

## 0.2.1 (2023-04-09)

### Fixed

- Serialization of route and track numbers. #10
- Mutable default values. #11

## 0.2.0 (2023-04-06)

With this release, PyGPX is now fully [^spec-compat] compatible with the [GPX 1.1 specification](https://www.topografix.com/GPX/1/1/gpx.xsd).

### Changes

- Added the following new modules and classes:
  - {py:class}`gpx.bounds.Bounds`
  - {py:class}`gpx.copyright.Copyright`
  - {py:class}`gpx.element.Element`
  - {py:class}`gpx.email.Email`
  - {py:class}`gpx.link.Link`
  - {py:class}`gpx.metadata.Metadata`
  - {py:class}`gpx.mixins.AttributesMutableMappingMixin`
  - {py:class}`gpx.mixins.PointsSequenceMixin`
  - {py:class}`gpx.mixins.PointsMutableSequenceMixin`
  - {py:class}`gpx.person.Person`
  - {py:class}`gpx.track_segment.TrackSegment`
  - {py:class}`gpx.types.Latitude`
  - {py:class}`gpx.types.Longitude`
  - {py:class}`gpx.types.Degrees`
  - {py:class}`gpx.types.Fix`
  - {py:class}`gpx.types.DGPSStation`
- All element classes now inherit from the new {py:class}`gpx.element.Element` base class.
- All element classes now make use of the new element / type classes (e.g. {py:class}`gpx.types.Latitude`), according to the GPX 1.1 specification.
- Added the {py:class}`gpx.errors.ParseError` exception for when attempting to parse an XML element that does not exist.
- All metadata attributes have been moved to the new {py:class}`gpx.metadata.Metadata` class, but are still accessible via the {py:class}`gpx.gpx.GPX` class via aliases for backwards compatibility and convenience.
- Changed all `duration` attributes to {external:class}`datetime.timedelta` objects (instead of `float`s).

## 0.1.1 (2023-03-31)

This release introduces a completely overhauled codebase. For this, I used my [cookiecutter-python-package](https://github.com/sgraaf/cookiecutter-python-package) Python package template. As such, this release comes with much higher code quality, documentation and automation.

The API itself has not changed (and as such, there is no minor version bump).

### Changes

- Completely refactored codebase, with:
  - Moved source code from `./gpx` to `./src/gpx`
  - Fully typed and documented
- Added documentation via [Read the Docs](https://readthedocs.org/)
- Updated CI/CD via GitHub Actions
- Added [pre-commit hooks](https://pre-commit.com) w/ CI-integration

## 0.1.0 (2021-06-08)

### Changes

- Initial release of PyGPX

[^spec-compat]: PyGPX is not compatible with extensions from other schemas (e.g. the [Garmin GPX extensions](https://www8.garmin.com/xmlschemas/GpxExtensionsv3.xsd)), and ignores them.
