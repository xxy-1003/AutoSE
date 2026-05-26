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
            # 1. Extract structured requirements with additional info
            requirements, additional_info = await self.requirement_analyzer.extract(text)
            
            # 2. Retrieve matching products with project type and budget
            project_type = additional_info.get("project_type", "unknown")
            budget_limit = additional_info.get("budget_limit", 0)
            
            products = await self.product_retriever.match(
                requirements, 
                project_type=project_type if project_type != "unknown" else None,
                budget_limit=budget_limit if budget_limit > 0 else None
            )
            
            # 3. Validate compatibility
            validation = await self.validator.validate(products, requirements)
            
            # 4. Generate proposal with additional info
            proposal = await self.proposal_generator.generate(
                requirements, products, validation, additional_info
            )
            
            return {
                "markdown": proposal.markdown,
                "json": proposal.json_data,
                "timestamp": proposal.timestamp,
                "requirements": requirements.model_dump(),
                "selected_products": products,  # Already dictionaries
                "validation": validation.model_dump(),
                "additional_info": additional_info
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
    
    async def analyze_intelligently(self, text: str) -> Dict[str, Any]:
        """
        Process requirement through intelligent pipeline.
        
        Args:
            text: Natural language requirement description
            
        Returns:
            Dictionary containing intelligent proposal data
            
        Raises:
            ExtractionError: If analysis fails
        """
        try:
            # 1. Perform intelligent analysis
            analysis = await self.requirement_analyzer.analyze_intelligently(text)
            
            # 2. Extract traditional requirements for validation
            requirements, additional_info = await self.requirement_analyzer.extract(text)
            
            # 3. Match products intelligently
            matching_results = self.product_retriever.match_intelligently(analysis)
            
            # 4. Check if we have exact matches
            exact_matches = matching_results.get("exact_matches", [])
            missing_products = matching_results.get("missing_products", [])
            
            # 5. If no exact match found, return no-match response
            if not exact_matches and missing_products:
                no_match_response = self.product_retriever.generate_no_match_response(
                    missing_products[0], analysis
                )
                return {
                    "success": False,
                    "no_exact_match": True,
                    "analysis": analysis,
                    "no_match_response": no_match_response,
                    "message": f"No exact match found for '{missing_products[0]}'",
                    "options": no_match_response.get("options", [])
                }
            
            # 6. Get all products for validation
            all_products = (
                matching_results.get("exact_matches", []) +
                matching_results.get("required_components", []) +
                matching_results.get("optional_components", [])
            )
            
            # 7. Validate compatibility
            validation = await self.validator.validate(all_products, requirements)
            
            # 8. Generate intelligent proposal
            intelligent_proposal = self.proposal_generator.generate_intelligent_proposal(
                analysis, matching_results, requirements, validation
            )
            
            # 9. Check for alert system questions
            alert_questions = intelligent_proposal.get("alert_system_questions", [])
            
            return {
                "success": True,
                "intelligent_analysis": True,
                "analysis": analysis,
                "matching_results": matching_results,
                "requirements": requirements.model_dump(),
                "selected_products": all_products,
                "validation": validation.model_dump(),
                "explanations": intelligent_proposal.get("explanations", []),
                "total_cost": matching_results.get("total_cost", 0),
                "recommendation_summary": intelligent_proposal.get("recommendation_summary", ""),
                "alert_system_questions": alert_questions,
                "has_alert_questions": len(alert_questions) > 0,
                "message": "Intelligent analysis completed successfully"
            }
            
        except Exception as e:
            raise ExtractionError(f"Intelligent analysis failed: {str(e)}")


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