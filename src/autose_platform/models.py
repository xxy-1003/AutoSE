"""
Data models for AutoSE Platform.

This module contains all Pydantic models for the AutoSE Platform.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class StructuredRequirements(BaseModel):
    """Extracted structured requirements from user input."""
    
    device_count: int = Field(..., ge=1, description="Number of devices/cameras")
    gpu_required: bool = Field(..., description="Whether GPU is required")
    estimated_power_w: int = Field(..., ge=0, description="Estimated power in watts")
    network_ports: int = Field(..., ge=0, description="Required network ports")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "device_count": 100,
                "gpu_required": True,
                "estimated_power_w": 1500,
                "network_ports": 48
            }
        }
    }


class Product(BaseModel):
    """Product from the hardcoded catalog."""
    
    name: str
    power_w: int = Field(..., ge=0, description="Power consumption in watts")
    gpu_count: int = Field(0, ge=0, description="Number of GPUs")
    price: int = Field(..., ge=0, description="Price in USD")
    max_cameras: int = Field(0, ge=0, description="Maximum cameras supported")
    port_count: int = Field(0, ge=0, description="Number of network ports")
    capacity_w: int = Field(0, ge=0, description="Capacity in watts (for UPS)")
    
    def can_support_cameras(self, count: int) -> bool:
        """Check if product can support given number of cameras."""
        return self.max_cameras >= count if self.max_cameras > 0 else True


class ValidationResult(BaseModel):
    """Results from deterministic validation."""
    
    power_check: str = Field(..., description="PASS/FAIL/WARNING")
    power_warning: Optional[str] = None
    network_check: str = Field(..., description="PASS/FAIL/WARNING")
    gpu_check: str = Field(..., description="PASS/FAIL/WARNING")
    warnings: List[str] = Field(default_factory=list)
    
    def is_valid(self) -> bool:
        """Check if all validations passed."""
        return all([
            self.power_check == "PASS",
            self.network_check == "PASS",
            self.gpu_check == "PASS"
        ])


class Proposal(BaseModel):
    """Final proposal output."""
    
    markdown: str = Field(..., description="Markdown formatted proposal")
    json_data: Dict[str, Any] = Field(..., description="JSON reasoning structure", alias="json")
    requirements: StructuredRequirements
    selected_products: List[Product]
    validation: ValidationResult
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# Request/Response models for API endpoints
class RequirementRequest(BaseModel):
    """Request model for requirement analysis endpoint."""
    
    text: str = Field(..., min_length=1, description="Natural language requirement description")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "Deploy an AI security system supporting 100 cameras with GPU acceleration"
            }
        }
    }


class ProposalResponse(BaseModel):
    """Response model for proposal generation endpoint."""
    
    markdown: str = Field(..., description="Markdown formatted proposal")
    json_data: Dict[str, Any] = Field(..., description="JSON reasoning structure", alias="json")
    timestamp: str = Field(..., description="ISO format timestamp of proposal generation")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "markdown": "# Proposal\n\n## Recommended Products...",
                "json": {
                    "requirements": {
                        "device_count": 100,
                        "gpu_required": True,
                        "estimated_power_w": 1500,
                        "network_ports": 48
                    },
                    "selected_products": [
                        {"name": "AI Server X2", "power_w": 1500, "gpu_count": 8, "price": 28000, "max_cameras": 120}
                    ],
                    "validation": {
                        "power_check": "PASS",
                        "network_check": "PASS",
                        "gpu_check": "PASS"
                    }
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    }


class ErrorResponse(BaseModel):
    """Error response model for API endpoints."""
    
    detail: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": "Failed to extract requirements from input text",
                "error_type": "ExtractionError",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    }