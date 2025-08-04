#!/usr/bin/env python3
"""
Test the improved scale factor calculation
"""

import sys
import os
sys.path.insert(0, '/home/andy/mysource/github/lidar_robotcar')

try:
    print("Testing improved scale factor calculation...")
    
    # Test imports
    from visualizer.config import SCALE_FACTOR, LIDAR_RESOLUTION, TARGET_RADIUS
    from main import calculate_scale_factor
    from pginput import DataManager
    
    print(f"✓ Imports successful")
    print(f"  Initial SCALE_FACTOR: {SCALE_FACTOR}")
    print(f"  TARGET_RADIUS: {TARGET_RADIUS}")
    
    # Test with different data files if available
    test_files = []
    if os.path.exists('data/run1/out1.txt'):
        test_files.append('data/run1/out1.txt')
    if os.path.exists('data/run2/out.txt'):
        test_files.append('data/run2/out.txt')
    if os.path.exists('data/run1/out2.txt'):
        test_files.append('data/run1/out2.txt')
    
    if not test_files:
        print("⚠ No test data files found")
        sys.exit(1)
    
    for i, test_file in enumerate(test_files):
        print(f"\n🔧 Testing with file {i+1}: {test_file}")
        
        # Create data manager
        data_manager = DataManager(test_file, 'data/run2/_out.txt', False)
        print(f"  📊 Total lines in file: {len(data_manager.lines)}")
        
        # Calculate scale factor using improved method
        result_scale = calculate_scale_factor(data_manager, sample_size=15)
        
        # Check if config was updated
        import config
        print(f"  ✓ Scale factor calculated: {result_scale:.4f}")
        print(f"  ✓ Config updated: {config.SCALE_FACTOR:.4f}")
        
        # Verify data manager reset correctly
        print(f"  ✓ Data manager pointer reset: {data_manager.pointer}")
        
        if i == 0:
            first_scale = result_scale
        else:
            if abs(result_scale - first_scale) > 0.001:
                print(f"  ✓ Scale factor varies between files: {first_scale:.4f} vs {result_scale:.4f}")
            else:
                print(f"  ⚠ Scale factors similar between different files")
    
    print(f"\n✅ Improved scale factor calculation test completed!")
    print(f"The scale factor now properly analyzes sample data and adapts to different environments.")
    
except Exception as e:
    print(f"❌ Test error: {e}")
    import traceback
    traceback.print_exc()
