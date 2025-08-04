#!/usr/bin/env python3
"""
Logging utilities for the LiDAR Robot Car project.

This module provides centralized logging functionality
for the modular visualizer application.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional


class VisualizerLogger:
    """
    Centralized logger for the LiDAR Robotcar Visualizer
    
    Supports multiple logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    Configurable output to console and/or file
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VisualizerLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.logger = logging.getLogger('LiDARVisualizer')
            self.logger.setLevel(logging.INFO)  # Default level
            
            # Prevent duplicate handlers
            if not self.logger.handlers:
                self._setup_handlers()
            
            VisualizerLogger._initialized = True
    
    def _setup_handlers(self):
        """Setup console and file handlers with formatters"""
        
        # Create formatters
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler with timestamped filenames
        try:
            # Create logs directory if it doesn't exist
            log_dir = os.path.join(os.path.dirname(__file__), 'logs')
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Generate timestamped log filename
            log_file = self._generate_log_filename(log_dir)
            
            # Use TimedRotatingFileHandler for daily rotation with custom naming
            file_handler = logging.handlers.TimedRotatingFileHandler(
                log_file, 
                when='midnight',
                interval=1,
                backupCount=30,  # Keep 30 days of logs
                encoding='utf-8'
            )
            
            # Custom filename for rotated logs
            file_handler.namer = self._get_rotated_filename
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            self.log_file_path = log_file
            
        except Exception as e:
            # If file logging fails, continue with console only
            self.logger.warning(f"Could not setup file logging: {e}")
            self.log_file_path = None
    
    def _generate_log_filename(self, log_dir):
        """
        Generate a timestamped log filename with running number
        
        Pattern: visualizer_YYYYMMDD_NNN.log
        Where NNN is a running number (001, 002, etc.) for the same date
        
        Args:
            log_dir: Directory to store log files
            
        Returns:
            str: Full path to the log file
        """
        from datetime import datetime
        
        # Get current date
        date_str = datetime.now().strftime('%Y%m%d')
        
        # Find the next available running number for today
        running_number = 1
        while True:
            filename = f"visualizer_{date_str}_{running_number:03d}.log"
            log_file = os.path.join(log_dir, filename)
            
            # If file doesn't exist or is small (likely new session), use it
            if not os.path.exists(log_file) or os.path.getsize(log_file) < 1024:  # Less than 1KB
                break
                
            running_number += 1
            
            # Safety check to prevent infinite loop
            if running_number > 999:
                filename = f"visualizer_{date_str}_999.log"
                log_file = os.path.join(log_dir, filename)
                break
        
        return log_file
    
    def _get_rotated_filename(self, default_name):
        """
        Custom filename generator for rotated log files
        
        Args:
            default_name: Default rotated filename from TimedRotatingFileHandler
            
        Returns:
            str: Custom filename with timestamp and sequence
        """
        # Extract date from the default rotated name
        # Default format is usually: filename.YYYY-MM-DD
        try:
            base_path = os.path.dirname(default_name)
            
            # Extract date from default name
            if '.' in default_name:
                parts = default_name.split('.')
                if len(parts) >= 2:
                    date_part = parts[-1]  # Should be YYYY-MM-DD
                    # Convert YYYY-MM-DD to YYYYMMDD
                    date_formatted = date_part.replace('-', '')
                    
                    # Find next available sequence number for this date
                    sequence = 1
                    while True:
                        rotated_filename = f"visualizer_{date_formatted}_{sequence:03d}_archived.log"
                        rotated_path = os.path.join(base_path, rotated_filename)
                        
                        if not os.path.exists(rotated_path):
                            return rotated_path
                            
                        sequence += 1
                        if sequence > 999:
                            return os.path.join(base_path, f"visualizer_{date_formatted}_999_archived.log")
            
            # Fallback to default name if parsing fails
            return default_name
            
        except Exception:
            # If anything goes wrong, use default naming
            return default_name
            self.log_file_path = None
    
    def set_level(self, level: str):
        """
        Set the logging level
        
        Args:
            level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        if level.upper() in level_map:
            self.logger.setLevel(level_map[level.upper()])
            # Also update console handler level
            for handler in self.logger.handlers:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    handler.setLevel(level_map[level.upper()])
            self.info(f"Logging level set to {level.upper()}")
        else:
            self.error(f"Invalid logging level: {level}. Valid levels: {list(level_map.keys())}")
    
    def get_level(self) -> str:
        """Get current logging level as string"""
        level_map = {
            logging.DEBUG: 'DEBUG',
            logging.INFO: 'INFO',
            logging.WARNING: 'WARNING',
            logging.ERROR: 'ERROR',
            logging.CRITICAL: 'CRITICAL'
        }
        return level_map.get(self.logger.level, 'UNKNOWN')
    
    def get_log_file_path(self) -> Optional[str]:
        """Get the current log file path"""
        return getattr(self, 'log_file_path', None)
    
    def is_file_logging_enabled(self) -> bool:
        """Check if file logging is enabled and working"""
        return hasattr(self, 'log_file_path') and self.log_file_path is not None
    
    def is_console_logging_enabled(self) -> bool:
        """Check if console logging is enabled"""
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                return True
        return False
    
    def get_logging_info(self) -> dict:
        """Get comprehensive logging configuration information"""
        return {
            'level': self.get_level(),
            'console_enabled': self.is_console_logging_enabled(),
            'file_enabled': self.is_file_logging_enabled(),
            'log_file_path': self.get_log_file_path(),
            'handlers_count': len(self.logger.handlers),
            'log_directory': os.path.join(os.path.dirname(__file__), 'logs') if self.is_file_logging_enabled() else None
        }
    
    # Logging methods
    def debug(self, message: str, module: Optional[str] = None):
        """Log debug message"""
        if module:
            message = f"[{module}] {message}"
        self.logger.debug(message)
    
    def info(self, message: str, module: Optional[str] = None):
        """Log info message"""
        if module:
            message = f"[{module}] {message}"
        self.logger.info(message)
    
    def warning(self, message: str, module: Optional[str] = None):
        """Log warning message"""
        if module:
            message = f"[{module}] {message}"
        self.logger.warning(message)
    
    def error(self, message: str, module: Optional[str] = None):
        """Log error message"""
        if module:
            message = f"[{module}] {message}"
        self.logger.error(message)
    
    def critical(self, message: str, module: Optional[str] = None):
        """Log critical message"""
        if module:
            message = f"[{module}] {message}"
        self.logger.critical(message)
    
    def log_exception(self, message: str, exc_info=True, module: Optional[str] = None):
        """Log exception with traceback"""
        if module:
            message = f"[{module}] {message}"
        self.logger.error(message, exc_info=exc_info)
    
    def log_function_entry(self, func_name: str, module: Optional[str] = None, **kwargs):
        """Log function entry with parameters (DEBUG level)"""
        params = ', '.join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else "no params"
        self.debug(f"Entering {func_name}({params})", module)
    
    def log_function_exit(self, func_name: str, result=None, module: Optional[str] = None):
        """Log function exit with result (DEBUG level)"""
        result_str = f" -> {result}" if result is not None else ""
        self.debug(f"Exiting {func_name}{result_str}", module)
    
    def log_data_operation(self, operation: str, details: str, module: Optional[str] = None):
        """Log data operations (INFO level)"""
        self.info(f"Data operation: {operation} - {details}", module)
    
    def log_ui_event(self, event: str, details: str = ""):
        """Log UI events (DEBUG level)"""
        message = f"UI Event: {event}"
        if details:
            message += f" - {details}"
        self.debug(message, "UI")
    
    def log_navigation(self, action: str, from_frame: int, to_frame: int, dataset_type: str = "main"):
        """Log navigation events (INFO level)"""
        self.info(f"Navigation: {action} from frame {from_frame} to {to_frame} in {dataset_type} dataset", "Navigation")
    
    def log_dataset_operation(self, operation: str, dataset_type: str, details: str = ""):
        """Log dataset operations (INFO level)"""
        message = f"Dataset operation: {operation} on {dataset_type} dataset"
        if details:
            message += f" - {details}"
        self.info(message, "Dataset")
    
    def log_performance(self, operation: str, duration: float, details: str = ""):
        """Log performance metrics (DEBUG level)"""
        message = f"Performance: {operation} took {duration:.3f}s"
        if details:
            message += f" - {details}"
        self.debug(message, "Performance")


# Global logger instance
_logger_instance = None

def get_logger() -> VisualizerLogger:
    """Get the global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = VisualizerLogger()
    return _logger_instance


# Convenience functions for direct use
def set_log_level(level: str):
    """Set the global logging level"""
    get_logger().set_level(level)

def get_log_level() -> str:
    """Get the current logging level"""
    return get_logger().get_level()

def get_log_file_path() -> Optional[str]:
    """Get the current log file path"""
    return get_logger().get_log_file_path()

def is_file_logging_enabled() -> bool:
    """Check if file logging is enabled"""
    return get_logger().is_file_logging_enabled()

def is_console_logging_enabled() -> bool:
    """Check if console logging is enabled"""
    return get_logger().is_console_logging_enabled()

def get_logging_info() -> dict:
    """Get comprehensive logging configuration information"""
    return get_logger().get_logging_info()

def debug(message: str, module: Optional[str] = None):
    """Log debug message"""
    get_logger().debug(message, module)

def info(message: str, module: Optional[str] = None):
    """Log info message"""
    get_logger().info(message, module)

def warning(message: str, module: Optional[str] = None):
    """Log warning message"""
    get_logger().warning(message, module)

def error(message: str, module: Optional[str] = None):
    """Log error message"""
    get_logger().error(message, module)

def critical(message: str, module: Optional[str] = None):
    """Log critical message"""
    get_logger().critical(message, module)

def log_exception(message: str, exc_info=True, module: Optional[str] = None):
    """Log exception with traceback"""
    get_logger().log_exception(message, exc_info, module)

def log_function_entry(func_name: str, module: Optional[str] = None, **kwargs):
    """Log function entry"""
    get_logger().log_function_entry(func_name, module, **kwargs)

def log_function_exit(func_name: str, result=None, module: Optional[str] = None):
    """Log function exit"""
    get_logger().log_function_exit(func_name, result, module)

def log_data_operation(operation: str, details: str, module: Optional[str] = None):
    """Log data operations"""
    get_logger().log_data_operation(operation, details, module)

def log_ui_event(event: str, details: str = ""):
    """Log UI events"""
    get_logger().log_ui_event(event, details)

def log_navigation(action: str, from_frame: int, to_frame: int, dataset_type: str = "main"):
    """Log navigation events"""
    get_logger().log_navigation(action, from_frame, to_frame, dataset_type)

def log_dataset_operation(operation: str, dataset_type: str, details: str = ""):
    """Log dataset operations"""
    get_logger().log_dataset_operation(operation, dataset_type, details)

def log_performance(operation: str, duration: float, details: str = ""):
    """Log performance metrics"""
    get_logger().log_performance(operation, duration, details)


# Decorator for function logging
def log_function(module: Optional[str] = None):
    """
    Decorator to automatically log function entry and exit
    
    Usage:
        @log_function("ModuleName")
        def my_function(param1, param2):
            return result
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            # Log entry with parameters (excluding 'self' for methods)
            params = {}
            if args and hasattr(args[0], '__class__'):
                # Skip 'self' parameter for methods
                for i, arg in enumerate(args[1:], 1):
                    params[f'arg{i}'] = arg
            else:
                for i, arg in enumerate(args):
                    params[f'arg{i}'] = arg
            params.update(kwargs)
            
            log_function_entry(func_name, module, **params)
            
            try:
                result = func(*args, **kwargs)
                log_function_exit(func_name, result, module)
                return result
            except Exception as e:
                log_exception(f"Exception in {func_name}: {str(e)}", module=module)
                raise
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test the logging system
    logger = get_logger()
    
    print("Testing logging system...")
    
    # Test different levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test module-specific logging
    logger.info("Module-specific message", "TestModule")
    
    # Test specialized logging functions
    logger.log_ui_event("Button clicked", "Next frame button")
    logger.log_navigation("next", 5, 6, "train")
    logger.log_dataset_operation("split", "main", "70/20/10 ratio")
    logger.log_performance("frame_render", 0.123, "360 points")
    
    # Test level changing
    print(f"\nCurrent level: {logger.get_level()}")
    logger.set_level("DEBUG")
    logger.debug("This debug message should now be visible")
    
    # Test decorator
    @log_function("TestModule")
    def test_function(x, y, option="default"):
        return x + y
    
    result = test_function(1, 2, option="test")
    print(f"Function result: {result}")
