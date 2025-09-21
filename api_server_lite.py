#!/usr/bin/env python3
"""
Lightweight FastAPI server for Deep Researcher - optimized for deployment
This version uses mock responses to avoid memory issues with ML models
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import tempfile
import os
import json
import time
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager

# Lightweight imports only
import uvicorn

# Pydantic models
class ResearchRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    max_sources: Optional[int] = 10

class SuggestionRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class ResearchReport(BaseModel):
    summary: str
    key_findings: List[str]
    confidence_score: float
    sources: List[Dict[str, Any]]

class ResearchResponse(BaseModel):
    success: bool
    research_report: ResearchReport
    execution_time: float
    sources_found: int
    reasoning_steps: int
    mode: str = "lite"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    # Startup
    print("🚀 Starting Deep Researcher Lite API Server...")
    print("📡 Running in lightweight mode (no ML models)")
    
    yield
    
    # Shutdown
    print("✅ Deep Researcher Lite API Server stopped")

app = FastAPI(
    title="Deep Researcher Lite API", 
    version="1.0.0", 
    description="Lightweight AI research assistant",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_mock_research_response(query: str) -> Dict[str, Any]:
    """Generate comprehensive mock research response"""
    return {
        "summary": f"""# Research Analysis: {query}

Based on comprehensive analysis of available sources, here are the key findings regarding "{query}":

## Executive Summary
This research provides a detailed examination of the topic, synthesizing information from multiple authoritative sources to deliver actionable insights.

## Key Insights
- **Primary Finding**: The research reveals significant developments and trends in this area
- **Secondary Finding**: Multiple perspectives and approaches have been identified
- **Tertiary Finding**: Future implications and recommendations are outlined

## Detailed Analysis
The research methodology involved systematic analysis of relevant sources, cross-referencing information, and synthesizing findings into coherent insights. The analysis reveals several important patterns and trends that are relevant to understanding this topic.

## Recommendations
Based on the research findings, several recommendations emerge:
1. Consider the primary trends identified
2. Evaluate the implications for your specific context
3. Monitor ongoing developments in this area

## Conclusion
This research provides a solid foundation for understanding the topic and making informed decisions.""",
        
        "key_findings": [
            f"Significant developments identified in {query}",
            f"Multiple approaches and perspectives available for {query}",
            f"Future implications and trends in {query}",
            f"Best practices and recommendations for {query}",
            f"Industry insights and expert opinions on {query}"
        ],
        
        "confidence_score": 0.85,
        
        "sources": [
            {
                "title": f"Comprehensive Analysis: {query}",
                "content": f"This source provides detailed information about {query}, including key concepts, methodologies, and practical applications. The content covers both theoretical foundations and real-world implementations.",
                "relevance_score": 0.92,
                "url": "https://example.com/source1",
                "type": "research_paper"
            },
            {
                "title": f"Industry Report: {query} Trends",
                "content": f"An industry-focused analysis of {query} that examines current trends, market dynamics, and future projections. This source offers valuable insights for practitioners and decision-makers.",
                "relevance_score": 0.88,
                "url": "https://example.com/source2", 
                "type": "industry_report"
            },
            {
                "title": f"Expert Insights: {query} Best Practices",
                "content": f"Expert commentary and best practices related to {query}. This source provides practical guidance and recommendations based on professional experience and case studies.",
                "relevance_score": 0.85,
                "url": "https://example.com/source3",
                "type": "expert_opinion"
            },
            {
                "title": f"Technical Deep Dive: {query}",
                "content": f"A technical examination of {query} that covers implementation details, technical considerations, and advanced concepts. Suitable for technical audiences seeking in-depth understanding.",
                "relevance_score": 0.82,
                "url": "https://example.com/source4",
                "type": "technical_documentation"
            },
            {
                "title": f"Case Studies: {query} Applications",
                "content": f"Real-world case studies and applications of {query}. This source demonstrates practical implementations and lessons learned from various projects and initiatives.",
                "relevance_score": 0.80,
                "url": "https://example.com/source5",
                "type": "case_study"
            }
        ]
    }

def get_mock_suggestions(query: str) -> List[Dict[str, Any]]:
    """Generate mock query suggestions"""
    return [
        {
            "suggested_query": f"More specific: {query} in 2024",
            "refinement_type": "specificity",
            "rationale": "Adding a time frame makes the query more specific and current",
            "confidence": 0.9,
            "expected_improvement": "high"
        },
        {
            "suggested_query": f"Broader scope: impact of {query}",
            "refinement_type": "breadth", 
            "rationale": "Broadening the scope to examine broader impacts and implications",
            "confidence": 0.8,
            "expected_improvement": "medium"
        },
        {
            "suggested_query": f"Comparative: {query} vs alternatives",
            "refinement_type": "comparison",
            "rationale": "Adding comparison elements provides more comprehensive analysis",
            "confidence": 0.75,
            "expected_improvement": "medium"
        }
    ]

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Deep Researcher Lite API is running",
        "status": "healthy",
        "mode": "lite",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mode": "lite",
        "timestamp": time.time(),
        "uptime": "active"
    }

@app.get("/status")
async def get_system_status():
    """Get detailed system status"""
    return {
        "status": "healthy",
        "mode": "lite",
        "message": "Lightweight mode - no ML models loaded",
        "features": {
            "research": True,
            "suggestions": True,
            "document_upload": False,  # Disabled in lite mode
            "ml_models": False
        },
        "performance": {
            "response_time": "< 1s",
            "memory_usage": "low",
            "cpu_usage": "low"
        }
    }

@app.post("/research", response_model=ResearchResponse)
async def conduct_research(request: ResearchRequest):
    """Conduct research using lightweight mock responses"""
    start_time = time.time()
    
    try:
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Generate mock research response
        research_data = get_mock_research_response(request.query)
        execution_time = time.time() - start_time
        
        return ResearchResponse(
            success=True,
            research_report=ResearchReport(**research_data),
            execution_time=execution_time,
            sources_found=len(research_data["sources"]),
            reasoning_steps=3,
            mode="lite"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/suggest")
async def get_suggestions(request: SuggestionRequest):
    """Get query suggestions"""
    try:
        # Simulate processing time
        await asyncio.sleep(0.2)
        
        suggestions = get_mock_suggestions(request.query)
        
        return {
            "success": True,
            "suggestions": suggestions,
            "mode": "lite"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
async def ingest_documents(files: List[UploadFile] = File(...)):
    """Document ingestion endpoint (disabled in lite mode)"""
    return {
        "success": False,
        "message": "Document ingestion is disabled in lite mode",
        "mode": "lite"
    }

if __name__ == "__main__":
    import os
    
    # Get port from environment variable (Render sets this)
    port = int(os.environ.get("PORT", 8001))
    
    print("🚀 Starting Deep Researcher Lite API Server...")
    print(f"📡 Backend will be available at: http://0.0.0.0:{port}")
    print("🎨 Frontend should connect to this URL")
    print("💡 Running in lightweight mode (no ML models)")
    
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
