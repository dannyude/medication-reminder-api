from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path



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
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "Medi Reminder"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    # password reset timer
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15

    # Frontend URL
    FRONTEND_URL: str = "http://localhost:3000"

    # Redis limiter settings
    MAX_ATTEMPTS_PER_EMAIL: int = 3
    MAX_ATTEMPTS_PER_IP: int = 10
    WINDOW_HOURS: int = 1
    COOLDOWN_MINUTES: int = 15

    REDIS_URL: str = "redis://localhost:6379"

    # Config to specify the .env file location
    model_config = SettingsConfigDict(
        # Use the explicit path we just built
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",

    )


# This line reads the .env file and creates the settings object
settings = Settings()
