import os
from typing import Any, Dict, List, Optional, Union, Annotated

from pydantic import AnyHttpUrl, PostgresDsn, field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "YouTube Scheduler API"
    APP_DESCRIPTION: str = "API for scheduling YouTube video uploads"
    APP_VERSION: str = "0.1.0"
    API_V1_STR: str = "/v1"
    SECRET_KEY: str = "your-secret-key-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    DEBUG: bool = False

    # CORS settings
    CORS_ORIGINS: Union[List[str], str] = Field(default=[])

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from various input formats."""
        if isinstance(v, str):
            # Handle empty string
            if not v:
                return []
            # Handle comma-separated string
            if "," in v and not v.startswith("["):
                return [origin.strip() for origin in v.split(",") if origin.strip()]
            # Try parsing as JSON if it starts with [, otherwise treat as a single origin
            if v.startswith("["):
                try:
                    import json
                    return json.loads(v)
                except json.JSONDecodeError:
                    # If JSON parsing fails, treat as a single origin
                    return [v]
            # Single origin
            return [v]
        # Already a list
        elif isinstance(v, list):
            return v
        # Empty value
        elif v is None:
            return []
        # Invalid type
        raise ValueError(f"Invalid CORS_ORIGINS format: {v}")

    # Database settings
    DATABASE_URL: str = "sqlite:///./app.db"
    
    @field_validator("DATABASE_URL", mode="before")
    def validate_db_url(cls, v: Optional[str]) -> Any:
        if v and v.startswith("postgres://"):
            # Replace postgres:// with postgresql:// for SQLAlchemy 1.4+
            return v.replace("postgres://", "postgresql://", 1)
        return v

    # Google API settings
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/youtube/callback"
    GOOGLE_AUTH_SCOPES: str = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube"

    # Redis settings (for Celery)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # File uploads
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 1024 * 1024 * 100  # 100 MB

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()

# Create upload directory if it doesn't exist
os.makedirs(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), settings.UPLOAD_DIR), exist_ok=True)

