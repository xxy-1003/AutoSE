"""
Configuration management for AutoSE Platform.

This module handles environment variables and application settings.
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings
    APP_NAME: str = "AutoSE Platform"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS settings - comma-separated string that will be split
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    # LLM API settings - Chutes API (OpenAI-compatible)
    CHUTES_API_KEY: str = ""
    CHUTES_API_URL: str = "https://llm.chutes.ai/v1"
    CHUTES_MODEL: str = "deepseek-ai/DeepSeek-V3-0324"
    
    # Legacy DeepSeek settings (for backward compatibility)
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/v1/chat/completions"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600  # 1 hour
    
    # Cache settings
    CACHE_TTL: int = 300  # 5 minutes
    
    # Validation settings
    POWER_THRESHOLD_W: int = 5000
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    @property
    def USING_CHUTES(self) -> bool:
        """Check if using Chutes API."""
        return bool(self.CHUTES_API_KEY)
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create global settings instance
settings = Settings()