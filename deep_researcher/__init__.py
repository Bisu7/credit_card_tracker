"""
Deep Researcher Agent - A local AI-powered research system.

This package provides comprehensive research capabilities through local embedding
generation, multi-step reasoning, and efficient document retrieval without
external API dependencies.
"""

__version__ = "0.1.0"
__author__ = "Deep Researcher Team"

from .agent import ResearchAgent
from .models import Document, TextChunk, ProcessedQuery, ResearchReport

__all__ = [
    "ResearchAgent",
    "Document", 
    "TextChunk",
    "ProcessedQuery",
    "ResearchReport"
]