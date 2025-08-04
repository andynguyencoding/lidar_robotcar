# LiDAR Visualizer Logging System

## Overview

The LiDAR Visualizer now includes a comprehensive logging system that provides configurable logging levels and both console and file output. This system helps with debugging, monitoring application behavior, and tracking user interactions.

## Features

### Logging Levels
- **DEBUG**: Detailed information for diagnosing problems (most verbose)
- **INFO**: General information about application operation (default level)
- **WARNING**: Warning messages about potential issues
- **ERROR**: Error messages for serious problems
- **CRITICAL**: Critical errors that may cause application failure

### Output Options
- **Console Output**: Real-time logging to the terminal/console
- **File Output**: Persistent logging to rotating log files in the `logs/` directory
- **Dual Output**: Both console and file logging simultaneously

### Specialized Logging Methods
- **Navigation Events**: Track frame navigation and dataset switching
- **UI Events**: Monitor user interface interactions
- **Data Operations**: Log data loading, saving, and processing
- **Performance Metrics**: Track timing and performance data
- **Function Tracing**: Automatic entry/exit logging with decorators

## Configuration

### Default Settings
- **Log Level**: INFO (set in `config.py`)
- **Console Logging**: Enabled
- **File Logging**: Enabled (logs stored in `logs/visualizer.log`)
- **Log Rotation**: 10MB max file size, 5 backup files

### Changing Log Level
1. **Via Menu**: Settings → Logging → Set Level...
2. **Via Code**: `set_log_level("DEBUG")`
3. **Via Config**: Edit `LOG_LEVEL` in `config.py`

## Usage Examples

### Basic Logging
```python
from logger import info, debug, warning, error, critical

info("Application started", "Main")
debug("Processing frame data", "DataManager")
warning("File not found, using default", "FileManager")
error("Failed to load data", "DataLoader")
critical("System out of memory", "Main")
```

### Module-Specific Logging
```python
from logger import get_logger

logger = get_logger()
logger.info("Message with module context", "MyModule")
```

### Specialized Logging
```python
from logger import log_navigation, log_ui_event, log_dataset_operation

# Log navigation events
log_navigation("next", from_frame=5, to_frame=6, dataset_type="train")

# Log UI interactions
log_ui_event("Button clicked", "Next frame button")

# Log data operations
log_dataset_operation("split", "main", "70/20/10 ratio")
```

### Function Tracing
```python
from logger import log_function

@log_function("DataManager")
def load_data_file(filename):
    # Function automatically logs entry and exit
    return data
```

### Exception Logging
```python
from logger import log_exception

try:
    risky_operation()
except Exception as e:
    log_exception("Operation failed", module="MyModule")
```

## File Locations

### Log Files
- **Primary Log**: `logs/visualizer.log`
- **Backup Logs**: `logs/visualizer.log.1` through `logs/visualizer.log.5`
- **Log Directory**: Automatically created in the application root

### Configuration
- **Logger Module**: `logger.py`
- **Configuration**: `config.py` (LOG_LEVEL, LOG_TO_FILE, LOG_TO_CONSOLE)

## Integration Points

### Core Modules
The logging system is integrated into:
- **visualizer.py**: Main application startup/shutdown
- **visualizer_core.py**: Core application logic and UI events
- **pginput.py**: Data management and navigation
- **ui_components.py**: User interface interactions
- **kbest_analysis.py**: Analysis operations

### Menu Integration
- **Settings → Logging → Set Level**: Configure logging level
- **Settings → Logging → View Logs**: View log file contents

## Log Format

### Console Format
```
HH:MM:SS - LiDARVisualizer - LEVEL - [Module] Message
```

### File Format
```
YYYY-MM-DD HH:MM:SS - LiDARVisualizer - LEVEL - module:line - [Module] Message
```

## Examples of Logged Events

### Application Lifecycle
```
10:30:15 - LiDARVisualizer - INFO - [Main] LiDAR Visualizer starting up
10:30:16 - LiDARVisualizer - INFO - [DataManager] Initializing DataManager with input file: data.txt
10:30:16 - LiDARVisualizer - INFO - [DataManager] Loaded 1000 lines from data file
```

### Navigation Events
```
10:31:20 - LiDARVisualizer - DEBUG - [DataManager] Navigation: next from frame 5 to 6
10:31:25 - LiDARVisualizer - INFO - [Navigation] Navigation: next from frame 5 to 6 in train dataset
```

### Data Operations  
```
10:32:10 - LiDARVisualizer - INFO - [Dataset] Dataset operation: split on main dataset - 70/20/10 ratio
10:32:15 - LiDARVisualizer - INFO - [DataLoader] Data file loaded successfully: sample_data.txt
```

### Error Handling
```
10:33:00 - LiDARVisualizer - ERROR - [UI] Error opening logging config dialog: Permission denied
10:33:05 - LiDARVisualizer - WARNING - [FileManager] Could not setup file logging: Permission denied
```

## Benefits

### For Development
- **Debugging**: Detailed trace of application behavior
- **Performance**: Track slow operations and bottlenecks
- **Error Tracking**: Comprehensive error logging with stack traces

### For Users
- **Troubleshooting**: Clear error messages and guidance
- **Activity Monitoring**: Track data processing and analysis
- **Configuration**: Adjustable verbosity levels

### For Maintenance
- **Log Rotation**: Prevents disk space issues
- **Structured Format**: Easy parsing and analysis
- **Module Context**: Clear identification of error sources

## Best Practices

### When to Use Each Level
- **DEBUG**: Detailed function tracing, variable values
- **INFO**: User actions, data operations, status changes  
- **WARNING**: Recoverable errors, fallback actions
- **ERROR**: Operation failures, invalid inputs
- **CRITICAL**: System failures, crash conditions

### Module Naming
- Use descriptive module names: "DataManager", "UI", "Navigation"
- Be consistent across related functionality
- Keep names short but meaningful

### Message Format
- Start with action or context: "Loading data file", "Navigation failed"
- Include relevant details: file names, frame numbers, error codes
- Keep messages concise but informative

## Troubleshooting

### Common Issues
1. **No log file created**: Check permissions in application directory
2. **Log level not changing**: Restart application or check config.py
3. **Console output missing**: Check LOG_TO_CONSOLE setting
4. **File logging disabled**: Check LOG_TO_FILE setting and disk space

### Performance Considerations
- DEBUG level can be verbose - use INFO for production
- Log file rotation prevents unlimited growth
- Console logging may slow down in high-volume scenarios
