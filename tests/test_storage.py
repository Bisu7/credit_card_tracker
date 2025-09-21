"""Tests for storage components."""

import pytest
import tempfile
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch

from deep_researcher.storage.vector_store import VectorStore
from deep_researcher.storage.document_store import DocumentStore
from deep_researcher.models import Document, TextChunk, DocumentFormat
from deep_researcher.exceptions import VectorStoreError, DocumentStoreError


class TestVectorStore:
    """Test VectorStore class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use temporary directory for test index
        self.temp_dir = tempfile.mkdtemp()
        self.index_path = Path(self.temp_dir) / "test_index.faiss"
        
        # Mock FAISS to avoid dependency in tests
        self.mock_index = Mock()
        self.mock_index.ntotal = 0
        self.mock_index.search.return_value = (np.array([[0.9, 0.8]]), np.array([[0, 1]]))
        
        with patch('deep_researcher.storage.vector_store.faiss') as mock_faiss:
            mock_faiss.IndexFlatIP.return_value = self.mock_index
            mock_faiss.read_index.return_value = self.mock_index
            mock_faiss.write_index = Mock()
            
            self.vector_store = VectorStore(str(self.index_path), dimension=384)
    
    def test_initialization(self):
        """Test vector store initialization."""
        assert self.vector_store.dimension == 384
        assert self.vector_store.index is not None
        assert self.vector_store.next_index == 0
    
    def test_initialization_no_faiss(self):
        """Test initialization when FAISS is not available."""
        with patch('deep_researcher.storage.vector_store.faiss', None):
            with pytest.raises(VectorStoreError, match="FAISS library not installed"):
                VectorStore()
    
    def test_add_vectors(self):
        """Test adding vectors to the store."""
        vectors = np.random.rand(3, 384)
        metadata = [
            {'chunk_id': 'chunk1', 'document_id': 'doc1'},
            {'chunk_id': 'chunk2', 'document_id': 'doc1'},
            {'chunk_id': 'chunk3', 'document_id': 'doc2'}
        ]
        
        vector_ids = self.vector_store.add_vectors(vectors, metadata)
        
        assert len(vector_ids) == 3
        assert all(isinstance(vid, str) for vid in vector_ids)
        assert self.vector_store.next_index == 3
        
        # Verify metadata is stored
        for vid, meta in zip(vector_ids, metadata):
            stored_meta = self.vector_store.get_vector_metadata(vid)
            assert stored_meta['chunk_id'] == meta['chunk_id']
    
    def test_add_vectors_dimension_mismatch(self):
        """Test adding vectors with wrong dimension."""
        vectors = np.random.rand(2, 256)  # Wrong dimension
        metadata = [{'chunk_id': 'chunk1'}, {'chunk_id': 'chunk2'}]
        
        with pytest.raises(VectorStoreError, match="Vector dimension"):
            self.vector_store.add_vectors(vectors, metadata)
    
    def test_add_vectors_metadata_mismatch(self):
        """Test adding vectors with mismatched metadata count."""
        vectors = np.random.rand(2, 384)
        metadata = [{'chunk_id': 'chunk1'}]  # Only one metadata for two vectors
        
        with pytest.raises(VectorStoreError, match="Number of vectors must match"):
            self.vector_store.add_vectors(vectors, metadata)
    
    def test_search_empty_index(self):
        """Test searching in empty index."""
        query_vector = np.random.rand(384)
        results = self.vector_store.search(query_vector, k=5)
        
        assert results == []
    
    def test_search_with_results(self):
        """Test searching with results."""
        # Add some vectors first
        vectors = np.random.rand(2, 384)
        metadata = [
            {'chunk_id': 'chunk1', 'content': 'test content 1'},
            {'chunk_id': 'chunk2', 'content': 'test content 2'}
        ]
        
        vector_ids = self.vector_store.add_vectors(vectors, metadata)
        
        # Mock the index to have vectors
        self.mock_index.ntotal = 2
        
        # Perform search
        query_vector = np.random.rand(384)
        results = self.vector_store.search(query_vector, k=2)
        
        assert len(results) <= 2
        # Results structure depends on mock behavior
    
    def test_search_wrong_dimension(self):
        """Test searching with wrong query dimension."""
        query_vector = np.random.rand(256)  # Wrong dimension
        
        with pytest.raises(VectorStoreError, match="Query vector dimension"):
            self.vector_store.search(query_vector)
    
    def test_delete_vectors(self):
        """Test deleting vectors."""
        # Add vectors first
        vectors = np.random.rand(2, 384)
        metadata = [{'chunk_id': 'chunk1'}, {'chunk_id': 'chunk2'}]
        vector_ids = self.vector_store.add_vectors(vectors, metadata)
        
        # Delete one vector
        self.vector_store.delete_vectors([vector_ids[0]])
        
        # Check that it's marked as deleted
        meta = self.vector_store.get_vector_metadata(vector_ids[0])
        assert meta['_deleted'] is True
    
    def test_get_vector_metadata(self):
        """Test getting vector metadata."""
        vectors = np.random.rand(1, 384)
        metadata = [{'chunk_id': 'chunk1', 'test_field': 'test_value'}]
        vector_ids = self.vector_store.add_vectors(vectors, metadata)
        
        retrieved_meta = self.vector_store.get_vector_metadata(vector_ids[0])
        
        assert retrieved_meta['chunk_id'] == 'chunk1'
        assert retrieved_meta['test_field'] == 'test_value'
    
    def test_update_vector_metadata(self):
        """Test updating vector metadata."""
        vectors = np.random.rand(1, 384)
        metadata = [{'chunk_id': 'chunk1'}]
        vector_ids = self.vector_store.add_vectors(vectors, metadata)
        
        # Update metadata
        new_metadata = {'updated_field': 'new_value'}
        result = self.vector_store.update_vector_metadata(vector_ids[0], new_metadata)
        
        assert result is True
        
        # Verify update
        retrieved_meta = self.vector_store.get_vector_metadata(vector_ids[0])
        assert retrieved_meta['updated_field'] == 'new_value'
        assert retrieved_meta['chunk_id'] == 'chunk1'  # Original data preserved
    
    def test_get_statistics(self):
        """Test getting vector store statistics."""
        # Add some vectors
        vectors = np.random.rand(3, 384)
        metadata = [{'chunk_id': f'chunk{i}'} for i in range(3)]
        self.vector_store.add_vectors(vectors, metadata)
        
        # Mock index total
        self.mock_index.ntotal = 3
        
        stats = self.vector_store.get_statistics()
        
        assert stats['dimension'] == 384
        assert stats['metadata_count'] == 3
        assert 'index_type' in stats
        assert 'index_path' in stats
    
    def test_normalize_vectors(self):
        """Test vector normalization."""
        vectors = np.array([[3.0, 4.0], [1.0, 0.0]])
        normalized = self.vector_store._normalize_vectors(vectors)
        
        # Check that vectors are normalized (unit length)
        norms = np.linalg.norm(normalized, axis=1)
        np.testing.assert_allclose(norms, 1.0, rtol=1e-6)
    
    def test_clear_index(self):
        """Test clearing the index."""
        # Add some vectors
        vectors = np.random.rand(2, 384)
        metadata = [{'chunk_id': 'chunk1'}, {'chunk_id': 'chunk2'}]
        self.vector_store.add_vectors(vectors, metadata)
        
        # Clear index
        self.vector_store.clear_index()
        
        assert len(self.vector_store.metadata) == 0
        assert len(self.vector_store.id_to_index) == 0
        assert self.vector_store.next_index == 0


class TestDocumentStore:
    """Test DocumentStore class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use in-memory SQLite database for tests
        self.temp_db = ":memory:"
        
        with patch('deep_researcher.storage.document_store.db_manager') as mock_db_manager:
            # Create a real database manager for testing
            from deep_researcher.database import DatabaseManager
            mock_db_manager.get_connection = DatabaseManager(self.temp_db).get_connection
            mock_db_manager.ensure_database_exists = DatabaseManager(self.temp_db).ensure_database_exists
            
            self.document_store = DocumentStore()
    
    def create_test_document(self) -> Document:
        """Create a test document."""
        return Document(
            id="test_doc_1",
            title="Test Document",
            content="This is test content for the document.",
            source_path="/path/to/test.txt",
            format_type=DocumentFormat.TXT,
            metadata={"author": "test_author", "category": "test"}
        )
    
    def create_test_chunk(self, document_id: str, index: int = 0) -> TextChunk:
        """Create a test chunk."""
        return TextChunk(
            id=f"chunk_{index}",
            content=f"This is chunk {index} content.",
            document_id=document_id,
            chunk_index=index,
            metadata={"chunk_type": "test"}
        )
    
    def test_store_document(self):
        """Test storing a document."""
        document = self.create_test_document()
        
        # Add some chunks
        chunk1 = self.create_test_chunk(document.id, 0)
        chunk2 = self.create_test_chunk(document.id, 1)
        document.add_chunk(chunk1)
        document.add_chunk(chunk2)
        
        # Store document
        stored_id = self.document_store.store_document(document)
        
        assert stored_id == document.id
    
    def test_store_duplicate_document(self):
        """Test storing duplicate document (same content hash)."""
        document1 = self.create_test_document()
        document2 = Document(
            id="test_doc_2",
            title="Different Title",
            content=document1.content,  # Same content
            source_path="/different/path.txt",
            format_type=DocumentFormat.TXT
        )
        
        # Store first document
        id1 = self.document_store.store_document(document1)
        
        # Store duplicate (should return existing ID)
        id2 = self.document_store.store_document(document2)
        
        assert id1 == id2  # Should return the same ID
    
    def test_get_document(self):
        """Test retrieving a document."""
        document = self.create_test_document()
        chunk = self.create_test_chunk(document.id)
        document.add_chunk(chunk)
        
        # Store and retrieve
        self.document_store.store_document(document)
        retrieved = self.document_store.get_document(document.id)
        
        assert retrieved is not None
        assert retrieved.id == document.id
        assert retrieved.title == document.title
        assert retrieved.format_type == document.format_type
        assert len(retrieved.chunks) == 1
        assert retrieved.chunks[0].content == chunk.content
    
    def test_get_nonexistent_document(self):
        """Test retrieving non-existent document."""
        result = self.document_store.get_document("nonexistent_id")
        assert result is None
    
    def test_search_documents(self):
        """Test searching documents."""
        # Store multiple documents
        doc1 = Document(
            id="doc1", title="Machine Learning Basics", content="Introduction to ML",
            source_path="/ml.txt", format_type=DocumentFormat.TXT
        )
        doc2 = Document(
            id="doc2", title="Deep Learning Guide", content="Neural networks and deep learning",
            source_path="/dl.txt", format_type=DocumentFormat.TXT
        )
        
        self.document_store.store_document(doc1)
        self.document_store.store_document(doc2)
        
        # Search for documents
        results = self.document_store.search_documents("learning")
        
        assert len(results) == 2
        assert all(doc.id in ["doc1", "doc2"] for doc in results)
    
    def test_search_documents_with_filters(self):
        """Test searching documents with filters."""
        doc = self.create_test_document()
        self.document_store.store_document(doc)
        
        # Search with format filter
        results = self.document_store.search_documents(
            "test", 
            filters={'format_type': 'txt'}
        )
        
        assert len(results) >= 0  # Should not error
    
    def test_delete_document(self):
        """Test deleting a document."""
        document = self.create_test_document()
        chunk = self.create_test_chunk(document.id)
        document.add_chunk(chunk)
        
        # Store and delete
        self.document_store.store_document(document)
        self.document_store.delete_document(document.id)
        
        # Verify deletion
        retrieved = self.document_store.get_document(document.id)
        assert retrieved is None
    
    def test_get_chunk(self):
        """Test getting a specific chunk."""
        document = self.create_test_document()
        chunk = self.create_test_chunk(document.id)
        document.add_chunk(chunk)
        
        self.document_store.store_document(document)
        
        retrieved_chunk = self.document_store.get_chunk(chunk.id)
        
        assert retrieved_chunk is not None
        assert retrieved_chunk.id == chunk.id
        assert retrieved_chunk.content == chunk.content
        assert retrieved_chunk.document_id == document.id
    
    def test_get_chunks_by_document(self):
        """Test getting all chunks for a document."""
        document = self.create_test_document()
        chunk1 = self.create_test_chunk(document.id, 0)
        chunk2 = self.create_test_chunk(document.id, 1)
        document.add_chunk(chunk1)
        document.add_chunk(chunk2)
        
        self.document_store.store_document(document)
        
        chunks = self.document_store.get_chunks_by_document(document.id)
        
        assert len(chunks) == 2
        assert chunks[0].chunk_index == 0
        assert chunks[1].chunk_index == 1
    
    def test_update_document_metadata(self):
        """Test updating document metadata."""
        document = self.create_test_document()
        self.document_store.store_document(document)
        
        new_metadata = {"updated": True, "version": 2}
        result = self.document_store.update_document_metadata(document.id, new_metadata)
        
        assert result is True
        
        # Verify update
        retrieved = self.document_store.get_document(document.id)
        assert retrieved.metadata == new_metadata
    
    def test_list_documents(self):
        """Test listing documents."""
        # Store multiple documents
        for i in range(3):
            doc = Document(
                id=f"doc_{i}",
                title=f"Document {i}",
                content=f"Content {i}",
                source_path=f"/doc_{i}.txt",
                format_type=DocumentFormat.TXT
            )
            self.document_store.store_document(doc)
        
        # List documents
        documents = self.document_store.list_documents(limit=2)
        
        assert len(documents) == 2
        assert all('id' in doc for doc in documents)
        assert all('title' in doc for doc in documents)
    
    def test_get_statistics(self):
        """Test getting storage statistics."""
        # Store a document with chunks
        document = self.create_test_document()
        chunk = self.create_test_chunk(document.id)
        document.add_chunk(chunk)
        
        self.document_store.store_document(document)
        
        stats = self.document_store.get_statistics()
        
        assert stats['total_documents'] >= 1
        assert stats['total_chunks'] >= 1
        assert 'format_distribution' in stats
        assert 'word_count_stats' in stats
    
    def test_cleanup_orphaned_chunks(self):
        """Test cleaning up orphaned chunks."""
        # This test would require manually inserting orphaned chunks
        # For now, just test that the method doesn't error
        removed_count = self.document_store.cleanup_orphaned_chunks()
        assert isinstance(removed_count, int)
        assert removed_count >= 0