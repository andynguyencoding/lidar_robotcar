# Test Scripts Directory

This directory contains test scripts and utilities for the LiDAR Robotcar project.

## Test Categories

### Core Application Tests
- `test_modular_refactoring.py` - Tests for the modular architecture refactoring
- `test_data_loading.py` - Data loading and management tests
- `test_dialogs.py` - UI dialog tests
- `test_scale_factor.py` - Scale factor calculation tests

### UI and Visualization Tests
- `test_frame_input.py` - Frame input field functionality tests
- `test_modular_frame_input_fix.py` - Modular version frame input tests
- `test_visualization_fixes.py` - Pygame visualization tests
- `test_velocity_toggles.py` - Velocity display toggle tests
- `test_toggle_callbacks.py` - UI callback tests

### AI Model Tests
- `test_ai.py` - AI model integration tests
- `test_ai_browse_default.py` - AI model browsing tests
- `test_pred_field.py` - AI prediction field tests

## Running Tests

To run individual test scripts:
```bash
python test_<script_name>.py
```

To run all tests in the directory:
```bash
python -m pytest test/
```

## Test Development Guidelines

When adding new test scripts:
1. Follow the naming convention: `test_<feature_name>.py`
2. Include clear docstrings explaining what the test covers
3. Use descriptive test function names
4. Include both positive and negative test cases where applicable
5. Mock external dependencies (hardware, AI models) when necessary

## Dependencies

Most tests require the main application modules:
- `visualizer_core.py`
- `pginput.py`
- `ai_model.py`
- Other core modules as needed

Some tests may require additional testing libraries:
- `pytest` for advanced testing features
- `unittest.mock` for mocking external dependencies

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
