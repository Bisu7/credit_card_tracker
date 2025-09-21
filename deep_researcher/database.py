"""Database schema and utilities for Deep Researcher Agent."""

import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from .config import config
from .exceptions import DocumentStoreError


class DatabaseManager:
    """Manages SQLite database connections and schema."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager."""
        self.db_path = db_path or config.document_db_path
        self.ensure_database_exists()
    
    def ensure_database_exists(self) -> None:
        """Create database and tables if they don't exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with self.get_connection() as conn:
            self.create_tables(conn)
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise DocumentStoreError(f"Database error: {e}")
        finally:
            if conn:
                conn.close()
    
    def create_tables(self, conn: sqlite3.Connection) -> None:
        """Create database tables."""
        
        # Documents table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                source_path TEXT NOT NULL,
                format_type TEXT NOT NULL,
                metadata TEXT,  -- JSON string
                created_at TEXT NOT NULL,
                word_count INTEGER,
                chunk_count INTEGER,
                UNIQUE(content_hash)
            )
        """)
        
        # Chunks table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                content TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                metadata TEXT,  -- JSON string
                created_at TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE,
                UNIQUE(document_id, chunk_index)
            )
        """)
        
        # Embeddings table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id TEXT PRIMARY KEY,
                chunk_id TEXT NOT NULL,
                vector BLOB NOT NULL,
                model_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (chunk_id) REFERENCES chunks (id) ON DELETE CASCADE,
                UNIQUE(chunk_id, model_name)
            )
        """)
        
        # Research sessions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS research_sessions (
                id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                query_type TEXT NOT NULL,
                complexity_score REAL NOT NULL,
                metadata TEXT,  -- JSON string
                created_at TEXT NOT NULL
            )
        """)
        
        # Reasoning steps table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reasoning_steps (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                description TEXT NOT NULL,
                query TEXT NOT NULL,
                confidence REAL NOT NULL,
                results TEXT,  -- JSON string
                execution_time REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES research_sessions (id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for better performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents (created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_format_type ON documents (format_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks (document_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_content_hash ON chunks (content_hash)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings (chunk_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_model_name ON embeddings (model_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON research_sessions (created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_steps_session_id ON reasoning_steps (session_id)")
        
        conn.commit()
    
    def get_database_stats(self) -> dict:
        """Get database statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Count documents
            cursor.execute("SELECT COUNT(*) FROM documents")
            stats['document_count'] = cursor.fetchone()[0]
            
            # Count chunks
            cursor.execute("SELECT COUNT(*) FROM chunks")
            stats['chunk_count'] = cursor.fetchone()[0]
            
            # Count embeddings
            cursor.execute("SELECT COUNT(*) FROM embeddings")
            stats['embedding_count'] = cursor.fetchone()[0]
            
            # Count sessions
            cursor.execute("SELECT COUNT(*) FROM research_sessions")
            stats['session_count'] = cursor.fetchone()[0]
            
            # Database size
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            stats['database_size_bytes'] = cursor.fetchone()[0]
            
            return stats
    
    def cleanup_orphaned_data(self) -> None:
        """Clean up orphaned data in the database."""
        with self.get_connection() as conn:
            # Remove chunks without documents
            conn.execute("""
                DELETE FROM chunks 
                WHERE document_id NOT IN (SELECT id FROM documents)
            """)
            
            # Remove embeddings without chunks
            conn.execute("""
                DELETE FROM embeddings 
                WHERE chunk_id NOT IN (SELECT id FROM chunks)
            """)
            
            # Remove reasoning steps without sessions
            conn.execute("""
                DELETE FROM reasoning_steps 
                WHERE session_id NOT IN (SELECT id FROM research_sessions)
            """)
            
            conn.commit()


# Global database manager instance
db_manager = DatabaseManager()