"""Tests for performance monitoring and optimization."""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock

from deep_researcher.monitoring import (
    PerformanceMonitor, 
    CacheManager, 
    PerformanceMetrics,
    monitor_performance,
    with_caching,
    get_performance_monitor,
    get_cache_manager
)


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""
    
    def test_metrics_creation(self):
        """Test creating performance metrics."""
        metrics = PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=50.0,
            memory_mb=100.0,
            memory_percent=25.0,
            disk_usage_mb=1000.0,
            active_threads=5,
            operation="test_operation",
            duration=1.5,
            custom_metrics={"documents_processed": 10}
        )
        
        assert metrics.cpu_percent == 50.0
        assert metrics.memory_mb == 100.0
        assert metrics.operation == "test_operation"
        assert metrics.duration == 1.5
        assert metrics.custom_metrics["documents_processed"] == 10


class TestPerformanceMonitor:
    """Test PerformanceMonitor functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor(history_size=100)
    
    def teardown_method(self):
        """Clean up after tests."""
        if self.monitor.monitoring_active:
            self.monitor.stop_monitoring()
    
    def test_monitor_initialization(self):
        """Test monitor initialization."""
        assert self.monitor.history_size == 100
        assert not self.monitor.monitoring_active
        assert self.monitor.monitor_thread is None
        assert len(self.monitor.metrics_history) == 0
    
    @patch('psutil.Process')
    def test_collect_metrics(self, mock_process):
        """Test metrics collection."""
        # Mock psutil.Process
        mock_proc = MagicMock()
        mock_proc.cpu_percent.return_value = 45.0
        mock_proc.memory_info.return_value = MagicMock(rss=104857600)  # 100MB
        mock_proc.memory_percent.return_value = 30.0
        mock_process.return_value = mock_proc
        
        # Mock disk usage
        with patch('psutil.disk_usage') as mock_disk:
            mock_disk.return_value = MagicMock(used=1073741824)  # 1GB
            
            metrics = self.monitor.collect_metrics(
                operation="test_op", 
                duration=2.0,
                custom_metrics={"test_metric": 42}
            )
        
        assert metrics.cpu_percent == 45.0
        assert metrics.memory_mb == 100.0
        assert metrics.memory_percent == 30.0
        assert metrics.disk_usage_mb == 1024.0
        assert metrics.operation == "test_op"
        assert metrics.duration == 2.0
        assert metrics.custom_metrics["test_metric"] == 42
    
    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        # Start monitoring
        self.monitor.start_monitoring(interval=1)
        
        assert self.monitor.monitoring_active
        assert self.monitor.monitor_thread is not None
        assert self.monitor.monitor_thread.is_alive()
        
        # Stop monitoring
        self.monitor.stop_monitoring()
        
        assert not self.monitor.monitoring_active
    
    @patch('psutil.Process')
    def test_threshold_checking(self, mock_process):
        """Test threshold checking and warnings."""
        # Mock high resource usage
        mock_proc = MagicMock()
        mock_proc.cpu_percent.return_value = 90.0  # Above threshold
        mock_proc.memory_info.return_value = MagicMock(rss=1073741824)  # 1GB
        mock_proc.memory_percent.return_value = 90.0  # Above threshold
        mock_process.return_value = mock_proc
        
        with patch('psutil.disk_usage') as mock_disk:
            mock_disk.return_value = MagicMock(used=12884901888)  # 12GB
            
            with patch('deep_researcher.monitoring.logger') as mock_logger:
                metrics = self.monitor.collect_metrics(duration=35.0)  # Above threshold
                self.monitor._check_thresholds(metrics)
                
                # Should log warnings for high usage
                assert mock_logger.warning.call_count >= 2
    
    def test_performance_summary(self):
        """Test performance summary generation."""
        # Add some test metrics
        for i in range(5):
            metrics = PerformanceMetrics(
                timestamp=time.time() - (i * 3600),  # Spread over hours
                cpu_percent=50.0 + i,
                memory_mb=100.0 + i * 10,
                memory_percent=25.0 + i,
                disk_usage_mb=1000.0,
                active_threads=5
            )
            self.monitor.metrics_history.append(metrics)
        
        summary = self.monitor.get_performance_summary(hours=24)
        
        assert summary['data_points'] == 5
        assert 'cpu_usage' in summary
        assert 'memory_usage' in summary
        assert summary['cpu_usage']['average'] == 52.0
        assert summary['memory_usage']['average_mb'] == 120.0
    
    def test_operation_performance(self):
        """Test operation-specific performance tracking."""
        # Add metrics for specific operation
        for i in range(3):
            metrics = PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=50.0,
                memory_mb=100.0,
                memory_percent=25.0,
                disk_usage_mb=1000.0,
                active_threads=5,
                operation="test_operation",
                duration=1.0 + i * 0.5
            )
            self.monitor.metrics_history.append(metrics)
        
        perf = self.monitor.get_operation_performance("test_operation", hours=1)
        
        assert perf['operation'] == "test_operation"
        assert perf['execution_count'] == 3
        assert perf['average_duration'] == 1.5  # (1.0 + 1.5 + 2.0) / 3 = 1.5
        assert perf['min_duration'] == 1.0
        assert perf['max_duration'] == 2.0


class TestCacheManager:
    """Test CacheManager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cache_manager = CacheManager(max_cache_size=10)
    
    def test_cache_initialization(self):
        """Test cache manager initialization."""
        assert self.cache_manager.max_cache_size == 10
        assert len(self.cache_manager.caches) == 0
        assert len(self.cache_manager.cache_stats) == 0
    
    def test_cache_operations(self):
        """Test basic cache operations."""
        # Test cache miss
        result = self.cache_manager.cache_get("test_cache", "key1")
        assert result is None
        
        # Test cache set and hit
        self.cache_manager.cache_set("test_cache", "key1", "value1")
        result = self.cache_manager.cache_get("test_cache", "key1")
        assert result == "value1"
        
        # Check stats
        stats = self.cache_manager.get_cache_stats()
        assert stats['total_caches'] == 1
        assert stats['total_items'] == 1
        assert stats['cache_details']['test_cache']['hits'] == 1
        assert stats['cache_details']['test_cache']['misses'] == 1
        assert stats['cache_details']['test_cache']['hit_rate'] == 0.5
    
    def test_cache_eviction(self):
        """Test cache eviction when full."""
        # Fill cache beyond capacity
        for i in range(15):
            self.cache_manager.cache_set("test_cache", f"key{i}", f"value{i}")
        
        # Should only have max_cache_size items
        cache = self.cache_manager.get_cache("test_cache")
        assert len(cache) == self.cache_manager.max_cache_size
        
        # Oldest items should be evicted
        assert "key0" not in cache
        assert "key14" in cache
    
    def test_clear_cache(self):
        """Test cache clearing."""
        # Add items to multiple caches
        self.cache_manager.cache_set("cache1", "key1", "value1")
        self.cache_manager.cache_set("cache2", "key2", "value2")
        
        # Clear specific cache
        self.cache_manager.clear_cache("cache1")
        assert len(self.cache_manager.get_cache("cache1")) == 0
        assert len(self.cache_manager.get_cache("cache2")) == 1
        
        # Clear all caches
        self.cache_manager.clear_cache()
        assert len(self.cache_manager.get_cache("cache1")) == 0
        assert len(self.cache_manager.get_cache("cache2")) == 0


class TestDecorators:
    """Test performance monitoring decorators."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = get_performance_monitor()
        self.cache_manager = get_cache_manager()
    
    def test_monitor_performance_decorator(self):
        """Test performance monitoring decorator."""
        @monitor_performance("test_function")
        def test_function(x, y):
            time.sleep(0.1)  # Simulate work
            return x + y
        
        with patch('deep_researcher.monitoring.log_performance') as mock_log:
            result = test_function(1, 2)
            
            assert result == 3
            mock_log.assert_called_once()
            
            # Check that duration was logged
            call_args = mock_log.call_args
            assert call_args[0][1] == "test_function"  # operation name
            assert call_args[0][2] >= 0.1  # duration should be at least 0.1s
    
    def test_monitor_performance_decorator_with_exception(self):
        """Test performance monitoring decorator with exceptions."""
        @monitor_performance("failing_function")
        def failing_function():
            raise ValueError("Test error")
        
        with patch('deep_researcher.monitoring.log_performance') as mock_log:
            with pytest.raises(ValueError):
                failing_function()
            
            # Should still log performance even on failure
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][1] == "failing_function_failed"
    
    def test_caching_decorator(self):
        """Test caching decorator."""
        call_count = 0
        
        @with_caching("test_cache")
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call should execute function
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Function not called again
        
        # Different argument should execute function
        result3 = expensive_function(10)
        assert result3 == 20
        assert call_count == 2
    
    def test_caching_decorator_with_custom_key(self):
        """Test caching decorator with custom key function."""
        def key_func(x, y):
            return f"custom_{x}_{y}"
        
        call_count = 0
        
        @with_caching("custom_cache", key_func=key_func)
        def function_with_custom_key(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # Test caching works with custom key
        result1 = function_with_custom_key(1, 2)
        result2 = function_with_custom_key(1, 2)
        
        assert result1 == result2 == 3
        assert call_count == 1


class TestGlobalInstances:
    """Test global instance management."""
    
    def test_get_performance_monitor(self):
        """Test getting global performance monitor."""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()
        
        # Should return same instance
        assert monitor1 is monitor2
        assert isinstance(monitor1, PerformanceMonitor)
    
    def test_get_cache_manager(self):
        """Test getting global cache manager."""
        cache1 = get_cache_manager()
        cache2 = get_cache_manager()
        
        # Should return same instance
        assert cache1 is cache2
        assert isinstance(cache1, CacheManager)


class TestIntegration:
    """Integration tests for monitoring system."""
    
    def test_end_to_end_monitoring(self):
        """Test complete monitoring workflow."""
        monitor = PerformanceMonitor(history_size=50)
        
        # Start monitoring
        monitor.start_monitoring(interval=1)
        
        try:
            # Simulate some operations
            for i in range(3):
                metrics = monitor.collect_metrics(
                    operation=f"operation_{i}",
                    duration=0.5 + i * 0.1,
                    custom_metrics={"iteration": i}
                )
                monitor.metrics_history.append(metrics)
                time.sleep(0.1)
            
            # Check that metrics were collected
            assert len(monitor.metrics_history) >= 3
            
            # Get performance summary
            summary = monitor.get_performance_summary(hours=1)
            assert summary['data_points'] >= 3
            
            # Get operation performance
            op_perf = monitor.get_operation_performance("operation_1", hours=1)
            assert op_perf['execution_count'] >= 1
            
        finally:
            monitor.stop_monitoring()
    
    def test_monitoring_with_caching(self):
        """Test monitoring combined with caching."""
        # Use global cache manager that the decorator uses
        cache_manager = get_cache_manager()
        
        @with_caching("integration_cache")
        @monitor_performance("cached_operation")
        def cached_expensive_operation(n):
            time.sleep(0.05)  # Simulate work
            return n ** 2
        
        with patch('deep_researcher.monitoring.log_performance') as mock_log:
            # First call - should be slow and logged
            result1 = cached_expensive_operation(5)
            assert result1 == 25
            
            # Second call - should be fast (cached) and not reach the monitoring decorator
            result2 = cached_expensive_operation(5)
            assert result2 == 25
            
            # Should have logged only the first call (second is cached)
            assert mock_log.call_count == 1
            
            # Third call with different argument - should be logged again
            result3 = cached_expensive_operation(10)
            assert result3 == 100
            assert mock_log.call_count == 2
            
            # Check cache stats
            stats = cache_manager.get_cache_stats()
            assert stats['cache_details']['integration_cache']['hits'] == 1
            assert stats['cache_details']['integration_cache']['misses'] == 2