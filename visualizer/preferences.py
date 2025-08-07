"""
Preferences management for the LiDAR Visualizer
Handles saving and loading user preferences to/from file
"""

import os
import json
from typing import Dict, Any, Optional
from .logger import info, warning, error


class PreferencesManager:
    """Manages user preferences persistence"""
    
    def __init__(self, preferences_file: str = "visualizer_preferences.json"):
        """
        Initialize preferences manager
        
        Args:
            preferences_file: Path to preferences file (relative to project root)
        """
        # Get the project root directory (parent of visualizer folder)
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.preferences_file = os.path.join(self.project_root, preferences_file)
        
        # Default preferences structure
        self.default_preferences = {
            "visual": {
                "scale_factor": 0.25,
                "direction_ratio_max_degree": 45.0,
                "direction_ratio_max_angular": 1.0
            },
            "data": {
                "augmentation_unit": "m",
                "split_ratios": [70, 20, 10]  # Train, Validation, Test percentages
            },
            "export": {
                "file_prefix": "lidar_dataset",
                "timestamp_format": "%Y%m%d_%H%M%S"
            },
            "ui": {
                "window_width": 850,
                "window_height": 750,
                "canvas_size": 680
            },
            "logging": {
                "log_level": "INFO",
                "log_to_file": True,
                "log_to_console": True
            },
            "session": {
                "last_opened_file": None,  # Path to the last opened file
                "remember_last_file": True  # Whether to auto-open last file
            }
        }
        
        self.preferences = self.default_preferences.copy()
    
    def load_preferences(self) -> Dict[str, Any]:
        """
        Load preferences from file
        
        Returns:
            dict: Loaded preferences (defaults if file doesn't exist or is invalid)
        """
        try:
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    loaded_prefs = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                self.preferences = self._merge_preferences(self.default_preferences, loaded_prefs)
                
                info(f"Preferences loaded from: {self.preferences_file}", "Preferences")
                return self.preferences
            else:
                info("No preferences file found, using defaults", "Preferences")
                self.preferences = self.default_preferences.copy()
                return self.preferences
                
        except (json.JSONDecodeError, IOError) as e:
            warning(f"Failed to load preferences: {e}. Using defaults.", "Preferences")
            self.preferences = self.default_preferences.copy()
            return self.preferences
    
    def save_preferences(self, preferences: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save preferences to file
        
        Args:
            preferences: Preferences dict to save (uses current if None)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if preferences is not None:
                self.preferences = preferences
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.preferences_file), exist_ok=True)
            
            # Save with pretty formatting
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(self.preferences, f, indent=2, ensure_ascii=False)
            
            info(f"Preferences saved to: {self.preferences_file}", "Preferences")
            return True
            
        except (IOError, OSError) as e:
            error(f"Failed to save preferences: {e}", "Preferences")
            return False
    
    def get_preference(self, category: str, key: str, default: Any = None) -> Any:
        """
        Get a specific preference value
        
        Args:
            category: Preference category (visual, data, export, ui, logging)
            key: Preference key within category
            default: Default value if not found
            
        Returns:
            Preference value or default
        """
        try:
            return self.preferences.get(category, {}).get(key, default)
        except (KeyError, AttributeError):
            return default
    
    def set_preference(self, category: str, key: str, value: Any) -> None:
        """
        Set a specific preference value
        
        Args:
            category: Preference category
            key: Preference key within category
            value: Value to set
        """
        if category not in self.preferences:
            self.preferences[category] = {}
        
        self.preferences[category][key] = value
    
    def update_preferences(self, updates: Dict[str, Dict[str, Any]]) -> None:
        """
        Update multiple preferences at once
        
        Args:
            updates: Dictionary of category -> {key: value} updates
        """
        for category, prefs in updates.items():
            if category not in self.preferences:
                self.preferences[category] = {}
            
            for key, value in prefs.items():
                self.preferences[category][key] = value
    
    def reset_to_defaults(self) -> Dict[str, Any]:
        """
        Reset all preferences to defaults
        
        Returns:
            dict: Default preferences
        """
        self.preferences = self.default_preferences.copy()
        info("Preferences reset to defaults", "Preferences")
        return self.preferences
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """
        Get all current preferences
        
        Returns:
            dict: All preferences
        """
        return self.preferences.copy()
    
    def _merge_preferences(self, defaults: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge loaded preferences with defaults to ensure all keys exist
        
        Args:
            defaults: Default preferences structure
            loaded: Loaded preferences from file
            
        Returns:
            dict: Merged preferences
        """
        merged = defaults.copy()
        
        for category, prefs in loaded.items():
            if category in merged and isinstance(prefs, dict):
                merged[category].update(prefs)
            else:
                merged[category] = prefs
        
        return merged
    
    def export_preferences(self, export_file: str) -> bool:
        """
        Export preferences to a different file
        
        Args:
            export_file: Path to export file
            
        Returns:
            bool: True if successful
        """
        try:
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(self.preferences, f, indent=2, ensure_ascii=False)
            
            info(f"Preferences exported to: {export_file}", "Preferences")
            return True
            
        except (IOError, OSError) as e:
            error(f"Failed to export preferences: {e}", "Preferences")
            return False
    
    def import_preferences(self, import_file: str) -> bool:
        """
        Import preferences from a file
        
        Args:
            import_file: Path to import file
            
        Returns:
            bool: True if successful
        """
        try:
            if not os.path.exists(import_file):
                warning(f"Import file not found: {import_file}", "Preferences")
                return False
            
            with open(import_file, 'r', encoding='utf-8') as f:
                imported_prefs = json.load(f)
            
            # Merge with defaults
            self.preferences = self._merge_preferences(self.default_preferences, imported_prefs)
            
            info(f"Preferences imported from: {import_file}", "Preferences")
            return True
            
        except (json.JSONDecodeError, IOError) as e:
            error(f"Failed to import preferences: {e}", "Preferences")
            return False


# Global preferences manager instance
_preferences_manager = None

def get_preferences_manager() -> PreferencesManager:
    """Get the global preferences manager instance"""
    global _preferences_manager
    if _preferences_manager is None:
        _preferences_manager = PreferencesManager()
    return _preferences_manager

def load_preferences() -> Dict[str, Any]:
    """Load preferences from file"""
    return get_preferences_manager().load_preferences()

def save_preferences(preferences: Optional[Dict[str, Any]] = None) -> bool:
    """Save preferences to file"""
    return get_preferences_manager().save_preferences(preferences)

def get_preference(category: str, key: str, default: Any = None) -> Any:
    """Get a specific preference value"""
    return get_preferences_manager().get_preference(category, key, default)

def set_preference(category: str, key: str, value: Any) -> None:
    """Set a specific preference value"""
    get_preferences_manager().set_preference(category, key, value)

def update_preferences(updates: Dict[str, Dict[str, Any]]) -> None:
    """Update multiple preferences at once"""
    get_preferences_manager().update_preferences(updates)

def set_last_opened_file(file_path: str) -> None:
    """Set the last opened file and save preferences"""
    if file_path and os.path.exists(file_path):
        set_preference("session", "last_opened_file", os.path.abspath(file_path))
        save_preferences()

def get_last_opened_file() -> Optional[str]:
    """Get the last opened file path if it exists and remember_last_file is enabled"""
    if get_preference("session", "remember_last_file", True):
        last_file = get_preference("session", "last_opened_file", None)
        if last_file and os.path.exists(last_file):
            return last_file
    return None

def should_remember_last_file() -> bool:
    """Check if the application should remember the last opened file"""
    return get_preference("session", "remember_last_file", True)

def set_remember_last_file(remember: bool) -> None:
    """Set whether to remember the last opened file"""
    set_preference("session", "remember_last_file", remember)
    save_preferences()

def set_last_file_memory_enabled(remember: bool) -> None:
    """Alias for set_remember_last_file for consistency"""
    set_remember_last_file(remember)
