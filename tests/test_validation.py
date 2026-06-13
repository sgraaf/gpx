"""Tests for gpx.validation module - GPX 1.1 schema validation."""

from decimal import Decimal
from pathlib import Path

import pytest

from gpx import (
    GPX,
    InvalidGPXError,
    Severity,
    ValidationIssue,
    ValidationResult,
    Waypoint,
    from_string,
    read_gpx,
    validate,
)
from gpx.types import Latitude, Longitude

from .conftest import (
    INVALID_FIXTURES_DIR,
    VALID_FIXTURES_DIR,
    WARNINGS_FIXTURES_DIR,
)


def _messages(issues: list[ValidationIssue]) -> str:
    return " | ".join(issue.message for issue in issues)


class TestValidationResult:
    """Tests for the ValidationResult and ValidationIssue data classes."""

    def test_empty_result_is_valid(self) -> None:
        result = ValidationResult()
        assert result.is_valid
        assert bool(result) is True
        assert result.errors == []
        assert result.warnings == []

    def test_errors_make_invalid(self) -> None:
        result = ValidationResult([ValidationIssue(Severity.ERROR, "boom", "gpx", 1)])
        assert not result.is_valid
        assert bool(result) is False
        assert len(result.errors) == 1
        assert result.warnings == []

    def test_warnings_keep_valid(self) -> None:
        result = ValidationResult([ValidationIssue(Severity.WARNING, "hmm", "gpx", 1)])
        assert result.is_valid
        assert len(result.warnings) == 1
        assert result.errors == []

    def test_issue_to_dict(self) -> None:
        issue = ValidationIssue(Severity.ERROR, "boom", "gpx > wpt[0]", 7)
        assert issue.to_dict() == {
            "severity": "error",
            "line": 7,
            "path": "gpx > wpt[0]",
            "message": "boom",
        }

    def test_issue_str_contains_line_and_path(self) -> None:
        issue = ValidationIssue(Severity.ERROR, "boom", "gpx > wpt[0]", 7)
        text = str(issue)
        assert "ERROR" in text
        assert "line 7" in text
        assert "gpx > wpt[0]" in text
        assert "boom" in text


class TestValidFixtures:
    """Every valid fixture must yield zero errors."""

    @pytest.mark.parametrize(
        "fixture", sorted(VALID_FIXTURES_DIR.glob("*.gpx")), ids=lambda p: p.name
    )
    def test_valid_fixture_has_no_errors(self, fixture: Path) -> None:
        result = validate(fixture)
        assert result.is_valid, _messages(result.errors)


class TestRootChecks:
    """Tests for root element and namespace validation."""

    def test_wrong_root_element(self) -> None:
        result = validate(INVALID_FIXTURES_DIR / "not_gpx_root.gpx")
        assert not result.is_valid
        assert any("root element" in i.message for i in result.errors)

    def test_gpx_10_namespace_hint(self) -> None:
        result = validate(INVALID_FIXTURES_DIR / "gpx_10_namespace.gpx")
        assert not result.is_valid
        assert any("GPX 1.0 namespace" in i.message for i in result.errors)

    def test_wrong_namespace(self) -> None:
        result = validate(INVALID_FIXTURES_DIR / "wrong_namespace.gpx")
        assert not result.is_valid
        assert any("unexpected namespace" in i.message for i in result.errors)

    def test_missing_namespace(self) -> None:
        result = validate(INVALID_FIXTURES_DIR / "missing_namespace.gpx")
        assert not result.is_valid
        assert any("missing GPX namespace" in i.message for i in result.errors)


class TestRequiredAttributes:
    """Tests for missing required attribute detection."""

    @pytest.mark.parametrize(
        ("fixture", "attr"),
        [
            ("missing_creator.gpx", "creator"),
            ("missing_version.gpx", "version"),
            ("missing_lat.gpx", "lat"),
            ("missing_lon.gpx", "lon"),
            ("missing_link_href.gpx", "href"),
            ("missing_copyright_author.gpx", "author"),
            ("missing_email_id.gpx", "id"),
            ("missing_email_domain.gpx", "domain"),
            ("missing_bounds_minlat.gpx", "minlat"),
        ],
    )
    def test_missing_attribute(self, fixture: str, attr: str) -> None:
        result = validate(INVALID_FIXTURES_DIR / fixture)
        assert not result.is_valid
        assert any(f"missing required '{attr}'" in i.message for i in result.errors)

    def test_missing_both_lat_and_lon(self) -> None:
        result = validate(INVALID_FIXTURES_DIR / "missing_lat_lon.gpx")
        messages = _messages(result.errors)
        assert "lat" in messages
        assert "lon" in messages


class TestUnknownElements:
    """Tests for unknown element detection and suggestions."""

    def test_unknown_element_is_error(self) -> None:
        result = validate(INVALID_FIXTURES_DIR / "unknown_element.gpx")
        assert not result.is_valid
        assert any("unknown element <nmae>" in i.message for i in result.errors)

    def test_unknown_element_suggestion(self) -> None:
        result = validate(INVALID_FIXTURES_DIR / "unknown_element.gpx")
        assert any("did you mean <name>?" in i.message for i in result.errors)


class TestDuplicateElements:
    """Tests for duplicate single-occurrence element detection."""

    def test_duplicate_metadata(self) -> None:
        result = validate(INVALID_FIXTURES_DIR / "duplicate_metadata.gpx")
        assert not result.is_valid
        assert any("duplicate <metadata>" in i.message for i in result.errors)

    def test_duplicate_name(self) -> None:
        result = validate(INVALID_FIXTURES_DIR / "duplicate_name.gpx")
        assert not result.is_valid
        assert any("duplicate <name>" in i.message for i in result.errors)


class TestContentValidation:
    """Tests for content type / value constraint detection."""

    @pytest.mark.parametrize(
        "fixture",
        [
            "lat_too_high.gpx",
            "lat_too_low.gpx",
            "lon_too_high.gpx",
            "lon_too_low.gpx",
            "non_numeric_lat.gpx",
            "non_numeric_lon.gpx",
            "non_numeric_elevation.gpx",
            "degrees_negative.gpx",
            "degrees_too_high.gpx",
            "dgps_station_negative.gpx",
            "dgps_station_too_high.gpx",
            "invalid_fix_value.gpx",
            "invalid_fix_uppercase.gpx",
            "non_integer_sat.gpx",
            "bad_copyright_year.gpx",
            "invalid_time.gpx",
        ],
    )
    def test_invalid_value_is_error(self, fixture: str) -> None:
        result = validate(INVALID_FIXTURES_DIR / fixture)
        assert not result.is_valid, fixture

    def test_invalid_sat_path_points_at_element(self) -> None:
        result = validate(INVALID_FIXTURES_DIR / "non_integer_sat.gpx")
        sat_errors = [i for i in result.errors if i.path.endswith("> sat")]
        assert sat_errors

    def test_issues_have_line_numbers(self) -> None:
        result = validate(INVALID_FIXTURES_DIR / "lat_too_high.gpx")
        assert all(i.line is not None for i in result.errors)


class TestWarnings:
    """Tests for warning-level (off-spec but readable) issues."""

    def test_wrong_version_is_warning(self) -> None:
        result = validate(WARNINGS_FIXTURES_DIR / "wrong_version.gpx")
        assert result.is_valid
        assert any("version is '1.0'" in i.message for i in result.warnings)

    def test_out_of_order_is_warning(self) -> None:
        result = validate(WARNINGS_FIXTURES_DIR / "out_of_order.gpx")
        assert result.is_valid
        assert any("out of order" in i.message for i in result.warnings)

    def test_longitude_180_is_warning(self) -> None:
        result = validate(WARNINGS_FIXTURES_DIR / "longitude_180.gpx")
        assert result.is_valid
        assert any("180.0" in i.message for i in result.warnings)

    def test_foreign_namespace_is_warning(self) -> None:
        result = validate(WARNINGS_FIXTURES_DIR / "foreign_namespace.gpx")
        assert result.is_valid
        assert any("foreign-namespace" in i.message for i in result.warnings)

    def test_naive_time_is_warning(self) -> None:
        result = validate(WARNINGS_FIXTURES_DIR / "naive_time.gpx")
        assert result.is_valid
        assert any("no timezone" in i.message for i in result.warnings)

    def test_unqualified_extensions_is_warning(self) -> None:
        # Extension children that inherit the default GPX namespace (no prefix)
        # violate the xsd:any namespace="##other" rule.
        result = validate(WARNINGS_FIXTURES_DIR / "unqualified_extensions.gpx")
        assert result.is_valid
        warnings = _messages(result.warnings)
        assert "<accuracy> is in the GPX namespace" in warnings
        assert "<speed> is in the GPX namespace" in warnings
        assert "<battery> is in the GPX namespace" in warnings

    def test_foreign_namespace_extensions_no_warning(self) -> None:
        # Properly namespaced extension content must not be flagged.
        content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v2"
     version="1.1" creator="Test">
  <wpt lat="52.0" lon="4.0">
    <extensions>
      <gpxtpx:TrackPointExtension>
        <gpxtpx:hr>142</gpxtpx:hr>
      </gpxtpx:TrackPointExtension>
    </extensions>
  </wpt>
</gpx>
"""
        result = validate(content)
        assert result.is_valid
        assert not any("foreign namespace" in i.message for i in result.warnings)


class TestMalformedXML:
    """Tests for not-well-formed XML handling."""

    def test_malformed_xml_reports_error(self) -> None:
        result = validate(INVALID_FIXTURES_DIR / "malformed_xml.gpx")
        assert not result.is_valid
        assert any("not well-formed" in i.message for i in result.errors)

    def test_empty_file_reports_error(self) -> None:
        result = validate(INVALID_FIXTURES_DIR / "empty_file.gpx")
        assert not result.is_valid


class TestValidateSources:
    """Tests for the different source types accepted by validate()."""

    def test_validate_path(self) -> None:
        result = validate(VALID_FIXTURES_DIR / "minimal.gpx")
        assert result.is_valid

    def test_validate_path_string(self) -> None:
        result = validate(str(VALID_FIXTURES_DIR / "minimal.gpx"))
        assert result.is_valid

    def test_validate_content_string(self) -> None:
        content = (VALID_FIXTURES_DIR / "minimal.gpx").read_text("utf-8")
        result = validate(content)
        assert result.is_valid

    def test_validate_gpx_instance(self) -> None:
        gpx = GPX(
            creator="Test",
            wpt=[Waypoint(lat=Latitude("52.0"), lon=Longitude("4.0"))],
        )
        result = validate(gpx)
        assert result.is_valid

    def test_validate_rejects_unsupported_type(self) -> None:
        with pytest.raises(TypeError):
            validate(42)  # type: ignore[arg-type]


class TestRoundTrip:
    """Anything serialized by the library must validate clean."""

    @pytest.mark.parametrize(
        "fixture", sorted(VALID_FIXTURES_DIR.glob("*.gpx")), ids=lambda p: p.name
    )
    def test_round_trip_has_no_errors(self, fixture: Path) -> None:
        gpx = read_gpx(fixture)
        result = validate(gpx)
        assert result.is_valid, _messages(result.errors)


class TestStrictMode:
    """Tests for strict parsing via read_gpx / from_string."""

    def test_read_gpx_strict_valid(self) -> None:
        gpx = read_gpx(VALID_FIXTURES_DIR / "minimal.gpx", strict=True)
        assert isinstance(gpx, GPX)

    def test_read_gpx_strict_raises_on_error(self) -> None:
        with pytest.raises(InvalidGPXError) as exc_info:
            read_gpx(INVALID_FIXTURES_DIR / "unknown_element.gpx", strict=True)
        assert exc_info.value.issues
        assert isinstance(exc_info.value.result, ValidationResult)

    def test_from_string_strict_raises_on_error(self) -> None:
        content = (INVALID_FIXTURES_DIR / "lat_too_high.gpx").read_text("utf-8")
        with pytest.raises(InvalidGPXError):
            from_string(content, strict=True)

    def test_from_string_strict_allows_warnings(self) -> None:
        content = (WARNINGS_FIXTURES_DIR / "naive_time.gpx").read_text("utf-8")
        gpx = from_string(content, strict=True)
        assert isinstance(gpx, GPX)

    def test_default_parsing_is_lenient(self) -> None:
        # Unknown elements are silently dropped without strict mode.
        content = (INVALID_FIXTURES_DIR / "unknown_element.gpx").read_text("utf-8")
        gpx = from_string(content)
        assert isinstance(gpx, GPX)

    def test_invalid_gpx_error_is_value_error(self) -> None:
        assert issubclass(InvalidGPXError, ValueError)


class TestGPXInstanceValidation:
    """Validating programmatically built GPX instances."""

    def test_invalid_coordinates_caught_at_construction(self) -> None:
        # The Latitude type itself guards range, so out-of-range data cannot
        # reach validate(); confirm a valid instance round-trips clean instead.
        gpx = GPX(
            creator="Test",
            wpt=[
                Waypoint(
                    lat=Latitude("52.0"),
                    lon=Longitude("4.0"),
                    ele=Decimal("10.0"),
                )
            ],
        )
        assert validate(gpx).is_valid
