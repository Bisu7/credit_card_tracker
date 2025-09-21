"""Session management for multi-turn research conversations."""

import uuid
import json
from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

from ..models import ProcessedQuery, ResearchReport, ReasoningStep
from ..reasoning.multi_step_reasoner import ReasoningContext
from ..exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Status of a research session."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"


@dataclass
class QueryHistory:
    """History entry for a query in the session."""
    query_id: str
    original_query: str
    processed_query: ProcessedQuery
    research_report: Optional[ResearchReport]
    reasoning_context: Optional[ReasoningContext]
    timestamp: datetime
    execution_time: float
    success: bool
    follow_up_suggestions: List[str]


@dataclass
class SessionContext:
    """Context maintained across queries in a session."""
    research_domain: str
    key_concepts: List[str]
    accumulated_knowledge: Dict[str, Any]
    user_preferences: Dict[str, Any]
    query_patterns: List[str]
    focus_areas: List[str]
    avoided_topics: List[str]


@dataclass
class ResearchSession:
    """A complete research session with history and context."""
    session_id: str
    user_id: Optional[str]
    title: str
    description: str
    status: SessionStatus
    created_at: datetime
    last_activity: datetime
    query_history: List[QueryHistory]
    session_context: SessionContext
    metadata: Dict[str, Any]
    
    def is_expired(self, expiry_hours: int = 24) -> bool:
        """Check if session has expired."""
        expiry_time = self.last_activity + timedelta(hours=expiry_hours)
        return datetime.now() > expiry_time
    
    def get_recent_queries(self, limit: int = 5) -> List[QueryHistory]:
        """Get recent queries from the session."""
        return sorted(self.query_history, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_successful_queries(self) -> List[QueryHistory]:
        """Get all successful queries from the session."""
        return [q for q in self.query_history if q.success]
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now()


class SessionManager:
    """Manages research sessions and context preservation."""
    
    def __init__(self, session_storage_path: Optional[str] = None):
        """
        Initialize session manager.
        
        Args:
            session_storage_path: Path to store session data
        """
        self.session_storage_path = session_storage_path or "./data/sessions"
        self.active_sessions: Dict[str, ResearchSession] = {}
        self.session_expiry_hours = 24
        
        # Ensure storage directory exists
        import os
        os.makedirs(self.session_storage_path, exist_ok=True)
        
        # Load existing sessions
        self._load_sessions()
    
    def create_session(self, 
                      title: str = "Research Session",
                      description: str = "",
                      user_id: Optional[str] = None) -> ResearchSession:
        """
        Create a new research session.
        
        Args:
            title: Session title
            description: Session description
            user_id: Optional user identifier
            
        Returns:
            New research session
        """
        try:
            session_id = str(uuid.uuid4())
            
            session = ResearchSession(
                session_id=session_id,
                user_id=user_id,
                title=title,
                description=description,
                status=SessionStatus.ACTIVE,
                created_at=datetime.now(),
                last_activity=datetime.now(),
                query_history=[],
                session_context=SessionContext(
                    research_domain="general",
                    key_concepts=[],
                    accumulated_knowledge={},
                    user_preferences={},
                    query_patterns=[],
                    focus_areas=[],
                    avoided_topics=[]
                ),
                metadata={}
            )
            
            self.active_sessions[session_id] = session
            self._save_session(session)
            
            logger.info(f"Created new session: {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise ConfigurationError(f"Failed to create session: {e}")
    
    def get_session(self, session_id: str) -> Optional[ResearchSession]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Research session or None if not found
        """
        # Check active sessions first
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            # Check if expired
            if session.is_expired(self.session_expiry_hours):
                session.status = SessionStatus.EXPIRED
                self._save_session(session)
                return None
            
            return session
        
        # Try to load from storage
        session = self._load_session(session_id)
        if session and not session.is_expired(self.session_expiry_hours):
            self.active_sessions[session_id] = session
            return session
        
        return None
    
    def add_query_to_session(self, 
                           session_id: str,
                           original_query: str,
                           processed_query: ProcessedQuery,
                           research_report: Optional[ResearchReport] = None,
                           reasoning_context: Optional[ReasoningContext] = None,
                           execution_time: float = 0.0,
                           success: bool = True) -> None:
        """
        Add a query and its results to a session.
        
        Args:
            session_id: Session identifier
            original_query: Original query string
            processed_query: Processed query object
            research_report: Generated research report
            reasoning_context: Reasoning context from execution
            execution_time: Time taken to execute query
            success: Whether query execution was successful
        """
        try:
            session = self.get_session(session_id)
            if not session:
                raise ValueError(f"Session not found: {session_id}")
            
            # Generate follow-up suggestions
            follow_up_suggestions = self._generate_follow_up_suggestions(
                original_query, processed_query, research_report, session
            )
            
            # Create query history entry
            query_history = QueryHistory(
                query_id=str(uuid.uuid4()),
                original_query=original_query,
                processed_query=processed_query,
                research_report=research_report,
                reasoning_context=reasoning_context,
                timestamp=datetime.now(),
                execution_time=execution_time,
                success=success,
                follow_up_suggestions=follow_up_suggestions
            )
            
            # Add to session
            session.query_history.append(query_history)
            session.update_activity()
            
            # Update session context
            self._update_session_context(session, original_query, processed_query, research_report)
            
            # Save session
            self._save_session(session)
            
            logger.info(f"Added query to session {session_id}: {original_query[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to add query to session: {e}")
            raise ConfigurationError(f"Failed to add query to session: {e}")
    
    def get_session_context_for_query(self, session_id: str) -> Dict[str, Any]:
        """
        Get relevant context for processing a new query in the session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Context dictionary for query processing
        """
        session = self.get_session(session_id)
        if not session:
            return {}
        
        context = {
            'session_id': session_id,
            'research_domain': session.session_context.research_domain,
            'key_concepts': session.session_context.key_concepts,
            'focus_areas': session.session_context.focus_areas,
            'user_preferences': session.session_context.user_preferences,
            'previous_queries': [q.original_query for q in session.get_recent_queries(3)],
            'accumulated_knowledge': session.session_context.accumulated_knowledge,
            'query_count': len(session.query_history),
            'successful_queries': len(session.get_successful_queries())
        }
        
        return context
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get a summary of the session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session summary dictionary
        """
        session = self.get_session(session_id)
        if not session:
            return {}
        
        successful_queries = session.get_successful_queries()
        
        summary = {
            'session_id': session_id,
            'title': session.title,
            'status': session.status.value,
            'created_at': session.created_at.isoformat(),
            'last_activity': session.last_activity.isoformat(),
            'total_queries': len(session.query_history),
            'successful_queries': len(successful_queries),
            'success_rate': len(successful_queries) / len(session.query_history) if session.query_history else 0,
            'research_domain': session.session_context.research_domain,
            'key_concepts': session.session_context.key_concepts,
            'focus_areas': session.session_context.focus_areas,
            'total_execution_time': sum(q.execution_time for q in session.query_history),
            'average_execution_time': sum(q.execution_time for q in session.query_history) / len(session.query_history) if session.query_history else 0
        }
        
        return summary
    
    def list_sessions(self, user_id: Optional[str] = None, status: Optional[SessionStatus] = None) -> List[Dict[str, Any]]:
        """
        List sessions with optional filtering.
        
        Args:
            user_id: Filter by user ID
            status: Filter by session status
            
        Returns:
            List of session summaries
        """
        sessions = []
        
        # Check active sessions
        for session in self.active_sessions.values():
            if user_id and session.user_id != user_id:
                continue
            if status and session.status != status:
                continue
            
            sessions.append(self.get_session_summary(session.session_id))
        
        # Load sessions from storage if needed
        # (This could be optimized with an index)
        
        return sorted(sessions, key=lambda x: x['last_activity'], reverse=True)
    
    def close_session(self, session_id: str) -> bool:
        """
        Close a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was closed successfully
        """
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            session.status = SessionStatus.COMPLETED
            session.update_activity()
            
            self._save_session(session)
            
            # Remove from active sessions
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            logger.info(f"Closed session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to close session: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        cleaned_count = 0
        
        # Check active sessions
        expired_sessions = []
        for session_id, session in self.active_sessions.items():
            if session.is_expired(self.session_expiry_hours):
                session.status = SessionStatus.EXPIRED
                self._save_session(session)
                expired_sessions.append(session_id)
                cleaned_count += 1
        
        # Remove from active sessions
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        logger.info(f"Cleaned up {cleaned_count} expired sessions")
        return cleaned_count
    
    def _update_session_context(self, 
                               session: ResearchSession,
                               original_query: str,
                               processed_query: ProcessedQuery,
                               research_report: Optional[ResearchReport]) -> None:
        """Update session context based on new query and results."""
        
        # Update key concepts
        new_concepts = processed_query.keywords
        for concept in new_concepts:
            if concept not in session.session_context.key_concepts:
                session.session_context.key_concepts.append(concept)
        
        # Limit key concepts to prevent unbounded growth
        session.session_context.key_concepts = session.session_context.key_concepts[-20:]
        
        # Update research domain based on query patterns
        domain = self._infer_research_domain(processed_query, session.query_history)
        if domain:
            session.session_context.research_domain = domain
        
        # Update accumulated knowledge
        if research_report:
            for finding in research_report.key_findings:
                # Store findings with timestamp
                finding_key = f"finding_{len(session.session_context.accumulated_knowledge)}"
                session.session_context.accumulated_knowledge[finding_key] = {
                    'content': finding,
                    'query': original_query,
                    'timestamp': datetime.now().isoformat(),
                    'confidence': research_report.confidence_score
                }
        
        # Update query patterns
        query_pattern = self._extract_query_pattern(processed_query)
        if query_pattern not in session.session_context.query_patterns:
            session.session_context.query_patterns.append(query_pattern)
        
        # Limit patterns to prevent unbounded growth
        session.session_context.query_patterns = session.session_context.query_patterns[-10:]
    
    def _generate_follow_up_suggestions(self, 
                                      original_query: str,
                                      processed_query: ProcessedQuery,
                                      research_report: Optional[ResearchReport],
                                      session: ResearchSession) -> List[str]:
        """Generate follow-up query suggestions."""
        suggestions = []
        
        # Based on query type
        if processed_query.query_type.value == "comparative":
            suggestions.append("What are the practical implications of these differences?")
            suggestions.append("Which option would be better for specific use cases?")
        elif processed_query.query_type.value == "analytical":
            suggestions.append("What are the potential future developments in this area?")
            suggestions.append("How do these findings compare to industry standards?")
        
        # Based on keywords
        for keyword in processed_query.keywords[:2]:
            suggestions.append(f"Can you provide more details about {keyword}?")
            suggestions.append(f"What are the latest developments in {keyword}?")
        
        # Based on research report findings
        if research_report and research_report.key_findings:
            first_finding = research_report.key_findings[0]
            if len(first_finding) > 20:
                # Extract key terms from finding
                words = first_finding.split()[:5]
                key_phrase = " ".join(words)
                suggestions.append(f"Tell me more about {key_phrase}")
        
        # Based on session context
        if session.session_context.key_concepts:
            recent_concept = session.session_context.key_concepts[-1]
            suggestions.append(f"How does {recent_concept} relate to current trends?")
        
        # Limit suggestions
        return suggestions[:5]
    
    def _infer_research_domain(self, processed_query: ProcessedQuery, query_history: List[QueryHistory]) -> Optional[str]:
        """Infer research domain from query patterns."""
        
        # Domain keywords mapping
        domain_keywords = {
            'technology': ['software', 'algorithm', 'computer', 'digital', 'AI', 'machine learning'],
            'science': ['research', 'study', 'experiment', 'data', 'analysis', 'scientific'],
            'business': ['market', 'company', 'revenue', 'strategy', 'business', 'economic'],
            'health': ['medical', 'health', 'disease', 'treatment', 'patient', 'clinical'],
            'education': ['learning', 'education', 'student', 'teaching', 'academic'],
            'environment': ['climate', 'environment', 'sustainability', 'green', 'pollution']
        }
        
        # Count keyword matches
        all_keywords = processed_query.keywords.copy()
        
        # Add keywords from recent queries
        for query in query_history[-3:]:
            all_keywords.extend(query.processed_query.keywords)
        
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in all_keywords if any(dk in keyword.lower() for dk in keywords))
            if score > 0:
                domain_scores[domain] = score
        
        # Return domain with highest score
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        
        return None
    
    def _extract_query_pattern(self, processed_query: ProcessedQuery) -> str:
        """Extract pattern from processed query."""
        return f"{processed_query.query_type.value}_{len(processed_query.keywords)}_keywords"
    
    def _save_session(self, session: ResearchSession) -> None:
        """Save session to storage."""
        try:
            import os
            session_file = os.path.join(self.session_storage_path, f"{session.session_id}.json")
            
            # Convert session to dictionary for JSON serialization
            session_dict = asdict(session)
            
            # Handle datetime serialization
            session_dict['created_at'] = session.created_at.isoformat()
            session_dict['last_activity'] = session.last_activity.isoformat()
            session_dict['status'] = session.status.value
            
            # Handle query history serialization
            for i, query in enumerate(session_dict['query_history']):
                query['timestamp'] = session.query_history[i].timestamp.isoformat()
                # Remove complex objects that can't be serialized
                query['processed_query'] = None
                query['research_report'] = None
                query['reasoning_context'] = None
            
            with open(session_file, 'w') as f:
                json.dump(session_dict, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save session {session.session_id}: {e}")
    
    def _load_session(self, session_id: str) -> Optional[ResearchSession]:
        """Load session from storage."""
        try:
            import os
            session_file = os.path.join(self.session_storage_path, f"{session_id}.json")
            
            if not os.path.exists(session_file):
                return None
            
            with open(session_file, 'r') as f:
                session_dict = json.load(f)
            
            # Convert back to session object (simplified version)
            # Note: This is a basic implementation - full implementation would
            # need to handle all object reconstructions
            
            session = ResearchSession(
                session_id=session_dict['session_id'],
                user_id=session_dict.get('user_id'),
                title=session_dict['title'],
                description=session_dict['description'],
                status=SessionStatus(session_dict['status']),
                created_at=datetime.fromisoformat(session_dict['created_at']),
                last_activity=datetime.fromisoformat(session_dict['last_activity']),
                query_history=[],  # Simplified - would need full reconstruction
                session_context=SessionContext(**session_dict['session_context']),
                metadata=session_dict.get('metadata', {})
            )
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None
    
    def _load_sessions(self) -> None:
        """Load existing sessions from storage."""
        try:
            import os
            if not os.path.exists(self.session_storage_path):
                return
            
            for filename in os.listdir(self.session_storage_path):
                if filename.endswith('.json'):
                    session_id = filename[:-5]  # Remove .json extension
                    session = self._load_session(session_id)
                    if session and not session.is_expired(self.session_expiry_hours):
                        self.active_sessions[session_id] = session
            
            logger.info(f"Loaded {len(self.active_sessions)} active sessions")
            
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get statistics about all sessions."""
        total_sessions = len(self.active_sessions)
        
        if total_sessions == 0:
            return {'total_sessions': 0}
        
        total_queries = sum(len(session.query_history) for session in self.active_sessions.values())
        successful_queries = sum(len(session.get_successful_queries()) for session in self.active_sessions.values())
        
        return {
            'total_sessions': total_sessions,
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'average_queries_per_session': total_queries / total_sessions,
            'overall_success_rate': successful_queries / total_queries if total_queries > 0 else 0,
            'active_sessions': len([s for s in self.active_sessions.values() if s.status == SessionStatus.ACTIVE])
        }