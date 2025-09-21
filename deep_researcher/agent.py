"""Main ResearchAgent class that orchestrates all components."""

import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from .config import config
from .models import Document, ProcessedQuery, ResearchReport
from .exceptions import DeepResearcherError
from .logging_config import get_logger, log_performance, LoggingManager
from .error_recovery import with_retry, graceful_degradation, get_error_recovery_manager

# Import all components
from .ingestion import DocumentIngester, TextProcessor
from .embeddings import EmbeddingGenerator, ModelManager
from .storage import VectorStore, DocumentStore
from .reasoning import QueryProcessor, MultiStepReasoner, DocumentRetriever
from .synthesis import ResultSynthesizer, ReasoningExplainer, ExportManager, ReportGenerator
from .session import SessionManager, QueryRefiner

logger = get_logger(__name__)


class ResearchAgent:
    """Main orchestrator class for the Deep Researcher Agent."""
    
    def __init__(self, 
                 data_dir: Optional[str] = None,
                 embedding_model: Optional[str] = None,
                 initialize_components: bool = True,
                 log_level: str = "INFO"):
        """
        Initialize the Research Agent.
        
        Args:
            data_dir: Directory for data storage
            embedding_model: Embedding model to use
            initialize_components: Whether to initialize all components immediately
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        try:
            # Initialize logging first
            self.logging_manager = LoggingManager(
                log_dir=data_dir + "/logs" if data_dir else None,
                log_level=log_level
            )
            
            logger.info("Initializing Deep Researcher Agent...")
            
            # Update config if provided
            if data_dir:
                config.data_dir = data_dir
            if embedding_model:
                config.embedding_model = embedding_model
            
            # Ensure directories exist
            config.ensure_directories()
            
            # Initialize error recovery manager
            self.error_recovery_manager = get_error_recovery_manager()
            
            # Initialize components
            self.components_initialized = False
            if initialize_components:
                self._initialize_components()
            
            logger.info("Deep Researcher Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Research Agent: {e}", exc_info=True)
            raise DeepResearcherError(f"Initialization failed: {e}")
    
    def _initialize_components(self) -> None:
        """Initialize all system components."""
        try:
            logger.info("Initializing system components...")
            
            # Core processing components
            self.document_ingester = DocumentIngester()
            self.text_processor = TextProcessor()
            
            # Embedding and model management
            self.model_manager = ModelManager()
            self.embedding_generator = self.model_manager.get_model()
            
            # Storage components
            self.vector_store = VectorStore(dimension=self.embedding_generator.embedding_dimension)
            self.document_store = DocumentStore()
            
            # Reasoning components
            self.query_processor = QueryProcessor()
            self.multi_step_reasoner = MultiStepReasoner()
            self.document_retriever = DocumentRetriever(
                self.vector_store,
                self.document_store,
                self.embedding_generator
            )
            
            # Synthesis components
            self.result_synthesizer = ResultSynthesizer()
            self.reasoning_explainer = ReasoningExplainer()
            self.export_manager = ExportManager()
            self.report_generator = ReportGenerator()
            
            # Session management
            self.session_manager = SessionManager()
            self.query_refiner = QueryRefiner()
            
            self.components_initialized = True
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            raise DeepResearcherError(f"Component initialization failed: {e}")
    
    @with_retry(max_retries=2, delay=1.0)
    def ingest_documents(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Ingest documents into the system.
        
        Args:
            file_paths: List of file paths to ingest
            
        Returns:
            Ingestion results summary
        """
        try:
            if not self.components_initialized:
                self._initialize_components()
            
            logger.info(f"Ingesting {len(file_paths)} documents...")
            start_time = time.time()
            
            # Ingest documents
            documents = self.document_ingester.batch_ingest(file_paths)
            
            # Process and store documents
            total_chunks = 0
            stored_documents = []
            
            for document in documents:
                try:
                    # Process text into chunks
                    chunks = self.text_processor.process_text(
                        document.content,
                        metadata={'document_id': document.id}
                    )
                    
                    # Add chunks to document
                    for chunk in chunks:
                        document.add_chunk(chunk)
                    
                    # Store document
                    self.document_store.store_document(document)
                    
                    # Generate embeddings for chunks
                    if chunks:
                        chunk_texts = [chunk.content for chunk in chunks]
                        embeddings = self.embedding_generator.generate_embeddings(chunk_texts)
                        
                        # Store embeddings with metadata
                        chunk_metadata = []
                        for chunk in chunks:
                            chunk_metadata.append({
                                'document_id': document.id,
                                'chunk_id': chunk.id,
                                'chunk_index': chunk.chunk_index
                            })
                        
                        self.vector_store.add_vectors(embeddings, chunk_metadata)
                    
                    stored_documents.append(document)
                    total_chunks += len(chunks)
                    
                except Exception as e:
                    logger.error(f"Failed to process document {document.source_path}: {e}")
                    continue
            
            processing_time = time.time() - start_time
            
            # Log performance metrics
            log_performance(
                logger, "document_ingestion", processing_time,
                documents_processed=len(stored_documents),
                total_chunks=total_chunks,
                documents_per_second=len(stored_documents) / processing_time if processing_time > 0 else 0,
                failed_documents=len(file_paths) - len(stored_documents)
            )
            
            result = {
                'success': True,
                'documents_processed': len(stored_documents),
                'total_chunks': total_chunks,
                'processing_time': processing_time,
                'documents_per_second': len(stored_documents) / processing_time if processing_time > 0 else 0,
                'failed_documents': len(file_paths) - len(stored_documents)
            }
            
            logger.info(f"Ingestion completed: {len(stored_documents)} documents, {total_chunks} chunks in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Document ingestion failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'documents_processed': 0,
                'total_chunks': 0,
                'processing_time': time.time() - start_time
            }
    
    @with_retry(max_retries=1, delay=2.0)
    def research(self, 
                query: str,
                session_id: Optional[str] = None,
                max_sources: int = 10) -> Dict[str, Any]:
        """
        Conduct research on a query.
        
        Args:
            query: Research query
            session_id: Optional session ID for context
            max_sources: Maximum number of sources to retrieve
            
        Returns:
            Research results with report and metadata
        """
        try:
            if not self.components_initialized:
                self._initialize_components()
            
            logger.info(f"Starting research for query: {query}")
            start_time = time.time()
            
            # Get session context if available
            session_context = {}
            session = None
            if session_id:
                session = self.session_manager.get_session(session_id)
                if session:
                    session_context = self.session_manager.get_session_context_for_query(session_id)
            
            # Process query
            processed_query = self.query_processor.process_query(query)
            
            # Execute reasoning
            reasoning_context = self.multi_step_reasoner.execute_full_reasoning(processed_query)
            
            # Retrieve relevant documents
            documents = self.document_retriever.retrieve_by_query(query, k=max_sources)
            
            # Synthesize results
            research_report = self.result_synthesizer.synthesize_results(
                documents, 
                query, 
                reasoning_context.steps
            )
            
            # Generate reasoning explanation
            reasoning_explanation = self.reasoning_explainer.explain_reasoning_process(reasoning_context)
            
            execution_time = time.time() - start_time
            
            # Log performance metrics
            log_performance(
                logger, "research_query", execution_time,
                query_complexity=processed_query.complexity_score,
                sources_found=len(documents),
                reasoning_steps=len(reasoning_context.steps),
                confidence_score=research_report.confidence_score
            )
            
            # Add to session if provided
            if session_id:
                self.session_manager.add_query_to_session(
                    session_id,
                    query,
                    processed_query,
                    research_report,
                    reasoning_context,
                    execution_time,
                    success=True
                )
            
            result = {
                'success': True,
                'research_report': research_report,
                'reasoning_explanation': reasoning_explanation,
                'processed_query': processed_query,
                'execution_time': execution_time,
                'sources_found': len(documents),
                'reasoning_steps': len(reasoning_context.steps),
                'session_id': session_id
            }
            
            logger.info(f"Research completed in {execution_time:.2f}s with {len(documents)} sources")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Research failed: {e}", exc_info=True)
            
            # Log failed performance
            log_performance(
                logger, "research_query_failed", execution_time,
                error=str(e),
                query_length=len(query)
            )
            
            # Add failed query to session if provided
            if session_id:
                try:
                    processed_query = self.query_processor.process_query(query)
                    self.session_manager.add_query_to_session(
                        session_id,
                        query,
                        processed_query,
                        execution_time=execution_time,
                        success=False
                    )
                except Exception as session_error:
                    logger.warning(f"Failed to add failed query to session: {session_error}")
            
            return {
                'success': False,
                'error': str(e),
                'execution_time': execution_time,
                'session_id': session_id
            }
    
    def create_session(self, title: str = "Research Session", description: str = "") -> str:
        """
        Create a new research session.
        
        Args:
            title: Session title
            description: Session description
            
        Returns:
            Session ID
        """
        try:
            if not self.components_initialized:
                self._initialize_components()
            
            session = self.session_manager.create_session(title, description)
            logger.info(f"Created session: {session.session_id}")
            return session.session_id
            
        except Exception as e:
            logger.error(f"Session creation failed: {e}")
            raise DeepResearcherError(f"Session creation failed: {e}")
    
    def get_query_suggestions(self, 
                            query: str,
                            session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get query refinement suggestions.
        
        Args:
            query: Original query
            session_id: Optional session ID for context
            
        Returns:
            List of query suggestions
        """
        try:
            if not self.components_initialized:
                self._initialize_components()
            
            # Get session context
            session = None
            if session_id:
                session = self.session_manager.get_session(session_id)
            
            # Process query for analysis
            processed_query = self.query_processor.process_query(query)
            
            # Get refinement analysis
            analysis = self.query_refiner.analyze_query_for_refinement(
                query, processed_query, session
            )
            
            # Convert suggestions to dict format
            suggestions = []
            for suggestion in analysis.suggested_refinements:
                suggestions.append({
                    'suggested_query': suggestion.suggested_query,
                    'refinement_type': suggestion.refinement_type.value,
                    'rationale': suggestion.rationale,
                    'confidence': suggestion.confidence,
                    'expected_improvement': suggestion.expected_improvement
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Query suggestion generation failed: {e}")
            return []
    
    def export_report(self, 
                     research_report: ResearchReport,
                     output_path: str,
                     format_type: str = "markdown",
                     template: str = "academic") -> str:
        """
        Export research report to file.
        
        Args:
            research_report: Research report to export
            output_path: Output file path
            format_type: Export format (pdf, markdown, html, txt, json)
            template: Report template (executive, academic, technical, etc.)
            
        Returns:
            Path to exported file
        """
        try:
            if not self.components_initialized:
                self._initialize_components()
            
            # Generate structured report if using template
            if template != "raw":
                from .synthesis.report_generator import ReportTemplate
                
                template_enum = ReportTemplate(template)
                structured_report = self.report_generator.generate_structured_report(
                    research_report, template_enum
                )
                
                # Convert structured report back to ResearchReport for export
                # (This is a simplified approach - could be enhanced)
                enhanced_report = ResearchReport(
                    query=research_report.query,
                    summary=structured_report.sections[0].content if structured_report.sections else research_report.summary,
                    key_findings=research_report.key_findings,
                    sources=research_report.sources,
                    reasoning_steps=research_report.reasoning_steps,
                    confidence_score=research_report.confidence_score,
                    metadata=research_report.metadata
                )
                
                export_path = self.export_manager.export_report(
                    enhanced_report, format_type, output_path
                )
            else:
                export_path = self.export_manager.export_report(
                    research_report, format_type, output_path
                )
            
            logger.info(f"Report exported to: {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"Report export failed: {e}")
            raise DeepResearcherError(f"Report export failed: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get system status and statistics.
        
        Returns:
            System status information
        """
        try:
            status = {
                'components_initialized': self.components_initialized,
                'config': {
                    'data_dir': config.data_dir,
                    'embedding_model': config.embedding_model,
                    'chunk_size': config.chunk_size,
                    'default_k': config.default_k
                },
                'error_recovery_stats': self.error_recovery_manager.get_recovery_stats()
            }
            
            if self.components_initialized:
                # Storage statistics
                status['storage'] = {
                    'vector_store': self.vector_store.get_statistics(),
                    'document_store': self.document_store.get_statistics()
                }
                
                # Model information
                status['models'] = {
                    'embedding_model': self.embedding_generator.get_model_info(),
                    'model_manager': self.model_manager.get_status()
                }
                
                # Session statistics
                status['sessions'] = self.session_manager.get_session_statistics()
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}", exc_info=True)
            return {
                'error': str(e),
                'components_initialized': self.components_initialized,
                'error_recovery_stats': self.error_recovery_manager.get_recovery_stats() if hasattr(self, 'error_recovery_manager') else {}
            }
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get comprehensive system health information.
        
        Returns:
            System health status with diagnostics
        """
        try:
            health = {
                'overall_status': 'healthy',
                'timestamp': time.time(),
                'issues': [],
                'warnings': []
            }
            
            # Check component initialization
            if not self.components_initialized:
                health['issues'].append("Components not initialized")
                health['overall_status'] = 'unhealthy'
            
            # Check error recovery statistics
            recovery_stats = self.error_recovery_manager.get_recovery_stats()
            if recovery_stats['total_errors'] > 0:
                recovery_rate = recovery_stats['recovery_rate']
                if recovery_rate < 0.5:
                    health['issues'].append(f"Low error recovery rate: {recovery_rate:.2%}")
                    health['overall_status'] = 'degraded'
                elif recovery_rate < 0.8:
                    health['warnings'].append(f"Moderate error recovery rate: {recovery_rate:.2%}")
            
            # Check storage health
            if self.components_initialized:
                try:
                    vector_stats = self.vector_store.get_statistics()
                    doc_stats = self.document_store.get_statistics()
                    
                    if vector_stats['total_vectors'] == 0:
                        health['warnings'].append("No documents indexed")
                    
                    if doc_stats['total_documents'] == 0:
                        health['warnings'].append("No documents stored")
                        
                except Exception as e:
                    health['issues'].append(f"Storage health check failed: {e}")
                    health['overall_status'] = 'degraded'
            
            # Set overall status based on issues
            if health['issues'] and health['overall_status'] == 'healthy':
                health['overall_status'] = 'degraded'
            
            health['recovery_statistics'] = recovery_stats
            
            return health
            
        except Exception as e:
            logger.error(f"System health check failed: {e}", exc_info=True)
            return {
                'overall_status': 'unhealthy',
                'error': str(e),
                'timestamp': time.time()
            }
    
    def cleanup(self) -> None:
        """Clean up system resources."""
        try:
            logger.info("Cleaning up system resources...")
            
            if hasattr(self, 'session_manager'):
                self.session_manager.cleanup_expired_sessions()
            
            if hasattr(self, 'model_manager'):
                self.model_manager.cleanup_old_models()
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()