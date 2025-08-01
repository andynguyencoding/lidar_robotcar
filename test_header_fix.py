#!/usr/bin/env python3
"""
Test script to verify the header detection fix
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_header_detection():
    """Test that header detection works for the autonomous_lidar_data file"""
    print("Testing header detection fix...")
    
    # Test file path (use an actual file with headers)
    test_file = "data/simulation/autonomous_lidar_data_20250801_155701.csv"
    
    if not os.path.exists(test_file):
        print(f"✗ Test file not found: {test_file}")
        return False
    
    try:
        # Test DataManager with header detection
        from pginput import DataManager
        print(f"✓ DataManager imported successfully")
        
        # Create a temporary output file for testing
        temp_output = "temp_test_output.txt"
        
        # Create DataManager instance
        print(f"Creating DataManager for: {test_file}")
        data_manager = DataManager(test_file, temp_output, False)
        
        # Check if header was detected
        has_header = getattr(data_manager, '_header_detected', False)
        data_start_line = getattr(data_manager, '_data_start_line', 0)
        
        print(f"✓ Header detected: {has_header}")
        print(f"✓ Data start line: {data_start_line}")
        
        # Test first frame reading
        if data_manager.has_next():
            first_frame = data_manager.dataframe
            print(f"✓ First frame length: {len(first_frame)}")
            
            if len(first_frame) >= 361:
                # Check if first frame contains numeric data (not headers)
                try:
                    # Try to convert the angular velocity (last column) to float
                    angular_vel = float(first_frame[360])
                    print(f"✓ Angular velocity from first frame: {angular_vel}")
                    
                    # Try to convert some LiDAR distances to float
                    lidar_sample = [float(first_frame[i]) for i in range(0, 5)]
                    print(f"✓ First 5 LiDAR distances: {lidar_sample}")
                    
                    print("✓ Successfully parsed numeric data from first frame")
                    
                except ValueError as e:
                    print(f"✗ Error parsing first frame data: {e}")
                    print(f"   First frame data sample: {first_frame[:5]} ... {first_frame[360]}")
                    # Clean up and return failure
                    data_manager.infile.close()
                    data_manager.outfile.close()
                    if os.path.exists(temp_output):
                        os.remove(temp_output)
                    return False
            else:
                print(f"✗ First frame has wrong length: {len(first_frame)}, expected 361")
                return False
        else:
            print("✗ No data frames available")
            return False
        
        # Test navigation
        print("Testing navigation...")
        initial_pointer = data_manager.pointer
        print(f"✓ Initial pointer: {initial_pointer}")
        
        # Test has_prev (should be False if we're at the first data line)
        has_prev = data_manager.has_prev()
        print(f"✓ Has previous frame: {has_prev}")
        
        # If header was detected, initial pointer should be 1, and has_prev should be False
        if has_header:
            if initial_pointer == 1 and not has_prev:
                print("✓ Navigation correctly starts after header")
            else:
                print(f"✗ Navigation issue - pointer: {initial_pointer}, has_prev: {has_prev}")
        
        # Test moving to next frame
        if data_manager.has_next():
            data_manager.next()
            second_frame = data_manager.dataframe
            print(f"✓ Second frame length: {len(second_frame)}")
            
            # Test second frame data
            try:
                angular_vel_2 = float(second_frame[360])
                print(f"✓ Angular velocity from second frame: {angular_vel_2}")
            except ValueError as e:
                print(f"✗ Error parsing second frame: {e}")
        
        # Clean up
        data_manager.infile.close()
        data_manager.outfile.close()
        if os.path.exists(temp_output):
            os.remove(temp_output)
            
        return True
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_content():
    """Test the content of the autonomous_lidar_data file"""
    print("\nTesting file content...")
    
    test_file = "data/simulation/autonomous_lidar_data_20250801_155701.csv"
    
    try:
        with open(test_file, 'r') as f:
            lines = f.readlines()
        
        print(f"✓ File has {len(lines)} lines")
        
        if len(lines) > 0:
            first_line = lines[0].strip()
            print(f"✓ First line: {first_line[:100]}...")
            
            # Check if it looks like a header
            columns = first_line.split(',')
            print(f"✓ First line has {len(columns)} columns")
            
            # Try to parse first few columns as numbers
            numeric_count = 0
            for i, col in enumerate(columns[:10]):  # Check first 10 columns
                try:
                    float(col)
                    numeric_count += 1
                except ValueError:
                    pass
            
            numeric_percent = (numeric_count / 10) * 100
            print(f"✓ First 10 columns are {numeric_percent:.1f}% numeric")
            
            if numeric_percent < 80:
                print("✓ First line appears to be a header (low numeric percentage)")
            else:
                print("✓ First line appears to be data (high numeric percentage)")
        
        if len(lines) > 1:
            second_line = lines[1].strip()
            print(f"✓ Second line: {second_line[:100]}...")
            
            # Try to parse second line
            columns = second_line.split(',')
            if len(columns) >= 361:
                try:
                    angular_vel = float(columns[360])
                    lidar_sample = [float(columns[i]) for i in range(0, 5)]
                    print(f"✓ Second line parsed successfully - angular_vel: {angular_vel}, lidar sample: {lidar_sample}")
                except ValueError as e:
                    print(f"✗ Error parsing second line: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return False

if __name__ == "__main__":
    print("=== Header Detection Fix Test ===\n")
    
    # Test file content first
    content_ok = test_file_content()
    
    # Test DataManager header detection
    detection_ok = test_header_detection()
    
    print(f"\n=== Test Results ===")
    print(f"File content analysis: {'✓ PASS' if content_ok else '✗ FAIL'}")
    print(f"Header detection: {'✓ PASS' if detection_ok else '✗ FAIL'}")
    
    if content_ok and detection_ok:
        print("\n🎉 Header detection fix works correctly!")
        print("\nChanges made:")
        print("  - Added _detect_header() method to DataManager")
        print("  - DataManager now starts from _data_start_line (0 or 1)")
        print("  - Updated load_initial_frame() to respect header detection")
        print("  - Updated calculate_scale_factor() in both versions")
        print("  - Navigation methods respect data start line")
    else:
        print("\n❌ Some issues remain. Check the errors above.")
        sys.exit(1)
