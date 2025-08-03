#!/usr/bin/env python3
"""
Test script to debug the dataset navigation issue where prev button is disabled 
when it shouldn't be, and the frame navigation doesn't work correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_dataset_pointer_logic():
    """Test the dataset pointer logic that controls button states"""
    print("🔍 DEBUGGING DATASET NAVIGATION ISSUE")
    print("=" * 50)
    
    # Simulate the dataset navigation state
    print("📊 SIMULATING DATASET SPLIT:")
    
    # Example: Original dataset has 849 frames (0-848)
    # After split:
    # - Train: frames [0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800]
    # - Validation: frames [10, 60, 110, 160, 210, 260, 310, 360, 410, 460, 510, 560, 610, 660, 710, 760, 810]  
    # - Test: frames [20, 70, 120, 170, 220, 270, 320, 370, 420, 470, 520, 570, 620, 670, 720, 770, 820]
    
    train_ids = [0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800]
    val_ids = [10, 60, 110, 160, 210, 260, 310, 360, 410, 460, 510, 560, 610, 660, 710, 760, 810]
    test_ids = [20, 70, 120, 170, 220, 270, 320, 370, 420, 470, 520, 570, 620, 670, 720, 770, 820]
    
    print(f"Train dataset: {len(train_ids)} frames, IDs: {train_ids[:5]}...{train_ids[-2:]}")
    print(f"Val dataset: {len(val_ids)} frames, IDs: {val_ids[:5]}...{val_ids[-2:]}")
    print(f"Test dataset: {len(test_ids)} frames, IDs: {test_ids[:5]}...{test_ids[-2:]}")
    
    # Test button state logic
    def test_button_states_for_dataset(dataset_name, dataset_ids, dataset_pointer):
        print(f"\n🔧 TESTING {dataset_name.upper()} DATASET:")
        print(f"   Dataset pointer: {dataset_pointer} (position in {dataset_name} list)")
        print(f"   Total frames in dataset: {len(dataset_ids)}")
        
        if dataset_pointer < len(dataset_ids):
            global_frame_id = dataset_ids[dataset_pointer]
            print(f"   Global frame ID: {global_frame_id}")
        else:
            print(f"   ERROR: Pointer {dataset_pointer} >= dataset size {len(dataset_ids)}")
            return
        
        # Button state logic (copied from the actual code)
        can_go_prev = dataset_pointer > 0
        can_go_next = dataset_pointer < len(dataset_ids) - 1
        
        print(f"   Can go prev: {can_go_prev} (pointer > 0)")
        print(f"   Can go next: {can_go_next} (pointer < {len(dataset_ids) - 1})")
        
        prev_state = "enabled" if can_go_prev else "disabled"
        next_state = "enabled" if can_go_next else "disabled"
        
        print(f"   Button states: Prev={prev_state}, Next={next_state}")
        
        return can_go_prev, can_go_next
    
    # Test scenarios
    scenarios = [
        ("Train", train_ids, 0),   # At beginning  
        ("Train", train_ids, 5),   # In middle
        ("Train", train_ids, 16),  # At end
        ("Val", val_ids, 0),       # At beginning
        ("Val", val_ids, 8),       # In middle  
        ("Val", val_ids, 16),      # At end
    ]
    
    print("\n" + "=" * 60)
    print("BUTTON STATE ANALYSIS:")
    
    for dataset_name, dataset_ids, pointer in scenarios:
        can_prev, can_next = test_button_states_for_dataset(dataset_name, dataset_ids, pointer)
        
        if pointer == 0 and can_prev:
            print(f"   ❌ ERROR: At beginning but prev is enabled!")
        elif pointer > 0 and not can_prev:
            print(f"   ❌ ERROR: Not at beginning but prev is disabled!")
        else:
            print(f"   ✅ Prev button state is correct")
    
    print("\n" + "=" * 60)
    print("🎯 KEY INSIGHTS:")
    print("1. Dataset pointer should be position within the dataset list (0-based)")
    print("2. Global frame ID is dataset_ids[dataset_pointer]")
    print("3. Button states depend on dataset_pointer, not global frame ID")
    print("4. If prev button is disabled when not at start, check dataset_pointer calculation")

def test_navigation_sequence():
    """Test the navigation sequence that might be causing issues"""
    print("\n" + "=" * 60) 
    print("🔄 TESTING NAVIGATION SEQUENCE")
    print("=" * 50)
    
    # Simulate user actions
    print("User scenario: Original set, frame_1 -> next -> prev")
    
    # Original dataset state
    main_pointer = 0  # User starts at frame 1 (global frame 0)
    print(f"1. User starts in Original dataset at frame {main_pointer + 1}")
    
    # User selects a split dataset (e.g., Train)
    current_dataset = 'train'
    train_ids = [0, 50, 100, 150, 200]  # Simplified for testing
    
    # Find the position of current frame in train dataset
    if main_pointer in train_ids:
        train_pointer = train_ids.index(main_pointer)
        print(f"2. User switches to Train dataset")
        print(f"   Global frame {main_pointer} is at position {train_pointer} in train dataset")
    else:
        # Current frame not in train dataset, go to first train frame
        train_pointer = 0
        print(f"2. User switches to Train dataset")
        print(f"   Global frame {main_pointer} not in train, jumping to first train frame")
        print(f"   Train dataset position: {train_pointer}, Global frame: {train_ids[train_pointer]}")
    
    # Test navigation within train dataset
    print(f"\n3. User clicks 'Next' in train dataset:")
    old_train_pointer = train_pointer
    train_pointer = min(train_pointer + 1, len(train_ids) - 1)
    print(f"   Train pointer: {old_train_pointer} -> {train_pointer}")
    print(f"   Global frame: {train_ids[old_train_pointer]} -> {train_ids[train_pointer]}")
    
    print(f"\n4. User clicks 'Prev' in train dataset:")
    old_train_pointer = train_pointer
    train_pointer = max(train_pointer - 1, 0)
    print(f"   Train pointer: {old_train_pointer} -> {train_pointer}")  
    print(f"   Global frame: {train_ids[old_train_pointer]} -> {train_ids[train_pointer]}")
    
    # Check if we're back to original position
    final_global_frame = train_ids[train_pointer]
    if final_global_frame == train_ids[0]:  # Back to first train frame
        print(f"   ✅ Successfully returned to first train frame ({final_global_frame})")
    else:
        print(f"   ❌ Did not return to original position")
    
if __name__ == "__main__":
    test_dataset_pointer_logic()
    test_navigation_sequence()
    
    print("\n" + "=" * 60)
    print("🔍 DEBUGGING CHECKLIST:")
    print("1. Check if _get_current_dataset_pointer() returns correct position")
    print("2. Check if _get_current_dataset_ids() returns correct dataset")
    print("3. Check if button state logic uses dataset_pointer correctly")
    print("4. Check if _sync_data_manager_to_current_frame() updates DataManager correctly")
    print("5. Verify that next/prev navigation actually changes dataset_pointer")
