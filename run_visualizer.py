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
    
    parser = argparse.ArgumentParser(description='LiDAR Robot Car Data Visualizer (runs modular version by default)')
    parser.add_argument('--data-file', '-f', type=str, 
                       help='Path to the data file to visualize (default: data/run1/out1.txt)')
    parser.add_argument('--augmented', '-a', action='store_true',
                       help='Enable augmented data mode')
    parser.add_argument('--inspect', '-i', action='store_true',
                       help='Start in inspection mode')
    parser.add_argument('--monolithic', '-m', action='store_true',
                       help='Run the monolithic version instead of modular (default)')
    
    args = parser.parse_args()
    
    try:
        if args.monolithic:
            # Run the monolithic version
            print("Starting monolithic visualizer...")
            from visualizer.visualizer import run_monolithic_visualizer
            
            # Create config for monolithic version
            config = {
                'data_file': args.data_file or 'data/run1/out1.txt',
                'augmented_mode': args.augmented,
                'inspection_mode': args.inspect
            }
            
            run_monolithic_visualizer(config)
            
        else:
            # Run modular version (default)
            print("Starting modular visualizer...")
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
