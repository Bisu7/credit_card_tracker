"""Document storage and retrieval using SQLite."""

import json
import sqlite3
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from ..interfaces import DocumentStoreInterface
from ..models import Document, TextChunk, DocumentFormat
from ..exceptions import DocumentStoreError
from ..database import db_manager

logger = logging.getLogger(__name__)


class DocumentStore(DocumentStoreInterface):
    """SQLite-based document storage and retrieval."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize document store.
        
        Args:
            db_path: Path to SQLite database (uses default if None)
        """
        self.db_manager = db_manager if db_path is None else type(db_manager)(db_path)
        
        # Ensure database is initialized
        self.db_manager.ensure_database_exists()
    
    def store_document(self, document: Document) -> str:
        """
        Store a document and return its ID.
        
        Args:
            document: Document to store
            
        Returns:
            Document ID
            
        Raises:
            DocumentStoreError: If storage fails
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if document already exists (by content hash)
                cursor.execute(
                    "SELECT id FROM documents WHERE content_hash = ?",
                    (document.content_hash,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    logger.info(f"Document with same content already exists: {existing[0]}")
                    return existing[0]
                
                # Insert document
                cursor.execute("""
                    INSERT INTO documents (
                        id, title, content_hash, source_path, format_type,
                        metadata, created_at, word_count, chunk_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    document.id,
                    document.title,
                    document.content_hash,
                    document.source_path,
                    document.format_type.value,
                    json.dumps(document.metadata),
                    document.created_at.isoformat(),
                    document.word_count,
                    document.chunk_count
                ))
                
                # Store chunks if any
                for chunk in document.chunks:
                    self._store_chunk(cursor, chunk)
                
                conn.commit()
                logger.info(f"Stored document: {document.id}")
                return document.id
                
        except sqlite3.IntegrityError as e:
            logger.error(f"Document storage integrity error: {e}")
            raise DocumentStoreError(f"Document already exists or constraint violation: {e}")
        except Exception as e:
            logger.error(f"Failed to store document: {e}")
            raise DocumentStoreError(f"Failed to store document: {e}")
    
    def _store_chunk(self, cursor: sqlite3.Cursor, chunk: TextChunk) -> None:
        """Store a text chunk."""
        cursor.execute("""
            INSERT OR REPLACE INTO chunks (
                id, document_id, content, chunk_index, content_hash,
                metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            chunk.id,
            chunk.document_id,
            chunk.content,
            chunk.chunk_index,
            chunk.content_hash,
            json.dumps(chunk.metadata),
            chunk.created_at.isoformat()
        ))
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Retrieve a document by ID.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Document object or None if not found
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get document metadata
                cursor.execute("""
                    SELECT id, title, source_path, format_type, metadata, created_at
                    FROM documents WHERE id = ?
                """, (document_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Get document content (stored separately for efficiency)
                content = self._get_document_content(cursor, document_id)
                
                # Create document object
                document = Document(
                    id=row[0],
                    title=row[1],
                    content=content,
                    source_path=row[2],
                    format_type=DocumentFormat(row[3]),
                    metadata=json.loads(row[4]) if row[4] else {},
                    created_at=datetime.fromisoformat(row[5])
                )
                
                # Load chunks
                document.chunks = self._get_document_chunks(cursor, document_id)
                
                return document
                
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            raise DocumentStoreError(f"Failed to get document: {e}")
    
    def _get_document_content(self, cursor: sqlite3.Cursor, document_id: str) -> str:
        """Get full document content by combining chunks."""
        cursor.execute("""
            SELECT content FROM chunks 
            WHERE document_id = ? 
            ORDER BY chunk_index
        """, (document_id,))
        
        chunks = cursor.fetchall()
        return "\n\n".join(chunk[0] for chunk in chunks)
    
    def _get_document_chunks(self, cursor: sqlite3.Cursor, document_id: str) -> List[TextChunk]:
        """Get all chunks for a document."""
        cursor.execute("""
            SELECT id, content, chunk_index, metadata, created_at
            FROM chunks 
            WHERE document_id = ? 
            ORDER BY chunk_index
        """, (document_id,))
        
        chunks = []
        for row in cursor.fetchall():
            chunk = TextChunk(
                id=row[0],
                content=row[1],
                document_id=document_id,
                chunk_index=row[2],
                metadata=json.loads(row[3]) if row[3] else {},
                created_at=datetime.fromisoformat(row[4])
            )
            chunks.append(chunk)
        
        return chunks
    
    def search_documents(self, query: str, filters: Dict[str, Any] = None) -> List[Document]:
        """
        Search documents by metadata or content.
        
        Args:
            query: Search query
            filters: Optional filters (format_type, date_range, etc.)
            
        Returns:
            List of matching documents
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build search query
                sql_parts = ["SELECT DISTINCT d.id FROM documents d"]
                params = []
                where_conditions = []
                
                # Text search in title and chunks
                if query.strip():
                    sql_parts.append("LEFT JOIN chunks c ON d.id = c.document_id")
                    where_conditions.append("(d.title LIKE ? OR c.content LIKE ?)")
                    search_term = f"%{query}%"
                    params.extend([search_term, search_term])
                
                # Apply filters
                if filters:
                    if 'format_type' in filters:
                        where_conditions.append("d.format_type = ?")
                        params.append(filters['format_type'])
                    
                    if 'date_from' in filters:
                        where_conditions.append("d.created_at >= ?")
                        params.append(filters['date_from'])
                    
                    if 'date_to' in filters:
                        where_conditions.append("d.created_at <= ?")
                        params.append(filters['date_to'])
                
                # Combine query
                if where_conditions:
                    sql_parts.append("WHERE " + " AND ".join(where_conditions))
                
                sql_parts.append("ORDER BY d.created_at DESC")
                
                # Add limit if specified
                limit = filters.get('limit', 100) if filters else 100
                sql_parts.append(f"LIMIT {limit}")
                
                sql = " ".join(sql_parts)
                cursor.execute(sql, params)
                
                # Get document IDs and load full documents
                document_ids = [row[0] for row in cursor.fetchall()]
                documents = []
                
                for doc_id in document_ids:
                    doc = self.get_document(doc_id)
                    if doc:
                        documents.append(doc)
                
                logger.info(f"Found {len(documents)} documents for query: {query}")
                return documents
                
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            raise DocumentStoreError(f"Document search failed: {e}")
    
    def delete_document(self, document_id: str) -> None:
        """
        Delete a document by ID.
        
        Args:
            document_id: ID of the document to delete
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete chunks first (foreign key constraint)
                cursor.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
                
                # Delete document
                cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Deleted document: {document_id}")
                else:
                    logger.warning(f"Document not found for deletion: {document_id}")
                
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise DocumentStoreError(f"Failed to delete document: {e}")
    
    def get_chunk(self, chunk_id: str) -> Optional[TextChunk]:
        """
        Get a specific chunk by ID.
        
        Args:
            chunk_id: ID of the chunk
            
        Returns:
            TextChunk object or None if not found
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, document_id, content, chunk_index, metadata, created_at
                    FROM chunks WHERE id = ?
                """, (chunk_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return TextChunk(
                    id=row[0],
                    content=row[2],
                    document_id=row[1],
                    chunk_index=row[3],
                    metadata=json.loads(row[4]) if row[4] else {},
                    created_at=datetime.fromisoformat(row[5])
                )
                
        except Exception as e:
            logger.error(f"Failed to get chunk {chunk_id}: {e}")
            return None
    
    def get_chunks_by_document(self, document_id: str) -> List[TextChunk]:
        """
        Get all chunks for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            List of TextChunk objects
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                return self._get_document_chunks(cursor, document_id)
                
        except Exception as e:
            logger.error(f"Failed to get chunks for document {document_id}: {e}")
            return []
    
    def update_document_metadata(self, document_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update document metadata.
        
        Args:
            document_id: ID of the document
            metadata: New metadata dictionary
            
        Returns:
            True if updated, False if document not found
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE documents SET metadata = ? WHERE id = ?
                """, (json.dumps(metadata), document_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Updated metadata for document: {document_id}")
                    return True
                else:
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to update document metadata: {e}")
            raise DocumentStoreError(f"Failed to update document metadata: {e}")
    
    def list_documents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List documents with basic information.
        
        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List of document information dictionaries
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, title, source_path, format_type, created_at, 
                           word_count, chunk_count
                    FROM documents 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                documents = []
                for row in cursor.fetchall():
                    documents.append({
                        'id': row[0],
                        'title': row[1],
                        'source_path': row[2],
                        'format_type': row[3],
                        'created_at': row[4],
                        'word_count': row[5],
                        'chunk_count': row[6]
                    })
                
                return documents
                
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            raise DocumentStoreError(f"Failed to list documents: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Document statistics
                cursor.execute("SELECT COUNT(*) FROM documents")
                doc_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM chunks")
                chunk_count = cursor.fetchone()[0]
                
                # Format distribution
                cursor.execute("""
                    SELECT format_type, COUNT(*) 
                    FROM documents 
                    GROUP BY format_type
                """)
                format_dist = dict(cursor.fetchall())
                
                # Size statistics
                cursor.execute("""
                    SELECT AVG(word_count), MIN(word_count), MAX(word_count)
                    FROM documents
                """)
                word_stats = cursor.fetchone()
                
                cursor.execute("""
                    SELECT AVG(chunk_count), MIN(chunk_count), MAX(chunk_count)
                    FROM documents
                """)
                chunk_stats = cursor.fetchone()
                
                return {
                    'total_documents': doc_count,
                    'total_chunks': chunk_count,
                    'format_distribution': format_dist,
                    'word_count_stats': {
                        'average': word_stats[0] or 0,
                        'minimum': word_stats[1] or 0,
                        'maximum': word_stats[2] or 0
                    },
                    'chunk_count_stats': {
                        'average': chunk_stats[0] or 0,
                        'minimum': chunk_stats[1] or 0,
                        'maximum': chunk_stats[2] or 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {'error': str(e)}
    
    def cleanup_orphaned_chunks(self) -> int:
        """
        Remove chunks that don't have corresponding documents.
        
        Returns:
            Number of orphaned chunks removed
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM chunks 
                    WHERE document_id NOT IN (SELECT id FROM documents)
                """)
                
                removed_count = cursor.rowcount
                conn.commit()
                
                if removed_count > 0:
                    logger.info(f"Removed {removed_count} orphaned chunks")
                
                return removed_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned chunks: {e}")
            raise DocumentStoreError(f"Failed to cleanup orphaned chunks: {e}")
    
    def export_documents(self, output_path: str, format_type: str = 'json') -> None:
        """
        Export all documents to a file.
        
        Args:
            output_path: Path for the export file
            format_type: Export format ('json' or 'csv')
        """
        try:
            documents = self.list_documents(limit=10000)  # Get all documents
            
            if format_type.lower() == 'json':
                import json
                with open(output_path, 'w') as f:
                    json.dump(documents, f, indent=2, default=str)
            elif format_type.lower() == 'csv':
                import csv
                if documents:
                    with open(output_path, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=documents[0].keys())
                        writer.writeheader()
                        writer.writerows(documents)
            else:
                raise DocumentStoreError(f"Unsupported export format: {format_type}")
            
            logger.info(f"Exported {len(documents)} documents to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export documents: {e}")
            raise DocumentStoreError(f"Failed to export documents: {e}")
    
    def vacuum_database(self) -> None:
        """Optimize database by running VACUUM command."""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute("VACUUM")
                logger.info("Database vacuum completed")
                
        except Exception as e:
            logger.error(f"Failed to vacuum database: {e}")
            raise DocumentStoreError(f"Failed to vacuum database: {e}")