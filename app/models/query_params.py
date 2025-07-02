"""
Query parameter models for NetSuite API operations.

This module defines Pydantic models for validating and parsing complex
query parameters used in NetSuite API operations.
"""

import contextlib
from datetime import datetime
from enum import Enum
from typing import Annotated, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from app.types import QueryParams


class SortOrder(str, Enum):
    """Sort order options."""

    ASC = "asc"
    DESC = "desc"


# Note: These individual parameter classes are kept for documentation purposes
# and potential future use, but BaseQueryParams now includes all fields directly
# to avoid issues with basedpyright and multiple inheritance.


class BaseQueryParams(BaseModel):
    """Base class with all query parameter types."""

    # Pagination parameters
    page: Annotated[int, Field(ge=1)] = 1
    page_size: Annotated[int, Field(ge=1, le=1000)] = 20
    search_id: str | None = Field(
        None,
        description="NetSuite search ID for continuing paginated results",
    )

    # Date range parameters
    created_since: datetime | None = Field(
        None,
        description="Filter records created on or after this date",
    )
    created_before: datetime | None = Field(
        None,
        description="Filter records created before this date",
    )
    updated_since: datetime | None = Field(
        None,
        description="Filter records updated on or after this date",
    )
    updated_before: datetime | None = Field(
        None,
        description="Filter records updated before this date",
    )

    # Field selection parameters
    fields: str | None = Field(
        None,
        description="Comma-separated list of fields to include in response",
        examples=["id,name,email", "id,balance,subsidiary.name"],
    )
    body_fields_only: bool = Field(
        False,
        description="Only return body fields (excludes joins/sublists)",
    )

    # ID filter parameters
    ids: str | None = Field(
        None,
        description="Filter by IDs (comma-separated, ranges, or arrays)",
        examples=["1,2,3", "1-100", "[1,2,3]"],
    )

    # Performance parameters
    fast: bool = Field(
        False,
        description="Enable fast mode (minimal data)",
    )
    include_inactive: bool = Field(
        False,
        description="Include inactive records",
    )

    # Sorting parameters
    sort_by: str | None = Field(
        None,
        description="Field to sort by",
        examples=["name", "created_date", "amount"],
    )
    order: SortOrder = Field(
        SortOrder.ASC,
        description="Sort order",
    )

    # Additional common parameters
    search: str | None = Field(
        None,
        description="General search term",
    )
    subsidiary_id: int | None = Field(
        None,
        description="Filter by subsidiary",
    )

    @model_validator(mode="after")
    def validate_date_ranges(self) -> Self:
        """Ensure date ranges are valid."""
        if self.created_since and self.created_before and self.created_since >= self.created_before:
            raise ValueError("created_since must be before created_before")

        if self.updated_since and self.updated_before and self.updated_since >= self.updated_before:
            raise ValueError("updated_since must be before updated_before")

        return self

    @property
    def field_list(self) -> list[str] | None:
        """Parse fields into a list."""
        if not self.fields:
            return None
        return [f.strip() for f in self.fields.split(",") if f.strip()]

    @property
    def id_list(self) -> list[int] | None:
        """Parse IDs into a list of integers."""
        if not self.ids:
            return None

        ids_str = self.ids.strip()
        if ids_str.startswith("[") and ids_str.endswith("]"):
            ids_str = ids_str[1:-1]

        result: list[int] = []

        parts = ids_str.split(",")
        for raw_part in parts:
            part = raw_part.strip()
            if not part:
                continue

            # Check if it's a range (e.g., "1-100")
            if "-" in part and part.count("-") == 1:
                try:
                    start, end = part.split("-")
                    start_int = int(start.strip())
                    end_int = int(end.strip())
                    if start_int <= end_int:
                        result.extend(range(start_int, end_int + 1))
                except ValueError:
                    # Not a valid range, treat as single ID
                    with contextlib.suppress(ValueError):
                        result.append(int(part))
            else:
                # Single ID
                with contextlib.suppress(ValueError):
                    result.append(int(part))

        return result if result else None

    def _add_pagination_params(self, params: QueryParams) -> None:
        """Add pagination parameters."""
        params["page"] = str(self.page)
        params["pageSize"] = str(self.page_size)
        if self.search_id:
            params["searchId"] = self.search_id

    def _add_date_params(self, params: QueryParams) -> None:
        """Add date range parameters."""
        if self.created_since:
            params["createdSince"] = self.created_since.isoformat()
        if self.created_before:
            params["createdBefore"] = self.created_before.isoformat()
        if self.updated_since:
            params["updatedSince"] = self.updated_since.isoformat()
        if self.updated_before:
            params["updatedBefore"] = self.updated_before.isoformat()

    def _add_field_params(self, params: QueryParams) -> None:
        """Add field selection parameters."""
        if self.fields:
            params["fields"] = self.fields
        if self.body_fields_only:
            params["bodyFieldsOnly"] = "true"

    def _add_filter_params(self, params: QueryParams) -> None:
        """Add filter parameters."""
        if self.ids:
            params["ids"] = self.ids
        if self.search:
            params["search"] = self.search
        if self.subsidiary_id:
            params["subsidiaryId"] = str(self.subsidiary_id)

    def _add_performance_params(self, params: QueryParams) -> None:
        """Add performance parameters."""
        if self.fast:
            params["fast"] = "true"
        if self.include_inactive:
            params["includeInactive"] = "true"

    def _add_sort_params(self, params: QueryParams) -> None:
        """Add sorting parameters."""
        if self.sort_by:
            params["sortBy"] = self.sort_by
            params["order"] = self.order.value

    def to_netsuite_params(self) -> QueryParams:
        """Convert to NetSuite-compatible parameters."""
        params: QueryParams = {}

        self._add_pagination_params(params)
        self._add_date_params(params)
        self._add_field_params(params)
        self._add_filter_params(params)
        self._add_performance_params(params)
        self._add_sort_params(params)

        return params


class CustomerQueryParams(BaseQueryParams):
    """Customer-specific query parameters extending base parameters."""

    status: str | None = Field(
        None,
        description="Filter by customer status",
        examples=["active", "inactive"],
    )
    customer_type: str | None = Field(
        None,
        description="Filter by customer type",
    )
    balance_min: float | None = Field(
        None,
        description="Minimum balance filter",
    )
    balance_max: float | None = Field(
        None,
        description="Maximum balance filter",
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        """Validate customer status."""
        if v and v.lower() not in ["active", "inactive"]:
            raise ValueError("Status must be 'active' or 'inactive'")
        return v.lower() if v else None

    def to_netsuite_params(self) -> QueryParams:
        """Convert to NetSuite-compatible parameters."""
        params = super().to_netsuite_params()

        if self.status:
            params["status"] = self.status
        if self.customer_type:
            params["customerType"] = self.customer_type
        if self.balance_min is not None:
            params["balanceMin"] = str(self.balance_min)
        if self.balance_max is not None:
            params["balanceMax"] = str(self.balance_max)

        return params


class InvoiceQueryParams(BaseQueryParams):
    """Invoice-specific query parameters."""

    status: str | None = Field(
        None,
        description="Filter by invoice status",
        examples=["open", "paid", "pending"],
    )
    customer_id: int | None = Field(
        None,
        description="Filter by customer ID",
    )
    amount_min: float | None = Field(
        None,
        description="Minimum amount filter",
    )
    amount_max: float | None = Field(
        None,
        description="Maximum amount filter",
    )
    due_date_since: datetime | None = Field(
        None,
        description="Filter invoices due on or after this date",
    )
    due_date_before: datetime | None = Field(
        None,
        description="Filter invoices due before this date",
    )

    def to_netsuite_params(self) -> QueryParams:
        """Convert to NetSuite-compatible parameters."""
        params = super().to_netsuite_params()

        if self.status:
            params["status"] = self.status
        if self.customer_id:
            params["customerId"] = str(self.customer_id)
        if self.amount_min is not None:
            params["amountMin"] = str(self.amount_min)
        if self.amount_max is not None:
            params["amountMax"] = str(self.amount_max)
        if self.due_date_since:
            params["dueDateSince"] = self.due_date_since.isoformat()
        if self.due_date_before:
            params["dueDateBefore"] = self.due_date_before.isoformat()

        return params


class TransactionQueryParams(BaseQueryParams):
    """Generic transaction query parameters."""

    transaction_type: str | None = Field(
        None,
        description="Filter by transaction type",
        examples=["Invoice", "Payment", "CreditMemo"],
    )
    account_id: int | None = Field(
        None,
        description="Filter by account ID",
    )
    posting_period_id: int | None = Field(
        None,
        description="Filter by posting period",
    )

    def to_netsuite_params(self) -> QueryParams:
        """Convert to NetSuite-compatible parameters."""
        params = super().to_netsuite_params()

        if self.transaction_type:
            params["transactionType"] = self.transaction_type
        if self.account_id:
            params["accountId"] = str(self.account_id)
        if self.posting_period_id:
            params["postingPeriodId"] = str(self.posting_period_id)

        return params
