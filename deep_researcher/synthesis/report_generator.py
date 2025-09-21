"""Structured report generation with templates and formatting."""

from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from ..models import ResearchReport, Document, ReasoningStep
from ..session.session_manager import ResearchSession
from ..synthesis.reasoning_explainer import ReasoningExplanation
from ..exceptions import SynthesisError

logger = logging.getLogger(__name__)


class ReportTemplate(Enum):
    """Available report templates."""
    EXECUTIVE = "executive"
    ACADEMIC = "academic"
    TECHNICAL = "technical"
    COMPARATIVE = "comparative"
    ANALYTICAL = "analytical"
    SUMMARY = "summary"


@dataclass
class ReportSection:
    """A section of a structured report."""
    title: str
    content: str
    subsections: List['ReportSection']
    metadata: Dict[str, Any]
    order: int


@dataclass
class ReportStructure:
    """Complete structure of a report."""
    title: str
    sections: List[ReportSection]
    bibliography: List[Dict[str, Any]]
    appendices: List[ReportSection]
    metadata: Dict[str, Any]


class ReportGenerator:
    """Generates structured reports with professional formatting."""
    
    def __init__(self):
        """Initialize report generator."""
        
        # Template configurations
        self.templates = {
            ReportTemplate.EXECUTIVE: {
                'sections': [
                    'executive_summary',
                    'key_findings',
                    'recommendations',
                    'conclusion'
                ],
                'max_length': 2000,
                'focus': 'business_impact'
            },
            ReportTemplate.ACADEMIC: {
                'sections': [
                    'abstract',
                    'introduction',
                    'methodology',
                    'findings',
                    'discussion',
                    'conclusion',
                    'references'
                ],
                'max_length': 5000,
                'focus': 'research_rigor'
            },
            ReportTemplate.TECHNICAL: {
                'sections': [
                    'overview',
                    'technical_details',
                    'implementation',
                    'performance',
                    'limitations',
                    'recommendations'
                ],
                'max_length': 4000,
                'focus': 'technical_depth'
            },
            ReportTemplate.COMPARATIVE: {
                'sections': [
                    'introduction',
                    'comparison_criteria',
                    'detailed_comparison',
                    'analysis',
                    'recommendations'
                ],
                'max_length': 3500,
                'focus': 'comparison_clarity'
            },
            ReportTemplate.ANALYTICAL: {
                'sections': [
                    'problem_definition',
                    'analysis_framework',
                    'findings',
                    'implications',
                    'recommendations'
                ],
                'max_length': 4000,
                'focus': 'analytical_depth'
            },
            ReportTemplate.SUMMARY: {
                'sections': [
                    'overview',
                    'key_points',
                    'conclusion'
                ],
                'max_length': 1500,
                'focus': 'conciseness'
            }
        }
    
    def generate_structured_report(self, 
                                 research_report: ResearchReport,
                                 template: ReportTemplate = ReportTemplate.ACADEMIC,
                                 session: Optional[ResearchSession] = None,
                                 reasoning_explanation: Optional[ReasoningExplanation] = None) -> ReportStructure:
        """
        Generate a structured report using the specified template.
        
        Args:
            research_report: Base research report
            template: Report template to use
            session: Optional session context
            reasoning_explanation: Optional reasoning explanation
            
        Returns:
            Structured report with sections and formatting
        """
        try:
            logger.info(f"Generating {template.value} report for query: {research_report.query}")
            
            template_config = self.templates[template]
            
            # Generate report title
            title = self._generate_report_title(research_report, template)
            
            # Generate sections based on template
            sections = []
            for section_name in template_config['sections']:
                section = self._generate_section(
                    section_name, 
                    research_report, 
                    template, 
                    session, 
                    reasoning_explanation
                )
                if section:
                    sections.append(section)
            
            # Generate bibliography
            bibliography = self._generate_bibliography(research_report.sources)
            
            # Generate appendices if needed
            appendices = self._generate_appendices(research_report, reasoning_explanation)
            
            # Create report structure
            report_structure = ReportStructure(
                title=title,
                sections=sections,
                bibliography=bibliography,
                appendices=appendices,
                metadata={
                    'template': template.value,
                    'generated_at': datetime.now().isoformat(),
                    'word_count': sum(len(section.content.split()) for section in sections),
                    'confidence_score': research_report.confidence_score,
                    'source_count': len(research_report.sources)
                }
            )
            
            logger.info(f"Generated structured report with {len(sections)} sections")
            return report_structure
            
        except Exception as e:
            logger.error(f"Structured report generation failed: {e}")
            raise SynthesisError(f"Structured report generation failed: {e}")
    
    def _generate_report_title(self, research_report: ResearchReport, template: ReportTemplate) -> str:
        """Generate an appropriate title for the report."""
        
        base_query = research_report.query
        
        if template == ReportTemplate.EXECUTIVE:
            return f"Executive Brief: {base_query}"
        elif template == ReportTemplate.ACADEMIC:
            return f"Research Analysis: {base_query}"
        elif template == ReportTemplate.TECHNICAL:
            return f"Technical Report: {base_query}"
        elif template == ReportTemplate.COMPARATIVE:
            return f"Comparative Analysis: {base_query}"
        elif template == ReportTemplate.ANALYTICAL:
            return f"Analytical Study: {base_query}"
        elif template == ReportTemplate.SUMMARY:
            return f"Summary Report: {base_query}"
        else:
            return f"Research Report: {base_query}"
    
    def _generate_section(self, 
                         section_name: str,
                         research_report: ResearchReport,
                         template: ReportTemplate,
                         session: Optional[ResearchSession],
                         reasoning_explanation: Optional[ReasoningExplanation]) -> Optional[ReportSection]:
        """Generate a specific section of the report."""
        
        section_generators = {
            'executive_summary': self._generate_executive_summary,
            'abstract': self._generate_abstract,
            'introduction': self._generate_introduction,
            'overview': self._generate_overview,
            'methodology': self._generate_methodology,
            'technical_details': self._generate_technical_details,
            'key_findings': self._generate_key_findings,
            'findings': self._generate_findings,
            'detailed_comparison': self._generate_detailed_comparison,
            'comparison_criteria': self._generate_comparison_criteria,
            'analysis': self._generate_analysis,
            'analysis_framework': self._generate_analysis_framework,
            'problem_definition': self._generate_problem_definition,
            'discussion': self._generate_discussion,
            'implications': self._generate_implications,
            'performance': self._generate_performance,
            'implementation': self._generate_implementation,
            'limitations': self._generate_limitations,
            'recommendations': self._generate_recommendations,
            'conclusion': self._generate_conclusion,
            'key_points': self._generate_key_points,
            'references': self._generate_references
        }
        
        generator = section_generators.get(section_name)
        if generator:
            return generator(research_report, template, session, reasoning_explanation)
        
        return None
    
    def _generate_executive_summary(self, research_report: ResearchReport, template: ReportTemplate, 
                                  session: Optional[ResearchSession], reasoning_explanation: Optional[ReasoningExplanation]) -> ReportSection:
        """Generate executive summary section."""
        
        content = []
        
        # Brief overview
        content.append(f"This report addresses the question: {research_report.query}")
        content.append("")
        
        # Key insights (condensed)
        content.append("Key insights from this analysis:")
        for i, finding in enumerate(research_report.key_findings[:3], 1):
            # Condense findings for executive summary
            condensed_finding = self._condense_text(finding, 100)
            content.append(f"• {condensed_finding}")
        
        content.append("")
        
        # Confidence and reliability
        confidence_text = "high" if research_report.confidence_score > 0.8 else "moderate" if research_report.confidence_score > 0.6 else "limited"
        content.append(f"This analysis is based on {len(research_report.sources)} sources with {confidence_text} confidence in the findings.")
        
        return ReportSection(
            title="Executive Summary",
            content="\n".join(content),
            subsections=[],
            metadata={'section_type': 'summary', 'word_count': len(" ".join(content).split())},
            order=1
        )
    
    def _generate_abstract(self, research_report: ResearchReport, template: ReportTemplate,
                          session: Optional[ResearchSession], reasoning_explanation: Optional[ReasoningExplanation]) -> ReportSection:
        """Generate abstract section for academic reports."""
        
        content = []
        
        # Background and objective
        content.append(f"Objective: This study investigates {research_report.query.lower()}")
        content.append("")
        
        # Methodology
        if reasoning_explanation:
            method_desc = f"The analysis employed a {len(reasoning_explanation.step_explanations)}-step reasoning approach"
            if research_report.sources:
                method_desc += f" examining {len(research_report.sources)} relevant sources"
            content.append(f"Methods: {method_desc}.")
        else:
            content.append(f"Methods: Systematic analysis of {len(research_report.sources)} sources using structured research methodology.")
        content.append("")
        
        # Results
        content.append(f"Results: The analysis identified {len(research_report.key_findings)} key findings.")
        for finding in research_report.key_findings[:2]:
            condensed = self._condense_text(finding, 80)
            content.append(f"• {condensed}")
        content.append("")
        
        # Conclusion
        conclusion = self._condense_text(research_report.summary, 120)
        content.append(f"Conclusion: {conclusion}")
        
        return ReportSection(
            title="Abstract",
            content="\n".join(content),
            subsections=[],
            metadata={'section_type': 'abstract', 'word_count': len(" ".join(content).split())},
            order=1
        )
    
    def _generate_introduction(self, research_report: ResearchReport, template: ReportTemplate,
                             session: Optional[ResearchSession], reasoning_explanation: Optional[ReasoningExplanation]) -> ReportSection:
        """Generate introduction section."""
        
        content = []
        
        # Context and background
        content.append(f"This report presents a comprehensive analysis of: {research_report.query}")
        content.append("")
        
        # Scope and approach
        if session and session.session_context.research_domain != 'general':
            content.append(f"The analysis is conducted within the context of {session.session_context.research_domain}.")
        
        content.append(f"The research draws upon {len(research_report.sources)} sources to provide evidence-based insights.")
        content.append("")
        
        # Structure overview
        content.append("This report is structured to provide:")
        if template == ReportTemplate.COMPARATIVE:
            content.append("• Systematic comparison of key alternatives")
            content.append("• Analysis of strengths and limitations")
            content.append("• Evidence-based recommendations")
        elif template == ReportTemplate.ANALYTICAL:
            content.append("• Detailed problem analysis")
            content.append("• Examination of contributing factors")
            content.append("• Assessment of implications")
        else:
            content.append("• Comprehensive examination of the topic")
            content.append("• Evidence-based findings")
            content.append("• Practical insights and recommendations")
        
        return ReportSection(
            title="Introduction",
            content="\n".join(content),
            subsections=[],
            metadata={'section_type': 'introduction', 'word_count': len(" ".join(content).split())},
            order=2
        )
    
    def _generate_methodology(self, research_report: ResearchReport, template: ReportTemplate,
                            session: Optional[ResearchSession], reasoning_explanation: Optional[ReasoningExplanation]) -> ReportSection:
        """Generate methodology section."""
        
        content = []
        
        # Research approach
        content.append("Research Approach:")
        content.append("This analysis employed a systematic research methodology combining:")
        content.append("• Multi-source information gathering")
        content.append("• Structured reasoning and analysis")
        content.append("• Evidence synthesis and validation")
        content.append("")
        
        # Data sources
        content.append("Data Sources:")
        format_counts = {}
        for source in research_report.sources:
            format_type = source.format_type.value
            format_counts[format_type] = format_counts.get(format_type, 0) + 1
        
        for format_type, count in format_counts.items():
            content.append(f"• {count} {format_type.upper()} document(s)")
        content.append("")
        
        # Analysis process
        if reasoning_explanation:
            content.append("Analysis Process:")
            content.append(f"The research followed a {len(reasoning_explanation.step_explanations)}-step reasoning process:")
            for i, step in enumerate(reasoning_explanation.step_explanations[:3], 1):
                content.append(f"{i}. {step.purpose}")
        
        return ReportSection(
            title="Methodology",
            content="\n".join(content),
            subsections=[],
            metadata={'section_type': 'methodology', 'word_count': len(" ".join(content).split())},
            order=3
        )
    
    def _generate_key_findings(self, research_report: ResearchReport, template: ReportTemplate,
                             session: Optional[ResearchSession], reasoning_explanation: Optional[ReasoningExplanation]) -> ReportSection:
        """Generate key findings section."""
        
        content = []
        
        content.append("The analysis revealed the following key findings:")
        content.append("")
        
        for i, finding in enumerate(research_report.key_findings, 1):
            content.append(f"{i}. {finding}")
            content.append("")
        
        # Add confidence assessment
        if research_report.confidence_score:
            confidence_text = self._get_confidence_description(research_report.confidence_score)
            content.append(f"Confidence Assessment: These findings are supported with {confidence_text} confidence based on the available evidence.")
        
        return ReportSection(
            title="Key Findings",
            content="\n".join(content),
            subsections=[],
            metadata={'section_type': 'findings', 'word_count': len(" ".join(content).split())},
            order=4
        )
    
    def _generate_recommendations(self, research_report: ResearchReport, template: ReportTemplate,
                                session: Optional[ResearchSession], reasoning_explanation: Optional[ReasoningExplanation]) -> ReportSection:
        """Generate recommendations section."""
        
        content = []
        
        content.append("Based on the analysis, the following recommendations are proposed:")
        content.append("")
        
        # Generate recommendations based on findings
        recommendations = self._derive_recommendations_from_findings(research_report.key_findings)
        
        for i, recommendation in enumerate(recommendations, 1):
            content.append(f"{i}. {recommendation}")
            content.append("")
        
        # Add implementation considerations
        content.append("Implementation Considerations:")
        content.append("• Verify findings with additional sources when making critical decisions")
        content.append("• Consider context-specific factors that may affect applicability")
        if research_report.confidence_score < 0.7:
            content.append("• Seek additional information to increase confidence in conclusions")
        
        return ReportSection(
            title="Recommendations",
            content="\n".join(content),
            subsections=[],
            metadata={'section_type': 'recommendations', 'word_count': len(" ".join(content).split())},
            order=8
        )
    
    def _generate_conclusion(self, research_report: ResearchReport, template: ReportTemplate,
                           session: Optional[ResearchSession], reasoning_explanation: Optional[ReasoningExplanation]) -> ReportSection:
        """Generate conclusion section."""
        
        content = []
        
        # Summarize main insights
        content.append(f"This analysis of '{research_report.query}' has provided comprehensive insights based on systematic research.")
        content.append("")
        
        # Highlight most significant findings
        if research_report.key_findings:
            most_significant = research_report.key_findings[0]
            content.append(f"The most significant finding is: {most_significant}")
            content.append("")
        
        # Overall assessment
        content.append(research_report.summary)
        content.append("")
        
        # Future considerations
        content.append("Future Considerations:")
        content.append("• Monitor developments in this area for updated information")
        content.append("• Consider conducting deeper analysis on specific aspects of interest")
        if session and session.session_context.key_concepts:
            recent_concepts = session.session_context.key_concepts[-2:]
            content.append(f"• Explore connections with related topics: {', '.join(recent_concepts)}")
        
        return ReportSection(
            title="Conclusion",
            content="\n".join(content),
            subsections=[],
            metadata={'section_type': 'conclusion', 'word_count': len(" ".join(content).split())},
            order=9
        )
    
    def _generate_bibliography(self, sources: List[Document]) -> List[Dict[str, Any]]:
        """Generate bibliography from sources."""
        
        bibliography = []
        
        for i, source in enumerate(sources, 1):
            entry = {
                'id': i,
                'title': source.title,
                'source': source.source_path,
                'format': source.format_type.value.upper(),
                'accessed': source.created_at.strftime('%Y-%m-%d'),
                'word_count': source.word_count
            }
            
            # Add metadata if available
            if source.metadata:
                if 'author' in source.metadata:
                    entry['author'] = source.metadata['author']
                if 'publication_date' in source.metadata:
                    entry['publication_date'] = source.metadata['publication_date']
            
            bibliography.append(entry)
        
        return bibliography
    
    def _generate_appendices(self, research_report: ResearchReport, 
                           reasoning_explanation: Optional[ReasoningExplanation]) -> List[ReportSection]:
        """Generate appendices for additional information."""
        
        appendices = []
        
        # Reasoning process appendix
        if reasoning_explanation:
            reasoning_content = []
            reasoning_content.append("Detailed Reasoning Process:")
            reasoning_content.append("")
            
            for i, step in enumerate(reasoning_explanation.step_explanations, 1):
                reasoning_content.append(f"Step {i}: {step.step_description}")
                reasoning_content.append(f"Purpose: {step.purpose}")
                reasoning_content.append(f"Confidence: {step.confidence_explanation}")
                reasoning_content.append("")
            
            appendices.append(ReportSection(
                title="Appendix A: Reasoning Process",
                content="\n".join(reasoning_content),
                subsections=[],
                metadata={'section_type': 'appendix', 'appendix_type': 'reasoning'},
                order=10
            ))
        
        # Source details appendix
        if research_report.sources:
            source_content = []
            source_content.append("Detailed Source Information:")
            source_content.append("")
            
            for i, source in enumerate(research_report.sources, 1):
                source_content.append(f"Source {i}: {source.title}")
                source_content.append(f"Path: {source.source_path}")
                source_content.append(f"Format: {source.format_type.value}")
                source_content.append(f"Word Count: {source.word_count}")
                if source.metadata:
                    source_content.append("Metadata:")
                    for key, value in source.metadata.items():
                        source_content.append(f"  {key}: {value}")
                source_content.append("")
            
            appendices.append(ReportSection(
                title="Appendix B: Source Details",
                content="\n".join(source_content),
                subsections=[],
                metadata={'section_type': 'appendix', 'appendix_type': 'sources'},
                order=11
            ))
        
        return appendices
    
    def _condense_text(self, text: str, max_words: int) -> str:
        """Condense text to specified word limit."""
        words = text.split()
        if len(words) <= max_words:
            return text
        
        condensed = " ".join(words[:max_words])
        return condensed + "..."
    
    def _get_confidence_description(self, confidence_score: float) -> str:
        """Get textual description of confidence score."""
        if confidence_score >= 0.9:
            return "very high"
        elif confidence_score >= 0.8:
            return "high"
        elif confidence_score >= 0.7:
            return "moderate"
        elif confidence_score >= 0.6:
            return "limited"
        else:
            return "low"
    
    def _derive_recommendations_from_findings(self, findings: List[str]) -> List[str]:
        """Derive actionable recommendations from findings."""
        recommendations = []
        
        for finding in findings[:3]:  # Focus on top 3 findings
            # Simple recommendation generation based on finding content
            if "increase" in finding.lower() or "improve" in finding.lower():
                recommendations.append(f"Consider strategies to leverage: {finding}")
            elif "decrease" in finding.lower() or "reduce" in finding.lower():
                recommendations.append(f"Develop mitigation approaches for: {finding}")
            elif "compare" in finding.lower() or "difference" in finding.lower():
                recommendations.append(f"Evaluate options based on: {finding}")
            else:
                recommendations.append(f"Further investigate: {finding}")
        
        return recommendations
    
    # Placeholder methods for other section types
    def _generate_overview(self, *args) -> ReportSection:
        return self._generate_introduction(*args)
    
    def _generate_findings(self, *args) -> ReportSection:
        return self._generate_key_findings(*args)
    
    def _generate_technical_details(self, research_report: ResearchReport, *args) -> ReportSection:
        content = "Technical implementation details and specifications based on the research findings."
        return ReportSection("Technical Details", content, [], {}, 4)
    
    def _generate_detailed_comparison(self, research_report: ResearchReport, *args) -> ReportSection:
        content = "Detailed comparison analysis based on the research findings."
        return ReportSection("Detailed Comparison", content, [], {}, 4)
    
    def _generate_comparison_criteria(self, research_report: ResearchReport, *args) -> ReportSection:
        content = "Criteria and methodology used for comparison analysis."
        return ReportSection("Comparison Criteria", content, [], {}, 3)
    
    def _generate_analysis(self, *args) -> ReportSection:
        return self._generate_key_findings(*args)
    
    def _generate_analysis_framework(self, research_report: ResearchReport, *args) -> ReportSection:
        content = "Framework and approach used for analytical assessment."
        return ReportSection("Analysis Framework", content, [], {}, 3)
    
    def _generate_problem_definition(self, research_report: ResearchReport, *args) -> ReportSection:
        content = f"Problem Definition: {research_report.query}"
        return ReportSection("Problem Definition", content, [], {}, 2)
    
    def _generate_discussion(self, *args) -> ReportSection:
        return self._generate_key_findings(*args)
    
    def _generate_implications(self, *args) -> ReportSection:
        return self._generate_recommendations(*args)
    
    def _generate_performance(self, research_report: ResearchReport, *args) -> ReportSection:
        content = "Performance analysis and metrics based on research findings."
        return ReportSection("Performance", content, [], {}, 5)
    
    def _generate_implementation(self, research_report: ResearchReport, *args) -> ReportSection:
        content = "Implementation considerations and practical applications."
        return ReportSection("Implementation", content, [], {}, 6)
    
    def _generate_limitations(self, research_report: ResearchReport, *args) -> ReportSection:
        content = f"This analysis is based on {len(research_report.sources)} sources. Additional research may provide further insights."
        return ReportSection("Limitations", content, [], {}, 7)
    
    def _generate_key_points(self, *args) -> ReportSection:
        return self._generate_key_findings(*args)
    
    def _generate_references(self, research_report: ResearchReport, *args) -> ReportSection:
        content = f"References: {len(research_report.sources)} sources consulted."
        return ReportSection("References", content, [], {}, 10)