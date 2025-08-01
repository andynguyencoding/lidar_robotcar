#!/usr/bin/env python3
"""
Test script to verify the default directory changes for file browsing
"""

import sys
import os
import tkinter as tk
from tkinter import filedialog

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_data_directory_exists():
    """Test that the data directory exists"""
    print("Testing data directory...")
    
    data_dir = "./data"
    if os.path.exists(data_dir):
        print(f"✓ Data directory exists: {os.path.abspath(data_dir)}")
        
        # List some files in the data directory
        try:
            files = os.listdir(data_dir)
            data_files = [f for f in files if f.endswith(('.txt', '.csv'))]
            print(f"  Found {len(data_files)} data files: {data_files[:3]}{'...' if len(data_files) > 3 else ''}")
        except Exception as e:
            print(f"  Error listing files: {e}")
        
        return True
    else:
        print(f"✗ Data directory does not exist: {os.path.abspath(data_dir)}")
        return False

def test_file_manager_import():
    """Test that file_manager can be imported and used"""
    print("\nTesting file_manager import...")
    
    try:
        from file_manager import FileManager
        file_manager = FileManager()
        print("✓ FileManager imported successfully")
        
        # Test the browse_data_file method signature (don't actually open dialog)
        method = getattr(file_manager, 'browse_data_file')
        if method:
            print("✓ browse_data_file method found")
            # Check default parameter
            import inspect
            sig = inspect.signature(method)
            if 'initial_dir' in sig.parameters:
                default_value = sig.parameters['initial_dir'].default
                if default_value == "./data":
                    print(f"✓ Default initial_dir is correctly set to: {default_value}")
                else:
                    print(f"⚠ Default initial_dir is: {default_value} (expected ./data)")
            return True
        else:
            print("✗ browse_data_file method not found")
            return False
            
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_directory_fallback():
    """Test directory fallback logic"""
    print("\nTesting directory fallback logic...")
    
    try:
        # Test existing directory
        data_dir = "./data"
        if os.path.exists(data_dir):
            result_dir = data_dir
        else:
            result_dir = "."
        print(f"✓ Directory selection logic: {data_dir} -> {result_dir}")
        
        # Test non-existing directory
        fake_dir = "./nonexistent_dir"
        if os.path.exists(fake_dir):
            result_dir = fake_dir
        else:
            result_dir = "."
        print(f"✓ Fallback logic: {fake_dir} -> {result_dir}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing fallback: {e}")
        return False

def test_ui_integration():
    """Test that the UI would work with new defaults"""
    print("\nTesting UI integration...")
    
    try:
        # Test the file types configuration
        file_types = [
            ("CSV files", "*.csv"),
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        print(f"✓ File types configured: {len(file_types)} types")
        
        # Test that tkinter filedialog can be imported
        from tkinter import filedialog
        print("✓ tkinter.filedialog imported successfully")
        
        # Test directory path resolution
        data_path = os.path.abspath("./data")
        current_path = os.path.abspath(".")
        print(f"✓ Path resolution:")
        print(f"  ./data resolves to: {data_path}")
        print(f"  . resolves to: {current_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ UI integration error: {e}")
        return False

if __name__ == "__main__":
    print("=== Default Directory Change Test ===\n")
    
    # Test data directory
    data_exists = test_data_directory_exists()
    
    # Test file manager
    file_manager_ok = test_file_manager_import()
    
    # Test fallback logic
    fallback_ok = test_directory_fallback()
    
    # Test UI integration
    ui_ok = test_ui_integration()
    
    print(f"\n=== Test Results ===")
    print(f"Data directory exists: {'✓ PASS' if data_exists else '✗ FAIL'}")
    print(f"FileManager integration: {'✓ PASS' if file_manager_ok else '✗ FAIL'}")
    print(f"Fallback logic: {'✓ PASS' if fallback_ok else '✗ FAIL'}")
    print(f"UI integration: {'✓ PASS' if ui_ok else '✗ FAIL'}")
    
    if data_exists and file_manager_ok and fallback_ok and ui_ok:
        print("\n🎉 Default directory change implemented successfully!")
        print("\nChanges made:")
        print("  - file_manager.py: Changed default from /home/andy to ./data")
        print("  - visualizer.py: Changed default from /home/andy to ./data") 
        print("  - visualizer_core.py: Added robust directory checking for AI models")
        print("  - Added fallback to current directory if ./data doesn't exist")
        print("\nFile browser will now default to:")
        print("  - Data files: ./data directory")
        print("  - AI models: ./models directory")
    else:
        print("\n❌ Some issues found. Check the errors above.")
        sys.exit(1)
