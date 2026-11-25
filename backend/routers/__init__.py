"""FastAPI API routers grouped by domain."""

from backend.routers import auth, master_data

__all__ = ["auth", "master_data"]
