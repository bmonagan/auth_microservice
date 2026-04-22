# config.py
import sys
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = "sqlite:///./data/dev.db"
    REDIS_URL: str = "redis://localhost:6379"
    APP_BASE_URL: str = "http://127.0.0.1:8000"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USE_TLS: bool = True
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "no-reply@example.com"

    model_config = SettingsConfigDict(env_file=".env")


try:
    settings = Settings()  # type: ignore[call-arg]
except Exception as e:
    print(
        f"ERROR: Failed to load settings: {e}\n"
        "Make sure the SECRET_KEY environment variable is set.\n"
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\"",
        file=sys.stderr,
    )
    sys.exit(1)