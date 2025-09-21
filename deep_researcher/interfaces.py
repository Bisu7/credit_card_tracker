"""Abstract interfaces for Deep Researcher Agent components."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np

from .models import Document, TextChunk, ProcessedQuery, ReasoningStep, ResearchReport


class DocumentIngesterInterface(ABC):
    """Interface for document ingestion components."""
    
    @abstractmethod
    def ingest_document(self, file_path: str) -> List[TextChunk]:
        """Ingest a document and return text chunks."""
        pass
    
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """Return list of supported file formats."""
        pass


class TextProcessorInterface(ABC):
    """Interface for text processing components."""
    
    @abstractmethod
    def process_text(self, raw_text: str, metadata: Dict[str, Any] = None) -> List[TextChunk]:
        """Process raw text into chunks."""
        pass
    
    @abstractmethod
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        pass


class EmbeddingGeneratorInterface(ABC):
    """Interface for embedding generation components."""
    
    @abstractmethod
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        pass
    
    @abstractmethod
    def generate_single_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        pass


class VectorStoreInterface(ABC):
    """Interface for vector storage and retrieval."""
    
    @abstractmethod
    def add_vectors(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> List[str]:
        """Add vectors to the store and return their IDs."""
        pass
    
    @abstractmethod
    def search(self, query_vector: np.ndarray, k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        pass
    
    @abstractmethod
    def delete_vectors(self, vector_ids: List[str]) -> None:
        """Delete vectors by their IDs."""
        pass


class DocumentStoreInterface(ABC):
    """Interface for document storage and retrieval."""
    
    @abstractmethod
    def store_document(self, document: Document) -> str:
        """Store a document and return its ID."""
        pass
    
    @abstractmethod
    def get_document(self, document_id: str) -> Optional[Document]:
        """Retrieve a document by ID."""
        pass
    
    @abstractmethod
    def search_documents(self, query: str, filters: Dict[str, Any] = None) -> List[Document]:
        """Search documents by metadata or content."""
        pass
    
    @abstractmethod
    def delete_document(self, document_id: str) -> None:
        """Delete a document by ID."""
        pass


class QueryProcessorInterface(ABC):
    """Interface for query processing components."""
    
    @abstractmethod
    def process_query(self, query: str) -> ProcessedQuery:
        """Process and analyze a query."""
        pass
    
    @abstractmethod
    def classify_query_type(self, query: str) -> str:
        """Classify the type of query."""
        pass


class MultiStepReasonerInterface(ABC):
    """Interface for multi-step reasoning components."""
    
    @abstractmethod
    def create_reasoning_plan(self, query: ProcessedQuery) -> List[ReasoningStep]:
        """Create a plan for multi-step reasoning."""
        pass
    
    @abstractmethod
    def execute_reasoning_step(self, step: ReasoningStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single reasoning step."""
        pass


class DocumentRetrieverInterface(ABC):
    """Interface for document retrieval components."""
    
    @abstractmethod
    def retrieve_documents(self, query_embedding: np.ndarray, k: int = 10, 
                          filters: Dict[str, Any] = None) -> List[Document]:
        """Retrieve relevant documents for a query."""
        pass
    
    @abstractmethod
    def rank_documents(self, documents: List[Document], query: str) -> List[Document]:
        """Rank documents by relevance to query."""
        pass


class ResultSynthesizerInterface(ABC):
    """Interface for result synthesis components."""
    
    @abstractmethod
    def synthesize_results(self, documents: List[Document], query: str, 
                          reasoning_steps: List[ReasoningStep]) -> ResearchReport:
        """Synthesize research results from multiple sources."""
        pass
    
    @abstractmethod
    def resolve_conflicts(self, documents: List[Document]) -> Dict[str, Any]:
        """Identify and resolve conflicting information."""
        pass


class ExportManagerInterface(ABC):
    """Interface for export management components."""
    
    @abstractmethod
    def export_report(self, report: ResearchReport, format_type: str, output_path: str) -> str:
        """Export research report to specified format."""
        pass
    
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """Return list of supported export formats."""
        pass