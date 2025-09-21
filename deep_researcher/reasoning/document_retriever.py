"""Document retrieval using semantic search and ranking."""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

from ..models import Document, TextChunk, SearchResult
from ..interfaces import DocumentRetrieverInterface
from ..storage.vector_store import VectorStore
from ..storage.document_store import DocumentStore
from ..embeddings.generator import EmbeddingGenerator
from ..exceptions import RetrievalError
from ..config import config

logger = logging.getLogger(__name__)


class RetrievalStrategy(Enum):
    """Different retrieval strategies."""
    SEMANTIC_ONLY = "semantic_only"
    KEYWORD_ONLY = "keyword_only"
    HYBRID = "hybrid"
    RERANK = "rerank"


@dataclass
class RetrievalConfig:
    """Configuration for document retrieval."""
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    max_results: int = 10
    similarity_threshold: float = 0.7
    keyword_weight: float = 0.3
    semantic_weight: float = 0.7
    diversity_factor: float = 0.1
    rerank_top_k: int = 50


class DocumentRetriever(DocumentRetrieverInterface):
    """Retrieves relevant documents using semantic search and ranking."""
    
    def __init__(self, 
                 vector_store: VectorStore,
                 document_store: DocumentStore,
                 embedding_generator: EmbeddingGenerator,
                 config: Optional[RetrievalConfig] = None):
        """
        Initialize document retriever.
        
        Args:
            vector_store: Vector store for similarity search
            document_store: Document store for metadata and content
            embedding_generator: Generator for query embeddings
            config: Retrieval configuration
        """
        self.vector_store = vector_store
        self.document_store = document_store
        self.embedding_generator = embedding_generator
        self.config = config or RetrievalConfig()
        
        # Cache for query embeddings
        self._query_embedding_cache: Dict[str, np.ndarray] = {}
    
    def retrieve_documents(self, 
                          query_embedding: np.ndarray, 
                          k: int = 10,
                          filters: Dict[str, Any] = None) -> List[Document]:
        """
        Retrieve relevant documents for a query embedding.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of documents to retrieve
            filters: Optional filters for retrieval
            
        Returns:
            List of relevant documents
        """
        try:
            logger.info(f"Retrieving documents with k={k}, strategy={self.config.strategy.value}")
            
            # Get search results from vector store
            search_results = self.vector_store.search(
                query_embedding, 
                k=min(k * 3, self.config.rerank_top_k)  # Get more for reranking
            )
            
            if not search_results:
                logger.warning("No search results found")
                return []
            
            # Filter by similarity threshold
            filtered_results = [
                result for result in search_results 
                if result['similarity_score'] >= self.config.similarity_threshold
            ]
            
            if not filtered_results:
                logger.warning(f"No results above similarity threshold {self.config.similarity_threshold}")
                return []
            
            # Get documents from search results
            documents = self._get_documents_from_results(filtered_results, filters)
            
            # Apply diversity filtering if needed
            if self.config.diversity_factor > 0:
                documents = self._apply_diversity_filtering(documents)
            
            # Limit results
            documents = documents[:k]
            
            logger.info(f"Retrieved {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            raise RetrievalError(f"Document retrieval failed: {e}")
    
    def retrieve_by_query(self, 
                         query: str, 
                         k: int = 10,
                         filters: Dict[str, Any] = None) -> List[Document]:
        """
        Retrieve documents by text query.
        
        Args:
            query: Text query
            k: Number of documents to retrieve
            filters: Optional filters
            
        Returns:
            List of relevant documents
        """
        try:
            # Get or generate query embedding
            query_embedding = self._get_query_embedding(query)
            
            # Use appropriate retrieval strategy
            if self.config.strategy == RetrievalStrategy.SEMANTIC_ONLY:
                return self.retrieve_documents(query_embedding, k, filters)
            elif self.config.strategy == RetrievalStrategy.KEYWORD_ONLY:
                return self._keyword_retrieval(query, k, filters)
            elif self.config.strategy == RetrievalStrategy.HYBRID:
                return self._hybrid_retrieval(query, query_embedding, k, filters)
            else:  # RERANK
                return self._rerank_retrieval(query, query_embedding, k, filters)
                
        except Exception as e:
            logger.error(f"Query-based retrieval failed: {e}")
            raise RetrievalError(f"Query-based retrieval failed: {e}")
    
    def rank_documents(self, documents: List[Document], query: str) -> List[Document]:
        """
        Rank documents by relevance to query.
        
        Args:
            documents: List of documents to rank
            query: Query string
            
        Returns:
            Ranked list of documents
        """
        try:
            if not documents:
                return documents
            
            logger.debug(f"Ranking {len(documents)} documents")
            
            # Get query embedding
            query_embedding = self._get_query_embedding(query)
            
            # Calculate relevance scores
            scored_documents = []
            
            for doc in documents:
                score = self._calculate_document_relevance(doc, query, query_embedding)
                scored_documents.append((doc, score))
            
            # Sort by score (descending)
            scored_documents.sort(key=lambda x: x[1], reverse=True)
            
            # Return ranked documents
            ranked_docs = [doc for doc, score in scored_documents]
            
            logger.debug(f"Ranked documents by relevance")
            return ranked_docs
            
        except Exception as e:
            logger.error(f"Document ranking failed: {e}")
            return documents  # Return original order on failure
    
    def _get_query_embedding(self, query: str) -> np.ndarray:
        """Get or generate embedding for query."""
        # Check cache first
        if query in self._query_embedding_cache:
            return self._query_embedding_cache[query]
        
        # Generate new embedding
        embedding = self.embedding_generator.generate_single_embedding(query)
        
        # Cache for future use
        self._query_embedding_cache[query] = embedding
        
        return embedding
    
    def _get_documents_from_results(self, 
                                   search_results: List[Dict[str, Any]], 
                                   filters: Dict[str, Any] = None) -> List[Document]:
        """Convert search results to documents."""
        documents = []
        seen_doc_ids = set()
        
        for result in search_results:
            # Get document ID from metadata
            metadata = result.get('metadata', {})
            doc_id = metadata.get('document_id')
            
            if not doc_id or doc_id in seen_doc_ids:
                continue
            
            # Get full document
            document = self.document_store.get_document(doc_id)
            if document:
                # Apply filters if specified
                if self._passes_filters(document, filters):
                    documents.append(document)
                    seen_doc_ids.add(doc_id)
        
        return documents
    
    def _passes_filters(self, document: Document, filters: Dict[str, Any] = None) -> bool:
        """Check if document passes the specified filters."""
        if not filters:
            return True
        
        # Format type filter
        if 'format_type' in filters:
            if document.format_type.value != filters['format_type']:
                return False
        
        # Date range filters
        if 'date_from' in filters:
            if document.created_at < filters['date_from']:
                return False
        
        if 'date_to' in filters:
            if document.created_at > filters['date_to']:
                return False
        
        # Metadata filters
        if 'metadata' in filters:
            for key, value in filters['metadata'].items():
                if document.metadata.get(key) != value:
                    return False
        
        # Minimum word count
        if 'min_words' in filters:
            if document.word_count < filters['min_words']:
                return False
        
        return True
    
    def _keyword_retrieval(self, 
                          query: str, 
                          k: int, 
                          filters: Dict[str, Any] = None) -> List[Document]:
        """Retrieve documents using keyword search."""
        try:
            # Use document store's search functionality
            documents = self.document_store.search_documents(query, filters)
            
            # Rank by keyword relevance
            ranked_docs = self._rank_by_keyword_relevance(documents, query)
            
            return ranked_docs[:k]
            
        except Exception as e:
            logger.error(f"Keyword retrieval failed: {e}")
            return []
    
    def _hybrid_retrieval(self, 
                         query: str, 
                         query_embedding: np.ndarray, 
                         k: int,
                         filters: Dict[str, Any] = None) -> List[Document]:
        """Combine semantic and keyword retrieval."""
        try:
            # Get semantic results
            semantic_docs = self.retrieve_documents(query_embedding, k * 2, filters)
            
            # Get keyword results
            keyword_docs = self._keyword_retrieval(query, k * 2, filters)
            
            # Combine and deduplicate
            all_docs = {}
            
            # Add semantic results with semantic weight
            for i, doc in enumerate(semantic_docs):
                score = self.config.semantic_weight * (1.0 - i / len(semantic_docs))
                all_docs[doc.id] = (doc, score)
            
            # Add keyword results with keyword weight
            for i, doc in enumerate(keyword_docs):
                keyword_score = self.config.keyword_weight * (1.0 - i / len(keyword_docs))
                if doc.id in all_docs:
                    # Combine scores
                    existing_doc, existing_score = all_docs[doc.id]
                    all_docs[doc.id] = (existing_doc, existing_score + keyword_score)
                else:
                    all_docs[doc.id] = (doc, keyword_score)
            
            # Sort by combined score
            sorted_docs = sorted(all_docs.values(), key=lambda x: x[1], reverse=True)
            
            return [doc for doc, score in sorted_docs[:k]]
            
        except Exception as e:
            logger.error(f"Hybrid retrieval failed: {e}")
            return []
    
    def _rerank_retrieval(self, 
                         query: str, 
                         query_embedding: np.ndarray, 
                         k: int,
                         filters: Dict[str, Any] = None) -> List[Document]:
        """Retrieve with reranking for better relevance."""
        try:
            # Get initial large set of candidates
            candidates = self.retrieve_documents(
                query_embedding, 
                self.config.rerank_top_k, 
                filters
            )
            
            if not candidates:
                return []
            
            # Rerank using multiple signals
            reranked = self._advanced_reranking(candidates, query, query_embedding)
            
            return reranked[:k]
            
        except Exception as e:
            logger.error(f"Rerank retrieval failed: {e}")
            return []
    
    def _rank_by_keyword_relevance(self, documents: List[Document], query: str) -> List[Document]:
        """Rank documents by keyword relevance."""
        query_words = set(query.lower().split())
        
        scored_docs = []
        for doc in documents:
            # Calculate keyword overlap score
            doc_words = set(doc.content.lower().split())
            title_words = set(doc.title.lower().split())
            
            # Score based on word overlap
            content_overlap = len(query_words.intersection(doc_words))
            title_overlap = len(query_words.intersection(title_words))
            
            # Weight title matches higher
            score = content_overlap + (title_overlap * 2)
            scored_docs.append((doc, score))
        
        # Sort by score
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, score in scored_docs]
    
    def _calculate_document_relevance(self, 
                                    document: Document, 
                                    query: str, 
                                    query_embedding: np.ndarray) -> float:
        """Calculate overall relevance score for a document."""
        score = 0.0
        
        # Semantic similarity (if document has embeddings)
        # This would require document embeddings to be stored
        # For now, use a placeholder
        semantic_score = 0.5  # Placeholder
        
        # Keyword relevance
        keyword_score = self._calculate_keyword_relevance(document, query)
        
        # Title relevance
        title_score = self._calculate_title_relevance(document, query)
        
        # Recency score (newer documents get slight boost)
        recency_score = self._calculate_recency_score(document)
        
        # Document quality score (based on length, structure, etc.)
        quality_score = self._calculate_quality_score(document)
        
        # Combine scores with weights
        score = (
            0.4 * semantic_score +
            0.3 * keyword_score +
            0.2 * title_score +
            0.05 * recency_score +
            0.05 * quality_score
        )
        
        return score
    
    def _calculate_keyword_relevance(self, document: Document, query: str) -> float:
        """Calculate keyword-based relevance score."""
        query_words = set(query.lower().split())
        doc_words = set(document.content.lower().split())
        
        if not query_words:
            return 0.0
        
        # Jaccard similarity
        intersection = len(query_words.intersection(doc_words))
        union = len(query_words.union(doc_words))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_title_relevance(self, document: Document, query: str) -> float:
        """Calculate title-based relevance score."""
        query_words = set(query.lower().split())
        title_words = set(document.title.lower().split())
        
        if not query_words or not title_words:
            return 0.0
        
        intersection = len(query_words.intersection(title_words))
        return intersection / len(query_words)
    
    def _calculate_recency_score(self, document: Document) -> float:
        """Calculate recency-based score."""
        # Simple recency scoring - newer documents get higher scores
        # This is a placeholder implementation
        return 0.5
    
    def _calculate_quality_score(self, document: Document) -> float:
        """Calculate document quality score."""
        score = 0.0
        
        # Length-based quality (not too short, not too long)
        word_count = document.word_count
        if 100 <= word_count <= 5000:
            score += 0.5
        elif word_count > 50:
            score += 0.3
        
        # Structure quality (has title, reasonable chunk count)
        if document.title and len(document.title) > 5:
            score += 0.3
        
        if 1 <= document.chunk_count <= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _apply_diversity_filtering(self, documents: List[Document]) -> List[Document]:
        """Apply diversity filtering to avoid too similar documents."""
        if len(documents) <= 1:
            return documents
        
        diverse_docs = [documents[0]]  # Always include the top result
        
        for doc in documents[1:]:
            # Check if document is sufficiently different from selected ones
            is_diverse = True
            
            for selected_doc in diverse_docs:
                similarity = self._calculate_document_similarity(doc, selected_doc)
                if similarity > (1.0 - self.config.diversity_factor):
                    is_diverse = False
                    break
            
            if is_diverse:
                diverse_docs.append(doc)
        
        return diverse_docs
    
    def _calculate_document_similarity(self, doc1: Document, doc2: Document) -> float:
        """Calculate similarity between two documents."""
        # Simple similarity based on title and content overlap
        title_sim = self._text_similarity(doc1.title, doc2.title)
        
        # For content, use first 500 characters for efficiency
        content1 = doc1.content[:500].lower()
        content2 = doc2.content[:500].lower()
        content_sim = self._text_similarity(content1, content2)
        
        return 0.3 * title_sim + 0.7 * content_sim
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using word overlap."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _advanced_reranking(self, 
                           documents: List[Document], 
                           query: str, 
                           query_embedding: np.ndarray) -> List[Document]:
        """Perform advanced reranking using multiple signals."""
        scored_docs = []
        
        for doc in documents:
            # Calculate comprehensive relevance score
            relevance = self._calculate_document_relevance(doc, query, query_embedding)
            scored_docs.append((doc, relevance))
        
        # Sort by relevance score
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, score in scored_docs]
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics."""
        return {
            "strategy": self.config.strategy.value,
            "similarity_threshold": self.config.similarity_threshold,
            "cached_queries": len(self._query_embedding_cache),
            "vector_store_stats": self.vector_store.get_statistics(),
            "document_store_stats": self.document_store.get_statistics()
        }
    
    def clear_cache(self) -> None:
        """Clear query embedding cache."""
        self._query_embedding_cache.clear()
        logger.info("Cleared query embedding cache")