# LiDAR Visualizer Project

This project has been organized with all visualization components moved to the `visualizer/` subfolder for better code organization.

## Project Structure

```
lidar_robotcar/
├── config.py                    # Global configuration
├── logger.py                    # Logging system
├── startup_config.py            # Startup configuration utilities
├── test_logging.py              # Logging tests
├── run_visualizer.py            # Main launcher script
├── visualizer/                  # Visualization package
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # Modular visualizer entry point
│   ├── visualizer.py            # Monolithic visualizer
│   ├── visualizer_core.py       # Core application controller
│   ├── ui_components.py         # UI components and menus
│   ├── visualization_renderer.py # Pygame rendering
│   ├── frame_navigation.py      # Frame navigation logic
│   ├── pginput.py               # Data management and pygame input
│   ├── file_manager.py          # File operations
│   ├── undo_system.py           # Undo/redo functionality
│   ├── data_statistics.py       # Data analysis tools
│   ├── ai_model.py              # AI model integration
│   ├── kbest_analysis.py        # K-best feature analysis
│   └── visualizer_recent_files.txt # Recent files cache
├── data/                        # Data files
├── models/                      # AI model files
├── logs/                        # Log files
├── docs/                        # Documentation
├── notebooks/                   # Jupyter notebooks
└── test/                        # Test files
```

## Running the Visualizer

### Option 1: Using the Launcher (Recommended)
```bash
# Run with default settings
python run_visualizer.py

# Run with command line options
python run_visualizer.py --data-file data/run1/out1.txt --inspect

# Run monolithic version
python run_visualizer.py --monolithic

# Show configuration dialog
python run_visualizer.py --config
```

### Option 2: Direct Module Execution
```bash
# Run modular version directly
python -m visualizer.main --data-file data/run1/out1.txt

# Run monolithic version directly
python visualizer/visualizer.py
```

### Option 3: Python API
```python
# Using the modular version
from visualizer import run
run(data_file='data/run1/out1.txt', inspection_mode=True)

# Using the monolithic version
from visualizer.visualizer import run_monolithic_visualizer
config = {
    'data_file': 'data/run1/out1.txt',
    'inspection_mode': True,
    'augmented_mode': False
}
run_monolithic_visualizer(config)
```

## Command Line Options

- `--data-file`, `-f`: Path to data file to visualize
- `--augmented`, `-a`: Enable augmented data mode
- `--inspect`, `-i`: Start in inspection mode
- `--monolithic`, `-m`: Use monolithic version
- `--config`, `-c`: Show startup configuration dialog

## Features

- **Dual Architecture**: Both monolithic and modular versions available
- **Interactive Visualization**: Real-time LiDAR data visualization with pygame
- **Data Management**: Load, save, and manipulate LiDAR datasets
- **AI Integration**: Load and use AI models for predictions
- **K-Best Analysis**: Feature selection and analysis tools
- **Comprehensive Logging**: Multi-level logging with file rotation
- **Data Statistics**: Advanced data analysis and statistics
- **Undo System**: Full undo/redo support for data modifications
- **Recent Files**: Quick access to recently used files

## Dependencies

- pygame
- tkinter
- numpy
- matplotlib
- scikit-learn (for K-best analysis)
- pandas (for data statistics)

## Getting Started

1. Install dependencies: `pip install -r requirements.txt` (if available)
2. Run the visualizer: `python run_visualizer.py`
3. Load a data file from the `data/` directory
4. Use the interface to visualize and analyze your LiDAR data

For more detailed documentation, see the `docs/` directory.
