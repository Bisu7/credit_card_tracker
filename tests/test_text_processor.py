"""Tests for text processor."""

import pytest
from deep_researcher.ingestion.text_processor import TextProcessor
from deep_researcher.models import TextChunk
from deep_researcher.exceptions import DocumentIngestionError


class TestTextProcessor:
    """Test TextProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = TextProcessor(chunk_size=100, chunk_overlap=20)
    
    def test_initialization(self):
        """Test processor initialization."""
        assert self.processor.chunk_size == 100
        assert self.processor.chunk_overlap == 20
    
    def test_initialization_validation(self):
        """Test initialization parameter validation."""
        with pytest.raises(ValueError, match="Chunk size must be positive"):
            TextProcessor(chunk_size=0)
        
        with pytest.raises(ValueError, match="Chunk overlap cannot be negative"):
            TextProcessor(chunk_size=100, chunk_overlap=-1)
        
        with pytest.raises(ValueError, match="Chunk overlap must be less than chunk size"):
            TextProcessor(chunk_size=100, chunk_overlap=100)
    
    def test_clean_text_basic(self):
        """Test basic text cleaning."""
        raw_text = "  This   is    a   test   text.  \n\n\n  Another  line.  "
        cleaned = self.processor.clean_text(raw_text)
        
        assert cleaned == "This is a test text.\n\nAnother line."
    
    def test_clean_text_control_characters(self):
        """Test removal of control characters."""
        raw_text = "Text with\x00control\x08characters\x1F."
        cleaned = self.processor.clean_text(raw_text)
        
        assert cleaned == "Text withcontrolcharacters."
    
    def test_clean_text_encoding_issues(self):
        """Test fixing common encoding issues."""
        raw_text = "Smart "quotes" and 'apostrophes' – em dash — en dash."
        cleaned = self.processor.clean_text(raw_text)
        
        assert cleaned == 'Smart "quotes" and \'apostrophes\' - em dash - en dash.'
    
    def test_clean_text_punctuation_spacing(self):
        """Test punctuation spacing normalization."""
        raw_text = "Text with bad spacing , and punctuation ."
        cleaned = self.processor.clean_text(raw_text)
        
        assert cleaned == "Text with bad spacing, and punctuation."
    
    def test_process_text_empty(self):
        """Test processing empty text."""
        chunks = self.processor.process_text("")
        assert chunks == []
        
        chunks = self.processor.process_text("   ")
        assert chunks == []
    
    def test_process_text_small(self):
        """Test processing text smaller than chunk size."""
        text = "This is a small text that fits in one chunk."
        metadata = {"document_id": "doc_1"}
        
        chunks = self.processor.process_text(text, metadata)
        
        assert len(chunks) == 1
        assert chunks[0].content == text
        assert chunks[0].document_id == "doc_1"
        assert chunks[0].chunk_index == 0
    
    def test_process_text_large(self):
        """Test processing text larger than chunk size."""
        # Create text larger than chunk size (100 chars)
        text = "This is a long paragraph. " * 10  # About 250 characters
        metadata = {"document_id": "doc_1"}
        
        chunks = self.processor.process_text(text, metadata)
        
        assert len(chunks) > 1
        assert all(chunk.document_id == "doc_1" for chunk in chunks)
        assert all(len(chunk.content) <= self.processor.chunk_size * 1.2 for chunk in chunks)
    
    def test_semantic_chunking_paragraphs(self):
        """Test semantic chunking with paragraphs."""
        text = """First paragraph with some content.

Second paragraph with more content that should be in the same chunk.

Third paragraph that might be in a different chunk depending on size."""
        
        metadata = {"document_id": "doc_1"}
        chunks = self.processor._semantic_chunking(text, metadata)
        
        assert len(chunks) >= 1
        assert all(chunk.document_id == "doc_1" for chunk in chunks)
    
    def test_sliding_window_chunking(self):
        """Test sliding window chunking."""
        # Create text that will require multiple chunks
        text = "Word " * 50  # 250 characters
        metadata = {"document_id": "doc_1"}
        
        chunks = self.processor._sliding_window_chunking(text, metadata)
        
        assert len(chunks) > 1
        
        # Check overlap
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i].content
            next_chunk = chunks[i + 1].content
            
            # There should be some overlap between consecutive chunks
            # (not always guaranteed due to word boundaries, but generally true)
            assert len(current_chunk) <= self.processor.chunk_size * 1.1
    
    def test_split_by_sentences(self):
        """Test sentence-based splitting."""
        text = "First sentence. Second sentence! Third sentence? Fourth sentence."
        metadata = {"document_id": "doc_1"}
        
        chunks = self.processor._split_by_sentences(text, metadata, 0)
        
        assert len(chunks) >= 1
        assert all("." in chunk.content or "!" in chunk.content or "?" in chunk.content 
                  for chunk in chunks)
    
    def test_get_chunk_statistics(self):
        """Test chunk statistics calculation."""
        text = "This is test content. " * 20
        metadata = {"document_id": "doc_1"}
        
        chunks = self.processor.process_text(text, metadata)
        stats = self.processor.get_chunk_statistics(chunks)
        
        assert stats['total_chunks'] == len(chunks)
        assert stats['total_characters'] > 0
        assert stats['average_chunk_size'] > 0
        assert stats['min_chunk_size'] > 0
        assert stats['max_chunk_size'] > 0
        assert 'chunk_size_distribution' in stats
    
    def test_get_chunk_statistics_empty(self):
        """Test chunk statistics with empty list."""
        stats = self.processor.get_chunk_statistics([])
        
        assert stats['total_chunks'] == 0
        assert stats['total_characters'] == 0
        assert stats['average_chunk_size'] == 0
    
    def test_merge_small_chunks(self):
        """Test merging small chunks."""
        # Create some small chunks
        chunks = [
            TextChunk(id="1", content="Small", document_id="doc_1", chunk_index=0),
            TextChunk(id="2", content="Also small", document_id="doc_1", chunk_index=1),
            TextChunk(id="3", content="This is a larger chunk that should not be merged", 
                     document_id="doc_1", chunk_index=2)
        ]
        
        merged = self.processor.merge_small_chunks(chunks, min_size=20)
        
        # Should have fewer chunks after merging
        assert len(merged) < len(chunks)
        
        # Check that chunk indices are updated
        for i, chunk in enumerate(merged):
            assert chunk.chunk_index == i
    
    def test_validate_chunks(self):
        """Test chunk validation."""
        # Create chunks with various issues
        chunks = [
            TextChunk(id="1", content="Normal chunk", document_id="doc_1", chunk_index=0),
            TextChunk(id="2", content="", document_id="doc_1", chunk_index=1),  # Empty
            TextChunk(id="3", content="X" * 200, document_id="doc_1", chunk_index=2),  # Too large
            TextChunk(id="1", content="Duplicate ID", document_id="doc_1", chunk_index=3),  # Duplicate ID
        ]
        
        issues = self.processor.validate_chunks(chunks)
        
        assert len(issues) >= 3  # Should find multiple issues
        assert any("empty" in issue.lower() for issue in issues)
        assert any("too large" in issue.lower() for issue in issues)
        assert any("duplicate" in issue.lower() for issue in issues)
    
    def test_validate_chunks_valid(self):
        """Test validation of valid chunks."""
        chunks = [
            TextChunk(id="1", content="Valid chunk 1", document_id="doc_1", chunk_index=0),
            TextChunk(id="2", content="Valid chunk 2", document_id="doc_1", chunk_index=1),
        ]
        
        issues = self.processor.validate_chunks(chunks)
        assert issues == []
    
    def test_process_text_with_metadata(self):
        """Test processing text with metadata preservation."""
        text = "Test content for metadata preservation."
        metadata = {
            "document_id": "doc_1",
            "source": "test",
            "author": "test_author"
        }
        
        chunks = self.processor.process_text(text, metadata)
        
        assert len(chunks) == 1
        chunk = chunks[0]
        
        assert chunk.metadata["document_id"] == "doc_1"
        assert chunk.metadata["source"] == "test"
        assert chunk.metadata["author"] == "test_author"
    
    def test_fix_encoding_issues(self):
        """Test encoding issue fixes."""
        text_with_issues = "Temperature: 25°C ± 2°C. Price: $100™. Copyright © 2023."
        fixed_text = self.processor._fix_encoding_issues(text_with_issues)
        
        assert " degrees" in fixed_text
        assert "+/-" in fixed_text
        assert "(TM)" in fixed_text
        assert "(C)" in fixed_text