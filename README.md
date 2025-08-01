# lidar_robotcar

## Introduction
Using Lidar with Machine Learning to build a self-driving car solution. This project combines RPLidar sensor data with machine learning algorithms to create an autonomous vehicle that can navigate using 360-degree lidar readings.

## Software Versions

This project includes two versions of the visualization software:

### 🔹 **Modular Version** (Recommended)
- **Entry Point**: `python main.py`
- **Architecture**: Clean, modular design with separate components
- **Files**: `main.py`, `visualizer_core.py`, `ui_components.py`, `frame_navigation.py`, etc.
- **Benefits**: 
  - Better maintainability and code organization
  - Easier to extend and modify
  - Follows modern software engineering practices
  - Faster startup and better performance

### 🔸 **Monolithic Version** (Legacy)
- **Entry Point**: `python visualizer.py`
- **Architecture**: Single-file implementation with all functionality
- **Files**: `visualizer.py` (3,300+ lines)
- **Benefits**:
  - Self-contained in one file
  - Good for understanding the complete system
  - Useful for debugging and learning

Both versions provide **identical functionality** including:
- Interactive LiDAR data visualization
- Frame-by-frame inspection mode
- Data statistics with histogram analysis
- Data imputation and augmentation tools
- AI model integration and predictions
- Help menu with About dialog (Version 0.1, Author: Hoang Giang Nguyen)

**Recommendation**: Use the modular version (`python main.py`) for regular use and development work.

## Quick Start

1. **Run the recommended modular version:**
   ```bash
   python main.py
   ```

2. **Or run the legacy monolithic version:**
   ```bash
   python visualizer.py
   ```

3. **Access Help and About information:**
   - Click **Help > About...** in the menu bar
   - Shows version 0.1, author information, and contact details

## Project Overview
- **Data Collection**: Manual driving to gather lidar readings and steering commands
- **Data Visualization**: Interactive GUI visualizer for analyzing and cleaning data
- **Data Processing**: Advanced imputation and augmentation tools with GUI interface
- **Data Augmentation**: Horizontal mirroring and append/replace options to enhance datasets
- **Machine Learning**: Random Forest Regressor for steering prediction
- **Autonomous Mode**: Real-time lidar-based navigation

## Project Structure

```
lidar_robotcar/
├── 📁 Core Application Files
│   ├── main.py                 # Modular version entry point
│   ├── visualizer_core.py      # Modular main controller
│   ├── ui_components.py        # UI management
│   ├── frame_navigation.py     # Frame navigation logic
│   ├── visualization_renderer.py # Pygame rendering
│   ├── visualizer.py          # Monolithic version (legacy)
│   ├── ai_model.py            # AI model integration
│   └── pginput.py             # Data management
├── 📁 test/                   # Test scripts and utilities
├── 📁 docs/                   # Documentation and manuals
│   └── development/           # Development documentation
├── 📁 data/                   # LiDAR data files
├── 📁 models/                 # Trained ML models (.pkl files)
└── 📁 notebooks/              # Jupyter notebooks for training
```

## Electronics components
The documentation is in docs folder. All the electronics parts are listed here.

## Steps to train ML model

### 1. Data Collection
After assembling the car, put it into data collection mode and drive it manually to gather training data. Press button "A" on your joystick (button may vary by model) to stop data collection. The collected data will be saved as CSV files with lidar readings and corresponding steering commands.

### 2. Data Visualization and Processing

## Using the GUI Visualizer

Both versions of the visualizer provide comprehensive interactive GUI for viewing, analyzing, and processing lidar data with extensive configuration and processing options.

### Starting the Visualizer

**Modular Version (Recommended):**
```bash
python main.py
```

**Monolithic Version (Legacy):**
```bash
python visualizer.py
```

**GUI Configuration Window:**
Both versions open a configuration window where you can:
- Choose data source (local data or browse for custom file)
- Enable inspection mode for frame-by-frame analysis
- Toggle augmented data display (mirrored data for training)
- Enable data concatenation to double your dataset

**Command Line with File Argument (Monolithic version only):**
```bash
py visualizer.py /path/to/your/datafile.csv
```
This opens the configuration window with the specified file pre-selected and data source options grayed out.

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

- **Black dots**: Regular lidar data points
- **Red dots with magenta lines**: Important feature points used by the ML model
- **Orange circle**: The car/robot position (center)
- **Blue line**: Car's forward direction
- **Green line**: Steering direction based on turn data
- **Red line**: Previous frame's steering direction (for comparison)
- **Orange line**: AI model prediction direction (when model is loaded)
- **Frame Info**: Current frame number, total frames, and data mode (REAL/AUGMENTED)
- **Input Fields**: Editable angular and linear velocity values with real-time updates
- **Previous Angular Vel**: Previous frame's angular velocity (readonly, for comparison)
- **Pred Angular Vel**: AI model's predicted angular velocity (readonly, shows "--" when no model loaded)

### Data Processing Workflow

1. **Load Data**: Use the GUI to select your data file
2. **Analyze Quality**: Open Data Statistics (Ctrl+I) to assess data quality
3. **Clean Data**: Use "Impute Invalid Data" to fill missing values
4. **Augment Dataset**: Use "Augment Data" to create mirrored versions for better ML training
5. **Inspect Results**: Use inspection mode to verify processing results frame-by-frame
6. **Save Processed Data**: Use the save function with header preservation options

### Data Format

Both visualizer versions support CSV/TXT files with:
- 360 columns of lidar distance data (one per degree, 0-359)
- 1 additional column for turn/steering value (column 360)
- Optional header row (automatically detected and preserved)
- Values can be numeric distances, 'inf', 'nan', or '0' for invalid readings
- Angular velocity values can be positive (right turn) or negative (left turn)

### Version Compatibility

Both versions provide identical functionality and data compatibility:
- Same file formats supported (CSV/TXT)
- Same keyboard shortcuts and menu options
- Same data processing capabilities
- Same AI model integration
- Identical visualization and analysis features

### Troubleshooting

**GUI Issues:**
- **Configuration window doesn't appear**: The program will fall back to console-based configuration
- **Buttons not responding**: Ensure you're in the correct mode (continuous vs inspection)
- **Statistics window not opening**: Try using Ctrl+I or the Data menu option

**Data Issues:**
- **File not found errors**: Ensure your data file path is correct and accessible
- **Invalid data warnings**: Use the "Impute Invalid Data" function to clean your dataset
- **Header issues**: Use the "Preserve header" checkbox in the statistics window

**Display Issues:**
- **Visualization not updating**: Check that your system supports pygame and tkinter
- **Performance issues**: Large datasets may require more processing time for statistics

### Advanced Tips

- **Data Quality**: Always check the statistics window before training ML models
- **Processing Order**: Apply imputation before augmentation for best results  
- **Navigation**: Use inspection mode for detailed frame-by-frame analysis
- **Batch Processing**: Process multiple operations sequentially (impute → augment → save)
- **Backup**: Always save processed data with descriptive filenames (_imputed, _augmented, etc.)

### 3. Model Training
After visualizing and cleaning your data, proceed with training the machine learning model using Random Forest Regressor from Scikit-Learn. This is accomplished using the Jupyter notebooks in the `notebooks/` folder:

- `randomforest_regression.ipynb`: Main training notebook
- `randomforest_regression-asis.ipynb`: Alternative training approach

The trained model will be saved as a `.pkl` file for use in autonomous driving mode.

Then go ahead with training the model using Random Forest Regressor from Scikit-Learn. This is done using the Jupyter notebook in the notebooks folder.

## References
Murtaza, Youtube How to run robot motors: https://youtu.be/0lXY87NwVIc?si=XjZ9y-pofpmrJ3lj <br />
Murtaza, Youtube How to run joystick with Raspberry Pi: https://youtu.be/TMBfiS7LNnU?si=BKFeUhWR-5dlGu2r <br />
Github, The origin Python library used with RP Lidar - Robotica/RPLidar: https://github.com/Roboticia/RPLidar <br />
Nikodem Bartik visualizer Python program: https://www.youtube.com/watch?v=PdSDhdciSpE&t=1s
