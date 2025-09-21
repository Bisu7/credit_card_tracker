"""Core data models for Deep Researcher Agent."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import numpy as np
import hashlib
import json


class QueryType(Enum):
    """Types of research queries."""
    SIMPLE = "simple"
    COMPLEX = "complex"
    MULTI_PART = "multi_part"
    COMPARATIVE = "comparative"
    ANALYTICAL = "analytical"


class DocumentFormat(Enum):
    """Supported document formats."""
    PDF = "pdf"
    TXT = "txt"
    DOCX = "docx"
    MD = "md"
    HTML = "html"


@dataclass
class TextChunk:
    """Represents a chunk of text from a document."""
    
    id: str
    content: str
    document_id: str
    chunk_index: int
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate chunk data after initialization."""
        if not self.content.strip():
            raise ValueError("Chunk content cannot be empty")
        if self.chunk_index < 0:
            raise ValueError("Chunk index must be non-negative")
        if len(self.content) > 10000:  # Reasonable limit
            raise ValueError("Chunk content too large (>10000 characters)")
    
    @property
    def content_hash(self) -> str:
        """Generate hash of chunk content for deduplication."""
        return hashlib.md5(self.content.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary for storage."""
        return {
            "id": self.id,
            "content": self.content,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "content_hash": self.content_hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextChunk":
        """Create chunk from dictionary."""
        return cls(
            id=data["id"],
            content=data["content"],
            document_id=data["document_id"],
            chunk_index=data["chunk_index"],
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"])
        )


@dataclass
class Document:
    """Represents a research document."""
    
    id: str
    title: str
    content: str
    source_path: str
    format_type: DocumentFormat
    chunks: List[TextChunk] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate document data after initialization."""
        if not self.title.strip():
            raise ValueError("Document title cannot be empty")
        if not self.content.strip():
            raise ValueError("Document content cannot be empty")
        if not self.source_path:
            raise ValueError("Document source path cannot be empty")
    
    @property
    def content_hash(self) -> str:
        """Generate hash of document content."""
        return hashlib.sha256(self.content.encode()).hexdigest()
    
    @property
    def word_count(self) -> int:
        """Count words in document content."""
        return len(self.content.split())
    
    @property
    def chunk_count(self) -> int:
        """Get number of chunks in document."""
        return len(self.chunks)
    
    def add_chunk(self, chunk: TextChunk) -> None:
        """Add a chunk to the document."""
        if chunk.document_id != self.id:
            raise ValueError("Chunk document_id must match document id")
        self.chunks.append(chunk)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary for storage."""
        return {
            "id": self.id,
            "title": self.title,
            "content_hash": self.content_hash,
            "source_path": self.source_path,
            "format_type": self.format_type.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "word_count": self.word_count,
            "chunk_count": self.chunk_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], content: str = "") -> "Document":
        """Create document from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            content=content,
            source_path=data["source_path"],
            format_type=DocumentFormat(data["format_type"]),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"])
        )


@dataclass
class ProcessedQuery:
    """Represents a processed research query."""
    
    original_query: str
    query_type: QueryType
    complexity_score: float
    sub_queries: List[str] = field(default_factory=list)
    expected_sources: int = 10
    keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate query data after initialization."""
        if not self.original_query.strip():
            raise ValueError("Query cannot be empty")
        if not 0 <= self.complexity_score <= 1:
            raise ValueError("Complexity score must be between 0 and 1")
        if self.expected_sources < 1:
            raise ValueError("Expected sources must be at least 1")
    
    @property
    def is_complex(self) -> bool:
        """Check if query is considered complex."""
        return self.complexity_score > 0.7 or len(self.sub_queries) > 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert query to dictionary."""
        return {
            "original_query": self.original_query,
            "query_type": self.query_type.value,
            "complexity_score": self.complexity_score,
            "sub_queries": self.sub_queries,
            "expected_sources": self.expected_sources,
            "keywords": self.keywords,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class ReasoningStep:
    """Represents a step in multi-step reasoning."""
    
    step_id: str
    description: str
    query: str
    dependencies: List[str] = field(default_factory=list)
    confidence: float = 1.0
    results: Dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate reasoning step data."""
        if not self.description.strip():
            raise ValueError("Step description cannot be empty")
        if not self.query.strip():
            raise ValueError("Step query cannot be empty")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
    
    @property
    def is_completed(self) -> bool:
        """Check if step has been executed."""
        return bool(self.results)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary."""
        return {
            "step_id": self.step_id,
            "description": self.description,
            "query": self.query,
            "dependencies": self.dependencies,
            "confidence": self.confidence,
            "results": self.results,
            "execution_time": self.execution_time,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class ResearchReport:
    """Represents a complete research report."""
    
    query: str
    summary: str
    key_findings: List[str]
    sources: List[Document]
    reasoning_steps: List[ReasoningStep] = field(default_factory=list)
    confidence_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate report data."""
        if not self.query.strip():
            raise ValueError("Report query cannot be empty")
        if not self.summary.strip():
            raise ValueError("Report summary cannot be empty")
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("Confidence score must be between 0 and 1")
    
    @property
    def source_count(self) -> int:
        """Get number of sources used."""
        return len(self.sources)
    
    @property
    def total_reasoning_steps(self) -> int:
        """Get total number of reasoning steps."""
        return len(self.reasoning_steps)
    
    @property
    def average_step_confidence(self) -> float:
        """Calculate average confidence across reasoning steps."""
        if not self.reasoning_steps:
            return 1.0
        return sum(step.confidence for step in self.reasoning_steps) / len(self.reasoning_steps)
    
    def add_source(self, document: Document) -> None:
        """Add a source document to the report."""
        if document not in self.sources:
            self.sources.append(document)
    
    def add_reasoning_step(self, step: ReasoningStep) -> None:
        """Add a reasoning step to the report."""
        self.reasoning_steps.append(step)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "query": self.query,
            "summary": self.summary,
            "key_findings": self.key_findings,
            "source_count": self.source_count,
            "confidence_score": self.confidence_score,
            "metadata": self.metadata,
            "generated_at": self.generated_at.isoformat(),
            "reasoning_steps": [step.to_dict() for step in self.reasoning_steps]
        }


@dataclass
class SearchResult:
    """Represents a search result from vector similarity search."""
    
    document_id: str
    chunk_id: str
    similarity_score: float
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate search result data."""
        if not 0 <= self.similarity_score <= 1:
            raise ValueError("Similarity score must be between 0 and 1")
        if not self.content.strip():
            raise ValueError("Search result content cannot be empty")
    
    @property
    def is_relevant(self) -> bool:
        """Check if result meets relevance threshold."""
        return self.similarity_score >= 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert search result to dictionary."""
        return {
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "similarity_score": self.similarity_score,
            "content": self.content,
            "metadata": self.metadata
        }