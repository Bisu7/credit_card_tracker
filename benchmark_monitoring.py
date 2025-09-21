#!/usr/bin/env python3
"""
Performance monitoring benchmark script.

This script demonstrates the monitoring and caching capabilities
of the Deep Researcher Agent system.
"""

import time
import random
from deep_researcher.monitoring import (
    get_performance_monitor, 
    get_cache_manager,
    monitor_performance,
    with_caching
)


@monitor_performance("document_processing")
def simulate_document_processing(doc_size: int) -> dict:
    """Simulate document processing with variable time based on size."""
    # Simulate processing time proportional to document size
    processing_time = doc_size / 1000.0  # 1ms per KB
    time.sleep(processing_time)
    
    return {
        "processed_chunks": doc_size // 100,
        "processing_time": processing_time,
        "status": "completed"
    }


@with_caching("embedding_cache")
@monitor_performance("embedding_generation")
def simulate_embedding_generation(text_hash: str) -> list:
    """Simulate embedding generation with caching."""
    # Simulate embedding generation time
    time.sleep(0.1)
    
    # Return mock embedding vector
    return [random.random() for _ in range(384)]


@monitor_performance("query_processing")
def simulate_query_processing(query: str, complexity: str = "simple") -> dict:
    """Simulate query processing with different complexity levels."""
    base_time = 0.05
    
    if complexity == "complex":
        base_time *= 3
    elif complexity == "multi_step":
        base_time *= 5
    
    time.sleep(base_time)
    
    return {
        "query": query,
        "complexity": complexity,
        "results_found": random.randint(5, 50),
        "processing_time": base_time
    }


def run_benchmark():
    """Run performance monitoring benchmark."""
    print("🚀 Starting Deep Researcher Agent Performance Benchmark")
    print("=" * 60)
    
    # Get monitoring instances
    monitor = get_performance_monitor()
    cache_manager = get_cache_manager()
    
    # Start continuous monitoring
    monitor.start_monitoring(interval=5)
    
    try:
        print("\n📊 Running document processing benchmark...")
        # Simulate processing documents of various sizes
        doc_sizes = [500, 1000, 2000, 5000, 1500, 3000]
        for i, size in enumerate(doc_sizes):
            print(f"  Processing document {i+1} ({size}KB)...")
            result = simulate_document_processing(size)
            print(f"    ✓ Processed {result['processed_chunks']} chunks in {result['processing_time']:.3f}s")
        
        print("\n🧠 Running embedding generation benchmark...")
        # Simulate embedding generation with some repeated texts (to test caching)
        texts = ["text_1", "text_2", "text_3", "text_1", "text_4", "text_2", "text_5"]
        for i, text_hash in enumerate(texts):
            print(f"  Generating embedding for {text_hash}...")
            embedding = simulate_embedding_generation(text_hash)
            print(f"    ✓ Generated {len(embedding)}-dimensional embedding")
        
        print("\n🔍 Running query processing benchmark...")
        # Simulate different types of queries
        queries = [
            ("What is machine learning?", "simple"),
            ("Explain the relationship between AI and neural networks", "complex"),
            ("Compare deep learning frameworks and analyze their performance", "multi_step"),
            ("Define artificial intelligence", "simple"),
            ("How do transformers work in NLP?", "complex")
        ]
        
        for query, complexity in queries:
            print(f"  Processing {complexity} query...")
            result = simulate_query_processing(query, complexity)
            print(f"    ✓ Found {result['results_found']} results in {result['processing_time']:.3f}s")
        
        # Wait a bit for monitoring to collect data
        time.sleep(2)
        
        print("\n📈 Performance Summary")
        print("-" * 40)
        
        # Get performance summary
        summary = monitor.get_performance_summary(hours=1)
        if 'error' not in summary:
            print(f"Data points collected: {summary['data_points']}")
            print(f"Average CPU usage: {summary['cpu_usage']['average']:.1f}%")
            print(f"Peak CPU usage: {summary['cpu_usage']['max']:.1f}%")
            print(f"Average memory usage: {summary['memory_usage']['average_mb']:.1f}MB")
            print(f"Peak memory usage: {summary['memory_usage']['max_mb']:.1f}MB")
        
        # Get operation-specific performance
        operations = ["document_processing", "embedding_generation", "query_processing"]
        for operation in operations:
            perf = monitor.get_operation_performance(operation, hours=1)
            if 'error' not in perf:
                print(f"\n{operation.replace('_', ' ').title()}:")
                print(f"  Executions: {perf['execution_count']}")
                print(f"  Average duration: {perf['average_duration']:.3f}s")
                print(f"  Min duration: {perf['min_duration']:.3f}s")
                print(f"  Max duration: {perf['max_duration']:.3f}s")
        
        # Get cache statistics
        print(f"\n💾 Cache Performance")
        print("-" * 40)
        cache_stats = cache_manager.get_cache_stats()
        if cache_stats['total_caches'] > 0:
            for cache_name, stats in cache_stats['cache_details'].items():
                print(f"{cache_name}:")
                print(f"  Items cached: {stats['size']}")
                print(f"  Cache hits: {stats['hits']}")
                print(f"  Cache misses: {stats['misses']}")
                print(f"  Hit rate: {stats['hit_rate']:.1%}")
        else:
            print("No cache data available")
        
    finally:
        # Stop monitoring
        monitor.stop_monitoring()
        print(f"\n✅ Benchmark completed successfully!")
        print("Monitoring stopped.")


if __name__ == "__main__":
    run_benchmark()