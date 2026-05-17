"""Tests for gpx.base module."""

import pytest

import gpx
from gpx import (
    GPX,
    Bounds,
    Copyright,
    Email,
    Extensions,
    GeoGPXModel,
    GPXModel,
    Link,
    Metadata,
    Person,
    Route,
    Track,
    TrackSegment,
    Waypoint,
)


class TestGeoGPXModelExport:
    """Tests that GeoGPXModel is part of the public API."""

    def test_importable_from_package(self) -> None:
        """GeoGPXModel is importable from the top-level package."""
        assert GeoGPXModel is gpx.GeoGPXModel

    def test_listed_in_all(self) -> None:
        """GeoGPXModel is listed in the package's __all__."""
        assert "GeoGPXModel" in gpx.__all__

    def test_subclass_of_gpx_model(self) -> None:
        """GeoGPXModel is a subclass of GPXModel."""
        assert issubclass(GeoGPXModel, GPXModel)


class TestGeometricModelsAreGeoGPXModel:
    """Tests that all geometric models inherit from GeoGPXModel."""

    @pytest.fixture
    def geometric_instances(
        self,
        sample_waypoint: Waypoint,
        sample_bounds: Bounds,
        sample_track_segment: TrackSegment,
        sample_route: Route,
        sample_track: Track,
    ) -> list[GeoGPXModel]:
        """All geometric model instances."""
        return [
            sample_waypoint,
            sample_bounds,
            sample_track_segment,
            sample_route,
            sample_track,
            GPX(),
        ]

    def test_isinstance_geo_gpx_model(
        self, geometric_instances: list[GeoGPXModel]
    ) -> None:
        """Every geometric instance is a GeoGPXModel."""
        for instance in geometric_instances:
            assert isinstance(instance, GeoGPXModel)

    def test_isinstance_gpx_model(self, geometric_instances: list[GeoGPXModel]) -> None:
        """Every geometric instance is also a GPXModel."""
        for instance in geometric_instances:
            assert isinstance(instance, GPXModel)

    def test_exposes_geo_interface(
        self, geometric_instances: list[GeoGPXModel]
    ) -> None:
        """Every geometric instance exposes a dict-typed __geo_interface__."""
        for instance in geometric_instances:
            geo = instance.__geo_interface__
            assert isinstance(geo, dict)
            assert "type" in geo


class TestNonGeometricModelsAreNotGeoGPXModel:
    """Tests that non-geometric models do not inherit from GeoGPXModel."""

    def test_metadata_is_not_geo(self, sample_metadata: Metadata) -> None:
        """Metadata is a GPXModel but not a GeoGPXModel."""
        assert isinstance(sample_metadata, GPXModel)
        assert not isinstance(sample_metadata, GeoGPXModel)

    def test_link_is_not_geo(self, sample_link: Link) -> None:
        """Link is a GPXModel but not a GeoGPXModel."""
        assert isinstance(sample_link, GPXModel)
        assert not isinstance(sample_link, GeoGPXModel)

    def test_person_is_not_geo(self, sample_person: Person) -> None:
        """Person is a GPXModel but not a GeoGPXModel."""
        assert isinstance(sample_person, GPXModel)
        assert not isinstance(sample_person, GeoGPXModel)

    def test_email_is_not_geo(self) -> None:
        """Email is a GPXModel but not a GeoGPXModel."""
        email = Email(id="test", domain="example.com")
        assert isinstance(email, GPXModel)
        assert not isinstance(email, GeoGPXModel)

    def test_copyright_is_not_geo(self) -> None:
        """Copyright is a GPXModel but not a GeoGPXModel."""
        copyright_ = Copyright(author="Author")
        assert isinstance(copyright_, GPXModel)
        assert not isinstance(copyright_, GeoGPXModel)

    def test_extensions_is_not_geo(self) -> None:
        """Extensions is not a GeoGPXModel."""
        extensions = Extensions(elements=[])
        assert not isinstance(extensions, GeoGPXModel)


class TestGeoGPXModelAbstractness:
    """Tests that GeoGPXModel enforces its __geo_interface__ contract."""

    def test_bare_subclass_is_not_instantiable(self) -> None:
        """A subclass that does not implement __geo_interface__ cannot be instantiated."""

        class Incomplete(GeoGPXModel):
            _tag = "incomplete"

        with pytest.raises(TypeError, match="abstract"):
            Incomplete()  # type: ignore[abstract] # pyrefly: ignore

    def test_subclass_with_geo_interface_is_instantiable(self) -> None:
        """A subclass that implements __geo_interface__ can be instantiated."""

        class Complete(GeoGPXModel):
            _tag = "complete"

            @property
            def __geo_interface__(self) -> dict:  # type: ignore[override]
                return {"type": "Point", "coordinates": [0.0, 0.0]}

        instance = Complete()
        assert isinstance(instance, GeoGPXModel)
        assert instance.__geo_interface__["type"] == "Point"
