#!/usr/bin/env python3
"""
Test script to verify change tracking functionality
"""

def test_change_tracking_methods():
    """Check if change tracking methods are properly implemented"""
    
    # Check monolithic version
    print("Testing monolithic version (visualizer.py)...")
    try:
        with open('visualizer.py', 'r') as f:
            monolithic_content = f.read()
        
        # Check for required methods
        required_methods = [
            'mark_data_changed', 'mark_data_saved', 'prompt_save_before_exit'
        ]
        
        missing_methods = []
        for method in required_methods:
            if f'def {method}(' not in monolithic_content:
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing methods in monolithic version: {missing_methods}")
        else:
            print("✅ All required methods found in monolithic version")
        
        # Check for change tracking calls
        change_tracking_calls = [
            'mark_data_changed()',
            'mark_data_saved()'
        ]
        
        found_calls = {}
        for call in change_tracking_calls:
            count = monolithic_content.count(call)
            found_calls[call] = count
            print(f"   - {call}: {count} calls found")
        
    except FileNotFoundError:
        print("❌ visualizer.py not found")
    
    print()
    
    # Check modular version
    print("Testing modular version (visualizer_core.py)...")
    try:
        with open('visualizer_core.py', 'r') as f:
            modular_content = f.read()
        
        # Check for required methods
        missing_methods = []
        for method in required_methods:
            if f'def {method}(' not in modular_content:
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing methods in modular version: {missing_methods}")
        else:
            print("✅ All required methods found in modular version")
        
        # Check for change tracking calls
        found_calls = {}
        for call in change_tracking_calls:
            count = modular_content.count(call)
            found_calls[call] = count
            print(f"   - {call}: {count} calls found")
        
    except FileNotFoundError:
        print("❌ visualizer_core.py not found")

if __name__ == "__main__":
    test_change_tracking_methods()
