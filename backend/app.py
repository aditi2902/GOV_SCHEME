"""
FastAPI Application — Government Scheme Eligibility Platform

REST API that exposes the multi-agent system via HTTP endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import HOST, PORT, CORS_ORIGINS
from models import (
    AnalyzeRequest,
    CompareRequest,
    ChatRequest,
    AnalysisResponse,
    SchemeDetail,
    StatsResponse,
)
from orchestrator import run_analysis, get_scheme_detail, get_stats
from rag_agent import chat_answer, search_schemes
from guidance_agent import generate_comparison
from profile_agent import extract_profile


# ── App Setup ──────────────────────────────────────────

app = FastAPI(
    title="SarkariSahay API",
    description=(
        "AI-powered Government Scheme Eligibility Platform. "
        "Find schemes you qualify for, get personalized guidance, "
        "and never miss a benefit."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health Check ───────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "SarkariSahay API"}


# ── Main Analysis Endpoint ─────────────────────────────

@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    """
    Full analysis pipeline:
    User text → Profile → Eligibility → Ranking → Documents → Guidance
    """
    try:
        result = run_analysis(req.text, include_guidance=True)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/quick")
async def analyze_quick(req: AnalyzeRequest):
    """
    Quick analysis without LLM guidance (faster).
    """
    try:
        result = run_analysis(req.text, include_guidance=False)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Profile Extraction ─────────────────────────────────

@app.post("/api/profile")
async def profile(req: AnalyzeRequest):
    """Extract structured profile from text."""
    try:
        return extract_profile(req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Scheme Endpoints ───────────────────────────────────

@app.get("/api/schemes/{slug}")
async def scheme_detail(slug: str):
    """Get full details for a scheme by slug."""
    detail = get_scheme_detail(slug)
    if not detail:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return detail


# ── Chat / RAG ─────────────────────────────────────────

@app.post("/api/chat")
async def chat(req: ChatRequest):
    """RAG-powered Q&A about government schemes."""
    try:
        answer = chat_answer(req.question, req.user_text)
        return {"question": req.question, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Scheme Comparison ──────────────────────────────────

@app.post("/api/compare")
async def compare(req: CompareRequest):
    """Compare multiple schemes side by side."""
    try:
        schemes = []
        for slug in req.slugs:
            detail = get_scheme_detail(slug)
            if detail:
                schemes.append(detail)

        if len(schemes) < 2:
            raise HTTPException(
                status_code=400,
                detail="Need at least 2 valid schemes to compare"
            )

        profile = None
        if req.user_text:
            profile = extract_profile(req.user_text)

        comparison = generate_comparison(
            profile or {},
            schemes,
        )

        return {
            "schemes": schemes,
            "comparison": comparison,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Statistics ─────────────────────────────────────────

@app.get("/api/stats")
async def stats():
    """Dashboard statistics."""
    try:
        return get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Run Server ─────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=True,
    )