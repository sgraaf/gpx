# CLAUDE.md

This file provides guidance for AI assistants working with the *gpx* codebase.

## Project Overview

*gpx* is a pure Python library for reading, manipulating, writing, and converting GPX (GPS Exchange Format) files. It provides a fully-typed, dataclass-based interface for working with GPX 1.1 specification data.

-   **Package name**: `gpx` (on PyPI)
-   **Current version**: 2025.1.0
-   **Python support**: 3.11+ (including 3.14)
-   **License**: GPL-3.0+
-   **Documentation**: https://gpx.readthedocs.io/

## Repository Structure

```
gpx/
├── src/gpx/              # Main source code (src layout)
│   ├── __init__.py       # Package exports and version
│   ├── base.py           # GPXModel base class with from_xml/to_xml
│   ├── gpx.py            # GPX root element model
│   ├── waypoint.py       # Waypoint dataclass model
│   ├── track.py          # Track dataclass model
│   ├── track_segment.py  # TrackSegment dataclass model
│   ├── route.py          # Route dataclass model
│   ├── metadata.py       # Metadata dataclass model
│   ├── bounds.py         # Bounds dataclass model
│   ├── link.py           # Link dataclass model
│   ├── person.py         # Person dataclass model
│   ├── email.py          # Email dataclass model
│   ├── copyright.py      # Copyright dataclass model
│   ├── types.py          # Custom types: Latitude, Longitude, Degrees, Fix, DGPSStation
│   ├── utils.py          # Utility functions for XML parsing and serialization
│   ├── convert.py        # Conversion functions: from_geo_interface, from_wkb, from_wkt
│   ├── io.py             # I/O functions: read_gpx, read_geojson, read_kml
│   └── py.typed          # PEP 561 marker for type hints
├── docs/                 # Sphinx documentation (MyST Markdown)
├── tests/                # Test suite
│   ├── __init__.py       # Package marker
│   ├── conftest.py       # Pytest configuration and fixtures
│   ├── smoke_test.py     # Comprehensive smoke tests
│   ├── test_edge_cases.py # Edge case tests for valid/invalid GPX
│   ├── test_gpx.py       # GPX model tests
│   ├── test_metadata.py  # Metadata model tests
│   ├── test_route.py     # Route model tests
│   ├── test_statistics.py # Statistics and calculation tests
│   ├── test_track.py     # Track model tests
│   ├── test_types.py     # Custom types tests
│   ├── test_utils.py     # Utilities tests
│   ├── test_waypoint.py  # Waypoint model tests
│   ├── test_io_convert.py # IO and conversion tests (read/write/convert)
│   └── fixtures/         # GPX fixture files for testing
│       ├── valid/        # Valid GPX files for parsing tests
│       └── invalid/      # Invalid GPX files for error handling tests
├── pyproject.toml        # Project configuration and dependencies
├── uv.lock               # Dependency lock file (managed by uv)
├── CHANGELOG.md          # Project changelog (needs updating)
├── CLAUDE.md             # AI assistant guidance (this file)
├── .pre-commit-config.yaml  # Pre-commit hooks configuration
├── .readthedocs.yaml     # ReadTheDocs configuration
├── .editorconfig         # Editor settings
├── .gitattributes        # Git attributes
└── .github/
    └── workflows/
        ├── publish.yml   # PyPI publishing workflow
        └── test.yml      # Python test workflow (3.11-3.14)
```

### Key Configuration Files

-   **pyproject.toml**: Central configuration for:
    -   Build system (uv_build)
    -   Project metadata and dependencies
    -   Ruff linting rules and per-file ignores
    -   Tool configurations
-   **uv.lock**: Dependency lock file (do not edit manually)
-   **.pre-commit-config.yaml**: Pre-commit hooks configuration
-   **.readthedocs.yaml**: ReadTheDocs build configuration
-   **.editorconfig**: Editor settings (4 spaces, LF line endings, UTF-8)
-   **.gitattributes**: Git attributes for line ending normalization

## Development Setup

The project uses **uv** as its build backend and package manager.

```bash
# Install from source with uv
pip install uv
uv sync

# Install with dev dependencies
uv sync --dev

# Install with test dependencies
uv sync --group tests

# Or install with pip (traditional method)
pip install -e ".[dev]"
pip install -e ".[tests]"
```

## Build System

The project uses **uv** as its build backend (configured in `pyproject.toml`):

```toml
[build-system]
requires = ["uv_build>=0.9.11,<0.10.0"]
build-backend = "uv_build"
```

Building the package:

```bash
# Build wheel and source distribution
uv build

# Build only wheel
uv build --wheel

# Build only source distribution
uv build --sdist
```

## Code Architecture

The project uses dataclass-based models for all GPX elements. All models inherit from the `GPXModel` base class and use Python's `@dataclass` decorator.

### Dataclass Model Hierarchy

```
GPXModel (base.py)
├── GPX (gpx.py) - root element
├── Waypoint (waypoint.py) - waypoint/track point/route point
├── Track (track.py) - track
├── TrackSegment (track_segment.py) - track segment
├── Route (route.py) - route
├── Metadata (metadata.py) - metadata
├── Bounds (bounds.py) - bounding box
├── Link (link.py) - web link
├── Person (person.py) - person/author
├── Email (email.py) - email address
└── Copyright (copyright.py) - copyright
```

### Design Patterns

1. **Dataclass Pattern**: Uses Python's `@dataclass` decorator with:
    - `slots=True`: Memory-efficient attribute storage
    - `kw_only=True`: For classes where all fields are optional (Track, Route, Metadata, etc.)
    - Field defaults and `field(default_factory=list)` for collections

2. **GPXModel Base Class** (`base.py`):
    - Provides `from_xml()` classmethod for parsing
    - Provides `to_xml()` method for serialization
    - Each model defines `_tag` class attribute for XML tag name

3. **Automatic Type Conversion** (`utils.py`):
    - `parse_from_xml()`: Auto-converts XML to Python types based on field annotations
    - `build_to_xml()`: Auto-converts Python types to XML based on field annotations
    - Uses `get_type_hints()` to introspect dataclass fields
    - Distinguishes attributes (required) vs elements (optional) automatically
    - GPX pattern: attributes have no `| None`, elements have `| None`

4. **Custom Types** (`types.py`):
    - `Latitude`, `Longitude`: Validated Decimal subclasses with range checks
    - `Degrees`: For bearing/heading (0-360)
    - `Fix`: GPS fix type enum-like string
    - `DGPSStation`: DGPS station ID (0-1023)

5. **GeoJSON Support**:
    - All geographic models (GPX, Waypoint, Track, Route) implement the `__geo_interface__` protocol
    - Provides GeoJSON-compatible geometry representation
    - GPX returns FeatureCollection, waypoints return Point, tracks return MultiLineString, routes return LineString

### Entry Points

**Reading GPX files:**

```python
from gpx import from_string, read_gpx

# Read from file
gpx = read_gpx("path/to/file.gpx")

# Read from string
gpx = from_string(gpx_string)

# Access basic properties
print(gpx.creator)
print(gpx.version)  # Always "1.1"
print(len(gpx.wpt))  # or gpx.wpt
print(len(gpx.trk))      # or gpx.trk
print(len(gpx.rte))      # or gpx.rte
```

**Reading from other file formats:**

```python
from gpx import read_geojson, read_kml

# Read GeoJSON file
gpx = read_geojson("path/to/file.geojson")

# Read KML file (Google Earth format)
gpx = read_kml("path/to/file.kml")
```

**Converting from data formats:**

```python
from gpx import from_geo_interface, from_wkb, from_wkt

# Convert from WKT (Well-Known Text)
gpx = from_wkt("POINT (4.0 52.0)")
gpx = from_wkt("LINESTRING (4.0 52.0, 4.1 52.1)")

# Convert from WKB (Well-Known Binary)
gpx = from_wkb(wkb_bytes)

# Convert from objects with __geo_interface__ (e.g., Shapely)
from shapely.geometry import Point
point = Point(4.0, 52.0)
gpx = from_geo_interface(point)

# Convert from GeoJSON dict
geojson = {"type": "Point", "coordinates": [4.0, 52.0]}
gpx = from_geo_interface(geojson)
```

**Writing GPX files:**

```python
# Write to GPX file
gpx.write_gpx("output.gpx")

# Write to other file formats
gpx.write_geojson("output.geojson")
gpx.write_kml("output.kml")

# Convert to string
gpx_string = gpx.to_string()

# Convert to data formats
wkt_string = gpx.to_wkt()  # Well-Known Text
wkb_bytes = gpx.to_wkb()   # Well-Known Binary

# Write with pretty printing (default)
gpx.write_gpx("output.gpx", pretty_print=True)
```

**Creating GPX data:**

```python
from gpx import GPX, Waypoint, Track, TrackSegment, Metadata
from decimal import Decimal
from datetime import datetime, timezone

# Create waypoints
waypoint = Waypoint(
    lat=Decimal("52.3676"),
    lon=Decimal("4.9041"),
    name="Amsterdam",
    ele=Decimal("2.0"),
)

# Create metadata
metadata = Metadata(
    name="My Track",
    desc="A sample track",
    time=datetime.now(timezone.utc),
)

# Create track with segments
segment = TrackSegment(
    trkpt=[
        Waypoint(
            lat=Decimal("52.0"),
            lon=Decimal("4.0"),
            time=datetime.now(timezone.utc),
        )
    ]
)
track = Track(name="Morning Run", trkseg=[segment])

# Create GPX object (creator defaults to "*gpx*")
gpx = GPX(creator="My Application", metadata=metadata, trk=[track])

# Save to file
gpx.to_file("output.gpx")
```

**Working with statistics:**

```python
# Get statistics from tracks
track = gpx.trk[0]
print(f"Distance: {track.total_distance} meters")
print(f"Duration: {track.total_duration}")
print(f"Avg speed: {track.avg_speed} m/s")
print(f"Max elevation: {track.max_elevation} m")
print(f"Total ascent: {track.total_ascent} m")
print(f"Bounds: {track.bounds}")

# Get elevation and speed profiles
elevation_profile = track.elevation_profile
speed_profile = track.speed_profile
```

**Using waypoint calculation methods:**

```python
from gpx import Waypoint
from decimal import Decimal
from datetime import datetime, timezone, timedelta

point1 = Waypoint(
    lat=Decimal("52.0"),
    lon=Decimal("4.0"),
    ele=Decimal("10.0"),
    time=datetime.now(timezone.utc),
)

point2 = Waypoint(
    lat=Decimal("52.01"),
    lon=Decimal("4.01"),
    ele=Decimal("15.0"),
    time=datetime.now(timezone.utc) + timedelta(minutes=5),
)

# Calculate distance, duration, speed, gain, slope
distance = point1.distance_to(point2)  # meters
duration = point1.duration_to(point2)  # timedelta
speed = point1.speed_to(point2)  # m/s
gain = point1.gain_to(point2)  # meters
slope = point1.slope_to(point2)  # percent

# GeoJSON interface
geo = point1.__geo_interface__  # {"type": "Point", "coordinates": [4.0, 52.0, 10.0]}
```

## Code Style and Conventions

### Formatting

-   **Formatter**: Ruff (`ruff format`)
-   **Linter**: Ruff (`ruff check`)
-   **Type checker**: mypy
-   **Indentation**: 4 spaces (2 for YAML)
-   **Line endings**: LF
-   **Max line length**: Not enforced (E501 ignored)

Running formatting and linting:

```bash
# Format code
ruff format .

# Lint and auto-fix
ruff check --fix .

# Lint with unsafe fixes
ruff check --fix --unsafe-fixes .

# Type check
mypy src/
```

### Ruff Rules Enabled

-   **ALL rules enabled** (`select = ["ALL"]`)
-   Specific ignores:
    -   `COM812`: missing-trailing-comma (handled by formatter)
    -   `D102`, `D105`, `D107`: undocumented methods/magic/init
    -   `E501`: line-too-long (handled by formatter)
    -   `PLC2401`: non-ascii-name
    -   `S101`: assert (for non-test files)
    -   `SLF001`: private-member-access
-   Google-style docstrings required
-   Per-file ignores for `__init__.py`, `docs/conf.py`, and test files

### Type Annotations

-   All public methods and attributes are fully typed
-   Use `from __future__ import annotations` for forward references
-   Use `| None` syntax (Python 3.10+ style via `__future__`)
-   Package is PEP 561 compliant (`py.typed` marker present)

### Docstrings

-   Google-style docstrings
-   Module-level docstrings describe the module's purpose
-   Class docstrings include `Args:` section for constructor parameters
-   Attribute docstrings use `#:` comment syntax for Sphinx

### Naming Conventions

-   GPX XML tag names preserved as field names (e.g., `lat`, `lon`, `ele`, `cmt`, `wpt`, `trk`, `rte`)
-   Aliases provided for readability (e.g., `waypoints` for `wpt`, `tracks` for `trk`)
-   Private attributes prefixed with `_` (e.g., `_tag`, `_points_with_ele`)

## Pre-commit Hooks

The project uses these pre-commit hooks:

-   `check-json`, `check-toml`, `check-xml`, `check-yaml`
-   `end-of-file-fixer`, `trailing-whitespace`
-   `validate-pyproject` (with schema store)
-   `check-github-workflows`, `check-readthedocs`
-   `ruff-check` (with auto-fix, unsafe fixes, and show fixes)
-   `ruff-format` (replaces black)
-   `mypy`
-   `codespell`

Run pre-commit manually:

```bash
pre-commit run --all-files
```

## Testing

```bash
# Run tests with pytest
pytest

# Run specific test files
pytest tests/test_gpx.py
pytest tests/smoke_test.py

# Install test dependencies
pip install -e ".[tests]"
# Or with uv
uv sync --group tests
```

The test suite includes:

-   Unit tests for all modules (`test_*.py`)
-   Comprehensive smoke tests (`smoke_test.py`) that validate:
    -   Package installation
    -   Basic GPX reading/writing
    -   Core functionality across the API

## Building Documentation

```bash
# Install docs dependencies
pip install -e ".[docs]"
# Or with uv
uv sync --group docs

# Build docs
cd docs
make html

# Or use auto-rebuild
sphinx-autobuild . _build/html
```

Documentation uses:

-   Sphinx with MyST-Parser (Markdown)
-   Furo theme
-   sphinx-copybutton
-   sphinxext-opengraph

## Publishing

Package is published to PyPI via GitHub Actions on tag push:

1. Push a tag starting with `v` (e.g., `v2025.1.0`)
2. GitHub Actions workflow automatically:
    - Installs uv
    - Builds the package with `uv build`
    - Runs smoke tests on both wheel and source distribution
    - Publishes to PyPI with `uv publish` (using trusted publishing)

## Development Workflow

### Pre-commit Configuration

The project uses pre-commit.ci for automated checks on pull requests. Configuration is managed via `.pre-commit-config.yaml` with monthly auto-updates.

### Typical Development Cycle

1. **Make changes** to the codebase
2. **Run pre-commit** to check formatting and linting:
   ```bash
   pre-commit run --all-files
   ```
3. **Run tests** to ensure nothing breaks:
   ```bash
   pytest
   ```
4. **Run type checks**:
   ```bash
   mypy src/
   ```
5. **Build and test** the package locally:
   ```bash
   uv build
   uv run --isolated --no-project --with dist/*.whl tests/smoke_test.py
   ```

### Version Numbering

The project uses calendar versioning (CalVer) in the format `YYYY.MINOR.MICRO` (e.g., `2025.1.0`).

## Change Management Requirements

**CRITICAL**: For every change to the codebase, the following conditions MUST be met before the change is considered complete:

### 1. Tests

-   **Add missing tests**: If your change introduces new functionality or modifies existing behavior, add corresponding tests to the test suite
-   **All tests must pass**: Run the full test suite and ensure all tests pass:
    ```bash
    uv run pytest
    ```
-   Test files should be placed in `tests/` and follow the naming convention `test_*.py`
-   Use fixtures from `tests/conftest.py` where appropriate
-   Ensure tests cover edge cases, error handling, and the happy path

### 2. Pre-commit Hooks

-   **All pre-commit checks must pass**: Run pre-commit hooks and fix any issues:
    ```bash
    uv run pre-commit run --all-files
    ```
-   This includes:
    -   Code formatting (Ruff)
    -   Linting (Ruff)
    -   Type checking (mypy)
    -   YAML/TOML/JSON validation
    -   Trailing whitespace and end-of-file fixes
    -   Codespell checks
-   Do not skip hooks or commit with `--no-verify` unless absolutely necessary and explicitly requested

### 3. API Reference Documentation

-   **Add new modules to API docs**: If you create a new module in `src/gpx/`, add it to the API reference in `docs/api.md`
-   Follow the existing format:
    ```markdown
    ## `gpx.module_name` Module

    ```{eval-rst}
    .. automodule:: gpx.module_name
        :members:
    ```
    ```
-   Place new module documentation in alphabetical order or logical grouping with related modules

### 4. Changelog

-   **Add entry to CHANGELOG.md**: All changes must be documented in the changelog under the `[Unreleased]` section
-   Follow the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format with these categories:
    -   `Added`: New features
    -   `Changed`: Changes in existing functionality
    -   `Deprecated`: Soon-to-be removed features
    -   `Removed`: Removed features
    -   `Fixed`: Bug fixes
    -   `Security`: Security fixes
-   Write clear, user-focused descriptions of changes
-   Include examples or migration notes for breaking changes

### 5. README Updates

-   **Update README.md for user-facing changes**: If your change affects how users interact with the package, update `README.md`
-   This includes:
    -   New public APIs or functions
    -   Changes to existing APIs
    -   New file format support
    -   New conversion methods
    -   Installation or setup changes
-   Keep examples accurate and working
-   Update code snippets to reflect current best practices

### Summary Checklist

Before considering your work complete, verify:

- [ ] All tests pass (`uv run pytest`)
- [ ] All pre-commit hooks pass (`uv run pre-commit run --all-files`)
- [ ] New modules are documented in `docs/api.md`
- [ ] Changes are documented in `CHANGELOG.md` under `[Unreleased]`
- [ ] User-facing changes are reflected in `README.md`

**If any of these conditions are not met, the change is NOT complete.**

## Common Tasks

### Adding a New GPX Element

1. Create new module in `src/gpx/`
2. Use `@dataclass(slots=True)` decorator
3. Inherit from `GPXModel`
4. Define `_tag` class attribute for XML tag name
5. Define fields with type annotations:
   - Required fields (XML attributes): no `| None`
   - Optional fields (XML child elements): with `| None`
   - Use `KW_ONLY` separator to mark optional args as keyword-only if all fields are optional
6. The `from_xml()` and `to_xml()` methods are inherited from `GPXModel`
7. Add custom types to `types.py` if needed
8. Export from `src/gpx/__init__.py`
9. Follow the [Change Management Requirements](#change-management-requirements) checklist:
   - Add tests for the new element
   - Add to API documentation in `docs/api.md`
   - Add entry to `CHANGELOG.md`
   - Update `README.md` if user-facing

Example dataclass model:

```python
from __future__ import annotations

from dataclasses import KW_ONLY, dataclass

from .base import GPXModel

@dataclass(slots=True)
class MyElement(GPXModel):
    """My custom GPX element.

    Args:
        required_attr: A required XML attribute.
        optional_elem: An optional XML child element. Defaults to None.

    """

    _tag = "myelem"

    # Required fields (XML attributes)
    required_attr: str
    _: KW_ONLY
    # Optional fields (XML child elements)
    optional_elem: str | None = None
```

### Working with XML Namespaces

-   Default namespace defined in `base.py`: `GPX_NAMESPACE = "http://www.topografix.com/GPX/1/1"`
-   Namespace handling is automatic in `parse_from_xml()` and `build_to_xml()` utilities
-   Uses XPath prefix approach with `namespaces` parameter for namespace-aware queries
-   Pass custom `nsmap` to `to_xml(nsmap=...)` if needed

### Statistics and Calculations

Waypoint-level calculations are available as methods on the `Waypoint` class:

-   `distance_to(other)`: Distance to another waypoint (Haversine formula)
-   `duration_to(other)`: Time duration to another waypoint
-   `speed_to(other)`: Speed to another waypoint (m/s)
-   `gain_to(other)`: Elevation gain to another waypoint
-   `slope_to(other)`: Slope to another waypoint (percent)
-   `__geo_interface__`: GeoJSON Point geometry representation

Track and route level statistics:

-   `bounds`: Geographic bounding box
-   `total_distance`, `total_duration`
-   `avg_speed`, `max_speed`, `min_speed`
-   `avg_elevation`, `max_elevation`, `min_elevation`
-   `total_ascent`, `total_descent`
-   `speed_profile`, `elevation_profile`

Distance calculations use Haversine formula (spherical earth model).

## Important Notes

-   **Pure Python**: No external dependencies required for core functionality
-   **GPX 1.1 Specification**: Fully compatible with GPX 1.1 (except extensions)
-   **GPX extensions** from other schemas (e.g., Garmin) are not supported and are ignored
-   **XML validation** is not currently implemented (no XSD validation)
-   **XML parsing**: Uses built-in `xml.etree.ElementTree` module (replaced lxml in v2025.1.0)
-   **Coordinates**: Use WGS84 datum
-   **Elevations**: In meters
-   **Timestamps**: UTC (ISO 8601 format)
-   **Field names**: Use exact GPX tag names (e.g., `trkpt`, `trkseg`, `wpt`, `rte`, `trk`) with property aliases for convenience (e.g., `points`, `segments`, `waypoints`, `routes`, `tracks`)
-   **Keyword-only arguments**: Models with all-optional fields use `kw_only=True` for clarity
-   **GeoJSON compatibility**: All geographic models implement `__geo_interface__` for GeoJSON interoperability
