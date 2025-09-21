"""Error recovery and resilience mechanisms."""

import time
import functools
import logging
from typing import Callable, Any, Optional, Dict, Type, List
from dataclasses import dataclass
from enum import Enum

from .exceptions import DeepResearcherError
from .logging_config import get_logger

logger = get_logger(__name__)


class RecoveryStrategy(Enum):
    """Available error recovery strategies."""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ABORT = "abort"
    PARTIAL_SUCCESS = "partial_success"


@dataclass
class RecoveryConfig:
    """Configuration for error recovery."""
    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay: float = 60.0
    recoverable_exceptions: List[Type[Exception]] = None
    strategy: RecoveryStrategy = RecoveryStrategy.RETRY


class ErrorRecoveryManager:
    """Manages error recovery strategies and mechanisms."""
    
    def __init__(self):
        """Initialize error recovery manager."""
        self.recovery_stats = {
            'total_errors': 0,
            'recovered_errors': 0,
            'failed_recoveries': 0,
            'recovery_strategies_used': {}
        }
    
    def with_recovery(self, config: RecoveryConfig = None):
        """Decorator for adding error recovery to functions."""
        if config is None:
            config = RecoveryConfig()
        
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return self._execute_with_recovery(func, config, *args, **kwargs)
            return wrapper
        return decorator
    
    def _execute_with_recovery(self, func: Callable, config: RecoveryConfig, 
                              *args, **kwargs) -> Any:
        """Execute function with error recovery."""
        last_exception = None
        delay = config.retry_delay
        
        for attempt in range(config.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                
                # Log successful recovery if this wasn't the first attempt
                if attempt > 0:
                    logger.info(f"Function {func.__name__} succeeded after {attempt} retries")
                    self.recovery_stats['recovered_errors'] += 1
                
                return result
                
            except Exception as e:
                last_exception = e
                self.recovery_stats['total_errors'] += 1
                
                # Check if this exception is recoverable
                if not self._is_recoverable_exception(e, config):
                    logger.error(f"Non-recoverable exception in {func.__name__}: {e}")
                    self.recovery_stats['failed_recoveries'] += 1
                    raise
                
                # If this is the last attempt, don't retry
                if attempt >= config.max_retries:
                    break
                
                # Log retry attempt
                logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                             f"Retrying in {delay:.2f}s...")
                
                # Wait before retry
                time.sleep(delay)
                delay = min(delay * config.backoff_multiplier, config.max_delay)
        
        # All retries exhausted
        logger.error(f"All {config.max_retries} retries exhausted for {func.__name__}")
        self.recovery_stats['failed_recoveries'] += 1
        
        # Apply recovery strategy
        return self._apply_recovery_strategy(func, config, last_exception, *args, **kwargs)
    
    def _is_recoverable_exception(self, exception: Exception, 
                                 config: RecoveryConfig) -> bool:
        """Check if an exception is recoverable."""
        if config.recoverable_exceptions is None:
            # Default recoverable exceptions
            recoverable_types = (
                ConnectionError,
                TimeoutError,
                OSError,
                # Add more as needed
            )
        else:
            recoverable_types = tuple(config.recoverable_exceptions)
        
        return isinstance(exception, recoverable_types)
    
    def _apply_recovery_strategy(self, func: Callable, config: RecoveryConfig,
                               exception: Exception, *args, **kwargs) -> Any:
        """Apply the configured recovery strategy."""
        strategy = config.strategy
        self.recovery_stats['recovery_strategies_used'][strategy.value] = \
            self.recovery_stats['recovery_strategies_used'].get(strategy.value, 0) + 1
        
        if strategy == RecoveryStrategy.FALLBACK:
            return self._apply_fallback(func, exception, *args, **kwargs)
        elif strategy == RecoveryStrategy.SKIP:
            logger.warning(f"Skipping failed operation {func.__name__} due to: {exception}")
            return None
        elif strategy == RecoveryStrategy.PARTIAL_SUCCESS:
            return self._apply_partial_success(func, exception, *args, **kwargs)
        else:  # ABORT
            logger.error(f"Aborting operation {func.__name__} due to: {exception}")
            raise exception
    
    def _apply_fallback(self, func: Callable, exception: Exception, 
                       *args, **kwargs) -> Any:
        """Apply fallback strategy."""
        # Try to find a fallback method
        fallback_name = f"{func.__name__}_fallback"
        
        # Look for fallback in the same module/class
        if hasattr(func, '__self__'):
            # Method of a class
            if hasattr(func.__self__, fallback_name):
                fallback_func = getattr(func.__self__, fallback_name)
                logger.info(f"Using fallback method {fallback_name}")
                return fallback_func(*args, **kwargs)
        
        # No fallback found, return default value
        logger.warning(f"No fallback found for {func.__name__}, returning None")
        return None
    
    def _apply_partial_success(self, func: Callable, exception: Exception,
                              *args, **kwargs) -> Any:
        """Apply partial success strategy."""
        # Return a partial result indicating what succeeded
        return {
            'success': False,
            'error': str(exception),
            'partial_result': True,
            'function': func.__name__
        }
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get error recovery statistics."""
        total_errors = self.recovery_stats['total_errors']
        if total_errors > 0:
            recovery_rate = self.recovery_stats['recovered_errors'] / total_errors
        else:
            recovery_rate = 0.0
        
        return {
            **self.recovery_stats,
            'recovery_rate': recovery_rate
        }
    
    def reset_stats(self):
        """Reset recovery statistics."""
        self.recovery_stats = {
            'total_errors': 0,
            'recovered_errors': 0,
            'failed_recoveries': 0,
            'recovery_strategies_used': {}
        }


# Global error recovery manager
_error_recovery_manager = None


def get_error_recovery_manager() -> ErrorRecoveryManager:
    """Get the global error recovery manager."""
    global _error_recovery_manager
    if _error_recovery_manager is None:
        _error_recovery_manager = ErrorRecoveryManager()
    return _error_recovery_manager


def with_retry(max_retries: int = 3, delay: float = 1.0, 
               backoff: float = 2.0, recoverable_exceptions: List[Type[Exception]] = None):
    """Decorator for adding retry logic to functions."""
    config = RecoveryConfig(
        max_retries=max_retries,
        retry_delay=delay,
        backoff_multiplier=backoff,
        recoverable_exceptions=recoverable_exceptions,
        strategy=RecoveryStrategy.RETRY
    )
    return get_error_recovery_manager().with_recovery(config)


def with_fallback(fallback_func: Optional[Callable] = None):
    """Decorator for adding fallback logic to functions."""
    config = RecoveryConfig(
        max_retries=1,
        strategy=RecoveryStrategy.FALLBACK
    )
    return get_error_recovery_manager().with_recovery(config)


def graceful_degradation(func: Callable) -> Callable:
    """Decorator for graceful degradation on errors."""
    config = RecoveryConfig(
        max_retries=0,
        strategy=RecoveryStrategy.PARTIAL_SUCCESS
    )
    return get_error_recovery_manager().with_recovery(config)(func)


class CircuitBreaker:
    """Circuit breaker pattern for preventing cascading failures."""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Time to wait before trying again (seconds)
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = 'closed'  # closed, open, half-open
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator for circuit breaker."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self._execute_with_circuit_breaker(func, *args, **kwargs)
        return wrapper
    
    def _execute_with_circuit_breaker(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker logic."""
        current_time = time.time()
        
        # Check circuit state
        if self.state == 'open':
            if current_time - self.last_failure_time < self.timeout:
                raise DeepResearcherError(f"Circuit breaker is open for {func.__name__}")
            else:
                self.state = 'half-open'
                logger.info(f"Circuit breaker for {func.__name__} is now half-open")
        
        try:
            result = func(*args, **kwargs)
            
            # Success - reset circuit breaker
            if self.state == 'half-open':
                self.state = 'closed'
                self.failure_count = 0
                logger.info(f"Circuit breaker for {func.__name__} is now closed")
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = current_time
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'open'
                logger.error(f"Circuit breaker for {func.__name__} is now open after "
                           f"{self.failure_count} failures")
            
            raise


def circuit_breaker(failure_threshold: int = 5, timeout: float = 60.0):
    """Decorator factory for circuit breaker."""
    return CircuitBreaker(failure_threshold, timeout)