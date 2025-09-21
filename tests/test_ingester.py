"""Tests for document ingester."""

import pytest
import tempfile
import os
from pathlib import Path

from deep_researcher.ingestion.ingester import DocumentIngester
from deep_researcher.models import DocumentFormat
from deep_researcher.exceptions import DocumentIngestionError


class TestDocumentIngester:
    """Test DocumentIngester class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.ingester = DocumentIngester()
    
    def test_supported_formats(self):
        """Test supported formats list."""
        formats = self.ingester.supported_formats()
        
        expected_formats = ['pdf', 'txt', 'docx', 'md', 'html']
        assert all(fmt in formats for fmt in expected_formats)
        assert len(formats) == 5
    
    def test_detect_format_txt(self):
        """Test format detection for text files."""
        format_type = self.ingester._detect_format("test.txt")
        assert format_type == DocumentFormat.TXT
    
    def test_detect_format_pdf(self):
        """Test format detection for PDF files."""
        format_type = self.ingester._detect_format("test.pdf")
        assert format_type == DocumentFormat.PDF
    
    def test_detect_format_docx(self):
        """Test format detection for DOCX files."""
        format_type = self.ingester._detect_format("test.docx")
        assert format_type == DocumentFormat.DOCX
        
        # Test .doc extension
        format_type = self.ingester._detect_format("test.doc")
        assert format_type == DocumentFormat.DOCX
    
    def test_detect_format_markdown(self):
        """Test format detection for Markdown files."""
        format_type = self.ingester._detect_format("test.md")
        assert format_type == DocumentFormat.MD
        
        format_type = self.ingester._detect_format("test.markdown")
        assert format_type == DocumentFormat.MD
    
    def test_detect_format_html(self):
        """Test format detection for HTML files."""
        format_type = self.ingester._detect_format("test.html")
        assert format_type == DocumentFormat.HTML
        
        format_type = self.ingester._detect_format("test.htm")
        assert format_type == DocumentFormat.HTML
    
    def test_detect_format_unsupported(self):
        """Test format detection for unsupported files."""
        with pytest.raises(DocumentIngestionError, match="Unsupported file extension"):
            self.ingester._detect_format("test.xyz")
    
    def test_extract_txt_content(self):
        """Test text file content extraction."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            test_content = "This is a test document.\nIt has multiple lines.\nAnd some content."
            f.write(test_content)
            f.flush()
            
            try:
                content, metadata = self.ingester._extract_txt_content(f.name)
                
                assert content == test_content
                assert 'encoding' in metadata
                assert 'file_size' in metadata
                assert 'line_count' in metadata
                assert metadata['line_count'] == 3
                
            finally:
                os.unlink(f.name)
    
    def test_extract_markdown_content(self):
        """Test Markdown file content extraction."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            markdown_content = """---
title: Test Document
author: Test Author
---

# Test Heading

This is **bold** text and this is *italic* text.

## Subheading

- List item 1
- List item 2
"""
            f.write(markdown_content)
            f.flush()
            
            try:
                content, metadata = self.ingester._extract_markdown_content(f.name)
                
                assert "Test Heading" in content
                assert "bold" in content
                assert "italic" in content
                assert "List item 1" in content
                
                assert metadata['title'] == 'Test Document'
                assert metadata['author'] == 'Test Author'
                assert metadata['has_front_matter'] is True
                
            finally:
                os.unlink(f.name)
    
    def test_extract_html_content(self):
        """Test HTML file content extraction."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Test HTML Document</title>
    <meta name="author" content="Test Author">
    <meta name="description" content="Test description">
</head>
<body>
    <h1>Main Heading</h1>
    <p>This is a paragraph with <strong>bold</strong> text.</p>
    <ul>
        <li>List item 1</li>
        <li>List item 2</li>
    </ul>
</body>
</html>"""
            f.write(html_content)
            f.flush()
            
            try:
                content, metadata = self.ingester._extract_html_content(f.name)
                
                assert "Main Heading" in content
                assert "This is a paragraph" in content
                assert "bold" in content
                assert "List item 1" in content
                
                assert metadata['html_title'] == 'Test HTML Document'
                assert metadata['meta_author'] == 'Test Author'
                assert metadata['meta_description'] == 'Test description'
                assert metadata['has_title'] is True
                
            finally:
                os.unlink(f.name)
    
    def test_extract_title_from_metadata(self):
        """Test title extraction from metadata."""
        metadata = {'title': 'Document Title from Metadata'}
        content = "Some content here"
        file_path = "/path/to/document.txt"
        
        title = self.ingester._extract_title(file_path, content, metadata)
        assert title == 'Document Title from Metadata'
    
    def test_extract_title_from_content(self):
        """Test title extraction from content first line."""
        metadata = {}
        content = "This is the title line\nThis is the rest of the content"
        file_path = "/path/to/document.txt"
        
        title = self.ingester._extract_title(file_path, content, metadata)
        assert title == 'This is the title line'
    
    def test_extract_title_from_filename(self):
        """Test title extraction from filename as fallback."""
        metadata = {}
        content = "Some very long first line that is too long to be a reasonable title and should not be used as the document title because it exceeds the length limit"
        file_path = "/path/to/my_document.txt"
        
        title = self.ingester._extract_title(file_path, content, metadata)
        assert title == 'my_document'
    
    def test_ingest_nonexistent_file(self):
        """Test ingestion of non-existent file."""
        with pytest.raises(DocumentIngestionError, match="File not found"):
            self.ingester.ingest_document("/nonexistent/file.txt")
    
    def test_get_file_info(self):
        """Test getting file information."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            f.flush()
            
            try:
                info = self.ingester.get_file_info(f.name)
                
                assert info['file_path'] == f.name
                assert info['file_name'] == Path(f.name).name
                assert info['file_size'] > 0
                assert info['format_type'] == 'txt'
                assert info['is_supported'] is True
                assert 'modified_time' in info
                
            finally:
                os.unlink(f.name)
    
    def test_get_file_info_nonexistent(self):
        """Test getting info for non-existent file."""
        with pytest.raises(DocumentIngestionError, match="File not found"):
            self.ingester.get_file_info("/nonexistent/file.txt")
    
    def test_batch_ingest_empty_list(self):
        """Test batch ingestion with empty list."""
        documents = self.ingester.batch_ingest([])
        assert documents == []
    
    def test_ingest_document_full_txt(self):
        """Test full document ingestion for text file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            test_content = "Test Document Title\n\nThis is the content of the test document."
            f.write(test_content)
            f.flush()
            
            try:
                document = self.ingester.ingest_document_full(f.name)
                
                assert document.title == "Test Document Title"
                assert document.content == test_content
                assert document.source_path == f.name
                assert document.format_type == DocumentFormat.TXT
                assert 'encoding' in document.metadata
                assert document.word_count > 0
                 
            finally:
                os.unlink(f.name)