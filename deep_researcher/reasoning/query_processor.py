"""Query processing and analysis functionality."""

import re
from typing import List, Dict, Any, Optional, Set
import logging
from dataclasses import dataclass

from ..models import ProcessedQuery, QueryType
from ..interfaces import QueryProcessorInterface
from ..exceptions import QueryProcessingError

logger = logging.getLogger(__name__)


@dataclass
class QueryFeatures:
    """Features extracted from a query for analysis."""
    word_count: int
    question_words: List[str]
    comparison_words: List[str]
    temporal_words: List[str]
    analytical_words: List[str]
    entities: List[str]
    has_multiple_questions: bool
    has_conjunctions: bool
    complexity_indicators: List[str]


class QueryProcessor(QueryProcessorInterface):
    """Processes and analyzes research queries."""
    
    # Query analysis patterns and keywords
    QUESTION_WORDS = {
        'what', 'how', 'why', 'when', 'where', 'who', 'which', 'whose',
        'can', 'could', 'should', 'would', 'will', 'do', 'does', 'did',
        'is', 'are', 'was', 'were', 'has', 'have', 'had'
    }
    
    COMPARISON_WORDS = {
        'compare', 'contrast', 'versus', 'vs', 'difference', 'similar',
        'different', 'better', 'worse', 'best', 'worst', 'more', 'less',
        'between', 'among', 'rather than', 'instead of', 'alternative'
    }
    
    TEMPORAL_WORDS = {
        'when', 'before', 'after', 'during', 'since', 'until', 'while',
        'history', 'historical', 'evolution', 'development', 'timeline',
        'past', 'present', 'future', 'recent', 'current', 'modern'
    }
    
    ANALYTICAL_WORDS = {
        'analyze', 'analysis', 'evaluate', 'assessment', 'examine',
        'investigate', 'study', 'research', 'explore', 'understand',
        'explain', 'describe', 'discuss', 'review', 'summarize',
        'implications', 'impact', 'effect', 'cause', 'reason'
    }
    
    COMPLEXITY_INDICATORS = {
        'comprehensive', 'detailed', 'thorough', 'in-depth', 'extensive',
        'complete', 'full', 'entire', 'all aspects', 'multiple',
        'various', 'different', 'several', 'many', 'numerous'
    }
    
    CONJUNCTIONS = {
        'and', 'or', 'but', 'however', 'moreover', 'furthermore',
        'additionally', 'also', 'plus', 'as well as', 'along with'
    }
    
    def __init__(self):
        """Initialize query processor."""
        self.entity_patterns = [
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Proper names
            r'\b[A-Z]{2,}\b',  # Acronyms
            r'\b\d{4}\b',  # Years
            r'\$\d+(?:,\d{3})*(?:\.\d{2})?\b',  # Money amounts
            r'\b\d+(?:\.\d+)?%\b'  # Percentages
        ]
    
    def process_query(self, query: str) -> ProcessedQuery:
        """
        Process and analyze a query.
        
        Args:
            query: Raw query string
            
        Returns:
            ProcessedQuery object with analysis results
        """
        if not query or not query.strip():
            raise QueryProcessingError("Query cannot be empty")
        
        try:
            # Clean and normalize query
            cleaned_query = self._clean_query(query)
            
            # Extract features
            features = self._extract_features(cleaned_query)
            
            # Classify query type
            query_type = self._classify_query_type(cleaned_query, features)
            
            # Calculate complexity score
            complexity_score = self._calculate_complexity(features)
            
            # Generate sub-queries for complex queries
            sub_queries = self._generate_sub_queries(cleaned_query, features, query_type)
            
            # Extract keywords
            keywords = self._extract_keywords(cleaned_query, features)
            
            # Estimate expected sources
            expected_sources = self._estimate_expected_sources(complexity_score, query_type)
            
            processed_query = ProcessedQuery(
                original_query=query,
                query_type=query_type,
                complexity_score=complexity_score,
                sub_queries=sub_queries,
                expected_sources=expected_sources,
                keywords=keywords,
                metadata={
                    'features': features.__dict__,
                    'cleaned_query': cleaned_query,
                    'word_count': features.word_count
                }
            )
            
            logger.info(f"Processed query: type={query_type.value}, complexity={complexity_score:.2f}")
            return processed_query
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            raise QueryProcessingError(f"Failed to process query: {e}")
    
    def classify_query_type(self, query: str) -> str:
        """
        Classify the type of query.
        
        Args:
            query: Query string to classify
            
        Returns:
            Query type as string
        """
        try:
            cleaned_query = self._clean_query(query)
            features = self._extract_features(cleaned_query)
            query_type = self._classify_query_type(cleaned_query, features)
            return query_type.value
        except Exception as e:
            logger.error(f"Query classification failed: {e}")
            return QueryType.SIMPLE.value
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize query text."""
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Normalize punctuation
        query = re.sub(r'[^\w\s\?\!\.\,\;\:\-\(\)]', ' ', query)
        
        # Remove excessive punctuation
        query = re.sub(r'[\.]{2,}', '.', query)
        query = re.sub(r'[\?]{2,}', '?', query)
        query = re.sub(r'[\!]{2,}', '!', query)
        
        return query.strip()
    
    def _extract_features(self, query: str) -> QueryFeatures:
        """Extract features from the query for analysis."""
        words = query.lower().split()
        word_count = len(words)
        
        # Find question words
        question_words = [w for w in words if w in self.QUESTION_WORDS]
        
        # Find comparison words
        comparison_words = [w for w in words if w in self.COMPARISON_WORDS]
        
        # Find temporal words
        temporal_words = [w for w in words if w in self.TEMPORAL_WORDS]
        
        # Find analytical words
        analytical_words = [w for w in words if w in self.ANALYTICAL_WORDS]
        
        # Find complexity indicators
        complexity_indicators = [w for w in words if w in self.COMPLEXITY_INDICATORS]
        
        # Check for multiple questions
        has_multiple_questions = query.count('?') > 1 or len(re.findall(r'\b(?:and|also|additionally)\s+(?:what|how|why)', query.lower())) > 0
        
        # Check for conjunctions
        has_conjunctions = any(conj in query.lower() for conj in self.CONJUNCTIONS)
        
        # Extract entities
        entities = self._extract_entities(query)
        
        return QueryFeatures(
            word_count=word_count,
            question_words=question_words,
            comparison_words=comparison_words,
            temporal_words=temporal_words,
            analytical_words=analytical_words,
            entities=entities,
            has_multiple_questions=has_multiple_questions,
            has_conjunctions=has_conjunctions,
            complexity_indicators=complexity_indicators
        )
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract named entities and important terms from query."""
        entities = []
        
        for pattern in self.entity_patterns:
            matches = re.findall(pattern, query)
            entities.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity.lower() not in seen:
                seen.add(entity.lower())
                unique_entities.append(entity)
        
        return unique_entities
    
    def _classify_query_type(self, query: str, features: QueryFeatures) -> QueryType:
        """Classify the query type based on features."""
        
        # Check for comparative queries
        if (len(features.comparison_words) > 0 or 
            'vs' in query.lower() or 
            'versus' in query.lower() or
            re.search(r'\b(?:difference|compare|contrast)\b', query.lower())):
            return QueryType.COMPARATIVE
        
        # Check for analytical queries
        if (len(features.analytical_words) > 0 or
            any(word in query.lower() for word in ['analyze', 'evaluate', 'assess', 'examine'])):
            return QueryType.ANALYTICAL
        
        # Check for multi-part queries
        if (features.has_multiple_questions or
            len(features.question_words) > 2 or
            features.word_count > 20):
            return QueryType.MULTI_PART
        
        # Check for complex queries
        if (features.word_count > 15 or
            len(features.complexity_indicators) > 0 or
            features.has_conjunctions):
            return QueryType.COMPLEX
        
        # Default to simple
        return QueryType.SIMPLE
    
    def _calculate_complexity(self, features: QueryFeatures) -> float:
        """Calculate complexity score based on query features."""
        score = 0.0
        
        # Base score from word count
        if features.word_count > 20:
            score += 0.4
        elif features.word_count > 10:
            score += 0.2
        
        # Question complexity
        if len(features.question_words) > 2:
            score += 0.2
        elif len(features.question_words) > 1:
            score += 0.1
        
        # Comparison complexity
        if len(features.comparison_words) > 0:
            score += 0.2
        
        # Analytical complexity
        if len(features.analytical_words) > 0:
            score += 0.2
        
        # Multiple questions
        if features.has_multiple_questions:
            score += 0.3
        
        # Conjunctions indicate complex relationships
        if features.has_conjunctions:
            score += 0.1
        
        # Complexity indicators
        if len(features.complexity_indicators) > 0:
            score += 0.2
        
        # Entities add complexity
        if len(features.entities) > 2:
            score += 0.1
        
        # Temporal aspects
        if len(features.temporal_words) > 0:
            score += 0.1
        
        # Clamp to [0, 1]
        return min(1.0, score)
    
    def _generate_sub_queries(self, query: str, features: QueryFeatures, query_type: QueryType) -> List[str]:
        """Generate sub-queries for complex queries."""
        sub_queries = []
        
        if query_type == QueryType.SIMPLE:
            return sub_queries
        
        # Split on conjunctions for multi-part queries
        if features.has_conjunctions or features.has_multiple_questions:
            # Split on common conjunctions
            parts = re.split(r'\b(?:and|also|additionally|furthermore|moreover)\b', query, flags=re.IGNORECASE)
            
            for part in parts:
                part = part.strip()
                if len(part) > 10 and any(qw in part.lower() for qw in self.QUESTION_WORDS):
                    sub_queries.append(part)
        
        # For comparative queries, create comparison sub-queries
        if query_type == QueryType.COMPARATIVE:
            entities = features.entities
            if len(entities) >= 2:
                sub_queries.extend([
                    f"What is {entities[0]}?",
                    f"What is {entities[1]}?",
                    f"How do {entities[0]} and {entities[1]} differ?"
                ])
        
        # For analytical queries, break down into components
        if query_type == QueryType.ANALYTICAL:
            if 'impact' in query.lower() or 'effect' in query.lower():
                sub_queries.extend([
                    "What are the main factors involved?",
                    "What are the direct effects?",
                    "What are the indirect consequences?"
                ])
        
        # Remove duplicates and empty queries
        sub_queries = [sq for sq in sub_queries if sq.strip()]
        return list(dict.fromkeys(sub_queries))  # Remove duplicates while preserving order
    
    def _extract_keywords(self, query: str, features: QueryFeatures) -> List[str]:
        """Extract important keywords from the query."""
        # Start with entities
        keywords = features.entities.copy()
        
        # Add important words (excluding stop words)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
        important_words = [w for w in words if w not in stop_words and w not in self.QUESTION_WORDS]
        
        # Add words that appear multiple times
        word_counts = {}
        for word in important_words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Add frequent words and unique important words
        for word, count in word_counts.items():
            if count > 1 or len(word) > 6:  # Frequent or long words
                if word not in [kw.lower() for kw in keywords]:
                    keywords.append(word)
        
        # Limit keywords
        return keywords[:10]
    
    def _estimate_expected_sources(self, complexity_score: float, query_type: QueryType) -> int:
        """Estimate number of sources needed based on query complexity."""
        base_sources = 5
        
        # Adjust based on complexity
        if complexity_score > 0.8:
            base_sources = 15
        elif complexity_score > 0.6:
            base_sources = 10
        elif complexity_score > 0.4:
            base_sources = 8
        
        # Adjust based on query type
        type_multipliers = {
            QueryType.SIMPLE: 1.0,
            QueryType.COMPLEX: 1.2,
            QueryType.MULTI_PART: 1.5,
            QueryType.COMPARATIVE: 1.3,
            QueryType.ANALYTICAL: 1.4
        }
        
        multiplier = type_multipliers.get(query_type, 1.0)
        return max(3, min(20, int(base_sources * multiplier)))
    
    def get_query_suggestions(self, query: str) -> List[str]:
        """
        Generate query suggestions for refinement.
        
        Args:
            query: Original query
            
        Returns:
            List of suggested refined queries
        """
        try:
            features = self._extract_features(self._clean_query(query))
            suggestions = []
            
            # Suggest more specific queries
            if features.word_count < 5:
                suggestions.append(f"Can you provide more specific details about {query}?")
                suggestions.append(f"What are the key aspects of {query}?")
            
            # Suggest breaking down complex queries
            if features.word_count > 20:
                suggestions.append("Consider breaking this into smaller, more focused questions")
                if features.entities:
                    suggestions.append(f"Focus on one aspect, such as {features.entities[0]}")
            
            # Suggest comparative analysis
            if len(features.entities) > 1:
                suggestions.append(f"Compare {features.entities[0]} and {features.entities[1]}")
            
            # Suggest temporal refinement
            if features.temporal_words:
                suggestions.append("Specify a time period for more focused results")
            
            return suggestions[:5]  # Limit suggestions
            
        except Exception as e:
            logger.error(f"Failed to generate query suggestions: {e}")
            return []
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Validate query and provide feedback.
        
        Args:
            query: Query to validate
            
        Returns:
            Validation results with suggestions
        """
        try:
            validation = {
                'is_valid': True,
                'issues': [],
                'suggestions': []
            }
            
            if not query or not query.strip():
                validation['is_valid'] = False
                validation['issues'].append("Query is empty")
                return validation
            
            cleaned_query = self._clean_query(query)
            features = self._extract_features(cleaned_query)
            
            # Check for very short queries
            if features.word_count < 3:
                validation['issues'].append("Query is very short")
                validation['suggestions'].append("Add more descriptive words")
            
            # Check for very long queries
            if features.word_count > 50:
                validation['issues'].append("Query is very long")
                validation['suggestions'].append("Consider breaking into multiple queries")
            
            # Check for question words
            if not features.question_words and not any(char in query for char in '?'):
                validation['suggestions'].append("Consider phrasing as a question")
            
            # Check for vague terms
            vague_terms = ['thing', 'stuff', 'something', 'anything', 'everything']
            if any(term in cleaned_query.lower() for term in vague_terms):
                validation['issues'].append("Query contains vague terms")
                validation['suggestions'].append("Use more specific terminology")
            
            return validation
            
        except Exception as e:
            logger.error(f"Query validation failed: {e}")
            return {
                'is_valid': False,
                'issues': [f"Validation error: {e}"],
                'suggestions': []
            }