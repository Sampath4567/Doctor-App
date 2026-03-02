from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "doctor_app"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""

    SECRET_KEY: str = "changeme"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    EMAIL_FROM_NAME: str = "DoctorBook"

    FRONTEND_URL: str = "http://localhost:5173"

    # Add this new field:
    GOOGLE_API_KEY: Optional[str] = None
    # You would add these if you want to use them:
    OPENAI_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "ollama" # Default to ollama

    class Config:
        env_file = ".env"
        extra = "forbid"
   
settings = Settings()
