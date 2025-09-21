"""Tests for error handling and recovery mechanisms."""

import pytest
import time
import logging
from unittest.mock import Mock, patch
import tempfile
import os

from deep_researcher.error_recovery import (
    ErrorRecoveryManager, RecoveryConfig, RecoveryStrategy,
    with_retry, with_fallback, graceful_degradation, CircuitBreaker
)
from deep_researcher.logging_config import LoggingManager, get_logger
from deep_researcher.exceptions import DeepResearcherError


class TestErrorRecoveryManager:
    """Test ErrorRecoveryManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.recovery_manager = ErrorRecoveryManager()
    
    def test_successful_execution_no_retry(self):
        """Test successful execution without any errors."""
        @self.recovery_manager.with_recovery()
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
        
        stats = self.recovery_manager.get_recovery_stats()
        assert stats['total_errors'] == 0
        assert stats['recovered_errors'] == 0
    
    def test_retry_with_eventual_success(self):
        """Test retry mechanism with eventual success."""
        call_count = 0
        
        @self.recovery_manager.with_recovery(RecoveryConfig(max_retries=3, retry_delay=0.1))
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert call_count == 3
        
        stats = self.recovery_manager.get_recovery_stats()
        assert stats['total_errors'] == 2  # First two attempts failed
        assert stats['recovered_errors'] == 1  # Eventually succeeded
    
    def test_retry_exhaustion(self):
        """Test behavior when all retries are exhausted."""
        @self.recovery_manager.with_recovery(RecoveryConfig(max_retries=2, retry_delay=0.1))
        def always_failing_function():
            raise ConnectionError("Always fails")
        
        with pytest.raises(ConnectionError):
            always_failing_function()
        
        stats = self.recovery_manager.get_recovery_stats()
        assert stats['total_errors'] == 3  # Initial + 2 retries
        assert stats['failed_recoveries'] == 1
    
    def test_non_recoverable_exception(self):
        """Test handling of non-recoverable exceptions."""
        @self.recovery_manager.with_recovery(RecoveryConfig(
            recoverable_exceptions=[ConnectionError]
        ))
        def function_with_non_recoverable_error():
            raise ValueError("This should not be retried")
        
        with pytest.raises(ValueError):
            function_with_non_recoverable_error()
        
        stats = self.recovery_manager.get_recovery_stats()
        assert stats['failed_recoveries'] == 1
    
    def test_fallback_strategy(self):
        """Test fallback recovery strategy."""
        class TestClass:
            def failing_method(self):
                raise ConnectionError("Method failed")
            
            def failing_method_fallback(self):
                return "fallback_result"
        
        test_obj = TestClass()
        
        config = RecoveryConfig(
            max_retries=1,
            strategy=RecoveryStrategy.FALLBACK,
            recoverable_exceptions=[ConnectionError]
        )
        
        decorated_method = self.recovery_manager.with_recovery(config)(test_obj.failing_method)
        test_obj.failing_method = decorated_method
        
        result = test_obj.failing_method()
        assert result == "fallback_result"
    
    def test_partial_success_strategy(self):
        """Test partial success recovery strategy."""
        @self.recovery_manager.with_recovery(RecoveryConfig(
            max_retries=1,
            strategy=RecoveryStrategy.PARTIAL_SUCCESS,
            recoverable_exceptions=[ConnectionError]
        ))
        def failing_function():
            raise ConnectionError("Function failed")
        
        result = failing_function()
        
        assert isinstance(result, dict)
        assert result['success'] is False
        assert 'error' in result
        assert result['partial_result'] is True
    
    def test_skip_strategy(self):
        """Test skip recovery strategy."""
        @self.recovery_manager.with_recovery(RecoveryConfig(
            max_retries=1,
            strategy=RecoveryStrategy.SKIP,
            recoverable_exceptions=[ConnectionError]
        ))
        def failing_function():
            raise ConnectionError("Function failed")
        
        result = failing_function()
        assert result is None


class TestRetryDecorator:
    """Test retry decorator functionality."""
    
    def test_with_retry_decorator(self):
        """Test the with_retry decorator."""
        call_count = 0
        
        @with_retry(max_retries=2, delay=0.1, recoverable_exceptions=[ConnectionError])
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert call_count == 2
    
    def test_with_fallback_decorator(self):
        """Test the with_fallback decorator."""
        class TestClass:
            @with_fallback()
            def failing_method(self):
                raise ConnectionError("Method failed")
            
            def failing_method_fallback(self):
                return "fallback_used"
        
        test_obj = TestClass()
        result = test_obj.failing_method()
        assert result == "fallback_used"
    
    def test_graceful_degradation_decorator(self):
        """Test graceful degradation decorator."""
        @graceful_degradation
        def failing_function():
            raise ValueError("Function failed")
        
        result = failing_function()
        assert isinstance(result, dict)
        assert result['success'] is False


class TestCircuitBreaker:
    """Test CircuitBreaker functionality."""
    
    def test_circuit_breaker_normal_operation(self):
        """Test circuit breaker during normal operation."""
        circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=1.0)
        
        @circuit_breaker
        def normal_function():
            return "success"
        
        # Should work normally
        result = normal_function()
        assert result == "success"
        assert circuit_breaker.state == 'closed'
    
    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        circuit_breaker = CircuitBreaker(failure_threshold=2, timeout=1.0)
        
        @circuit_breaker
        def failing_function():
            raise ConnectionError("Function failed")
        
        # First failure
        with pytest.raises(ConnectionError):
            failing_function()
        assert circuit_breaker.state == 'closed'
        
        # Second failure - should open circuit
        with pytest.raises(ConnectionError):
            failing_function()
        assert circuit_breaker.state == 'open'
        
        # Third call should be blocked by circuit breaker
        with pytest.raises(DeepResearcherError, match="Circuit breaker is open"):
            failing_function()
    
    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker half-open state and recovery."""
        circuit_breaker = CircuitBreaker(failure_threshold=1, timeout=0.1)
        
        call_count = 0
        
        @circuit_breaker
        def recovering_function():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("First failure")
            return "success"
        
        # First call fails, opens circuit
        with pytest.raises(ConnectionError):
            recovering_function()
        assert circuit_breaker.state == 'open'
        
        # Wait for timeout
        time.sleep(0.2)
        
        # Next call should succeed and close circuit
        result = recovering_function()
        assert result == "success"
        assert circuit_breaker.state == 'closed'


class TestLoggingManager:
    """Test LoggingManager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.logging_manager = LoggingManager(log_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_logger_creation(self):
        """Test logger creation and configuration."""
        logger = self.logging_manager.get_logger("test_logger")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
    
    def test_log_files_created(self):
        """Test that log files are created."""
        logger = self.logging_manager.get_logger("test")
        logger.info("Test message")
        logger.error("Test error")
        
        # Check that log files exist
        log_files = [
            "deep_researcher.log",
            "errors.log",
            "performance.log",
            "structured.jsonl"
        ]
        
        for log_file in log_files:
            log_path = os.path.join(self.temp_dir, log_file)
            assert os.path.exists(log_path)
    
    def test_performance_logging(self):
        """Test performance logging functionality."""
        logger = self.logging_manager.get_logger("performance_test")
        
        self.logging_manager.log_performance(
            logger, "test_operation", 1.5,
            documents_processed=100,
            memory_used="500MB"
        )
        
        # Check that performance log file exists and has content
        perf_log_path = os.path.join(self.temp_dir, "performance.log")
        assert os.path.exists(perf_log_path)
        
        with open(perf_log_path, 'r') as f:
            content = f.read()
            assert "test_operation" in content
            assert "1.5" in content
    
    def test_context_logging(self):
        """Test logging with context."""
        logger = self.logging_manager.get_logger("context_test")
        
        context = {
            "user_id": "test_user",
            "session_id": "test_session",
            "operation": "document_ingestion"
        }
        
        self.logging_manager.log_with_context(
            logger, logging.INFO, "Test message with context", context
        )
        
        # Check that structured log file has the context
        struct_log_path = os.path.join(self.temp_dir, "structured.jsonl")
        assert os.path.exists(struct_log_path)
        
        with open(struct_log_path, 'r') as f:
            content = f.read()
            assert "user_id" in content
            assert "test_user" in content


class TestIntegratedErrorHandling:
    """Test integrated error handling across components."""
    
    def test_component_error_handling_integration(self):
        """Test error handling integration across multiple components."""
        
        # Mock a component that might fail
        class MockComponent:
            def __init__(self):
                self.call_count = 0
            
            @with_retry(max_retries=2, delay=0.1)
            def process_data(self, data):
                self.call_count += 1
                if self.call_count < 2:
                    raise ConnectionError("Temporary network issue")
                return f"processed_{data}"
            
            @graceful_degradation
            def optional_enhancement(self, data):
                raise ValueError("Enhancement failed")
        
        component = MockComponent()
        
        # Test retry mechanism
        result = component.process_data("test_data")
        assert result == "processed_test_data"
        assert component.call_count == 2
        
        # Test graceful degradation
        result = component.optional_enhancement("test_data")
        assert isinstance(result, dict)
        assert result['success'] is False
    
    def test_error_recovery_statistics(self):
        """Test error recovery statistics collection."""
        recovery_manager = ErrorRecoveryManager()
        
        @recovery_manager.with_recovery(RecoveryConfig(max_retries=1, retry_delay=0.1))
        def test_function():
            raise ConnectionError("Test error")
        
        # Execute function that will fail
        try:
            test_function()
        except ConnectionError:
            pass
        
        stats = recovery_manager.get_recovery_stats()
        assert stats['total_errors'] > 0
        assert stats['failed_recoveries'] > 0
        assert stats['recovery_rate'] >= 0.0
        
        # Reset stats
        recovery_manager.reset_stats()
        new_stats = recovery_manager.get_recovery_stats()
        assert new_stats['total_errors'] == 0