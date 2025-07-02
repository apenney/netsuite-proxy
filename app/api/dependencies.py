"""
Common dependency injection patterns for FastAPI endpoints.

This module provides type aliases and dependency functions that can be reused
across different endpoints to maintain consistency and reduce boilerplate.
"""

from typing import Annotated

from fastapi import Depends

from app.core.config import NetSuiteConfig, Settings, get_netsuite_config, get_settings

# Type aliases for common dependencies
SettingsDep = Annotated[Settings, Depends(get_settings)]
NetSuiteConfigDep = Annotated[NetSuiteConfig, Depends(get_netsuite_config)]


# Additional dependency functions can be added here as needed
# For example:
# async def get_current_user(...) -> User:
#     ...
# CurrentUserDep = Annotated[User, Depends(get_current_user)]
