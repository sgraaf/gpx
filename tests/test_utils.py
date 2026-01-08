"""Tests for gpx.utils module."""

import datetime as dt
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from gpx.link import Link
from gpx.utils import (
    build_geo_properties,
    build_to_xml,
    extract_namespaces_from_string,
    from_isoformat,
    get_inner_type,
    get_list_item_type,
    has_geo_properties,
    is_list_type,
    is_optional,
    parse_from_xml,
    remove_encoding_from_string,
    to_isoformat,
)


class TestRemoveEncodingFromString:
    """Tests for the remove_encoding_from_string utility function."""

    def test_removes_double_quoted_utf8_encoding(self) -> None:
        """Test removal of double-quoted UTF-8 encoding declaration."""
        input_str = '<?xml version="1.0" encoding="UTF-8"?>'
        expected = '<?xml version="1.0" ?>'
        assert remove_encoding_from_string(input_str) == expected

    def test_removes_single_quoted_utf8_encoding(self) -> None:
        """Test removal of single-quoted UTF-8 encoding declaration."""
        input_str = "<?xml version='1.0' encoding='UTF-8'?>"
        expected = "<?xml version='1.0' ?>"
        assert remove_encoding_from_string(input_str) == expected

    def test_removes_lowercase_utf8_encoding(self) -> None:
        """Test removal of lowercase utf-8 encoding declaration."""
        input_str = '<?xml version="1.0" encoding="utf-8"?>'
        expected = '<?xml version="1.0" ?>'
        assert remove_encoding_from_string(input_str) == expected

    def test_removes_iso_8859_encoding(self) -> None:
        """Test removal of ISO-8859-1 encoding declaration."""
        input_str = '<?xml version="1.0" encoding="ISO-8859-1"?>'
        expected = '<?xml version="1.0" ?>'
        assert remove_encoding_from_string(input_str) == expected

    def test_removes_windows_1252_encoding(self) -> None:
        """Test removal of Windows-1252 encoding declaration."""
        input_str = '<?xml version="1.0" encoding="windows-1252"?>'
        expected = '<?xml version="1.0" ?>'
        assert remove_encoding_from_string(input_str) == expected

    def test_no_encoding_returns_unchanged(self) -> None:
        """Test that string without encoding is returned unchanged."""
        input_str = '<?xml version="1.0"?>'
        assert remove_encoding_from_string(input_str) == input_str

    def test_empty_string_returns_empty(self) -> None:
        """Test that empty string returns empty."""
        assert remove_encoding_from_string("") == ""

    def test_preserves_rest_of_xml(self) -> None:
        """Test that the rest of the XML content is preserved."""
        input_str = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="52.5" lon="13.4"/>
</gpx>"""
        result = remove_encoding_from_string(input_str)
        assert "<gpx" in result
        assert '<wpt lat="52.5" lon="13.4"/>' in result
        assert 'encoding="UTF-8"' not in result

    def test_handles_encoding_with_spaces(self) -> None:
        """Test handling of encoding with extra spaces."""
        input_str = '<?xml version="1.0"  encoding="UTF-8" ?>'
        result = remove_encoding_from_string(input_str)
        assert 'encoding="UTF-8"' not in result


class TestNamespaceExtraction:
    """Tests for namespace extraction utilities."""

    def test_extract_namespaces_from_string(self) -> None:
        """Test extracting namespace declarations from XML string."""
        xml_str = '<gpx xmlns="http://www.topografix.com/GPX/1/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"></gpx>'
        namespaces = extract_namespaces_from_string(xml_str)
        assert namespaces[""] == "http://www.topografix.com/GPX/1/1"
        assert namespaces["xsi"] == "http://www.w3.org/2001/XMLSchema-instance"

    def test_extract_namespaces_no_default(self) -> None:
        """Test extracting namespaces without default namespace."""
        xml_str = '<root xmlns:foo="http://example.com/foo"></root>'
        namespaces = extract_namespaces_from_string(xml_str)
        assert "foo" in namespaces
        assert namespaces["foo"] == "http://example.com/foo"

    def test_extract_namespaces_empty_string(self) -> None:
        """Test extracting namespaces from empty string."""
        namespaces = extract_namespaces_from_string("")
        assert namespaces == {}


class TestTypeIntrospection:
    """Tests for type introspection utilities."""

    def test_is_optional_with_optional_type(self) -> None:
        """Test is_optional with Optional type."""
        assert is_optional(int | None) is True  # type: ignore[arg-type]

    def test_is_optional_with_required_type(self) -> None:
        """Test is_optional with required type."""
        assert is_optional(int) is False

    def test_is_optional_with_union_containing_none(self) -> None:
        """Test is_optional with Union containing None."""
        assert is_optional(str | int | None) is True  # type: ignore[arg-type]

    def test_get_inner_type_with_optional(self) -> None:
        """Test get_inner_type with Optional."""
        inner = get_inner_type(str | None)  # type: ignore[arg-type]
        assert inner is str

    def test_get_inner_type_with_union_multiple_non_none(self) -> None:
        """Test get_inner_type with Union of multiple non-None types."""
        union_type = str | int | None  # type: ignore[assignment]
        result = get_inner_type(union_type)  # type: ignore[arg-type]
        # Should keep the union when there are multiple non-None types
        assert result == union_type

    def test_get_inner_type_with_required_type(self) -> None:
        """Test get_inner_type with required type returns same type."""
        assert get_inner_type(int) is int

    def test_is_list_type_with_list(self) -> None:
        """Test is_list_type with list type."""
        assert is_list_type(list[str]) is True

    def test_is_list_type_with_non_list(self) -> None:
        """Test is_list_type with non-list type."""
        assert is_list_type(str) is False

    def test_get_list_item_type_with_typed_list(self) -> None:
        """Test get_list_item_type with typed list."""
        item_type = get_list_item_type(list[int])
        assert item_type is int

    def test_get_list_item_type_with_untyped_list(self) -> None:
        """Test get_list_item_type with untyped list."""
        item_type = get_list_item_type(list)  # type: ignore[arg-type]
        assert item_type is Any


class TestDatetimeFormatting:
    """Tests for datetime formatting utilities."""

    def test_to_isoformat_with_microseconds(self) -> None:
        """Test to_isoformat with microseconds."""
        dt_obj = dt.datetime(2024, 1, 15, 10, 30, 45, 123456, tzinfo=dt.UTC)
        result = to_isoformat(dt_obj)
        assert "2024-01-15T10:30:45.123" in result
        assert result.endswith("Z")

    def test_to_isoformat_without_microseconds(self) -> None:
        """Test to_isoformat without microseconds."""
        dt_obj = dt.datetime(2024, 1, 15, 10, 30, 45, tzinfo=dt.UTC)
        result = to_isoformat(dt_obj)
        assert result == "2024-01-15T10:30:45Z"

    def test_from_isoformat_with_z_suffix(self) -> None:
        """Test from_isoformat with Z suffix."""
        dt_str = "2024-01-15T10:30:45Z"
        dt_obj = from_isoformat(dt_str)
        assert dt_obj.year == 2024
        assert dt_obj.month == 1
        assert dt_obj.day == 15

    def test_from_isoformat_with_milliseconds(self) -> None:
        """Test from_isoformat with milliseconds."""
        dt_str = "2024-01-15T10:30:45.123Z"
        dt_obj = from_isoformat(dt_str)
        assert dt_obj.microsecond == 123000


class TestXMLParsing:
    """Tests for XML parsing utilities."""

    def test_parse_from_xml_with_kw_only_field(self) -> None:
        """Test parse_from_xml skips KW_ONLY marker."""

        @dataclass
        class TestModel:
            """Test model with KW_ONLY."""

            required: str
            _: Any = field(default=None, init=False, repr=False)  # type: ignore[misc]
            optional: str | None = None

        element = ET.fromstring(
            '<test required="value"><optional>opt</optional></test>'
        )
        result = parse_from_xml(TestModel, element)
        assert result["required"] == "value"
        assert result["optional"] == "opt"
        assert "_" not in result

    def test_parse_from_xml_list_with_non_model_items(self) -> None:
        """Test parse_from_xml with list of non-model items."""

        @dataclass
        class TestModel:
            """Test model with list of strings."""

            items: list[str] = field(default_factory=list)

        element = ET.fromstring("<test><items>item1</items><items>item2</items></test>")
        result = parse_from_xml(TestModel, element)
        assert result["items"] == ["item1", "item2"]

    def test_parse_from_xml_optional_child_with_none_text(self) -> None:
        """Test parse_from_xml with optional child that has None text."""

        @dataclass
        class TestModel:
            """Test model."""

            value: str | None = None

        element = ET.fromstring("<test><value></value></test>")
        result = parse_from_xml(TestModel, element)
        assert result["value"] is None

    def test_parse_from_xml_optional_list(self) -> None:
        """Test parse_from_xml with optional list field."""

        @dataclass
        class TestModel:
            """Test model with optional list."""

            items: list[str] | None = None

        element = ET.fromstring("<test><items>item1</items></test>")
        result = parse_from_xml(TestModel, element)
        assert result["items"] == ["item1"]

    def test_build_to_xml_with_nsmap_field(self) -> None:
        """Test build_to_xml skips nsmap field."""

        @dataclass
        class TestModel:
            """Test model with nsmap."""

            value: str
            nsmap: dict[str | None, str] = field(default_factory=dict)

        obj = TestModel(value="test", nsmap={"": "http://example.com"})
        element = ET.Element("test")
        build_to_xml(obj, element)
        # nsmap should not appear as attribute or child
        assert "nsmap" not in element.attrib
        assert len(element.findall("nsmap")) == 0

    def test_build_to_xml_list_with_non_model_items(self) -> None:
        """Test build_to_xml with list of non-model items."""

        @dataclass
        class TestModel:
            """Test model with list of strings."""

            items: list[str] = field(default_factory=list)

        obj = TestModel(items=["item1", "item2"])
        element = ET.Element("test")
        build_to_xml(obj, element)
        items = element.findall("items")
        assert len(items) == 2
        assert items[0].text == "item1"
        assert items[1].text == "item2"

    def test_build_to_xml_optional_list(self) -> None:
        """Test build_to_xml with optional list field."""

        @dataclass
        class TestModel:
            """Test model with optional list."""

            items: list[str] | None = None

        obj = TestModel(items=["item1"])
        element = ET.Element("test")
        build_to_xml(obj, element)
        items = element.findall("items")
        assert len(items) == 1
        assert items[0].text == "item1"


class TestGeoProperties:
    """Tests for GeoJSON properties utilities."""

    def test_has_geo_properties_with_empty_list(self) -> None:
        """Test has_geo_properties returns False for empty lists."""

        @dataclass
        class TestModel:
            """Test model with empty list."""

            items: list[str] = field(default_factory=list)

        obj = TestModel(items=[])
        assert has_geo_properties(obj) is False

    def test_has_geo_properties_with_non_empty_list(self) -> None:
        """Test has_geo_properties returns True for non-empty lists."""

        @dataclass
        class TestModel:
            """Test model with list."""

            items: list[str] = field(default_factory=list)

        obj = TestModel(items=["item"])
        assert has_geo_properties(obj) is True

    def test_build_geo_properties_with_link_objects(self) -> None:
        """Test build_geo_properties with Link objects."""

        @dataclass
        class TestModel:
            """Test model with links."""

            link: list[Link] = field(default_factory=list)

        link1 = Link(href="http://example.com", text="Example", type="text/html")
        obj = TestModel(link=[link1])
        props = build_geo_properties(obj)
        assert "link" in props
        assert props["link"][0]["href"] == "http://example.com"
        assert props["link"][0]["text"] == "Example"
        assert props["link"][0]["type"] == "text/html"

    def test_build_geo_properties_with_decimal(self) -> None:
        """Test build_geo_properties converts Decimal to float."""

        @dataclass
        class TestModel:
            """Test model with decimal."""

            value: Decimal | None = None

        obj = TestModel(value=Decimal("123.456"))
        props = build_geo_properties(obj)
        assert props["value"] == 123.456
        assert isinstance(props["value"], float)

    def test_build_geo_properties_with_int(self) -> None:
        """Test build_geo_properties converts int-like values to float for JSON."""

        @dataclass
        class TestModel:
            """Test model with int."""

            count: int | None = None

        obj = TestModel(count=42)
        props = build_geo_properties(obj)
        # Integers are converted to float for consistent JSON serialization
        assert props["count"] == 42.0
        assert isinstance(props["count"], float)

    def test_build_geo_properties_with_bool(self) -> None:
        """Test build_geo_properties converts bool to float."""

        @dataclass
        class TestModel:
            """Test model with bool."""

            flag: bool | None = None

        obj = TestModel(flag=True)
        props = build_geo_properties(obj)
        # Booleans are converted to float (1.0/0.0) per SupportsFloat behavior
        assert props["flag"] == 1.0
        assert isinstance(props["flag"], float)
