# CLAUDE.md

This file provides guidance for AI assistants working with the PyGPX codebase.

## Project Overview

PyGPX is a Python library for reading, writing, and converting GPX (GPS Exchange Format) files. It provides a fully-typed, object-oriented interface for working with GPX 1.1 specification data.

-   **Package name**: `gpx` (on PyPI)
-   **Current version**: 0.2.1
-   **Python support**: 3.10+
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
├── pyproject.toml        # Project configuration and dependencies
└── .pre-commit-config.yaml
```

## Key Dependencies

-   **lxml**: XML parsing and building
-   **python-dateutil**: ISO 8601 datetime parsing

## Development Setup

```bash
# Install from source with flit
pip install flit
flit install

# Install with dev dependencies
pip install -e ".[dev]"

# Install with test dependencies
pip install -e ".[tests]"
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

Reading GPX files:

```python
from gpx import GPX
gpx = GPX.from_file("path/to/file.gpx")
gpx = GPX.from_string(gpx_string, validate=True)
```

Writing GPX files:

```python
gpx.to_file("output.gpx")
gpx_string = gpx.to_string()
```

## Code Style and Conventions

### Formatting

-   **Formatter**: Black
-   **Linter**: Ruff
-   **Type checker**: mypy
-   **Indentation**: 4 spaces (2 for YAML)
-   **Line endings**: LF
-   **Max line length**: Not enforced (E501 ignored)

### Ruff Rules Enabled

-   `B`: flake8-bugbear
-   `C90`: mccabe complexity
-   `E`, `W`: pycodestyle
-   `F`: pyflakes
-   `I`: isort
-   `UP`: pyupgrade
-   `RUF100`: unused noqa

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
-   `validate-pyproject`
-   `check-github-workflows`, `check-readthedocs`
-   `ruff` (with auto-fix)
-   `black`
-   `mypy` (with `types-python-dateutil`)
-   `codespell`
-   `prettier` (for non-Python files)

Run pre-commit manually:

```bash
pre-commit run --all-files
```

## Testing

```bash
# Run tests with pytest
pytest

# Install test dependencies
pip install -e ".[tests]"
```

## Building Documentation

```bash
# Install docs dependencies
pip install -e ".[docs]"

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

Package is published to PyPI via GitHub Actions on release:

1. Create a GitHub release
2. Workflow builds and publishes using Flit

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
