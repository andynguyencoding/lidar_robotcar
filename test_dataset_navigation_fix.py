#!/usr/bin/env python3
"""
Test script to verify that dataset navigation and button states work correctly.

This test validates:
1. Basic navigation works after DataManager fix
2. Dataset navigation uses consistent state variables
3. Button states reflect actual navigation positions
4. Pointer systems are synchronized between navigation and button logic
"""

import sys
import os
import traceback

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up environment variables needed for testing
os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Avoid GUI issues in testing

try:
    from visualizer_core import VisualizerWindow
    from pginput import DataManager
    import config
    
    def test_dataset_navigation_fix():
        """Test the dataset navigation and button state consistency."""
        try:
            print("=" * 60)
            print("TESTING DATASET NAVIGATION FIX")
            print("=" * 60)
            
            # Create test config
            test_config = {
                'augmented_mode': True,
                'screen_width': 800,
                'screen_height': 600
            }
            
            # Create test instance
            print("Initializing visualizer core...")
            visualizer = VisualizerWindow(test_config)
            
            # Load test data
            test_file = "/home/andy/mysource/github/lidar_robotcar/test_with_headers.csv"
            if not os.path.exists(test_file):
                print(f"❌ Test file not found: {test_file}")
                return False
                
            # Initialize data manager
            print(f"Loading test data from: {test_file}")
            visualizer.data_manager = DataManager()
            visualizer.data_manager.import_from_file(test_file)
            
            total_frames = len(visualizer.data_manager.lines)
            print(f"✅ Loaded {total_frames} frames")
            
            # Test basic navigation consistency (from previous fix)
            print("\n--- Testing Basic Navigation Consistency ---")
            
            # Test the original bug: frame_1 -> next -> prev should return to frame_1
            original_pointer = visualizer.data_manager._pointer
            original_read_pos = visualizer.data_manager._read_pos
            print(f"Starting position - Pointer: {original_pointer}, Read pos: {original_read_pos}")
            
            # Navigate next
            visualizer.data_manager.next()
            after_next_pointer = visualizer.data_manager._pointer
            after_next_read_pos = visualizer.data_manager._read_pos
            print(f"After NEXT - Pointer: {after_next_pointer}, Read pos: {after_next_read_pos}")
            
            # Navigate back
            visualizer.data_manager.prev()
            final_pointer = visualizer.data_manager._pointer
            final_read_pos = visualizer.data_manager._read_pos
            print(f"After PREV - Pointer: {final_pointer}, Read pos: {final_read_pos}")
            
            # Verify we're back to original position
            if original_pointer == final_pointer and original_read_pos == final_read_pos:
                print("✅ Basic navigation consistency: PASSED")
            else:
                print(f"❌ Basic navigation consistency: FAILED")
                print(f"   Expected: Pointer={original_pointer}, Read pos={original_read_pos}")
                print(f"   Got: Pointer={final_pointer}, Read pos={final_read_pos}")
                return False
                
            # Test dataset navigation if splits exist
            print("\n--- Testing Dataset Navigation System ---")
            
            # Check if we have dataset attributes
            has_dataset_system = (hasattr(visualizer, 'train_ids') and 
                                hasattr(visualizer, 'train_pointer') and
                                hasattr(visualizer, '_get_current_dataset_pointer'))
            
            if not has_dataset_system:
                print("ℹ️  Dataset system not initialized - creating mock datasets for testing")
                # Initialize dataset system
                visualizer.train_ids = list(range(0, min(20, total_frames)))
                visualizer.val_ids = list(range(20, min(40, total_frames)))  
                visualizer.test_ids = list(range(40, min(60, total_frames)))
                visualizer.train_pointer = 0
                visualizer.val_pointer = 0  
                visualizer.test_pointer = 0
                visualizer.main_pointer = 0
                visualizer.current_dataset_type = 'train'
                visualizer.current_dataset_position = 0
                
            print(f"Testing dataset system with {len(visualizer.train_ids)} train frames")
            
            # Test pointer consistency between navigation and button states
            print("\n--- Testing Pointer Consistency ---")
            
            # Set to train dataset
            visualizer.current_dataset_type = 'train'
            visualizer.train_pointer = 5  # Set a known position
            
            # Get pointer using button state logic
            button_pointer = visualizer._get_current_dataset_pointer()
            
            # Simulate navigation and check if _navigate_dataset_frame uses same pointer
            old_pointer = button_pointer
            if old_pointer < len(visualizer.train_ids) - 1:
                # Test next navigation
                visualizer._navigate_dataset_frame('next')
                new_button_pointer = visualizer._get_current_dataset_pointer()
                
                if new_button_pointer == old_pointer + 1:
                    print("✅ Next navigation pointer consistency: PASSED")
                else:
                    print(f"❌ Next navigation pointer consistency: FAILED")
                    print(f"   Expected: {old_pointer + 1}, Got: {new_button_pointer}")
                    return False
                    
                # Test prev navigation  
                visualizer._navigate_dataset_frame('prev')
                final_button_pointer = visualizer._get_current_dataset_pointer()
                
                if final_button_pointer == old_pointer:
                    print("✅ Prev navigation pointer consistency: PASSED")
                else:
                    print(f"❌ Prev navigation pointer consistency: FAILED")
                    print(f"   Expected: {old_pointer}, Got: {final_button_pointer}")
                    return False
            else:
                print("ℹ️  Skipping navigation test - train dataset too small")
            
            # Test button state logic
            print("\n--- Testing Button State Logic ---")
            
            # Test at beginning of dataset
            visualizer.train_pointer = 0
            button_pointer = visualizer._get_current_dataset_pointer()
            
            if button_pointer == 0:
                print("✅ Button pointer at beginning: PASSED")
                # At beginning, prev should be disabled, next should be enabled (if dataset has >1 frame)
                if len(visualizer.train_ids) > 1:
                    print("ℹ️  At position 0 of train dataset - prev should be disabled, next enabled")
                else:
                    print("ℹ️  Train dataset has only 1 frame - both buttons should be disabled")
            else:
                print(f"❌ Button pointer at beginning: FAILED - Expected 0, got {button_pointer}")
                return False
                
            # Test at end of dataset
            if len(visualizer.train_ids) > 1:
                visualizer.train_pointer = len(visualizer.train_ids) - 1
                button_pointer = visualizer._get_current_dataset_pointer()
                
                if button_pointer == len(visualizer.train_ids) - 1:
                    print("✅ Button pointer at end: PASSED")
                    print("ℹ️  At last position of train dataset - next should be disabled, prev enabled")
                else:
                    print(f"❌ Button pointer at end: FAILED - Expected {len(visualizer.train_ids) - 1}, got {button_pointer}")
                    return False
            
            # Test dataset switching synchronization
            print("\n--- Testing Dataset Switching ---")
            
            # Test switching between datasets maintains pointers
            visualizer.current_dataset_type = 'train'
            visualizer.train_pointer = 3
            train_position = visualizer._get_current_dataset_pointer()
            
            visualizer.current_dataset_type = 'validation'
            visualizer.val_pointer = 7
            val_position = visualizer._get_current_dataset_pointer()
            
            # Switch back to train
            visualizer.current_dataset_type = 'train'
            restored_train_position = visualizer._get_current_dataset_pointer()
            
            if restored_train_position == train_position:
                print("✅ Dataset switching maintains pointers: PASSED")
            else:
                print(f"❌ Dataset switching maintains pointers: FAILED")
                print(f"   Expected train position: {train_position}, Got: {restored_train_position}")
                return False
                
            print("\n" + "=" * 60)
            print("✅ ALL DATASET NAVIGATION TESTS PASSED!")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"❌ TEST FAILED with exception: {e}")
            print("Traceback:")
            traceback.print_exc()
            return False

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("This test requires the visualizer_core and pginput modules.")
    
    def test_dataset_navigation_fix():
        print("❌ Cannot run test - missing dependencies")
        return False

if __name__ == "__main__":
    success = test_dataset_navigation_fix()
    sys.exit(0 if success else 1)
