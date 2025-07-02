"""Unit tests for query parameter models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.query_params import (
    BaseQueryParams,
    CustomerQueryParams,
    InvoiceQueryParams,
    SortOrder,
    TransactionQueryParams,
)


class TestPaginationParams:
    """Tests for pagination-related parameters in BaseQueryParams."""

    def test_default_values(self):
        """Test default pagination values."""
        params = BaseQueryParams()
        assert params.page == 1
        assert params.page_size == 20
        assert params.search_id is None

    def test_valid_values(self):
        """Test valid pagination values."""
        params = BaseQueryParams(page=5, page_size=100, search_id="ABC123")
        assert params.page == 5
        assert params.page_size == 100
        assert params.search_id == "ABC123"

    def test_page_validation(self):
        """Test page number validation."""
        # Valid
        params = BaseQueryParams(page=1)
        assert params.page == 1

        # Invalid - less than 1
        with pytest.raises(ValidationError) as exc_info:
            BaseQueryParams(page=0)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("page",) for e in errors)

    def test_page_size_validation(self):
        """Test page size validation."""
        # Valid
        params = BaseQueryParams(page_size=1000)
        assert params.page_size == 1000

        # Invalid - less than 1
        with pytest.raises(ValidationError) as exc_info:
            BaseQueryParams(page_size=0)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("page_size",) for e in errors)

        # Invalid - greater than 1000
        with pytest.raises(ValidationError) as exc_info:
            BaseQueryParams(page_size=1001)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("page_size",) for e in errors)


class TestDateRangeParams:
    """Tests for date range parameters in BaseQueryParams."""

    def test_empty_date_range(self):
        """Test empty date range."""
        params = BaseQueryParams()
        assert params.created_since is None
        assert params.created_before is None
        assert params.updated_since is None
        assert params.updated_before is None

    def test_valid_date_ranges(self):
        """Test valid date ranges."""
        created_since = datetime(2024, 1, 1, tzinfo=UTC)
        created_before = datetime(2024, 12, 31, tzinfo=UTC)
        params = BaseQueryParams(
            created_since=created_since,
            created_before=created_before,
        )
        assert params.created_since == created_since
        assert params.created_before == created_before

    def test_invalid_created_date_range(self):
        """Test invalid created date range."""
        with pytest.raises(ValidationError) as exc_info:
            BaseQueryParams(
                created_since=datetime(2024, 12, 31, tzinfo=UTC),
                created_before=datetime(2024, 1, 1, tzinfo=UTC),
            )
        assert "created_since must be before created_before" in str(exc_info.value)

    def test_invalid_updated_date_range(self):
        """Test invalid updated date range."""
        with pytest.raises(ValidationError) as exc_info:
            BaseQueryParams(
                updated_since=datetime(2024, 12, 31, tzinfo=UTC),
                updated_before=datetime(2024, 1, 1, tzinfo=UTC),
            )
        assert "updated_since must be before updated_before" in str(exc_info.value)

    def test_partial_date_ranges(self):
        """Test partial date ranges."""
        # Only since
        params = BaseQueryParams(created_since=datetime(2024, 1, 1, tzinfo=UTC))
        assert params.created_since == datetime(2024, 1, 1, tzinfo=UTC)
        assert params.created_before is None

        # Only before
        params = BaseQueryParams(updated_before=datetime(2024, 12, 31, tzinfo=UTC))
        assert params.updated_since is None
        assert params.updated_before == datetime(2024, 12, 31, tzinfo=UTC)

    def test_timezone_aware_datetime_required(self):
        """Test that naive datetimes are rejected."""
        # Naive datetime should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            BaseQueryParams(created_since=datetime(2024, 1, 1))  # noqa: DTZ001 - Testing naive datetime
        errors = exc_info.value.errors()
        assert any("timezone-aware" in str(e) for e in errors)

    def test_string_datetime_parsing(self):
        """Test that string datetimes are parsed as timezone-aware."""
        # ISO format string should be parsed with UTC timezone
        params = BaseQueryParams(created_since="2024-01-01T12:00:00")
        assert params.created_since is not None
        assert params.created_since.tzinfo is not None

        # ISO format with timezone should preserve timezone info
        params = BaseQueryParams(created_since="2024-01-01T12:00:00+05:00")
        assert params.created_since is not None
        assert params.created_since.tzinfo is not None


class TestFieldSelection:
    """Tests for field selection parameters in BaseQueryParams."""

    def test_empty_fields(self):
        """Test empty field selection."""
        params = BaseQueryParams()
        assert params.fields is None
        assert params.body_fields_only is False
        assert params.field_list is None

    def test_single_field(self):
        """Test single field selection."""
        params = BaseQueryParams(fields="id")
        assert params.fields == "id"
        assert params.field_list == ["id"]

    def test_multiple_fields(self):
        """Test multiple field selection."""
        params = BaseQueryParams(fields="id,name,email")
        assert params.fields == "id,name,email"
        assert params.field_list == ["id", "name", "email"]

    def test_fields_with_spaces(self):
        """Test field parsing with spaces."""
        params = BaseQueryParams(fields="id, name , email")
        assert params.field_list == ["id", "name", "email"]

    def test_nested_fields(self):
        """Test nested field selection."""
        params = BaseQueryParams(fields="id,subsidiary.name,address.city")
        assert params.field_list == ["id", "subsidiary.name", "address.city"]

    def test_body_fields_only(self):
        """Test body fields only flag."""
        params = BaseQueryParams(body_fields_only=True)
        assert params.body_fields_only is True


class TestIdFiltering:
    """Tests for ID filtering parameters in BaseQueryParams."""

    def test_empty_ids(self):
        """Test empty ID filter."""
        params = BaseQueryParams()
        assert params.ids is None
        assert params.id_list is None

    def test_single_id(self):
        """Test single ID."""
        params = BaseQueryParams(ids="123")
        assert params.ids == "123"
        assert params.id_list == [123]

    def test_comma_separated_ids(self):
        """Test comma-separated IDs."""
        params = BaseQueryParams(ids="1,2,3")
        assert params.id_list == [1, 2, 3]

    def test_id_range(self):
        """Test ID range."""
        params = BaseQueryParams(ids="1-5")
        assert params.id_list == [1, 2, 3, 4, 5]

    def test_mixed_ids(self):
        """Test mixed ID formats."""
        params = BaseQueryParams(ids="1,5-7,10")
        assert params.id_list == [1, 5, 6, 7, 10]

    def test_array_format(self):
        """Test array format IDs."""
        params = BaseQueryParams(ids="[1,2,3]")
        assert params.id_list == [1, 2, 3]

    def test_invalid_ids(self):
        """Test invalid ID formats."""
        params = BaseQueryParams(ids="abc,def")
        assert params.id_list is None

    def test_partial_invalid_ids(self):
        """Test partial invalid IDs."""
        params = BaseQueryParams(ids="1,abc,3")
        assert params.id_list == [1, 3]


class TestPerformanceParams:
    """Tests for performance parameters in BaseQueryParams."""

    def test_default_values(self):
        """Test default performance values."""
        params = BaseQueryParams()
        assert params.fast is False
        assert params.include_inactive is False

    def test_fast_mode(self):
        """Test fast mode."""
        params = BaseQueryParams(fast=True)
        assert params.fast is True

    def test_include_inactive(self):
        """Test include inactive flag."""
        params = BaseQueryParams(include_inactive=True)
        assert params.include_inactive is True


class TestSortingParams:
    """Tests for sorting parameters in BaseQueryParams."""

    def test_default_values(self):
        """Test default sorting values."""
        params = BaseQueryParams()
        assert params.sort_by is None
        assert params.order == SortOrder.ASC

    def test_sort_by_field(self):
        """Test sort by field."""
        params = BaseQueryParams(sort_by="name")
        assert params.sort_by == "name"
        assert params.order == SortOrder.ASC

    def test_sort_order(self):
        """Test sort order."""
        params = BaseQueryParams(sort_by="created_date", order=SortOrder.DESC)
        assert params.sort_by == "created_date"
        assert params.order == SortOrder.DESC


class TestBaseQueryParamsCombined:
    """Tests for combined parameters in BaseQueryParams."""

    def test_default_values(self):
        """Test default query parameter values."""
        params = BaseQueryParams()
        assert params.page == 1
        assert params.page_size == 20
        assert params.search is None
        assert params.subsidiary_id is None

    def test_combined_params(self):
        """Test combining multiple parameter types."""
        params = BaseQueryParams(
            page=2,
            page_size=50,
            ids="1-10",
            fields="id,name",
            created_since=datetime(2024, 1, 1, tzinfo=UTC),
            sort_by="name",
            order=SortOrder.DESC,
            search="test",
            fast=True,
        )
        assert params.page == 2
        assert params.page_size == 50
        assert params.id_list == list(range(1, 11))
        assert params.field_list == ["id", "name"]
        assert params.created_since == datetime(2024, 1, 1, tzinfo=UTC)
        assert params.sort_by == "name"
        assert params.order == SortOrder.DESC
        assert params.search == "test"
        assert params.fast is True

    def test_to_netsuite_params(self):
        """Test conversion to NetSuite parameters."""
        params = BaseQueryParams(
            page=2,
            page_size=50,
            search_id="ABC123",
            created_since=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            fields="id,name",
            ids="1,2,3",
            fast=True,
            sort_by="name",
            order=SortOrder.DESC,
            search="test",
            subsidiary_id=123,
        )

        ns_params = params.to_netsuite_params()

        assert ns_params["page"] == "2"
        assert ns_params["pageSize"] == "50"
        assert ns_params["searchId"] == "ABC123"
        assert ns_params["createdSince"] == "2024-01-01T12:00:00+00:00"
        assert ns_params["fields"] == "id,name"
        assert ns_params["ids"] == "1,2,3"
        assert ns_params["fast"] == "true"
        assert ns_params["sortBy"] == "name"
        assert ns_params["order"] == "desc"
        assert ns_params["search"] == "test"
        assert ns_params["subsidiaryId"] == "123"


class TestCustomerQueryParams:
    """Tests for customer-specific query parameters."""

    def test_customer_specific_params(self):
        """Test customer-specific parameters."""
        params = CustomerQueryParams(
            status="active",
            customer_type="Company",
            balance_min=100.0,
            balance_max=1000.0,
        )
        assert params.status == "active"
        assert params.customer_type == "Company"
        assert params.balance_min == 100.0
        assert params.balance_max == 1000.0

    def test_status_validation(self):
        """Test customer status validation."""
        # Valid statuses
        params = CustomerQueryParams(status="ACTIVE")
        assert params.status == "active"  # Normalized to lowercase

        params = CustomerQueryParams(status="inactive")
        assert params.status == "inactive"

        # Invalid status
        with pytest.raises(ValidationError) as exc_info:
            CustomerQueryParams(status="pending")
        assert "Status must be 'active' or 'inactive'" in str(exc_info.value)

    def test_customer_to_netsuite_params(self):
        """Test customer params conversion to NetSuite."""
        params = CustomerQueryParams(
            page=1,
            status="active",
            customer_type="Company",
            balance_min=100.0,
            balance_max=1000.0,
        )

        ns_params = params.to_netsuite_params()

        assert ns_params["page"] == "1"
        assert ns_params["status"] == "active"
        assert ns_params["customerType"] == "Company"
        assert ns_params["balanceMin"] == "100.0"
        assert ns_params["balanceMax"] == "1000.0"


class TestInvoiceQueryParams:
    """Tests for invoice-specific query parameters."""

    def test_invoice_specific_params(self):
        """Test invoice-specific parameters."""
        due_since = datetime(2024, 1, 1, tzinfo=UTC)
        due_before = datetime(2024, 12, 31, tzinfo=UTC)

        params = InvoiceQueryParams(
            status="open",
            customer_id=123,
            amount_min=100.0,
            amount_max=1000.0,
            due_date_since=due_since,
            due_date_before=due_before,
        )
        assert params.status == "open"
        assert params.customer_id == 123
        assert params.amount_min == 100.0
        assert params.amount_max == 1000.0
        assert params.due_date_since == due_since
        assert params.due_date_before == due_before

    def test_invoice_to_netsuite_params(self):
        """Test invoice params conversion to NetSuite."""
        params = InvoiceQueryParams(
            page=1,
            status="paid",
            customer_id=456,
            amount_min=50.0,
            due_date_since=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        )

        ns_params = params.to_netsuite_params()

        assert ns_params["page"] == "1"
        assert ns_params["status"] == "paid"
        assert ns_params["customerId"] == "456"
        assert ns_params["amountMin"] == "50.0"
        assert ns_params["dueDateSince"] == "2024-01-01T00:00:00+00:00"


class TestTransactionQueryParams:
    """Tests for transaction-specific query parameters."""

    def test_transaction_specific_params(self):
        """Test transaction-specific parameters."""
        params = TransactionQueryParams(
            transaction_type="Invoice",
            account_id=789,
            posting_period_id=12,
        )
        assert params.transaction_type == "Invoice"
        assert params.account_id == 789
        assert params.posting_period_id == 12

    def test_transaction_to_netsuite_params(self):
        """Test transaction params conversion to NetSuite."""
        params = TransactionQueryParams(
            page=3,
            transaction_type="Payment",
            account_id=100,
            posting_period_id=6,
        )

        ns_params = params.to_netsuite_params()

        assert ns_params["page"] == "3"
        assert ns_params["transactionType"] == "Payment"
        assert ns_params["accountId"] == "100"
        assert ns_params["postingPeriodId"] == "6"
