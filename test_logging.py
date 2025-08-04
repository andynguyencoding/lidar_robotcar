#!/usr/bin/env python3
"""
Test script for the logging system
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from logger import get_logger, info, debug, warning, error, critical, log_function
import config

def test_logging_system():
    """Test the logging system functionality"""
    logger = get_logger()
    
    print("=== Testing LiDAR Visualizer Logging System ===\n")
    
    # Test current level
    print(f"Current logging level: {logger.get_level()}")
    
    # Test different log levels
    print("\n--- Testing different log levels ---")
    debug("This is a debug message", "TestModule")
    info("This is an info message", "TestModule")
    warning("This is a warning message", "TestModule")
    error("This is an error message", "TestModule")
    critical("This is a critical message", "TestModule")
    
    # Test specialized logging methods
    print("\n--- Testing specialized logging methods ---")
    logger.log_ui_event("Button clicked", "Test button")
    logger.log_navigation("next", 5, 6, "train")
    logger.log_dataset_operation("split", "main", "70/20/10 ratio")
    logger.log_performance("frame_render", 0.123, "360 points")
    
    # Test function decorator
    print("\n--- Testing function decorator ---")
    
    @log_function("TestModule")
    def sample_function(x, y, option="default"):
        """Sample function to test logging decorator"""
        result = x + y
        return result
    
    result = sample_function(10, 20, option="test")
    print(f"Function returned: {result}")
    
    # Test level changing
    print(f"\n--- Testing level changes ---")
    print(f"Current level: {logger.get_level()}")
    
    logger.set_level("WARNING")
    print("After setting to WARNING level:")
    debug("This debug message should NOT appear")
    info("This info message should NOT appear")
    warning("This warning message SHOULD appear")
    
    # Reset to INFO
    logger.set_level("INFO")
    print("\nReset to INFO level")
    info("Info messages should now appear again")
    
    # Test exception logging
    print("\n--- Testing exception logging ---")
    try:
        raise ValueError("This is a test exception")
    except ValueError as e:
        logger.log_exception("Caught test exception", module="TestModule")
    
    print("\n=== Logging test completed ===")
    print(f"Check the logs directory for 'visualizer.log' file")
    
    # Show log file location
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    log_file = os.path.join(log_dir, 'visualizer.log')
    if os.path.exists(log_file):
        print(f"Log file location: {log_file}")
        print(f"Log file size: {os.path.getsize(log_file)} bytes")
    else:
        print(f"Log file will be created at: {log_file}")

if __name__ == "__main__":
    test_logging_system()
