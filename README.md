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

If you'd like, you can also install PyGPX from source (with [`flit`](https://flit.readthedocs.io/en/latest/)):

```bash
git clone https://github.com/sgraaf/gpx.git
cd gpx
python3 -m pip install flit
flit install
```

<!-- end docs-include-installation -->

## Documentation

Check out the [PyGPX documentation](https://gpx.readthedocs.io/en/stable/) for the [User's Guide](https://gpx.readthedocs.io/en/stable/usage.html) and [API Reference](https://gpx.readthedocs.io/en/stable/api.html).

## Usage

<!-- start docs-include-usage -->

### Reading a GPX file

```python
>>> from gpx import GPX
>>> # read the GPX data from file
>>> gpx = GPX.from_file("path/to/file.gpx")
>>> # print the bounds of the GPX data
>>> print(gpx.bounds)
```

### Manipulating GPX data

```python
>>> from gpx import Waypoint
>>>
>>> # delete the last waypoint
>>> del gpx.waypoints[-1]
>>>
>>> # add a new waypoint
>>> wpt = Waypoint()
>>> wpt.latitude = 52.123
>>> wpt.longitude = 4.123
>>> gpx.waypoints.append(wpt)
```

### Writing a GPX file

```python
>>> # write the GPX data to a file
>>> gpx.to_file("path/to/file.gpx")
```

<!-- end docs-include-usage -->
