"""
Requirement Analyzer Agent for AutoSE Platform.

This module implements Agent 1 that extracts structured fields from natural language
using Chutes API (OpenAI-compatible) with DeepSeek-V3-0324 model.
"""

import json
import re
from typing import Dict, Any, Optional, Tuple, List
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
        
        # Project type detection patterns
        self.project_type_patterns = {
            "security_system": [
                r"security\s*system",
                r"surveillance",
                r"camera",
                r"monitoring",
                r"video\s*recording",
                r"nvr",
                r"dvr",
                r"cctv"
            ],
            "smart_home": [
                r"smart\s*home",
                r"home\s*automation",
                r"smart\s*house",
                r"home\s*control",
                r"home\s*iot",
                r"connected\s*home"
            ],
            "office_network": [
                r"office\s*network",
                r"corporate\s*network",
                r"business\s*network",
                r"enterprise\s*network",
                r"wifi\s*network",
                r"lan\s*setup"
            ],
            "data_center": [
                r"data\s*center",
                r"server\s*room",
                r"server\s*farm",
                r"hosting\s*infrastructure",
                r"cloud\s*infrastructure"
            ],
            "retail_surveillance": [
                r"retail\s*security",
                r"store\s*security",
                r"shop\s*monitoring",
                r"retail\s*camera",
                r"point\s*of\s*sale\s*security"
            ]
        }
        
        # Negotiation intent detection patterns
        self.negotiation_patterns = {
            "complaining": [
                r"wrong",
                r"not\s+good",
                r"not\s+suitable",
                r"not\s+right",
                r"doesn't\s+match",
                r"doesn't\s+fit",
                r"not\s+reasonable",
                r"not\s+what\s+I\s+need",
                r"not\s+what\s+I\s+want"
            ],
            "rejecting": [
                r"too\s+expensive",
                r"too\s+costly",
                r"too\s+much",
                r"over\s+budget",
                r"can't\s+afford",
                r"price\s+is\s+high",
                r"cost\s+is\s+high"
            ],
            "asking_for_lower_price": [
                r"cheaper",
                r"lower\s+price",
                r"reduce\s+price",
                r"cut\s+price",
                r"budget\s+constraint",
                r"budget\s+limit",
                r"budget\s+=\s*\d+",
                r"\$\d+"
            ],
            "asking_for_fewer_devices": [
                r"fewer\s+cameras",
                r"reduce\s+cameras",
                r"less\s+devices",
                r"fewer\s+devices",
                r"simplify",
                r"simpler\s+solution",
                r"minimum\s+setup"
            ],
            "asking_for_alternative": [
                r"alternative",
                r"different",
                r"other\s+option",
                r"another\s+way",
                r"what\s+else",
                r"show\s+me\s+options",
                r"compare"
            ]
        }
        
        # Fallback patterns for simple extraction
        self.fallback_patterns = {
            "device_count": [
                r"(\d+)\s*(?:camera|device|sensor|room|user|port|plug|light)s?",
                r"support(?:ing)?\s*(\d+)\s*(?:camera|device|sensor|room|user|port|plug|light)s?",
                r"(\d+)-camera",
                r"(\d+)\s*cameras?",
                r"(\d+)\s*bedroom",
                r"(\d+)\s*room"
            ],
            "gpu_required": [
                r"gpu",
                r"gpu\s*acceleration",
                r"graphics\s*processing",
                r"nvidia",
                r"cuda",
                r"ai\s*inference",
                r"deep\s*learning",
                r"machine\s*learning",
                r"computer\s*vision"
            ],
            "estimated_power_w": [
                r"(\d+)\s*w(?:atts?)?",
                r"power\s*consumption\s*(\d+)",
                r"(\d+)\s*w\s*power",
                r"(\d+)\s*watt"
            ],
            "network_ports": [
                r"(\d+)\s*port",
                r"(\d+)-port",
                r"network\s*ports?\s*(\d+)",
                r"switch\s*with\s*(\d+)\s*ports",
                r"(\d+)\s*ethernet\s*ports?"
            ],
            "camera_count": [
                r"(\d+)\s*camera",
                r"(\d+)\s*cameras",
                r"camera\s*count\s*(\d+)",
                r"(\d+)\s*security\s*cameras?"
            ],
            "room_count": [
                r"(\d+)\s*room",
                r"(\d+)\s*bedroom",
                r"(\d+)\s*living\s*room",
                r"(\d+)\s*office",
                r"room\s*count\s*(\d+)"
            ],
            "user_count": [
                r"(\d+)\s*user",
                r"(\d+)\s*employee",
                r"(\d+)\s*staff",
                r"user\s*count\s*(\d+)",
                r"(\d+)\s*people"
            ],
            "budget_limit": [
                r"\$(\d+(?:,\d+)*(?:\.\d+)?)",
                r"(\d+(?:,\d+)*(?:\.\d+)?)\s*dollars",
                r"budget\s*of\s*\$?(\d+(?:,\d+)*(?:\.\d+)?)",
                r"cost\s*less\s*than\s*\$?(\d+(?:,\d+)*(?:\.\d+)?)",
                r"under\s*\$?(\d+(?:,\d+)*(?:\.\d+)?)",
                r"budget\s*=\s*(\d+)",
                r"budget\s*:\s*\$?(\d+)"
            ],
            "constraint_modification": [
                r"reduce\s+to\s+(\d+)\s*cameras",
                r"cameras\s*=\s*(\d+)",
                r"devices\s*=\s*(\d+)",
                r"only\s+(\d+)\s*cameras",
                r"maximum\s+(\d+)\s*cameras"
            ]
        }
    
    async def extract(self, text: str) -> Tuple[StructuredRequirements, Dict[str, Any]]:
        """
        Extract structured fields from natural language text.
        
        Args:
            text: Natural language requirement description
            
        Returns:
            Tuple of (StructuredRequirements, additional_info) where additional_info
            contains project_type, camera_count, room_count, user_count, budget_limit
            
        Raises:
            ExtractionError: If extraction fails
        """
        try:
            # First try LLM extraction
            structured_data, additional_info = await self._extract_with_llm(text)
            
            # Validate and return
            return StructuredRequirements(**structured_data), additional_info
            
        except Exception as llm_error:
            # If LLM extraction fails, try fallback regex extraction
            try:
                structured_data, additional_info = self._extract_with_fallback(text)
                return StructuredRequirements(**structured_data), additional_info
            except Exception as fallback_error:
                # Both methods failed
                raise ExtractionError(
                    f"Failed to extract requirements from text: {text}. "
                    f"LLM error: {llm_error}. Fallback error: {fallback_error}"
                )
    
    async def analyze_intelligently(self, text: str) -> Dict[str, Any]:
        """
        Perform intelligent analysis of user request using LLM reasoning.
        
        Args:
            text: Natural language requirement description
            
        Returns:
            Dictionary with structured reasoning output as specified in Part 3
            
        Raises:
            ExtractionError: If analysis fails
        """
        try:
            return await self._analyze_with_llm_reasoning(text)
        except Exception as e:
            # Fallback to basic analysis
            try:
                return self._analyze_with_fallback_reasoning(text)
            except Exception as fallback_error:
                raise ExtractionError(
                    f"Failed to analyze requirements intelligently: {text}. "
                    f"LLM error: {e}. Fallback error: {fallback_error}"
                )
    
    async def _extract_with_llm(self, text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Extract structured fields using Chutes API (OpenAI-compatible).
        
        Args:
            text: Natural language requirement description
            
        Returns:
            Tuple of (structured_data, additional_info)
            
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
        
        Additionally, extract these optional fields if mentioned:
        5. camera_count: integer - number of cameras specifically (if different from device_count)
        6. room_count: integer - number of rooms
        7. user_count: integer - number of users/employees
        8. budget_limit: integer - budget limit in USD (remove commas, convert to integer)
        9. project_type: string - one of: security_system, smart_home, office_network, data_center, retail_surveillance, or "unknown"
        
        If a field cannot be determined from the text, use these defaults:
        - device_count: 1
        - gpu_required: false
        - estimated_power_w: 100
        - network_ports: 1
        - camera_count: 0 (if not mentioned)
        - room_count: 0 (if not mentioned)
        - user_count: 0 (if not mentioned)
        - budget_limit: 0 (if not mentioned, meaning no budget limit)
        - project_type: "unknown"
        
        Return ONLY a valid JSON object with these exact keys:
        {{
            "device_count": <integer>,
            "gpu_required": <boolean>,
            "estimated_power_w": <integer>,
            "network_ports": <integer>,
            "camera_count": <integer>,
            "room_count": <integer>,
            "user_count": <integer>,
            "budget_limit": <integer>,
            "project_type": <string>
        }}
        
        Do not include any additional text, explanations, or markdown formatting.
        """
    
    def _parse_llm_response(self, content: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Parse JSON from LLM response and separate into structured_data and additional_info."""
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
            
            # Separate structured data from additional info
            structured_data = {
                "device_count": data["device_count"],
                "gpu_required": data["gpu_required"],
                "estimated_power_w": data["estimated_power_w"],
                "network_ports": data["network_ports"]
            }
            
            additional_info = {
                "camera_count": data.get("camera_count", 0),
                "room_count": data.get("room_count", 0),
                "user_count": data.get("user_count", 0),
                "budget_limit": data.get("budget_limit", 0),
                "project_type": data.get("project_type", "unknown")
            }
            
            return structured_data, additional_info
        else:
            raise ValueError("No JSON found in LLM response")
    
    def _extract_with_fallback(self, text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Extract fields using regex patterns as fallback.
        
        Args:
            text: Natural language requirement description
            
        Returns:
            Tuple of (structured_data, additional_info)
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
        
        # Extract camera_count
        camera_count = 0
        for pattern in self.fallback_patterns["camera_count"]:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    camera_count = int(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue
        
        # Extract room_count
        room_count = 0
        for pattern in self.fallback_patterns["room_count"]:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    room_count = int(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue
        
        # Extract user_count
        user_count = 0
        for pattern in self.fallback_patterns["user_count"]:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    user_count = int(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue
        
        # Extract budget_limit
        budget_limit = 0
        for pattern in self.fallback_patterns["budget_limit"]:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    # Remove commas and convert to integer
                    budget_str = match.group(1).replace(',', '')
                    budget_limit = int(float(budget_str))
                    break
                except (ValueError, IndexError):
                    continue
        
        # Detect project type
        project_type = "unknown"
        for proj_type, patterns in self.project_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    project_type = proj_type
                    break
            if project_type != "unknown":
                break
        
        # If camera_count is mentioned but device_count is default, use camera_count
        if camera_count > 0 and device_count == 1:
            device_count = camera_count
        
        structured_data = {
            "device_count": device_count,
            "gpu_required": gpu_required,
            "estimated_power_w": estimated_power_w,
            "network_ports": network_ports
        }
        
        additional_info = {
            "camera_count": camera_count,
            "room_count": room_count,
            "user_count": user_count,
            "budget_limit": budget_limit,
            "project_type": project_type
        }
        
        return structured_data, additional_info
    
    def detect_project_type(self, text: str) -> str:
        """
        Detect project type from text using patterns.
        
        Args:
            text: Natural language requirement description
            
        Returns:
            Project type string
        """
        text_lower = text.lower()
        
        for project_type, patterns in self.project_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return project_type
        
        return "unknown"
    
    def detect_negotiation_intent(self, text: str) -> Dict[str, bool]:
        """
        Detect negotiation intent from user text.
        
        Args:
            text: User input text
            
        Returns:
            Dictionary with negotiation intent flags
        """
        text_lower = text.lower()
        intent = {
            "is_negotiating": False,
            "is_complaining": False,
            "is_rejecting": False,
            "wants_lower_price": False,
            "wants_fewer_devices": False,
            "wants_alternative": False
        }
        
        # Check each negotiation pattern
        for intent_type, patterns in self.negotiation_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    intent["is_negotiating"] = True
                    
                    if intent_type == "complaining":
                        intent["is_complaining"] = True
                    elif intent_type == "rejecting":
                        intent["is_rejecting"] = True
                    elif intent_type == "asking_for_lower_price":
                        intent["wants_lower_price"] = True
                    elif intent_type == "asking_for_fewer_devices":
                        intent["wants_fewer_devices"] = True
                    elif intent_type == "asking_for_alternative":
                        intent["wants_alternative"] = True
        
        return intent
    
    def extract_constraints_from_negotiation(self, text: str) -> Dict[str, Any]:
        """
        Extract constraints from negotiation text.
        
        Args:
            text: User negotiation text
            
        Returns:
            Dictionary with extracted constraints
        """
        text_lower = text.lower()
        constraints = {
            "budget_limit": 0,
            "device_count": None,
            "camera_count": None,
            "modifications": []
        }
        
        # Extract budget limit
        for pattern in self.fallback_patterns["budget_limit"]:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    budget_str = match.group(1).replace(',', '')
                    constraints["budget_limit"] = int(float(budget_str))
                    break
                except (ValueError, IndexError):
                    continue
        
        # Extract device/camera count modifications
        for pattern in self.fallback_patterns["constraint_modification"]:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    count = int(match.group(1))
                    constraints["device_count"] = count
                    constraints["camera_count"] = count
                    constraints["modifications"].append(f"Reduce to {count} devices/cameras")
                    break
                except (ValueError, IndexError):
                    continue
        
        # Extract device count from general patterns
        if constraints["device_count"] is None:
            for pattern in self.fallback_patterns["device_count"]:
                match = re.search(pattern, text_lower)
                if match:
                    try:
                        constraints["device_count"] = int(match.group(1))
                        break
                    except (ValueError, IndexError):
                        continue
        
        # Extract camera count from specific patterns
        if constraints["camera_count"] is None:
            for pattern in self.fallback_patterns["camera_count"]:
                match = re.search(pattern, text_lower)
                if match:
                    try:
                        constraints["camera_count"] = int(match.group(1))
                        break
                    except (ValueError, IndexError):
                        continue
        
        return constraints
    
    async def _analyze_with_llm_reasoning(self, text: str) -> Dict[str, Any]:
        """
        Perform intelligent analysis using LLM reasoning.
        
        Args:
            text: Natural language requirement description
            
        Returns:
            Dictionary with structured reasoning output
        """
        if not self.api_key:
            raise Exception("LLM API key not configured. Please set CHUTES_API_KEY or DEEPSEEK_API_KEY in .env file")
        
        # Prepare the prompt for intelligent reasoning
        prompt = self._build_intelligent_reasoning_prompt(text)
        
        # Prepare API request (OpenAI-compatible format)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an intelligent sales engineer assistant. Analyze user requirements and provide structured reasoning about required components."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 1000,
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
                return self._parse_intelligent_reasoning_response(content)
                
            except httpx.RequestError as e:
                # Provide more specific error message
                api_name = "Chutes" if self.using_chutes else "DeepSeek"
                raise Exception(f"{api_name} API request failed: {e}")
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                raise Exception(f"Failed to parse API response: {e}")
    
    def _build_intelligent_reasoning_prompt(self, text: str) -> str:
        """Build prompt for intelligent reasoning analysis."""
        return f"""
        Analyze the user's requirement and provide structured reasoning about what they need.
        
        User requirement: "{text}"
        
        Analyze and provide output in this exact JSON format:
        {{
            "goal": "what user wants to achieve in 1-2 sentences",
            "core_products": ["list of product types mentioned or implied"],
            "required_components": ["what MUST be added for a working system"],
            "optional_components": ["nice-to-have additions"],
            "missing_info": ["what needs to be asked to provide better recommendations"],
            "reasoning": "detailed explanation of why these components are needed"
        }}
        
        Guidelines:
        1. For "flood detector and alert system": 
           - goal: "detect flooding and receive alerts"
           - core_products: ["flood_detector"]
           - required_components: ["gateway", "notification_service"]
           - optional_components: ["siren"]
           - missing_info: ["mobile alerts or local siren?", "indoor or outdoor?"]
           - reasoning: "A flood sensor cannot send alerts alone; it needs a gateway to connect to internet and a notification service to send alerts."
        
        2. DO NOT hardcode rules like "if flood → add gateway". Instead, reason about what's needed.
        3. Think about complete systems: sensors need connectivity, alerts need notification methods.
        4. If user asks for something specific (like "flood detector"), check if it exists in catalog.
        5. If no exact match exists, identify what's missing and ask clarifying questions.
        6. Consider power requirements, connectivity, and user interface needs.
        
        Return ONLY the JSON object, no additional text.
        """
    
    def _parse_intelligent_reasoning_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from intelligent reasoning response."""
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["goal", "core_products", "required_components", "optional_components", "missing_info", "reasoning"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            return data
        else:
            raise ValueError("No JSON found in LLM response")
    
    def _analyze_with_fallback_reasoning(self, text: str) -> Dict[str, Any]:
        """
        Fallback intelligent analysis using pattern matching.
        
        Args:
            text: Natural language requirement description
            
        Returns:
            Dictionary with structured reasoning output
        """
        text_lower = text.lower()
        
        # Default analysis
        analysis = {
            "goal": "Unknown goal",
            "core_products": [],
            "required_components": [],
            "optional_components": [],
            "missing_info": [],
            "reasoning": "Basic analysis using pattern matching"
        }
        
        # Detect flood/water related requests
        if any(word in text_lower for word in ["flood", "water", "leak", "moisture", "humidity"]):
            analysis["goal"] = "detect water presence and receive alerts"
            analysis["core_products"] = ["water_sensor", "flood_detector"]
            analysis["required_components"] = ["gateway", "notification_system"]
            analysis["optional_components"] = ["siren", "multiple_sensors"]
            analysis["missing_info"] = ["indoor or outdoor?", "mobile alerts or local siren?", "area size?"]
            analysis["reasoning"] = "Water sensors need connectivity to send alerts and a notification system to inform users."
        
        # Detect security requests
        elif any(word in text_lower for word in ["security", "camera", "surveillance", "monitor"]):
            analysis["goal"] = "security monitoring and recording"
            analysis["core_products"] = ["camera", "recorder"]
            analysis["required_components"] = ["storage", "network"]
            analysis["optional_components"] = ["ai_analysis", "multiple_cameras"]
            analysis["missing_info"] = ["number of cameras?", "recording duration?", "indoor/outdoor?"]
            analysis["reasoning"] = "Cameras need storage for recording and network connectivity for remote access."
        
        # Detect smart home requests
        elif any(word in text_lower for word in ["smart home", "home automation", "light", "thermostat"]):
            analysis["goal"] = "home automation and control"
            analysis["core_products"] = ["controller", "sensors"]
            analysis["required_components"] = ["hub", "network"]
            analysis["optional_components"] = ["voice_control", "multiple_devices"]
            analysis["missing_info"] = ["number of rooms?", "specific devices?", "budget?"]
            analysis["reasoning"] = "Smart home systems need a central hub to coordinate devices and network connectivity for remote control."
        
        # Generic analysis for other requests
        else:
            analysis["goal"] = "implement requested system"
            analysis["core_products"] = ["main_device"]
            analysis["required_components"] = ["power", "connectivity"]
            analysis["missing_info"] = ["specific requirements?", "budget?", "environment?"]
            analysis["reasoning"] = "Most systems require power and some form of connectivity to function properly."
        
        return analysis


class ExtractionError(Exception):
    """Exception raised when requirement extraction fails."""
    pass