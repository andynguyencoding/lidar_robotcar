#!/usr/bin/env python3
"""
Debug script to identify why split dataset prev navigation isn't working.
This will help us understand what's happening when the user clicks prev.
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_navigation_debug():
    """Debug the navigation flow to identify the issue."""
    print("=" * 70)
    print("DEBUG: SPLIT DATASET NAVIGATION ISSUE")
    print("=" * 70)
    
    print("Let's trace through what should happen when prev button is clicked...")
    print()
    
    # Simulate the current state based on user's description
    print("1. USER SCENARIO:")
    print("   - Dataset is split (train/val/test)")
    print("   - Currently viewing one of the split datasets (not 'main')")
    print("   - Prev button shows as ENABLED")
    print("   - User clicks prev button")
    print("   - Nothing happens (no navigation)")
    print()
    
    print("2. EXPECTED CALL FLOW:")
    print("   Button click → prev_frame() → _navigate_dataset_frame('prev')")
    print()
    
    print("3. POTENTIAL ISSUES TO CHECK:")
    print()
    
    # Issue 1: Conditional logic
    print("   ISSUE 1: Conditional Logic in prev_frame()")
    print("   Code: if self.current_dataset_type != 'main' and hasattr(self, 'train_ids'):")
    print("   Question: Is this condition being met?")
    print()
    
    # Issue 2: _navigate_dataset_frame return value
    print("   ISSUE 2: _navigate_dataset_frame() Return Value")
    print("   Current: Returns None (implicit)")
    print("   Problem: Method doesn't explicitly return True/False for success")
    print()
    
    # Issue 3: Navigation boundary check
    print("   ISSUE 3: Navigation Boundary Logic")
    print("   Code: if direction == 'prev' and current_pointer > 0:")
    print("   Question: Is current_pointer actually > 0?")
    print()
    
    # Issue 4: Dataset pointer synchronization
    print("   ISSUE 4: Dataset Pointer Values")
    print("   Question: Are the dataset pointers initialized correctly?")
    print()
    
    # Issue 5: _navigate_to_frame_id execution
    print("   ISSUE 5: Frame ID Navigation")
    print("   Question: Is _navigate_to_frame_id() actually updating the data manager?")
    print()
    
    print("4. DEBUGGING STRATEGY:")
    print("   Add more debug prints to identify which part is failing:")
    print()
    
    debug_code = '''
    def prev_frame(self):
        """Move to previous frame in inspect mode - DEBUG VERSION"""
        print("DEBUG: prev_frame() called")
        
        if not self.inspect_mode:
            print("DEBUG: Not in inspect mode, returning")
            return
        
        print(f"DEBUG: current_dataset_type = {self.current_dataset_type}")
        print(f"DEBUG: hasattr(self, 'train_ids') = {hasattr(self, 'train_ids')}")
        
        # Check if we're in a split dataset mode
        if self.current_dataset_type != 'main' and hasattr(self, 'train_ids'):
            print("DEBUG: Using dataset navigation")
            result = self._navigate_dataset_frame('prev')
            print(f"DEBUG: _navigate_dataset_frame returned: {result}")
        elif self.frame_navigator.prev_frame():
            print("DEBUG: Using frame navigator")
            # Original navigation logic for main dataset
            # ... rest of code
        else:
            print("DEBUG: No navigation occurred - frame_navigator.prev_frame() returned False")
    '''
    
    print(debug_code)
    print()
    
    print("5. RECOMMENDED FIX:")
    print("   Based on the code analysis, the most likely issue is that")
    print("   _navigate_dataset_frame() doesn't return a proper success indicator.")
    print("   This might cause the navigation to appear to do nothing.")
    print()
    
    return True

if __name__ == "__main__":
    test_navigation_debug()
