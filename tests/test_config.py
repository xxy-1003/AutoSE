"""Tests for configuration management."""

import os
from autose_platform.config import Settings


def test_settings_defaults():
    """Test that settings have appropriate defaults."""
    settings = Settings()
    
    assert settings.APP_NAME == "AutoSE Platform"
    assert settings.HOST == "0.0.0.0"
    assert settings.PORT == 8000
    assert settings.POWER_THRESHOLD_W == 5000


def test_settings_from_env(monkeypatch):
    """Test that settings can be loaded from environment variables."""
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("POWER_THRESHOLD_W", "6000")
    
    settings = Settings()
    
    assert settings.DEBUG is True
    assert settings.PORT == 9000
    assert settings.POWER_THRESHOLD_W == 6000


def test_cors_origins_parsing(monkeypatch):
    """Test that CORS origins are properly parsed from comma-separated string."""
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080,https://example.com")
    
    settings = Settings()
    
    assert len(settings.CORS_ORIGINS) == 3
    assert "http://localhost:3000" in settings.CORS_ORIGINS
    assert "http://localhost:8080" in settings.CORS_ORIGINS
    assert "https://example.com" in settings.CORS_ORIGINS