# lidar_robotcar

## Introduction
Using Lidar with Machine Learning to build a self-driving car solution. This project combines RPLidar sensor data with machine learning algorithms to create an autonomous vehicle that can navigate using 360-degree lidar readings.

## Project Overview
- **Data Collection**: Manual driving to gather lidar readings and steering commands
- **Data Visualization**: Interactive visualizer for analyzing and cleaning data
- **Data Augmentation**: Horizontal mirroring to increase dataset size
- **Machine Learning**: Random Forest Regressor for steering prediction
- **Autonomous Mode**: Real-time lidar-based navigation

## Electronics components
The documentation is in docs folder. All the electronics parts are listed here.

## Steps to train ML model

### 1. Data Collection
After assembling the car, put it into data collection mode and drive it manually to gather training data. Press button "A" on your joystick (button may vary by model) to stop data collection. The collected data will be saved as CSV files with lidar readings and corresponding steering commands.

### 2. Data Visualization and Cleaning

## Using the Visualizer

The visualizer.py program provides an interactive way to view and analyze lidar data with multiple configuration options.

### Starting the Visualizer

**Method 1: GUI Configuration Window (Recommended)**
```bash
python3 visualizer.py
```
This opens a configuration window where you can:
- Choose data source (local data or browse for custom file)
- Enable inspection mode for frame-by-frame analysis
- Toggle augmented data display (mirrored data for training)
- Enable data concatenation to double your dataset

**Method 2: Command Line with File Argument**
```bash
python3 visualizer.py /path/to/your/datafile.csv
```
This opens the configuration window with the specified file pre-selected and data source options grayed out.

### Configuration Options

#### Data Source
- **Local data**: Uses `data/run1/out1.txt` (default test data)
- **Browse for file**: Click "Browse..." to select any CSV or TXT file from your system

#### Visualization Modes
- **Inspection Mode**: Frame-by-frame viewing - pauses at each data point for detailed analysis
- **Show Augmented Data**: Displays horizontally mirrored lidar data (useful for data augmentation)

#### Data Processing
- **Concatenate augmented data**: Automatically appends mirrored data to your input file, doubling the dataset size

### Interactive Controls (During Visualization)

Once the visualizer is running, use these keyboard shortcuts:

- **SPACE**: Pause/resume playback
- **I**: Toggle inspection mode (frame-by-frame vs continuous)
- **A**: Toggle between real and augmented (mirrored) data display
- **Q**: Quit the visualizer

### Understanding the Display

- **Black dots**: Regular lidar data points
- **Red dots with magenta lines**: Important feature points used by the ML model
- **Orange circle**: The car/robot position (center)
- **Blue line**: Car's forward direction
- **Green line**: Steering direction based on turn data
- **Bottom text**: Shows current line number, turn value, and data mode (REAL/AUGMENTED)

### Data Format

The visualizer expects CSV/TXT files with:
- 360 columns of lidar distance data (one per degree)
- 1 additional column for turn/steering value
- Values can be numeric distances or 'inf' for invalid readings

### Troubleshooting

- **Configuration window doesn't appear**: The program will fall back to console-based configuration
- **File not found errors**: Ensure your data file path is correct and accessible
- **Display issues**: Check that your system supports pygame and has proper display drivers

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
