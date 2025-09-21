# Deep Researcher Agent

A sophisticated local AI-powered research system that can search, analyze, and synthesize information from large-scale data sources without external API dependencies.

## Features

🔍 **Intelligent Research**: Multi-step reasoning with query decomposition and analysis  
📄 **Multi-Format Support**: PDF, DOCX, TXT, Markdown, HTML document ingestion  
🧠 **Local AI**: Sentence-transformers for embedding generation (no external APIs)  
💾 **Efficient Storage**: FAISS vector search with SQLite metadata storage  
🔄 **Interactive Sessions**: Multi-turn conversations with context preservation  
📊 **Professional Reports**: Multiple export formats (PDF, Markdown, HTML, JSON)  
🎯 **Query Refinement**: Intelligent suggestions for improving research queries  
🔬 **Reasoning Transparency**: Complete explanations of the analysis process  

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/deepresearcher/deep-researcher-agent.git
cd deep-researcher-agent

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Basic Usage

1. **Ingest Documents**
```bash
# Ingest documents into the system
deep-researcher ingest documents/*.pdf documents/*.txt

# Or use patterns
deep-researcher ingest "research_papers/**/*.pdf"
```

2. **Conduct Research**
```bash
# Simple research query
deep-researcher research "What is machine learning?"

# Research with export
deep-researcher research "Compare Python vs Java" --output report.pdf --format pdf --template comparative
```

3. **Interactive Mode**
```bash
# Start interactive research session
deep-researcher interactive
```

4. **Session Management**
```bash
# Create a research session
deep-researcher create-session --title "AI Research" --description "Exploring AI technologies"

# Research within a session (maintains context)
deep-researcher research "What is deep learning?" --session-id <session-id>
```

### Python API

```python
from deep_researcher import ResearchAgent

# Initialize the agent
with ResearchAgent() as agent:
    # Ingest documents
    result = agent.ingest_documents(['document1.pdf', 'document2.txt'])
    
    # Conduct research
    research_result = agent.research("What are the latest developments in AI?")
    
    # Export report
    agent.export_report(
        research_result['research_report'],
        'ai_research_report.pdf',
        format_type='pdf',
        template='academic'
    )
```

## Architecture

The Deep Researcher Agent consists of several integrated components:

### Core Components

- **Document Ingestion**: Multi-format document processing and text extraction
- **Embedding Generation**: Local sentence-transformer models for semantic understanding
- **Vector Storage**: FAISS-based similarity search with metadata
- **Query Processing**: Intelligent query analysis and decomposition
- **Multi-Step Reasoning**: Complex query breakdown and systematic analysis
- **Result Synthesis**: Information combination with conflict resolution
- **Session Management**: Context preservation across multiple queries
- **Export System**: Professional report generation in multiple formats

### Data Flow

```
Documents → Ingestion → Text Processing → Embedding Generation → Vector Storage
                                                                        ↓
Query → Processing → Reasoning → Document Retrieval → Synthesis → Report Export
```

## Configuration

The system can be configured through environment variables or configuration files:

```bash
# Environment variables
export EMBEDDING_MODEL="all-MiniLM-L6-v2"
export DATA_DIR="./research_data"
export CHUNK_SIZE="512"
export BATCH_SIZE="32"

# Or use command-line options
deep-researcher --data-dir ./my_data --embedding-model all-mpnet-base-v2 research "query"
```

## Report Templates

The system supports multiple report templates for different use cases:

- **Executive**: Business-focused summaries with recommendations
- **Academic**: Research-style reports with methodology and citations
- **Technical**: Implementation-focused with technical details
- **Comparative**: Side-by-side analysis and comparison
- **Analytical**: Problem-focused analysis with implications
- **Summary**: Concise overviews for quick consumption

## Export Formats

- **PDF**: Professional reports with formatting and layout
- **Markdown**: Clean, structured text for documentation systems
- **HTML**: Web-ready reports with styling
- **TXT**: Plain text for basic compatibility
- **JSON**: Structured data for programmatic access

## Advanced Features

### Query Refinement

The system provides intelligent suggestions to improve your research queries:

```bash
deep-researcher suggest "AI applications"
# Returns refined suggestions like:
# - "What are the practical applications of AI in healthcare?"
# - "How is AI being used in financial services?"
```

### Session Context

Maintain context across multiple related queries:

```python
# Create session
session_id = agent.create_session("AI Research Session")

# Research builds on previous context
agent.research("What is machine learning?", session_id=session_id)
agent.research("How does it compare to deep learning?", session_id=session_id)  # Understands "it" refers to ML
```

### Reasoning Transparency

Get detailed explanations of how the system reached its conclusions:

```python
result = agent.research("Compare renewable energy sources")
explanation = result['reasoning_explanation']

# Shows step-by-step reasoning process
for step in explanation.step_explanations:
    print(f"Step: {step.purpose}")
    print(f"Confidence: {step.confidence_explanation}")
```

## System Requirements

- Python 3.8+
- 4GB+ RAM (recommended for large document collections)
- 2GB+ disk space for models and data
- No internet connection required after initial model download

## Supported Document Formats

- **PDF**: Text extraction with metadata
- **DOCX**: Microsoft Word documents
- **TXT**: Plain text files
- **Markdown**: Structured text with formatting
- **HTML**: Web pages and HTML documents

## Performance

The system is optimized for local operation:

- **Document Ingestion**: ~100 documents/minute
- **Query Processing**: <5 seconds for simple queries, <30 seconds for complex
- **Memory Usage**: <4GB for 100K documents
- **Storage**: ~10MB per 1000 documents including embeddings

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions and support:

- 📖 [Documentation](https://deepresearcher.readthedocs.io)
- 🐛 [Issue Tracker](https://github.com/deepresearcher/deep-researcher-agent/issues)
- 💬 [Discussions](https://github.com/deepresearcher/deep-researcher-agent/discussions)

## Acknowledgments

- Built with [sentence-transformers](https://www.sbert.net/) for embeddings
- Uses [FAISS](https://faiss.ai/) for efficient similarity search
- Powered by [SQLite](https://sqlite.org/) for metadata storage
- CLI built with [Click](https://click.palletsprojects.com/)