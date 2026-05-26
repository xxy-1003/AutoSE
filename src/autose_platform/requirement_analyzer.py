"""
Requirement Analyzer Agent for AutoSE Platform.

This module implements Agent 1 that extracts structured fields from natural language
using Chutes API (OpenAI-compatible) with DeepSeek-V3-0324 model.
"""

import json
import re
from typing import Dict, Any, Optional
import httpx
from pydantic import ValidationError as PydanticValidationError

from .models import StructuredRequirements
from .config import settings


class RequirementAnalyzer:
    """Agent 1: Extracts structured requirements from natural language text."""
    
    def __init__(self):
        """Initialize the requirement analyzer with API configuration."""
        # Use Chutes API by default, fall back to DeepSeek if Chutes not configured
        self.api_key = settings.CHUTES_API_KEY or settings.DEEPSEEK_API_KEY
        self.api_url = settings.CHUTES_API_URL or settings.DEEPSEEK_API_URL
        self.model = settings.CHUTES_MODEL or settings.DEEPSEEK_MODEL
        
        # Determine which API we're using for logging/debugging
        self.using_chutes = bool(settings.CHUTES_API_KEY)
        self.using_deepseek = bool(settings.DEEPSEEK_API_KEY) and not self.using_chutes
        
        # Fallback patterns for simple extraction
        self.fallback_patterns = {
            "device_count": [
                r"(\d+)\s*(?:camera|device|sensor)s?",
                r"support(?:ing)?\s*(\d+)\s*(?:camera|device|sensor)s?",
                r"(\d+)-camera",
                r"(\d+)\s*cameras?"
            ],
            "gpu_required": [
                r"gpu",
                r"gpu\s*acceleration",
                r"graphics\s*processing",
                r"nvidia",
                r"cuda",
                r"ai\s*inference",
                r"deep\s*learning"
            ],
            "estimated_power_w": [
                r"(\d+)\s*w(?:atts?)?",
                r"power\s*consumption\s*(\d+)",
                r"(\d+)\s*w\s*power"
            ],
            "network_ports": [
                r"(\d+)\s*port",
                r"(\d+)-port",
                r"network\s*ports?\s*(\d+)",
                r"switch\s*with\s*(\d+)\s*ports"
            ]
        }
    
    async def extract(self, text: str) -> StructuredRequirements:
        """
        Extract structured fields from natural language text.
        
        Args:
            text: Natural language requirement description
            
        Returns:
            StructuredRequirements object with extracted fields
            
        Raises:
            ExtractionError: If extraction fails
        """
        try:
            # First try LLM extraction
            structured_data = await self._extract_with_llm(text)
            
            # Validate and return
            return StructuredRequirements(**structured_data)
            
        except Exception as llm_error:
            # If LLM extraction fails, try fallback regex extraction
            try:
                structured_data = self._extract_with_fallback(text)
                return StructuredRequirements(**structured_data)
            except Exception as fallback_error:
                # Both methods failed
                raise ExtractionError(
                    f"Failed to extract requirements from text: {text}. "
                    f"LLM error: {llm_error}. Fallback error: {fallback_error}"
                )
    
    async def _extract_with_llm(self, text: str) -> Dict[str, Any]:
        """
        Extract structured fields using Chutes API (OpenAI-compatible).
        
        Args:
            text: Natural language requirement description
            
        Returns:
            Dictionary with extracted fields
            
        Raises:
            Exception: If API call fails or response is invalid
        """
        if not self.api_key:
            raise Exception("LLM API key not configured. Please set CHUTES_API_KEY or DEEPSEEK_API_KEY in .env file")
        
        # Prepare the prompt for structured extraction
        prompt = self._build_extraction_prompt(text)
        
        # Prepare API request (OpenAI-compatible format)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a requirement extraction assistant. Extract structured data from user requirements."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 500,
            "response_format": {"type": "json_object"}  # Request JSON response format
        }
        
        # Make API call
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(f"{self.api_url}/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                
                # Extract content from response (OpenAI-compatible format)
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                elif "output" in result:  # Alternative response format
                    content = result["output"]
                else:
                    raise KeyError("No valid response content found in API response")
                
                # Parse JSON from response
                return self._parse_llm_response(content)
                
            except httpx.RequestError as e:
                # Provide more specific error message
                api_name = "Chutes" if self.using_chutes else "DeepSeek"
                raise Exception(f"{api_name} API request failed: {e}")
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                raise Exception(f"Failed to parse API response: {e}")
    
    def _build_extraction_prompt(self, text: str) -> str:
        """Build prompt for structured extraction."""
        return f"""
        Extract the following structured fields from the user requirement:
        
        User requirement: "{text}"
        
        Extract these fields:
        1. device_count: integer - number of devices/cameras
        2. gpu_required: boolean - whether GPU is required
        3. estimated_power_w: integer - estimated power in watts
        4. network_ports: integer - required network ports
        
        If a field cannot be determined from the text, use these defaults:
        - device_count: 1
        - gpu_required: false
        - estimated_power_w: 100
        - network_ports: 1
        
        Return ONLY a valid JSON object with these exact keys:
        {{
            "device_count": <integer>,
            "gpu_required": <boolean>,
            "estimated_power_w": <integer>,
            "network_ports": <integer>
        }}
        
        Do not include any additional text, explanations, or markdown formatting.
        """
    
    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response."""
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["device_count", "gpu_required", "estimated_power_w", "network_ports"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            return data
        else:
            raise ValueError("No JSON found in LLM response")
    
    def _extract_with_fallback(self, text: str) -> Dict[str, Any]:
        """
        Extract fields using regex patterns as fallback.
        
        Args:
            text: Natural language requirement description
            
        Returns:
            Dictionary with extracted fields
        """
        text_lower = text.lower()
        
        # Extract device_count
        device_count = 1
        for pattern in self.fallback_patterns["device_count"]:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    device_count = int(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue
        
        # Extract gpu_required
        gpu_required = False
        for pattern in self.fallback_patterns["gpu_required"]:
            if re.search(pattern, text_lower):
                gpu_required = True
                break
        
        # Extract estimated_power_w
        estimated_power_w = 100
        for pattern in self.fallback_patterns["estimated_power_w"]:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    estimated_power_w = int(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue
        
        # Extract network_ports
        network_ports = 1
        for pattern in self.fallback_patterns["network_ports"]:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    network_ports = int(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue
        
        return {
            "device_count": device_count,
            "gpu_required": gpu_required,
            "estimated_power_w": estimated_power_w,
            "network_ports": network_ports
        }


class ExtractionError(Exception):
    """Exception raised when requirement extraction fails."""
    pass