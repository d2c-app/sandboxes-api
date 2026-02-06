import logging
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Logging settings
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] | None = None

    # Web server settings
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Background queue settings
    RQ_REDIS_URL: str = "redis://localhost:6379/0"

    AUTH_KEY: str


@lru_cache
def settings() -> Settings:
    return Settings()


if settings().LOG_LEVEL:
    logging.basicConfig(
        level=settings().LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
