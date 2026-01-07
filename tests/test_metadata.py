"""Tests for metadata-related classes: Metadata, Bounds, Link, Person, Email, Copyright."""

import datetime as dt

from gpx import Bounds, Copyright, Email, Link, Metadata, Person, from_string
from gpx.types import Latitude, Longitude

#: GPX 1.1 namespace
GPX_NAMESPACE = "http://www.topografix.com/GPX/1/1"


class TestMetadataParsing:
    """Tests for parsing metadata from XML."""

    def test_parse_metadata_name(self, gpx_with_metadata_string: str) -> None:
        """Test parsing metadata name."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        assert gpx.metadata.name == "Test GPX File"

    def test_parse_metadata_desc(self, gpx_with_metadata_string: str) -> None:
        """Test parsing metadata description."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        assert gpx.metadata.desc == "A test GPX file for unit testing"

    def test_parse_metadata_time(self, gpx_with_metadata_string: str) -> None:
        """Test parsing metadata time."""
        gpx = from_string(gpx_with_metadata_string)
        expected = dt.datetime(2023, 6, 15, 10, 0, 0, tzinfo=dt.UTC)
        assert gpx.metadata is not None
        assert gpx.metadata.time == expected

    def test_parse_metadata_keywords(self, gpx_with_metadata_string: str) -> None:
        """Test parsing metadata keywords."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        assert gpx.metadata.keywords == "test, gpx, example"

    def test_parse_metadata_author(self, gpx_with_metadata_string: str) -> None:
        """Test parsing metadata author."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        assert gpx.metadata.author is not None
        assert gpx.metadata is not None
        assert gpx.metadata.author.name == "Test Author"

    def test_parse_metadata_copyright(self, gpx_with_metadata_string: str) -> None:
        """Test parsing metadata copyright."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        assert gpx.metadata.copyright is not None
        assert gpx.metadata is not None
        assert gpx.metadata.copyright.author == "Test Author"

    def test_parse_metadata_links(self, gpx_with_metadata_string: str) -> None:
        """Test parsing metadata links."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        assert gpx.metadata.link is not None
        assert len(gpx.metadata.link) == 1

    def test_parse_metadata_bounds(self, gpx_with_metadata_string: str) -> None:
        """Test parsing metadata bounds."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        assert gpx.metadata.bounds is not None
        assert gpx.metadata is not None
        assert gpx.metadata.bounds.minlat == Latitude("52.5")


class TestMetadataBuilding:
    """Tests for building metadata XML."""

    def test_build_metadata(self, sample_metadata: Metadata) -> None:
        """Test building metadata XML."""
        element = sample_metadata.to_xml()
        assert element.tag.endswith("}metadata")

    def test_build_metadata_name(self, sample_metadata: Metadata) -> None:
        """Test building metadata with name."""

        element = sample_metadata.to_xml()
        name = element.find(f"{{{GPX_NAMESPACE}}}name")
        assert name is not None
        assert name.text == "Test GPX"

    def test_build_metadata_roundtrip(self, gpx_with_metadata_string: str) -> None:
        """Test metadata roundtrip."""
        gpx = from_string(gpx_with_metadata_string)
        output = gpx.to_string()
        gpx2 = from_string(output)

        assert gpx.metadata is not None
        assert gpx2.metadata is not None
        assert gpx2.metadata.name == gpx.metadata.name
        assert gpx2.metadata.desc == gpx.metadata.desc


class TestMetadataCreation:
    """Tests for creating metadata programmatically."""

    def test_create_empty_metadata(self) -> None:
        """Test creating empty metadata."""
        meta = Metadata()
        assert meta.name is None
        assert meta.desc is None
        assert meta.author is None
        assert meta.link == []

    def test_create_metadata_with_all_fields(self) -> None:
        """Test creating metadata with all fields."""
        meta = Metadata(
            name="Test",
            desc="Description",
            time=dt.datetime(2023, 6, 15, 10, 0, 0, tzinfo=dt.UTC),
            keywords="test, metadata",
        )

        assert meta.name == "Test"
        assert meta.desc == "Description"
        assert meta.keywords == "test, metadata"


class TestBoundsParsing:
    """Tests for parsing bounds from XML."""

    def test_parse_bounds(self, gpx_with_metadata_string: str) -> None:
        """Test parsing bounds."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        bounds = gpx.metadata.bounds
        assert bounds is not None
        assert bounds.minlat == Latitude("52.5")
        assert bounds.minlon == Longitude("13.4")
        assert bounds.maxlat == Latitude("52.6")
        assert bounds.maxlon == Longitude("13.5")


class TestBoundsBuilding:
    """Tests for building bounds XML."""

    def test_build_bounds(self, sample_bounds: Bounds) -> None:
        """Test building bounds XML."""
        element = sample_bounds.to_xml()
        assert element.tag.endswith("}bounds")
        assert element.get("minlat") == "52.5"
        assert element.get("minlon") == "13.4"
        assert element.get("maxlat") == "52.6"
        assert element.get("maxlon") == "13.5"

    def test_bounds_roundtrip(self, gpx_with_metadata_string: str) -> None:
        """Test bounds roundtrip."""
        gpx = from_string(gpx_with_metadata_string)
        output = gpx.to_string()
        gpx2 = from_string(output)

        assert gpx.metadata is not None
        assert gpx.metadata.bounds is not None
        assert gpx2.metadata is not None
        assert gpx2.metadata.bounds is not None
        assert gpx2.metadata.bounds.minlat == gpx.metadata.bounds.minlat
        assert gpx2.metadata.bounds.maxlat == gpx.metadata.bounds.maxlat


class TestBoundsCreation:
    """Tests for creating bounds programmatically."""

    def test_create_bounds(self) -> None:
        """Test creating bounds."""
        bounds = Bounds(
            minlat=Latitude("52.5"),
            minlon=Longitude("13.4"),
            maxlat=Latitude("52.6"),
            maxlon=Longitude("13.5"),
        )

        assert bounds.minlat == Latitude("52.5")
        assert bounds.maxlat == Latitude("52.6")


class TestLinkParsing:
    """Tests for parsing links from XML."""

    def test_parse_link_href(self, gpx_with_metadata_string: str) -> None:
        """Test parsing link href."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        link = gpx.metadata.link[0]
        assert link.href == "https://example.com/gpx"

    def test_parse_link_text(self, gpx_with_metadata_string: str) -> None:
        """Test parsing link text."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        link = gpx.metadata.link[0]
        assert link.text == "GPX File Link"

    def test_parse_link_type(self, gpx_with_metadata_string: str) -> None:
        """Test parsing link type."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        link = gpx.metadata.link[0]
        assert link.type == "text/html"


class TestLinkBuilding:
    """Tests for building link XML."""

    def test_build_link(self, sample_link: Link) -> None:
        """Test building link XML."""
        element = sample_link.to_xml()
        assert element.tag.endswith("}link")
        assert element.get("href") == "https://example.com"

    def test_build_link_text(self, sample_link: Link) -> None:
        """Test building link with text."""

        element = sample_link.to_xml()
        text = element.find(f"{{{GPX_NAMESPACE}}}text")
        assert text is not None
        assert text.text == "Example Link"

    def test_link_roundtrip(self, gpx_with_metadata_string: str) -> None:
        """Test link roundtrip."""
        gpx = from_string(gpx_with_metadata_string)
        output = gpx.to_string()
        gpx2 = from_string(output)

        assert gpx.metadata is not None
        assert gpx2.metadata is not None
        assert gpx2.metadata.link[0].href == gpx.metadata.link[0].href


class TestLinkCreation:
    """Tests for creating links programmatically."""

    def test_create_link(self) -> None:
        """Test creating link."""
        link = Link(
            href="https://example.com",
            text="Example",
            type="text/html",
        )

        assert link.href == "https://example.com"
        assert link.text == "Example"
        assert link.type == "text/html"


class TestPersonParsing:
    """Tests for parsing person from XML."""

    def test_parse_person_name(self, gpx_with_metadata_string: str) -> None:
        """Test parsing person name."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        person = gpx.metadata.author
        assert person is not None
        assert person.name == "Test Author"

    def test_parse_person_email(self, gpx_with_metadata_string: str) -> None:
        """Test parsing person email."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        person = gpx.metadata.author
        assert person is not None
        assert person.email is not None
        assert person.email.id == "test"
        assert person.email.domain == "example.com"

    def test_parse_person_link(self, gpx_with_metadata_string: str) -> None:
        """Test parsing person link."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        person = gpx.metadata.author
        assert person is not None
        assert person.link is not None
        assert person.link.href == "https://example.com"


class TestPersonBuilding:
    """Tests for building person XML."""

    def test_build_person(self, sample_person: Person) -> None:
        """Test building person XML."""
        element = sample_person.to_xml()
        # Default tag is "author"
        assert element.tag.endswith("}author")

    def test_build_person_as_author(self, sample_person: Person) -> None:
        """Test building person XML with author tag (as used in metadata)."""
        element = sample_person.to_xml()
        assert element.tag.endswith("}author")

    def test_build_person_name(self, sample_person: Person) -> None:
        """Test building person with name."""

        element = sample_person.to_xml()
        name = element.find(f"{{{GPX_NAMESPACE}}}name")
        assert name is not None
        assert name.text == "Test Author"

    def test_person_roundtrip(self, gpx_with_metadata_string: str) -> None:
        """Test person roundtrip."""
        gpx = from_string(gpx_with_metadata_string)
        output = gpx.to_string()
        gpx2 = from_string(output)

        assert gpx.metadata is not None
        assert gpx.metadata.author is not None
        assert gpx2.metadata is not None
        assert gpx2.metadata.author is not None
        assert gpx2.metadata.author.name == gpx.metadata.author.name


class TestPersonCreation:
    """Tests for creating person programmatically."""

    def test_create_person(self) -> None:
        """Test creating person."""
        person = Person(name="John Doe")

        assert person.name == "John Doe"

    def test_create_person_with_email(self) -> None:
        """Test creating person with email."""
        email = Email(id="john", domain="example.com")

        person = Person(name="John Doe", email=email)

        assert person.email is not None
        assert person.email.id == "john"


class TestEmailParsing:
    """Tests for parsing email from XML."""

    def test_parse_email(self, gpx_with_metadata_string: str) -> None:
        """Test parsing email."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        assert gpx.metadata.author is not None
        email = gpx.metadata.author.email
        assert email is not None
        assert email.id == "test"
        assert email.domain == "example.com"


class TestEmailBuilding:
    """Tests for building email XML."""

    def test_build_email(self) -> None:
        """Test building email XML."""
        email = Email(id="test", domain="example.com")

        element = email.to_xml()
        assert element.tag.endswith("}email")
        assert element.get("id") == "test"
        assert element.get("domain") == "example.com"


class TestEmailCreation:
    """Tests for creating email programmatically."""

    def test_create_email(self) -> None:
        """Test creating email."""
        email = Email(id="john", domain="example.com")

        assert email.id == "john"
        assert email.domain == "example.com"


class TestCopyrightParsing:
    """Tests for parsing copyright from XML."""

    def test_parse_copyright_author(self, gpx_with_metadata_string: str) -> None:
        """Test parsing copyright author."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        copyright_ = gpx.metadata.copyright
        assert copyright_ is not None
        assert copyright_.author == "Test Author"

    def test_parse_copyright_year(self, gpx_with_metadata_string: str) -> None:
        """Test parsing copyright year."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        copyright_ = gpx.metadata.copyright
        assert copyright_ is not None
        assert copyright_.year == 2023

    def test_parse_copyright_license(self, gpx_with_metadata_string: str) -> None:
        """Test parsing copyright license."""
        gpx = from_string(gpx_with_metadata_string)
        assert gpx.metadata is not None
        copyright_ = gpx.metadata.copyright
        assert copyright_ is not None
        assert copyright_.license == "https://creativecommons.org/licenses/by/4.0/"


class TestCopyrightBuilding:
    """Tests for building copyright XML."""

    def test_build_copyright(self) -> None:
        """Test building copyright XML."""
        copyright_ = Copyright(
            author="Test Author",
            year=2023,
            license="https://example.com/license",
        )

        element = copyright_.to_xml()
        assert element.tag.endswith("}copyright")
        assert element.get("author") == "Test Author"

    def test_copyright_roundtrip(self, gpx_with_metadata_string: str) -> None:
        """Test copyright roundtrip."""
        gpx = from_string(gpx_with_metadata_string)
        output = gpx.to_string()
        gpx2 = from_string(output)

        assert gpx.metadata is not None
        assert gpx.metadata.copyright is not None
        assert gpx2.metadata is not None
        assert gpx2.metadata.copyright is not None
        assert gpx2.metadata.copyright.author == gpx.metadata.copyright.author
        assert gpx2.metadata.copyright.year == gpx.metadata.copyright.year


class TestCopyrightCreation:
    """Tests for creating copyright programmatically."""

    def test_create_copyright(self) -> None:
        """Test creating copyright."""
        copyright_ = Copyright(
            author="Test Author",
            year=2023,
            license="MIT",
        )

        assert copyright_.author == "Test Author"
        assert copyright_.year == 2023
        assert copyright_.license == "MIT"
