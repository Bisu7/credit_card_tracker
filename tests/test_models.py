"""Tests for core data models."""

import pytest
from datetime import datetime
import numpy as np

from deep_researcher.models import (
    Document, TextChunk, ProcessedQuery, ReasoningStep, ResearchReport,
    SearchResult, QueryType, DocumentFormat
)


class TestTextChunk:
    """Test TextChunk model."""
    
    def test_valid_chunk_creation(self):
        """Test creating a valid text chunk."""
        chunk = TextChunk(
            id="chunk_1",
            content="This is test content",
            document_id="doc_1",
            chunk_index=0
        )
        
        assert chunk.id == "chunk_1"
        assert chunk.content == "This is test content"
        assert chunk.document_id == "doc_1"
        assert chunk.chunk_index == 0
        assert isinstance(chunk.created_at, datetime)
    
    def test_empty_content_validation(self):
        """Test validation of empty content."""
        with pytest.raises(ValueError, match="Chunk content cannot be empty"):
            TextChunk(
                id="chunk_1",
                content="   ",  # Only whitespace
                document_id="doc_1",
                chunk_index=0
            )
    
    def test_negative_chunk_index_validation(self):
        """Test validation of negative chunk index."""
        with pytest.raises(ValueError, match="Chunk index must be non-negative"):
            TextChunk(
                id="chunk_1",
                content="Valid content",
                document_id="doc_1",
                chunk_index=-1
            )
    
    def test_content_hash_generation(self):
        """Test content hash generation."""
        chunk = TextChunk(
            id="chunk_1",
            content="Test content",
            document_id="doc_1",
            chunk_index=0
        )
        
        hash1 = chunk.content_hash
        assert isinstance(hash1, str)
        assert len(hash1) == 32  # MD5 hash length
        
        # Same content should produce same hash
        chunk2 = TextChunk(
            id="chunk_2",
            content="Test content",
            document_id="doc_2",
            chunk_index=1
        )
        assert chunk2.content_hash == hash1
    
    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        chunk = TextChunk(
            id="chunk_1",
            content="Test content",
            document_id="doc_1",
            chunk_index=0,
            metadata={"source": "test"}
        )
        
        data = chunk.to_dict()
        
        assert data["id"] == "chunk_1"
        assert data["content"] == "Test content"
        assert data["document_id"] == "doc_1"
        assert data["chunk_index"] == 0
        assert data["metadata"] == {"source": "test"}
        assert "created_at" in data
        assert "content_hash" in data
    
    def test_from_dict_creation(self):
        """Test creation from dictionary."""
        data = {
            "id": "chunk_1",
            "content": "Test content",
            "document_id": "doc_1",
            "chunk_index": 0,
            "metadata": {"source": "test"},
            "created_at": datetime.now().isoformat()
        }
        
        chunk = TextChunk.from_dict(data)
        
        assert chunk.id == "chunk_1"
        assert chunk.content == "Test content"
        assert chunk.document_id == "doc_1"
        assert chunk.chunk_index == 0
        assert chunk.metadata == {"source": "test"}


class TestDocument:
    """Test Document model."""
    
    def test_valid_document_creation(self):
        """Test creating a valid document."""
        doc = Document(
            id="doc_1",
            title="Test Document",
            content="This is test content for the document.",
            source_path="/path/to/test.txt",
            format_type=DocumentFormat.TXT
        )
        
        assert doc.id == "doc_1"
        assert doc.title == "Test Document"
        assert doc.source_path == "/path/to/test.txt"
        assert doc.format_type == DocumentFormat.TXT
        assert isinstance(doc.created_at, datetime)
        assert doc.chunks == []
    
    def test_empty_title_validation(self):
        """Test validation of empty title."""
        with pytest.raises(ValueError, match="Document title cannot be empty"):
            Document(
                id="doc_1",
                title="   ",
                content="Valid content",
                source_path="/path/to/test.txt",
                format_type=DocumentFormat.TXT
            )
    
    def test_word_count_property(self):
        """Test word count calculation."""
        doc = Document(
            id="doc_1",
            title="Test Document",
            content="This is a test document with ten words total.",
            source_path="/path/to/test.txt",
            format_type=DocumentFormat.TXT
        )
        
        assert doc.word_count == 10
    
    def test_add_chunk_functionality(self):
        """Test adding chunks to document."""
        doc = Document(
            id="doc_1",
            title="Test Document",
            content="Test content",
            source_path="/path/to/test.txt",
            format_type=DocumentFormat.TXT
        )
        
        chunk = TextChunk(
            id="chunk_1",
            content="Test chunk",
            document_id="doc_1",
            chunk_index=0
        )
        
        doc.add_chunk(chunk)
        
        assert len(doc.chunks) == 1
        assert doc.chunks[0] == chunk
        assert doc.chunk_count == 1
    
    def test_add_chunk_validation(self):
        """Test validation when adding chunks."""
        doc = Document(
            id="doc_1",
            title="Test Document",
            content="Test content",
            source_path="/path/to/test.txt",
            format_type=DocumentFormat.TXT
        )
        
        chunk = TextChunk(
            id="chunk_1",
            content="Test chunk",
            document_id="wrong_doc_id",  # Wrong document ID
            chunk_index=0
        )
        
        with pytest.raises(ValueError, match="Chunk document_id must match document id"):
            doc.add_chunk(chunk)


class TestProcessedQuery:
    """Test ProcessedQuery model."""
    
    def test_valid_query_creation(self):
        """Test creating a valid processed query."""
        query = ProcessedQuery(
            original_query="What is machine learning?",
            query_type=QueryType.SIMPLE,
            complexity_score=0.3,
            expected_sources=5
        )
        
        assert query.original_query == "What is machine learning?"
        assert query.query_type == QueryType.SIMPLE
        assert query.complexity_score == 0.3
        assert query.expected_sources == 5
        assert not query.is_complex
    
    def test_complex_query_detection(self):
        """Test complex query detection."""
        query = ProcessedQuery(
            original_query="Compare machine learning and deep learning approaches",
            query_type=QueryType.COMPARATIVE,
            complexity_score=0.8,
            sub_queries=["What is machine learning?", "What is deep learning?"]
        )
        
        assert query.is_complex
    
    def test_complexity_score_validation(self):
        """Test complexity score validation."""
        with pytest.raises(ValueError, match="Complexity score must be between 0 and 1"):
            ProcessedQuery(
                original_query="Test query",
                query_type=QueryType.SIMPLE,
                complexity_score=1.5  # Invalid score
            )


class TestResearchReport:
    """Test ResearchReport model."""
    
    def test_valid_report_creation(self):
        """Test creating a valid research report."""
        doc = Document(
            id="doc_1",
            title="Test Document",
            content="Test content",
            source_path="/path/to/test.txt",
            format_type=DocumentFormat.TXT
        )
        
        report = ResearchReport(
            query="What is AI?",
            summary="AI is artificial intelligence.",
            key_findings=["AI involves machine learning", "AI has many applications"],
            sources=[doc]
        )
        
        assert report.query == "What is AI?"
        assert report.summary == "AI is artificial intelligence."
        assert len(report.key_findings) == 2
        assert report.source_count == 1
        assert report.total_reasoning_steps == 0
    
    def test_add_source_functionality(self):
        """Test adding sources to report."""
        report = ResearchReport(
            query="Test query",
            summary="Test summary",
            key_findings=["Finding 1"],
            sources=[]
        )
        
        doc = Document(
            id="doc_1",
            title="Test Document",
            content="Test content",
            source_path="/path/to/test.txt",
            format_type=DocumentFormat.TXT
        )
        
        report.add_source(doc)
        
        assert report.source_count == 1
        assert doc in report.sources
        
        # Adding same document again should not duplicate
        report.add_source(doc)
        assert report.source_count == 1


class TestSearchResult:
    """Test SearchResult model."""
    
    def test_valid_search_result_creation(self):
        """Test creating a valid search result."""
        result = SearchResult(
            document_id="doc_1",
            chunk_id="chunk_1",
            similarity_score=0.85,
            content="Relevant content found"
        )
        
        assert result.document_id == "doc_1"
        assert result.chunk_id == "chunk_1"
        assert result.similarity_score == 0.85
        assert result.content == "Relevant content found"
        assert result.is_relevant  # Score > 0.7
    
    def test_relevance_threshold(self):
        """Test relevance threshold detection."""
        low_score_result = SearchResult(
            document_id="doc_1",
            chunk_id="chunk_1",
            similarity_score=0.5,
            content="Less relevant content"
        )
        
        assert not low_score_result.is_relevant
    
    def test_similarity_score_validation(self):
        """Test similarity score validation."""
        with pytest.raises(ValueError, match="Similarity score must be between 0 and 1"):
            SearchResult(
                document_id="doc_1",
                chunk_id="chunk_1",
                similarity_score=1.5,  # Invalid score
                content="Test content"
            )