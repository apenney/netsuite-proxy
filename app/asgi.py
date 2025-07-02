"""
ASGI application entry point for production deployments.
"""

from app.main import app

# Export the app for ASGI servers
__all__ = ["app"]
