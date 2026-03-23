"""
Dependency injection for API routes
"""

from functools import lru_cache
from app.config import settings


def get_settings() -> dict:
    """Get application settings"""
    return {
        "max_upload_size": settings.MAX_UPLOAD_SIZE,
        "upload_dir": settings.UPLOAD_DIR,
        "redis_url": settings.REDIS_URL,
        "environment": settings.ENVIRONMENT
    }
