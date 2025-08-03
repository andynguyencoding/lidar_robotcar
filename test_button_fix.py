#!/usr/bin/env python3
"""
Test script to demonstrate the fixed navigation button states for dataset navigation
"""

def test_button_state_logic():
    """Test the navigation button state logic for different scenarios"""
    print("=== NAVIGATION BUTTON STATE FIX ===\n")
    
    def simulate_button_states(dataset_type, current_pointer, total_frames):
        """Simulate how button states will be determined"""
        states = {
            'first': 'normal' if current_pointer > 0 else 'disabled',
            'prev': 'normal' if current_pointer > 0 else 'disabled',
            'next': 'normal' if current_pointer < total_frames - 1 else 'disabled',
            'last': 'normal' if current_pointer < total_frames - 1 else 'disabled'
        }
        return states
    
    print("🔧 PROBLEM IDENTIFIED:")
    print("❌ Old logic tried to find global frame ID in local dataset indices")
    print("❌ For example: Looking for frame 156 in [0, 1, 2, 3, 4] → ValueError")
    print("❌ ValueError caused all buttons to be disabled")
    print()
    
    print("✅ SOLUTION IMPLEMENTED:")
    print("✅ Use separate dataset pointers instead of global frame IDs")
    print("✅ Compare pointer position against dataset size")
    print("✅ Simple arithmetic: pointer vs (total_frames - 1)")
    print()
    
    # Test scenarios
    scenarios = [
        ("Original", 0, 849, "Full dataset, at beginning"),
        ("Original", 424, 849, "Full dataset, in middle"),  
        ("Original", 848, 849, "Full dataset, at end"),
        ("Train", 0, 20, "Train dataset, at beginning"),
        ("Train", 10, 20, "Train dataset, in middle"),
        ("Train", 19, 20, "Train dataset, at end"),
        ("Validation", 0, 20, "Validation dataset, at beginning"),
        ("Validation", 10, 20, "Validation dataset, in middle"),
        ("Validation", 19, 20, "Validation dataset, at end"),
        ("Test", 0, 20, "Test dataset, at beginning"),
        ("Test", 10, 20, "Test dataset, in middle"),
        ("Test", 19, 20, "Test dataset, at end"),
    ]
    
    print("🧪 BUTTON STATE TEST SCENARIOS:")
    print("Dataset       Pointer  Total  │ First  Prev   Next   Last  │ Description")
    print("─" * 80)
    
    for dataset, pointer, total, description in scenarios:
        states = simulate_button_states(dataset, pointer, total)
        
        first_state = "🟢" if states['first'] == 'normal' else "🔴"
        prev_state = "🟢" if states['prev'] == 'normal' else "🔴"
        next_state = "🟢" if states['next'] == 'normal' else "🔴"
        last_state = "🟢" if states['last'] == 'normal' else "🔴"
        
        print(f"{dataset:<12}  {pointer:>3}/{total:<3}    │ {first_state}      {prev_state}      {next_state}      {last_state}   │ {description}")
    
    print()
    print("🟢 = Enabled (normal state)")
    print("🔴 = Disabled")
    print()
    
    print("🔍 KEY LOGIC CHANGES:")
    print()
    print("Modular Version (visualizer_core.py):")
    print("  _update_dataset_button_states():")
    print("    - OLD: dataset_frames.index(current_frame) → ValueError for split datasets")
    print("    - NEW: current_pointer = self._get_current_dataset_pointer()")
    print("    - NEW: Compare pointer < total_frames - 1")
    print()
    
    print("Monolithic Version (visualizer.py):")
    print("  update_button_states():")
    print("    - OLD: self.data_manager.has_prev() / has_next() → Wrong for split datasets")
    print("    - NEW: Check if in dataset mode: self.current_dataset_type != 'main'")
    print("    - NEW: Use separate pointer logic for datasets")
    print("    - NEW: Fall back to data_manager.has_prev() for Original dataset")
    print()
    
    print("🎯 EXPECTED BEHAVIOR:")
    print("1. Original dataset: Uses full navigation (849 frames)")
    print("2. Train/Val/Test: Uses subset navigation (20 frames each)")
    print("3. First/Last buttons disabled at boundaries")
    print("4. Prev/Next buttons disabled at boundaries")
    print("5. Navigation works smoothly in all datasets")

if __name__ == "__main__":
    test_button_state_logic()
