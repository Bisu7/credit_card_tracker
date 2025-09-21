"""Embedding generation using local models."""

import numpy as np
from typing import List, Optional, Union, Dict, Any
import logging
from pathlib import Path
import time
import hashlib
from functools import lru_cache

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from ..interfaces import EmbeddingGeneratorInterface
from ..exceptions import EmbeddingGenerationError, ModelLoadError
from ..config import config

logger = logging.getLogger(__name__)


class EmbeddingGenerator(EmbeddingGeneratorInterface):
    """Generates embeddings using local sentence transformer models."""
    
    def __init__(self, model_name: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize embedding generator.
        
        Args:
            model_name: Name of the sentence transformer model to use
            cache_dir: Directory to cache downloaded models
        """
        if SentenceTransformer is None:
            raise ModelLoadError("sentence-transformers library not installed. Install with: pip install sentence-transformers")
        
        self.model_name = model_name or config.embedding_model
        self.cache_dir = cache_dir or config.embedding_model_cache_dir
        self.model: Optional[SentenceTransformer] = None
        self.embedding_dimension: Optional[int] = None
        
        # Embedding cache for frequently used texts
        self.embedding_cache: Dict[str, np.ndarray] = {}
        self.cache_enabled = config.enable_embedding_cache
        self.max_cache_size = config.embedding_cache_size
        
        # Ensure cache directory exists
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        
        # Load model on initialization
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the sentence transformer model."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            start_time = time.time()
            
            self.model = SentenceTransformer(
                self.model_name,
                cache_folder=self.cache_dir
            )
            
            # Get embedding dimension
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            
            load_time = time.time() - start_time
            logger.info(f"Model loaded successfully in {load_time:.2f}s. Embedding dimension: {self.embedding_dimension}")
            
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            raise ModelLoadError(f"Failed to load embedding model {self.model_name}: {e}")
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts with caching support.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            NumPy array of embeddings with shape (len(texts), embedding_dim)
            
        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        if not texts:
            return np.array([]).reshape(0, self.embedding_dimension or 384)
        
        if self.model is None:
            raise EmbeddingGenerationError("Model not loaded")
        
        try:
            # Filter out empty texts and check cache
            valid_texts = []
            valid_indices = []
            cached_embeddings = []
            texts_to_generate = []
            cache_indices = []
            
            for i, text in enumerate(texts):
                if text and text.strip():
                    text = text.strip()
                    valid_texts.append(text)
                    valid_indices.append(i)
                    
                    # Check cache if enabled
                    if self.cache_enabled:
                        text_hash = hashlib.md5(text.encode()).hexdigest()
                        if text_hash in self.embedding_cache:
                            cached_embeddings.append(self.embedding_cache[text_hash])
                            cache_indices.append(len(cached_embeddings) - 1)
                        else:
                            texts_to_generate.append(text)
                            cache_indices.append(None)
                    else:
                        texts_to_generate.append(text)
                        cache_indices.append(None)
            
            if not valid_texts:
                # Return zero embeddings for empty texts
                return np.zeros((len(texts), self.embedding_dimension))
            
            logger.debug(f"Generating embeddings for {len(texts_to_generate)} new texts, {len(cached_embeddings)} from cache")
            start_time = time.time()
            
            # Generate embeddings for new texts
            if texts_to_generate:
                batch_size = config.batch_size
                all_embeddings = []
                
                for i in range(0, len(texts_to_generate), batch_size):
                    batch_texts = texts_to_generate[i:i + batch_size]
                    batch_embeddings = self.model.encode(
                        batch_texts,
                        convert_to_numpy=True,
                        show_progress_bar=False,
                        normalize_embeddings=True  # Normalize for better similarity search
                    )
                    all_embeddings.append(batch_embeddings)
                
                # Combine all batch embeddings
                if all_embeddings:
                    new_embeddings = np.vstack(all_embeddings)
                else:
                    new_embeddings = np.array([]).reshape(0, self.embedding_dimension)
                
                # Cache new embeddings
                if self.cache_enabled:
                    for i, text in enumerate(texts_to_generate):
                        text_hash = hashlib.md5(text.encode()).hexdigest()
                        self.embedding_cache[text_hash] = new_embeddings[i]
                        
                        # Limit cache size
                        if len(self.embedding_cache) > self.max_cache_size:
                            # Remove oldest entries (simple LRU)
                            oldest_key = next(iter(self.embedding_cache))
                            del self.embedding_cache[oldest_key]
            else:
                new_embeddings = np.array([]).reshape(0, self.embedding_dimension)
            
            # Combine cached and new embeddings
            valid_embeddings = []
            new_idx = 0
            cache_idx = 0
            
            for i, cache_idx_val in enumerate(cache_indices):
                if cache_idx_val is not None:
                    valid_embeddings.append(cached_embeddings[cache_idx_val])
                else:
                    valid_embeddings.append(new_embeddings[new_idx])
                    new_idx += 1
            
            if valid_embeddings:
                valid_embeddings = np.vstack(valid_embeddings)
            else:
                valid_embeddings = np.array([]).reshape(0, self.embedding_dimension)
            
            # Create full embedding array with zeros for empty texts
            full_embeddings = np.zeros((len(texts), self.embedding_dimension))
            full_embeddings[valid_indices] = valid_embeddings
            
            generation_time = time.time() - start_time
            logger.debug(f"Generated {len(texts)} embeddings in {generation_time:.2f}s (cache hit rate: {len(cached_embeddings)/len(valid_texts)*100:.1f}%)")
            
            return full_embeddings
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise EmbeddingGenerationError(f"Failed to generate embeddings: {e}")
    
    def generate_single_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text string to embed
            
        Returns:
            NumPy array embedding with shape (embedding_dim,)
        """
        embeddings = self.generate_embeddings([text])
        return embeddings[0]
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        if self.model is None:
            return {"model_loaded": False}
        
        return {
            "model_loaded": True,
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dimension,
            "max_sequence_length": getattr(self.model, 'max_seq_length', 'unknown'),
            "cache_dir": self.cache_dir
        }
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        try:
            # Ensure embeddings are normalized
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Compute cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            
            # Clamp to valid range due to floating point precision
            return float(np.clip(similarity, -1.0, 1.0))
            
        except Exception as e:
            logger.error(f"Similarity computation failed: {e}")
            return 0.0
    
    def compute_similarities(self, query_embedding: np.ndarray, 
                           document_embeddings: np.ndarray) -> np.ndarray:
        """
        Compute similarities between a query embedding and multiple document embeddings.
        
        Args:
            query_embedding: Query embedding vector with shape (embedding_dim,)
            document_embeddings: Document embeddings with shape (n_docs, embedding_dim)
            
        Returns:
            Array of similarity scores with shape (n_docs,)
        """
        try:
            if document_embeddings.size == 0:
                return np.array([])
            
            # Ensure query embedding is 2D for matrix operations
            if query_embedding.ndim == 1:
                query_embedding = query_embedding.reshape(1, -1)
            
            # Normalize embeddings
            query_norm = np.linalg.norm(query_embedding, axis=1, keepdims=True)
            doc_norms = np.linalg.norm(document_embeddings, axis=1, keepdims=True)
            
            # Avoid division by zero
            query_norm = np.where(query_norm == 0, 1, query_norm)
            doc_norms = np.where(doc_norms == 0, 1, doc_norms)
            
            query_normalized = query_embedding / query_norm
            docs_normalized = document_embeddings / doc_norms
            
            # Compute cosine similarities
            similarities = np.dot(query_normalized, docs_normalized.T).flatten()
            
            # Clamp to valid range
            return np.clip(similarities, -1.0, 1.0)
            
        except Exception as e:
            logger.error(f"Batch similarity computation failed: {e}")
            return np.zeros(len(document_embeddings))
    
    def validate_embedding(self, embedding: np.ndarray) -> bool:
        """
        Validate that an embedding has the correct shape and properties.
        
        Args:
            embedding: Embedding to validate
            
        Returns:
            True if embedding is valid, False otherwise
        """
        try:
            # Check if it's a numpy array
            if not isinstance(embedding, np.ndarray):
                return False
            
            # Check dimension
            if embedding.ndim != 1:
                return False
            
            # Check size matches model dimension
            if len(embedding) != self.embedding_dimension:
                return False
            
            # Check for NaN or infinite values
            if not np.isfinite(embedding).all():
                return False
            
            # Check if it's not all zeros (which might indicate an error)
            if np.allclose(embedding, 0):
                logger.warning("Embedding is all zeros")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Embedding validation failed: {e}")
            return False
    
    def get_embedding_stats(self, embeddings: np.ndarray) -> Dict[str, Any]:
        """
        Get statistics about a set of embeddings.
        
        Args:
            embeddings: Array of embeddings with shape (n_embeddings, embedding_dim)
            
        Returns:
            Dictionary with embedding statistics
        """
        try:
            if embeddings.size == 0:
                return {"count": 0}
            
            return {
                "count": len(embeddings),
                "dimension": embeddings.shape[1] if embeddings.ndim > 1 else len(embeddings),
                "mean_norm": float(np.mean(np.linalg.norm(embeddings, axis=-1))),
                "std_norm": float(np.std(np.linalg.norm(embeddings, axis=-1))),
                "min_value": float(np.min(embeddings)),
                "max_value": float(np.max(embeddings)),
                "mean_value": float(np.mean(embeddings)),
                "has_nan": bool(np.isnan(embeddings).any()),
                "has_inf": bool(np.isinf(embeddings).any())
            }
            
        except Exception as e:
            logger.error(f"Failed to compute embedding stats: {e}")
            return {"error": str(e)}
    
    def reload_model(self, model_name: Optional[str] = None) -> None:
        """
        Reload the model, optionally with a different model name.
        
        Args:
            model_name: New model name to load (optional)
        """
        if model_name:
            self.model_name = model_name
        
        logger.info(f"Reloading model: {self.model_name}")
        self.model = None
        self.embedding_dimension = None
        self._load_model()
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        if hasattr(self, 'model') and self.model is not None:
            # Clean up model resources if needed
            self.model = None