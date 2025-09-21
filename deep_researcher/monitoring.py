"""Performance monitoring and optimization for Deep Researcher Agent."""

import time
import psutil
import os
from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import threading
from collections import deque

from .logging_config import get_logger, log_performance

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for system monitoring."""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_usage_mb: float
    active_threads: int
    operation: Optional[str] = None
    duration: Optional[float] = None
    custom_metrics: Dict[str, Any] = None


class PerformanceMonitor:
    """Monitors system performance and resource usage."""
    
    def __init__(self, history_size: int = 1000):
        """
        Initialize performance monitor.
        
        Args:
            history_size: Number of metrics to keep in history
        """
        self.history_size = history_size
        self.metrics_history = deque(maxlen=history_size)
        self.monitoring_active = False
        self.monitor_thread = None
        self.monitor_interval = 30  # seconds
        
        # Performance thresholds
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_usage_gb': 10.0,
            'response_time_seconds': 30.0
        }
    
    def start_monitoring(self, interval: int = 30) -> None:
        """
        Start continuous performance monitoring.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self.monitoring_active:
            logger.warning("Performance monitoring already active")
            return
        
        self.monitor_interval = interval
        self.monitoring_active = True
        
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info(f"Started performance monitoring with {interval}s interval")
    
    def stop_monitoring(self) -> None:
        """Stop continuous performance monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Stopped performance monitoring")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                metrics = self.collect_metrics()
                self.metrics_history.append(metrics)
                
                # Check thresholds and log warnings
                self._check_thresholds(metrics)
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                time.sleep(self.monitor_interval)
    
    def collect_metrics(self, operation: Optional[str] = None, 
                       duration: Optional[float] = None,
                       custom_metrics: Dict[str, Any] = None) -> PerformanceMetrics:
        """
        Collect current performance metrics.
        
        Args:
            operation: Optional operation name
            duration: Optional operation duration
            custom_metrics: Optional custom metrics
            
        Returns:
            Current performance metrics
        """
        try:
            process = psutil.Process()
            
            # System metrics
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = process.memory_percent()
            
            # Disk usage for data directory
            disk_usage = psutil.disk_usage(os.getcwd())
            disk_usage_mb = disk_usage.used / 1024 / 1024
            
            # Thread count
            active_threads = threading.active_count()
            
            metrics = PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                disk_usage_mb=disk_usage_mb,
                active_threads=active_threads,
                operation=operation,
                duration=duration,
                custom_metrics=custom_metrics or {}
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_mb=0.0,
                memory_percent=0.0,
                disk_usage_mb=0.0,
                active_threads=0
            )
    
    def _check_thresholds(self, metrics: PerformanceMetrics) -> None:
        """Check if metrics exceed thresholds and log warnings."""
        
        if metrics.cpu_percent > self.thresholds['cpu_percent']:
            logger.warning(f"High CPU usage: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent > self.thresholds['memory_percent']:
            logger.warning(f"High memory usage: {metrics.memory_percent:.1f}% ({metrics.memory_mb:.1f}MB)")
        
        if metrics.disk_usage_mb > self.thresholds['disk_usage_gb'] * 1024:
            logger.warning(f"High disk usage: {metrics.disk_usage_mb / 1024:.1f}GB")
        
        if metrics.duration and metrics.duration > self.thresholds['response_time_seconds']:
            logger.warning(f"Slow operation '{metrics.operation}': {metrics.duration:.2f}s")
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance summary for the specified time period.
        
        Args:
            hours: Number of hours to include in summary
            
        Returns:
            Performance summary statistics
        """
        if not self.metrics_history:
            return {'error': 'No performance data available'}
        
        # Filter metrics by time period
        cutoff_time = time.time() - (hours * 3600)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {'error': f'No data available for last {hours} hours'}
        
        # Calculate statistics
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_mb for m in recent_metrics]
        memory_percent_values = [m.memory_percent for m in recent_metrics]
        
        summary = {
            'time_period_hours': hours,
            'data_points': len(recent_metrics),
            'cpu_usage': {
                'average': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory_usage': {
                'average_mb': sum(memory_values) / len(memory_values),
                'max_mb': max(memory_values),
                'min_mb': min(memory_values),
                'average_percent': sum(memory_percent_values) / len(memory_percent_values),
                'max_percent': max(memory_percent_values)
            },
            'disk_usage_mb': recent_metrics[-1].disk_usage_mb if recent_metrics else 0,
            'active_threads': recent_metrics[-1].active_threads if recent_metrics else 0
        }
        
        return summary
    
    def get_operation_performance(self, operation: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance statistics for a specific operation.
        
        Args:
            operation: Operation name to analyze
            hours: Number of hours to include
            
        Returns:
            Operation performance statistics
        """
        cutoff_time = time.time() - (hours * 3600)
        operation_metrics = [
            m for m in self.metrics_history 
            if m.timestamp >= cutoff_time and m.operation == operation and m.duration is not None
        ]
        
        if not operation_metrics:
            return {'error': f'No performance data for operation: {operation}'}
        
        durations = [m.duration for m in operation_metrics]
        
        return {
            'operation': operation,
            'execution_count': len(operation_metrics),
            'average_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'total_time': sum(durations),
            'operations_per_hour': len(operation_metrics) / hours
        }


class CacheManager:
    """Manages caching for performance optimization."""
    
    def __init__(self, max_cache_size: int = 1000):
        """
        Initialize cache manager.
        
        Args:
            max_cache_size: Maximum number of items to cache
        """
        self.max_cache_size = max_cache_size
        self.caches = {}
        self.cache_stats = {}
    
    def get_cache(self, cache_name: str) -> Dict[str, Any]:
        """Get or create a cache."""
        if cache_name not in self.caches:
            self.caches[cache_name] = {}
            self.cache_stats[cache_name] = {
                'hits': 0,
                'misses': 0,
                'size': 0,
                'created_at': time.time()
            }
        
        return self.caches[cache_name]
    
    def cache_get(self, cache_name: str, key: str) -> Any:
        """Get item from cache."""
        cache = self.get_cache(cache_name)
        
        if key in cache:
            self.cache_stats[cache_name]['hits'] += 1
            return cache[key]
        else:
            self.cache_stats[cache_name]['misses'] += 1
            return None
    
    def cache_set(self, cache_name: str, key: str, value: Any) -> None:
        """Set item in cache."""
        cache = self.get_cache(cache_name)
        
        # Implement simple LRU eviction if cache is full
        if len(cache) >= self.max_cache_size:
            # Remove oldest item (simplified LRU)
            oldest_key = next(iter(cache))
            del cache[oldest_key]
        
        cache[key] = value
        self.cache_stats[cache_name]['size'] = len(cache)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_stats = {
            'total_caches': len(self.caches),
            'total_items': sum(len(cache) for cache in self.caches.values()),
            'cache_details': {}
        }
        
        for cache_name, stats in self.cache_stats.items():
            hit_rate = stats['hits'] / (stats['hits'] + stats['misses']) if (stats['hits'] + stats['misses']) > 0 else 0
            total_stats['cache_details'][cache_name] = {
                **stats,
                'hit_rate': hit_rate
            }
        
        return total_stats
    
    def clear_cache(self, cache_name: Optional[str] = None) -> None:
        """Clear cache(s)."""
        if cache_name:
            if cache_name in self.caches:
                self.caches[cache_name].clear()
                self.cache_stats[cache_name]['size'] = 0
        else:
            for cache in self.caches.values():
                cache.clear()
            for stats in self.cache_stats.values():
                stats['size'] = 0


# Global instances
_performance_monitor = None
_cache_manager = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def monitor_performance(operation: str):
    """Decorator for monitoring operation performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            monitor = get_performance_monitor()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Collect metrics
                metrics = monitor.collect_metrics(operation, duration)
                
                # Log performance
                log_performance(
                    logger, operation, duration,
                    cpu_percent=metrics.cpu_percent,
                    memory_mb=metrics.memory_mb,
                    **metrics.custom_metrics
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                log_performance(
                    logger, f"{operation}_failed", duration,
                    error=str(e)
                )
                raise
        
        return wrapper
    return decorator


def with_caching(cache_name: str, key_func=None):
    """Decorator for adding caching to functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cached_result = cache_manager.cache_get(cache_name, cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.cache_set(cache_name, cache_key, result)
            
            return result
        
        return wrapper
    return decorator