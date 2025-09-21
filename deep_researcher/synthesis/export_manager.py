"""Export management for research reports in multiple formats."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from dataclasses import dataclass

from ..models import ResearchReport, Document
from ..interfaces import ExportManagerInterface
from ..exceptions import ExportError
from ..config import config

logger = logging.getLogger(__name__)


@dataclass
class ExportOptions:
    """Options for export formatting."""
    include_sources: bool = True
    include_reasoning_steps: bool = True
    include_metadata: bool = True
    include_confidence_scores: bool = True
    include_timestamps: bool = True
    page_numbers: bool = True
    table_of_contents: bool = True
    executive_summary: bool = True


class ExportManager(ExportManagerInterface):
    """Manages export of research reports to multiple formats."""
    
    def __init__(self, export_dir: Optional[str] = None):
        """
        Initialize export manager.
        
        Args:
            export_dir: Directory for exported files
        """
        self.export_dir = Path(export_dir or config.export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        self._supported_formats = ['pdf', 'markdown', 'html', 'txt', 'json']
    
    def export_report(self, 
                     report: ResearchReport, 
                     format_type: str, 
                     output_path: str,
                     options: Optional[ExportOptions] = None) -> str:
        """
        Export research report to specified format.
        
        Args:
            report: Research report to export
            format_type: Export format ('pdf', 'markdown', 'html', 'txt', 'json')
            output_path: Output file path
            options: Export formatting options
            
        Returns:
            Path to exported file
        """ 
        try:
            if format_type.lower() not in self._supported_formats:
                raise ExportError(f"Unsupported format: {format_type}")
            
            options = options or ExportOptions()
            
            # Ensure output directory exists
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Export based on format
            if format_type.lower() == 'pdf':
                return self._export_pdf(report, output_path, options)
            elif format_type.lower() == 'markdown':
                return self._export_markdown(report, output_path, options)
            elif format_type.lower() == 'html':
                return self._export_html(report, output_path, options)
            elif format_type.lower() == 'txt':
                return self._export_txt(report, output_path, options)
            elif format_type.lower() == 'json':
                return self._export_json(report, output_path, options)
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise ExportError(f"Export failed: {e}")
    
    def supported_formats(self) -> List[str]:
        """Return list of supported export formats."""
        return self._supported_formats.copy()
    
    def _export_markdown(self, 
                        report: ResearchReport, 
                        output_path: Path, 
                        options: ExportOptions) -> str:
        """Export report to Markdown format."""
        try:
            content = []
            
            # Title and metadata
            content.append(f"# Research Report: {report.query}")
            content.append("")
            
            if options.include_timestamps:
                content.append(f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
                content.append("")
            
            if options.include_confidence_scores:
                content.append(f"**Confidence Score:** {report.confidence_score:.2f}")
                content.append("")
            
            # Table of contents
            if options.table_of_contents:
                content.extend(self._generate_markdown_toc(report, options))
                content.append("")
            
            # Executive summary
            if options.executive_summary:
                content.append("## Executive Summary")
                content.append("")
                content.append(report.summary)
                content.append("")
            
            # Key findings
            content.append("## Key Findings")
            content.append("")
            for i, finding in enumerate(report.key_findings, 1):
                content.append(f"{i}. {finding}")
            content.append("")
            
            # Reasoning steps
            if options.include_reasoning_steps and report.reasoning_steps:
                content.append("## Reasoning Process")
                content.append("")
                for i, step in enumerate(report.reasoning_steps, 1):
                    content.append(f"### Step {i}: {step.description}")
                    content.append("")
                    content.append(f"**Query:** {step.query}")
                    content.append("")
                    if options.include_confidence_scores:
                        content.append(f"**Confidence:** {step.confidence:.2f}")
                        content.append("")
                    if step.execution_time:
                        content.append(f"**Execution Time:** {step.execution_time:.2f}s")
                        content.append("")
                    content.append("")
            
            # Sources
            if options.include_sources and report.sources:
                content.append("## Sources")
                content.append("")
                for i, source in enumerate(report.sources, 1):
                    content.append(f"### {i}. {source.title}")
                    content.append("")
                    content.append(f"**Source:** {source.source_path}")
                    content.append("")
                    content.append(f"**Format:** {source.format_type.value.upper()}")
                    content.append("")
                    if options.include_metadata and source.metadata:
                        content.append("**Metadata:**")
                        for key, value in source.metadata.items():
                            content.append(f"- {key}: {value}")
                        content.append("")
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            
            logger.info(f"Exported Markdown report to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise ExportError(f"Markdown export failed: {e}")    
   
    def _export_pdf(self, 
                    report: ResearchReport, 
                    output_path: Path, 
                    options: ExportOptions) -> str:
        """Export report to PDF format."""
        try:
            # Try using reportlab for PDF generation
            try:
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
                
                # Create PDF document
                doc = SimpleDocTemplate(str(output_path), pagesize=A4)
                styles = getSampleStyleSheet()
                story = []
                
                # Custom styles
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=18,
                    spaceAfter=30,
                    alignment=TA_CENTER
                )
                
                heading_style = ParagraphStyle(
                    'CustomHeading',
                    parent=styles['Heading2'],
                    fontSize=14,
                    spaceAfter=12,
                    spaceBefore=20
                )
                
                # Title
                story.append(Paragraph(f"Research Report: {report.query}", title_style))
                story.append(Spacer(1, 20))
                
                # Metadata
                if options.include_timestamps:
                    story.append(Paragraph(f"<b>Generated:</b> {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
                
                if options.include_confidence_scores:
                    story.append(Paragraph(f"<b>Confidence Score:</b> {report.confidence_score:.2f}", styles['Normal']))
                
                story.append(Spacer(1, 20))
                
                # Executive Summary
                if options.executive_summary:
                    story.append(Paragraph("Executive Summary", heading_style))
                    story.append(Paragraph(report.summary, styles['Normal']))
                    story.append(Spacer(1, 15))
                
                # Key Findings
                story.append(Paragraph("Key Findings", heading_style))
                for i, finding in enumerate(report.key_findings, 1):
                    story.append(Paragraph(f"{i}. {finding}", styles['Normal']))
                story.append(Spacer(1, 15))
                
                # Reasoning Steps
                if options.include_reasoning_steps and report.reasoning_steps:
                    story.append(Paragraph("Reasoning Process", heading_style))
                    for i, step in enumerate(report.reasoning_steps, 1):
                        story.append(Paragraph(f"Step {i}: {step.description}", styles['Heading3']))
                        story.append(Paragraph(f"<b>Query:</b> {step.query}", styles['Normal']))
                        if options.include_confidence_scores:
                            story.append(Paragraph(f"<b>Confidence:</b> {step.confidence:.2f}", styles['Normal']))
                        story.append(Spacer(1, 10))
                
                # Sources
                if options.include_sources and report.sources:
                    story.append(PageBreak())
                    story.append(Paragraph("Sources", heading_style))
                    for i, source in enumerate(report.sources, 1):
                        story.append(Paragraph(f"{i}. {source.title}", styles['Heading4']))
                        story.append(Paragraph(f"<b>Source:</b> {source.source_path}", styles['Normal']))
                        story.append(Paragraph(f"<b>Format:</b> {source.format_type.value.upper()}", styles['Normal']))
                        story.append(Spacer(1, 10))
                
                # Build PDF
                doc.build(story)
                
            except ImportError:
                # Fallback: create a simple text-based PDF using fpdf
                try:
                    from fpdf import FPDF
                    
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font('Arial', 'B', 16)
                    
                    # Title
                    pdf.cell(0, 10, f'Research Report: {report.query}', 0, 1, 'C')
                    pdf.ln(10)
                    
                    # Content
                    pdf.set_font('Arial', '', 12)
                    
                    # Summary
                    pdf.cell(0, 10, 'Executive Summary:', 0, 1)
                    pdf.set_font('Arial', '', 10)
                    
                    # Split long text into lines
                    summary_lines = self._split_text_for_pdf(report.summary, 80)
                    for line in summary_lines:
                        pdf.cell(0, 6, line, 0, 1)
                    
                    pdf.ln(5)
                    
                    # Key Findings
                    pdf.set_font('Arial', 'B', 12)
                    pdf.cell(0, 10, 'Key Findings:', 0, 1)
                    pdf.set_font('Arial', '', 10)
                    
                    for i, finding in enumerate(report.key_findings, 1):
                        finding_lines = self._split_text_for_pdf(f"{i}. {finding}", 80)
                        for line in finding_lines:
                            pdf.cell(0, 6, line, 0, 1)
                    
                    pdf.output(str(output_path))
                    
                except ImportError:
                    # Final fallback: export as text and inform user
                    txt_path = output_path.with_suffix('.txt')
                    self._export_txt(report, txt_path, options)
                    raise ExportError("PDF libraries not available. Exported as TXT instead.")
            
            logger.info(f"Exported PDF report to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise ExportError(f"PDF export failed: {e}")
    
    def _split_text_for_pdf(self, text: str, max_chars: int) -> List[str]:
        """Split text into lines for PDF generation."""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= max_chars:
                current_line += " " + word if current_line else word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines 
   
    def _export_html(self, 
                    report: ResearchReport, 
                    output_path: Path, 
                    options: ExportOptions) -> str:
        """Export report to HTML format."""
        try:
            html_content = []
            
            # HTML header
            html_content.extend([
                "<!DOCTYPE html>",
                "<html lang='en'>",
                "<head>",
                "    <meta charset='UTF-8'>",
                "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
                f"    <title>Research Report: {report.query}</title>",
                "    <style>",
                "        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }",
                "        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; }",
                "        h2 { color: #34495e; margin-top: 30px; }",
                "        h3 { color: #7f8c8d; }",
                "        .metadata { background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }",
                "        .confidence { color: #27ae60; font-weight: bold; }",
                "        .finding { margin: 10px 0; padding: 10px; background-color: #f8f9fa; border-left: 4px solid #3498db; }",
                "        .source { margin: 15px 0; padding: 15px; background-color: #f1f2f6; border-radius: 5px; }",
                "        .step { margin: 15px 0; padding: 15px; background-color: #fff5f5; border-radius: 5px; }",
                "    </style>",
                "</head>",
                "<body>",
                f"    <h1>Research Report: {report.query}</h1>"
            ])
            
            # Metadata section
            if options.include_timestamps or options.include_confidence_scores:
                html_content.append("    <div class='metadata'>")
                if options.include_timestamps:
                    html_content.append(f"        <p><strong>Generated:</strong> {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>")
                if options.include_confidence_scores:
                    html_content.append(f"        <p><strong>Confidence Score:</strong> <span class='confidence'>{report.confidence_score:.2f}</span></p>")
                html_content.append("    </div>")
            
            # Executive Summary
            if options.executive_summary:
                html_content.extend([
                    "    <h2>Executive Summary</h2>",
                    f"    <p>{self._escape_html(report.summary)}</p>"
                ])
            
            # Key Findings
            html_content.append("    <h2>Key Findings</h2>")
            for i, finding in enumerate(report.key_findings, 1):
                html_content.append(f"    <div class='finding'>{i}. {self._escape_html(finding)}</div>")
            
            # Reasoning Steps
            if options.include_reasoning_steps and report.reasoning_steps:
                html_content.append("    <h2>Reasoning Process</h2>")
                for i, step in enumerate(report.reasoning_steps, 1):
                    html_content.extend([
                        "    <div class='step'>",
                        f"        <h3>Step {i}: {self._escape_html(step.description)}</h3>",
                        f"        <p><strong>Query:</strong> {self._escape_html(step.query)}</p>"
                    ])
                    if options.include_confidence_scores:
                        html_content.append(f"        <p><strong>Confidence:</strong> {step.confidence:.2f}</p>")
                    if step.execution_time:
                        html_content.append(f"        <p><strong>Execution Time:</strong> {step.execution_time:.2f}s</p>")
                    html_content.append("    </div>")
            
            # Sources
            if options.include_sources and report.sources:
                html_content.append("    <h2>Sources</h2>")
                for i, source in enumerate(report.sources, 1):
                    html_content.extend([
                        "    <div class='source'>",
                        f"        <h3>{i}. {self._escape_html(source.title)}</h3>",
                        f"        <p><strong>Source:</strong> {self._escape_html(source.source_path)}</p>",
                        f"        <p><strong>Format:</strong> {source.format_type.value.upper()}</p>"
                    ])
                    if options.include_metadata and source.metadata:
                        html_content.append("        <p><strong>Metadata:</strong></p>")
                        html_content.append("        <ul>")
                        for key, value in source.metadata.items():
                            html_content.append(f"            <li>{self._escape_html(str(key))}: {self._escape_html(str(value))}</li>")
                        html_content.append("        </ul>")
                    html_content.append("    </div>")
            
            # HTML footer
            html_content.extend([
                "</body>",
                "</html>"
            ])
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(html_content))
            
            logger.info(f"Exported HTML report to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise ExportError(f"HTML export failed: {e}")
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))
    
    def _export_txt(self, 
                   report: ResearchReport, 
                   output_path: Path, 
                   options: ExportOptions) -> str:
        """Export report to plain text format."""
        try:
            content = []
            
            # Title
            title = f"RESEARCH REPORT: {report.query.upper()}"
            content.append(title)
            content.append("=" * len(title))
            content.append("")
            
            # Metadata
            if options.include_timestamps:
                content.append(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if options.include_confidence_scores:
                content.append(f"Confidence Score: {report.confidence_score:.2f}")
            content.append("")
            
            # Executive Summary
            if options.executive_summary:
                content.append("EXECUTIVE SUMMARY")
                content.append("-" * 17)
                content.append(report.summary)
                content.append("")
            
            # Key Findings
            content.append("KEY FINDINGS")
            content.append("-" * 12)
            for i, finding in enumerate(report.key_findings, 1):
                content.append(f"{i}. {finding}")
            content.append("")
            
            # Reasoning Steps
            if options.include_reasoning_steps and report.reasoning_steps:
                content.append("REASONING PROCESS")
                content.append("-" * 17)
                for i, step in enumerate(report.reasoning_steps, 1):
                    content.append(f"Step {i}: {step.description}")
                    content.append(f"Query: {step.query}")
                    if options.include_confidence_scores:
                        content.append(f"Confidence: {step.confidence:.2f}")
                    if step.execution_time:
                        content.append(f"Execution Time: {step.execution_time:.2f}s")
                    content.append("")
            
            # Sources
            if options.include_sources and report.sources:
                content.append("SOURCES")
                content.append("-" * 7)
                for i, source in enumerate(report.sources, 1):
                    content.append(f"{i}. {source.title}")
                    content.append(f"   Source: {source.source_path}")
                    content.append(f"   Format: {source.format_type.value.upper()}")
                    if options.include_metadata and source.metadata:
                        content.append("   Metadata:")
                        for key, value in source.metadata.items():
                            content.append(f"     - {key}: {value}")
                    content.append("")
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            
            logger.info(f"Exported TXT report to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise ExportError(f"TXT export failed: {e}")
    
    def _export_json(self, 
                    report: ResearchReport, 
                    output_path: Path, 
                    options: ExportOptions) -> str:
        """Export report to JSON format."""
        try:
            import json
            
            # Convert report to dictionary
            report_dict = {
                'query': report.query,
                'summary': report.summary,
                'key_findings': report.key_findings,
                'confidence_score': report.confidence_score,
                'generated_at': report.generated_at.isoformat(),
                'metadata': report.metadata
            }
            
            # Add reasoning steps if requested
            if options.include_reasoning_steps and report.reasoning_steps:
                report_dict['reasoning_steps'] = []
                for step in report.reasoning_steps:
                    step_dict = {
                        'step_id': step.step_id,
                        'description': step.description,
                        'query': step.query,
                        'confidence': step.confidence,
                        'dependencies': step.dependencies,
                        'results': step.results,
                        'execution_time': step.execution_time,
                        'created_at': step.created_at.isoformat()
                    }
                    report_dict['reasoning_steps'].append(step_dict)
            
            # Add sources if requested
            if options.include_sources and report.sources:
                report_dict['sources'] = []
                for source in report.sources:
                    source_dict = {
                        'id': source.id,
                        'title': source.title,
                        'source_path': source.source_path,
                        'format_type': source.format_type.value,
                        'word_count': source.word_count,
                        'chunk_count': source.chunk_count,
                        'created_at': source.created_at.isoformat()
                    }
                    if options.include_metadata:
                        source_dict['metadata'] = source.metadata
                    report_dict['sources'].append(source_dict)
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported JSON report to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise ExportError(f"JSON export failed: {e}")
    
    def _generate_markdown_toc(self, report: ResearchReport, options: ExportOptions) -> List[str]:
        """Generate table of contents for Markdown."""
        toc = ["## Table of Contents", ""]
        
        if options.executive_summary:
            toc.append("- [Executive Summary](#executive-summary)")
        
        toc.append("- [Key Findings](#key-findings)")
        
        if options.include_reasoning_steps and report.reasoning_steps:
            toc.append("- [Reasoning Process](#reasoning-process)")
        
        if options.include_sources and report.sources:
            toc.append("- [Sources](#sources)")
        
        return toc