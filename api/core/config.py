from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# --- This code finds your .env file ---

# 1. Get the path to this file (app/core/config.py)
ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
# --- End setup ---


class Settings(BaseSettings):
    """Application settings, loaded from .env file."""

    PROJECT_NAME: str = "Medi-Minder API"
    DATABASE_URL: str

    model_config = SettingsConfigDict(
        # Use the explicit path we just built
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore"
    )

# This line reads the .env file and creates the settings object
settings = Settings()