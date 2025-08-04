# LiDAR Visualizer Project

This project provides a modular LiDAR data visualization system organized in the `visualizer/` package.

## Project Structure

```
lidar_robotcar/
├── run_visualizer.py            # Main launcher script
├── visualizer/                  # Visualization package
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # Main entry point
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
│   ├── config.py                # Configuration management
│   ├── logger.py                # Logging utilities
│   └── visualizer_recent_files.txt # Recent files cache
├── test/                        # Test files
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
python run_visualizer.py --data-file data/run1/out1.txt --inspect --augmented
```

### Option 2: Direct Module Execution
```bash
# Run directly through Python module
python -m visualizer.main --data-file data/run1/out1.txt
```

### Option 3: Python API
```python
# Using the visualizer package
from visualizer import run
run(data_file='data/run1/out1.txt', inspection_mode=True, show_augmented=True)
```

## Command Line Options

- `--data-file`, `-f`: Path to data file to visualize
- `--augmented`, `-a`: Enable augmented data mode
- `--inspect`, `-i`: Start in inspection mode

## Key Features

### Interactive Visualization
- **360-degree LiDAR View**: Real-time visualization of lidar sensor data
- **Frame Navigation**: Frame-by-frame inspection with navigation controls
- **Dynamic Display**: Toggle between continuous playback and inspection modes
- **Visual Indicators**: Color-coded data points and directional lines

### Data Processing Tools
- **Data Imputation**: Fill missing or invalid lidar readings
- **Data Augmentation**: Create mirrored datasets for enhanced training
- **Statistics Analysis**: Comprehensive data quality analysis with histograms
- **Export Functionality**: Save processed data in various formats

### AI Integration
- **Model Loading**: Load pre-trained ML models (.pkl files)
- **Real-time Predictions**: Display AI predictions alongside actual data
- **Model Comparison**: Compare predictions with ground truth data

## Detailed Usage Guide

### Starting the Visualizer

#### Command Line Options
```bash
# Basic usage
python run_visualizer.py

# Specify a data file
python run_visualizer.py --data-file /path/to/your/datafile.csv

# Enable inspection mode for frame-by-frame analysis
python run_visualizer.py --inspect

# Enable augmented data display (mirrored data for training)
python run_visualizer.py --augmented

# Combine options
python run_visualizer.py --data-file data/custom.txt --inspect --augmented
```

### Configuration Options

#### Data Source
- **Local data**: Uses `data/run1/out1.txt` (default test data)
- **Browse for file**: Click "Browse..." to select any CSV or TXT file from your system

#### Visualization Modes
- **Continuous Mode**: Real-time playback with play/pause controls
- **Inspection Mode**: Frame-by-frame viewing with navigation controls for detailed analysis
- **Show Augmented Data**: Toggle between real and mirrored lidar data display

#### Data Processing
- **Concatenate augmented data**: Automatically appends mirrored data to your input file, doubling the dataset size

### Advanced GUI Features

#### Main Visualizer Window
- **Dynamic Mode Switching**: Switch between Continuous and Inspection modes during runtime
- **Navigation Controls**: In inspection mode, use First/Prev/Next/Last buttons for precise frame control
- **Real-time Input**: Modify angular velocity values and see changes immediately
- **Status Display**: Current frame information, mode indicators, and data type display

#### Data Statistics Window (Ctrl+I)
Access comprehensive data analysis and processing tools:

**Data Quality Analysis:**
- Total frames count and validity statistics
- Invalid data points detection and percentage
- Angular velocity distribution histogram
- Real-time statistics updates after processing

**Data Processing Tools:**
- **Impute Invalid Data**: Automatically fill missing or invalid lidar readings using adjacent value interpolation
- **Augment Data**: Create mirrored versions of your dataset with two options:
  - **Append**: Add augmented data to existing data (doubles dataset size)
  - **Replace**: Replace original data with augmented versions
- **Sequential Processing**: Apply multiple operations (e.g., impute then augment) that build on each other
- **Preserve Header Option**: Checkbox to control whether file headers are saved with processed data

**Save Functionality:**
- **Smart Save**: Save any combination of processed data (imputed, augmented, or both)
- **Format Preservation**: Maintains original file format and structure
- **Header Control**: User-controlled header preservation during save operations

### Interactive Controls

#### Keyboard Shortcuts
- **SPACE**: Play/pause (continuous mode) or advance frame (inspection mode)
- **I**: Toggle between continuous and inspection modes
- **A**: Toggle between real and augmented data display
- **Q**: Quit the visualizer
- **←/→ Arrow Keys**: Navigate previous/next frame (inspection mode only)
- **Home/End**: Jump to first/last frame (inspection mode only)
- **Ctrl+I**: Open data statistics window
- **Ctrl+S**: Save current data modifications
- **Ctrl+O**: Browse for new data file

#### Mouse Controls
- **Button Interface**: Full mouse support for all navigation and processing functions
- **Input Fields**: Click and type to modify angular velocity values
- **Menu System**: Access all features through organized menu system

#### AI Menu Features
- **Browse Model...**: Load a pre-trained machine learning model (.pkl files) for prediction
- **Model Info...**: Display detailed information about the currently loaded model
- **Clear Model**: Unload the current AI model to stop predictions
- **Real-time Predictions**: When a model is loaded, predictions are displayed as:
  - Orange direction line in the visualization
  - Predicted angular velocity value in the "Pred Angular Vel" input field

#### Velocity Visualization Toggles
- **Cur Vel**: Toggle display of current frame angular velocity (green line)
- **Prev Vel**: Toggle display of previous frame angular velocity (red line)
- **Pred Vel**: Toggle display of AI model prediction (orange line)
- **Fwd Dir**: Toggle display of forward direction (blue line)
- **Real-time Updates**: Checkboxes immediately update the visualization when toggled
- All toggles are enabled by default; uncheck to hide specific velocity visualizations
- AI prediction text field continues to update even when visualization is disabled
- Perfect for comparing different velocity indicators or reducing visual clutter

### Understanding the Display

#### Visual Elements
- **Black dots**: Regular lidar data points
- **Red dots with magenta lines**: Important feature points used by the ML model
- **Orange circle**: The car/robot position (center)
- **Blue line**: Car's forward direction
- **Green line**: Steering direction based on turn data
- **Red line**: Previous frame's steering direction (for comparison)
- **Orange line**: AI model prediction direction (when model is loaded)

#### Information Display
- **Frame Info**: Current frame number, total frames, and data mode (REAL/AUGMENTED)
- **Input Fields**: Editable angular and linear velocity values with real-time updates
- **Previous Angular Vel**: Previous frame's angular velocity (readonly, for comparison)
- **Status Indicators**: Mode display, data type, and processing status

## Tips for Best Results

### Data Processing Workflow
- **Processing Order**: Apply imputation before augmentation for best results  
- **Navigation**: Use inspection mode for detailed frame-by-frame analysis
- **Batch Processing**: Process multiple operations sequentially (impute → augment → save)
- **Backup**: Always save processed data with descriptive filenames (_imputed, _augmented, etc.)

### Performance Optimization
- **File Size**: Large datasets may take time to load - use progress indicators
- **Memory Usage**: Close statistics windows when not needed to free memory
- **Visualization**: Disable unnecessary velocity indicators to improve rendering speed

### Troubleshooting
- **Import Errors**: Ensure you're running from the project root directory
- **File Access**: Check file permissions if save operations fail
- **Performance**: Reduce visualization elements if experiencing lag

## Dependencies

### Required Python Libraries
```bash
pip install pygame tkinter numpy matplotlib scikit-learn pandas
```

### Hardware Libraries (for robot operation)
- RPLidar Python library for sensor communication
- GPIO libraries for Raspberry Pi hardware control

## Getting Started

1. **Install dependencies**: `pip install -r requirements.txt` (if available)
2. **Run the visualizer**: `python run_visualizer.py`
3. **Load a data file**: Use default data or browse for your own CSV/TXT files
4. **Explore features**: Use the interface to visualize and analyze your LiDAR data

## Additional Resources

- **Main Documentation**: See [README.md](README.md) for project overview
- **Development Docs**: Check `docs/development/` for technical details
- **Test Files**: Use files in `test/` directory for validation
- **Example Data**: Sample datasets available in `data/` directory

For technical support, please open an issue in the repository.
