"""AutoSE Platform - Main FastAPI Application with Conversation Memory"""
import sys
from pathlib import Path
import uuid
from datetime import datetime
from typing import List, Optional

# Add parent directory to path for absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any

from autose_platform.config import settings
from autose_platform.requirement_analyzer import RequirementAnalyzer
from autose_platform.product_retriever import ProductRetriever
from autose_platform.validation_layer import ValidationLayer
from autose_platform.proposal_generator import ProposalGenerator

# Create FastAPI app
app = FastAPI(
    title="AutoSE Platform",
    description="Autonomous Enterprise Solution Intelligence Platform with Conversation Memory",
    version="3.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
requirement_analyzer = RequirementAnalyzer()
product_retriever = ProductRetriever()
validator = ValidationLayer()
proposal_generator = ProposalGenerator()

# In-memory conversation store
conversation_store = {}

class ConversationMemory(BaseModel):
    """Stores conversation history for a session"""
    session_id: str
    created_at: datetime
    updated_at: datetime
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    original_requirement: Optional[Dict[str, Any]] = None
    current_solution: Optional[Dict[str, Any]] = None
    budget_constraints: Optional[Dict[str, Any]] = None
    modifications: List[Dict[str, Any]] = Field(default_factory=list)

class RequirementRequest(BaseModel):
    text: str
    session_id: Optional[str] = None  # Optional: if provided, continues existing conversation


class HealthResponse(BaseModel):
    status: str
    api_url: str
    using_chutes: bool


class SessionResponse(BaseModel):
    session_id: str
    created_at: datetime
    message_count: int


def get_or_create_session(session_id: Optional[str] = None) -> ConversationMemory:
    """Get existing session or create a new one"""
    if session_id and session_id in conversation_store:
        # Update timestamp for existing session
        conversation_store[session_id].updated_at = datetime.now()
        return conversation_store[session_id]
    else:
        # Create new session
        new_session_id = str(uuid.uuid4())
        now = datetime.now()
        new_session = ConversationMemory(
            session_id=new_session_id,
            created_at=now,
            updated_at=now,
            messages=[]
        )
        conversation_store[new_session_id] = new_session
        return new_session


def is_follow_up_question(text: str) -> bool:
    """Detect if the user is asking a follow-up question"""
    follow_up_keywords = [
        "budget", "price", "cost", "cheaper", "expensive", "minimum", "maximum",
        "reduce", "increase", "add", "remove", "what if", "how much", "can i",
        "alternative", "option", "different", "modify", "change", "adjust"
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in follow_up_keywords)

def is_negotiation(text: str, requirement_analyzer: RequirementAnalyzer) -> Dict[str, Any]:
    """
    Detect if the user is negotiating and extract intent/constraints.
    
    Args:
        text: User input text
        requirement_analyzer: RequirementAnalyzer instance
        
    Returns:
        Dictionary with negotiation detection results
    """
    intent = requirement_analyzer.detect_negotiation_intent(text)
    constraints = requirement_analyzer.extract_constraints_from_negotiation(text)
    
    return {
        "is_negotiating": intent.get("is_negotiating", False),
        "intent": intent,
        "constraints": constraints
    }


def handle_follow_up_question(session: ConversationMemory, text: str, current_result: Dict[str, Any]) -> Dict[str, Any]:
    """Process follow-up questions based on conversation history"""
    text_lower = text.lower()
    
    # Initialize modified result
    modified_result = current_result.copy()
    modified_result["is_follow_up"] = True
    modified_result["original_session_id"] = session.session_id
    
    # Check for budget/price questions
    if any(word in text_lower for word in ["budget", "price", "cost", "cheaper", "expensive", "minimum", "maximum"]):
        if session.current_solution:
            # All products are now dictionaries
            products = session.current_solution.get("products", [])
            total_cost = sum(product.get("price", 0) for product in products)
            
            modified_result["follow_up_response"] = {
                "type": "budget_info",
                "total_cost": total_cost,
                "currency": "USD",
                "message": f"The current solution costs ${total_cost:,}. You can reduce costs by removing optional features or selecting lower-tier products."
            }
    
    # Check for modification requests
    elif any(word in text_lower for word in ["reduce", "remove", "add", "modify", "change", "adjust"]):
        if session.current_solution:
            modified_result["follow_up_response"] = {
                "type": "modification_request",
                "message": "I can help you modify the solution. Please specify what you'd like to change (e.g., 'remove GPU acceleration', 'add redundant power', 'reduce camera count')."
            }
    
    # Check for alternative options
    elif any(word in text_lower for word in ["alternative", "option", "different"]):
        if session.current_solution:
            modified_result["follow_up_response"] = {
                "type": "alternative_request",
                "message": "I can suggest alternative configurations. Would you like me to show cheaper options, more powerful options, or different product combinations?"
            }
    
    # Generic follow-up response
    else:
        modified_result["follow_up_response"] = {
            "type": "general_follow_up",
            "message": "I understand this is a follow-up question. Based on our conversation, I can help you refine the solution further."
        }
    
    # Store modification in session history
    session.modifications.append({
        "timestamp": datetime.now(),
        "question": text,
        "response": modified_result.get("follow_up_response", {}),
        "original_solution": session.current_solution
    })
    
    return modified_result

def handle_negotiation(session: ConversationMemory, text: str, 
                      requirement_analyzer: RequirementAnalyzer,
                      product_retriever: ProductRetriever,
                      proposal_generator: ProposalGenerator) -> Dict[str, Any]:
    """
    Handle negotiation with the user.
    
    Args:
        session: Current conversation session
        text: User negotiation text
        requirement_analyzer: RequirementAnalyzer instance
        product_retriever: ProductRetriever instance
        proposal_generator: ProposalGenerator instance
        
    Returns:
        Dictionary with negotiation response
    """
    # Detect negotiation intent and constraints
    negotiation_result = is_negotiation(text, requirement_analyzer)
    
    if not negotiation_result["is_negotiating"]:
        # Fall back to regular follow-up handling
        return handle_follow_up_question(session, text, session.current_solution)
    
    # Get current solution
    current_solution = session.current_solution
    if not current_solution:
        return {
            "success": False,
            "error": "No current solution to negotiate about. Please provide a requirement first.",
            "is_negotiation": True
        }
    
    # Get current products
    current_products = current_solution.get("products", [])
    
    # Generate alternative solutions based on constraints
    alternative_solutions = product_retriever.generate_alternative_solutions(
        current_products,
        negotiation_result["constraints"]
    )
    
    # Generate negotiation response
    negotiation_response = proposal_generator.generate_negotiation_response(
        current_solution,
        negotiation_result["intent"],
        negotiation_result["constraints"],
        alternative_solutions
    )
    
    # Build response
    response = {
        "success": True,
        "session_id": session.session_id,
        "is_negotiation": True,
        "negotiation_intent": negotiation_result["intent"],
        "constraints": negotiation_result["constraints"],
        "current_solution_summary": negotiation_response["current_solution_summary"],
        "clarifying_questions": negotiation_response["clarifying_questions"],
        "alternative_options": negotiation_response.get("alternative_options", {}),
        "alternative_comparison": negotiation_response.get("alternative_comparison", {}),
        "recommended_action": negotiation_response["recommended_action"],
        "message": self._format_negotiation_message(negotiation_response)
    }
    
    # Store negotiation in session history
    session.modifications.append({
        "timestamp": datetime.now(),
        "question": text,
        "response": response,
        "negotiation_intent": negotiation_result["intent"],
        "constraints": negotiation_result["constraints"],
        "original_solution": current_solution
    })
    
    return response

def _format_negotiation_message(negotiation_response: Dict[str, Any]) -> str:
    """Format negotiation response into a readable message."""
    message_parts = []
    
    # Add acknowledgment
    message_parts.append("I understand you'd like to discuss the solution. Let me help you with that.")
    
    # Add clarifying questions if any
    clarifying_questions = negotiation_response.get("clarifying_questions", [])
    if clarifying_questions:
        message_parts.append("\n**To better understand your needs, could you clarify:**")
        for i, question in enumerate(clarifying_questions[:3]):  # Limit to 3 questions
            message_parts.append(f"{i+1}. {question}")
    
    # Add current solution summary
    current_summary = negotiation_response.get("current_solution_summary", {})
    if current_summary:
        message_parts.append(f"\n**Current solution:** ${current_summary.get('total_cost', 0):,} for {current_summary.get('device_count', 0)} devices")
        
        # Show most expensive items
        expensive_items = current_summary.get("most_expensive_items", [])
        if expensive_items:
            message_parts.append("**Most expensive items:**")
            for item in expensive_items[:3]:
                message_parts.append(f"- {item.get('name')}: ${item.get('price', 0):,}")
    
    # Add alternative options if available
    alternative_options = negotiation_response.get("alternative_options", {})
    if alternative_options:
        message_parts.append("\n**I can provide these alternative options:**")
        
        for alt_type, summary in alternative_options.items():
            if summary.get("total_cost", 0) > 0:
                alt_type_display = alt_type.capitalize()
                message_parts.append(f"- **{alt_type_display}**: ${summary.get('total_cost', 0):,} ({summary.get('product_count', 0)} products)")
    
    # Add recommended action
    recommended_action = negotiation_response.get("recommended_action", "")
    if recommended_action:
        message_parts.append(f"\n**Recommended next step:** {recommended_action}")
    
    return "\n".join(message_parts)


@app.get("/", response_model=Dict[str, str])
async def root():
    return {"message": "AutoSE Platform API with Conversation Memory", "version": "3.0.0"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        api_url=settings.CHUTES_API_URL,
        using_chutes=settings.USING_CHUTES
    )


@app.get("/api/sessions")
async def list_sessions() -> Dict[str, Any]:
    """List all active sessions"""
    return {
        "total_sessions": len(conversation_store),
        "sessions": [
            {
                "session_id": session.session_id,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "message_count": len(session.messages)
            }
            for session in conversation_store.values()
        ]
    }


@app.get("/api/session/{session_id}")
async def get_session(session_id: str) -> Dict[str, Any]:
    """Get details of a specific session"""
    if session_id not in conversation_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = conversation_store[session_id]
    return {
        "session_id": session.session_id,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "message_count": len(session.messages),
        "original_requirement": session.original_requirement,
        "current_solution": session.current_solution,
        "modification_count": len(session.modifications)
    }


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str) -> Dict[str, str]:
    """Delete a session"""
    if session_id in conversation_store:
        del conversation_store[session_id]
        return {"message": f"Session {session_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.post("/api/analyze")
async def analyze_requirement(request: RequirementRequest) -> Dict[str, Any]:
    """Process client requirement through the AutoSE pipeline with conversation memory"""
    try:
        # Get or create session
        session = get_or_create_session(request.session_id)
        
        # Add user message to session history
        user_message = {
            "role": "user",
            "text": request.text,
            "timestamp": datetime.now()
        }
        session.messages.append(user_message)
        
        # Check if this is a negotiation
        negotiation_result = is_negotiation(request.text, requirement_analyzer)
        
        if negotiation_result["is_negotiating"] and session.current_solution is not None:
            # Handle negotiation
            result = handle_negotiation(
                session, 
                request.text, 
                requirement_analyzer,
                product_retriever,
                proposal_generator
            )
            
            # Add assistant response to session history
            assistant_message = {
                "role": "assistant",
                "text": result.get("message", "Negotiation response"),
                "timestamp": datetime.now(),
                "is_negotiation": True
            }
            session.messages.append(assistant_message)
            
        # Check if this is a follow-up question
        elif is_follow_up_question(request.text) and session.current_solution is not None:
            # Handle follow-up question using existing solution
            result = handle_follow_up_question(session, request.text, session.current_solution)
            
            # Add assistant response to session history
            assistant_message = {
                "role": "assistant",
                "text": f"Follow-up response: {result.get('follow_up_response', {}).get('message', '')}",
                "timestamp": datetime.now(),
                "is_follow_up": True
            }
            session.messages.append(assistant_message)
            
        else:
            # Process as new requirement
            # Step 1: Extract requirements with additional info
            requirements, additional_info = await requirement_analyzer.extract(request.text)
            
            # Step 2: Match products with project type and budget
            project_type = additional_info.get("project_type", "unknown")
            budget_limit = additional_info.get("budget_limit", 0)
            
            products = await product_retriever.match(
                requirements, 
                project_type=project_type if project_type != "unknown" else None,
                budget_limit=budget_limit if budget_limit > 0 else None
            )
            
            # Step 3: Validate compatibility
            validation = await validator.validate(products, requirements)
            
            # Step 4: Generate proposal with additional info
            proposal = await proposal_generator.generate(
                requirements=requirements,
                products=products,
                validation=validation,
                additional_info=additional_info
            )
            
            # Store as current solution
            session.original_requirement = requirements
            session.current_solution = {
                "requirements": requirements,
                "products": products,
                "validation": validation,
                "proposal": proposal,
                "additional_info": additional_info
            }
            
            result = {
                "success": True,
                "session_id": session.session_id,
                "is_follow_up": False,
                "is_negotiation": False,
                "requirements": requirements,
                "products": products,
                "validation": validation,
                "proposal": proposal,
                "additional_info": additional_info
            }
            
            # Add assistant response to session history
            assistant_message = {
                "role": "assistant",
                "text": f"Generated solution for: {request.text}",
                "timestamp": datetime.now(),
                "is_follow_up": False
            }
            session.messages.append(assistant_message)
        
        # Update session timestamp
        session.updated_at = datetime.now()
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze_intelligently")
async def analyze_intelligently(request: RequirementRequest) -> Dict[str, Any]:
    """Process client requirement through intelligent AutoSE pipeline"""
    try:
        # Get or create session
        session = get_or_create_session(request.session_id)
        
        # Add user message to session history
        user_message = {
            "role": "user",
            "text": request.text,
            "timestamp": datetime.now()
        }
        session.messages.append(user_message)
        
        # Initialize backend orchestrator
        from autose_platform.backend import FastAPIBackend
        backend = FastAPIBackend()
        
        # Perform intelligent analysis
        result = await backend.analyze_intelligently(request.text)
        
        # Store as current solution if successful
        if result.get("success", False) and not result.get("no_exact_match", False):
            session.current_solution = result
        
        # Add assistant response to session history
        assistant_message = {
            "role": "assistant",
            "text": result.get("message", "Intelligent analysis completed"),
            "timestamp": datetime.now(),
            "is_intelligent_analysis": True
        }
        session.messages.append(assistant_message)
        
        # Update session timestamp
        session.updated_at = datetime.now()
        
        # Add session ID to result
        result["session_id"] = session.session_id
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# New endpoints for product catalog
@app.get("/api/products")
async def get_products(category: Optional[str] = None) -> Dict[str, Any]:
    """Get product catalog, optionally filtered by category"""
    try:
        if category:
            products = product_retriever.get_products_by_category(category)
        else:
            products = product_retriever.get_catalog()
        
        categories = product_retriever.get_categories()
        
        return {
            "success": True,
            "total_products": len(products),
            "categories": categories,
            "products": products
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/{product_id}")
async def get_product(product_id: str) -> Dict[str, Any]:
    """Get a specific product by ID"""
    try:
        product = product_retriever.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ID '{product_id}' not found")
        
        return {
            "success": True,
            "product": product
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/categories")
async def get_categories() -> Dict[str, Any]:
    """Get all available product categories"""
    try:
        categories = product_retriever.get_categories()
        
        # Get count of products per category
        category_counts = {}
        for category in categories:
            products = product_retriever.get_products_by_category(category)
            category_counts[category] = len(products)
        
        return {
            "success": True,
            "total_categories": len(categories),
            "categories": categories,
            "category_counts": category_counts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)