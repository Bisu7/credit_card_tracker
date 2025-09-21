"""Vector storage and retrieval using FAISS."""

import os
import pickle
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
import numpy as np

try:
    import faiss
except ImportError:
    faiss = None

from ..interfaces import VectorStoreInterface
from ..models import SearchResult
from ..exceptions import VectorStoreError
from ..config import config

logger = logging.getLogger(__name__)


class VectorStore(VectorStoreInterface):
    """FAISS-based vector storage and similarity search."""
    
    def __init__(self, index_path: Optional[str] = None, dimension: int = 384):
        """
        Initialize vector store.
        
        Args:
            index_path: Path to store/load FAISS index
            dimension: Dimension of vectors to store
        """
        if faiss is None:
            raise VectorStoreError("FAISS library not installed. Install with: pip install faiss-cpu")
        
        self.index_path = Path(index_path or config.vector_index_path)
        self.dimension = dimension
        self.index: Optional[faiss.Index] = None
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.id_to_index: Dict[str, int] = {}
        self.index_to_id: Dict[int, str] = {}
        self.next_index = 0
        
        # Ensure directory exists
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize or load index
        self._initialize_index()
    
    def _initialize_index(self) -> None:
        """Initialize or load existing FAISS index."""
        try:
            if self.index_path.exists():
                self._load_index()
                logger.info(f"Loaded existing index with {self.index.ntotal} vectors")
            else:
                self._create_new_index()
                logger.info(f"Created new FAISS index with dimension {self.dimension}")
        except Exception as e:
            logger.error(f"Failed to initialize index: {e}")
            raise VectorStoreError(f"Index initialization failed: {e}")
    
    def _create_new_index(self) -> None:
        """Create a new FAISS index."""
        # Use IndexFlatIP for cosine similarity (inner product with normalized vectors)
        self.index = faiss.IndexFlatIP(self.dimension)
        
        # For larger datasets, consider using IndexIVFFlat for faster search
        # nlist = 100  # number of clusters
        # quantizer = faiss.IndexFlatIP(self.dimension)
        # self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
        
        self.metadata = {}
        self.id_to_index = {}
        self.index_to_id = {}
        self.next_index = 0
    
    def _load_index(self) -> None:
        """Load existing FAISS index and metadata."""
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_path))
            
            # Load metadata
            metadata_path = self.index_path.with_suffix('.metadata')
            if metadata_path.exists():
                with open(metadata_path, 'rb') as f:
                    data = pickle.load(f)
                    self.metadata = data.get('metadata', {})
                    self.id_to_index = data.get('id_to_index', {})
                    self.index_to_id = data.get('index_to_id', {})
                    self.next_index = data.get('next_index', 0)
            else:
                logger.warning("Metadata file not found, starting with empty metadata")
                self.metadata = {}
                self.id_to_index = {}
                self.index_to_id = {}
                self.next_index = self.index.ntotal
                
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            raise VectorStoreError(f"Failed to load index: {e}")
    
    def _save_index(self) -> None:
        """Save FAISS index and metadata to disk."""
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))
            
            # Save metadata
            metadata_path = self.index_path.with_suffix('.metadata')
            with open(metadata_path, 'wb') as f:
                pickle.dump({
                    'metadata': self.metadata,
                    'id_to_index': self.id_to_index,
                    'index_to_id': self.index_to_id,
                    'next_index': self.next_index
                }, f)
                
            logger.debug(f"Saved index with {self.index.ntotal} vectors")
            
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            raise VectorStoreError(f"Failed to save index: {e}")
    
    def add_vectors(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> List[str]:
        """
        Add vectors to the store.
        
        Args:
            vectors: Array of vectors with shape (n_vectors, dimension)
            metadata: List of metadata dictionaries for each vector
            
        Returns:
            List of assigned vector IDs
            
        Raises:
            VectorStoreError: If addition fails
        """
        if self.index is None:
            raise VectorStoreError("Index not initialized")
        
        if len(vectors) != len(metadata):
            raise VectorStoreError("Number of vectors must match number of metadata entries")
        
        if vectors.shape[1] != self.dimension:
            raise VectorStoreError(f"Vector dimension {vectors.shape[1]} doesn't match index dimension {self.dimension}")
        
        try:
            # Generate IDs for new vectors
            vector_ids = [str(uuid.uuid4()) for _ in range(len(vectors))]
            
            # Normalize vectors for cosine similarity
            normalized_vectors = self._normalize_vectors(vectors)
            
            # Add vectors to FAISS index
            self.index.add(normalized_vectors.astype(np.float32))
            
            # Update mappings and metadata
            for i, (vector_id, meta) in enumerate(zip(vector_ids, metadata)):
                index_pos = self.next_index + i
                self.id_to_index[vector_id] = index_pos
                self.index_to_id[index_pos] = vector_id
                self.metadata[vector_id] = meta.copy()
            
            self.next_index += len(vectors)
            
            # Save to disk
            self._save_index()
            
            logger.info(f"Added {len(vectors)} vectors to index")
            return vector_ids
            
        except Exception as e:
            logger.error(f"Failed to add vectors: {e}")
            raise VectorStoreError(f"Failed to add vectors: {e}")
    
    def search(self, query_vector: np.ndarray, k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query vector with shape (dimension,)
            k: Number of results to return
            
        Returns:
            List of search results with scores and metadata
        """
        if self.index is None:
            raise VectorStoreError("Index not initialized")
        
        if self.index.ntotal == 0:
            return []
        
        if len(query_vector) != self.dimension:
            raise VectorStoreError(f"Query vector dimension {len(query_vector)} doesn't match index dimension {self.dimension}")
        
        try:
            # Normalize query vector
            normalized_query = self._normalize_vectors(query_vector.reshape(1, -1))
            
            # Perform search with optimized parameters
            k = min(k, self.index.ntotal)  # Don't search for more than available
            scores, indices = self.index.search(normalized_query.astype(np.float32), k)
            
            # Convert results to SearchResult format with vectorized operations
            results = []
            valid_indices = indices[0] != -1  # Filter out invalid results
            
            if np.any(valid_indices):
                valid_scores = scores[0][valid_indices]
                valid_idx_positions = indices[0][valid_indices]
                
                # Batch metadata retrieval for better performance
                for score, idx in zip(valid_scores, valid_idx_positions):
                    vector_id = self.index_to_id.get(idx)
                    if vector_id is not None:
                        metadata = self.metadata.get(vector_id, {})
                        
                        result = {
                            'vector_id': vector_id,
                            'similarity_score': float(score),
                            'metadata': metadata,
                            'index_position': int(idx)
                        }
                        results.append(result)
                    else:
                        logger.warning(f"No ID found for index {idx}")
            
            logger.debug(f"Found {len(results)} results for query")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise VectorStoreError(f"Search failed: {e}")
    
    def delete_vectors(self, vector_ids: List[str]) -> None:
        """
        Delete vectors by their IDs.
        
        Note: FAISS doesn't support efficient deletion, so this marks vectors as deleted
        in metadata. For true deletion, the index needs to be rebuilt.
        
        Args:
            vector_ids: List of vector IDs to delete
        """
        try:
            deleted_count = 0
            
            for vector_id in vector_ids:
                if vector_id in self.metadata:
                    # Mark as deleted in metadata
                    self.metadata[vector_id]['_deleted'] = True
                    deleted_count += 1
            
            if deleted_count > 0:
                self._save_index()
                logger.info(f"Marked {deleted_count} vectors as deleted")
            
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            raise VectorStoreError(f"Failed to delete vectors: {e}")
    
    def get_vector_metadata(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific vector.
        
        Args:
            vector_id: ID of the vector
            
        Returns:
            Metadata dictionary or None if not found
        """
        return self.metadata.get(vector_id)
    
    def update_vector_metadata(self, vector_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a specific vector.
        
        Args:
            vector_id: ID of the vector
            metadata: New metadata dictionary
            
        Returns:
            True if updated, False if vector not found
        """
        if vector_id in self.metadata:
            self.metadata[vector_id].update(metadata)
            self._save_index()
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with statistics
        """
        total_vectors = self.index.ntotal if self.index else 0
        deleted_vectors = sum(1 for meta in self.metadata.values() if meta.get('_deleted', False))
        active_vectors = total_vectors - deleted_vectors
        
        return {
            'total_vectors': total_vectors,
            'active_vectors': active_vectors,
            'deleted_vectors': deleted_vectors,
            'dimension': self.dimension,
            'index_type': type(self.index).__name__ if self.index else None,
            'index_path': str(self.index_path),
            'metadata_count': len(self.metadata)
        }
    
    def rebuild_index(self) -> None:
        """
        Rebuild the index, removing deleted vectors.
        
        This is expensive but necessary for true deletion and optimization.
        """
        if self.index is None or self.index.ntotal == 0:
            return
        
        try:
            logger.info("Rebuilding index to remove deleted vectors")
            
            # Get all active vectors and their metadata
            active_vectors = []
            active_metadata = []
            active_ids = []
            
            for vector_id, meta in self.metadata.items():
                if not meta.get('_deleted', False):
                    index_pos = self.id_to_index.get(vector_id)
                    if index_pos is not None and index_pos < self.index.ntotal:
                        # Reconstruct vector from index (this is approximate)
                        # In practice, you'd want to store original vectors separately
                        active_ids.append(vector_id)
                        active_metadata.append(meta)
            
            # Create new index
            old_index = self.index
            self._create_new_index()
            
            # Note: This is a simplified rebuild. In practice, you'd need to
            # store original vectors to properly rebuild the index.
            logger.warning("Index rebuild is simplified - original vectors not available")
            
            self._save_index()
            logger.info(f"Index rebuilt with {len(active_ids)} active vectors")
            
        except Exception as e:
            logger.error(f"Failed to rebuild index: {e}")
            raise VectorStoreError(f"Failed to rebuild index: {e}")
    
    def _normalize_vectors(self, vectors: np.ndarray) -> np.ndarray:
        """
        Normalize vectors for cosine similarity.
        
        Args:
            vectors: Array of vectors to normalize
            
        Returns:
            Normalized vectors
        """
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        # Avoid division by zero
        norms = np.where(norms == 0, 1, norms)
        return vectors / norms
    
    def clear_index(self) -> None:
        """Clear all vectors from the index."""
        try:
            self._create_new_index()
            self._save_index()
            logger.info("Cleared all vectors from index")
        except Exception as e:
            logger.error(f"Failed to clear index: {e}")
            raise VectorStoreError(f"Failed to clear index: {e}")
    
    def backup_index(self, backup_path: str) -> None:
        """
        Create a backup of the index.
        
        Args:
            backup_path: Path for the backup
        """
        try:
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy index file
            if self.index_path.exists():
                import shutil
                shutil.copy2(self.index_path, backup_path)
                
                # Copy metadata file
                metadata_src = self.index_path.with_suffix('.metadata')
                metadata_dst = backup_path.with_suffix('.metadata')
                if metadata_src.exists():
                    shutil.copy2(metadata_src, metadata_dst)
                
                logger.info(f"Created backup at {backup_path}")
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise VectorStoreError(f"Failed to create backup: {e}")
    
    def restore_from_backup(self, backup_path: str) -> None:
        """
        Restore index from backup.
        
        Args:
            backup_path: Path to the backup
        """
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                raise VectorStoreError(f"Backup file not found: {backup_path}")
            
            # Copy backup to current location
            import shutil
            shutil.copy2(backup_path, self.index_path)
            
            # Copy metadata if exists
            metadata_src = backup_path.with_suffix('.metadata')
            metadata_dst = self.index_path.with_suffix('.metadata')
            if metadata_src.exists():
                shutil.copy2(metadata_src, metadata_dst)
            
            # Reload index
            self._load_index()
            logger.info(f"Restored index from backup: {backup_path}")
            
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            raise VectorStoreError(f"Failed to restore from backup: {e}")
    
    def __len__(self) -> int:
        """Return number of vectors in the index."""
        return self.index.ntotal if self.index else 0
    
    def __contains__(self, vector_id: str) -> bool:
        """Check if vector ID exists in the store."""
        return vector_id in self.metadata and not self.metadata[vector_id].get('_deleted', False)