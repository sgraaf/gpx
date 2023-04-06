# Changelog

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
