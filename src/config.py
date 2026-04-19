# config.py
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"

load_dotenv()  # Load environment variables from .env file
settings = Settings(
    SECRET_KEY=os.getenv("SECRET_KEY", ""),
    DATABASE_URL=os.getenv("DATABASE_URL", "")
)