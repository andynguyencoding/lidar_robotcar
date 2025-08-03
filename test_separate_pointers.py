#!/usr/bin/env python3
"""
Test script to demonstrate the separate dataset pointer system
"""

def test_separate_pointers():
    """Test the separate dataset pointer logic"""
    print("=== SEPARATE DATASET POINTERS TEST ===\n")
    
    # Simulate a dataset with 100 frames (IDs 0-99)
    total_frames = 100
    
    # Simulate split datasets using IDs
    train_ids = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45]    # 10 frames from train
    val_ids = [1, 6, 11, 16, 21, 26, 31, 36, 41, 46]      # 10 frames from validation  
    test_ids = [2, 7, 12, 17, 22, 27, 32, 37, 42, 47]     # 10 frames from test
    
    # Simulate separate pointers for each dataset
    main_pointer = 0       # Position in original dataset (0-99)
    train_pointer = 0      # Position in train_ids list (0-9)
    val_pointer = 0        # Position in val_ids list (0-9)
    test_pointer = 0       # Position in test_ids list (0-9)
    
    def get_current_global_frame_id(dataset_type, pointer, train_ids, val_ids, test_ids, main_pointer):
        """Get the global frame ID based on dataset and pointer"""
        if dataset_type == 'train':
            if pointer < len(train_ids):
                return train_ids[pointer]
        elif dataset_type == 'validation':
            if pointer < len(val_ids):
                return val_ids[pointer]
        elif dataset_type == 'test':
            if pointer < len(test_ids):
                return test_ids[pointer]
        else:  # main
            return main_pointer
        return 0
    
    def simulate_navigation(dataset_type, current_pointer, dataset_ids):
        """Simulate navigation within a dataset"""
        print(f"\n--- {dataset_type.upper()} Dataset Navigation ---")
        print(f"Dataset has {len(dataset_ids)} frames")
        print(f"Frame IDs: {dataset_ids}")
        
        # Test navigation at different positions
        for pos in [0, 2, 4, len(dataset_ids)-1]:
            if pos < len(dataset_ids):
                global_frame_id = dataset_ids[pos]
                actual_frame_id = global_frame_id + 1  # +1 for display
                dataset_position = pos + 1  # +1 for display
                
                print(f"  Position {dataset_position}/{len(dataset_ids)}: Frame {actual_frame_id} (Global ID: {global_frame_id})")
    
    print("=== SEPARATE POINTER BENEFITS ===")
    print("1. Each dataset maintains its own navigation position")
    print("2. Switching between datasets preserves where you were")
    print("3. Navigation is independent per dataset")
    print("4. Frame IDs always show the actual original frame number")
    print()
    
    # Simulate navigation in each dataset
    simulate_navigation('train', train_pointer, train_ids)
    simulate_navigation('validation', val_pointer, val_ids)
    simulate_navigation('test', test_pointer, test_ids)
    
    print("\n=== DATASET SWITCHING SCENARIO ===")
    
    # Simulate user navigating through train dataset
    current_dataset = 'train'
    train_pointer = 3  # User navigated to 4th position in train
    print(f"1. User navigates to position 4 in TRAIN dataset")
    global_frame = get_current_global_frame_id(current_dataset, train_pointer, train_ids, val_ids, test_ids, main_pointer)
    print(f"   Showing Frame {global_frame + 1} (Global ID: {global_frame})")
    
    # User switches to validation dataset  
    val_pointer = 1  # Validation was previously at position 2
    current_dataset = 'validation'
    print(f"\n2. User switches to VALIDATION dataset")
    print(f"   Restores to position 2 (where they left off in validation)")
    global_frame = get_current_global_frame_id(current_dataset, val_pointer, train_ids, val_ids, test_ids, main_pointer)
    print(f"   Showing Frame {global_frame + 1} (Global ID: {global_frame})")
    
    # User switches back to train dataset
    current_dataset = 'train'
    print(f"\n3. User switches back to TRAIN dataset")
    print(f"   Restores to position 4 (where they left off in train)")
    global_frame = get_current_global_frame_id(current_dataset, train_pointer, train_ids, val_ids, test_ids, main_pointer)
    print(f"   Showing Frame {global_frame + 1} (Global ID: {global_frame})")
    
    print("\n=== KEY IMPROVEMENTS ===")
    print("✅ Navigation state preserved when switching datasets")
    print("✅ Each dataset remembers where user was")
    print("✅ Frame numbers always show actual original frame ID")
    print("✅ Position within dataset clearly indicated")
    print("✅ No more confusion about frame 1, 2, 3... when it should be frame 91, 156, etc.")

if __name__ == "__main__":
    test_separate_pointers()
