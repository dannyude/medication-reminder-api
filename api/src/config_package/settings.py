from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from pydantic import SecretStr


# 1. Get the path to this file (app/core/config.py)
ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Application settings, loaded from .env file."""

    PROJECT_NAME: str = "Medi-Minder API"
    DATABASE_URL: str

    # jwt settings
    SECRET_KEY: str
    ALGORITHM: str

    # token expiration settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # NEW EMAIL SETTINGS ADDED HERE
    MAIL_USERNAME: str
    MAIL_PASSWORD: SecretStr
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    # password reset timer
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15

    # Frontend URL
    FRONTEND_URL: str = "http://localhost:3000"

    # CORS Configuration - Control via environment variable
    # Comma-separated list: "http://localhost:3000,https://app.example.com"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"

    # Environment mode - production, staging, development
    ENVIRONMENT: str = "development"
    MAX_ATTEMPTS_PER_EMAIL: int = 3
    MAX_ATTEMPTS_PER_IP: int = 10
    WINDOW_HOURS: int = 1
    COOLDOWN_MINUTES: int = 15

    REDIS_URL: str = "redis://localhost:6379"

    # Africa's Talking configuration
    AT_API_KEY: str
    AT_USERNAME: str
    AT_SENDER_ID: str
    AT_ENV: str

    # Google's OAuth Client ID
    GOOGLE_CLIENT_ID: str

    # Config to specify the .env file location
    model_config = SettingsConfigDict(
        # Use the explicit path we just built
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",

    )


# This line reads the .env file and creates the settings object
settings = Settings()
