# lidar_robotcar

## Introduction
Using Lidar with Machine Learning to build a self-driving car solution. This project combines RPLidar sensor data with machine learning algorithms to create an autonomous vehicle that can navigate using 360-degree lidar readings.

## Software Overview

This project features a **modular visualizer package** designed for interactive LiDAR data analysis and processing:

- **Architecture**: Clean, modular design with separate components
- **Entry Point**: `python run_visualizer.py`
- **Benefits**: 
  - Better maintainability and code organization
  - Easier to extend and modify
  - Follows modern software engineering practices
  - Faster startup and better performance

**Key Features:**
- Interactive LiDAR data visualization with 360-degree view
- Frame-by-frame inspection mode for detailed analysis
- Data statistics with histogram analysis
- Data imputation and augmentation tools
- AI model integration and predictions
- Help menu with About dialog (Version 0.1, Author: Hoang Giang Nguyen)

## Quick Start

### Running the Visualizer
```bash
python run_visualizer.py
```

For detailed visualizer usage instructions, see [VISUALIZER_README.md](VISUALIZER_README.md).

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
├── 📁 visualizer/              # Modular visualizer package
│   ├── main.py                # Entry point
│   ├── visualizer_core.py     # Main controller
│   ├── ui_components.py       # UI management
│   ├── frame_navigation.py    # Frame navigation logic
│   ├── visualization_renderer.py # Pygame rendering
│   ├── ai_model.py           # AI model integration
│   ├── config.py             # Configuration management
│   └── logger.py             # Logging utilities
├── run_visualizer.py          # Unified launcher
├── 📁 test/                   # Test scripts and utilities
├── 📁 docs/                   # Documentation and manuals
│   └── development/           # Development documentation
├── 📁 data/                   # LiDAR data files
├── 📁 models/                 # Trained ML models (.pkl files)
└── 📁 notebooks/              # Jupyter notebooks for training
```

## Electronics Components
The documentation is in docs folder. All the electronics parts are listed here.

## Machine Learning Workflow

### 1. Data Collection
After assembling the car, put it into data collection mode and drive it manually to gather training data. Press button "A" on your joystick (button may vary by model) to stop data collection. The collected data will be saved as CSV files with lidar readings and corresponding steering commands.

### 2. Data Visualization and Processing

Use the interactive GUI visualizer to analyze and process your LiDAR data:

```bash
python run_visualizer.py
```

**Key Features:**
- Interactive LiDAR data visualization with 360-degree view
- Frame-by-frame inspection mode for detailed analysis
- Data statistics and histogram analysis
- Data imputation tools for handling invalid readings
- Data augmentation with horizontal mirroring
- AI model integration for real-time predictions
- Export processed data for training

For complete visualizer documentation, see [VISUALIZER_README.md](VISUALIZER_README.md).

### 3. Model Training
After visualizing and cleaning your data, proceed with training the machine learning model using Random Forest Regressor from Scikit-Learn. This is accomplished using the Jupyter notebooks in the `notebooks/` folder:

- `randomforest_regression.ipynb`: Main training notebook
- `randomforest_regression-asis.ipynb`: Alternative training approach

### 4. Autonomous Operation
Deploy the trained model with the hardware to enable autonomous navigation. The car will use real-time lidar data to make steering decisions based on the trained model.

## Hardware Components

### Essential Parts
- Raspberry Pi 4B (4GB RAM recommended)
- RPLidar A1 or A2 sensor
- Motor controller (L298N or similar)
- DC motors with wheels
- Chassis/frame
- Battery pack
- Jumper wires and breadboard

### Optional Components
- Camera module (for future computer vision integration)
- IMU sensor (for enhanced navigation)
- Ultrasonic sensors (for backup collision detection)
- LED indicators (for status display)

## Software Dependencies

### Python Libraries
```bash
pip install pygame tkinter numpy matplotlib scikit-learn pandas
```

### Hardware Libraries
- RPLidar Python library for sensor communication
- GPIO libraries for Raspberry Pi hardware control

## Development

This project has evolved from a monolithic architecture to a clean, modular design. See the `docs/development/` folder for detailed development history, architectural decisions, and troubleshooting guides.

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with the visualizer
5. Submit a pull request

### Testing
Run the test suite:
```bash
python -m pytest test/
```

## License
This project is open source. Please refer to the license file for more details.

## Author
**Hoang Giang Nguyen**  
Version 0.1

For technical support and questions, please open an issue in the repository.
