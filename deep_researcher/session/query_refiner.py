"""Query refinement and suggestion engine for interactive research."""

from typing import List, Dict, Any, Optional, Tuple, Set
import logging
from dataclasses import dataclass
from enum import Enum
import re

from ..models import ProcessedQuery, QueryType, ResearchReport
from ..session.session_manager import ResearchSession, QueryHistory
from ..exceptions import QueryProcessingError

logger = logging.getLogger(__name__)


class RefinementType(Enum):
    """Types of query refinements."""
    CLARIFICATION = "clarification"
    EXPANSION = "expansion"
    NARROWING = "narrowing"
    ALTERNATIVE_ANGLE = "alternative_angle"
    FOLLOW_UP = "follow_up"
    RELATED_TOPIC = "related_topic"


@dataclass
class QuerySuggestion:
    """A suggested query refinement."""
    suggestion_id: str
    suggested_query: str
    refinement_type: RefinementType
    rationale: str
    confidence: float
    expected_improvement: str
    context_relevance: float


@dataclass
class RefinementAnalysis:
    """Analysis of how a query could be refined."""
    original_query: str
    issues_identified: List[str]
    improvement_opportunities: List[str]
    suggested_refinements: List[QuerySuggestion]
    session_context_used: bool
    confidence_in_analysis: float


class QueryRefiner:
    """Provides query refinement and suggestion capabilities."""
    
    def __init__(self):
        """Initialize query refiner."""
        
        # Patterns for identifying query issues
        self.vague_terms = {
            'thing', 'stuff', 'something', 'anything', 'everything', 'some', 'many', 'few',
            'good', 'bad', 'better', 'best', 'important', 'interesting', 'useful'
        }
        
        self.temporal_indicators = {
            'recent', 'current', 'modern', 'latest', 'new', 'old', 'historical',
            'future', 'upcoming', 'past', 'previous', 'today', 'now'
        }
        
        self.comparison_indicators = {
            'compare', 'versus', 'vs', 'difference', 'similar', 'different',
            'better', 'worse', 'best', 'worst', 'alternative'
        }
        
        # Domain-specific refinement templates
        self.refinement_templates = {
            'technology': {
                'expansion': [
                    "What are the technical specifications of {topic}?",
                    "How does {topic} compare to alternatives?",
                    "What are the implementation challenges of {topic}?",
                    "What are the security implications of {topic}?"
                ],
                'clarification': [
                    "Are you asking about {topic} for enterprise or personal use?",
                    "Do you want information about {topic} development or deployment?",
                    "Are you interested in open-source or commercial {topic} solutions?"
                ]
            },
            'science': {
                'expansion': [
                    "What is the current research status on {topic}?",
                    "What are the methodological approaches to studying {topic}?",
                    "What are the ethical considerations regarding {topic}?",
                    "How has understanding of {topic} evolved over time?"
                ],
                'clarification': [
                    "Are you looking for theoretical or applied research on {topic}?",
                    "Do you want peer-reviewed studies or general information about {topic}?",
                    "Are you interested in recent findings or historical perspective on {topic}?"
                ]
            },
            'business': {
                'expansion': [
                    "What are the market trends for {topic}?",
                    "What are the financial implications of {topic}?",
                    "How does {topic} affect different industries?",
                    "What are the regulatory considerations for {topic}?"
                ],
                'clarification': [
                    "Are you asking about {topic} from a startup or enterprise perspective?",
                    "Do you want strategic or operational information about {topic}?",
                    "Are you interested in B2B or B2C aspects of {topic}?"
                ]
            }
        }
    
    def analyze_query_for_refinement(self, 
                                   query: str,
                                   processed_query: Optional[ProcessedQuery] = None,
                                   session: Optional[ResearchSession] = None) -> RefinementAnalysis:
        """
        Analyze a query and suggest refinements.
        
        Args:
            query: Original query string
            processed_query: Optional processed query object
            session: Optional session context
            
        Returns:
            Analysis with refinement suggestions
        """
        try:
            logger.info(f"Analyzing query for refinement: {query[:50]}...")
            
            # Identify issues with the current query
            issues = self._identify_query_issues(query, processed_query)
            
            # Identify improvement opportunities
            opportunities = self._identify_improvement_opportunities(query, processed_query, session)
            
            # Generate refinement suggestions
            suggestions = self._generate_refinement_suggestions(query, processed_query, session, issues, opportunities)
            
            # Calculate confidence in analysis
            confidence = self._calculate_analysis_confidence(query, processed_query, session, suggestions)
            
            analysis = RefinementAnalysis(
                original_query=query,
                issues_identified=issues,
                improvement_opportunities=opportunities,
                suggested_refinements=suggestions,
                session_context_used=session is not None,
                confidence_in_analysis=confidence
            )
            
            logger.info(f"Generated {len(suggestions)} refinement suggestions")
            return analysis
            
        except Exception as e:
            logger.error(f"Query refinement analysis failed: {e}")
            raise QueryProcessingError(f"Query refinement analysis failed: {e}")
    
    def suggest_follow_up_queries(self, 
                                 research_report: ResearchReport,
                                 session: Optional[ResearchSession] = None) -> List[QuerySuggestion]:
        """
        Suggest follow-up queries based on research results.
        
        Args:
            research_report: Completed research report
            session: Optional session context
            
        Returns:
            List of follow-up query suggestions
        """
        try:
            suggestions = []
            
            # Based on key findings
            for i, finding in enumerate(research_report.key_findings[:3]):
                # Extract key concepts from finding
                key_concepts = self._extract_key_concepts_from_text(finding)
                
                for concept in key_concepts[:2]:
                    suggestions.append(QuerySuggestion(
                        suggestion_id=f"finding_{i}_{concept}",
                        suggested_query=f"Tell me more about {concept}",
                        refinement_type=RefinementType.FOLLOW_UP,
                        rationale=f"Explore the concept '{concept}' mentioned in the findings",
                        confidence=0.8,
                        expected_improvement="Deeper understanding of specific concepts",
                        context_relevance=0.9
                    ))
            
            # Based on confidence level
            if research_report.confidence_score < 0.7:
                suggestions.append(QuerySuggestion(
                    suggestion_id="low_confidence_refinement",
                    suggested_query=f"Can you provide more specific information about {research_report.query}?",
                    refinement_type=RefinementType.CLARIFICATION,
                    rationale="Low confidence suggests need for more specific query",
                    confidence=0.7,
                    expected_improvement="Higher confidence results with more specific information",
                    context_relevance=0.8
                ))
            
            # Based on source diversity
            synthesis_info = research_report.metadata.get('synthesis_info', {})
            if synthesis_info.get('source_diversity', 0) < 0.5:
                suggestions.append(QuerySuggestion(
                    suggestion_id="diversity_improvement",
                    suggested_query=f"What are different perspectives on {research_report.query}?",
                    refinement_type=RefinementType.ALTERNATIVE_ANGLE,
                    rationale="Limited source diversity suggests exploring different viewpoints",
                    confidence=0.6,
                    expected_improvement="More comprehensive and balanced analysis",
                    context_relevance=0.7
                ))
            
            # Based on session context
            if session:
                session_suggestions = self._generate_session_based_suggestions(research_report, session)
                suggestions.extend(session_suggestions)
            
            # Sort by relevance and confidence
            suggestions.sort(key=lambda x: x.context_relevance * x.confidence, reverse=True)
            
            return suggestions[:8]  # Limit to top 8 suggestions
            
        except Exception as e:
            logger.error(f"Follow-up suggestion generation failed: {e}")
            return []
    
    def refine_query_interactively(self, 
                                  original_query: str,
                                  user_feedback: Dict[str, Any],
                                  session: Optional[ResearchSession] = None) -> str:
        """
        Refine a query based on user feedback.
        
        Args:
            original_query: Original query string
            user_feedback: User feedback about what they want to change
            session: Optional session context
            
        Returns:
            Refined query string
        """
        try:
            refined_query = original_query
            
            # Handle different types of feedback
            if user_feedback.get('make_more_specific'):
                refined_query = self._make_query_more_specific(refined_query, user_feedback)
            
            if user_feedback.get('broaden_scope'):
                refined_query = self._broaden_query_scope(refined_query, user_feedback)
            
            if user_feedback.get('change_focus'):
                refined_query = self._change_query_focus(refined_query, user_feedback)
            
            if user_feedback.get('add_constraints'):
                refined_query = self._add_query_constraints(refined_query, user_feedback)
            
            if user_feedback.get('change_timeframe'):
                refined_query = self._change_query_timeframe(refined_query, user_feedback)
            
            # Use session context if available
            if session:
                refined_query = self._apply_session_context_to_refinement(refined_query, session)
            
            logger.info(f"Refined query: '{original_query}' -> '{refined_query}'")
            return refined_query
            
        except Exception as e:
            logger.error(f"Interactive query refinement failed: {e}")
            return original_query
    
    def _identify_query_issues(self, query: str, processed_query: Optional[ProcessedQuery]) -> List[str]:
        """Identify issues with the current query."""
        issues = []
        
        # Check for vague terms
        query_words = set(query.lower().split())
        vague_found = query_words.intersection(self.vague_terms)
        if vague_found:
            issues.append(f"Contains vague terms: {', '.join(vague_found)}")
        
        # Check query length
        if len(query.split()) < 3:
            issues.append("Query is very short and may lack specificity")
        elif len(query.split()) > 25:
            issues.append("Query is very long and may be too complex")
        
        # Check for missing question structure
        if not any(char in query for char in '?') and not any(word in query.lower() for word in ['what', 'how', 'why', 'when', 'where']):
            issues.append("Query lacks clear question structure")
        
        # Check for ambiguous pronouns
        pronouns = {'it', 'this', 'that', 'they', 'them'}
        if query_words.intersection(pronouns):
            issues.append("Contains ambiguous pronouns that may need clarification")
        
        # Check processed query issues
        if processed_query:
            if processed_query.complexity_score > 0.8:
                issues.append("Query complexity is very high, consider breaking into parts")
            
            if len(processed_query.keywords) < 2:
                issues.append("Few keywords identified, query may need more specific terms")
        
        return issues
    
    def _identify_improvement_opportunities(self, 
                                         query: str, 
                                         processed_query: Optional[ProcessedQuery],
                                         session: Optional[ResearchSession]) -> List[str]:
        """Identify opportunities to improve the query."""
        opportunities = []
        
        # Temporal specificity
        if any(term in query.lower() for term in self.temporal_indicators):
            opportunities.append("Could specify exact time periods for more precise results")
        
        # Comparison opportunities
        if any(term in query.lower() for term in self.comparison_indicators):
            opportunities.append("Could specify comparison criteria or dimensions")
        
        # Domain specificity
        if processed_query and processed_query.keywords:
            domain = self._infer_domain_from_keywords(processed_query.keywords)
            if domain:
                opportunities.append(f"Could add {domain}-specific context or constraints")
        
        # Scope clarification
        if 'all' in query.lower() or 'everything' in query.lower():
            opportunities.append("Could narrow scope to specific aspects or categories")
        
        # Perspective specification
        if not any(word in query.lower() for word in ['for', 'from', 'perspective', 'viewpoint']):
            opportunities.append("Could specify target audience or perspective")
        
        # Session-based opportunities
        if session and session.session_context.key_concepts:
            recent_concepts = session.session_context.key_concepts[-3:]
            if not any(concept in query.lower() for concept in recent_concepts):
                opportunities.append("Could relate to previously discussed concepts")
        
        return opportunities
    
    def _generate_refinement_suggestions(self, 
                                       query: str,
                                       processed_query: Optional[ProcessedQuery],
                                       session: Optional[ResearchSession],
                                       issues: List[str],
                                       opportunities: List[str]) -> List[QuerySuggestion]:
        """Generate specific refinement suggestions."""
        suggestions = []
        
        # Address vague terms
        if any("vague terms" in issue for issue in issues):
            suggestions.append(QuerySuggestion(
                suggestion_id="clarify_vague_terms",
                suggested_query=self._replace_vague_terms(query),
                refinement_type=RefinementType.CLARIFICATION,
                rationale="Replace vague terms with more specific language",
                confidence=0.8,
                expected_improvement="More precise and actionable results",
                context_relevance=0.9
            ))
        
        # Address short queries
        if any("very short" in issue for issue in issues):
            expanded_query = self._expand_short_query(query, processed_query, session)
            suggestions.append(QuerySuggestion(
                suggestion_id="expand_short_query",
                suggested_query=expanded_query,
                refinement_type=RefinementType.EXPANSION,
                rationale="Add more context and specific details to the query",
                confidence=0.7,
                expected_improvement="More comprehensive and relevant results",
                context_relevance=0.8
            ))
        
        # Address complex queries
        if any("very high" in issue for issue in issues):
            simplified_queries = self._break_down_complex_query(query, processed_query)
            for i, simple_query in enumerate(simplified_queries[:2]):
                suggestions.append(QuerySuggestion(
                    suggestion_id=f"simplify_complex_{i}",
                    suggested_query=simple_query,
                    refinement_type=RefinementType.NARROWING,
                    rationale=f"Focus on one aspect of the complex query (part {i+1})",
                    confidence=0.8,
                    expected_improvement="More focused and manageable analysis",
                    context_relevance=0.7
                ))
        
        # Add temporal specificity
        if any("time periods" in opp for opp in opportunities):
            temporal_query = self._add_temporal_specificity(query)
            suggestions.append(QuerySuggestion(
                suggestion_id="add_temporal_context",
                suggested_query=temporal_query,
                refinement_type=RefinementType.CLARIFICATION,
                rationale="Add specific time frame for more targeted results",
                confidence=0.7,
                expected_improvement="More current and relevant information",
                context_relevance=0.8
            ))
        
        # Add domain-specific context
        if processed_query and processed_query.keywords:
            domain = self._infer_domain_from_keywords(processed_query.keywords)
            if domain and domain in self.refinement_templates:
                domain_suggestions = self._generate_domain_specific_suggestions(query, domain, processed_query)
                suggestions.extend(domain_suggestions)
        
        # Session-based suggestions
        if session:
            session_suggestions = self._generate_session_context_suggestions(query, session)
            suggestions.extend(session_suggestions)
        
        return suggestions
    
    def _replace_vague_terms(self, query: str) -> str:
        """Replace vague terms with more specific alternatives."""
        replacements = {
            'thing': 'concept/technology/method',
            'stuff': 'materials/information/data',
            'good': 'effective/reliable/high-quality',
            'bad': 'ineffective/problematic/low-quality',
            'important': 'critical/essential/significant',
            'interesting': 'notable/relevant/significant'
        }
        
        words = query.split()
        for i, word in enumerate(words):
            if word.lower() in replacements:
                words[i] = replacements[word.lower()]
        
        return ' '.join(words)
    
    def _expand_short_query(self, 
                           query: str, 
                           processed_query: Optional[ProcessedQuery],
                           session: Optional[ResearchSession]) -> str:
        """Expand a short query with more context."""
        
        # Add question structure if missing
        if not query.endswith('?') and not any(word in query.lower() for word in ['what', 'how', 'why']):
            if processed_query and processed_query.query_type == QueryType.COMPARATIVE:
                query = f"How do {query} compare?"
            else:
                query = f"What should I know about {query}?"
        
        # Add context from session if available
        if session and session.session_context.research_domain != 'general':
            domain = session.session_context.research_domain
            query = f"In the context of {domain}, {query.lower()}"
        
        return query
    
    def _break_down_complex_query(self, 
                                 query: str, 
                                 processed_query: Optional[ProcessedQuery]) -> List[str]:
        """Break down a complex query into simpler parts."""
        
        # Simple approach: split on conjunctions
        parts = re.split(r'\b(?:and|also|additionally|furthermore)\b', query, flags=re.IGNORECASE)
        
        simplified_queries = []
        for part in parts:
            part = part.strip()
            if len(part) > 10:
                # Ensure it's a proper question
                if not part.endswith('?') and not any(word in part.lower() for word in ['what', 'how', 'why']):
                    part = f"What about {part}?"
                simplified_queries.append(part)
        
        # If no good splits found, create thematic splits
        if len(simplified_queries) <= 1 and processed_query:
            if processed_query.keywords:
                for keyword in processed_query.keywords[:2]:
                    simplified_queries.append(f"What is {keyword}?")
        
        return simplified_queries
    
    def _add_temporal_specificity(self, query: str) -> str:
        """Add temporal specificity to a query."""
        
        # Check if query already has temporal context
        if any(term in query.lower() for term in ['2020', '2021', '2022', '2023', '2024', 'recent', 'current']):
            return query
        
        # Add current year context
        current_year = datetime.now().year
        
        if 'trend' in query.lower() or 'development' in query.lower():
            return f"{query} in {current_year}"
        else:
            return f"{query} (current as of {current_year})"
    
    def _generate_domain_specific_suggestions(self, 
                                            query: str, 
                                            domain: str,
                                            processed_query: ProcessedQuery) -> List[QuerySuggestion]:
        """Generate domain-specific refinement suggestions."""
        suggestions = []
        
        if domain not in self.refinement_templates:
            return suggestions
        
        templates = self.refinement_templates[domain]
        main_topic = processed_query.keywords[0] if processed_query.keywords else "the topic"
        
        # Generate expansion suggestions
        for template in templates.get('expansion', [])[:2]:
            suggested_query = template.format(topic=main_topic)
            suggestions.append(QuerySuggestion(
                suggestion_id=f"domain_expansion_{domain}",
                suggested_query=suggested_query,
                refinement_type=RefinementType.EXPANSION,
                rationale=f"Explore {domain}-specific aspects of the topic",
                confidence=0.7,
                expected_improvement=f"More detailed {domain} perspective",
                context_relevance=0.8
            ))
        
        # Generate clarification suggestions
        for template in templates.get('clarification', [])[:1]:
            suggested_query = template.format(topic=main_topic)
            suggestions.append(QuerySuggestion(
                suggestion_id=f"domain_clarification_{domain}",
                suggested_query=suggested_query,
                refinement_type=RefinementType.CLARIFICATION,
                rationale=f"Clarify {domain}-specific context",
                confidence=0.6,
                expected_improvement="More targeted and relevant results",
                context_relevance=0.7
            ))
        
        return suggestions
    
    def _generate_session_context_suggestions(self, 
                                            query: str,
                                            session: ResearchSession) -> List[QuerySuggestion]:
        """Generate suggestions based on session context."""
        suggestions = []
        
        # Based on previous queries
        if session.query_history:
            recent_query = session.query_history[-1]
            if recent_query.success and recent_query.research_report:
                # Suggest connecting to previous findings
                suggestions.append(QuerySuggestion(
                    suggestion_id="connect_to_previous",
                    suggested_query=f"How does {query} relate to {recent_query.original_query}?",
                    refinement_type=RefinementType.RELATED_TOPIC,
                    rationale="Connect current query to previous research",
                    confidence=0.6,
                    expected_improvement="Better context and continuity",
                    context_relevance=0.9
                ))
        
        # Based on key concepts
        if session.session_context.key_concepts:
            recent_concept = session.session_context.key_concepts[-1]
            if recent_concept.lower() not in query.lower():
                suggestions.append(QuerySuggestion(
                    suggestion_id="include_session_concept",
                    suggested_query=f"{query} in relation to {recent_concept}",
                    refinement_type=RefinementType.EXPANSION,
                    rationale=f"Include previously discussed concept: {recent_concept}",
                    confidence=0.7,
                    expected_improvement="Leverage accumulated session knowledge",
                    context_relevance=0.8
                ))
        
        return suggestions
    
    def _generate_session_based_suggestions(self, 
                                          research_report: ResearchReport,
                                          session: ResearchSession) -> List[QuerySuggestion]:
        """Generate follow-up suggestions based on session history."""
        suggestions = []
        
        # Look for patterns in successful queries
        successful_queries = session.get_successful_queries()
        if len(successful_queries) > 1:
            # Find common themes
            all_keywords = []
            for query_hist in successful_queries:
                all_keywords.extend(query_hist.processed_query.keywords)
            
            # Find most common keywords not in current report
            from collections import Counter
            keyword_counts = Counter(all_keywords)
            current_keywords = set(kw.lower() for kw in research_report.query.split())
            
            for keyword, count in keyword_counts.most_common(3):
                if keyword.lower() not in current_keywords and count > 1:
                    suggestions.append(QuerySuggestion(
                        suggestion_id=f"session_pattern_{keyword}",
                        suggested_query=f"How does {keyword} relate to {research_report.query}?",
                        refinement_type=RefinementType.RELATED_TOPIC,
                        rationale=f"Explore connection to frequently discussed topic: {keyword}",
                        confidence=0.6,
                        expected_improvement="Leverage session learning patterns",
                        context_relevance=0.7
                    ))
        
        return suggestions
    
    def _make_query_more_specific(self, query: str, feedback: Dict[str, Any]) -> str:
        """Make a query more specific based on user feedback."""
        specific_aspects = feedback.get('specific_aspects', [])
        
        if specific_aspects:
            aspects_str = ', '.join(specific_aspects)
            return f"{query}, specifically focusing on {aspects_str}"
        
        return f"{query} (please provide specific details)"
    
    def _broaden_query_scope(self, query: str, feedback: Dict[str, Any]) -> str:
        """Broaden the scope of a query."""
        return f"What are all the aspects and implications of {query}?"
    
    def _change_query_focus(self, query: str, feedback: Dict[str, Any]) -> str:
        """Change the focus of a query."""
        new_focus = feedback.get('new_focus', 'general overview')
        return f"From a {new_focus} perspective, {query.lower()}"
    
    def _add_query_constraints(self, query: str, feedback: Dict[str, Any]) -> str:
        """Add constraints to a query."""
        constraints = feedback.get('constraints', [])
        
        if constraints:
            constraints_str = ', '.join(constraints)
            return f"{query}, considering constraints: {constraints_str}"
        
        return query
    
    def _change_query_timeframe(self, query: str, feedback: Dict[str, Any]) -> str:
        """Change the timeframe of a query."""
        timeframe = feedback.get('timeframe', 'current')
        
        if timeframe == 'historical':
            return f"Historical perspective on {query.lower()}"
        elif timeframe == 'future':
            return f"Future outlook and predictions for {query.lower()}"
        elif timeframe == 'recent':
            return f"Recent developments in {query.lower()}"
        
        return query
    
    def _apply_session_context_to_refinement(self, query: str, session: ResearchSession) -> str:
        """Apply session context to refine a query."""
        
        # Add domain context if relevant
        if session.session_context.research_domain != 'general':
            domain = session.session_context.research_domain
            if domain not in query.lower():
                query = f"In the context of {domain}, {query.lower()}"
        
        return query
    
    def _extract_key_concepts_from_text(self, text: str) -> List[str]:
        """Extract key concepts from text."""
        # Simple extraction - could be improved with NLP
        words = re.findall(r'\b[A-Za-z]{4,}\b', text)
        
        # Filter out common words
        stop_words = {'that', 'this', 'with', 'from', 'they', 'have', 'been', 'were', 'said', 'each', 'which', 'their', 'time', 'will', 'about', 'would', 'there', 'could', 'other', 'more', 'very', 'what', 'know', 'just', 'first', 'into', 'over', 'think', 'also', 'your', 'work', 'life', 'only', 'can', 'still', 'should', 'after', 'being', 'now', 'made', 'before', 'here', 'through', 'when', 'where', 'much', 'some', 'these', 'many', 'then', 'them', 'well', 'were'}
        
        key_concepts = [word for word in words if word.lower() not in stop_words]
        
        # Return most frequent concepts
        from collections import Counter
        concept_counts = Counter(key_concepts)
        return [concept for concept, count in concept_counts.most_common(5)]
    
    def _infer_domain_from_keywords(self, keywords: List[str]) -> Optional[str]:
        """Infer domain from keywords."""
        domain_indicators = {
            'technology': ['software', 'algorithm', 'computer', 'digital', 'programming', 'AI', 'machine', 'data'],
            'science': ['research', 'study', 'experiment', 'analysis', 'scientific', 'theory', 'hypothesis'],
            'business': ['market', 'company', 'revenue', 'strategy', 'business', 'economic', 'financial'],
            'health': ['medical', 'health', 'disease', 'treatment', 'patient', 'clinical', 'therapy'],
            'education': ['learning', 'education', 'student', 'teaching', 'academic', 'school', 'university']
        }
        
        keyword_lower = [kw.lower() for kw in keywords]
        
        for domain, indicators in domain_indicators.items():
            if any(indicator in ' '.join(keyword_lower) for indicator in indicators):
                return domain
        
        return None
    
    def _calculate_analysis_confidence(self, 
                                     query: str,
                                     processed_query: Optional[ProcessedQuery],
                                     session: Optional[ResearchSession],
                                     suggestions: List[QuerySuggestion]) -> float:
        """Calculate confidence in the refinement analysis."""
        confidence = 0.5  # Base confidence
        
        # Boost for processed query availability
        if processed_query:
            confidence += 0.2
        
        # Boost for session context
        if session and session.query_history:
            confidence += 0.1
        
        # Boost for number of suggestions generated
        if len(suggestions) > 3:
            confidence += 0.1
        
        # Boost for query clarity
        if len(query.split()) > 5 and any(char in query for char in '?'):
            confidence += 0.1
        
        return min(1.0, confidence)