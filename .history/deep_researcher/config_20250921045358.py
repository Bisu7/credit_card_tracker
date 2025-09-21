"""Configuration management for Deep Researcher Agent."""

import os
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class Config:
    """Main configuration class for the Deep Researcher Agent."""
    
    # Model settings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_model_cache_dir: str = "./models/embeddings"
    reasoning_model: str = "local"
    
    # Storage settings
    data_dir: str = "./data"
    vector_index_path: str = "./data/vector_index"
    document_db_path: str = "./data/documents.db"
    
    # Processing settings
    chunk_size: int = 512
    chunk_overlap: int = 50
    max_chunks_per_document: int = 1000
    
    # Retrieval settings
    default_k: int = 10
    similarity_threshold: float = 0.7
    max_reasoning_steps: int = 5
    search_batch_size: int = 100  # Batch vector searches
    enable_parallel_search: bool = True  # Parallel search processing
    
    # Performance settings
    batch_size: int = 64  # Increased for better GPU utilization
    max_memory_usage_gb: float = 4.0
    embedding_cache_size: int = 1000  # Cache frequently used embeddings
    enable_embedding_cache: bool = True
    
    # Export settings
    export_dir: str = "./exports"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            embedding_model_cache_dir=os.getenv("MODEL_CACHE_DIR", "./models/embeddings"),
            data_dir=os.getenv("DATA_DIR", "./data"),
            chunk_size=int(os.getenv("CHUNK_SIZE", "512")),
            batch_size=int(os.getenv("BATCH_SIZE", "32")),
        )
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.data_dir,
            self.embedding_model_cache_dir,
            self.export_dir,
            Path(self.vector_index_path).parent,
            Path(self.document_db_path).parent,
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)


# Global configuration instance
config = Config.from_env()