"""
Configuration management using Pydantic Settings.
Demonstrates encapsulation and configuration as a class.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Application configuration class.
    
    OOP Principle: Encapsulation
    - Centralizes configuration management
    - Validates environment variables at startup
    """
    
    # Database
    MONGO_URI: str
    
    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Email Configuration (optional)
    EMAIL_USER: str = ""
    EMAIL_PASS: str = ""
    
    # Server
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Singleton instance
settings = Settings()
