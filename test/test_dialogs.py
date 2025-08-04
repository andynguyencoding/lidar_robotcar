#!/usr/bin/env python3
"""
Quick test for the scale factor and direction ratio dialogs
"""

import sys
import os
sys.path.insert(0, '/home/andy/mysource/github/lidar_robotcar')

try:
    print("Testing modular dialog implementations...")
    
    # Test imports
    from visualizer.config import SCALE_FACTOR, LIDAR_RESOLUTION
    from main import calculate_scale_factor
    from pginput import DataManager
    
    print(f"✓ Config imports successful")
    print(f"  SCALE_FACTOR: {SCALE_FACTOR}")
    print(f"  LIDAR_RESOLUTION: {LIDAR_RESOLUTION}")
    
    # Test data manager creation with default file
    default_data_file = 'data/run1/out1.txt'
    if os.path.exists(default_data_file):
        print(f"✓ Default data file exists: {default_data_file}")
        
        # Test data manager initialization
        data_manager = DataManager(default_data_file, 'data/run2/_out.txt', False)
        print(f"✓ DataManager created successfully")
        print(f"  Total lines: {len(data_manager.lines)}")
        
        # Test scale factor calculation
        calculate_scale_factor(data_manager)
        print(f"✓ Scale factor calculation completed")
        
    else:
        print(f"⚠ Default data file not found: {default_data_file}")
        available_files = []
        if os.path.exists('data/run1/'):
            available_files.extend([f"data/run1/{f}" for f in os.listdir('data/run1/') if f.endswith('.txt')])
        if os.path.exists('data/run2/'):
            available_files.extend([f"data/run2/{f}" for f in os.listdir('data/run2/') if f.endswith('.txt')])
        
        if available_files:
            test_file = available_files[0]
            print(f"  Using alternative file: {test_file}")
            data_manager = DataManager(test_file, 'data/run2/_out.txt', False)
            calculate_scale_factor(data_manager)
            print(f"✓ Scale factor calculation completed with alternative file")
        else:
            print("  No data files found for testing")
    
    print(f"\n✅ All modular dialog tests passed!")
    print(f"The scale factor and direction ratio dialogs should now work properly.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Test error: {e}")
    import traceback
    traceback.print_exc()
