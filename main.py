from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# Create FastAPI app instance
app = FastAPI(title="TruthSignal API", version="1.0.0")

# Include CORS middleware to allow requests from browser extensions
# Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models matching the API specification
class AnalysisRequest(BaseModel):
    url: str
    html_content: Optional[str] = None
    user_credentials: Optional[dict] = None


class AnalysisResponse(BaseModel):
    trust_score: str  # "red", "yellow", "green"
    reasons: List[str]
    scan_id: str
    analysis_timestamp: str


@app.get("/")
async def root():
    """Root endpoint to verify API is running"""
    return {"status": "TruthSignal API is running"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_website(request: AnalysisRequest):
    """
    Analyze website content for trustworthiness

    This is a STUB implementation that returns hardcoded response data.
    In the real implementation, this will perform actual content analysis.
    """
    # Hardcoded stub response matching the API specification
    stub_response = AnalysisResponse(
        trust_score="yellow",
        reasons=["Initial stub response"],
        scan_id="test_123",
        analysis_timestamp="2024-01-01T00:00:00Z"
    )
    return stub_response

# To run the server locally:
# uvicorn main:app --reload --host 0.0.0.0 --port 8000
#
# The server will be available at:
# - Local: http://localhost:8000
# - Docs: http://localhost:8000/docs
#
# --reload enables auto-reload during development
# --host 0.0.0.0 makes it accessible on your network
# --port 8000 sets the port (default is 8000)