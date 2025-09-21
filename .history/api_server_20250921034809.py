#!/usr/bin/env python3
"""
Simple FastAPI server to provide HTTP API for Deep Researcher Agent.
This bridges the CLI interface with the React frontend.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import tempfile
import os
import json
from pathlib import Path

from deep_researcher.agent import ResearchAgent
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    # Startup
    try:
        get_agent()
        print("✅ Deep Researcher Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
    
    yield
    
    # Shutdown
    global agent
    if agent:
        try:
            agent.__exit__(None, None, None)
            print("✅ Agent cleaned up successfully")
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")

app = FastAPI(title="Deep Researcher API", version="1.0.0", lifespan=lifespan)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
agent = None

def get_agent():
    global agent
    if agent is None:
        agent = ResearchAgent()
        agent.__enter__()  # Initialize the agent
    return agent

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
    return {"message": "Deep Researcher API is running", "status": "healthy"}

@app.post("/research")
async def conduct_research(request: ResearchRequest):
    """Conduct research on a query."""
    try:
        research_agent = get_agent()
        
        result = research_agent.research(
            query=request.query,
            session_id=request.session_id,
            max_sources=request.max_sources
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=400, 
                detail=result.get('error', 'Research failed')
            )
        
        # Transform the result to match frontend expectations
        research_report = result['research_report']
        
        return {
            "success": True,
            "research_report": {
                "summary": research_report.summary,
                "key_findings": research_report.key_findings,
                "confidence_score": research_report.confidence_score,
                "sources": [
                    {
                        "title": source.title if hasattr(source, 'title') else f"Source {i+1}",
                        "content": source.content if hasattr(source, 'content') else str(source),
                        "relevance_score": getattr(source, 'relevance_score', 0.8)
                    }
                    for i, source in enumerate(research_report.sources)
                ]
            },
            "execution_time": result.get('execution_time', 0),
            "sources_found": result.get('sources_found', 0),
            "reasoning_steps": result.get('reasoning_steps', 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/suggest")
async def get_suggestions(request: SuggestionRequest):
    """Get query refinement suggestions."""
    try:
        research_agent = get_agent()
        
        suggestions = research_agent.get_query_suggestions(
            request.query, 
            request.session_id
        )
        
        return {
            "success": True,
            "suggestions": suggestions or []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
async def ingest_documents(files: List[UploadFile] = File(...)):
    """Ingest documents into the research system."""
    try:
        research_agent = get_agent()
        
        # Save uploaded files to temporary directory
        temp_files = []
        for file in files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
                content = await file.read()
                tmp.write(content)
                temp_files.append(tmp.name)
        
        try:
            # Ingest the files
            result = research_agent.ingest_documents(temp_files)
            
            return {
                "success": result['success'],
                "documents_processed": result.get('documents_processed', 0),
                "total_chunks": result.get('total_chunks', 0),
                "processing_time": result.get('processing_time', 0),
                "error": result.get('error')
            }
            
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
                    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_system_status():
    """Get system status and statistics."""
    try:
        research_agent = get_agent()
        status = research_agent.get_system_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def get_system_health():
    """Get system health diagnostics."""
    try:
        research_agent = get_agent()
        health = research_agent.get_system_health()
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)