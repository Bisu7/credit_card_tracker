"""Text processing and chunking functionality."""

import re
import uuid
from typing import List, Dict, Any, Optional
import logging

from ..models import TextChunk
from ..interfaces import TextProcessorInterface
from ..exceptions import DocumentIngestionError
from ..config import config

logger = logging.getLogger(__name__)


class TextProcessor(TextProcessorInterface):
    """Handles text cleaning, normalization, and chunking."""
    
    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        """
        Initialize text processor.
        
        Args:
            chunk_size: Maximum size of text chunks in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size or config.chunk_size
        self.chunk_overlap = chunk_overlap or config.chunk_overlap
        
        # Validate parameters
        if self.chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        if self.chunk_overlap < 0:
            raise ValueError("Chunk overlap cannot be negative")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")
    
    def process_text(self, raw_text: str, metadata: Dict[str, Any] = None) -> List[TextChunk]:
        """
        Process raw text into chunks.
        
        Args:
            raw_text: Raw text content to process
            metadata: Optional metadata to include with chunks
            
        Returns:
            List of TextChunk objects
        """
        if not raw_text or not raw_text.strip():
            return []
        
        try:
            # Clean and normalize text
            cleaned_text = self.clean_text(raw_text)
            
            if not cleaned_text.strip():
                return []
            
            # Create chunks
            chunks = self._create_chunks(cleaned_text, metadata or {})
            
            logger.info(f"Processed text into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Text processing failed: {e}")
            raise DocumentIngestionError(f"Text processing failed: {e}")
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive newlines (more than 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Remove excessive spaces around punctuation
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)
        text = re.sub(r'([,.!?;:])\s+', r'\1 ', text)
        
        # Fix common encoding issues
        text = self._fix_encoding_issues(text)
        
        return text.strip()
    
    def _fix_encoding_issues(self, text: str) -> str:
        """Fix common encoding and character issues."""
        # Common replacements for encoding issues
        replacements = {
            '"': '"',  # Smart quotes
            '"': '"',
            ''': "'",
            ''': "'",
            '–': '-',  # En dash
            '—': '-',  # Em dash
            '…': '...',  # Ellipsis
            '™': '(TM)',
            '®': '(R)',
            '©': '(C)',
            '°': ' degrees',
            '±': '+/-',
            '×': 'x',
            '÷': '/',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _create_chunks(self, text: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """
        Create text chunks from cleaned text.
        
        Args:
            text: Cleaned text to chunk
            metadata: Metadata to include with chunks
            
        Returns:
            List of TextChunk objects
        """
        if len(text) <= self.chunk_size:
            # Text is small enough to be a single chunk
            chunk = TextChunk(
                id=str(uuid.uuid4()),
                content=text,
                document_id=metadata.get('document_id', ''),
                chunk_index=0,
                metadata=metadata.copy()
            )
            return [chunk]
        
        # Use semantic chunking strategy
        chunks = self._semantic_chunking(text, metadata)
        
        # If semantic chunking fails or produces too large chunks, fall back to sliding window
        if not chunks or any(len(chunk.content) > self.chunk_size * 1.2 for chunk in chunks):
            logger.warning("Falling back to sliding window chunking")
            chunks = self._sliding_window_chunking(text, metadata)
        
        return chunks
    
    def _semantic_chunking(self, text: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """
        Create chunks based on semantic boundaries (paragraphs, sentences).
        
        Args:
            text: Text to chunk
            metadata: Metadata for chunks
            
        Returns:
            List of TextChunk objects
        """
        chunks = []
        
        # Split by paragraphs first
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) + 2 > self.chunk_size:
                if current_chunk:
                    # Save current chunk
                    chunk = TextChunk(
                        id=str(uuid.uuid4()),
                        content=current_chunk.strip(),
                        document_id=metadata.get('document_id', ''),
                        chunk_index=chunk_index,
                        metadata=metadata.copy()
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Handle large paragraphs
                if len(paragraph) > self.chunk_size:
                    # Split large paragraph by sentences
                    sentence_chunks = self._split_by_sentences(paragraph, metadata, chunk_index)
                    chunks.extend(sentence_chunks)
                    chunk_index += len(sentence_chunks)
                    current_chunk = ""
                else:
                    current_chunk = paragraph
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add final chunk if there's remaining content
        if current_chunk:
            chunk = TextChunk(
                id=str(uuid.uuid4()),
                content=current_chunk.strip(),
                document_id=metadata.get('document_id', ''),
                chunk_index=chunk_index,
                metadata=metadata.copy()
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_by_sentences(self, text: str, metadata: Dict[str, Any], start_index: int) -> List[TextChunk]:
        """
        Split text by sentences when paragraphs are too large.
        
        Args:
            text: Text to split
            metadata: Metadata for chunks
            start_index: Starting chunk index
            
        Returns:
            List of TextChunk objects
        """
        # Simple sentence splitting (can be improved with NLP libraries)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        chunk_index = start_index
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > self.chunk_size:
                if current_chunk:
                    chunk = TextChunk(
                        id=str(uuid.uuid4()),
                        content=current_chunk.strip(),
                        document_id=metadata.get('document_id', ''),
                        chunk_index=chunk_index,
                        metadata=metadata.copy()
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                
                # If single sentence is too long, it will be handled by sliding window
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add final chunk
        if current_chunk:
            chunk = TextChunk(
                id=str(uuid.uuid4()),
                content=current_chunk.strip(),
                document_id=metadata.get('document_id', ''),
                chunk_index=chunk_index,
                metadata=metadata.copy()
            )
            chunks.append(chunk)
        
        return chunks
    
    def _sliding_window_chunking(self, text: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """
        Create chunks using sliding window approach.
        
        Args:
            text: Text to chunk
            metadata: Metadata for chunks
            
        Returns:
            List of TextChunk objects
        """
        chunks = []
        chunk_index = 0
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # If this is not the last chunk, try to end at a word boundary
            if end < len(text):
                # Look for the last space within the chunk
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk = TextChunk(
                    id=str(uuid.uuid4()),
                    content=chunk_text,
                    document_id=metadata.get('document_id', ''),
                    chunk_index=chunk_index,
                    metadata=metadata.copy()
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            
            # Ensure we make progress
            if start <= chunks[-1].content.rfind(' ') if chunks else 0:
                start = end
        
        return chunks
    
    def get_chunk_statistics(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """
        Get statistics about the chunks.
        
        Args:
            chunks: List of chunks to analyze
            
        Returns:
            Dictionary with chunk statistics
        """
        if not chunks:
            return {
                'total_chunks': 0,
                'total_characters': 0,
                'average_chunk_size': 0,
                'min_chunk_size': 0,
                'max_chunk_size': 0
            }
        
        chunk_sizes = [len(chunk.content) for chunk in chunks]
        
        return {
            'total_chunks': len(chunks),
            'total_characters': sum(chunk_sizes),
            'average_chunk_size': sum(chunk_sizes) / len(chunk_sizes),
            'min_chunk_size': min(chunk_sizes),
            'max_chunk_size': max(chunk_sizes),
            'chunk_size_distribution': {
                'small': len([s for s in chunk_sizes if s < self.chunk_size * 0.5]),
                'medium': len([s for s in chunk_sizes if self.chunk_size * 0.5 <= s < self.chunk_size * 0.8]),
                'large': len([s for s in chunk_sizes if s >= self.chunk_size * 0.8])
            }
        }
    
    def merge_small_chunks(self, chunks: List[TextChunk], min_size: Optional[int] = None) -> List[TextChunk]:
        """
        Merge chunks that are smaller than the minimum size.
        
        Args:
            chunks: List of chunks to process
            min_size: Minimum chunk size (default: chunk_size / 4)
            
        Returns:
            List of merged chunks
        """
        if not chunks:
            return []
        
        min_size = min_size or (self.chunk_size // 4)
        merged_chunks = []
        current_chunk = None
        
        for chunk in chunks:
            if len(chunk.content) < min_size and current_chunk is not None:
                # Merge with previous chunk if combined size is reasonable
                combined_content = current_chunk.content + "\n\n" + chunk.content
                if len(combined_content) <= self.chunk_size * 1.2:
                    current_chunk.content = combined_content
                    continue
            
            # Save previous chunk if exists
            if current_chunk is not None:
                merged_chunks.append(current_chunk)
            
            # Start new chunk
            current_chunk = TextChunk(
                id=str(uuid.uuid4()),
                content=chunk.content,
                document_id=chunk.document_id,
                chunk_index=len(merged_chunks),
                metadata=chunk.metadata.copy()
            )
        
        # Add final chunk
        if current_chunk is not None:
            merged_chunks.append(current_chunk)
        
        return merged_chunks
    
    def validate_chunks(self, chunks: List[TextChunk]) -> List[str]:
        """
        Validate chunks and return list of issues found.
        
        Args:
            chunks: List of chunks to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        for i, chunk in enumerate(chunks):
            # Check chunk size
            if len(chunk.content) > self.chunk_size * 1.5:
                issues.append(f"Chunk {i} is too large: {len(chunk.content)} characters")
            
            # Check for empty chunks
            if not chunk.content.strip():
                issues.append(f"Chunk {i} is empty or contains only whitespace")
            
            # Check chunk index consistency
            if chunk.chunk_index != i:
                issues.append(f"Chunk {i} has incorrect index: {chunk.chunk_index}")
            
            # Check for duplicate IDs
            for j, other_chunk in enumerate(chunks[i+1:], i+1):
                if chunk.id == other_chunk.id:
                    issues.append(f"Duplicate chunk ID found: chunks {i} and {j}")
        
        return issues