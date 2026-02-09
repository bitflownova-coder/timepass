"""
Application Configuration Manager
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional
import os


class Config:
    """
    Centralized configuration management with file persistence
    """
    
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize configuration with defaults and load from file"""
        self.app_dir = Path.home() / ".bitflow_toolkit"
        self.app_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.app_dir / "config.json"
        self.data_dir = self.app_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.logs_dir = self.app_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        self.cache_dir = self.app_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Default configuration
        self._defaults = {
            "theme": "dark_teal.xml",
            "font_size": 10,
            "font_family": "Consolas",
            "sidebar_collapsed": False,
            "window_state": {},
            "recent_files": [],
            "max_recent_files": 10,
            
            # Time Tracker defaults
            "time_tracker": {
                "default_hourly_rate": 0.0,
                "auto_pause_after_mins": 0,
                "reminder_interval_mins": 30
            },
            
            # Quick Notes defaults
            "quick_notes": {
                "auto_save": True,
                "default_folder": "General"
            },
            
            # Snippet Manager defaults
            "snippets": {
                "default_language": "python",
                "sync_enabled": False
            },
            
            # API Tester defaults
            "api_tester": {
                "default_timeout": 30,
                "follow_redirects": True,
                "verify_ssl": True
            },
            
            # Crawler defaults
            "crawler": {
                "default_depth": 2,
                "default_concurrency": 3,
                "default_delay": 1,
                "download_images": True,
                "download_documents": True
            },
            
            # Finance defaults  
            "finance": {
                "currency": "INR",
                "currency_symbol": "₹",
                "date_format": "dd/MM/yyyy"
            }
        }
        
        self._config = self._defaults.copy()
        self._load()
    
    def _load(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self._deep_update(self._config, loaded)
            except (json.JSONDecodeError, IOError):
                pass
    
    def _deep_update(self, base: dict, update: dict):
        """Deep merge update into base dict"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def save(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Failed to save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value
    
    def set(self, key: str, value: Any, save: bool = True):
        """Set a configuration value using dot notation"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        if save:
            self.save()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get an entire configuration section"""
        return self._config.get(section, {})
    
    @property
    def database_path(self) -> Path:
        """Get the database file path"""
        return self.data_dir / "bitflow_toolkit.db"
    
    @property
    def crawler_output_dir(self) -> Path:
        """Get the crawler output directory"""
        path = self.data_dir / "crawler_output"
        path.mkdir(exist_ok=True)
        return path
    
    def add_recent_file(self, file_path: str):
        """Add a file to recent files list"""
        recents = self.get("recent_files", [])
        if file_path in recents:
            recents.remove(file_path)
        recents.insert(0, file_path)
        max_files = self.get("max_recent_files", 10)
        self._config["recent_files"] = recents[:max_files]
        self.save()


# Global singleton instance
config = Config()
