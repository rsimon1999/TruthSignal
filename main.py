from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import re
import uuid

# Import analysis modules
try:
    from affiliate_scanner import find_affiliate_links
    from llm_analysis import analyze_with_llm
    from score_aggregator import calculate_trust_score
except ImportError:
    # Fallback for development if modules aren't available yet
    def find_affiliate_links(html_content):
        return {"affiliate_links": [], "count": 0}


    def analyze_with_llm(text):
        return {"sentiment": "neutral", "key_issues": []}


    def calculate_trust_score(affiliate_data, llm_data):
        return {"trust_score": "yellow", "reasons": ["Development mode"]}

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


def extract_clean_text(html_content: str) -> str:
    """
    Extract clean text from HTML content by removing tags and basic cleaning
    """
    if not html_content:
        return ""

    # Remove HTML tags
    clean_text = re.sub('<[^<]+?>', ' ', html_content)

    # Remove extra whitespace and newlines - use raw string for regex
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    # Remove common script and style content that might slip through
    clean_text = re.sub(r'{(.*?)}', '', clean_text)
    clean_text = re.sub(r'//<!\[CDATA\[(.*?)//\]\]>', '', clean_text)

    return clean_text


@app.get("/")
async def root():
    """Root endpoint to verify API is running"""
    return {"status": "TruthSignal API is running"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_website(request: AnalysisRequest):
    """
    Analyze website content for trustworthiness

    Integrates three analysis modules:
    1. Affiliate link scanner
    2. LLM content analysis
    3. Trust score aggregator
    """
    try:
        # Generate unique scan ID and timestamp
        scan_id = f"scan_{uuid.uuid4().hex[:12]}"
        analysis_timestamp = datetime.utcnow().isoformat() + "Z"

        # If no HTML content provided, return default response
        if not request.html_content:
            return AnalysisResponse(
                trust_score="yellow",
                reasons=["No HTML content provided for analysis"],
                scan_id=scan_id,
                analysis_timestamp=analysis_timestamp
            )

        # Step 1: Extract clean text from HTML
        cleaned_text = extract_clean_text(request.html_content)

        # Step 2: Analyze affiliate links
        try:
            affiliate_data = find_affiliate_links(request.html_content)
        except Exception as e:
            affiliate_data = {"error": f"Affiliate analysis failed: {str(e)}"}

        # Step 3: Analyze content with LLM
        try:
            llm_data = analyze_with_llm(cleaned_text)
        except Exception as e:
            llm_data = {"error": f"LLM analysis failed: {str(e)}"}

        # Step 4: Calculate final trust score
        try:
            trust_result = calculate_trust_score(affiliate_data, llm_data)

            # Ensure we have the expected structure
            if isinstance(trust_result, dict) and "trust_score" in trust_result:
                trust_score = trust_result["trust_score"]
                reasons = trust_result.get("reasons", ["Analysis completed"])
            else:
                trust_score = "yellow"
                reasons = ["Score calculation returned unexpected format"]

        except Exception as e:
            trust_score = "yellow"
            reasons = [f"Score aggregation failed: {str(e)}"]

        # If any critical module failed, default to yellow with error info
        if ("error" in str(affiliate_data) or "error" in str(llm_data)) and trust_score != "red":
            trust_score = "yellow"
            if "error" in str(affiliate_data):
                reasons.append("Partial analysis: Affiliate scanning issues")
            if "error" in str(llm_data):
                reasons.append("Partial analysis: LLM analysis issues")

        return AnalysisResponse(
            trust_score=trust_score,
            reasons=reasons,
            scan_id=scan_id,
            analysis_timestamp=analysis_timestamp
        )

    except Exception as e:
        # Global error handling - return yellow score for any unexpected failures
        scan_id = f"error_{uuid.uuid4().hex[:8]}"
        return AnalysisResponse(
            trust_score="yellow",
            reasons=[f"Analysis incomplete: {str(e)}"],
            scan_id=scan_id,
            analysis_timestamp=datetime.utcnow().isoformat() + "Z"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

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