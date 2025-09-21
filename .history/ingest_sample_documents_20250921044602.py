#!/usr/bin/env python3
"""
Script to ingest sample documents into the Deep Researcher system
"""

import os
import sys
import time
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from deep_researcher.agent import ResearchAgent
    from deep_researcher.ingestion.ingester import DocumentIngester
    print("✅ Deep Researcher modules imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Deep Researcher modules: {e}")
    print("⚠️ Make sure you're in the correct directory and dependencies are installed")
    sys.exit(1)

def ingest_sample_documents():
    """Ingest sample documents into the Deep Researcher system."""
    
    # Initialize the research agent
    print("🚀 Initializing Deep Researcher Agent...")
    try:
        agent = ResearchAgent()
        agent.__enter__()
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return False
    
    # Get the sample documents directory
    sample_docs_dir = Path("sample_documents")
    if not sample_docs_dir.exists():
        print(f"❌ Sample documents directory not found: {sample_docs_dir}")
        return False
    
    # Get all document files
    document_files = []
    for ext in ['*.txt', '*.md', '*.pdf']:
        document_files.extend(sample_docs_dir.glob(ext))
    
    if not document_files:
        print("❌ No sample documents found")
        return False
    
    print(f"📄 Found {len(document_files)} sample documents:")
    for doc in document_files:
        print(f"  - {doc.name}")
    
    # Ingest each document
    successful_ingestions = 0
    failed_ingestions = 0
    
    for doc_file in document_files:
        try:
            print(f"\n📥 Ingesting: {doc_file.name}")
            
            # Use the agent's ingest method
            result = agent.ingest_documents([str(doc_file)])
            
            if result.get('success', False):
                print(f"✅ Successfully ingested: {doc_file.name}")
                print(f"   - Documents processed: {result.get('documents_processed', 0)}")
                print(f"   - Total chunks: {result.get('total_chunks', 0)}")
                print(f"   - Processing time: {result.get('processing_time', 0):.2f}s")
                successful_ingestions += 1
            else:
                print(f"❌ Failed to ingest: {doc_file.name}")
                print(f"   - Error: {result.get('error', 'Unknown error')}")
                failed_ingestions += 1
                
        except Exception as e:
            print(f"❌ Error ingesting {doc_file.name}: {e}")
            failed_ingestions += 1
    
    # Summary
    print(f"\n📊 Ingestion Summary:")
    print(f"   - Successful: {successful_ingestions}")
    print(f"   - Failed: {failed_ingestions}")
    print(f"   - Total: {len(document_files)}")
    
    # Test the system with a sample query
    print(f"\n🔍 Testing system with sample query...")
    try:
        test_query = "What are the latest trends in artificial intelligence?"
        print(f"Query: {test_query}")
        
        result = agent.research(query=test_query, max_sources=5)
        
        if result.get('success', False):
            research_report = result['research_report']
            print(f"✅ Research successful!")
            print(f"   - Sources found: {result.get('sources_found', 0)}")
            print(f"   - Confidence score: {research_report.confidence_score:.2f}")
            print(f"   - Execution time: {result.get('execution_time', 0):.2f}s")
            
            # Show a snippet of the summary
            summary = research_report.summary
            if len(summary) > 200:
                summary = summary[:200] + "..."
            print(f"   - Summary preview: {summary}")
        else:
            print(f"❌ Research failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error testing research: {e}")
    
    # Cleanup
    try:
        agent.__exit__(None, None, None)
        print("✅ Agent cleaned up successfully")
    except Exception as e:
        print(f"⚠️ Error during cleanup: {e}")
    
    return successful_ingestions > 0

if __name__ == "__main__":
    print("🚀 Starting sample document ingestion...")
    print("=" * 50)
    
    success = ingest_sample_documents()
    
    print("=" * 50)
    if success:
        print("✅ Sample document ingestion completed successfully!")
        print("🎉 The Deep Researcher system now has sample documents for testing")
    else:
        print("❌ Sample document ingestion failed")
        print("🔧 Please check the error messages above and try again")
