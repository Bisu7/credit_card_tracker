#!/usr/bin/env python3
"""
Demo script showing how to use Deep Researcher Agent
to ingest documents and conduct research.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from deep_researcher.agent import ResearchAgent


def demo_document_research():
    """Demonstrate document ingestion and research workflow."""
    
    print("🚀 Deep Researcher Agent Demo")
    print("=" * 50)
    
    # Initialize the research agent
    print("\n1️⃣ Initializing Deep Researcher Agent...")
    
    try:
        with ResearchAgent() as agent:
            print("✅ Agent initialized successfully!")
            
            # Step 1: Ingest the sample document
            print("\n2️⃣ Ingesting sample document...")
            
            # Check if sample document exists
            sample_doc = "sample_document.txt"
            if not os.path.exists(sample_doc):
                print(f"❌ Sample document not found: {sample_doc}")
                return
            
            # Ingest the document
            result = agent.ingest_documents([sample_doc])
            
            if result['success']:
                print(f"✅ Document ingested successfully!")
                print(f"   📄 Documents processed: {result['documents_processed']}")
                print(f"   📝 Text chunks created: {result['total_chunks']}")
                print(f"   ⏱️  Processing time: {result['processing_time']:.2f}s")
            else:
                print(f"❌ Document ingestion failed: {result.get('error', 'Unknown error')}")
                return
            
            # Step 2: Conduct research queries
            print("\n3️⃣ Conducting research queries...")
            
            # Define some research questions
            research_queries = [
                "What are the main effects of climate change on ocean ecosystems?",
                "How does ocean acidification affect marine life?",
                "What conservation efforts are being made to protect marine ecosystems?",
                "What are the economic implications of climate change on fishing industries?"
            ]
            
            for i, query in enumerate(research_queries, 1):
                print(f"\n🔍 Query {i}: {query}")
                print("-" * 60)
                
                # Conduct research
                research_result = agent.research(query, max_sources=5)
                
                if research_result['success']:
                    report = research_result['research_report']
                    
                    print(f"✅ Research completed in {research_result['execution_time']:.2f}s")
                    print(f"📊 Sources found: {research_result['sources_found']}")
                    print(f"🎯 Confidence score: {report.confidence_score:.2f}")
                    
                    print(f"\n📋 Summary:")
                    print(f"   {report.summary}")
                    
                    print(f"\n🔑 Key Findings:")
                    for j, finding in enumerate(report.key_findings[:3], 1):
                        print(f"   {j}. {finding}")
                    
                    if report.sources:
                        print(f"\n📚 Sources:")
                        for source in report.sources[:2]:  # Show first 2 sources
                            print(f"   • {source.get('title', 'Unknown')} (Relevance: {source.get('relevance_score', 0):.2f})")
                
                else:
                    print(f"❌ Research failed: {research_result.get('error', 'Unknown error')}")
                
                print()  # Add spacing between queries
            
            # Step 3: Demonstrate interactive session
            print("\n4️⃣ Creating research session for follow-up queries...")
            
            session_id = agent.create_session("Climate Change Research", "Demo session for ocean ecosystem research")
            print(f"✅ Created session: {session_id}")
            
            # Follow-up query with context
            follow_up_query = "Based on the previous research, what specific actions can individuals take to help?"
            print(f"\n🔍 Follow-up query: {follow_up_query}")
            
            follow_up_result = agent.research(follow_up_query, session_id=session_id, max_sources=3)
            
            if follow_up_result['success']:
                report = follow_up_result['research_report']
                print(f"✅ Follow-up research completed in {follow_up_result['execution_time']:.2f}s")
                print(f"📋 Summary: {report.summary}")
            
            # Step 4: Export a research report
            print("\n5️⃣ Exporting research report...")
            
            # Use the last research result for export
            if 'report' in locals():
                try:
                    export_path = agent.export_report(
                        research_report=report,
                        output_path="climate_research_report.md",
                        format_type="markdown",
                        template="academic"
                    )
                    print(f"✅ Report exported to: {export_path}")
                except Exception as e:
                    print(f"⚠️  Export failed: {e}")
            
            # Step 5: Show system status
            print("\n6️⃣ System Status:")
            status = agent.get_system_status()
            
            if 'storage' in status:
                doc_stats = status['storage']['document_store']
                vector_stats = status['storage']['vector_store']
                
                print(f"   📄 Total documents: {doc_stats['total_documents']}")
                print(f"   📝 Total chunks: {doc_stats['total_chunks']}")
                print(f"   🧠 Total vectors: {vector_stats['total_vectors']}")
            
            print("\n🎉 Demo completed successfully!")
            print("\nNext steps:")
            print("1. Add more documents using: python -m deep_researcher.cli ingest your_document.pdf")
            print("2. Start interactive mode: python -m deep_researcher.cli interactive")
            print("3. Conduct specific research: python -m deep_researcher.cli research 'your question'")
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


def show_cli_usage():
    """Show how to use the CLI commands."""
    
    print("\n" + "=" * 60)
    print("📖 CLI Usage Examples")
    print("=" * 60)
    
    print("\n1. Ingest documents:")
    print("   python -m deep_researcher.cli ingest sample_document.txt")
    print("   python -m deep_researcher.cli ingest *.pdf")
    print("   python -m deep_researcher.cli ingest folder/*.docx")
    
    print("\n2. Conduct research:")
    print("   python -m deep_researcher.cli research 'What is climate change?'")
    print("   python -m deep_researcher.cli research 'Compare renewable energy sources' --output report.pdf")
    
    print("\n3. Interactive mode:")
    print("   python -m deep_researcher.cli interactive")
    
    print("\n4. Create research session:")
    print("   python -m deep_researcher.cli create-session --title 'My Research'")
    
    print("\n5. Get query suggestions:")
    print("   python -m deep_researcher.cli suggest 'climate change effects'")
    
    print("\n6. Check system status:")
    print("   python -m deep_researcher.cli status")
    print("   python -m deep_researcher.cli health")


if __name__ == "__main__":
    demo_document_research()
    show_cli_usage()