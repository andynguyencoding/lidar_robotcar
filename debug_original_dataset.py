#!/usr/bin/env python3
"""
Debug guide for the "original dataset prev button disabled" issue.
"""

def debug_original_dataset_issue():
    print("=" * 70)
    print("DEBUG GUIDE: ORIGINAL DATASET PREV BUTTON ISSUE")
    print("=" * 70)
    
    print("ISSUE: When switching back to 'original' dataset, prev button is disabled")
    print("even when not at the first frame.")
    print()
    
    print("DEBUGGING STEPS:")
    print("1. Load your dataset and split it (train/val/test)")
    print("2. Navigate in one of the split datasets (e.g., train)")
    print("3. Switch back to 'Original' dataset")
    print("4. Check console output for debug messages")
    print()
    
    print("WHAT TO LOOK FOR IN DEBUG OUTPUT:")
    print()
    
    print("A. DATASET SWITCHING MESSAGES:")
    print("   - Should see: 'DATASET SELECTION CHANGE'")
    print("   - Should see: 'Switching from: TRAIN → ORIGINAL' (or similar)")
    print("   - Should see: 'Saved train_pointer = X (global frame Y)'")
    print("   - Should see: 'For main dataset, main_pointer = Z'")
    print()
    
    print("B. DATA MANAGER SYNC MESSAGES:")
    print("   - Should see: '_sync_data_manager_to_current_frame() - global_frame_id = N'")  
    print("   - Should see: 'Before sync - data_manager._pointer = M'")
    print("   - Should see: 'After sync - data_manager._pointer = N'")
    print("   - Should see: 'data_manager.has_prev() = True/False'")
    print()
    
    print("C. BUTTON STATE MESSAGES:")
    print("   - Should see: 'update_button_states() called - current_dataset_type = main'")
    print("   - Should see: 'has_data_splits = True'") 
    print("   - Should see: 'Using dataset navigation logic'")
    print()
    
    print("POTENTIAL ISSUES TO IDENTIFY:")
    print()
    
    print("ISSUE 1: main_pointer is 0")
    print("   - If you see 'main_pointer = 0', but you were at a different frame")
    print("   - This means main_pointer wasn't properly saved when switching away")
    print()
    
    print("ISSUE 2: data_manager.has_prev() returns False")
    print("   - If you see 'data_manager.has_prev() = False' but pointer > 0")
    print("   - This could be a problem with _data_start_line or boundary checking")
    print()
    
    print("ISSUE 3: Button state logic choosing wrong path")
    print("   - If you see 'Using regular navigation logic' instead of 'Using dataset navigation logic'")
    print("   - This means the button logic is using the wrong method")
    print()
    
    print("COMMON SCENARIOS:")
    print()
    
    print("Scenario A: main_pointer not saved correctly")
    print("   Expected: main_pointer should be the frame you were at before splitting")
    print("   Problem: main_pointer is 0, causing nav to think you're at beginning")
    print("   Solution: Fix the main_pointer initialization/saving logic")
    print()
    
    print("Scenario B: data_manager._pointer out of sync")
    print("   Expected: data_manager._pointer should match main_pointer for main dataset")
    print("   Problem: Pointer mismatch causing has_prev() to return wrong value")
    print("   Solution: Fix the sync logic in _sync_data_manager_to_current_frame()")
    print()
    
    print("=" * 70)
    print("PLEASE RUN THE TEST AND SHARE THE DEBUG OUTPUT")
    print("=" * 70)

if __name__ == "__main__":
    debug_original_dataset_issue()
