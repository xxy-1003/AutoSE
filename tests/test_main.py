"""Tests for main FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from autose_platform.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns API information."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "message" in data
    assert "version" in data
    assert "docs" in data
    assert "endpoints" in data
    assert data["version"] == "0.1.0"


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "service" in data


def test_docs_endpoint():
    """Test that API documentation endpoints are accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    
    response = client.get("/redoc")
    assert response.status_code == 200


def test_analyze_endpoint_success():
    """Test the analyze endpoint with valid input."""
    test_data = {
        "text": "Deploy an AI security system supporting 100 cameras with GPU acceleration"
    }
    
    response = client.post("/analyze", json=test_data)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "markdown" in data
    assert "json" in data
    assert "timestamp" in data
    
    # Check data types
    assert isinstance(data["markdown"], str)
    assert isinstance(data["json"], dict)
    assert isinstance(data["timestamp"], str)
    
    # Check JSON structure
    json_data = data["json"]
    assert "requirements" in json_data
    assert "selected_products" in json_data
    assert "validation" in json_data
    assert "reasoning" in json_data
    assert "optimization_suggestions" in json_data


def test_analyze_endpoint_empty_text():
    """Test the analyze endpoint with empty text (should fail validation)."""
    test_data = {
        "text": ""
    }
    
    response = client.post("/analyze", json=test_data)
    
    # Should return 422 Unprocessable Entity for validation error
    assert response.status_code == 422
    data = response.json()
    
    # Check error response structure
    assert "detail" in data


def test_analyze_endpoint_missing_text():
    """Test the analyze endpoint with missing text field."""
    test_data = {}
    
    response = client.post("/analyze", json=test_data)
    
    # Should return 422 Unprocessable Entity for validation error
    assert response.status_code == 422
    data = response.json()
    
    # Check error response structure
    assert "detail" in data


def test_analyze_endpoint_invalid_json():
    """Test the analyze endpoint with invalid JSON."""
    response = client.post("/analyze", data="invalid json")
    
    # Should return 422 Unprocessable Entity
    assert response.status_code == 422
    data = response.json()
    
    # Check error response structure
    assert "detail" in data