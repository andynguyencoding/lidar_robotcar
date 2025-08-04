"""
LiDAR Visualizer Package

This package contains the complete LiDAR data visualization system including:
- Modular visualizer components (visualizer_core.py, ui_components.py, etc.)
- Data management and statistics
- AI model integration
- K-best analysis tools
- File management and undo system
"""

# Main entry points
from .main import run
from .visualizer_core import VisualizerWindow

# Core components
from .pginput import DataManager, InputBox
from .ui_components import UIManager
from .frame_navigation import FrameNavigator
from .file_manager import FileManager
from .undo_system import UndoSystem
from .data_statistics import DataAnalyzer
from .visualization_renderer import VisualizationRenderer
from .ai_model import load_ai_model, get_ai_prediction, is_ai_model_loaded
from .kbest_analysis import show_kbest_analysis_dialog

__version__ = "1.0.0"
__author__ = "Hoang Giang Nguyen"
__email__ = "hoang.g.nguyen@student.uts.edu.au"
