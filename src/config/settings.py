from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings."""

    # Google Gemini API Configuration
    google_api_key: str

    # Model Configuration
    model_name: str = "gemini-2.0-flash-exp"
    temperature: float = 0.1
    max_iterations: int = 10

    # Application Configuration
    upload_dir: str = "./uploads"
    log_level: str = "INFO"

    # API Configuration
    api_title: str = "Agentic RAG Excel Analyzer"
    api_version: str = "1.0.0"
    api_description: str = "AI-powered Excel data analysis with plan-and-execute agent"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
