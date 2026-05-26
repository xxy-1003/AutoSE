"""
Backend orchestrator for AutoSE Platform.

This module contains the main FastAPIBackend class that orchestrates the multi-agent pipeline.
"""

import asyncio
from typing import Dict, Any, List
from datetime import datetime

from .models import (
    StructuredRequirements, 
    Product, 
    ValidationResult, 
    Proposal,
    RequirementRequest,
    ProposalResponse
)
from .config import settings
from .requirement_analyzer import RequirementAnalyzer, ExtractionError
from .product_retriever import ProductRetriever
from .validation_layer import ValidationLayer
from .proposal_generator import ProposalGenerator


class FastAPIBackend:
    """Main backend orchestrator for AutoSE platform."""
    
    def __init__(self):
        """Initialize all agent components."""
        # Initialize all agent components
        self.requirement_analyzer = RequirementAnalyzer()
        self.product_retriever = ProductRetriever()
        self.validator = ValidationLayer()
        self.proposal_generator = ProposalGenerator()
    
    async def analyze_requirement(self, text: str) -> Dict[str, Any]:
        """
        Process requirement through the full pipeline.
        
        Args:
            text: Natural language requirement description
            
        Returns:
            Dictionary containing proposal data
            
        Raises:
            ExtractionError: If requirement extraction fails
            ValidationError: If validation fails
            GenerationError: If proposal generation fails
        """
        try:
            # 1. Extract structured requirements
            requirements = await self.requirement_analyzer.extract(text)
            
            # 2. Retrieve matching products
            products = await self.product_retriever.match(requirements)
            
            # 3. Validate compatibility
            validation = await self.validator.validate(products, requirements)
            
            # 4. Generate proposal
            proposal = await self.proposal_generator.generate(
                requirements, products, validation
            )
            
            return {
                "markdown": proposal.markdown,
                "json": proposal.json_data,
                "timestamp": proposal.timestamp,
                "requirements": requirements.model_dump(),
                "selected_products": [p.model_dump() for p in proposal.selected_products],
                "validation": validation.model_dump()
            }
            
        except Exception as e:
            # Re-raise with appropriate error type
            error_type = type(e).__name__
            if "extract" in str(e).lower():
                raise ExtractionError(f"Requirement extraction failed: {str(e)}")
            elif "validate" in str(e).lower():
                raise ValidationError(f"Validation failed: {str(e)}")
            elif "generate" in str(e).lower():
                raise GenerationError(f"Proposal generation failed: {str(e)}")
            else:
                raise PipelineError(f"Pipeline processing failed: {str(e)}")





# Custom exception classes for error handling
class ExtractionError(Exception):
    """Exception raised when requirement extraction fails."""
    pass


class ValidationError(Exception):
    """Exception raised when validation fails."""
    pass


class GenerationError(Exception):
    """Exception raised when proposal generation fails."""
    pass


class PipelineError(Exception):
    """Exception raised when pipeline processing fails."""
    pass
