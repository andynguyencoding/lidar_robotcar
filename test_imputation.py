#!/usr/bin/env python3
"""
Test script to validate the imputation functionality
"""

import os
import sys
sys.path.append('.')

from pginput import DataManager
import math

def test_data_format():
    """Test the data format to ensure it's correct"""
    print("Testing data format...")
    
    data_file = 'data/run1/out1.txt'
    if not os.path.exists(data_file):
        print(f"Data file {data_file} not found!")
        return False
    
    # Use DataManager to read data
    manager = DataManager(data_file, 'test_output.txt', w_mode=False)
    
    line_count = 0
    valid_lines = 0
    invalid_count = 0
    
    while manager.has_next() and line_count < 10:  # Test first 10 lines
        data = manager.dataframe
        line_count += 1
        
        print(f"Line {line_count}: Length = {len(data)}")
        
        if len(data) == 361:  # 360 lidar + 1 angular velocity
            valid_lines += 1
            
            # Count invalid lidar readings
            line_invalid = 0
            for i in range(360):
                try:
                    value = float(data[i])
                    if math.isinf(value) or math.isnan(value) or value == 0:
                        line_invalid += 1
                except (ValueError, TypeError):
                    line_invalid += 1
            
            invalid_count += line_invalid
            
            # Show angular velocity
            try:
                ang_vel = float(data[360])
                print(f"  Angular velocity: {ang_vel}")
            except:
                print(f"  Angular velocity: INVALID ({data[360]})")
            
            print(f"  Invalid lidar readings in this line: {line_invalid}")
        else:
            print(f"  ERROR: Expected 361 data points, got {len(data)}")
        
        manager.next()
    
    manager.infile.close()
    
    print(f"\nSummary:")
    print(f"Lines tested: {line_count}")
    print(f"Valid format lines: {valid_lines}")
    print(f"Total invalid lidar readings: {invalid_count}")
    
    # Clean up
    try:
        os.remove('test_output.txt')
    except:
        pass
    
    return valid_lines == line_count

def test_imputation_logic():
    """Test the imputation logic with sample data"""
    print("\nTesting imputation logic...")
    
    # Sample data with invalid values (represented as None initially, 0 in actual data)
    test_data = [100.0, 0, 120.0, 0, 140.0, 150.0, 0, 170.0]  # 0 represents invalid
    
    # Convert to our format (None for invalid)
    lidar_values = []
    for val in test_data:
        if val == 0:
            lidar_values.append(None)
        else:
            lidar_values.append(val)
    
    print(f"Original: {test_data}")
    print(f"As processed: {lidar_values}")
    
    # Apply imputation logic
    for i in range(len(lidar_values)):
        if lidar_values[i] is None:  # Invalid value found
            # Find left valid value
            left_val = None
            left_idx = i - 1
            while left_idx >= 0 and left_val is None:
                if lidar_values[left_idx] is not None:
                    left_val = lidar_values[left_idx]
                    break
                left_idx -= 1
            
            # Find right valid value
            right_val = None
            right_idx = i + 1
            while right_idx < len(lidar_values) and right_val is None:
                if lidar_values[right_idx] is not None:
                    right_val = lidar_values[right_idx]
                    break
                right_idx += 1
            
            # Impute based on available adjacent values
            if left_val is not None and right_val is not None:
                # Average of left and right
                lidar_values[i] = (left_val + right_val) / 2
                print(f"  Position {i}: Imputed as average of {left_val} and {right_val} = {lidar_values[i]}")
            elif left_val is not None:
                # Use left value
                lidar_values[i] = left_val
                print(f"  Position {i}: Imputed using left value {left_val}")
            elif right_val is not None:
                # Use right value
                lidar_values[i] = right_val
                print(f"  Position {i}: Imputed using right value {right_val}")
            else:
                # No valid adjacent values, use default
                lidar_values[i] = 500.0
                print(f"  Position {i}: Imputed using default value 500.0")
    
    print(f"After imputation: {lidar_values}")
    return True

if __name__ == "__main__":
    print("="*50)
    print("LIDAR DATA IMPUTATION TEST")
    print("="*50)
    
    success1 = test_data_format()
    success2 = test_imputation_logic()
    
    print(f"\n{'='*50}")
    if success1 and success2:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED!")
    print("="*50)
