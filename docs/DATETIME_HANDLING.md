# DateTime Handling Guidelines

## Overview

This document outlines how datetime values are handled throughout the NetSuite Proxy service. Proper datetime handling is critical for a service that interfaces with NetSuite across multiple timezones.

## Core Principle: Always Use Timezone-Aware Datetimes

**We NEVER use naive datetimes in this codebase.** All datetime objects must have timezone information.

### Why?

1. **NetSuite operates globally** - Accounts can be in any timezone
2. **API consistency** - Ambiguous times lead to data errors
3. **DST transitions** - Naive datetimes can't handle daylight saving time correctly
4. **Audit trails** - Accurate timestamps are critical for financial data

## Implementation Guidelines

### 1. Default to UTC

When no timezone is specified, assume UTC:

```python
from datetime import datetime, timezone

# Good - timezone-aware
dt = datetime.now(timezone.utc)

# Bad - naive datetime
dt = datetime.now()  # DON'T DO THIS!
```

### 2. Parsing User Input

When parsing dates from query parameters or API requests, we use Pendulum for robust timezone-aware parsing:

```python
import pendulum

def parse_date_param(date_str: str) -> datetime:
    """Parse date string and return timezone-aware datetime."""
    # Pendulum automatically handles timezone-aware parsing
    # Defaults to UTC if no timezone specified
    # Pendulum DateTime is already a datetime.datetime subclass, no conversion needed
    return pendulum.parse(date_str, tz="UTC")
```

Pendulum advantages:
- Always returns timezone-aware datetimes
- Handles multiple date formats automatically
- No DTZ007 linting warnings
- Cleaner, more maintainable code

### 3. NetSuite API Integration

NetSuite timestamps typically include timezone information:
- Format: `2024-01-01T00:00:00.000-08:00`
- Always preserve the original timezone when available
- Convert to UTC for internal processing if needed

### 4. Database Storage

Store all timestamps in UTC:
- Consistent comparison and sorting
- No ambiguity during DST transitions
- Easy to convert to user's local time

### 5. API Responses

Always return timezone-aware timestamps:
- ISO 8601 format with timezone offset
- Example: `2024-01-01T08:00:00+00:00`

## Code Examples

### Creating Timestamps

```python
from datetime import datetime, timezone

# Current time in UTC
now_utc = datetime.now(timezone.utc)

# Specific time in UTC
specific_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
```

### Converting Timezones

```python
from zoneinfo import ZoneInfo  # Python 3.9+

# Convert UTC to Pacific Time
utc_time = datetime.now(timezone.utc)
pacific_time = utc_time.astimezone(ZoneInfo("America/Los_Angeles"))

# Convert to NetSuite account timezone
account_tz = ZoneInfo("America/New_York")
local_time = utc_time.astimezone(account_tz)
```

### Serialization

```python
# For API responses
def serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO format with timezone."""
    return dt.isoformat()

# Example output: "2024-01-01T12:00:00+00:00"
```

## Testing Guidelines

When writing tests:

```python
from datetime import datetime, timezone

# Good - explicit timezone
test_date = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

# Bad - naive datetime in tests
test_date = datetime(2024, 1, 1, 12, 0, 0)  # DON'T DO THIS!
```

## Common Pitfalls to Avoid

1. **Don't use `datetime.now()`** - Use `datetime.now(timezone.utc)`
2. **Don't use `datetime.utcnow()`** - It returns naive datetime!
3. **Don't ignore timezone in comparisons** - Naive and aware datetimes can't be compared
4. **Don't assume local timezone** - Always be explicit

## Linting and Type Checking

Ruff is configured to warn about naive datetimes:
- `DTZ001`: Checks for `datetime()` without timezone
- `DTZ005`: Checks for `datetime.now()` without timezone
- `DTZ007`: Checks for `strptime()` without timezone handling

**We do not ignore these warnings** - fix them by adding proper timezone handling.

## Migration Strategy

When encountering naive datetimes in the codebase:

1. Determine the intended timezone (usually UTC)
2. Update to use timezone-aware datetime
3. Update tests to use timezone-aware datetimes
4. Document any assumptions made

## References

- [Python datetime documentation](https://docs.python.org/3/library/datetime.html)
- [Pendulum documentation](https://pendulum.eustace.io/)
- [PEP 615 - zoneinfo](https://www.python.org/dev/peps/pep-0615/)
- [NetSuite Date/Time handling](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_1498770293.html)