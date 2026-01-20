"""
Configuration management for TaskLedger backend.
Loads environment variables and provides app-wide settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "TaskLedger"
    environment: str = "development"
    log_level: str = "INFO"
    
    # Google Gemini API
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash-exp"
    
    # Database
    database_url: str = "postgresql+asyncpg://taskledger:taskledger@localhost:5432/taskledger"
    database_echo: bool = False  # Set to True for SQL query logging
    
    # Site Information
    site_url: str = "http://localhost:3000"
    site_name: str = "TaskLedger"
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()
