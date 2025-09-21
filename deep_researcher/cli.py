"""Command-line interface for Deep Researcher Agent."""

import click
import json
import sys
from pathlib import Path
from typing import Optional, List
import logging

from .agent import ResearchAgent
from .config import config
from .exceptions import DeepResearcherError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--data-dir', default=None, help='Data directory for storage')
@click.option('--embedding-model', default=None, help='Embedding model to use')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, data_dir: Optional[str], embedding_model: Optional[str], verbose: bool):
    """Deep Researcher Agent - Local AI-powered research system."""
    
    # Set up logging
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize context
    ctx.ensure_object(dict)
    ctx.obj['data_dir'] = data_dir
    ctx.obj['embedding_model'] = embedding_model


@cli.command()
@click.argument('files', nargs=-1, required=True)
@click.option('--batch-size', default=10, help='Batch size for processing')
@click.pass_context
def ingest(ctx, files: tuple, batch_size: int):
    """Ingest documents into the research system."""
    
    try:
        click.echo("🔄 Initializing Deep Researcher Agent...")
        
        with ResearchAgent(
            data_dir=ctx.obj['data_dir'],
            embedding_model=ctx.obj['embedding_model']
        ) as agent:
            
            # Convert file patterns to actual file paths
            file_paths = []
            for file_pattern in files:
                if '*' in file_pattern or '?' in file_pattern:
                    import glob
                    file_paths.extend(glob.glob(file_pattern))
                else:
                    file_paths.append(file_pattern)
            
            # Validate files exist
            valid_files = []
            for file_path in file_paths:
                if Path(file_path).exists():
                    valid_files.append(file_path)
                else:
                    click.echo(f"⚠️  File not found: {file_path}", err=True)
            
            if not valid_files:
                click.echo("❌ No valid files found to ingest", err=True)
                sys.exit(1)
            
            click.echo(f"📄 Ingesting {len(valid_files)} documents...")
            
            # Process files in batches
            total_processed = 0
            total_chunks = 0
            
            for i in range(0, len(valid_files), batch_size):
                batch = valid_files[i:i + batch_size]
                click.echo(f"Processing batch {i//batch_size + 1}: {len(batch)} files")
                
                result = agent.ingest_documents(batch)
                
                if result['success']:
                    total_processed += result['documents_processed']
                    total_chunks += result['total_chunks']
                    
                    click.echo(f"✅ Batch completed: {result['documents_processed']} documents, "
                             f"{result['total_chunks']} chunks in {result['processing_time']:.2f}s")
                else:
                    click.echo(f"❌ Batch failed: {result.get('error', 'Unknown error')}", err=True)
            
            click.echo(f"\n🎉 Ingestion completed!")
            click.echo(f"📊 Total: {total_processed} documents, {total_chunks} chunks")
            
    except Exception as e:
        click.echo(f"❌ Ingestion failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('query')
@click.option('--session-id', default=None, help='Session ID for context')
@click.option('--max-sources', default=10, help='Maximum sources to retrieve')
@click.option('--output', '-o', default=None, help='Output file for results')
@click.option('--format', 'output_format', default='markdown', 
              type=click.Choice(['markdown', 'pdf', 'html', 'txt', 'json']),
              help='Output format')
@click.option('--template', default='academic',
              type=click.Choice(['executive', 'academic', 'technical', 'comparative', 'analytical', 'summary']),
              help='Report template')
@click.pass_context
def research(ctx, query: str, session_id: Optional[str], max_sources: int, 
            output: Optional[str], output_format: str, template: str):
    """Conduct research on a query."""
    
    try:
        click.echo("🔄 Initializing Deep Researcher Agent...")
        
        with ResearchAgent(
            data_dir=ctx.obj['data_dir'],
            embedding_model=ctx.obj['embedding_model']
        ) as agent:
            
            click.echo(f"🔍 Researching: {query}")
            
            # Conduct research
            result = agent.research(
                query=query,
                session_id=session_id,
                max_sources=max_sources
            )
            
            if not result['success']:
                click.echo(f"❌ Research failed: {result.get('error', 'Unknown error')}", err=True)
                sys.exit(1)
            
            research_report = result['research_report']
            
            # Display results
            click.echo(f"\n✅ Research completed in {result['execution_time']:.2f}s")
            click.echo(f"📊 Found {result['sources_found']} sources, {result['reasoning_steps']} reasoning steps")
            click.echo(f"🎯 Confidence: {research_report.confidence_score:.2f}")
            
            click.echo(f"\n📋 Summary:")
            click.echo(research_report.summary)
            
            click.echo(f"\n🔑 Key Findings:")
            for i, finding in enumerate(research_report.key_findings, 1):
                click.echo(f"{i}. {finding}")
            
            # Export if requested
            if output:
                click.echo(f"\n💾 Exporting report...")
                
                export_path = agent.export_report(
                    research_report=research_report,
                    output_path=output,
                    format_type=output_format,
                    template=template
                )
                
                click.echo(f"✅ Report exported to: {export_path}")
            
            # Show session info if used
            if session_id:
                click.echo(f"\n📝 Session: {session_id}")
            
    except Exception as e:
        click.echo(f"❌ Research failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--title', default='Research Session', help='Session title')
@click.option('--description', default='', help='Session description')
@click.pass_context
def create_session(ctx, title: str, description: str):
    """Create a new research session."""
    
    try:
        with ResearchAgent(
            data_dir=ctx.obj['data_dir'],
            embedding_model=ctx.obj['embedding_model']
        ) as agent:
            
            session_id = agent.create_session(title, description)
            
            click.echo(f"✅ Created session: {session_id}")
            click.echo(f"📝 Title: {title}")
            if description:
                click.echo(f"📄 Description: {description}")
            
    except Exception as e:
        click.echo(f"❌ Session creation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('query')
@click.option('--session-id', default=None, help='Session ID for context')
@click.pass_context
def suggest(ctx, query: str, session_id: Optional[str]):
    """Get query refinement suggestions."""
    
    try:
        with ResearchAgent(
            data_dir=ctx.obj['data_dir'],
            embedding_model=ctx.obj['embedding_model']
        ) as agent:
            
            suggestions = agent.get_query_suggestions(query, session_id)
            
            if not suggestions:
                click.echo("💡 No suggestions available for this query")
                return
            
            click.echo(f"💡 Query suggestions for: {query}\n")
            
            for i, suggestion in enumerate(suggestions, 1):
                click.echo(f"{i}. {suggestion['suggested_query']}")
                click.echo(f"   Type: {suggestion['refinement_type']}")
                click.echo(f"   Rationale: {suggestion['rationale']}")
                click.echo(f"   Confidence: {suggestion['confidence']:.2f}")
                click.echo()
            
    except Exception as e:
        click.echo(f"❌ Suggestion generation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status and statistics."""
    
    try:
        with ResearchAgent(
            data_dir=ctx.obj['data_dir'],
            embedding_model=ctx.obj['embedding_model']
        ) as agent:
            
            status_info = agent.get_system_status()
            
            if 'error' in status_info:
                click.echo(f"❌ Status check failed: {status_info['error']}", err=True)
                return
            
            click.echo("📊 Deep Researcher Agent Status\n")
            
            # Configuration
            click.echo("⚙️  Configuration:")
            config_info = status_info['config']
            click.echo(f"   Data Directory: {config_info['data_dir']}")
            click.echo(f"   Embedding Model: {config_info['embedding_model']}")
            click.echo(f"   Chunk Size: {config_info['chunk_size']}")
            click.echo()
            
            # Error Recovery Statistics
            recovery_stats = status_info.get('error_recovery_stats', {})
            if recovery_stats.get('total_errors', 0) > 0:
                click.echo("🔧 Error Recovery:")
                click.echo(f"   Total Errors: {recovery_stats['total_errors']}")
                click.echo(f"   Recovered: {recovery_stats['recovered_errors']}")
                click.echo(f"   Recovery Rate: {recovery_stats['recovery_rate']:.2%}")
                click.echo()
            
            if status_info['components_initialized']:
                # Storage statistics
                storage = status_info['storage']
                click.echo("💾 Storage:")
                
                vector_stats = storage['vector_store']
                click.echo(f"   Vector Store: {vector_stats['total_vectors']} vectors")
                click.echo(f"   Active Vectors: {vector_stats['active_vectors']}")
                
                doc_stats = storage['document_store']
                click.echo(f"   Documents: {doc_stats['total_documents']}")
                click.echo(f"   Chunks: {doc_stats['total_chunks']}")
                click.echo()
                
                # Model information
                models = status_info['models']
                click.echo("🤖 Models:")
                
                embedding_info = models['embedding_model']
                click.echo(f"   Embedding Model: {embedding_info['model_name']}")
                click.echo(f"   Dimension: {embedding_info['embedding_dimension']}")
                
                model_manager = models['model_manager']
                click.echo(f"   Loaded Models: {model_manager['loaded_models']}")
                click.echo()
                
                # Session statistics
                sessions = status_info['sessions']
                click.echo("📝 Sessions:")
                click.echo(f"   Total Sessions: {sessions['total_sessions']}")
                click.echo(f"   Total Queries: {sessions['total_queries']}")
                click.echo(f"   Success Rate: {sessions['overall_success_rate']:.2%}")
            else:
                click.echo("⚠️  Components not initialized")
            
    except Exception as e:
        click.echo(f"❌ Status check failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def health(ctx):
    """Check system health and diagnostics."""
    
    try:
        with ResearchAgent(
            data_dir=ctx.obj['data_dir'],
            embedding_model=ctx.obj['embedding_model']
        ) as agent:
            
            health_info = agent.get_system_health()
            
            if 'error' in health_info:
                click.echo(f"❌ Health check failed: {health_info['error']}", err=True)
                return
            
            # Overall status
            status = health_info['overall_status']
            if status == 'healthy':
                click.echo("✅ System Status: HEALTHY")
            elif status == 'degraded':
                click.echo("⚠️  System Status: DEGRADED")
            else:
                click.echo("❌ System Status: UNHEALTHY")
            
            click.echo()
            
            # Issues
            if health_info.get('issues'):
                click.echo("🚨 Issues:")
                for issue in health_info['issues']:
                    click.echo(f"   • {issue}")
                click.echo()
            
            # Warnings
            if health_info.get('warnings'):
                click.echo("⚠️  Warnings:")
                for warning in health_info['warnings']:
                    click.echo(f"   • {warning}")
                click.echo()
            
            # Recovery statistics
            recovery_stats = health_info.get('recovery_statistics', {})
            if recovery_stats.get('total_errors', 0) > 0:
                click.echo("📈 Error Recovery Statistics:")
                click.echo(f"   Total Errors: {recovery_stats['total_errors']}")
                click.echo(f"   Recovered: {recovery_stats['recovered_errors']}")
                click.echo(f"   Failed Recoveries: {recovery_stats['failed_recoveries']}")
                click.echo(f"   Recovery Rate: {recovery_stats['recovery_rate']:.2%}")
                
                if recovery_stats.get('recovery_strategies_used'):
                    click.echo("   Strategies Used:")
                    for strategy, count in recovery_stats['recovery_strategies_used'].items():
                        click.echo(f"     - {strategy}: {count}")
            
            if status == 'healthy':
                click.echo("\n🎉 All systems operational!")
            
    except Exception as e:
        click.echo(f"❌ Health check failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def interactive(ctx):
    """Start interactive research mode."""
    
    try:
        click.echo("🚀 Starting Deep Researcher Agent Interactive Mode")
        click.echo("Type 'help' for commands, 'quit' to exit\n")
        
        with ResearchAgent(
            data_dir=ctx.obj['data_dir'],
            embedding_model=ctx.obj['embedding_model']
        ) as agent:
            
            session_id = None
            
            while True:
                try:
                    user_input = click.prompt("🔍", type=str).strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        click.echo("👋 Goodbye!")
                        break
                    
                    elif user_input.lower() == 'help':
                        click.echo("Available commands:")
                        click.echo("  research <query>     - Conduct research")
                        click.echo("  suggest <query>      - Get query suggestions")
                        click.echo("  session new          - Create new session")
                        click.echo("  session info         - Show current session")
                        click.echo("  status               - Show system status")
                        click.echo("  help                 - Show this help")
                        click.echo("  quit                 - Exit interactive mode")
                        continue
                    
                    elif user_input.lower().startswith('research '):
                        query = user_input[9:].strip()
                        if not query:
                            click.echo("❌ Please provide a query")
                            continue
                        
                        click.echo(f"🔍 Researching: {query}")
                        result = agent.research(query, session_id=session_id)
                        
                        if result['success']:
                            report = result['research_report']
                            click.echo(f"✅ Research completed ({result['execution_time']:.2f}s)")
                            click.echo(f"📊 Confidence: {report.confidence_score:.2f}")
                            click.echo(f"\n📋 {report.summary}")
                            
                            click.echo(f"\n🔑 Key Findings:")
                            for i, finding in enumerate(report.key_findings[:3], 1):
                                click.echo(f"{i}. {finding}")
                        else:
                            click.echo(f"❌ Research failed: {result.get('error', 'Unknown error')}")
                    
                    elif user_input.lower().startswith('suggest '):
                        query = user_input[8:].strip()
                        if not query:
                            click.echo("❌ Please provide a query")
                            continue
                        
                        suggestions = agent.get_query_suggestions(query, session_id)
                        
                        if suggestions:
                            click.echo(f"💡 Suggestions for: {query}")
                            for i, suggestion in enumerate(suggestions[:3], 1):
                                click.echo(f"{i}. {suggestion['suggested_query']}")
                        else:
                            click.echo("💡 No suggestions available")
                    
                    elif user_input.lower() == 'session new':
                        title = click.prompt("Session title", default="Interactive Session")
                        session_id = agent.create_session(title)
                        click.echo(f"✅ Created session: {session_id}")
                    
                    elif user_input.lower() == 'session info':
                        if session_id:
                            click.echo(f"📝 Current session: {session_id}")
                        else:
                            click.echo("📝 No active session")
                    
                    elif user_input.lower() == 'status':
                        status_info = agent.get_system_status()
                        if 'storage' in status_info:
                            doc_count = status_info['storage']['document_store']['total_documents']
                            vector_count = status_info['storage']['vector_store']['total_vectors']
                            click.echo(f"📊 {doc_count} documents, {vector_count} vectors indexed")
                        else:
                            click.echo("📊 System not fully initialized")
                    
                    else:
                        click.echo("❓ Unknown command. Type 'help' for available commands.")
                
                except KeyboardInterrupt:
                    click.echo("\n👋 Goodbye!")
                    break
                except EOFError:
                    click.echo("\n👋 Goodbye!")
                    break
                except Exception as e:
                    click.echo(f"❌ Error: {e}")
    
    except Exception as e:
        click.echo(f"❌ Interactive mode failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def cleanup(ctx):
    """Clean up system resources and expired data."""
    
    try:
        with ResearchAgent(
            data_dir=ctx.obj['data_dir'],
            embedding_model=ctx.obj['embedding_model']
        ) as agent:
            
            click.echo("🧹 Cleaning up system resources...")
            agent.cleanup()
            click.echo("✅ Cleanup completed")
            
    except Exception as e:
        click.echo(f"❌ Cleanup failed: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()