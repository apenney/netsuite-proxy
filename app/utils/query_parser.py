"""
Query parameter parsing utilities.

This module provides utilities for parsing and converting various query parameter
formats used in the NetSuite API.
"""

from datetime import UTC, datetime
from typing import Any, cast

import pendulum
from pendulum.parsing.exceptions import ParserError

from app.core.logging import get_logger

logger = get_logger(__name__)


def _parse_range(part: str) -> tuple[int, int] | None:
    """Parse a potential range string like '1-100' or '-5--1'."""
    if "-" not in part:
        return None

    # Handle negative numbers in ranges
    if part.startswith("-"):
        remaining = part[1:]
        if "-" in remaining:
            idx = remaining.index("-")
            try:
                start = int("-" + remaining[:idx])
                end = int(remaining[idx + 1 :])
                return (start, end)
            except ValueError:
                return None
    else:
        # Positive start
        idx = part.index("-")
        if idx > 0:
            try:
                start = int(part[:idx])
                end = int(part[idx + 1 :])
                return (start, end)
            except ValueError:
                return None
    return None


def _parse_single_id(part: str) -> int | None:
    """Parse a single ID string."""
    try:
        return int(part)
    except ValueError:
        logger.warning("Failed to parse ID", id_str=part)
        return None


def _process_id_range(start: int, end: int, part: str) -> list[int]:
    """Process an ID range, with validation and limits."""
    if start > end:
        logger.warning(
            "Invalid ID range",
            range_str=part,
            start=start,
            end=end,
        )
        return []

    # Limit range size to prevent memory issues
    if end - start > 10000:
        logger.warning(
            "ID range too large, limiting to 10000 items",
            range_str=part,
            start=start,
            end=end,
        )
        end = start + 10000

    return list(range(start, end + 1))


def parse_id_parameter(ids_param: str | None) -> list[int] | None:
    """
    Parse ID parameter in various formats.

    Supports:
    - Comma-separated: "1,2,3"
    - Ranges: "1-100"
    - Arrays: "[1,2,3]"
    - Mixed: "1,5-10,15"

    Args:
        ids_param: The ID parameter string

    Returns:
        List of integer IDs or None if empty/invalid
    """
    if not ids_param:
        return None

    ids_str = ids_param.strip()

    # Remove array brackets if present
    if ids_str.startswith("[") and ids_str.endswith("]"):
        ids_str = ids_str[1:-1]

    result: list[int] = []
    parts = ids_str.split(",")

    for raw_part in parts:
        part = raw_part.strip()
        if not part:
            continue

        # Try to parse as range
        range_result = _parse_range(part)
        if range_result:
            start, end = range_result
            result.extend(_process_id_range(start, end, part))
        else:
            # Try to parse as single ID
            single_id = _parse_single_id(part)
            if single_id is not None:
                result.append(single_id)

    return result if result else None


def parse_field_list(fields_param: str | None) -> list[str] | None:
    """
    Parse comma-separated field list.

    Args:
        fields_param: Comma-separated field names

    Returns:
        List of field names or None if empty
    """
    if not fields_param:
        return None

    fields = [f.strip() for f in fields_param.split(",") if f.strip()]
    return fields if fields else None


def parse_date_param(date_str: str | None) -> datetime | None:
    """
    Parse date parameter in various formats.

    Supports:
    - ISO format: "2024-01-01T00:00:00"
    - Date only: "2024-01-01"
    - US format: "01/01/2024"

    All returned datetimes are timezone-aware (UTC if no timezone specified).

    Args:
        date_str: Date string to parse

    Returns:
        Parsed datetime with timezone or None if invalid
    """
    if not date_str:
        return None

    date_str = date_str.strip()

    # Check for empty string after stripping
    if not date_str:
        return None

    try:
        # Pendulum automatically handles timezone-aware parsing
        # and can parse many formats including ISO, US, European dates
        # Pendulum DateTime is already a datetime.datetime subclass
        return cast("datetime", pendulum.parse(date_str, tz="UTC"))
    except (ParserError, ValueError):
        # For ambiguous dates like 01/02/2024 (Jan 2 or Feb 1?)
        # Try US format first (MM/DD/YYYY), then European (DD/MM/YYYY)
        if "/" in date_str and len(date_str) == 10:
            parts = date_str.split("/")
            if len(parts) == 3:
                try:
                    # Try US format: MM/DD/YYYY
                    month, day, year = parts
                    dt = pendulum.datetime(int(year), int(month), int(day), tz="UTC")
                    return cast("datetime", dt)
                except (ValueError, ParserError):
                    try:
                        # Try European format: DD/MM/YYYY
                        day, month, year = parts
                        dt = pendulum.datetime(int(year), int(month), int(day), tz="UTC")
                        return cast("datetime", dt)
                    except (ValueError, ParserError):
                        pass

    logger.warning("Failed to parse date", date_str=date_str)
    return None


def parse_boolean_param(bool_str: str | None) -> bool | None:
    """
    Parse boolean parameter.

    Accepts: true/false, yes/no, 1/0, on/off

    Args:
        bool_str: Boolean string to parse

    Returns:
        Boolean value or None if invalid
    """
    if not bool_str:
        return None

    bool_str = bool_str.strip().lower()

    true_values = {"true", "yes", "1", "on", "t", "y"}
    false_values = {"false", "no", "0", "off", "f", "n"}

    if bool_str in true_values:
        return True
    if bool_str in false_values:
        return False

    return None


def parse_float_param(float_str: str | None) -> float | None:
    """
    Parse float parameter.

    Args:
        float_str: Float string to parse

    Returns:
        Float value or None if invalid
    """
    if not float_str:
        return None

    try:
        return float(float_str.strip())
    except ValueError:
        logger.warning("Failed to parse float", float_str=float_str)
        return None


def build_netsuite_filter(params: dict[str, Any]) -> dict[str, Any]:
    """
    Build NetSuite search filter from query parameters.

    Args:
        params: Query parameters dictionary

    Returns:
        NetSuite-compatible filter dictionary
    """
    filters: dict[str, Any] = {}

    # Date range filters
    if created_since := params.get("created_since"):
        filters["dateCreated"] = {
            "operator": "onOrAfter",
            "searchValue": created_since.isoformat()
            if isinstance(created_since, datetime)
            else created_since,
        }

    if created_before := params.get("created_before"):
        filters["dateCreated"] = {
            "operator": "before",
            "searchValue": created_before.isoformat()
            if isinstance(created_before, datetime)
            else created_before,
        }

    if updated_since := params.get("updated_since"):
        filters["lastModifiedDate"] = {
            "operator": "onOrAfter",
            "searchValue": updated_since.isoformat()
            if isinstance(updated_since, datetime)
            else updated_since,
        }

    if updated_before := params.get("updated_before"):
        filters["lastModifiedDate"] = {
            "operator": "before",
            "searchValue": updated_before.isoformat()
            if isinstance(updated_before, datetime)
            else updated_before,
        }

    # ID filters
    if ids := params.get("ids"):
        if isinstance(ids, list):
            filters["internalId"] = {"operator": "anyOf", "searchValue": ids}
        else:
            filters["internalId"] = {"operator": "is", "searchValue": ids}

    # Status filter
    if status := params.get("status"):
        filters["isInactive"] = {"operator": "is", "searchValue": status.lower() == "inactive"}

    # Search term
    if search := params.get("search"):
        filters["_text"] = {"operator": "contains", "searchValue": search}

    # Subsidiary filter
    if subsidiary_id := params.get("subsidiary_id"):
        filters["subsidiary"] = {
            "operator": "anyOf",
            "searchValue": [{"internalId": str(subsidiary_id)}],
        }

    return filters


def extract_pagination_info(response_headers: dict[str, str]) -> dict[str, Any]:
    """
    Extract pagination information from NetSuite response headers.

    Args:
        response_headers: HTTP response headers

    Returns:
        Dictionary with pagination information
    """
    return {
        "search_id": response_headers.get("NETSUITE-SEARCH-ID"),
        "total_records": int(response_headers.get("NETSUITE-TOTAL-RECORDS", "0")),
        "total_pages": int(response_headers.get("NETSUITE-TOTAL-PAGES", "0")),
        "page_size": int(response_headers.get("NETSUITE-PAGE-SIZE", "20")),
    }


def format_netsuite_timestamp(dt: datetime) -> str:
    """
    Format datetime for NetSuite API.

    NetSuite expects timestamps in specific format.

    Args:
        dt: Datetime to format

    Returns:
        Formatted timestamp string
    """
    # NetSuite typically expects ISO format without timezone
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def parse_netsuite_timestamp(timestamp_str: str | None) -> datetime | None:
    """
    Parse NetSuite timestamp string.

    Args:
        timestamp_str: Timestamp from NetSuite

    Returns:
        Parsed datetime or None
    """
    if not timestamp_str:
        return None

    # NetSuite timestamps are typically in format: 2024-01-01T00:00:00.000-08:00
    try:
        # First try with timezone
        dt = datetime.fromisoformat(timestamp_str)
        # If no timezone, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except ValueError:
        pass

    # Try without timezone
    try:
        # Remove timezone suffix if present
        if "+" in timestamp_str or timestamp_str.count("-") > 2:
            # Find the last occurrence of + or -
            for i in range(len(timestamp_str) - 1, -1, -1):
                if timestamp_str[i] in "+-":
                    timestamp_str = timestamp_str[:i]
                    break

        dt = datetime.fromisoformat(timestamp_str)
        # If no timezone, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except ValueError:
        logger.warning("Failed to parse NetSuite timestamp", timestamp=timestamp_str)
        return None
