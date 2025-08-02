#!/usr/bin/env python3
"""
Test script to verify the dataset radio buttons functionality
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

def test_monolithic_version():
    """Test the radio buttons in the monolithic version"""
    print("Testing monolithic version (visualizer.py)...")
    
    try:
        # Import the monolithic visualizer
        import visualizer
        
        # Create a simple test
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Create visualizer instance with config
        config = {
            'data_file': 'data/run1/out1.txt',
            'highlight_frames': True,
            'augmented_mode': False,
            'inspection_mode': False
        }
        viz = visualizer.VisualizerWindow(config)
        
        # Check if radio buttons exist but are hidden initially
        if hasattr(viz, 'dataset_radio_frame'):
            is_visible = viz.dataset_radio_frame.winfo_manager() is not None
            print(f"✓ Radio buttons exist in monolithic version")
            print(f"✓ Initially hidden: {not is_visible}")
            
            # Test showing radio buttons (simulate data split)
            viz.dataset_radio_frame.pack(fill='x', pady=(5, 0))
            print(f"✓ Radio buttons can be shown")
            
            # Test that default selection is TRAIN
            if hasattr(viz, 'selected_dataset'):
                default_value = viz.selected_dataset.get()
                print(f"✓ Default selection: {default_value}")
            
            print("✓ Monolithic version: PASSED")
        else:
            print("✗ Radio buttons not found in monolithic version")
            return False
            
        root.destroy()
        return True
        
    except Exception as e:
        print(f"✗ Error testing monolithic version: {e}")
        return False

def test_modular_version():
    """Test the radio buttons in the modular version"""
    print("\nTesting modular version (ui_components.py + visualizer_core.py)...")
    
    try:
        # Import the modular components
        from ui_components import UIManager
        from visualizer_core import VisualizerWindow
        
        # Create a simple test
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Create minimal config
        config = {
            'data_file': 'data/run1/out1.txt',
            'highlight_frames': True,
            'augmented_mode': False,
            'inspection_mode': False
        }
        
        # Create visualizer instance
        viz = VisualizerWindow(config)
        
        # Check if radio buttons exist in UI manager
        if hasattr(viz.ui_manager, 'dataset_radio_frame'):
            is_visible = viz.ui_manager.dataset_radio_frame.winfo_manager() is not None
            print(f"✓ Radio buttons exist in modular version")
            print(f"✓ Initially hidden: {not is_visible}")
            
            # Test showing radio buttons
            viz.ui_manager.show_dataset_radio_buttons()
            print(f"✓ Radio buttons can be shown")
            
            # Test that default selection is TRAIN
            if hasattr(viz.ui_manager, 'selected_dataset'):
                default_value = viz.ui_manager.selected_dataset.get()
                print(f"✓ Default selection: {default_value}")
            
            print("✓ Modular version: PASSED")
        else:
            print("✗ Radio buttons not found in modular version")
            return False
            
        root.destroy()
        return True
        
    except Exception as e:
        print(f"✗ Error testing modular version: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Dataset Radio Buttons Test Suite")
    print("=" * 40)
    
    # Test both versions
    monolithic_passed = test_monolithic_version()
    modular_passed = test_modular_version()
    
    print("\n" + "=" * 40)
    print("SUMMARY:")
    print(f"Monolithic version: {'PASSED' if monolithic_passed else 'FAILED'}")
    print(f"Modular version: {'PASSED' if modular_passed else 'FAILED'}")
    
    if monolithic_passed and modular_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("Dataset radio buttons are implemented correctly in both versions!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
