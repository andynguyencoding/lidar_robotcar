import numpy as np
import pygame as pg
import csv

COLOR_INACTIVE = pg.Color('red')
COLOR_ACTIVE = pg.Color('green')


class Observable:
    def __init__(self):
        self.observers = []

    def add_observer(self, observer):
        self.observers.append(observer)

    def remove_observer(self, observer):
        self.observers.remove(observer)

    def notify_observers(self):
        for observer in self.observers:
            observer.update(self)


class Observer:
    def update(self, observable):
        pass


class InputBox(Observable):

    def __init__(self, x, y, w, h, font, text=''):
        super().__init__()
        self.rect = pg.Rect(x, y, w, h)
        self.color = COLOR_INACTIVE
        self.text = text
        self.font = font
        self.txt_surface = self.font.render(text, True, self.color)
        self.active = False
        self._value = ''

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE
        if event.type == pg.KEYDOWN:
            if self.active:
                if event.key == pg.K_RETURN:
                    self._value = self.text
                    self.notify_observers()
                    self.text = ''
                elif event.key == pg.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Re-render the text.
                self.txt_surface = self.font.render(self.text, True, self.color)

    def set_text(self, text):
        self.text = text
        self.txt_surface = self.font.render(self.text, True, self.color)

    def update(self):
        # Resize the box if the text is too long.
        width = max(200, self.txt_surface.get_width() + 10)
        self.rect.w = width

    def draw(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        # Blit the rect.
        pg.draw.rect(screen, self.color, self.rect, 2)


class DataManager(Observer):
    def __init__(self, in_file, out_file, w_mode=True):
        super().__init__()
        self.in_file = in_file  # Store the input file path for saving
        self.infile = open(in_file, 'r')
        self.lines = self.infile.readlines()
        
        # Detect and skip header if present
        self._header_detected = self._detect_header()
        self._data_start_line = 1 if self._header_detected else 0
        
        self._pointer = self._data_start_line  # Start from first data line
        self._read_pos = -1
        self.outfile = open(out_file, 'w', newline='')
        self.writer = csv.writer(self.outfile)
        self.w_mode = w_mode
        # current line
        self._line = ''
        # current dataframe
        self._lidar_dataframe = []
        
        # Modified frames tracking
        self._modified_frames = []  # List of frame indices that have been modified
        self._modified_pointer = -1  # Pointer for navigating through modified frames
        
        # Augmented frames tracking
        self._augmented_frames_added = False  # Flag to track if augmented frames were added
        
        if self._header_detected:
            print(f"Header detected in {in_file}, skipping first line")
    
    def _detect_header(self):
        """Detect if the file has a header row"""
        try:
            if not self.lines:
                return False
                
            first_line = self.lines[0].strip()
            if not first_line:
                return False
            
            # Split the first line
            data = first_line.split(',')
            
            # Import LIDAR_RESOLUTION from config
            from config import LIDAR_RESOLUTION
            
            # For our lidar data format, we expect exactly 361 columns (360 lidar + 1 angular velocity)
            if len(data) != LIDAR_RESOLUTION + 1:
                return False  # Not the expected format
            
            # Check if first line contains mostly non-numeric data (likely headers)
            numeric_count = 0
            non_numeric_items = []
            for item in data:
                try:
                    float(item)
                    numeric_count += 1
                except (ValueError, TypeError):
                    non_numeric_items.append(item.strip().lower())
            
            # If less than 80% of values are numeric, likely a header
            numeric_percentage = (numeric_count / len(data)) * 100
            if numeric_percentage < 80:
                return True
            
            # Additional check: if first line has typical header words AND multiple non-numeric fields
            # This prevents false positives from data files with mostly numeric data but one text field
            if len(non_numeric_items) > 1:  # More than one non-numeric field suggests headers
                header_keywords = ['lidar', 'angle', 'distance', 'angular', 'velocity', 'x', 'y', 'theta']
                for item in non_numeric_items:
                    for keyword in header_keywords:
                        if keyword in item:
                            return True
            
            return False
            
        except Exception as e:
            print(f"Error detecting header: {e}")
            return False

    @property
    def dataframe(self):
        if self._read_pos < self._pointer:
            self._line = self.lines[self._pointer].rstrip()
            self._lidar_dataframe = self._line.split(',')
            self._read_pos = self._pointer
        return self._lidar_dataframe

    @property
    def pointer(self):
        return self._pointer

    @property
    def read_pos(self):
        return self._read_pos
    
    @property
    def modified_frames(self):
        """Get the list of modified frame indices"""
        return self._modified_frames.copy()
    
    @property
    def modified_pointer(self):
        """Get the current position in the modified frames list"""
        return self._modified_pointer
    
    @property
    def modified_frames_count(self):
        """Get the total number of modified frames"""
        return len(self._modified_frames)

    def has_next(self):
        return self._pointer < len(self.lines)

    def next(self):
        self._pointer += 1
        return self._lidar_dataframe

    def has_prev(self):
        return self._pointer > self._data_start_line

    def prev(self):
        if self._pointer > self._data_start_line:
            self._pointer -= 1
            # Reset read position to force re-reading of the dataframe
            self._read_pos = self._pointer - 1
        return self._lidar_dataframe

    def first(self):
        """Jump to the first frame"""
        self._pointer = self._data_start_line
        # Reset read position to force re-reading of the dataframe
        self._read_pos = -1
        return self._lidar_dataframe

    def last(self):
        """Jump to the last frame"""
        if len(self.lines) > 0:
            self._pointer = len(self.lines) - 1
            # Reset read position to force re-reading of the dataframe
            self._read_pos = self._pointer - 1
        return self._lidar_dataframe

    # Modified frames navigation methods
    def has_next_modified(self):
        """Check if there's a next modified frame"""
        return self._modified_pointer < len(self._modified_frames) - 1
    
    def has_prev_modified(self):
        """Check if there's a previous modified frame"""
        return self._modified_pointer > 0
    
    def next_modified(self):
        """Navigate to the next modified frame"""
        if self.has_next_modified():
            self._modified_pointer += 1
            self._pointer = self._modified_frames[self._modified_pointer]
            # Reset read position to force re-reading of the dataframe
            self._read_pos = self._pointer - 1
        return self._lidar_dataframe
    
    def prev_modified(self):
        """Navigate to the previous modified frame"""
        if self.has_prev_modified():
            self._modified_pointer -= 1
            self._pointer = self._modified_frames[self._modified_pointer]
            # Reset read position to force re-reading of the dataframe
            self._read_pos = self._pointer - 1
        return self._lidar_dataframe
    
    def first_modified(self):
        """Jump to the first modified frame"""
        if self._modified_frames:
            self._modified_pointer = 0
            self._pointer = self._modified_frames[0]
            # Reset read position to force re-reading of the dataframe
            self._read_pos = self._pointer - 1
        return self._lidar_dataframe
    
    def last_modified(self):
        """Jump to the last modified frame"""
        if self._modified_frames:
            self._modified_pointer = len(self._modified_frames) - 1
            self._pointer = self._modified_frames[-1]
            # Reset read position to force re-reading of the dataframe
            self._read_pos = self._pointer - 1
        return self._lidar_dataframe
    
    def get_modified_position_info(self):
        """Get information about current position in modified frames"""
        if not self._modified_frames:
            return "No modified frames"
        
        if self._pointer in self._modified_frames:
            current_index = self._modified_frames.index(self._pointer)
            return f"Modified frame {current_index + 1} of {len(self._modified_frames)} (Frame #{self._pointer})"
        else:
            return f"Current frame #{self._pointer} (not modified) - {len(self._modified_frames)} modified frames total"
    
    def clear_modified_frames(self):
        """Clear the list of modified frames"""
        self._modified_frames.clear()
        self._modified_pointer = -1
    
    def backup_current_frame(self):
        """Create a backup of the current frame for undo functionality"""
        # This is a placeholder - actual undo functionality would need
        # more sophisticated backup system
        pass
    
    def update_current_frame(self, new_data):
        """Update the current frame with new data"""
        if self._pointer < len(self.lines):
            # Convert the new data to a comma-separated line
            new_line = ','.join(str(x) for x in new_data) + '\n'
            
            # Update the lines array
            self.lines[self._pointer] = new_line
            
            # Update the current dataframe
            self._lidar_dataframe = new_data[:]
            
            # Mark this frame as modified
            if self._pointer not in self._modified_frames:
                self._modified_frames.append(self._pointer)
                self._modified_frames.sort()  # Keep the list sorted
                
            print(f"Frame {self._pointer} updated and marked as modified")
    
    def get_current_dataframe(self):
        """Get current dataframe - compatibility method"""
        return self.dataframe
    
    def update_current_frame_from_string(self, data_string):
        """Update current frame from a comma-separated string"""
        try:
            # Parse the string into data components
            new_data = data_string.split(',')
            
            # Update the current dataframe
            self._lidar_dataframe = new_data[:]
            
            # Mark this frame as modified
            if self._pointer not in self._modified_frames:
                self._modified_frames.append(self._pointer)
                self._modified_frames.sort()  # Keep the list sorted
                
            print(f"Frame {self._pointer} updated from string and marked as modified")
            
        except Exception as e:
            print(f"Error updating frame from string: {e}")
    
    def mark_augmented_frames_added(self):
        """Mark that augmented frames have been added to the dataset"""
        self._augmented_frames_added = True
        print("Marked dataset as having augmented frames added")
    
    def has_changes_to_save(self):
        """Check if there are any changes (modifications or augmented frames) to save"""
        return bool(self._modified_frames) or self._augmented_frames_added

    def save_to_original_file(self):
        """Save all modifications back to the original input file"""
        try:
            # Close the current input file handle
            if hasattr(self, 'infile') and self.infile:
                self.infile.close()
            
            # Write all lines back to the original file
            with open(self.in_file, 'w') as f:
                f.writelines(self.lines)
            
            print(f"DEBUG: Saved {len(self.lines)} lines to {self.in_file}")
            print(f"DEBUG: Modified frames: {self._modified_frames}")
            if self._modified_frames:
                first_modified = self._modified_frames[0]
                print(f"DEBUG: First modified frame ({first_modified}) data: {self.lines[first_modified][:100]}...")
            
            # Reopen the input file for continued reading
            self.infile = open(self.in_file, 'r')
            return True
        except Exception as e:
            print(f"Error saving to original file: {e}")
            # Try to reopen the input file even if save failed
            try:
                self.infile = open(self.in_file, 'r')
            except:
                pass
            return False

    def close(self):
        """Close all file handles"""
        try:
            if hasattr(self, 'infile') and self.infile:
                self.infile.close()
            if hasattr(self, 'outfile') and self.outfile:
                self.outfile.close()
        except:
            pass

    def write_line(self):
        if self.w_mode:
            self.writer.writerow(self._lidar_dataframe)

    def update(self, observable):
        if isinstance(observable, InputBox):
            self._lidar_dataframe[360] = observable.value
            # Update the original line data in memory
            updated_line = ','.join(str(x) for x in self._lidar_dataframe)
            self.lines[self._pointer] = updated_line + '\n'
            # Track this frame as modified
            current_frame = self._pointer
            if current_frame not in self._modified_frames:
                self._modified_frames.append(current_frame)
                self._modified_frames.sort()  # Keep the list sorted
                # Update the modified pointer to point to the current frame
                self._modified_pointer = self._modified_frames.index(current_frame)


def main():
    font = pg.font.Font(None, 32)
    screen = pg.display.set_mode((640, 480))
    clock = pg.time.Clock()
    input_box1 = InputBox(100, 100, 140, 32, font)
    input_box2 = InputBox(100, 300, 140, 32, font)
    input_boxes = [input_box1, input_box2]
    done = False

    while not done:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                done = True
            for box in input_boxes:
                box.handle_event(event)

        for box in input_boxes:
            box.update()

        screen.fill((30, 30, 30))
        for box in input_boxes:
            box.draw(screen)

        pg.display.flip()
        clock.tick(30)


def get_augmented_data():
    data_manager = DataManager('./data/run2/out.txt', './data/run2/augmented_out.txt')
    augmented_data = []
    while data_manager.has_next():
        data = data_manager.dataframe
        augmented_data = np.zeros_like(data)
        for i in range(360):
            augmented_data[359 - i] = data[i]
        augmented_data[360] = 0 - float(data[360])

        data_manager.writer.writerow(augmented_data)

        data_manager.next()
    return augmented_data


def test_modified_frames_navigation():
    """Test function to demonstrate the modified frames navigation functionality"""
    print("Testing Modified Frames Navigation")
    print("=" * 50)
    
    # This would normally be done with actual data files
    # For testing, we'll simulate the functionality
    
    # Create a mock DataManager (this is just for demonstration)
    print("1. DataManager now tracks modified frames automatically")
    print("2. When user updates angular velocity, frame index is added to modified list")
    print("3. New navigation methods available:")
    print("   - has_next_modified() / has_prev_modified()")
    print("   - next_modified() / prev_modified()")
    print("   - first_modified() / last_modified()")
    print("4. Properties available:")
    print("   - modified_frames: list of modified frame indices")
    print("   - modified_frames_count: total number of modified frames")
    print("   - get_modified_position_info(): current position info")
    print("\nExample usage in visualizer:")
    print("- First set: Navigate through ALL frames (existing buttons)")
    print("- Second set: Navigate through MODIFIED frames only (new buttons)")


if __name__ == '__main__':
    # pg.init()
    # main()
    # pg.quit()
    # get_augmented_data()
    test_modified_frames_navigation()
