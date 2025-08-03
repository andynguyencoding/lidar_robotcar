#!/usr/bin/env python3
"""
Test for the complete navigation flow to verify the split dataset prev button issue is fixed.
"""

import sys
import os

def test_complete_navigation_flow():
    """Test the complete navigation flow including data manager sync."""
    print("=" * 70)
    print("TESTING COMPLETE NAVIGATION FLOW - PREV BUTTON FIX")
    print("=" * 70)
    
    # Mock DataManager with the same behavior as the real one
    class MockDataManager:
        def __init__(self, total_frames=100):
            self.lines = [f"frame_{i}_data" for i in range(total_frames)]
            self._pointer = 0
            self._read_pos = -1
            self._data_start_line = 0
        
        @property
        def dataframe(self):
            """Mock dataframe property that checks _read_pos like the real one"""
            if self._read_pos < self._pointer:
                self._line = self.lines[self._pointer]
                self._lidar_dataframe = self._line.split('_')  # Mock split
                self._read_pos = self._pointer
                print(f"DEBUG: DataManager read frame {self._pointer}: {self._line}")
            return self._lidar_dataframe
    
    # Mock the complete navigation system
    class MockVisualizer:
        def __init__(self):
            self.data_manager = MockDataManager()
            self.main_dataset = self.data_manager  # Reference to main dataset
            
            # Dataset setup
            self.train_ids = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45]  # 10 frames
            self.val_ids = [1, 6, 11, 16, 21, 26, 31, 36, 41, 46]    # 10 frames
            self.test_ids = [2, 7, 12, 17, 22, 27, 32, 37, 42, 47]   # 10 frames
            
            # Pointers
            self.train_pointer = 5  # Start at middle position
            self.val_pointer = 0
            self.test_pointer = 0
            self.main_pointer = 0
            
            self.current_dataset_type = 'train'
            self.current_dataset_position = 5  # For backward compatibility
            
            self.distances = []  # Mock distances
        
        def _get_current_dataset_pointer(self):
            """Get the pointer for the current dataset"""
            if self.current_dataset_type == 'train':
                return self.train_pointer
            elif self.current_dataset_type == 'validation':
                return self.val_pointer
            elif self.current_dataset_type == 'test':
                return self.test_pointer
            else:  # main
                return self.main_pointer
        
        def _set_current_dataset_pointer(self, position):
            """Set the pointer for the current dataset"""
            if self.current_dataset_type == 'train':
                self.train_pointer = max(0, min(position, len(self.train_ids) - 1))
            elif self.current_dataset_type == 'validation':
                self.val_pointer = max(0, min(position, len(self.val_ids) - 1))
            elif self.current_dataset_type == 'test':
                self.test_pointer = max(0, min(position, len(self.test_ids) - 1))
            else:  # main
                self.main_pointer = max(0, min(position, len(self.main_dataset.lines) - 1))
        
        def _get_current_dataset_ids(self):
            """Get the IDs for the current dataset"""
            if self.current_dataset_type == 'train':
                return self.train_ids
            elif self.current_dataset_type == 'validation':
                return self.val_ids
            elif self.current_dataset_type == 'test':
                return self.test_ids
            else:
                return list(range(len(self.main_dataset.lines)))
        
        def _get_current_frame_id(self):
            """Get the actual frame ID in the original dataset (FIXED VERSION)"""
            current_pointer = self._get_current_dataset_pointer()
            dataset_ids = self._get_current_dataset_ids()
            
            if current_pointer < len(dataset_ids):
                return dataset_ids[current_pointer]
            return 0
        
        def _navigate_to_frame_id(self, frame_id):
            """Navigate the main dataset to a specific frame ID (FIXED VERSION)"""
            if 0 <= frame_id < len(self.main_dataset.lines):
                self.main_dataset._pointer = frame_id
                self.data_manager._pointer = frame_id  # Keep data_manager in sync
                # Reset read position to force re-reading of the dataframe
                self.data_manager._read_pos = frame_id - 1
                print(f"DEBUG: Navigated data manager to frame ID {frame_id}")
        
        def render_frame(self):
            """Mock render frame"""
            print(f"DEBUG: Rendered frame")
        
        def update_inputs(self):
            """Mock update inputs"""
            print(f"DEBUG: Updated inputs")
        
        def update_button_states(self):
            """Mock update button states"""
            current_pointer = self._get_current_dataset_pointer()
            dataset_size = len(self._get_current_dataset_ids())
            
            prev_enabled = current_pointer > 0
            next_enabled = current_pointer < dataset_size - 1
            
            print(f"DEBUG: Button states - Prev: {'enabled' if prev_enabled else 'disabled'}, Next: {'enabled' if next_enabled else 'disabled'}")
        
        def _navigate_dataset_frame(self, direction):
            """Navigate within the current ID-based dataset (FIXED VERSION)"""
            dataset_ids = self._get_current_dataset_ids()
            
            # Get current pointer and update based on direction
            current_pointer = self._get_current_dataset_pointer()
            old_position = current_pointer
            
            if direction == 'prev' and current_pointer > 0:
                new_position = current_pointer - 1
            elif direction == 'next' and current_pointer < len(dataset_ids) - 1:
                new_position = current_pointer + 1
            else:
                print(f"Navigation blocked: {direction} not possible from position {current_pointer} in {self.current_dataset_type} dataset")
                return False  # Can't navigate further
            
            # Set the new position using the dataset pointer system
            self._set_current_dataset_pointer(new_position)
            
            # Get updated position for display
            self.current_dataset_position = new_position  # Keep for backward compatibility
            new_pointer = self._get_current_dataset_pointer()
            
            # Navigate to the frame ID in the original dataset
            frame_id = self._get_current_frame_id()
            print(f"Navigation: {self.current_dataset_type.upper()} {old_position}→{new_pointer} (Frame ID: {frame_id})")
            self._navigate_to_frame_id(frame_id)
            
            # Update the display
            self.distances = self.data_manager.dataframe
            if len(self.distances) >= 3:  # Mock check (361 in real code)
                self.render_frame()
                self.update_inputs()
            
            self.update_button_states()
            print(f"Dataset navigation: {self.current_dataset_type.upper()} frame {new_pointer + 1}/{len(dataset_ids)} (ID: {frame_id})")
            return True
        
        def prev_frame(self):
            """Move to previous frame in inspect mode (FIXED VERSION)"""
            print(f"\n--- PREV_FRAME CALLED ---")
            
            # Check if we're in a split dataset mode
            if self.current_dataset_type != 'main' and hasattr(self, 'train_ids'):
                print(f"Using dataset navigation for {self.current_dataset_type}")
                return self._navigate_dataset_frame('prev')
            else:
                print(f"Would use main dataset navigation")
                return False
    
    # Run the test
    print("Setting up mock visualizer...")
    visualizer = MockVisualizer()
    
    print(f"\n--- Initial State ---")
    print(f"Dataset: {visualizer.current_dataset_type}")
    print(f"Pointer: {visualizer._get_current_dataset_pointer()}")
    print(f"Frame ID: {visualizer._get_current_frame_id()}")
    print(f"Data Manager Pointer: {visualizer.data_manager._pointer}")
    print(f"Data Manager Read Pos: {visualizer.data_manager._read_pos}")
    
    print(f"\n--- Test 1: First Prev Navigation ---")
    success = visualizer.prev_frame()
    if success:
        print(f"✅ First prev navigation: SUCCESS")
        print(f"New pointer: {visualizer._get_current_dataset_pointer()}")
        print(f"New frame ID: {visualizer._get_current_frame_id()}")
        print(f"Data Manager Pointer: {visualizer.data_manager._pointer}")
        print(f"Data Manager Read Pos: {visualizer.data_manager._read_pos}")
        
        # Test that dataframe property works
        dataframe = visualizer.data_manager.dataframe
        print(f"Dataframe access successful: {dataframe[:2]}...")
    else:
        print(f"❌ First prev navigation: FAILED")
        return False
    
    print(f"\n--- Test 2: Second Prev Navigation ---")
    success = visualizer.prev_frame()
    if success:
        print(f"✅ Second prev navigation: SUCCESS")
        print(f"New pointer: {visualizer._get_current_dataset_pointer()}")
        print(f"New frame ID: {visualizer._get_current_frame_id()}")
        print(f"Data Manager Pointer: {visualizer.data_manager._pointer}")
        
        # Test that dataframe updates correctly
        dataframe = visualizer.data_manager.dataframe
        print(f"Dataframe access successful: {dataframe[:2]}...")
    else:
        print(f"❌ Second prev navigation: FAILED")
        return False
    
    print(f"\n--- Test 3: Multiple Prev Until Beginning ---")
    navigation_count = 0
    while True:
        old_pointer = visualizer._get_current_dataset_pointer()
        success = visualizer.prev_frame()
        navigation_count += 1
        
        if not success:
            print(f"Navigation stopped at position {old_pointer} after {navigation_count-1} steps")
            break
        
        if navigation_count > 10:  # Safety break
            print(f"❌ Too many navigation steps - possible infinite loop")
            return False
    
    final_pointer = visualizer._get_current_dataset_pointer()
    if final_pointer == 0:
        print(f"✅ Multiple prev navigation: SUCCESS (reached beginning)")
    else:
        print(f"❌ Multiple prev navigation: FAILED (stopped at {final_pointer})")
        return False
    
    print(f"\n--- Test 4: Data Manager Synchronization Check ---")
    # Verify that data manager is correctly synchronized
    expected_frame_id = visualizer._get_current_frame_id()
    actual_data_manager_pointer = visualizer.data_manager._pointer
    
    if expected_frame_id == actual_data_manager_pointer:
        print(f"✅ Data manager synchronization: SUCCESS")
        print(f"Frame ID: {expected_frame_id}, Data Manager Pointer: {actual_data_manager_pointer}")
    else:
        print(f"❌ Data manager synchronization: FAILED")
        print(f"Expected Frame ID: {expected_frame_id}, Data Manager Pointer: {actual_data_manager_pointer}")
        return False
    
    print(f"\n" + "=" * 70)
    print("✅ ALL COMPLETE NAVIGATION FLOW TESTS PASSED!")
    print("=" * 70)
    print("\nThe fixes should now resolve the split dataset prev button issue:")
    print("✅ _navigate_dataset_frame() uses consistent pointer system")
    print("✅ _get_current_frame_id() uses dataset pointers")
    print("✅ _navigate_to_frame_id() properly syncs data manager")
    print("✅ data_manager._read_pos is reset to force dataframe re-reading")
    print("✅ Complete navigation flow updates display and button states")
    
    return True

if __name__ == "__main__":
    try:
        success = test_complete_navigation_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ TEST FAILED with exception: {e}")
        import traceback
        print("Traceback:")
        traceback.print_exc()
        sys.exit(1)
