"""Tests for embedding components."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from deep_researcher.embeddings.generator import EmbeddingGenerator
from deep_researcher.embeddings.model_manager import ModelManager, ModelInfo
from deep_researcher.exceptions import EmbeddingGenerationError, ModelLoadError


class TestEmbeddingGenerator:
    """Test EmbeddingGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock SentenceTransformer to avoid loading actual models in tests
        self.mock_model = Mock()
        self.mock_model.get_sentence_embedding_dimension.return_value = 384
        self.mock_model.encode.return_value = np.random.rand(2, 384)
        
        with patch('deep_researcher.embeddings.generator.SentenceTransformer') as mock_st:
            mock_st.return_value = self.mock_model
            self.generator = EmbeddingGenerator(model_name="test-model")
    
    def test_initialization(self):
        """Test generator initialization."""
        assert self.generator.model_name == "test-model"
        assert self.generator.embedding_dimension == 384
        assert self.generator.model is not None
    
    def test_initialization_no_sentence_transformers(self):
        """Test initialization when sentence-transformers is not available."""
        with patch('deep_researcher.embeddings.generator.SentenceTransformer', None):
            with pytest.raises(ModelLoadError, match="sentence-transformers library not installed"):
                EmbeddingGenerator()
    
    def test_generate_embeddings_empty_list(self):
        """Test generating embeddings for empty list."""
        embeddings = self.generator.generate_embeddings([])
        assert embeddings.shape == (0, 384)
    
    def test_generate_embeddings_valid_texts(self):
        """Test generating embeddings for valid texts."""
        texts = ["Hello world", "Test sentence"]
        embeddings = self.generator.generate_embeddings(texts)
        
        assert embeddings.shape == (2, 384)
        assert isinstance(embeddings, np.ndarray)
        
        # Verify model.encode was called
        self.mock_model.encode.assert_called()
    
    def test_generate_embeddings_with_empty_texts(self):
        """Test generating embeddings with some empty texts."""
        texts = ["Hello world", "", "Test sentence", "   "]
        embeddings = self.generator.generate_embeddings(texts)
        
        assert embeddings.shape == (4, 384)
        # Empty texts should have zero embeddings
        assert np.allclose(embeddings[1], 0)
        assert np.allclose(embeddings[3], 0)
    
    def test_generate_single_embedding(self):
        """Test generating single embedding."""
        embedding = self.generator.generate_single_embedding("Test text")
        
        assert embedding.shape == (384,)
        assert isinstance(embedding, np.ndarray)
    
    def test_compute_similarity(self):
        """Test similarity computation."""
        emb1 = np.random.rand(384)
        emb2 = np.random.rand(384)
        
        similarity = self.generator.compute_similarity(emb1, emb2)
        
        assert isinstance(similarity, float)
        assert -1.0 <= similarity <= 1.0
    
    def test_compute_similarity_identical(self):
        """Test similarity of identical embeddings."""
        emb = np.random.rand(384)
        similarity = self.generator.compute_similarity(emb, emb)
        
        assert abs(similarity - 1.0) < 1e-6  # Should be very close to 1.0
    
    def test_compute_similarity_zero_vectors(self):
        """Test similarity with zero vectors."""
        emb1 = np.zeros(384)
        emb2 = np.random.rand(384)
        
        similarity = self.generator.compute_similarity(emb1, emb2)
        assert similarity == 0.0
    
    def test_compute_similarities_batch(self):
        """Test batch similarity computation."""
        query_emb = np.random.rand(384)
        doc_embs = np.random.rand(5, 384)
        
        similarities = self.generator.compute_similarities(query_emb, doc_embs)
        
        assert similarities.shape == (5,)
        assert all(-1.0 <= sim <= 1.0 for sim in similarities)
    
    def test_compute_similarities_empty(self):
        """Test batch similarity with empty document embeddings."""
        query_emb = np.random.rand(384)
        doc_embs = np.array([]).reshape(0, 384)
        
        similarities = self.generator.compute_similarities(query_emb, doc_embs)
        assert similarities.shape == (0,)
    
    def test_validate_embedding_valid(self):
        """Test validation of valid embedding."""
        embedding = np.random.rand(384)
        assert self.generator.validate_embedding(embedding) is True
    
    def test_validate_embedding_wrong_dimension(self):
        """Test validation of wrong dimension embedding."""
        embedding = np.random.rand(256)  # Wrong dimension
        assert self.generator.validate_embedding(embedding) is False
    
    def test_validate_embedding_not_array(self):
        """Test validation of non-array input."""
        assert self.generator.validate_embedding([1, 2, 3]) is False
    
    def test_validate_embedding_nan_values(self):
        """Test validation of embedding with NaN values."""
        embedding = np.random.rand(384)
        embedding[0] = np.nan
        assert self.generator.validate_embedding(embedding) is False
    
    def test_validate_embedding_all_zeros(self):
        """Test validation of all-zero embedding."""
        embedding = np.zeros(384)
        assert self.generator.validate_embedding(embedding) is False
    
    def test_get_embedding_stats(self):
        """Test embedding statistics computation."""
        embeddings = np.random.rand(10, 384)
        stats = self.generator.get_embedding_stats(embeddings)
        
        assert stats["count"] == 10
        assert stats["dimension"] == 384
        assert "mean_norm" in stats
        assert "std_norm" in stats
        assert "min_value" in stats
        assert "max_value" in stats
        assert stats["has_nan"] is False
        assert stats["has_inf"] is False
    
    def test_get_embedding_stats_empty(self):
        """Test statistics for empty embeddings."""
        embeddings = np.array([]).reshape(0, 384)
        stats = self.generator.get_embedding_stats(embeddings)
        
        assert stats["count"] == 0
    
    def test_get_model_info(self):
        """Test getting model information."""
        info = self.generator.get_model_info()
        
        assert info["model_loaded"] is True
        assert info["model_name"] == "test-model"
        assert info["embedding_dimension"] == 384
    
    def test_model_loading_failure(self):
        """Test handling of model loading failure."""
        with patch('deep_researcher.embeddings.generator.SentenceTransformer') as mock_st:
            mock_st.side_effect = Exception("Model loading failed")
            
            with pytest.raises(ModelLoadError, match="Failed to load embedding model"):
                EmbeddingGenerator(model_name="invalid-model")


class TestModelManager:
    """Test ModelManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('deep_researcher.embeddings.model_manager.EmbeddingGenerator'):
            self.manager = ModelManager()
    
    def test_initialization(self):
        """Test manager initialization."""
        assert self.manager.cache_dir.exists()
        assert isinstance(self.manager.AVAILABLE_MODELS, dict)
        assert len(self.manager.AVAILABLE_MODELS) > 0
    
    def test_list_available_models(self):
        """Test listing available models."""
        models = self.manager.list_available_models()
        
        assert len(models) > 0
        assert all(isinstance(model, ModelInfo) for model in models)
        assert any(model.name == "all-MiniLM-L6-v2" for model in models)
    
    def test_get_model_info(self):
        """Test getting model information."""
        info = self.manager.get_model_info("all-MiniLM-L6-v2")
        
        assert info is not None
        assert info["name"] == "all-MiniLM-L6-v2"
        assert info["dimension"] == 384
        assert "use_case" in info
        assert "is_cached" in info
        assert "is_loaded" in info
    
    def test_get_model_info_invalid(self):
        """Test getting info for invalid model."""
        info = self.manager.get_model_info("invalid-model")
        assert info is None
    
    def test_select_model_for_use_case(self):
        """Test model selection by use case."""
        model_name = self.manager._select_model_for_use_case("general")
        assert model_name == "all-MiniLM-L6-v2"
        
        model_name = self.manager._select_model_for_use_case("high_quality")
        assert model_name == "all-mpnet-base-v2"
        
        model_name = self.manager._select_model_for_use_case("multilingual")
        assert model_name == "paraphrase-multilingual-MiniLM-L12-v2"
    
    def test_select_model_invalid_use_case(self):
        """Test model selection with invalid use case."""
        model_name = self.manager._select_model_for_use_case("invalid_use_case")
        # Should fall back to default model
        assert model_name is not None
    
    @patch('deep_researcher.embeddings.model_manager.EmbeddingGenerator')
    def test_get_model_caching(self, mock_generator_class):
        """Test model caching behavior."""
        mock_generator = Mock()
        mock_generator.get_model_info.return_value = {
            "embedding_dimension": 384,
            "max_sequence_length": 256
        }
        mock_generator_class.return_value = mock_generator
        
        # First call should create new generator
        gen1 = self.manager.get_model("test-model")
        assert mock_generator_class.called
        
        # Second call should return cached generator
        mock_generator_class.reset_mock()
        gen2 = self.manager.get_model("test-model")
        assert not mock_generator_class.called
        assert gen1 is gen2
    
    def test_unload_model(self):
        """Test model unloading."""
        # Add a mock model to active generators
        mock_generator = Mock()
        self.manager.active_generators["test-model"] = mock_generator
        
        # Unload existing model
        result = self.manager.unload_model("test-model")
        assert result is True
        assert "test-model" not in self.manager.active_generators
        
        # Try to unload non-existent model
        result = self.manager.unload_model("non-existent")
        assert result is False
    
    def test_unload_all_models(self):
        """Test unloading all models."""
        # Add some mock models
        self.manager.active_generators["model1"] = Mock()
        self.manager.active_generators["model2"] = Mock()
        
        count = self.manager.unload_all_models()
        
        assert count == 2
        assert len(self.manager.active_generators) == 0
    
    def test_recommend_model(self):
        """Test model recommendation."""
        # Test different priorities
        assert self.manager.recommend_model({"priority": "speed"}) == "all-MiniLM-L6-v2"
        assert self.manager.recommend_model({"priority": "quality"}) == "all-mpnet-base-v2"
        assert self.manager.recommend_model({"priority": "multilingual"}) == "paraphrase-multilingual-MiniLM-L12-v2"
        assert self.manager.recommend_model({"priority": "balanced"}) == "all-MiniLM-L12-v2"
        assert self.manager.recommend_model({}) == "all-MiniLM-L12-v2"  # Default
    
    def test_get_status(self):
        """Test getting manager status."""
        status = self.manager.get_status()
        
        assert "cache_dir" in status
        assert "available_models" in status
        assert "cached_models" in status
        assert "loaded_models" in status
        assert "active_models" in status
        assert "memory_usage" in status
        
        assert status["available_models"] > 0
        assert isinstance(status["active_models"], list)
    
    @patch('deep_researcher.embeddings.model_manager.time.time')
    def test_cleanup_old_models(self, mock_time):
        """Test cleanup of old models."""
        # Set up mock time
        current_time = 1000000
        mock_time.return_value = current_time
        
        # Add models with different ages
        self.manager.active_generators["old_model"] = Mock()
        self.manager.active_generators["new_model"] = Mock()
        
        # Set metadata with different last_used times
        self.manager.model_metadata["old_model"] = {
            "last_used": current_time - 25 * 3600  # 25 hours ago
        }
        self.manager.model_metadata["new_model"] = {
            "last_used": current_time - 1 * 3600   # 1 hour ago
        }
        
        # Cleanup models older than 24 hours
        count = self.manager.cleanup_old_models(max_age_hours=24.0)
        
        assert count == 1
        assert "old_model" not in self.manager.active_generators
        assert "new_model" in self.manager.active_generators