#!/usr/bin/env python3
"""
LiDAR Visualizer Launcher

This is the main entry point for the LiDAR Visualizer application.
It provides both command-line interface and startup configuration dialog.
"""

import sys
import os
import argparse

# Add the current directory to Python path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point for the visualizer application"""
    
    parser = argparse.ArgumentParser(description='LiDAR Robot Car Data Visualizer')
    parser.add_argument('--data-file', '-f', type=str, 
                       help='Path to the data file to visualize (default: data/run1/out1.txt)')
    parser.add_argument('--augmented', '-a', action='store_true',
                       help='Enable augmented data mode')
    parser.add_argument('--inspect', '-i', action='store_true',
                       help='Start in inspection mode')
    
    args = parser.parse_args()
    
    try:
        # Run modular visualizer
        print("Starting visualizer...")
        from visualizer.main import run
        
        run(
            data_file=args.data_file or 'data/run1/out1.txt',
            show_augmented=args.augmented,
            inspection_mode=args.inspect
        )
            
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you're running from the project root directory.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nVisualizer interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error running visualizer: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
