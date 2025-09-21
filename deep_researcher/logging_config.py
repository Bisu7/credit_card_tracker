"""Comprehensive logging configuration for Deep Researcher Agent."""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime

from .config import config


class PerformanceFilter(logging.Filter):
    """Filter for performance-related log messages."""
    
    def filter(self, record):
        return hasattr(record, 'performance') and record.performance


class ErrorFilter(logging.Filter):
    """Filter for error-related log messages."""
    
    def filter(self, record):
        return record.levelno >= logging.ERROR


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add performance metrics if present
        if hasattr(record, 'performance_metrics'):
            log_entry['performance'] = record.performance_metrics
        
        # Add context if present
        if hasattr(record, 'context'):
            log_entry['context'] = record.context
        
        return json.dumps(log_entry)


class LoggingManager:
    """Manages logging configuration for the entire system."""
    
    def __init__(self, log_dir: Optional[str] = None, log_level: str = "INFO"):
        """
        Initialize logging manager.
        
        Args:
            log_dir: Directory for log files
            log_level: Default logging level
        """
        self.log_dir = Path(log_dir or os.path.join(config.data_dir, "logs"))
        self.log_level = getattr(logging, log_level.upper())
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up comprehensive logging configuration."""
        
        # Clear existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Set root logger level
        root_logger.setLevel(logging.DEBUG)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        json_formatter = JSONFormatter()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
        
        # Main application log file
        main_log_file = self.log_dir / "deep_researcher.log"
        main_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        main_handler.setLevel(logging.DEBUG)
        main_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(main_handler)
        
        # Error log file
        error_log_file = self.log_dir / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        error_handler.addFilter(ErrorFilter())
        root_logger.addHandler(error_handler)
        
        # Performance log file
        performance_log_file = self.log_dir / "performance.log"
        performance_handler = logging.handlers.RotatingFileHandler(
            performance_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        performance_handler.setLevel(logging.INFO)
        performance_handler.setFormatter(json_formatter)
        performance_handler.addFilter(PerformanceFilter())
        root_logger.addHandler(performance_handler)
        
        # JSON structured log file
        json_log_file = self.log_dir / "structured.jsonl"
        json_handler = logging.handlers.RotatingFileHandler(
            json_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=3
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(json_formatter)
        root_logger.addHandler(json_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the specified name."""
        return logging.getLogger(name)
    
    def log_performance(self, logger: logging.Logger, operation: str, 
                       duration: float, **metrics):
        """Log performance metrics."""
        performance_data = {
            'operation': operation,
            'duration_seconds': duration,
            **metrics
        }
        
        # Create log record with performance flag
        record = logger.makeRecord(
            logger.name, logging.INFO, "", 0,
            f"Performance: {operation} completed in {duration:.2f}s",
            (), None
        )
        record.performance = True
        record.performance_metrics = performance_data
        
        logger.handle(record)
    
    def log_with_context(self, logger: logging.Logger, level: int, 
                        message: str, context: Dict[str, Any]):
        """Log message with additional context."""
        record = logger.makeRecord(
            logger.name, level, "", 0, message, (), None
        )
        record.context = context
        logger.handle(record)


# Global logging manager instance
_logging_manager = None


def get_logging_manager() -> LoggingManager:
    """Get the global logging manager instance."""
    global _logging_manager
    if _logging_manager is None:
        _logging_manager = LoggingManager()
    return _logging_manager


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return get_logging_manager().get_logger(name)


def log_performance(logger: logging.Logger, operation: str, 
                   duration: float, **metrics):
    """Log performance metrics."""
    get_logging_manager().log_performance(logger, operation, duration, **metrics)


def log_with_context(logger: logging.Logger, level: int, 
                    message: str, context: Dict[str, Any]):
    """Log message with additional context."""
    get_logging_manager().log_with_context(logger, level, message, context)