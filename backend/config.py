"""
YeetChess Configuration
Loads environment variables with Pydantic Settings for type-safe access.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application Settings - loaded from environment or .env file"""
    
    # Database
    database_url: str = "postgresql+asyncpg://yeetchess:yeetchess_dev_password@db:5432/yeetchess"
    
    # Redis
    redis_url: str = "redis://redis:6379"
    
    # FastAPI
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # JWT & Authentication
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_expiration_minutes: int = 15
    jwt_refresh_expiration_days: int = 7
    
    # Frontend
    frontend_port: int = 5173
    vite_api_url: str = "http://localhost:8000"
    vite_ws_url: str = "ws://localhost:8000"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
