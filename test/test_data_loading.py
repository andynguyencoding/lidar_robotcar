#!/usr/bin/env python3
"""
Test data loading and visualization functionality
"""

import sys
import os
import time
sys.path.insert(0, '/home/andy/mysource/github/lidar_robotcar')

def test_data_loading():
    """Test loading different data files and visualization"""
    
    print("🧪 Testing data loading and visualization...")
    
    try:
        # Test imports
        from visualizer.config import SCALE_FACTOR, LIDAR_RESOLUTION
        from pginput import DataManager
        from main import calculate_scale_factor
        
        print("✓ Imports successful")
        
        # Test with different data files
        test_files = []
        if os.path.exists('data/run1/out1.txt'):
            test_files.append('data/run1/out1.txt')
        if os.path.exists('data/run2/out.txt'):
            test_files.append('data/run2/out.txt')
        if os.path.exists('data/run1/out2.txt'):
            test_files.append('data/run1/out2.txt')
        
        if not test_files:
            print("⚠ No test data files found")
            return
        
        print(f"📁 Found {len(test_files)} test files")
        
        # Test each file
        for i, test_file in enumerate(test_files):
            print(f"\n🔧 Testing file {i+1}: {test_file}")
            
            # Create data manager
            data_manager = DataManager(test_file, 'data/run2/_out.txt', False)
            
            # Test initial state
            print(f"  📊 Total lines: {len(data_manager.lines)}")
            print(f"  📍 Initial pointer: {data_manager.pointer}")
            print(f"  📖 Initial read_pos: {data_manager.read_pos}")
            
            # Test initial frame loading (similar to our fixed method)
            if hasattr(data_manager, '_pointer'):
                data_manager._pointer = 0
                data_manager._read_pos = -1  # Force reading of first frame
            
            # Get first frame data
            distances = data_manager.dataframe
            
            if distances and len(distances) == LIDAR_RESOLUTION + 1:
                print(f"  ✅ Frame data loaded: {len(distances)} data points")
                
                # Test some data values
                angular_vel = float(distances[360])
                lidar_sample = [float(distances[j]) for j in range(0, 10)]  # First 10 LiDAR points
                
                print(f"  📊 Angular velocity: {angular_vel:.3f}")
                print(f"  📡 First 10 LiDAR points: {[f'{x:.1f}' for x in lidar_sample]}")
                
                # Calculate scale factor
                calculate_scale_factor(data_manager, sample_size=5)
                
                import config
                print(f"  📏 Scale factor: {config.SCALE_FACTOR:.4f}")
                
            else:
                print(f"  ❌ Frame data error: {len(distances) if distances else 0} data points (expected {LIDAR_RESOLUTION + 1})")
        
        print(f"\n✅ Data loading test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_data_loading()
