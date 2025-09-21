"""Result synthesis and information combination functionality."""

import re
from typing import List, Dict, Any, Optional, Set, Tuple
import logging
from dataclasses import dataclass
from collections import Counter, defaultdict
from datetime import datetime

from ..models import Document, ReasoningStep, ResearchReport
from ..interfaces import ResultSynthesizerInterface
from ..exceptions import SynthesisError

logger = logging.getLogger(__name__)


@dataclass
class SourceEvidence:
    """Evidence from a source document."""
    document_id: str
    content: str
    confidence: float
    relevance_score: float
    source_quality: float
    extraction_method: str


@dataclass
class ConflictInfo:
    """Information about conflicting evidence."""
    topic: str
    conflicting_sources: List[SourceEvidence]
    conflict_type: str  # "contradiction", "inconsistency", "ambiguity"
    resolution_strategy: str
    confidence_in_resolution: float


@dataclass
class SynthesisResult:
    """Result of information synthesis."""
    main_findings: List[str]
    supporting_evidence: List[SourceEvidence]
    conflicts: List[ConflictInfo]
    confidence_score: float
    source_diversity: float
    completeness_score: float


class ResultSynthesizer(ResultSynthesizerInterface):
    """Synthesizes research results from multiple sources."""
    
    def __init__(self):
        """Initialize result synthesizer."""
        # Patterns for identifying different types of statements
        self.fact_patterns = [
            r'\b(?:is|are|was|were|has|have|had)\b',
            r'\b(?:according to|research shows|studies indicate)\b',
            r'\b(?:data shows|statistics reveal|evidence suggests)\b'
        ]
        
        self.opinion_patterns = [
            r'\b(?:believe|think|feel|opinion|view|perspective)\b',
            r'\b(?:argue|claim|suggest|propose|recommend)\b',
            r'\b(?:might|could|may|possibly|potentially)\b'
        ]
        
        self.temporal_patterns = [
            r'\b(?:in \d{4}|since \d{4}|by \d{4}|during \d{4})\b',
            r'\b(?:recently|currently|now|today|yesterday)\b',
            r'\b(?:future|will|going to|expected to)\b'
        ]
        
        # Conflict detection patterns
        self.contradiction_indicators = [
            r'\b(?:however|but|although|despite|contrary to)\b',
            r'\b(?:not|no|never|none|neither)\b',
            r'\b(?:different|opposite|contradicts|disagrees)\b'
        ]
    
    def synthesize_results(self, 
                          documents: List[Document], 
                          query: str,
                          reasoning_steps: List[ReasoningStep]) -> ResearchReport:
        """
        Synthesize research results from multiple sources.
        
        Args:
            documents: Source documents
            query: Original research query
            reasoning_steps: Reasoning steps that were executed
            
        Returns:
            Complete research report
        """
        try:
            logger.info(f"Synthesizing results from {len(documents)} documents")
            
            # Extract evidence from all sources
            evidence_list = self._extract_evidence_from_documents(documents, query)
            
            # Group evidence by topics/themes
            topic_groups = self._group_evidence_by_topics(evidence_list)
            
            # Detect and resolve conflicts
            conflicts = self._detect_conflicts(topic_groups)
            resolved_conflicts = self._resolve_conflicts(conflicts)
            
            # Generate main findings
            main_findings = self._generate_main_findings(topic_groups, resolved_conflicts)
            
            # Calculate confidence and quality scores
            confidence_score = self._calculate_overall_confidence(evidence_list, resolved_conflicts)
            
            # Generate summary
            summary = self._generate_summary(main_findings, query)
            
            # Create research report
            report = ResearchReport(
                query=query,
                summary=summary,
                key_findings=main_findings,
                sources=documents,
                reasoning_steps=reasoning_steps,
                confidence_score=confidence_score,
                metadata={
                    'synthesis_info': {
                        'total_evidence_pieces': len(evidence_list),
                        'topic_groups': len(topic_groups),
                        'conflicts_detected': len(conflicts),
                        'conflicts_resolved': len(resolved_conflicts),
                        'source_diversity': self._calculate_source_diversity(documents),
                        'completeness_score': self._calculate_completeness_score(evidence_list, query)
                    }
                }
            )
            
            logger.info(f"Synthesis completed: {len(main_findings)} findings, "
                       f"confidence={confidence_score:.2f}")
            
            return report
            
        except Exception as e:
            logger.error(f"Result synthesis failed: {e}")
            raise SynthesisError(f"Result synthesis failed: {e}")
    
    def resolve_conflicts(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Identify and resolve conflicting information.
        
        Args:
            documents: Documents to analyze for conflicts
            
        Returns:
            Dictionary with conflict analysis results
        """
        try:
            # Extract evidence
            evidence_list = self._extract_evidence_from_documents(documents, "")
            
            # Group by topics
            topic_groups = self._group_evidence_by_topics(evidence_list)
            
            # Detect conflicts
            conflicts = self._detect_conflicts(topic_groups)
            
            # Resolve conflicts
            resolved_conflicts = self._resolve_conflicts(conflicts)
            
            return {
                'total_conflicts': len(conflicts),
                'resolved_conflicts': len(resolved_conflicts),
                'conflict_types': Counter([c.conflict_type for c in conflicts]),
                'resolution_strategies': Counter([c.resolution_strategy for c in resolved_conflicts]),
                'average_resolution_confidence': sum(c.confidence_in_resolution for c in resolved_conflicts) / len(resolved_conflicts) if resolved_conflicts else 0,
                'conflicts_by_topic': {c.topic: c.conflict_type for c in conflicts}
            }
            
        except Exception as e:
            logger.error(f"Conflict resolution failed: {e}")
            raise SynthesisError(f"Conflict resolution failed: {e}")
    
    def _extract_evidence_from_documents(self, documents: List[Document], query: str) -> List[SourceEvidence]:
        """Extract evidence pieces from documents."""
        evidence_list = []
        query_keywords = set(query.lower().split()) if query else set()
        
        for doc in documents:
            # Split content into sentences/paragraphs
            sentences = self._split_into_sentences(doc.content)
            
            for sentence in sentences:
                if len(sentence.strip()) < 20:  # Skip very short sentences
                    continue
                
                # Calculate relevance to query
                relevance = self._calculate_sentence_relevance(sentence, query_keywords)
                
                if relevance > 0.1:  # Only include somewhat relevant sentences
                    # Determine extraction method and confidence
                    extraction_method = self._classify_statement_type(sentence)
                    confidence = self._calculate_statement_confidence(sentence, doc)
                    source_quality = self._assess_source_quality(doc)
                    
                    evidence = SourceEvidence(
                        document_id=doc.id,
                        content=sentence.strip(),
                        confidence=confidence,
                        relevance_score=relevance,
                        source_quality=source_quality,
                        extraction_method=extraction_method
                    )
                    evidence_list.append(evidence)
        
        # Sort by relevance and confidence
        evidence_list.sort(key=lambda x: x.relevance_score * x.confidence, reverse=True)
        
        return evidence_list
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting - could be improved with NLP libraries
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _calculate_sentence_relevance(self, sentence: str, query_keywords: Set[str]) -> float:
        """Calculate how relevant a sentence is to the query."""
        if not query_keywords:
            return 0.5  # Default relevance when no query
        
        sentence_words = set(sentence.lower().split())
        
        # Calculate keyword overlap
        overlap = len(query_keywords.intersection(sentence_words))
        relevance = overlap / len(query_keywords) if query_keywords else 0
        
        # Boost for exact phrase matches
        sentence_lower = sentence.lower()
        for keyword in query_keywords:
            if keyword in sentence_lower:
                relevance += 0.1
        
        return min(1.0, relevance)
    
    def _classify_statement_type(self, sentence: str) -> str:
        """Classify the type of statement (fact, opinion, etc.)."""
        sentence_lower = sentence.lower()
        
        # Check for factual patterns
        for pattern in self.fact_patterns:
            if re.search(pattern, sentence_lower):
                return "factual"
        
        # Check for opinion patterns
        for pattern in self.opinion_patterns:
            if re.search(pattern, sentence_lower):
                return "opinion"
        
        # Check for temporal information
        for pattern in self.temporal_patterns:
            if re.search(pattern, sentence_lower):
                return "temporal"
        
        return "general"
    
    def _calculate_statement_confidence(self, sentence: str, document: Document) -> float:
        """Calculate confidence in a statement."""
        confidence = 0.5  # Base confidence
        
        # Boost for factual language
        if any(word in sentence.lower() for word in ['research', 'study', 'data', 'evidence']):
            confidence += 0.2
        
        # Boost for specific numbers/statistics
        if re.search(r'\d+(?:\.\d+)?%|\d+(?:,\d{3})*', sentence):
            confidence += 0.1
        
        # Reduce for uncertain language
        if any(word in sentence.lower() for word in ['might', 'could', 'possibly', 'perhaps']):
            confidence -= 0.1
        
        # Boost for authoritative sources (based on document metadata)
        if document.metadata.get('author') or document.metadata.get('publisher'):
            confidence += 0.1
        
        return max(0.1, min(1.0, confidence))
    
    def _assess_source_quality(self, document: Document) -> float:
        """Assess the quality of a source document."""
        quality = 0.5  # Base quality
        
        # Length-based quality
        if 500 <= document.word_count <= 10000:
            quality += 0.2
        elif document.word_count > 100:
            quality += 0.1
        
        # Structure quality
        if document.title and len(document.title) > 10:
            quality += 0.1
        
        # Metadata richness
        if document.metadata:
            quality += min(0.2, len(document.metadata) * 0.05)
        
        # Format quality (some formats are more reliable)
        format_scores = {
            'pdf': 0.2,
            'docx': 0.15,
            'md': 0.1,
            'txt': 0.05,
            'html': 0.05
        }
        quality += format_scores.get(document.format_type.value, 0)
        
        return max(0.1, min(1.0, quality))
    
    def _group_evidence_by_topics(self, evidence_list: List[SourceEvidence]) -> Dict[str, List[SourceEvidence]]:
        """Group evidence by topics/themes."""
        topic_groups = defaultdict(list)
        
        # Simple topic extraction based on keywords
        for evidence in evidence_list:
            topics = self._extract_topics_from_text(evidence.content)
            
            if not topics:
                topics = ['general']
            
            for topic in topics:
                topic_groups[topic].append(evidence)
        
        return dict(topic_groups)
    
    def _extract_topics_from_text(self, text: str) -> List[str]:
        """Extract topics/themes from text."""
        # Simple keyword-based topic extraction
        # In a full implementation, this could use more sophisticated NLP
        
        topics = []
        text_lower = text.lower()
        
        # Define topic keywords
        topic_keywords = {
            'technology': ['technology', 'software', 'computer', 'digital', 'algorithm'],
            'science': ['research', 'study', 'experiment', 'data', 'analysis'],
            'business': ['company', 'market', 'business', 'revenue', 'profit'],
            'health': ['health', 'medical', 'disease', 'treatment', 'patient'],
            'education': ['education', 'learning', 'student', 'school', 'university'],
            'environment': ['environment', 'climate', 'pollution', 'sustainability'],
            'economics': ['economic', 'economy', 'financial', 'money', 'cost']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics if topics else ['general']
    
    def _detect_conflicts(self, topic_groups: Dict[str, List[SourceEvidence]]) -> List[ConflictInfo]:
        """Detect conflicts within topic groups."""
        conflicts = []
        
        for topic, evidence_list in topic_groups.items():
            if len(evidence_list) < 2:
                continue
            
            # Look for contradictory statements
            for i, evidence1 in enumerate(evidence_list):
                for evidence2 in evidence_list[i+1:]:
                    conflict_type = self._analyze_conflict_between_statements(
                        evidence1.content, evidence2.content
                    )
                    
                    if conflict_type:
                        conflicts.append(ConflictInfo(
                            topic=topic,
                            conflicting_sources=[evidence1, evidence2],
                            conflict_type=conflict_type,
                            resolution_strategy="",  # Will be filled in resolution
                            confidence_in_resolution=0.0
                        ))
        
        return conflicts
    
    def _analyze_conflict_between_statements(self, statement1: str, statement2: str) -> Optional[str]:
        """Analyze if two statements conflict and determine conflict type."""
        s1_lower = statement1.lower()
        s2_lower = statement2.lower()
        
        # Look for direct contradictions
        contradiction_pairs = [
            (['is', 'are'], ['is not', 'are not', 'isn\'t', 'aren\'t']),
            (['increase', 'rise', 'grow'], ['decrease', 'fall', 'decline']),
            (['positive', 'good', 'beneficial'], ['negative', 'bad', 'harmful']),
            (['true', 'correct', 'accurate'], ['false', 'incorrect', 'inaccurate'])
        ]
        
        for positive_words, negative_words in contradiction_pairs:
            has_positive_1 = any(word in s1_lower for word in positive_words)
            has_negative_1 = any(word in s1_lower for word in negative_words)
            has_positive_2 = any(word in s2_lower for word in positive_words)
            has_negative_2 = any(word in s2_lower for word in negative_words)
            
            if (has_positive_1 and has_negative_2) or (has_negative_1 and has_positive_2):
                return "contradiction"
        
        # Look for numerical inconsistencies
        numbers1 = re.findall(r'\d+(?:\.\d+)?', statement1)
        numbers2 = re.findall(r'\d+(?:\.\d+)?', statement2)
        
        if numbers1 and numbers2:
            # Check for significantly different numbers in similar contexts
            try:
                num1 = float(numbers1[0])
                num2 = float(numbers2[0])
                if abs(num1 - num2) / max(num1, num2) > 0.5:  # 50% difference
                    return "inconsistency"
            except ValueError:
                pass
        
        # Look for temporal conflicts
        if any(indicator in s1_lower for indicator in ['before', 'after', 'during']):
            if any(indicator in s2_lower for indicator in ['before', 'after', 'during']):
                # Simple temporal conflict detection
                years1 = re.findall(r'\b\d{4}\b', statement1)
                years2 = re.findall(r'\b\d{4}\b', statement2)
                if years1 and years2 and years1[0] != years2[0]:
                    return "temporal_inconsistency"
        
        return None
    
    def _resolve_conflicts(self, conflicts: List[ConflictInfo]) -> List[ConflictInfo]:
        """Resolve detected conflicts using various strategies."""
        resolved_conflicts = []
        
        for conflict in conflicts:
            resolution_strategy, confidence = self._determine_resolution_strategy(conflict)
            
            conflict.resolution_strategy = resolution_strategy
            conflict.confidence_in_resolution = confidence
            
            resolved_conflicts.append(conflict)
        
        return resolved_conflicts
    
    def _determine_resolution_strategy(self, conflict: ConflictInfo) -> Tuple[str, float]:
        """Determine how to resolve a specific conflict."""
        sources = conflict.conflicting_sources
        
        # Strategy 1: Trust higher quality source
        if len(sources) == 2:
            source1, source2 = sources
            if source1.source_quality > source2.source_quality + 0.2:
                return f"trust_higher_quality_source_{source1.document_id}", 0.8
            elif source2.source_quality > source1.source_quality + 0.2:
                return f"trust_higher_quality_source_{source2.document_id}", 0.8
        
        # Strategy 2: Trust more confident statement
        max_confidence_source = max(sources, key=lambda x: x.confidence)
        if max_confidence_source.confidence > 0.8:
            return f"trust_higher_confidence_{max_confidence_source.document_id}", 0.7
        
        # Strategy 3: Look for consensus among other sources
        # (This would require checking other evidence in the same topic)
        
        # Strategy 4: Acknowledge uncertainty
        if conflict.conflict_type == "contradiction":
            return "acknowledge_contradiction", 0.6
        elif conflict.conflict_type == "inconsistency":
            return "note_inconsistency", 0.5
        else:
            return "require_further_research", 0.4
    
    def _generate_main_findings(self, 
                               topic_groups: Dict[str, List[SourceEvidence]], 
                               resolved_conflicts: List[ConflictInfo]) -> List[str]:
        """Generate main findings from evidence groups."""
        findings = []
        
        for topic, evidence_list in topic_groups.items():
            if not evidence_list:
                continue
            
            # Get high-confidence evidence
            high_confidence_evidence = [
                e for e in evidence_list 
                if e.confidence > 0.7 and e.relevance_score > 0.5
            ]
            
            if high_confidence_evidence:
                # Create finding based on most confident evidence
                top_evidence = max(high_confidence_evidence, key=lambda x: x.confidence)
                
                # Check if this topic has conflicts
                topic_conflicts = [c for c in resolved_conflicts if c.topic == topic]
                
                if topic_conflicts:
                    # Include conflict information in finding
                    finding = f"Regarding {topic}: {top_evidence.content} (Note: Some conflicting information exists)"
                else:
                    finding = f"Regarding {topic}: {top_evidence.content}"
                
                findings.append(finding)
        
        # Limit number of findings
        return findings[:10]
    
    def _calculate_overall_confidence(self, 
                                    evidence_list: List[SourceEvidence], 
                                    resolved_conflicts: List[ConflictInfo]) -> float:
        """Calculate overall confidence in the synthesis."""
        if not evidence_list:
            return 0.0
        
        # Base confidence from evidence quality
        avg_evidence_confidence = sum(e.confidence for e in evidence_list) / len(evidence_list)
        avg_source_quality = sum(e.source_quality for e in evidence_list) / len(evidence_list)
        
        base_confidence = (avg_evidence_confidence + avg_source_quality) / 2
        
        # Reduce confidence based on unresolved conflicts
        conflict_penalty = 0.0
        for conflict in resolved_conflicts:
            if conflict.confidence_in_resolution < 0.7:
                conflict_penalty += 0.1
        
        final_confidence = max(0.1, base_confidence - conflict_penalty)
        
        return min(1.0, final_confidence)
    
    def _generate_summary(self, main_findings: List[str], query: str) -> str:
        """Generate a summary of the research results."""
        if not main_findings:
            return f"No significant findings were identified for the query: {query}"
        
        summary_parts = [
            f"Based on the analysis of multiple sources, the following key insights were identified regarding: {query}",
            ""
        ]
        
        # Add top findings
        for i, finding in enumerate(main_findings[:5], 1):
            # Clean up the finding text
            clean_finding = finding.replace("Regarding general:", "").replace("Regarding ", "").strip()
            summary_parts.append(f"{i}. {clean_finding}")
        
        if len(main_findings) > 5:
            summary_parts.append(f"\nAdditional findings ({len(main_findings) - 5} more) provide further supporting evidence.")
        
        return "\n".join(summary_parts)
    
    def _calculate_source_diversity(self, documents: List[Document]) -> float:
        """Calculate diversity of sources."""
        if not documents:
            return 0.0
        
        # Diversity based on different factors
        format_diversity = len(set(doc.format_type for doc in documents)) / len(documents)
        
        # Path diversity (different directories/sources)
        paths = [doc.source_path for doc in documents]
        unique_dirs = len(set(path.split('/')[:-1] for path in paths if '/' in path))
        path_diversity = min(1.0, unique_dirs / len(documents))
        
        # Metadata diversity
        all_metadata_keys = set()
        for doc in documents:
            all_metadata_keys.update(doc.metadata.keys())
        
        metadata_diversity = min(1.0, len(all_metadata_keys) / max(1, len(documents)))
        
        return (format_diversity + path_diversity + metadata_diversity) / 3
    
    def _calculate_completeness_score(self, evidence_list: List[SourceEvidence], query: str) -> float:
        """Calculate how complete the evidence is for answering the query."""
        if not evidence_list:
            return 0.0
        
        # Completeness based on evidence coverage
        high_relevance_count = sum(1 for e in evidence_list if e.relevance_score > 0.7)
        coverage_score = min(1.0, high_relevance_count / 5)  # Expect at least 5 high-relevance pieces
        
        # Completeness based on evidence types
        evidence_types = set(e.extraction_method for e in evidence_list)
        type_diversity = len(evidence_types) / 4  # Expect up to 4 types
        
        return (coverage_score + type_diversity) / 2