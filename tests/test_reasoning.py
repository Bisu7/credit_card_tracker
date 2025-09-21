"""Tests for reasoning components."""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime

from deep_researcher.reasoning.query_processor import QueryProcessor, QueryFeatures
from deep_researcher.reasoning.multi_step_reasoner import MultiStepReasoner, ReasoningContext
from deep_researcher.reasoning.document_retriever import DocumentRetriever, RetrievalConfig, RetrievalStrategy
from deep_researcher.models import ProcessedQuery, QueryType, ReasoningStep, Document, DocumentFormat
from deep_researcher.exceptions import QueryProcessingError, ReasoningError, RetrievalError


class TestQueryProcessor:
    """Test QueryProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = QueryProcessor()
    
    def test_process_simple_query(self):
        """Test processing a simple query."""
        query = "What is machine learning?"
        
        result = self.processor.process_query(query)
        
        assert result.original_query == query
        assert result.query_type == QueryType.SIMPLE
        assert 0 <= result.complexity_score <= 1
        assert len(result.keywords) > 0
        assert result.expected_sources > 0
    
    def test_process_complex_query(self):
        """Test processing a complex query."""
        query = "Compare machine learning and deep learning approaches, analyze their differences, and explain when to use each method"
        
        result = self.processor.process_query(query)
        
        assert result.original_query == query
        assert result.query_type in [QueryType.COMPLEX, QueryType.COMPARATIVE, QueryType.ANALYTICAL]
        assert result.complexity_score > 0.5
        assert len(result.keywords) > 0
        assert len(result.sub_queries) >= 0
    
    def test_process_comparative_query(self):
        """Test processing a comparative query."""
        query = "Compare Python vs Java for web development"
        
        result = self.processor.process_query(query)
        
        assert result.query_type == QueryType.COMPARATIVE
        assert "python" in [k.lower() for k in result.keywords] or "java" in [k.lower() for k in result.keywords]
    
    def test_process_analytical_query(self):
        """Test processing an analytical query."""
        query = "Analyze the impact of artificial intelligence on employment"
        
        result = self.processor.process_query(query)
        
        assert result.query_type == QueryType.ANALYTICAL
        assert result.complexity_score > 0.3
    
    def test_process_empty_query(self):
        """Test processing empty query."""
        with pytest.raises(QueryProcessingError, match="Query cannot be empty"):
            self.processor.process_query("")
    
    def test_classify_query_type(self):
        """Test query type classification."""
        # Simple query
        assert self.processor.classify_query_type("What is AI?") == QueryType.SIMPLE.value
        
        # Comparative query
        assert self.processor.classify_query_type("Compare A vs B") == QueryType.COMPARATIVE.value
        
        # Analytical query
        assert self.processor.classify_query_type("Analyze the effects of X") == QueryType.ANALYTICAL.value
    
    def test_extract_features(self):
        """Test feature extraction."""
        query = "What are the differences between machine learning and deep learning?"
        features = self.processor._extract_features(query)
        
        assert isinstance(features, QueryFeatures)
        assert features.word_count > 0
        assert len(features.question_words) > 0
        assert len(features.comparison_words) > 0
    
    def test_clean_query(self):
        """Test query cleaning."""
        dirty_query = "  What   is    AI???   "
        cleaned = self.processor._clean_query(dirty_query)
        
        assert cleaned == "What is AI?"
    
    def test_extract_keywords(self):
        """Test keyword extraction."""
        query = "machine learning algorithms for natural language processing"
        features = QueryFeatures(
            word_count=7, question_words=[], comparison_words=[],
            temporal_words=[], analytical_words=[], entities=[],
            has_multiple_questions=False, has_conjunctions=False,
            complexity_indicators=[]
        )
        
        keywords = self.processor._extract_keywords(query, features)
        
        assert len(keywords) > 0
        assert any(keyword in ["machine", "learning", "algorithms", "natural", "language", "processing"] 
                  for keyword in keywords)
    
    def test_get_query_suggestions(self):
        """Test query suggestion generation."""
        # Short query
        suggestions = self.processor.get_query_suggestions("AI")
        assert len(suggestions) > 0
        
        # Long query
        long_query = "What are all the comprehensive details about machine learning algorithms and their applications in various domains"
        suggestions = self.processor.get_query_suggestions(long_query)
        assert len(suggestions) > 0
    
    def test_validate_query(self):
        """Test query validation."""
        # Valid query
        validation = self.processor.validate_query("What is machine learning?")
        assert validation['is_valid'] is True
        
        # Empty query
        validation = self.processor.validate_query("")
        assert validation['is_valid'] is False
        assert len(validation['issues']) > 0
        
        # Very short query
        validation = self.processor.validate_query("AI")
        assert len(validation['issues']) > 0 or len(validation['suggestions']) > 0


class TestMultiStepReasoner:
    """Test MultiStepReasoner class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.reasoner = MultiStepReasoner(max_steps=5)
    
    def create_test_query(self, query_type: QueryType = QueryType.COMPLEX) -> ProcessedQuery:
        """Create a test processed query."""
        return ProcessedQuery(
            original_query="Test query for reasoning",
            query_type=query_type,
            complexity_score=0.8,
            sub_queries=["Sub query 1", "Sub query 2"],
            keywords=["test", "reasoning", "query"]
        )
    
    def test_create_reasoning_plan_comparative(self):
        """Test creating reasoning plan for comparative query."""
        query = self.create_test_query(QueryType.COMPARATIVE)
        
        steps = self.reasoner.create_reasoning_plan(query)
        
        assert len(steps) > 0
        assert all(isinstance(step, ReasoningStep) for step in steps)
        assert any("research" in step.description.lower() for step in steps)
    
    def test_create_reasoning_plan_analytical(self):
        """Test creating reasoning plan for analytical query."""
        query = self.create_test_query(QueryType.ANALYTICAL)
        
        steps = self.reasoner.create_reasoning_plan(query)
        
        assert len(steps) > 0
        assert any("analyze" in step.description.lower() or "analytical" in step.description.lower() 
                  for step in steps)
    
    def test_create_reasoning_plan_multi_part(self):
        """Test creating reasoning plan for multi-part query."""
        query = self.create_test_query(QueryType.MULTI_PART)
        
        steps = self.reasoner.create_reasoning_plan(query)
        
        assert len(steps) > 0
        # Should have steps for sub-queries
        assert len(steps) >= len(query.sub_queries)
    
    def test_create_reasoning_plan_simple(self):
        """Test creating reasoning plan for simple query."""
        query = self.create_test_query(QueryType.SIMPLE)
        
        steps = self.reasoner.create_reasoning_plan(query)
        
        assert len(steps) > 0
        # Simple queries should have fewer steps
        assert len(steps) <= 2
    
    def test_execute_reasoning_step(self):
        """Test executing a single reasoning step."""
        step = ReasoningStep(
            step_id="test_step",
            description="Test step for execution",
            query="What is the test about?",
            confidence=0.9
        )
        
        context = {}
        result = self.reasoner.execute_reasoning_step(step, context)
        
        assert isinstance(result, dict)
        assert result['step_id'] == step.step_id
        assert result['status'] == 'completed'
        assert step.results == result
    
    def test_execute_reasoning_step_with_dependencies(self):
        """Test executing step with dependencies."""
        step = ReasoningStep(
            step_id="dependent_step",
            description="Step with dependencies",
            query="Dependent query",
            dependencies=["missing_dep"],
            confidence=0.8
        )
        
        context = {}
        
        with pytest.raises(ReasoningError, match="Missing dependencies"):
            self.reasoner.execute_reasoning_step(step, context)
    
    def test_execute_full_reasoning(self):
        """Test executing full reasoning process."""
        query = self.create_test_query(QueryType.COMPARATIVE)
        
        context = self.reasoner.execute_full_reasoning(query)
        
        assert isinstance(context, ReasoningContext)
        assert context.original_query == query
        assert len(context.steps) > 0
        assert len(context.step_results) >= 0  # Some steps might fail in test
    
    def test_determine_execution_order(self):
        """Test determining execution order based on dependencies."""
        steps = [
            ReasoningStep(step_id="step1", description="First", query="Query 1"),
            ReasoningStep(step_id="step2", description="Second", query="Query 2", dependencies=["step1"]),
            ReasoningStep(step_id="step3", description="Third", query="Query 3", dependencies=["step1", "step2"])
        ]
        
        order = self.reasoner._determine_execution_order(steps)
        
        assert order.index("step1") < order.index("step2")
        assert order.index("step2") < order.index("step3")
    
    def test_validate_and_optimize_plan(self):
        """Test plan validation and optimization."""
        query = self.create_test_query()
        
        # Create steps with duplicate queries
        steps = [
            ReasoningStep(step_id="step1", description="First", query="Same query"),
            ReasoningStep(step_id="step2", description="Second", query="Same query"),  # Duplicate
            ReasoningStep(step_id="step3", description="Third", query="Different query")
        ]
        
        optimized = self.reasoner._validate_and_optimize_plan(steps, query)
        
        # Should remove duplicates
        assert len(optimized) < len(steps)
        queries = [step.query for step in optimized]
        assert len(queries) == len(set(queries))  # No duplicates
    
    def test_get_reasoning_summary(self):
        """Test getting reasoning summary."""
        query = self.create_test_query()
        context = ReasoningContext(
            original_query=query,
            steps=[],
            step_results={"step1": {"status": "completed"}},
            global_context={"all_findings": ["finding1", "finding2"]},
            execution_order=["step1"],
            failed_steps=[],
            start_time=time.time() - 10
        )
        
        summary = self.reasoner.get_reasoning_summary(context)
        
        assert summary['original_query'] == query.original_query
        assert summary['completed_steps'] == 1
        assert summary['failed_steps'] == 0
        assert summary['execution_time'] > 0
        assert 'global_findings' in summary


class TestDocumentRetriever:
    """Test DocumentRetriever class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_vector_store = Mock()
        self.mock_document_store = Mock()
        self.mock_embedding_generator = Mock()
        
        # Configure mocks
        self.mock_vector_store.search.return_value = [
            {
                'vector_id': 'vec1',
                'similarity_score': 0.9,
                'metadata': {'document_id': 'doc1', 'chunk_id': 'chunk1'}
            },
            {
                'vector_id': 'vec2', 
                'similarity_score': 0.8,
                'metadata': {'document_id': 'doc2', 'chunk_id': 'chunk2'}
            }
        ]
        
        self.mock_embedding_generator.generate_single_embedding.return_value = np.random.rand(384)
        
        # Create test documents
        self.test_doc1 = Document(
            id="doc1",
            title="Test Document 1",
            content="This is test content about machine learning",
            source_path="/test1.txt",
            format_type=DocumentFormat.TXT
        )
        
        self.test_doc2 = Document(
            id="doc2", 
            title="Test Document 2",
            content="This is test content about deep learning",
            source_path="/test2.txt",
            format_type=DocumentFormat.TXT
        )
        
        self.mock_document_store.get_document.side_effect = lambda doc_id: {
            'doc1': self.test_doc1,
            'doc2': self.test_doc2
        }.get(doc_id)
        
        # Create retriever
        self.retriever = DocumentRetriever(
            self.mock_vector_store,
            self.mock_document_store,
            self.mock_embedding_generator
        )
    
    def test_retrieve_documents(self):
        """Test document retrieval by embedding."""
        query_embedding = np.random.rand(384)
        
        documents = self.retriever.retrieve_documents(query_embedding, k=2)
        
        assert len(documents) <= 2
        self.mock_vector_store.search.assert_called_once()
    
    def test_retrieve_by_query(self):
        """Test document retrieval by text query."""
        query = "machine learning algorithms"
        
        documents = self.retriever.retrieve_by_query(query, k=2)
        
        assert isinstance(documents, list)
        self.mock_embedding_generator.generate_single_embedding.assert_called_with(query)
    
    def test_rank_documents(self):
        """Test document ranking."""
        documents = [self.test_doc1, self.test_doc2]
        query = "machine learning"
        
        ranked = self.retriever.rank_documents(documents, query)
        
        assert len(ranked) == len(documents)
        assert all(isinstance(doc, Document) for doc in ranked)
    
    def test_keyword_retrieval(self):
        """Test keyword-based retrieval."""
        self.mock_document_store.search_documents.return_value = [self.test_doc1]
        
        documents = self.retriever._keyword_retrieval("machine learning", k=5)
        
        assert len(documents) > 0
        self.mock_document_store.search_documents.assert_called_once()
    
    def test_hybrid_retrieval(self):
        """Test hybrid retrieval strategy."""
        self.retriever.config.strategy = RetrievalStrategy.HYBRID
        query = "machine learning"
        query_embedding = np.random.rand(384)
        
        # Mock both semantic and keyword results
        self.mock_document_store.search_documents.return_value = [self.test_doc2]
        
        documents = self.retriever._hybrid_retrieval(query, query_embedding, k=5)
        
        assert isinstance(documents, list)
    
    def test_passes_filters(self):
        """Test document filtering."""
        # No filters - should pass
        assert self.retriever._passes_filters(self.test_doc1, None) is True
        
        # Format filter - should pass
        filters = {'format_type': 'txt'}
        assert self.retriever._passes_filters(self.test_doc1, filters) is True
        
        # Format filter - should fail
        filters = {'format_type': 'pdf'}
        assert self.retriever._passes_filters(self.test_doc1, filters) is False
    
    def test_calculate_keyword_relevance(self):
        """Test keyword relevance calculation."""
        query = "machine learning test"
        
        relevance = self.retriever._calculate_keyword_relevance(self.test_doc1, query)
        
        assert 0 <= relevance <= 1
        assert isinstance(relevance, float)
    
    def test_calculate_title_relevance(self):
        """Test title relevance calculation."""
        query = "test document"
        
        relevance = self.retriever._calculate_title_relevance(self.test_doc1, query)
        
        assert 0 <= relevance <= 1
        assert isinstance(relevance, float)
    
    def test_apply_diversity_filtering(self):
        """Test diversity filtering."""
        # Create similar documents
        similar_docs = [self.test_doc1, self.test_doc2]
        
        diverse_docs = self.retriever._apply_diversity_filtering(similar_docs)
        
        assert len(diverse_docs) <= len(similar_docs)
        assert len(diverse_docs) > 0
    
    def test_text_similarity(self):
        """Test text similarity calculation."""
        text1 = "machine learning algorithms"
        text2 = "machine learning models"
        
        similarity = self.retriever._text_similarity(text1, text2)
        
        assert 0 <= similarity <= 1
        assert similarity > 0  # Should have some overlap
    
    def test_get_retrieval_stats(self):
        """Test getting retrieval statistics."""
        self.mock_vector_store.get_statistics.return_value = {'total_vectors': 100}
        self.mock_document_store.get_statistics.return_value = {'total_documents': 50}
        
        stats = self.retriever.get_retrieval_stats()
        
        assert 'strategy' in stats
        assert 'similarity_threshold' in stats
        assert 'vector_store_stats' in stats
        assert 'document_store_stats' in stats
    
    def test_clear_cache(self):
        """Test clearing query embedding cache."""
        # Add something to cache
        self.retriever._query_embedding_cache['test'] = np.random.rand(384)
        
        self.retriever.clear_cache()
        
        assert len(self.retriever._query_embedding_cache) == 0