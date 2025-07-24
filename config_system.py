"""
Centralized Configuration System for CrewAI Workflow Orchestration Platform.

This module provides a layered configuration system with fallbacks:
1. Environment variables (highest priority)
2. Environment-specific configuration files
3. Base configuration files (lowest priority)

Configuration values can be accessed using dot notation keys, and
type conversion is handled automatically.
"""

import os
import json
import logging
from typing import Any, Dict, Optional
from pathlib import Path

from logging_config import log_info, log_error, log_warning, log_debug

logger = logging.getLogger(__name__)

class ConfigSystem:
    """Centralized configuration system with layered fallbacks"""
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize the configuration system.
        
        Args:
            config_dir (str, optional): Directory containing configuration files.
                Defaults to "config".
        """
        self.config_dir = Path(config_dir)
        self.env_prefix = "CREWAI_"
        self.config_cache = {}
        self.load_config()
    
    def load_config(self):
        """
        Load configuration from files.
        
        Loads configuration in layers:
        1. Base configuration (config/base_config.json)
        2. Environment-specific configuration (config/{env}_config.json)
        
        Environment is determined by the CREWAI_ENV environment variable,
        defaulting to "development" if not set.
        """
        try:
            # Create config directory if it doesn't exist
            os.makedirs(self.config_dir, exist_ok=True)
            
            # Load base configuration
            base_config_path = self.config_dir / "base_config.json"
            if base_config_path.exists():
                with open(base_config_path, "r") as f:
                    self.config_cache = json.load(f)
                    log_info(logger, f"Loaded base configuration from {base_config_path}")
            else:
                log_warning(logger, f"Base configuration file not found: {base_config_path}")
            
            # Load environment-specific configuration
            env = os.getenv(f"{self.env_prefix}ENV", "development")
            env_config_path = self.config_dir / f"{env}_config.json"
            if env_config_path.exists():
                with open(env_config_path, "r") as f:
                    env_config = json.load(f)
                    # Merge with base config
                    self._deep_merge(self.config_cache, env_config)
                    log_info(logger, f"Loaded {env} configuration from {env_config_path}")
            else:
                log_warning(logger, f"Environment configuration file not found: {env_config_path}")
        except Exception as e:
            log_error(logger, "Error loading configuration", e)
    
    def _deep_merge(self, base: Dict, override: Dict):
        """
        Deep merge two dictionaries.
        
        Args:
            base (Dict): Base dictionary to merge into
            override (Dict): Dictionary with values to override base
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with fallbacks.
        
        Checks for configuration values in the following order:
        1. Environment variable (CREWAI_KEY_NAME)
        2. Configuration cache (loaded from files)
        3. Default value provided
        
        Args:
            key (str): Configuration key in dot notation (e.g., "llm.temperature")
            default (Any, optional): Default value if key not found. Defaults to None.
            
        Returns:
            Any: Configuration value or default
        """
        # Try environment variable first
        env_key = f"{self.env_prefix}{key.upper().replace('.', '_')}"
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._convert_value(env_value)
        
        # Try config cache
        parts = key.split(".")
        config = self.config_cache
        for part in parts:
            if isinstance(config, dict) and part in config:
                config = config[part]
            else:
                return default
        return config
    
    def _convert_value(self, value: str) -> Any:
        """
        Convert string value to appropriate type.
        
        Args:
            value (str): String value to convert
            
        Returns:
            Any: Converted value (bool, int, float, or str)
        """
        # Try to convert to appropriate type
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value
    
    def set_default_config(self, config: Dict[str, Any]):
        """
        Set default configuration if no configuration files exist.
        
        Args:
            config (Dict[str, Any]): Default configuration dictionary
        """
        if not self.config_cache:
            self.config_cache = config
            log_info(logger, "Set default configuration")
            
            # Save to base_config.json if it doesn't exist
            base_config_path = self.config_dir / "base_config.json"
            if not base_config_path.exists():
                try:
                    with open(base_config_path, "w") as f:
                        json.dump(config, f, indent=2)
                    log_info(logger, f"Saved default configuration to {base_config_path}")
                except Exception as e:
                    log_error(logger, f"Error saving default configuration", e)

# Default configuration
DEFAULT_CONFIG = {
    "llm": {
        "temperature": 0.3,
        "max_tokens": 2048,
        "streaming": True,
        "top_p": 0.9,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1
    },
    "quality": {
        "thresholds": {
            "excellent": 0.85,
            "good": 0.70,
            "acceptable": 0.55,
            "poor": 0.40
        }
    },
    "cache": {
        "ttl": {
            "profile_enrichment": 7200,
            "thread_analysis": 3600,
            "reply_generation": 1800
        }
    },
    "api": {
        "cors": {
            "allowed_origins": ["http://localhost:3000", "http://localhost:8100"]
        }
    }
}

# Global instance
config_system = ConfigSystem()

# Set default configuration
config_system.set_default_config(DEFAULT_CONFIG)

# Update logging configuration with values from config system
from logging_config import configure_logging
configure_logging(config_system)