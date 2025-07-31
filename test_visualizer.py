#!/usr/bin/env python3
"""
Test script to directly test the VisualizerWindow with input fields
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from visualizer import VisualizerWindow

def test_visualizer():
    """Test the visualizer window directly"""
    print("Testing VisualizerWindow with input fields...")
    
    # Create a test configuration
    config = {
        'data_file': 'data/run1/out1.txt',
        'inspection_mode': True,  # Start in inspection mode for easier testing
        'augmented_mode': False,
        'concatenate_data': False
    }
    
    try:
        # Create and run the visualizer
        visualizer = VisualizerWindow(config)
        print("Visualizer window created successfully!")
        print("Input fields should be visible at the bottom of the window.")
        print("Instructions:")
        print("- Angular Velocity field: Type a value and press Enter to update")
        print("- Linear Velocity field: Placeholder (not yet implemented)")
        print("- Use Space, I, A, Q keys for controls")
        visualizer.run()
    except Exception as e:
        print(f"Error creating visualizer: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_visualizer()
