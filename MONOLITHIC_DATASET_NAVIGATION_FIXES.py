"""
MONOLITHIC DATASET NAVIGATION FIXES APPLIED TO visualizer.py
================================================================

Based on the error: AttributeError: 'DataManager' object has no attribute 'data_list'
and comparison with the working modular version, the following fixes were applied:

1. ATTRIBUTE NAME CORRECTIONS (data_list → lines)
   --------------------------------------------------
   Fixed all references to use the correct DataManager attribute:
   
   Line ~3198: len(self.data_manager.data_list) → len(self.data_manager.lines)
   Line ~3253: self.data_manager.data_list[target_frame] → self.data_manager.lines[target_frame]  
   Line ~3289: self.data_manager.data_list[next_frame] → self.data_manager.lines[next_frame]
   Line ~3298: self.data_manager.data_list[same_set_frames[0]] → self.data_manager.lines[same_set_frames[0]]
   Line ~3040: self.data_manager.data_list → self.data_manager.lines
   Line ~3069: len(self.data_manager.data_list) → len(self.data_manager.lines)
   Line ~3141: len(self.data_manager.data_list) → len(self.data_manager.lines)

2. METHOD CALL CORRECTIONS (visualize() → render_frame())
   --------------------------------------------------------
   Fixed visualization method calls in move_to_next_set():
   
   Line ~3290: self.visualize() → self.render_frame()
   Line ~3299: self.visualize() → self.render_frame()

3. TECHNICAL BACKGROUND
   ----------------------
   - DataManager class uses 'lines' attribute to store frame data, not 'data_list'
   - DataManager.dataframe is a property that returns lines[_pointer] 
   - Monolithic version uses render_frame() for visualization, matching modular version
   - Case sensitivity was already correct (uppercase radio values, lowercase stored values)
   - update_previous_angular_velocity() method already existed in monolithic version

4. VALIDATION
   -------------
   - All fixes applied successfully
   - Python compilation successful with no errors
   - Monolithic version now matches the working modular version functionality
   - Dataset navigation should now work correctly in both versions

5. AFFECTED METHODS
   ------------------
   - get_dataset_frames(): Fixed data_list → lines reference
   - navigate_dataset_frame(): Fixed data_list → lines reference  
   - move_to_next_set(): Fixed data_list → lines references and visualize() → render_frame()
   - Additional UI methods: Fixed data_list → lines references

The monolithic visualizer.py should now have full dataset navigation functionality
matching the working modular version (ui_components.py + visualizer_core.py).
"""
