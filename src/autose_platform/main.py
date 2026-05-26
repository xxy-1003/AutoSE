"""AutoSE Platform - Main FastAPI Application"""
import sys
from pathlib import Path

# Add parent directory to path for absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

from autose_platform.config import settings
from autose_platform.requirement_analyzer import RequirementAnalyzer
from autose_platform.product_retriever import ProductRetriever
from autose_platform.validation_layer import ValidationLayer
from autose_platform.proposal_generator import ProposalGenerator

# Create FastAPI app
app = FastAPI(
    title="AutoSE Platform",
    description="Autonomous Enterprise Solution Intelligence Platform",
    version="1.0.0"
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


class RequirementRequest(BaseModel):
    text: str


class HealthResponse(BaseModel):
    status: str
    api_url: str
    using_chutes: bool


@app.get("/", response_model=Dict[str, str])
async def root():
    return {"message": "AutoSE Platform API", "version": "1.0.0"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        api_url=settings.CHUTES_API_URL,
        using_chutes=settings.USING_CHUTES
    )


@app.post("/api/analyze")
async def analyze_requirement(request: RequirementRequest) -> Dict[str, Any]:
    """Process client requirement through the AutoSE pipeline"""
    try:
        # Step 1: Extract requirements
        requirements = await requirement_analyzer.extract(request.text)

        # Step 2: Match products
        products = await product_retriever.match(requirements)

        # Step 3: Validate compatibility
        validation = await validator.validate(products, requirements)

        # Step 4: Generate proposal
        proposal = await proposal_generator.generate(
            requirements=requirements,
            products=products,
            validation=validation
        )

        return {
            "success": True,
            "requirements": requirements,
            "products": products,
            "validation": validation,
            "proposal": proposal
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)