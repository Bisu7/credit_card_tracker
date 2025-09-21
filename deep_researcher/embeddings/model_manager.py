"""Model management for embedding generators."""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from dataclasses import dataclass, asdict

from .generator import EmbeddingGenerator
from ..exceptions import ModelLoadError, ConfigurationError
from ..config import config

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about an embedding model."""
    name: str
    dimension: int
    max_sequence_length: int
    description: str
    use_case: str
    performance_score: float = 0.0
    memory_usage_mb: float = 0.0
    load_time_seconds: float = 0.0
    last_used: Optional[str] = None


class ModelManager:
    """Manages embedding models and their lifecycle."""
    
    # Predefined model configurations
    AVAILABLE_MODELS = {
        "all-MiniLM-L6-v2": ModelInfo(
            name="all-MiniLM-L6-v2",
            dimension=384,
            max_sequence_length=256,
            description="Fast and efficient model for general purpose embeddings",
            use_case="general",
            performance_score=0.8
        ),
        "all-mpnet-base-v2": ModelInfo(
            name="all-mpnet-base-v2", 
            dimension=768,
            max_sequence_length=384,
            description="High quality model with better performance",
            use_case="high_quality",
            performance_score=0.9
        ),
        "all-MiniLM-L12-v2": ModelInfo(
            name="all-MiniLM-L12-v2",
            dimension=384,
            max_sequence_length=256,
            description="Balanced model between speed and quality",
            use_case="balanced",
            performance_score=0.85
        ),
        "paraphrase-multilingual-MiniLM-L12-v2": ModelInfo(
            name="paraphrase-multilingual-MiniLM-L12-v2",
            dimension=384,
            max_sequence_length=128,
            description="Multilingual model for non-English content",
            use_case="multilingual",
            performance_score=0.75
        )
    }
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize model manager.
        
        Args:
            cache_dir: Directory to cache models and metadata
        """
        self.cache_dir = Path(cache_dir or config.embedding_model_cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.cache_dir / "model_metadata.json"
        self.active_generators: Dict[str, EmbeddingGenerator] = {}
        self.model_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Load existing metadata
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Load model metadata from cache."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    self.model_metadata = json.load(f)
                logger.info(f"Loaded metadata for {len(self.model_metadata)} models")
            else:
                self.model_metadata = {}
        except Exception as e:
            logger.warning(f"Failed to load model metadata: {e}")
            self.model_metadata = {}
    
    def _save_metadata(self) -> None:
        """Save model metadata to cache."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.model_metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save model metadata: {e}")
    
    def get_model(self, model_name: Optional[str] = None, use_case: Optional[str] = None) -> EmbeddingGenerator:
        """
        Get an embedding generator for the specified model.
        
        Args:
            model_name: Specific model name to load
            use_case: Use case to select appropriate model (if model_name not provided)
            
        Returns:
            EmbeddingGenerator instance
            
        Raises:
            ModelLoadError: If model loading fails
        """
        # Determine which model to use
        if model_name is None:
            model_name = self._select_model_for_use_case(use_case)
        
        # Check if model is already loaded
        if model_name in self.active_generators:
            logger.debug(f"Returning cached model: {model_name}")
            self._update_last_used(model_name)
            return self.active_generators[model_name]
        
        # Load new model
        try:
            logger.info(f"Loading new model: {model_name}")
            start_time = time.time()
            
            generator = EmbeddingGenerator(
                model_name=model_name,
                cache_dir=str(self.cache_dir)
            )
            
            load_time = time.time() - start_time
            
            # Cache the generator
            self.active_generators[model_name] = generator
            
            # Update metadata
            self._update_model_metadata(model_name, generator, load_time)
            
            logger.info(f"Successfully loaded model {model_name} in {load_time:.2f}s")
            return generator
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise ModelLoadError(f"Failed to load model {model_name}: {e}")
    
    def _select_model_for_use_case(self, use_case: Optional[str]) -> str:
        """
        Select appropriate model based on use case.
        
        Args:
            use_case: Desired use case
            
        Returns:
            Model name to use
        """
        if use_case is None:
            return config.embedding_model
        
        # Find model matching use case
        for model_name, model_info in self.AVAILABLE_MODELS.items():
            if model_info.use_case == use_case:
                return model_name
        
        # Fallback to default model
        logger.warning(f"No model found for use case '{use_case}', using default")
        return config.embedding_model
    
    def _update_model_metadata(self, model_name: str, generator: EmbeddingGenerator, load_time: float) -> None:
        """Update metadata for a model."""
        model_info = generator.get_model_info()
        
        self.model_metadata[model_name] = {
            "name": model_name,
            "dimension": model_info.get("embedding_dimension"),
            "max_sequence_length": model_info.get("max_sequence_length"),
            "load_time_seconds": load_time,
            "last_used": time.time(),
            "cache_dir": str(self.cache_dir)
        }
        
        self._save_metadata()
    
    def _update_last_used(self, model_name: str) -> None:
        """Update last used timestamp for a model."""
        if model_name in self.model_metadata:
            self.model_metadata[model_name]["last_used"] = time.time()
            self._save_metadata()
    
    def list_available_models(self) -> List[ModelInfo]:
        """
        List all available models.
        
        Returns:
            List of ModelInfo objects
        """
        return list(self.AVAILABLE_MODELS.values())
    
    def list_cached_models(self) -> List[str]:
        """
        List models that are cached locally.
        
        Returns:
            List of cached model names
        """
        cached_models = []
        
        # Check for model directories in cache
        if self.cache_dir.exists():
            for item in self.cache_dir.iterdir():
                if item.is_dir() and item.name in self.AVAILABLE_MODELS:
                    cached_models.append(item.name)
        
        return cached_models
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model information dictionary or None if not found
        """
        # Check predefined models
        if model_name in self.AVAILABLE_MODELS:
            model_info = asdict(self.AVAILABLE_MODELS[model_name])
            
            # Add runtime metadata if available
            if model_name in self.model_metadata:
                model_info.update(self.model_metadata[model_name])
            
            # Add cache status
            model_info["is_cached"] = model_name in self.list_cached_models()
            model_info["is_loaded"] = model_name in self.active_generators
            
            return model_info
        
        return None
    
    def unload_model(self, model_name: str) -> bool:
        """
        Unload a model from memory.
        
        Args:
            model_name: Name of the model to unload
            
        Returns:
            True if model was unloaded, False if not loaded
        """
        if model_name in self.active_generators:
            del self.active_generators[model_name]
            logger.info(f"Unloaded model: {model_name}")
            return True
        
        return False
    
    def unload_all_models(self) -> int:
        """
        Unload all models from memory.
        
        Returns:
            Number of models unloaded
        """
        count = len(self.active_generators)
        self.active_generators.clear()
        logger.info(f"Unloaded {count} models")
        return count
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get memory usage information for loaded models.
        
        Returns:
            Dictionary with memory usage stats
        """
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            "total_memory_mb": memory_info.rss / 1024 / 1024,
            "loaded_models": list(self.active_generators.keys()),
            "model_count": len(self.active_generators)
        }
    
    def cleanup_old_models(self, max_age_hours: float = 24.0) -> int:
        """
        Cleanup models that haven't been used recently.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
            
        Returns:
            Number of models cleaned up
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        models_to_remove = []
        
        for model_name in self.active_generators:
            if model_name in self.model_metadata:
                last_used = self.model_metadata[model_name].get("last_used", 0)
                age = current_time - last_used
                
                if age > max_age_seconds:
                    models_to_remove.append(model_name)
        
        # Remove old models
        for model_name in models_to_remove:
            self.unload_model(model_name)
        
        if models_to_remove:
            logger.info(f"Cleaned up {len(models_to_remove)} old models: {models_to_remove}")
        
        return len(models_to_remove)
    
    def benchmark_model(self, model_name: str, test_texts: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Benchmark a model's performance.
        
        Args:
            model_name: Name of the model to benchmark
            test_texts: Optional test texts (uses default if not provided)
            
        Returns:
            Benchmark results
        """
        if test_texts is None:
            test_texts = [
                "This is a short test sentence.",
                "This is a longer test sentence with more words to evaluate performance.",
                "Machine learning is a subset of artificial intelligence that focuses on algorithms.",
                "Natural language processing enables computers to understand human language.",
                "Deep learning uses neural networks with multiple layers to learn complex patterns."
            ]
        
        try:
            generator = self.get_model(model_name)
            
            # Benchmark embedding generation
            start_time = time.time()
            embeddings = generator.generate_embeddings(test_texts)
            generation_time = time.time() - start_time
            
            # Benchmark similarity computation
            start_time = time.time()
            similarities = generator.compute_similarities(embeddings[0], embeddings[1:])
            similarity_time = time.time() - start_time
            
            return {
                "model_name": model_name,
                "test_text_count": len(test_texts),
                "embedding_generation_time": generation_time,
                "similarity_computation_time": similarity_time,
                "embeddings_per_second": len(test_texts) / generation_time,
                "embedding_dimension": len(embeddings[0]),
                "average_similarity": float(similarities.mean()) if len(similarities) > 0 else 0.0
            }
            
        except Exception as e:
            logger.error(f"Benchmark failed for model {model_name}: {e}")
            return {"error": str(e)}
    
    def recommend_model(self, requirements: Dict[str, Any]) -> str:
        """
        Recommend a model based on requirements.
        
        Args:
            requirements: Dictionary with requirements like 'speed', 'quality', 'memory'
            
        Returns:
            Recommended model name
        """
        priority = requirements.get("priority", "balanced")
        
        if priority == "speed":
            return "all-MiniLM-L6-v2"
        elif priority == "quality":
            return "all-mpnet-base-v2"
        elif priority == "multilingual":
            return "paraphrase-multilingual-MiniLM-L12-v2"
        else:  # balanced
            return "all-MiniLM-L12-v2"
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get overall status of the model manager.
        
        Returns:
            Status information
        """
        return {
            "cache_dir": str(self.cache_dir),
            "available_models": len(self.AVAILABLE_MODELS),
            "cached_models": len(self.list_cached_models()),
            "loaded_models": len(self.active_generators),
            "active_models": list(self.active_generators.keys()),
            "memory_usage": self.get_memory_usage()
        }