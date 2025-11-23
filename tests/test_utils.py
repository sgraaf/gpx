"""Tests for gpx.utils module."""

from gpx.utils import remove_encoding_from_string


class TestRemoveEncodingFromString:
    """Tests for the remove_encoding_from_string utility function."""

    def test_removes_double_quoted_utf8_encoding(self):
        """Test removal of double-quoted UTF-8 encoding declaration."""
        input_str = '<?xml version="1.0" encoding="UTF-8"?>'
        expected = '<?xml version="1.0" ?>'
        assert remove_encoding_from_string(input_str) == expected

    def test_removes_single_quoted_utf8_encoding(self):
        """Test removal of single-quoted UTF-8 encoding declaration."""
        input_str = "<?xml version='1.0' encoding='UTF-8'?>"
        expected = "<?xml version='1.0' ?>"
        assert remove_encoding_from_string(input_str) == expected

    def test_removes_lowercase_utf8_encoding(self):
        """Test removal of lowercase utf-8 encoding declaration."""
        input_str = '<?xml version="1.0" encoding="utf-8"?>'
        expected = '<?xml version="1.0" ?>'
        assert remove_encoding_from_string(input_str) == expected

    def test_removes_iso_8859_encoding(self):
        """Test removal of ISO-8859-1 encoding declaration."""
        input_str = '<?xml version="1.0" encoding="ISO-8859-1"?>'
        expected = '<?xml version="1.0" ?>'
        assert remove_encoding_from_string(input_str) == expected

    def test_removes_windows_1252_encoding(self):
        """Test removal of Windows-1252 encoding declaration."""
        input_str = '<?xml version="1.0" encoding="windows-1252"?>'
        expected = '<?xml version="1.0" ?>'
        assert remove_encoding_from_string(input_str) == expected

    def test_no_encoding_returns_unchanged(self):
        """Test that string without encoding is returned unchanged."""
        input_str = '<?xml version="1.0"?>'
        assert remove_encoding_from_string(input_str) == input_str

    def test_empty_string_returns_empty(self):
        """Test that empty string returns empty."""
        assert remove_encoding_from_string("") == ""

    def test_preserves_rest_of_xml(self):
        """Test that the rest of the XML content is preserved."""
        input_str = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="52.5" lon="13.4"/>
</gpx>"""
        result = remove_encoding_from_string(input_str)
        assert "<gpx" in result
        assert '<wpt lat="52.5" lon="13.4"/>' in result
        assert 'encoding="UTF-8"' not in result

    def test_handles_encoding_with_spaces(self):
        """Test handling of encoding with extra spaces."""
        input_str = '<?xml version="1.0"  encoding="UTF-8" ?>'
        result = remove_encoding_from_string(input_str)
        assert 'encoding="UTF-8"' not in result
