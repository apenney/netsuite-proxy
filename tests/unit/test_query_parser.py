"""Unit tests for query parser utilities."""

from datetime import UTC, datetime

from app.utils.query_parser import (
    build_netsuite_filter,
    extract_pagination_info,
    format_netsuite_timestamp,
    parse_boolean_param,
    parse_date_param,
    parse_field_list,
    parse_float_param,
    parse_id_parameter,
    parse_netsuite_timestamp,
)


class TestParseIdParameter:
    """Tests for parse_id_parameter function."""

    def test_none_input(self):
        """Test None input."""
        assert parse_id_parameter(None) is None

    def test_empty_string(self):
        """Test empty string."""
        assert parse_id_parameter("") is None
        assert parse_id_parameter("  ") is None

    def test_single_id(self):
        """Test single ID."""
        assert parse_id_parameter("123") == [123]

    def test_comma_separated(self):
        """Test comma-separated IDs."""
        assert parse_id_parameter("1,2,3") == [1, 2, 3]
        assert parse_id_parameter("1, 2, 3") == [1, 2, 3]  # With spaces

    def test_range(self):
        """Test ID range."""
        assert parse_id_parameter("1-5") == [1, 2, 3, 4, 5]
        assert parse_id_parameter("10-15") == [10, 11, 12, 13, 14, 15]

    def test_reverse_range(self):
        """Test reverse range (should be skipped)."""
        # This should not include any IDs since start > end
        result = parse_id_parameter("5-1")
        assert result is None or result == []

    def test_large_range(self):
        """Test large range (should be limited)."""
        # Should limit to 10000 items
        result = parse_id_parameter("1-20000")
        assert result is not None
        assert len(result) == 10001  # 1 through 10001 inclusive

    def test_array_format(self):
        """Test array format."""
        assert parse_id_parameter("[1,2,3]") == [1, 2, 3]
        assert parse_id_parameter("[1, 2, 3]") == [1, 2, 3]

    def test_mixed_format(self):
        """Test mixed formats."""
        assert parse_id_parameter("1,5-7,10") == [1, 5, 6, 7, 10]
        assert parse_id_parameter("1, 5-7, 10") == [1, 5, 6, 7, 10]

    def test_invalid_ids(self):
        """Test invalid IDs."""
        assert parse_id_parameter("abc") is None
        assert parse_id_parameter("1,abc,3") == [1, 3]  # Partial valid

    def test_negative_ids(self):
        """Test negative IDs."""
        assert parse_id_parameter("-1") == [-1]
        assert parse_id_parameter("-5--1") == [-5, -4, -3, -2, -1]


class TestParseFieldList:
    """Tests for parse_field_list function."""

    def test_none_input(self):
        """Test None input."""
        assert parse_field_list(None) is None

    def test_empty_string(self):
        """Test empty string."""
        assert parse_field_list("") is None
        assert parse_field_list("  ") is None

    def test_single_field(self):
        """Test single field."""
        assert parse_field_list("id") == ["id"]

    def test_multiple_fields(self):
        """Test multiple fields."""
        assert parse_field_list("id,name,email") == ["id", "name", "email"]

    def test_fields_with_spaces(self):
        """Test fields with spaces."""
        assert parse_field_list("id, name , email") == ["id", "name", "email"]

    def test_nested_fields(self):
        """Test nested field notation."""
        assert parse_field_list("id,subsidiary.name,address.city") == [
            "id",
            "subsidiary.name",
            "address.city",
        ]

    def test_empty_fields(self):
        """Test empty fields in list."""
        assert parse_field_list("id,,name") == ["id", "name"]
        assert parse_field_list(",,,") is None


class TestParseDateParam:
    """Tests for parse_date_param function."""

    def test_none_input(self):
        """Test None input."""
        assert parse_date_param(None) is None

    def test_empty_string(self):
        """Test empty string."""
        assert parse_date_param("") is None
        assert parse_date_param("  ") is None

    def test_iso_format(self):
        """Test ISO format."""
        result = parse_date_param("2024-01-01T12:30:00")
        assert result == datetime(2024, 1, 1, 12, 30, 0, tzinfo=UTC)

    def test_iso_with_milliseconds(self):
        """Test ISO format with milliseconds."""
        result = parse_date_param("2024-01-01T12:30:00.123")
        assert result == datetime(2024, 1, 1, 12, 30, 0, 123000, tzinfo=UTC)

    def test_date_only(self):
        """Test date only format."""
        result = parse_date_param("2024-01-01")
        assert result == datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)

    def test_us_format(self):
        """Test US date format."""
        result = parse_date_param("01/15/2024")
        assert result == datetime(2024, 1, 15, 0, 0, 0, tzinfo=UTC)

    def test_european_format(self):
        """Test European date format."""
        result = parse_date_param("15/01/2024")
        assert result == datetime(2024, 1, 15, 0, 0, 0, tzinfo=UTC)

    def test_iso_with_timezone(self):
        """Test ISO format with timezone."""
        result = parse_date_param("2024-01-01T12:30:00-08:00")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1

    def test_invalid_date(self):
        """Test invalid date format."""
        assert parse_date_param("not-a-date") is None
        assert parse_date_param("2024-13-01") is None  # Invalid month


class TestParseBooleanParam:
    """Tests for parse_boolean_param function."""

    def test_none_input(self):
        """Test None input."""
        assert parse_boolean_param(None) is None

    def test_empty_string(self):
        """Test empty string."""
        assert parse_boolean_param("") is None

    def test_true_values(self):
        """Test various true values."""
        assert parse_boolean_param("true") is True
        assert parse_boolean_param("TRUE") is True
        assert parse_boolean_param("yes") is True
        assert parse_boolean_param("YES") is True
        assert parse_boolean_param("1") is True
        assert parse_boolean_param("on") is True
        assert parse_boolean_param("t") is True
        assert parse_boolean_param("y") is True

    def test_false_values(self):
        """Test various false values."""
        assert parse_boolean_param("false") is False
        assert parse_boolean_param("FALSE") is False
        assert parse_boolean_param("no") is False
        assert parse_boolean_param("NO") is False
        assert parse_boolean_param("0") is False
        assert parse_boolean_param("off") is False
        assert parse_boolean_param("f") is False
        assert parse_boolean_param("n") is False

    def test_invalid_values(self):
        """Test invalid boolean values."""
        assert parse_boolean_param("maybe") is None
        assert parse_boolean_param("2") is None
        assert parse_boolean_param("yep") is None


class TestParseFloatParam:
    """Tests for parse_float_param function."""

    def test_none_input(self):
        """Test None input."""
        assert parse_float_param(None) is None

    def test_empty_string(self):
        """Test empty string."""
        assert parse_float_param("") is None

    def test_integer_string(self):
        """Test integer string."""
        assert parse_float_param("123") == 123.0

    def test_float_string(self):
        """Test float string."""
        assert parse_float_param("123.45") == 123.45

    def test_negative_float(self):
        """Test negative float."""
        assert parse_float_param("-123.45") == -123.45

    def test_scientific_notation(self):
        """Test scientific notation."""
        assert parse_float_param("1.23e2") == 123.0

    def test_with_spaces(self):
        """Test float with spaces."""
        assert parse_float_param("  123.45  ") == 123.45

    def test_invalid_float(self):
        """Test invalid float."""
        assert parse_float_param("not-a-number") is None
        assert parse_float_param("12.34.56") is None


class TestBuildNetsuiteFilter:
    """Tests for build_netsuite_filter function."""

    def test_empty_params(self):
        """Test empty parameters."""
        filters = build_netsuite_filter({})
        assert filters == {}

    def test_date_filters(self):
        """Test date range filters."""
        params = {
            "created_since": datetime(2024, 1, 1, tzinfo=UTC),
            "updated_before": datetime(2024, 12, 31, tzinfo=UTC),
        }
        filters = build_netsuite_filter(params)

        assert filters["dateCreated"]["operator"] == "onOrAfter"
        assert filters["dateCreated"]["searchValue"] == "2024-01-01T00:00:00+00:00"
        assert filters["lastModifiedDate"]["operator"] == "before"
        assert filters["lastModifiedDate"]["searchValue"] == "2024-12-31T00:00:00+00:00"

    def test_id_filters(self):
        """Test ID filters."""
        # Single ID
        filters = build_netsuite_filter({"ids": "123"})
        assert filters["internalId"]["operator"] == "is"
        assert filters["internalId"]["searchValue"] == "123"

        # Multiple IDs
        filters = build_netsuite_filter({"ids": [1, 2, 3]})
        assert filters["internalId"]["operator"] == "anyOf"
        assert filters["internalId"]["searchValue"] == [1, 2, 3]

    def test_status_filter(self):
        """Test status filter."""
        # Active status
        filters = build_netsuite_filter({"status": "active"})
        assert filters["isInactive"]["operator"] == "is"
        assert filters["isInactive"]["searchValue"] is False

        # Inactive status
        filters = build_netsuite_filter({"status": "inactive"})
        assert filters["isInactive"]["operator"] == "is"
        assert filters["isInactive"]["searchValue"] is True

    def test_search_filter(self):
        """Test search term filter."""
        filters = build_netsuite_filter({"search": "test customer"})
        assert filters["_text"]["operator"] == "contains"
        assert filters["_text"]["searchValue"] == "test customer"

    def test_subsidiary_filter(self):
        """Test subsidiary filter."""
        filters = build_netsuite_filter({"subsidiary_id": 123})
        assert filters["subsidiary"]["operator"] == "anyOf"
        assert filters["subsidiary"]["searchValue"] == [{"internalId": "123"}]


class TestExtractPaginationInfo:
    """Tests for extract_pagination_info function."""

    def test_empty_headers(self):
        """Test empty headers."""
        info = extract_pagination_info({})
        assert info["search_id"] is None
        assert info["total_records"] == 0
        assert info["total_pages"] == 0
        assert info["page_size"] == 20

    def test_all_headers(self):
        """Test all pagination headers."""
        headers = {
            "NETSUITE-SEARCH-ID": "ABC123",
            "NETSUITE-TOTAL-RECORDS": "150",
            "NETSUITE-TOTAL-PAGES": "8",
            "NETSUITE-PAGE-SIZE": "20",
        }
        info = extract_pagination_info(headers)
        assert info["search_id"] == "ABC123"
        assert info["total_records"] == 150
        assert info["total_pages"] == 8
        assert info["page_size"] == 20

    def test_partial_headers(self):
        """Test partial headers."""
        headers = {
            "NETSUITE-TOTAL-RECORDS": "50",
        }
        info = extract_pagination_info(headers)
        assert info["search_id"] is None
        assert info["total_records"] == 50
        assert info["total_pages"] == 0
        assert info["page_size"] == 20


class TestFormatNetsuiteTimestamp:
    """Tests for format_netsuite_timestamp function."""

    def test_basic_datetime(self):
        """Test basic datetime formatting."""
        dt = datetime(2024, 1, 15, 14, 30, 45, tzinfo=UTC)
        result = format_netsuite_timestamp(dt)
        assert result == "2024-01-15T14:30:45"

    def test_midnight(self):
        """Test midnight datetime."""
        dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        result = format_netsuite_timestamp(dt)
        assert result == "2024-01-01T00:00:00"


class TestParseNetsuiteTimestamp:
    """Tests for parse_netsuite_timestamp function."""

    def test_none_input(self):
        """Test None input."""
        assert parse_netsuite_timestamp(None) is None
        assert parse_netsuite_timestamp("") is None

    def test_basic_timestamp(self):
        """Test basic timestamp."""
        result = parse_netsuite_timestamp("2024-01-15T14:30:45")
        assert result == datetime(2024, 1, 15, 14, 30, 45, tzinfo=UTC)

    def test_timestamp_with_milliseconds(self):
        """Test timestamp with milliseconds."""
        result = parse_netsuite_timestamp("2024-01-15T14:30:45.123")
        assert result == datetime(2024, 1, 15, 14, 30, 45, 123000, tzinfo=UTC)

    def test_timestamp_with_timezone(self):
        """Test timestamp with timezone."""
        result = parse_netsuite_timestamp("2024-01-15T14:30:45.000-08:00")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_timestamp_with_positive_timezone(self):
        """Test timestamp with positive timezone."""
        result = parse_netsuite_timestamp("2024-01-15T14:30:45.000+05:30")
        assert result is not None
        assert result.year == 2024

    def test_invalid_timestamp(self):
        """Test invalid timestamp."""
        assert parse_netsuite_timestamp("not-a-timestamp") is None
