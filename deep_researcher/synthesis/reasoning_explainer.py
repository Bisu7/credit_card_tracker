"""Reasoning explanation and transparency functionality."""

from typing import List, Dict, Any, Optional, Tuple
import logging
import time
from dataclasses import dataclass
from enum import Enum

from ..models import ReasoningStep, ResearchReport, Document
from ..reasoning.multi_step_reasoner import ReasoningContext
from ..exceptions import SynthesisError

logger = logging.getLogger(__name__)


class ExplanationLevel(Enum):
    """Different levels of explanation detail."""
    BRIEF = "brief"
    DETAILED = "detailed"
    TECHNICAL = "technical"
    STEP_BY_STEP = "step_by_step"


@dataclass
class StepExplanation:
    """Explanation for a single reasoning step."""
    step_id: str
    step_description: str
    purpose: str
    input_context: List[str]
    reasoning_process: str
    output_summary: str
    confidence_explanation: str
    dependencies_explanation: str
    execution_time: float
    success: bool
    challenges_encountered: List[str]


@dataclass
class ReasoningExplanation:
    """Complete explanation of the reasoning process."""
    query: str
    overall_strategy: str
    step_explanations: List[StepExplanation]
    decision_points: List[Dict[str, Any]]
    confidence_factors: Dict[str, float]
    limitations: List[str]
    alternative_approaches: List[str]
    quality_assessment: Dict[str, Any]


class ReasoningExplainer:
    """Provides explanations for reasoning processes and decisions."""
    
    def __init__(self):
        """Initialize reasoning explainer."""
        self.explanation_templates = {
            "comparative": "This analysis compared multiple entities by first researching each individually, then identifying key dimensions for comparison, and finally synthesizing the differences and similarities.",
            "analytical": "This analysis broke down the complex topic into key components, gathered evidence for each component, analyzed relationships between them, and drew conclusions based on the evidence.",
            "multi_part": "This analysis addressed each part of the multi-faceted question separately, then synthesized the findings to provide a comprehensive answer.",
            "complex": "This analysis decomposed the complex query into manageable components, researched each component thoroughly, and then analyzed how they interact to answer the original question."
        }
    
    def explain_reasoning_process(self, 
                                 context: ReasoningContext, 
                                 level: ExplanationLevel = ExplanationLevel.DETAILED) -> ReasoningExplanation:
        """
        Generate explanation for the complete reasoning process.
        
        Args:
            context: Reasoning context with steps and results
            level: Level of detail for explanation
            
        Returns:
            Complete reasoning explanation
        """
        try:
            logger.info(f"Generating {level.value} explanation for reasoning process")
            
            # Generate overall strategy explanation
            overall_strategy = self._explain_overall_strategy(context)
            
            # Generate step-by-step explanations
            step_explanations = []
            for step in context.steps:
                step_explanation = self._explain_reasoning_step(step, context, level)
                step_explanations.append(step_explanation)
            
            # Identify key decision points
            decision_points = self._identify_decision_points(context)
            
            # Analyze confidence factors
            confidence_factors = self._analyze_confidence_factors(context)
            
            # Identify limitations
            limitations = self._identify_limitations(context)
            
            # Suggest alternative approaches
            alternative_approaches = self._suggest_alternative_approaches(context)
            
            # Assess overall quality
            quality_assessment = self._assess_reasoning_quality(context)
            
            explanation = ReasoningExplanation(
                query=context.original_query.original_query,
                overall_strategy=overall_strategy,
                step_explanations=step_explanations,
                decision_points=decision_points,
                confidence_factors=confidence_factors,
                limitations=limitations,
                alternative_approaches=alternative_approaches,
                quality_assessment=quality_assessment
            )
            
            logger.info("Reasoning explanation generated successfully")
            return explanation
            
        except Exception as e:
            logger.error(f"Failed to generate reasoning explanation: {e}")
            raise SynthesisError(f"Failed to generate reasoning explanation: {e}")
    
    def explain_source_selection(self, 
                                documents: List[Document], 
                                query: str,
                                retrieval_scores: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Explain why specific sources were selected.
        
        Args:
            documents: Selected documents
            query: Original query
            retrieval_scores: Optional retrieval scores for documents
            
        Returns:
            Explanation of source selection
        """
        try:
            explanations = []
            
            for doc in documents:
                doc_explanation = {
                    'document_id': doc.id,
                    'title': doc.title,
                    'selection_reasons': self._explain_document_selection(doc, query),
                    'relevance_indicators': self._identify_relevance_indicators(doc, query),
                    'quality_factors': self._assess_document_quality_factors(doc),
                    'retrieval_score': retrieval_scores.get(doc.id) if retrieval_scores else None
                }
                explanations.append(doc_explanation)
            
            return {
                'total_sources': len(documents),
                'selection_criteria': self._get_selection_criteria(),
                'source_explanations': explanations,
                'diversity_analysis': self._analyze_source_diversity(documents),
                'coverage_assessment': self._assess_query_coverage(documents, query)
            }
            
        except Exception as e:
            logger.error(f"Failed to explain source selection: {e}")
            return {'error': str(e)}
    
    def explain_confidence_scoring(self, report: ResearchReport) -> Dict[str, Any]:
        """
        Explain how confidence scores were calculated.
        
        Args:
            report: Research report with confidence scores
            
        Returns:
            Explanation of confidence scoring
        """
        try:
            # Analyze confidence factors from the report
            confidence_breakdown = {
                'overall_confidence': report.confidence_score,
                'contributing_factors': [],
                'reducing_factors': [],
                'calculation_method': 'weighted_average_with_penalties'
            }
            
            # Analyze source quality contribution
            if report.sources:
                source_quality = self._analyze_source_quality_impact(report.sources)
                confidence_breakdown['contributing_factors'].append({
                    'factor': 'source_quality',
                    'impact': source_quality,
                    'explanation': 'Higher quality sources increase confidence'
                })
            
            # Analyze reasoning step success rate
            if report.reasoning_steps:
                step_success_rate = len([s for s in report.reasoning_steps if s.results]) / len(report.reasoning_steps)
                confidence_breakdown['contributing_factors'].append({
                    'factor': 'reasoning_success_rate',
                    'impact': step_success_rate,
                    'explanation': 'Successful completion of reasoning steps increases confidence'
                })
            
            # Analyze conflicts and inconsistencies
            synthesis_info = report.metadata.get('synthesis_info', {})
            if synthesis_info.get('conflicts_detected', 0) > 0:
                conflict_impact = -0.1 * synthesis_info['conflicts_detected']
                confidence_breakdown['reducing_factors'].append({
                    'factor': 'information_conflicts',
                    'impact': conflict_impact,
                    'explanation': 'Conflicting information reduces confidence'
                })
            
            return confidence_breakdown
            
        except Exception as e:
            logger.error(f"Failed to explain confidence scoring: {e}")
            return {'error': str(e)}
    
    def _explain_overall_strategy(self, context: ReasoningContext) -> str:
        """Explain the overall reasoning strategy used."""
        query_type = context.original_query.query_type.value
        
        # Get template explanation
        template = self.explanation_templates.get(query_type, 
            "This analysis used a systematic approach to break down the query and gather relevant information.")
        
        # Customize based on actual steps
        step_count = len(context.steps)
        success_rate = len(context.step_results) / step_count if step_count > 0 else 0
        
        strategy_explanation = f"{template} "
        
        if step_count > 1:
            strategy_explanation += f"The process involved {step_count} distinct reasoning steps, "
            strategy_explanation += f"with {len(context.step_results)} steps completed successfully "
            strategy_explanation += f"(success rate: {success_rate:.1%}). "
        
        if context.failed_steps:
            strategy_explanation += f"Some challenges were encountered in {len(context.failed_steps)} steps, "
            strategy_explanation += "but the analysis continued with available information. "
        
        return strategy_explanation
    
    def _explain_reasoning_step(self, 
                               step: ReasoningStep, 
                               context: ReasoningContext, 
                               level: ExplanationLevel) -> StepExplanation:
        """Generate explanation for a single reasoning step."""
        
        # Determine step purpose
        purpose = self._determine_step_purpose(step)
        
        # Explain input context
        input_context = self._explain_input_context(step, context)
        
        # Explain reasoning process
        reasoning_process = self._explain_reasoning_process_for_step(step, level)
        
        # Summarize output
        output_summary = self._summarize_step_output(step)
        
        # Explain confidence
        confidence_explanation = self._explain_step_confidence(step)
        
        # Explain dependencies
        dependencies_explanation = self._explain_step_dependencies(step, context)
        
        # Identify challenges
        challenges = self._identify_step_challenges(step, context)
        
        return StepExplanation(
            step_id=step.step_id,
            step_description=step.description,
            purpose=purpose,
            input_context=input_context,
            reasoning_process=reasoning_process,
            output_summary=output_summary,
            confidence_explanation=confidence_explanation,
            dependencies_explanation=dependencies_explanation,
            execution_time=step.execution_time or 0.0,
            success=bool(step.results and step.results.get('status') == 'completed'),
            challenges_encountered=challenges
        )
    
    def _determine_step_purpose(self, step: ReasoningStep) -> str:
        """Determine the purpose of a reasoning step."""
        description_lower = step.description.lower()
        
        if 'research' in description_lower:
            return "Information gathering - collecting relevant data and evidence"
        elif 'compare' in description_lower:
            return "Comparative analysis - identifying similarities and differences"
        elif 'analyze' in description_lower:
            return "Analysis - examining relationships and patterns in the information"
        elif 'synthesize' in description_lower:
            return "Synthesis - combining information from multiple sources"
        elif 'identify' in description_lower:
            return "Identification - finding specific elements or patterns"
        else:
            return "Information processing - working with available data to answer the query"
    
    def _explain_input_context(self, step: ReasoningStep, context: ReasoningContext) -> List[str]:
        """Explain what input context was available for the step."""
        input_context = []
        
        # Check dependencies
        for dep_id in step.dependencies:
            if dep_id in context.step_results:
                input_context.append(f"Results from step {dep_id}")
        
        # Check global context
        if context.global_context:
            input_context.append("Global research context including query keywords and previous findings")
        
        if not input_context:
            input_context.append("Original query and initial context")
        
        return input_context
    
    def _explain_reasoning_process_for_step(self, step: ReasoningStep, level: ExplanationLevel) -> str:
        """Explain the reasoning process used in a step."""
        if level == ExplanationLevel.BRIEF:
            return f"Processed the query: '{step.query}'"
        
        process_explanation = f"This step processed the query '{step.query}' by "
        
        # Analyze the step description to infer process
        description_lower = step.description.lower()
        
        if 'research' in description_lower:
            process_explanation += "searching for relevant information in the available sources, "
            process_explanation += "evaluating the relevance and quality of found information, "
            process_explanation += "and extracting key facts and insights."
        elif 'compare' in description_lower:
            process_explanation += "identifying comparable aspects between the entities, "
            process_explanation += "analyzing similarities and differences, "
            process_explanation += "and organizing the comparison results."
        elif 'analyze' in description_lower:
            process_explanation += "examining the available information for patterns, "
            process_explanation += "identifying relationships between different elements, "
            process_explanation += "and drawing analytical conclusions."
        else:
            process_explanation += "applying systematic reasoning to the available information "
            process_explanation += "to generate insights relevant to the query."
        
        return process_explanation
    
    def _summarize_step_output(self, step: ReasoningStep) -> str:
        """Summarize the output of a reasoning step."""
        if not step.results:
            return "No results generated (step may have failed)"
        
        results = step.results
        
        if results.get('status') == 'completed':
            summary = "Successfully completed. "
            
            if 'findings' in results:
                findings_count = len(results['findings'])
                summary += f"Generated {findings_count} key findings. "
            
            if 'source_count' in results:
                summary += f"Used {results['source_count']} sources. "
            
            if 'confidence' in results:
                summary += f"Confidence level: {results['confidence']:.2f}. "
        else:
            summary = f"Status: {results.get('status', 'unknown')}. "
        
        return summary
    
    def _explain_step_confidence(self, step: ReasoningStep) -> str:
        """Explain the confidence level of a step."""
        confidence = step.confidence
        
        if confidence >= 0.9:
            explanation = "Very high confidence - step based on clear, reliable information"
        elif confidence >= 0.8:
            explanation = "High confidence - step supported by good quality information"
        elif confidence >= 0.7:
            explanation = "Moderate confidence - step has reasonable support"
        elif confidence >= 0.6:
            explanation = "Lower confidence - step based on limited or uncertain information"
        else:
            explanation = "Low confidence - step involves significant uncertainty"
        
        # Add specific factors if available in results
        if step.results and 'confidence_factors' in step.results:
            factors = step.results['confidence_factors']
            explanation += f" (Factors: {', '.join(factors)})"
        
        return explanation
    
    def _explain_step_dependencies(self, step: ReasoningStep, context: ReasoningContext) -> str:
        """Explain the dependencies of a step."""
        if not step.dependencies:
            return "No dependencies - this step could be executed independently"
        
        explanation = f"Depended on {len(step.dependencies)} previous step(s): "
        
        dep_explanations = []
        for dep_id in step.dependencies:
            dep_step = context.get_step_by_id(dep_id)
            if dep_step:
                dep_explanations.append(f"'{dep_step.description}'")
            else:
                dep_explanations.append(f"step {dep_id}")
        
        explanation += ", ".join(dep_explanations)
        
        return explanation
    
    def _identify_step_challenges(self, step: ReasoningStep, context: ReasoningContext) -> List[str]:
        """Identify challenges encountered in a step."""
        challenges = []
        
        # Check if step failed
        if step.step_id in context.failed_steps:
            challenges.append("Step execution failed")
        
        # Check for low confidence
        if step.confidence < 0.6:
            challenges.append("Low confidence due to uncertain information")
        
        # Check for missing dependencies
        for dep_id in step.dependencies:
            if dep_id not in context.step_results:
                challenges.append(f"Missing dependency: {dep_id}")
        
        # Check execution time (if unusually long)
        if step.execution_time and step.execution_time > 30:
            challenges.append("Longer than expected execution time")
        
        return challenges
    
    def _identify_decision_points(self, context: ReasoningContext) -> List[Dict[str, Any]]:
        """Identify key decision points in the reasoning process."""
        decision_points = []
        
        # Decision point: Query decomposition strategy
        query_type = context.original_query.query_type.value
        decision_points.append({
            'decision': 'reasoning_strategy_selection',
            'description': f'Selected {query_type} reasoning strategy based on query analysis',
            'alternatives': ['simple_search', 'comparative_analysis', 'multi_step_breakdown'],
            'rationale': f'Query characteristics indicated {query_type} approach would be most effective'
        })
        
        # Decision point: Step execution order
        if len(context.steps) > 1:
            decision_points.append({
                'decision': 'step_execution_order',
                'description': 'Determined optimal order for executing reasoning steps',
                'alternatives': ['sequential', 'parallel', 'dependency_based'],
                'rationale': 'Used dependency-based ordering to ensure proper information flow'
            })
        
        # Decision point: Failure handling
        if context.failed_steps:
            decision_points.append({
                'decision': 'failure_handling',
                'description': 'Decided to continue analysis despite some step failures',
                'alternatives': ['abort_on_failure', 'continue_with_partial_results', 'retry_failed_steps'],
                'rationale': 'Sufficient successful steps provided adequate information for analysis'
            })
        
        return decision_points
    
    def _analyze_confidence_factors(self, context: ReasoningContext) -> Dict[str, float]:
        """Analyze factors contributing to overall confidence."""
        factors = {}
        
        # Step success rate
        if context.steps:
            success_rate = len(context.step_results) / len(context.steps)
            factors['step_success_rate'] = success_rate
        
        # Average step confidence
        if context.steps:
            avg_confidence = sum(step.confidence for step in context.steps) / len(context.steps)
            factors['average_step_confidence'] = avg_confidence
        
        # Execution efficiency
        total_time = time.time() - context.start_time if hasattr(context, 'start_time') else 0
        if total_time > 0:
            efficiency = min(1.0, 60 / total_time)  # Normalize to 1 minute baseline
            factors['execution_efficiency'] = efficiency
        
        return factors
    
    def _identify_limitations(self, context: ReasoningContext) -> List[str]:
        """Identify limitations in the reasoning process."""
        limitations = []
        
        # Failed steps
        if context.failed_steps:
            limitations.append(f"{len(context.failed_steps)} reasoning steps failed to complete")
        
        # Low confidence steps
        low_confidence_steps = [s for s in context.steps if s.confidence < 0.6]
        if low_confidence_steps:
            limitations.append(f"{len(low_confidence_steps)} steps had low confidence scores")
        
        # Limited context
        if not context.global_context or len(context.global_context) < 3:
            limitations.append("Limited contextual information available for reasoning")
        
        # Time constraints
        if hasattr(context, 'start_time'):
            total_time = time.time() - context.start_time
            if total_time > 300:  # 5 minutes
                limitations.append("Extended processing time may have limited depth of analysis")
        
        return limitations
    
    def _suggest_alternative_approaches(self, context: ReasoningContext) -> List[str]:
        """Suggest alternative approaches that could have been used."""
        alternatives = []
        
        query_type = context.original_query.query_type.value
        
        if query_type == 'comparative':
            alternatives.extend([
                "Could have used quantitative comparison metrics",
                "Alternative: Side-by-side feature comparison table",
                "Could have included user experience perspectives"
            ])
        elif query_type == 'analytical':
            alternatives.extend([
                "Could have used statistical analysis methods",
                "Alternative: Root cause analysis approach",
                "Could have included predictive modeling"
            ])
        elif query_type == 'complex':
            alternatives.extend([
                "Could have used hierarchical decomposition",
                "Alternative: Mind mapping approach",
                "Could have applied systems thinking methodology"
            ])
        
        # General alternatives
        alternatives.extend([
            "Could have gathered additional sources for broader perspective",
            "Alternative: Focus on more recent information only",
            "Could have used expert opinion weighting"
        ])
        
        return alternatives[:5]  # Limit to top 5
    
    def _assess_reasoning_quality(self, context: ReasoningContext) -> Dict[str, Any]:
        """Assess the overall quality of the reasoning process."""
        quality_metrics = {}
        
        # Completeness
        if context.steps:
            completion_rate = len(context.step_results) / len(context.steps)
            quality_metrics['completeness'] = completion_rate
        
        # Consistency
        step_confidences = [step.confidence for step in context.steps]
        if step_confidences:
            confidence_variance = sum((c - sum(step_confidences)/len(step_confidences))**2 for c in step_confidences) / len(step_confidences)
            consistency = max(0, 1 - confidence_variance)
            quality_metrics['consistency'] = consistency
        
        # Efficiency
        if hasattr(context, 'start_time'):
            total_time = time.time() - context.start_time
            steps_per_minute = len(context.steps) / (total_time / 60) if total_time > 0 else 0
            efficiency = min(1.0, steps_per_minute / 2)  # Normalize to 2 steps per minute
            quality_metrics['efficiency'] = efficiency
        
        # Overall quality score
        if quality_metrics:
            overall_quality = sum(quality_metrics.values()) / len(quality_metrics)
            quality_metrics['overall_quality'] = overall_quality
        
        return quality_metrics
    
    def _explain_document_selection(self, document: Document, query: str) -> List[str]:
        """Explain why a specific document was selected."""
        reasons = []
        
        # Title relevance
        query_words = set(query.lower().split())
        title_words = set(document.title.lower().split())
        if query_words.intersection(title_words):
            reasons.append("Title contains relevant keywords")
        
        # Content relevance
        content_words = set(document.content.lower().split())
        if len(query_words.intersection(content_words)) > len(query_words) * 0.3:
            reasons.append("Content has high keyword overlap with query")
        
        # Document quality
        if document.word_count > 500:
            reasons.append("Substantial content length indicates comprehensive coverage")
        
        # Metadata richness
        if document.metadata:
            reasons.append("Rich metadata suggests authoritative source")
        
        return reasons if reasons else ["Selected based on semantic similarity"]
    
    def _identify_relevance_indicators(self, document: Document, query: str) -> List[str]:
        """Identify specific indicators of document relevance."""
        indicators = []
        
        query_lower = query.lower()
        content_lower = document.content.lower()
        
        # Direct keyword matches
        query_words = query_lower.split()
        for word in query_words:
            if word in content_lower:
                indicators.append(f"Contains keyword: '{word}'")
        
        # Topic indicators
        if any(topic in content_lower for topic in ['research', 'study', 'analysis']):
            indicators.append("Contains research-oriented content")
        
        return indicators[:5]  # Limit to top 5
    
    def _assess_document_quality_factors(self, document: Document) -> Dict[str, Any]:
        """Assess quality factors for a document."""
        return {
            'word_count': document.word_count,
            'has_title': bool(document.title),
            'metadata_richness': len(document.metadata),
            'format_type': document.format_type.value,
            'chunk_count': document.chunk_count
        }
    
    def _get_selection_criteria(self) -> List[str]:
        """Get the criteria used for source selection."""
        return [
            "Semantic similarity to query",
            "Keyword relevance",
            "Document quality and completeness",
            "Source diversity",
            "Recency and timeliness"
        ]
    
    def _analyze_source_diversity(self, documents: List[Document]) -> Dict[str, Any]:
        """Analyze diversity of selected sources."""
        if not documents:
            return {}
        
        format_types = [doc.format_type.value for doc in documents]
        unique_formats = len(set(format_types))
        
        return {
            'format_diversity': unique_formats / len(documents),
            'total_sources': len(documents),
            'format_distribution': dict(Counter(format_types))
        }
    
    def _assess_query_coverage(self, documents: List[Document], query: str) -> Dict[str, Any]:
        """Assess how well the documents cover the query."""
        query_words = set(query.lower().split())
        
        covered_words = set()
        for doc in documents:
            doc_words = set(doc.content.lower().split())
            covered_words.update(query_words.intersection(doc_words))
        
        coverage_ratio = len(covered_words) / len(query_words) if query_words else 0
        
        return {
            'coverage_ratio': coverage_ratio,
            'covered_keywords': list(covered_words),
            'missing_keywords': list(query_words - covered_words)
        }
    
    def _analyze_source_quality_impact(self, sources: List[Document]) -> float:
        """Analyze the impact of source quality on confidence."""
        if not sources:
            return 0.0
        
        # Simple quality assessment based on available metrics
        quality_scores = []
        for doc in sources:
            score = 0.5  # Base score
            
            # Length-based quality
            if 500 <= doc.word_count <= 5000:
                score += 0.2
            
            # Metadata richness
            if doc.metadata:
                score += min(0.2, len(doc.metadata) * 0.05)
            
            # Title quality
            if doc.title and len(doc.title) > 10:
                score += 0.1
            
            quality_scores.append(min(1.0, score))
        
        return sum(quality_scores) / len(quality_scores)