# Test Scripts

This folder contains test scripts for the LiDAR Robot Car project.

## Test Files

- **test_ai.py** - Tests the AI model integration functionality
- **test_ai_browse_default.py** - Tests the AI model browsing with default directory functionality
- **test_pred_field.py** - Tests the prediction field display functionality
- **test_toggle_callbacks.py** - Tests the toggle callback functionality for UI elements
- **test_velocity_toggles.py** - Tests the velocity visualization toggle controls

## Running Tests

To run any test script, navigate to the project root directory and execute:

```bash
cd /home/andy/mysource/github/lidar_robotcar
python test/<test_script_name>.py
```

For example:
```bash
python test/test_ai.py
python test/test_velocity_toggles.py
```

## Test Dependencies

These test scripts require the same dependencies as the main application:
- tkinter (for GUI testing)
- pygame (for visualization testing) 
- numpy, pandas, scikit-learn (for AI model testing)

Most tests are verification scripts that validate specific functionality and provide status reports rather than automated unit tests.
