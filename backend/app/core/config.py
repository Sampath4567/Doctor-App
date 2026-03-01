from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Central application configuration.

    Values are loaded from environment variables and an optional `.env` file
    located in the backend directory.
    """

    # Application
    PROJECT_NAME: str = "DoctorBook API"
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # Database
    DB_HOST: str = "db"
    DB_PORT: int = 3306
    DB_NAME: str = "doctor_app"
    DB_USER: str = "doctor_app"
    DB_PASSWORD: str = "doctor_app"

    # Security
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """
    Return a singleton Settings instance.

    Using an lru_cache avoids re-parsing environment variables on each import.
    """

    return Settings()

