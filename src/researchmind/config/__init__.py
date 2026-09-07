"""Configuration module."""
import functools

from .settings import Settings


@functools.lru_cache()
def get_settings() -> Settings:
    """Get the cached application settings.
    
    Returns:
        Settings: The application settings instance.
    """
    return Settings()
