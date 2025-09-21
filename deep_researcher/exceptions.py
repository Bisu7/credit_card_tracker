"""Custom exceptions for Deep Researcher Agent."""


class DeepResearcherError(Exception):
    """Base exception for all Deep Researcher Agent errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DocumentIngestionError(DeepResearcherError):
    """Errors during document processing and ingestion."""
    pass


class EmbeddingGenerationError(DeepResearcherError):
    """Errors during embedding creation and processing."""
    pass


class VectorStoreError(DeepResearcherError):
    """Errors related to vector storage and retrieval."""
    pass


class DocumentStoreError(DeepResearcherError):
    """Errors related to document storage and retrieval."""
    pass


class QueryProcessingError(DeepResearcherError):
    """Errors during query processing and analysis."""
    pass


class ReasoningError(DeepResearcherError):
    """Errors during multi-step reasoning execution."""
    pass


class RetrievalError(DeepResearcherError):
    """Errors during document retrieval operations."""
    pass


class SynthesisError(DeepResearcherError):
    """Errors during result synthesis and report generation."""
    pass


class ExportError(DeepResearcherError):
    """Errors during result export and formatting."""
    pass


class ConfigurationError(DeepResearcherError):
    """Errors related to system configuration."""
    pass


class ModelLoadError(DeepResearcherError):
    """Errors during model loading and initialization."""
    pass