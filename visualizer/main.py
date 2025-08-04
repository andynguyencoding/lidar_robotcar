"""
Main entry point and utility functions for the LiDAR Visualizer
"""

import os
import sys
import shutil
import math
from .config import LIDAR_RESOLUTION
from .data_input import DataManager


def concatenate_augmented_data(input_file):
    """
    Concatenate original data with augmented data for training purposes.
    Creates a new file with both original and augmented data.
    """
    try:
        print(f"Starting data concatenation for: {input_file}")
        
        # Ensure input file exists
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Create output filename
        base_name, ext = os.path.splitext(input_file)
        output_file = f"{base_name}_augmented{ext}"
        
        # Count total lines for progress tracking
        with open(input_file, 'r') as f:
            total_lines = sum(1 for _ in f)
        
        print(f"Processing {total_lines} lines...")
        
        # Read original data and create augmented version
        augmented_lines = []
        processed_lines = 0
        
        with open(input_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Add progress indicator
                processed_lines += 1
                if processed_lines % 1000 == 0:
                    progress = (processed_lines / total_lines) * 100
                    print(f"Progress: {progress:.1f}%")
                
                try:
                    data = line.split(',')
                    if len(data) == LIDAR_RESOLUTION + 1:  # 360 lidar + 1 turn value
                        # Original line
                        augmented_lines.append(line)
                        
                        # Create augmented version (flip turn direction)
                        augmented_data = data.copy()
                        try:
                            original_turn = float(augmented_data[360])
                            augmented_data[360] = str(-original_turn)  # Flip the turn value
                            augmented_line = ','.join(augmented_data)
                            augmented_lines.append(augmented_line)
                        except (ValueError, TypeError):
                            # If turn value is invalid, skip augmented version
                            pass
                            
                except Exception as e:
                    print(f"Warning: Could not process line {processed_lines}: {e}")
                    # Add original line anyway
                    augmented_lines.append(line)
        
        # Write combined data to output file
        print(f"Writing {len(augmented_lines)} lines to {output_file}...")
        with open(output_file, 'w') as f:
            for line in augmented_lines:
                f.write(line + '\n')
        
        print(f"✅ Data concatenation complete!")
        print(f"📁 Original file: {input_file} ({total_lines} lines)")
        print(f"📁 Augmented file: {output_file} ({len(augmented_lines)} lines)")
        print(f"📈 Data increase: {((len(augmented_lines) / total_lines) - 1) * 100:.1f}%")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error in data concatenation: {e}")
        raise


def run(data_file=None, highlight_frames=True, show_augmented=False, inspection_mode=False):
    """
    Main entry point for running the visualizer
    """
    try:
        config = {
            'data_file': data_file or 'data/run1/out1.txt',
            'highlight_frames': highlight_frames,
            'augmented_mode': show_augmented,
            'inspection_mode': inspection_mode
        }
        
        # Import here to avoid circular imports
        from .visualizer_core import VisualizerWindow
        
        # Create and run the visualizer
        visualizer = VisualizerWindow(config)
        visualizer.root.mainloop()
        
    except KeyboardInterrupt:
        print("Visualizer interrupted by user")
    except Exception as e:
        print(f"Error running visualizer: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    """
    Command line entry point
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='LiDAR Robot Car Data Visualizer')
    parser.add_argument('--data-file', '-f', type=str, 
                       help='Path to the data file to visualize (default: data/run1/out1.txt)')
    parser.add_argument('--augmented', '-a', action='store_true',
                       help='Enable augmented data mode')
    parser.add_argument('--inspect', '-i', action='store_true',
                       help='Start in inspection mode')
    
    args = parser.parse_args()
    
    # Run visualizer directly with command line arguments
    run(
        data_file=args.data_file or 'data/run1/out1.txt',  # Default data file
        show_augmented=args.augmented,
        inspection_mode=args.inspect
    )
