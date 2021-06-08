# PyGPX

PyGPX is a python package that brings support for reading, writing and converting GPX files.

[![PyPI Version][pypi-image]][pypi-url]
[![Build Status][build-image]][build-url]
[![License][license-image]][license-url]

## Installation
### From PyPI
PyGPX is available on [PyPI](https://pypi.org/project/gpx/). Install with `pip` or your package manager of choice:
```bash
python -m pip install --upgrade gpx
```

### From source
If you'd like, you can also install PyGPX from source (with [`flit`](https://flit.readthedocs.io/en/latest/)):
```bash
git clone https://github.com/sgraaf/PyGPX.git
cd PyGPX
python -m pip install flit
python -m flit install --deps production
```

## Contributing
Feel free to submit a PR for any bug fixes, enhancements, etc. For any major / breaking changes, please [open an issue](https://github.com/sgraaf/PyGPX/issues/new/choose) first to discuss the proposed change. Please make sure to add or update any tests as appropriate. Also make sure to follow the [_Black_ code style](https://black.readthedocs.io/en/stable/the_black_code_style.html) and [Conventional Commits specification](https://www.conventionalcommits.org/) for your commit messages!

### License
PyGPX is open-source and licensed under GNU GPL, Version 3.

<!-- Badges -->
[pypi-image]: https://img.shields.io/pypi/v/gpx
[pypi-url]: https://pypi.org/project/gpx/
[build-image]: https://github.com/sgraaf/PyGPX/actions/workflows/build.yml/badge.svg
[build-url]: https://github.com/sgraaf/PyGPX/actions/workflows/build.yml
[license-image]: https://img.shields.io/github/license/sgraaf/PyGPX.svg?color=blue
[license-url]: https://github.com/sgraaf/PyGPX/blob/master/LICENSE
