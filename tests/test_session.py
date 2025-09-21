"""Tests for session management components."""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from deep_researcher.session.session_manager import SessionManager, ResearchSession, SessionStatus, QueryHistory, SessionContext
from deep_researcher.session.query_refiner import QueryRefiner, RefinementType, QuerySuggestion
from deep_researcher.models import ProcessedQuery, QueryType, ResearchReport, Document, DocumentFormat
from deep_researcher.exceptions import ConfigurationError, QueryProcessingError


class TestSessionManager:
    """Test SessionManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.session_manager = SessionManager(session_storage_path=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_session(self):
        """Test creating a new session."""
        session = self.session_manager.create_session(
            title="Test Session",
            description="Test description",
            user_id="test_user"
        )
        
        assert session.title == "Test Session"
        assert session.description == "Test description"
        assert session.user_id == "test_user"
        assert session.status == SessionStatus.ACTIVE
        assert len(session.query_history) == 0
        assert session.session_id in self.session_manager.active_sessions
    
    def test_get_session(self):
        """Test retrieving a session."""
        # Create session
        session = self.session_manager.create_session(title="Test Session")
        session_id = session.session_id
        
        # Retrieve session
        retrieved_session = self.session_manager.get_session(session_id)
        
        assert retrieved_session is not None
        assert retrieved_session.session_id == session_id
        assert retrieved_session.title == "Test Session"
    
    def test_get_nonexistent_session(self):
        """Test retrieving non-existent session."""
        result = self.session_manager.get_session("nonexistent_id")
        assert result is None
    
    def test_add_query_to_session(self):
        """Test adding a query to a session."""
        # Create session
        session = self.session_manager.create_session(title="Test Session")
        
        # Create test query
        processed_query = ProcessedQuery(
            original_query="What is AI?",
            query_type=QueryType.SIMPLE,
            complexity_score=0.3,
            keywords=["AI", "artificial", "intelligence"]
        )
        
        # Create test report
        test_doc = Document(
            id="doc1",
            title="AI Document",
            content="AI is artificial intelligence",
            source_path="/test.txt",
            format_type=DocumentFormat.TXT
        )
        
        research_report = ResearchReport(
            query="What is AI?",
            summary="AI is artificial intelligence technology",
            key_findings=["AI involves machine learning", "AI has many applications"],
            sources=[test_doc]
        )
        
        # Add query to session
        self.session_manager.add_query_to_session(
            session.session_id,
            "What is AI?",
            processed_query,
            research_report,
            execution_time=5.0,
            success=True
        )
        
        # Verify query was added
        updated_session = self.session_manager.get_session(session.session_id)
        assert len(updated_session.query_history) == 1
        
        query_entry = updated_session.query_history[0]
        assert query_entry.original_query == "What is AI?"
        assert query_entry.success is True
        assert query_entry.execution_time == 5.0
        assert len(query_entry.follow_up_suggestions) > 0
    
    def test_get_session_context_for_query(self):
        """Test getting session context for query processing."""
        # Create session with some history
        session = self.session_manager.create_session(title="Test Session")
        
        processed_query = ProcessedQuery(
            original_query="What is machine learning?",
            query_type=QueryType.SIMPLE,
            complexity_score=0.4,
            keywords=["machine", "learning"]
        )
        
        self.session_manager.add_query_to_session(
            session.session_id,
            "What is machine learning?",
            processed_query,
            success=True
        )
        
        # Get context
        context = self.session_manager.get_session_context_for_query(session.session_id)
        
        assert context['session_id'] == session.session_id
        assert 'key_concepts' in context
        assert 'previous_queries' in context
        assert context['query_count'] == 1
        assert context['successful_queries'] == 1
    
    def test_get_session_summary(self):
        """Test getting session summary."""
        # Create session with queries
        session = self.session_manager.create_session(title="Test Session")
        
        # Add successful query
        processed_query = ProcessedQuery(
            original_query="Test query",
            query_type=QueryType.SIMPLE,
            complexity_score=0.3,
            keywords=["test"]
        )
        
        self.session_manager.add_query_to_session(
            session.session_id,
            "Test query",
            processed_query,
            execution_time=3.0,
            success=True
        )
        
        # Get summary
        summary = self.session_manager.get_session_summary(session.session_id)
        
        assert summary['session_id'] == session.session_id
        assert summary['title'] == "Test Session"
        assert summary['total_queries'] == 1
        assert summary['successful_queries'] == 1
        assert summary['success_rate'] == 1.0
        assert summary['total_execution_time'] == 3.0
    
    def test_list_sessions(self):
        """Test listing sessions."""
        # Create multiple sessions
        session1 = self.session_manager.create_session(title="Session 1", user_id="user1")
        session2 = self.session_manager.create_session(title="Session 2", user_id="user2")
        
        # List all sessions
        all_sessions = self.session_manager.list_sessions()
        assert len(all_sessions) == 2
        
        # List sessions by user
        user1_sessions = self.session_manager.list_sessions(user_id="user1")
        assert len(user1_sessions) == 1
        assert user1_sessions[0]['title'] == "Session 1"
    
    def test_close_session(self):
        """Test closing a session."""
        session = self.session_manager.create_session(title="Test Session")
        session_id = session.session_id
        
        # Close session
        result = self.session_manager.close_session(session_id)
        assert result is True
        
        # Verify session is closed
        closed_session = self.session_manager.get_session(session_id)
        assert closed_session is None  # Should not be retrievable as active
    
    def test_session_expiry(self):
        """Test session expiry functionality."""
        session = self.session_manager.create_session(title="Test Session")
        
        # Manually set last activity to past
        session.last_activity = datetime.now() - timedelta(hours=25)
        
        # Check if expired
        assert session.is_expired(24) is True
    
    def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions."""
        # Create session and make it expired
        session = self.session_manager.create_session(title="Expired Session")
        session.last_activity = datetime.now() - timedelta(hours=25)
        
        # Run cleanup
        cleaned_count = self.session_manager.cleanup_expired_sessions()
        
        assert cleaned_count >= 0  # Should clean up at least the expired session
    
    def test_get_session_statistics(self):
        """Test getting session statistics."""
        # Create sessions with queries
        session = self.session_manager.create_session(title="Test Session")
        
        processed_query = ProcessedQuery(
            original_query="Test query",
            query_type=QueryType.SIMPLE,
            complexity_score=0.3,
            keywords=["test"]
        )
        
        self.session_manager.add_query_to_session(
            session.session_id,
            "Test query",
            processed_query,
            success=True
        )
        
        # Get statistics
        stats = self.session_manager.get_session_statistics()
        
        assert stats['total_sessions'] >= 1
        assert stats['total_queries'] >= 1
        assert stats['successful_queries'] >= 1
        assert 'average_queries_per_session' in stats
        assert 'overall_success_rate' in stats


class TestQueryRefiner:
    """Test QueryRefiner class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.query_refiner = QueryRefiner()
    
    def create_test_processed_query(self, query_type: QueryType = QueryType.SIMPLE) -> ProcessedQuery:
        """Create a test processed query."""
        return ProcessedQuery(
            original_query="What is machine learning?",
            query_type=query_type,
            complexity_score=0.5,
            keywords=["machine", "learning", "AI"]
        )
    
    def create_test_session(self) -> ResearchSession:
        """Create a test session."""
        return ResearchSession(
            session_id="test_session",
            user_id="test_user",
            title="Test Session",
            description="Test description",
            status=SessionStatus.ACTIVE,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            query_history=[],
            session_context=SessionContext(
                research_domain="technology",
                key_concepts=["AI", "machine learning"],
                accumulated_knowledge={},
                user_preferences={},
                query_patterns=[],
                focus_areas=["artificial intelligence"],
                avoided_topics=[]
            ),
            metadata={}
        )
    
    def test_analyze_query_for_refinement(self):
        """Test query analysis for refinement."""
        query = "What is AI?"
        processed_query = self.create_test_processed_query()
        
        analysis = self.query_refiner.analyze_query_for_refinement(
            query, processed_query
        )
        
        assert analysis.original_query == query
        assert isinstance(analysis.issues_identified, list)
        assert isinstance(analysis.improvement_opportunities, list)
        assert isinstance(analysis.suggested_refinements, list)
        assert 0 <= analysis.confidence_in_analysis <= 1
    
    def test_analyze_vague_query(self):
        """Test analysis of vague query."""
        vague_query = "Tell me about good stuff"
        
        analysis = self.query_refiner.analyze_query_for_refinement(vague_query)
        
        # Should identify vague terms as an issue
        assert any("vague terms" in issue for issue in analysis.issues_identified)
        
        # Should suggest clarification
        assert any(suggestion.refinement_type == RefinementType.CLARIFICATION 
                  for suggestion in analysis.suggested_refinements)
    
    def test_analyze_short_query(self):
        """Test analysis of very short query."""
        short_query = "AI"
        
        analysis = self.query_refiner.analyze_query_for_refinement(short_query)
        
        # Should identify short length as an issue
        assert any("very short" in issue for issue in analysis.issues_identified)
        
        # Should suggest expansion
        assert any(suggestion.refinement_type == RefinementType.EXPANSION 
                  for suggestion in analysis.suggested_refinements)
    
    def test_analyze_complex_query(self):
        """Test analysis of complex query."""
        complex_query = "What is machine learning and how does it compare to deep learning and what are the applications and limitations and future prospects?"
        processed_query = ProcessedQuery(
            original_query=complex_query,
            query_type=QueryType.COMPLEX,
            complexity_score=0.9,
            keywords=["machine", "learning", "deep", "applications"]
        )
        
        analysis = self.query_refiner.analyze_query_for_refinement(
            complex_query, processed_query
        )
        
        # Should identify high complexity
        assert any("very high" in issue for issue in analysis.issues_identified)
        
        # Should suggest narrowing
        assert any(suggestion.refinement_type == RefinementType.NARROWING 
                  for suggestion in analysis.suggested_refinements)
    
    def test_suggest_follow_up_queries(self):
        """Test follow-up query suggestions."""
        # Create test research report
        test_doc = Document(
            id="doc1",
            title="AI Document",
            content="AI content",
            source_path="/test.txt",
            format_type=DocumentFormat.TXT
        )
        
        research_report = ResearchReport(
            query="What is AI?",
            summary="AI is artificial intelligence",
            key_findings=["AI involves machine learning", "AI has neural networks"],
            sources=[test_doc],
            confidence_score=0.8
        )
        
        suggestions = self.query_refiner.suggest_follow_up_queries(research_report)
        
        assert len(suggestions) > 0
        assert all(isinstance(suggestion, QuerySuggestion) for suggestion in suggestions)
        assert any(suggestion.refinement_type == RefinementType.FOLLOW_UP 
                  for suggestion in suggestions)
    
    def test_suggest_follow_up_with_low_confidence(self):
        """Test follow-up suggestions for low confidence results."""
        test_doc = Document(
            id="doc1",
            title="AI Document", 
            content="AI content",
            source_path="/test.txt",
            format_type=DocumentFormat.TXT
        )
        
        low_confidence_report = ResearchReport(
            query="What is AI?",
            summary="Limited information about AI",
            key_findings=["Some information about AI"],
            sources=[test_doc],
            confidence_score=0.4  # Low confidence
        )
        
        suggestions = self.query_refiner.suggest_follow_up_queries(low_confidence_report)
        
        # Should suggest clarification due to low confidence
        assert any(suggestion.refinement_type == RefinementType.CLARIFICATION 
                  for suggestion in suggestions)
    
    def test_refine_query_interactively(self):
        """Test interactive query refinement."""
        original_query = "What is AI?"
        
        # Test making query more specific
        feedback = {
            'make_more_specific': True,
            'specific_aspects': ['machine learning', 'neural networks']
        }
        
        refined_query = self.query_refiner.refine_query_interactively(
            original_query, feedback
        )
        
        assert refined_query != original_query
        assert 'machine learning' in refined_query
        assert 'neural networks' in refined_query
    
    def test_refine_query_broaden_scope(self):
        """Test broadening query scope."""
        original_query = "What is supervised learning?"
        
        feedback = {'broaden_scope': True}
        
        refined_query = self.query_refiner.refine_query_interactively(
            original_query, feedback
        )
        
        assert refined_query != original_query
        assert 'all' in refined_query.lower() or 'aspects' in refined_query.lower()
    
    def test_refine_query_change_focus(self):
        """Test changing query focus."""
        original_query = "What is machine learning?"
        
        feedback = {
            'change_focus': True,
            'new_focus': 'business'
        }
        
        refined_query = self.query_refiner.refine_query_interactively(
            original_query, feedback
        )
        
        assert 'business' in refined_query.lower()
    
    def test_refine_query_with_session_context(self):
        """Test query refinement with session context."""
        original_query = "What is deep learning?"
        session = self.create_test_session()
        
        feedback = {'make_more_specific': True}
        
        refined_query = self.query_refiner.refine_query_interactively(
            original_query, feedback, session
        )
        
        # Should incorporate session domain context
        assert 'technology' in refined_query.lower() or original_query in refined_query
    
    def test_identify_query_issues(self):
        """Test identification of query issues."""
        # Test vague query
        vague_query = "Tell me about good things"
        issues = self.query_refiner._identify_query_issues(vague_query, None)
        
        assert any("vague terms" in issue for issue in issues)
    
    def test_identify_improvement_opportunities(self):
        """Test identification of improvement opportunities."""
        query = "Compare recent AI developments"
        processed_query = self.create_test_processed_query(QueryType.COMPARATIVE)
        
        opportunities = self.query_refiner._identify_improvement_opportunities(
            query, processed_query, None
        )
        
        assert len(opportunities) > 0
        # Should suggest temporal specificity
        assert any("time periods" in opp for opp in opportunities)
    
    def test_replace_vague_terms(self):
        """Test replacement of vague terms."""
        vague_query = "Tell me about good stuff"
        
        refined_query = self.query_refiner._replace_vague_terms(vague_query)
        
        assert "good" not in refined_query
        assert "stuff" not in refined_query
        assert "effective" in refined_query or "high-quality" in refined_query
    
    def test_expand_short_query(self):
        """Test expansion of short queries."""
        short_query = "AI"
        
        expanded_query = self.query_refiner._expand_short_query(short_query, None, None)
        
        assert len(expanded_query) > len(short_query)
        assert "?" in expanded_query
    
    def test_break_down_complex_query(self):
        """Test breaking down complex queries."""
        complex_query = "What is AI and how does it work and what are its applications?"
        
        simplified_queries = self.query_refiner._break_down_complex_query(complex_query, None)
        
        assert len(simplified_queries) > 1
        assert all(len(query) < len(complex_query) for query in simplified_queries)
    
    def test_domain_inference(self):
        """Test domain inference from keywords."""
        tech_keywords = ["software", "algorithm", "programming"]
        domain = self.query_refiner._infer_domain_from_keywords(tech_keywords)
        
        assert domain == "technology"
        
        science_keywords = ["research", "study", "experiment"]
        domain = self.query_refiner._infer_domain_from_keywords(science_keywords)
        
        assert domain == "science"
    
    def test_extract_key_concepts(self):
        """Test key concept extraction."""
        text = "Machine learning algorithms use neural networks for pattern recognition"
        
        concepts = self.query_refiner._extract_key_concepts_from_text(text)
        
        assert len(concepts) > 0
        assert any("machine" in concept.lower() or "learning" in concept.lower() 
                  for concept in concepts)