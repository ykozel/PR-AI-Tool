"""Application configuration and settings"""
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "PR Profile"
    debug: bool = False
    secret_key: str = "your-secret-key-change-in-production"

    # Database
    # For local development on Windows, use SQLite (no external DB needed)
    # For production, set DATABASE_URL to PostgreSQL connection string
    database_url: str = "sqlite:///./pr_profile.db"
    database_echo: bool = False

    # CORS
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # AI/ML
    openai_api_key: Optional[str] = None
    ai_model: str = "gpt-4"

    # PDF Processing
    max_file_size: int = 50  # MB
    allowed_file_types: List[str] = ["pdf"]
    temp_upload_dir: str = "/tmp/uploads"

    # Email
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None

    # Security
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
