"""Tests for metadata-related classes: Metadata, Bounds, Link, Person, Email, Copyright."""

from datetime import datetime, timezone

from gpx import GPX, Bounds, Copyright, Email, Link, Metadata, Person
from gpx.types import Latitude, Longitude


class TestMetadataParsing:
    """Tests for parsing metadata from XML."""

    def test_parse_metadata_name(self, gpx_with_metadata_string):
        """Test parsing metadata name."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        assert gpx.metadata.name == "Test GPX File"

    def test_parse_metadata_desc(self, gpx_with_metadata_string):
        """Test parsing metadata description."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        assert gpx.metadata.desc == "A test GPX file for unit testing"

    def test_parse_metadata_time(self, gpx_with_metadata_string):
        """Test parsing metadata time."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        expected = datetime(2023, 6, 15, 10, 0, 0, tzinfo=timezone.utc)
        assert gpx.metadata.time == expected

    def test_parse_metadata_keywords(self, gpx_with_metadata_string):
        """Test parsing metadata keywords."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        assert gpx.metadata.keywords == "test, gpx, example"

    def test_parse_metadata_author(self, gpx_with_metadata_string):
        """Test parsing metadata author."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        assert gpx.metadata.author is not None
        assert gpx.metadata.author.name == "Test Author"

    def test_parse_metadata_copyright(self, gpx_with_metadata_string):
        """Test parsing metadata copyright."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        assert gpx.metadata.copyright is not None
        assert gpx.metadata.copyright.author == "Test Author"

    def test_parse_metadata_links(self, gpx_with_metadata_string):
        """Test parsing metadata links."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        assert gpx.metadata.links is not None
        assert len(gpx.metadata.links) == 1

    def test_parse_metadata_bounds(self, gpx_with_metadata_string):
        """Test parsing metadata bounds."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        assert gpx.metadata.bounds is not None
        assert gpx.metadata.bounds.minlat == Latitude("52.5")


class TestMetadataBuilding:
    """Tests for building metadata XML."""

    def test_build_metadata(self, sample_metadata):
        """Test building metadata XML."""
        element = sample_metadata._build()
        assert element.tag == "metadata"

    def test_build_metadata_name(self, sample_metadata):
        """Test building metadata with name."""
        element = sample_metadata._build()
        name = element.find("name")
        assert name is not None
        assert name.text == "Test GPX"

    def test_build_metadata_roundtrip(self, gpx_with_metadata_string):
        """Test metadata roundtrip."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        output = gpx.to_string()
        gpx2 = GPX.from_string(output)

        assert gpx2.metadata.name == gpx.metadata.name
        assert gpx2.metadata.desc == gpx.metadata.desc


class TestMetadataCreation:
    """Tests for creating metadata programmatically."""

    def test_create_empty_metadata(self):
        """Test creating empty metadata."""
        meta = Metadata()
        assert meta.name is None
        assert meta.desc is None
        assert meta.author is None
        assert meta.links == []

    def test_create_metadata_with_all_fields(self):
        """Test creating metadata with all fields."""
        meta = Metadata()
        meta.name = "Test"
        meta.desc = "Description"
        meta.time = datetime(2023, 6, 15, 10, 0, 0, tzinfo=timezone.utc)
        meta.keywords = "test, metadata"

        assert meta.name == "Test"
        assert meta.desc == "Description"
        assert meta.keywords == "test, metadata"


class TestBoundsParsing:
    """Tests for parsing bounds from XML."""

    def test_parse_bounds(self, gpx_with_metadata_string):
        """Test parsing bounds."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        bounds = gpx.metadata.bounds
        assert bounds.minlat == Latitude("52.5")
        assert bounds.minlon == Longitude("13.4")
        assert bounds.maxlat == Latitude("52.6")
        assert bounds.maxlon == Longitude("13.5")


class TestBoundsBuilding:
    """Tests for building bounds XML."""

    def test_build_bounds(self, sample_bounds):
        """Test building bounds XML."""
        element = sample_bounds._build()
        assert element.tag == "bounds"
        assert element.get("minlat") == "52.5"
        assert element.get("minlon") == "13.4"
        assert element.get("maxlat") == "52.6"
        assert element.get("maxlon") == "13.5"

    def test_bounds_roundtrip(self, gpx_with_metadata_string):
        """Test bounds roundtrip."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        output = gpx.to_string()
        gpx2 = GPX.from_string(output)

        assert gpx2.metadata.bounds.minlat == gpx.metadata.bounds.minlat
        assert gpx2.metadata.bounds.maxlat == gpx.metadata.bounds.maxlat


class TestBoundsCreation:
    """Tests for creating bounds programmatically."""

    def test_create_bounds(self):
        """Test creating bounds."""
        bounds = Bounds()
        bounds.minlat = Latitude("52.5")
        bounds.minlon = Longitude("13.4")
        bounds.maxlat = Latitude("52.6")
        bounds.maxlon = Longitude("13.5")

        assert bounds.minlat == Latitude("52.5")
        assert bounds.maxlat == Latitude("52.6")


class TestLinkParsing:
    """Tests for parsing links from XML."""

    def test_parse_link_href(self, gpx_with_metadata_string):
        """Test parsing link href."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        link = gpx.metadata.links[0]
        assert link.href == "https://example.com/gpx"

    def test_parse_link_text(self, gpx_with_metadata_string):
        """Test parsing link text."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        link = gpx.metadata.links[0]
        assert link.text == "GPX File Link"

    def test_parse_link_type(self, gpx_with_metadata_string):
        """Test parsing link type."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        link = gpx.metadata.links[0]
        assert link.type == "text/html"


class TestLinkBuilding:
    """Tests for building link XML."""

    def test_build_link(self, sample_link):
        """Test building link XML."""
        element = sample_link._build()
        assert element.tag == "link"
        assert element.get("href") == "https://example.com"

    def test_build_link_text(self, sample_link):
        """Test building link with text."""
        element = sample_link._build()
        text = element.find("text")
        assert text is not None
        assert text.text == "Example Link"

    def test_link_roundtrip(self, gpx_with_metadata_string):
        """Test link roundtrip."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        output = gpx.to_string()
        gpx2 = GPX.from_string(output)

        assert gpx2.metadata.links[0].href == gpx.metadata.links[0].href


class TestLinkCreation:
    """Tests for creating links programmatically."""

    def test_create_link(self):
        """Test creating link."""
        link = Link()
        link.href = "https://example.com"
        link.text = "Example"
        link.type = "text/html"

        assert link.href == "https://example.com"
        assert link.text == "Example"
        assert link.type == "text/html"


class TestPersonParsing:
    """Tests for parsing person from XML."""

    def test_parse_person_name(self, gpx_with_metadata_string):
        """Test parsing person name."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        person = gpx.metadata.author
        assert person.name == "Test Author"

    def test_parse_person_email(self, gpx_with_metadata_string):
        """Test parsing person email."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        person = gpx.metadata.author
        assert person.email is not None
        assert person.email.id == "test"
        assert person.email.domain == "example.com"

    def test_parse_person_link(self, gpx_with_metadata_string):
        """Test parsing person link."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        person = gpx.metadata.author
        assert person.link is not None
        assert person.link.href == "https://example.com"


class TestPersonBuilding:
    """Tests for building person XML."""

    def test_build_person(self, sample_person):
        """Test building person XML."""
        element = sample_person._build()
        # Default tag is "person", but when built from metadata it uses "author"
        assert element.tag == "person"

    def test_build_person_as_author(self, sample_person):
        """Test building person XML with author tag (as used in metadata)."""
        element = sample_person._build("author")
        assert element.tag == "author"

    def test_build_person_name(self, sample_person):
        """Test building person with name."""
        element = sample_person._build()
        name = element.find("name")
        assert name is not None
        assert name.text == "Test Author"

    def test_person_roundtrip(self, gpx_with_metadata_string):
        """Test person roundtrip."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        output = gpx.to_string()
        gpx2 = GPX.from_string(output)

        assert gpx2.metadata.author.name == gpx.metadata.author.name


class TestPersonCreation:
    """Tests for creating person programmatically."""

    def test_create_person(self):
        """Test creating person."""
        person = Person()
        person.name = "John Doe"

        assert person.name == "John Doe"

    def test_create_person_with_email(self):
        """Test creating person with email."""
        email = Email()
        email.id = "john"
        email.domain = "example.com"

        person = Person()
        person.name = "John Doe"
        person.email = email

        assert person.email.id == "john"


class TestEmailParsing:
    """Tests for parsing email from XML."""

    def test_parse_email(self, gpx_with_metadata_string):
        """Test parsing email."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        email = gpx.metadata.author.email
        assert email.id == "test"
        assert email.domain == "example.com"


class TestEmailBuilding:
    """Tests for building email XML."""

    def test_build_email(self):
        """Test building email XML."""
        email = Email()
        email.id = "test"
        email.domain = "example.com"

        element = email._build()
        assert element.tag == "email"
        assert element.get("id") == "test"
        assert element.get("domain") == "example.com"


class TestEmailCreation:
    """Tests for creating email programmatically."""

    def test_create_email(self):
        """Test creating email."""
        email = Email()
        email.id = "john"
        email.domain = "example.com"

        assert email.id == "john"
        assert email.domain == "example.com"


class TestCopyrightParsing:
    """Tests for parsing copyright from XML."""

    def test_parse_copyright_author(self, gpx_with_metadata_string):
        """Test parsing copyright author."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        copyright = gpx.metadata.copyright
        assert copyright.author == "Test Author"

    def test_parse_copyright_year(self, gpx_with_metadata_string):
        """Test parsing copyright year."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        copyright = gpx.metadata.copyright
        assert copyright.year == 2023

    def test_parse_copyright_license(self, gpx_with_metadata_string):
        """Test parsing copyright license."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        copyright = gpx.metadata.copyright
        assert copyright.license == "https://creativecommons.org/licenses/by/4.0/"


class TestCopyrightBuilding:
    """Tests for building copyright XML."""

    def test_build_copyright(self):
        """Test building copyright XML."""
        copyright = Copyright()
        copyright.author = "Test Author"
        copyright.year = 2023
        copyright.license = "https://example.com/license"

        element = copyright._build()
        assert element.tag == "copyright"
        assert element.get("author") == "Test Author"

    def test_copyright_roundtrip(self, gpx_with_metadata_string):
        """Test copyright roundtrip."""
        gpx = GPX.from_string(gpx_with_metadata_string)
        output = gpx.to_string()
        gpx2 = GPX.from_string(output)

        assert gpx2.metadata.copyright.author == gpx.metadata.copyright.author
        assert gpx2.metadata.copyright.year == gpx.metadata.copyright.year


class TestCopyrightCreation:
    """Tests for creating copyright programmatically."""

    def test_create_copyright(self):
        """Test creating copyright."""
        copyright = Copyright()
        copyright.author = "Test Author"
        copyright.year = 2023
        copyright.license = "MIT"

        assert copyright.author == "Test Author"
        assert copyright.year == 2023
        assert copyright.license == "MIT"
