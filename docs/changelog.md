# Changelog

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
