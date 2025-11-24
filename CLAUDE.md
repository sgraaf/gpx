# CLAUDE.md

This file provides guidance for AI assistants working with the PyGPX codebase.

## Project Overview

PyGPX is a Python library for reading, writing, and converting GPX (GPS Exchange Format) files. It provides a fully-typed, object-oriented interface for working with GPX 1.1 specification data.

-   **Package name**: `gpx` (on PyPI)
-   **Current version**: 2025.1.0
-   **Python support**: 3.10+ (including 3.14)
-   **License**: GPL-3.0+
-   **Documentation**: https://gpx.readthedocs.io/

## Repository Structure

```
gpx/
├── src/gpx/              # Main source code (src layout)
│   ├── __init__.py       # Package exports and version
│   ├── gpx.py            # Main GPX class - entry point for reading/writing files
│   ├── element.py        # Base Element class for all GPX elements
│   ├── waypoint.py       # Waypoint class with coordinates and metadata
│   ├── track.py          # Track class (ordered list of track segments)
│   ├── track_segment.py  # TrackSegment class (list of track points)
│   ├── route.py          # Route class (ordered waypoints to destination)
│   ├── metadata.py       # Metadata class for GPX file information
│   ├── bounds.py         # Bounds class for geographic boundaries
│   ├── link.py           # Link class for external references
│   ├── person.py         # Person class for author information
│   ├── email.py          # Email class
│   ├── copyright.py      # Copyright class
│   ├── types.py          # Custom types: Latitude, Longitude, Degrees, Fix, DGPSStation
│   ├── mixins.py         # Mixin classes for statistics and sequence behavior
│   ├── errors.py         # Custom exceptions: InvalidGPXError, ParseError
│   ├── utils.py          # Utility functions
│   ├── gpx.xsd           # GPX 1.1 XML schema for validation
│   └── py.typed          # PEP 561 marker for type hints
├── docs/                 # Sphinx documentation (MyST Markdown)
├── tests/                # Test suite
│   ├── conftest.py       # Pytest configuration and fixtures
│   ├── smoke_test.py     # Comprehensive smoke tests
│   └── test_*.py         # Unit tests for each module
├── pyproject.toml        # Project configuration and dependencies
├── uv.lock               # Dependency lock file (managed by uv)
├── .pre-commit-config.yaml  # Pre-commit hooks configuration
├── .readthedocs.yaml     # ReadTheDocs configuration
└── .github/
    └── workflows/
        └── publish.yml   # PyPI publishing workflow
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

## Key Dependencies

-   **lxml**: XML parsing and building
-   **python-dateutil**: ISO 8601 datetime parsing
-   **typing-extensions**: Type hints backports (Python < 3.11 only)

## Development Setup

The project uses **uv** as its build backend and package manager.

```bash
# Install from source with uv
pip install uv
uv sync

# Install with dev dependencies
uv sync --extra dev

# Install with test dependencies
uv sync --extra tests

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

### Class Hierarchy

All GPX element classes inherit from `Element` base class:

```
Element (element.py)
├── GPX (gpx.py) - root element
├── Waypoint (waypoint.py) - wpt/trkpt/rtept elements
├── Track (track.py) - trk element
├── TrackSegment (track_segment.py) - trkseg element
├── Route (route.py) - rte element
├── Metadata (metadata.py)
├── Bounds (bounds.py)
├── Link (link.py)
├── Person (person.py)
├── Email (email.py)
└── Copyright (copyright.py)
```

### Design Patterns

1. **Parse/Build Pattern**: Each element class implements:

    - `_parse()`: Parse XML element to Python attributes
    - `_build()`: Build Python attributes back to XML element

2. **Mixin Classes** (`mixins.py`):

    - `PointsStatisticsMixin`: Provides distance, duration, speed, elevation statistics
    - `PointsMutableSequenceMixin`: Makes point containers behave like lists
    - `AttributesMutableMappingMixin`: Dict-like access to attributes

3. **Custom Types** (`types.py`):
    - `Latitude`, `Longitude`: Validated Decimal subclasses with range checks
    - `Degrees`: For bearing/heading (0-360)
    - `Fix`: GPS fix type enum-like string
    - `DGPSStation`: DGPS station ID (0-1023)

### Entry Points

**Reading GPX files:**

```python
from gpx import GPX

# Read from file
gpx = GPX.from_file("path/to/file.gpx")

# Read from string with validation
gpx = GPX.from_string(gpx_string, validate=True)

# Access basic properties
print(gpx.creator)
print(gpx.version)  # Always "1.1"
print(len(gpx.waypoints))
print(len(gpx.tracks))
print(len(gpx.routes))
```

**Writing GPX files:**

```python
# Write to file
gpx.to_file("output.gpx")

# Convert to string
gpx_string = gpx.to_string()

# Write with pretty printing (default)
gpx.to_file("output.gpx", pretty_print=True)
```

**Creating GPX data:**

```python
from gpx import GPX, Waypoint, Track, TrackSegment, Metadata
from decimal import Decimal
from datetime import datetime, timezone

# Create GPX object
gpx = GPX()
gpx.creator = "My Application v1.0"

# Add metadata
metadata = Metadata()
metadata.name = "Track Name"
metadata.desc = "Description"
metadata.time = datetime.now(timezone.utc)
gpx.metadata = metadata

# Add waypoints
waypoint = Waypoint()
waypoint.lat = Decimal("52.3676")
waypoint.lon = Decimal("4.9041")
waypoint.name = "Amsterdam"
waypoint.ele = Decimal("2.0")
gpx.waypoints.append(waypoint)

# Add tracks with segments
track = Track()
track.name = "My Track"
segment = TrackSegment()

# Add track points
point = Waypoint()  # Track points are also Waypoint objects
point.lat = Decimal("52.0")
point.lon = Decimal("4.0")
point.time = datetime.now(timezone.utc)
segment.points.append(point)

track.segments.append(segment)
gpx.tracks.append(track)
```

**Working with statistics:**

```python
# Get statistics from tracks
track = gpx.tracks[0]
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

-   GPX XML tag names preserved as attribute names (e.g., `lat`, `lon`, `ele`, `cmt`)
-   Aliases provided for readability (e.g., `points` for `rtepts`/`trkpts`)
-   Private attributes prefixed with `_` (e.g., `_element`, `_nsmap`)

## Pre-commit Hooks

The project uses these pre-commit hooks:

-   `check-json`, `check-toml`, `check-xml`, `check-yaml`
-   `end-of-file-fixer`, `trailing-whitespace`
-   `validate-pyproject` (with schema store)
-   `check-github-workflows`, `check-readthedocs`
-   `ruff-check` (with auto-fix, unsafe fixes, and show fixes)
-   `ruff-format` (replaces black)
-   `mypy` (with `types-python-dateutil`)
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
uv sync --extra tests
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
uv sync --extra docs

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

## Common Tasks

### Adding a New GPX Element

1. Create new module in `src/gpx/`
2. Inherit from `Element`
3. Implement `__init__`, `_parse()`, and `_build()` methods
4. Add custom types to `types.py` if needed
5. Export from `__init__.py`
6. Add to documentation

### Working with XML Namespaces

-   Default namespace: `http://www.topografix.com/GPX/1/1`
-   Use `self._nsmap` for namespace-aware XML operations
-   `_filter_nsmap()` removes unused namespaces when building

### Statistics and Calculations

The `PointsStatisticsMixin` provides:

-   `bounds`: Geographic bounding box
-   `total_distance`, `total_duration`
-   `avg_speed`, `max_speed`, `min_speed`
-   `avg_elevation`, `max_elevation`, `min_elevation`
-   `total_ascent`, `total_descent`
-   `speed_profile`, `elevation_profile`

Distance calculations use Haversine formula (spherical earth model).

## Important Notes

-   GPX extensions from other schemas (e.g., Garmin) are not supported and are ignored
-   XML validation against GPX 1.1 XSD is optional (`validate=True`)
-   Coordinates use WGS84 datum
-   Elevations are in meters
-   Timestamps are UTC (ISO 8601 format)
