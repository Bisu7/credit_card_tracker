#!/usr/bin/env python3
"""
Simple test backend for Deep Researcher
This bypasses the complex model initialization to test the API endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json

app = FastAPI(title="Deep Researcher Test API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    max_sources: Optional[int] = 10

class SuggestionRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Deep Researcher Test API is running", "status": "healthy"}

@app.post("/research")
async def conduct_research(request: ResearchRequest):
    """Conduct research on a query."""
    try:
        # Simulate research processing
        import time
        time.sleep(2)  # Simulate processing time
        
        # Mock research results
        research_report = {
            "summary": f"Based on your query '{request.query}', here's what I found:\n\nThis is a comprehensive analysis of your research question. The findings suggest several key insights that are relevant to your query. The research methodology involved analyzing multiple sources and synthesizing information to provide you with accurate and up-to-date information.\n\nKey findings include:\n- Important insight 1\n- Important insight 2\n- Important insight 3",
            "key_findings": [
                f"Finding 1 related to: {request.query}",
                f"Finding 2 related to: {request.query}",
                f"Finding 3 related to: {request.query}"
            ],
            "confidence_score": 0.85,
            "sources": [
                {
                    "title": f"Source 1: Research on {request.query}",
                    "content": f"This source provides detailed information about {request.query}. It contains relevant data and analysis that supports the research findings.",
                    "relevance_score": 0.9
                },
                {
                    "title": f"Source 2: Analysis of {request.query}",
                    "content": f"Another comprehensive source that offers insights into {request.query}. This source provides additional context and supporting evidence.",
                    "relevance_score": 0.8
                },
                {
                    "title": f"Source 3: Expert opinion on {request.query}",
                    "content": f"Expert analysis and commentary on {request.query}. This source offers professional insights and recommendations.",
                    "relevance_score": 0.75
                }
            ]
        }
        
        return {
            "success": True,
            "research_report": research_report,
            "execution_time": 2.1,
            "sources_found": 3,
            "reasoning_steps": 5
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/suggest")
async def get_suggestions(request: SuggestionRequest):
    """Get query refinement suggestions."""
    try:
        # Mock suggestions based on the query
        suggestions = [
            {
                "suggested_query": f"More specific: {request.query} in 2024",
                "refinement_type": "specificity",
                "rationale": "Adding a time frame makes the query more specific",
                "confidence": 0.8,
                "expected_improvement": 0.15
            },
            {
                "suggested_query": f"Broader scope: What are the main aspects of {request.query}?",
                "refinement_type": "scope",
                "rationale": "Broadening the scope might provide more comprehensive results",
                "confidence": 0.7,
                "expected_improvement": 0.1
            }
        ]
        
        return {
            "success": True,
            "suggestions": suggestions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
async def ingest_documents():
    """Mock document ingestion."""
    return {
        "success": True,
        "documents_processed": 0,
        "total_chunks": 0,
        "processing_time": 0.1,
        "message": "Document ingestion endpoint ready (mock mode)"
    }

@app.get("/status")
async def get_system_status():
    """Get system status and statistics."""
    return {
        "status": "healthy",
        "mode": "test",
        "message": "Test backend running successfully"
    }

@app.get("/health")
async def get_system_health():
    """Get system health diagnostics."""
    return {
        "overall_status": "healthy",
        "timestamp": "2025-09-21T03:00:00Z",
        "issues": [],
        "warnings": [],
        "mode": "test"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
