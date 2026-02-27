"""Configuration module using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    location_name: str = "Paris"
    latitude: float = 48.8566
    longitude: float = 2.3522

    temp_max_threshold: float = 35.0
    uv_threshold: float = 8.0
    precipitation_threshold: float = 8.0

    alert_enabled: bool = True
   
    push_notification_enabled: bool | None = None
    push_notification_topic: str | None = None
   
    email_enabled: bool | None = None
    gmail_smtp_app_password: str | None = None
   
    slack_webhook_url: str | None = None
    discord_webhook_url: str | None = None

    data_dir: str = "./data"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
