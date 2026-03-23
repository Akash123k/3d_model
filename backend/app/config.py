"""
Configuration management for the application
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "DEBUG"
    
    # Backend
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8283
    
    # Upload limits (100MB default)
    MAX_UPLOAD_SIZE: int = 104857600
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS - Allow all origins in development
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8283,http://127.0.0.1:3000,http://127.0.0.1:5173,http://0.0.0.0:3000,http://0.0.0.0:5173"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # File paths
    UPLOAD_DIR: str = "uploads"
    LOGS_DIR: str = "logs"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables like VITE_API_URL


# Create singleton instance
settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.LOGS_DIR, exist_ok=True)
