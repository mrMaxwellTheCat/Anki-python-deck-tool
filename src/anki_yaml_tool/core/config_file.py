"""Configuration file support for anki-yaml-tool.

This module provides utilities for loading and merging configuration
from various sources:
1. Project config file (.anki-yaml-tool.yaml in current directory)
2. User config file (~/.anki-yaml-tool.yaml)
3. Command-line options (highest priority)
"""

from pathlib import Path
from typing import Any

import yaml

from anki_yaml_tool.core.logging_config import get_logger

log = get_logger("config_file")

# Default config file names
PROJECT_CONFIG_NAME = ".anki-yaml-tool.yaml"
USER_CONFIG_PATH = Path.home() / ".anki-yaml-tool.yaml"


class ConfigFile:
    """Configuration file handler.

    Loads and merges configuration from project and user config files.
    """

    def __init__(self) -> None:
        """Initialize with empty configuration."""
        self._config: dict[str, Any] = {}
        self._loaded_from: list[Path] = []

    @property
    def config(self) -> dict[str, Any]:
        """Return the loaded configuration."""
        return self._config

    @property
    def loaded_from(self) -> list[Path]:
        """Return list of config files that were loaded."""
        return self._loaded_from

    def load(self, project_dir: Path | None = None) -> "ConfigFile":
        """Load configuration from all sources.

        Args:
            project_dir: Project directory to search for config file.
                        Defaults to current working directory.

        Returns:
            Self for method chaining
        """
        project_dir = project_dir or Path.cwd()

        # Load user config first (lower priority)
        if USER_CONFIG_PATH.exists():
            self._load_file(USER_CONFIG_PATH)

        # Load project config (higher priority, overrides user config)
        project_config = project_dir / PROJECT_CONFIG_NAME
        if project_config.exists():
            self._load_file(project_config)

        return self

    def _load_file(self, path: Path) -> None:
        """Load a single config file and merge into current config.

        Args:
            path: Path to the YAML config file
        """
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            if not isinstance(data, dict):
                log.warning("Config file %s is not a dictionary, skipping", path)
                return

            self._merge_config(data)
            self._loaded_from.append(path)
            log.info("Loaded config from: %s", path)

        except yaml.YAMLError as e:
            log.warning("Error parsing config file %s: %s", path, e)
        except OSError as e:
            log.warning("Error reading config file %s: %s", path, e)

    def _merge_config(self, new_config: dict[str, Any]) -> None:
        """Merge new configuration into existing config.

        Args:
            new_config: Configuration dictionary to merge
        """
        for key, value in new_config.items():
            if isinstance(value, dict) and key in self._config:
                # Deep merge for nested dicts
                if isinstance(self._config[key], dict):
                    self._config[key] = {**self._config[key], **value}
                else:
                    self._config[key] = value
            else:
                self._config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (supports dot notation for nested values)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        parts = key.split(".")
        value = self._config

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value

    def get_profile(self, profile_name: str) -> dict[str, Any]:
        """Get configuration for a specific profile.

        Profiles are stored under the 'profiles' key in the config file.
        Profile values are merged with the base configuration.

        Args:
            profile_name: Name of the profile to load

        Returns:
            Merged configuration for the profile
        """
        base = {k: v for k, v in self._config.items() if k != "profiles"}
        profiles = self._config.get("profiles", {})

        if profile_name not in profiles:
            log.debug("Profile '%s' not found, using base config", profile_name)
            return base

        profile_config = profiles[profile_name]
        if not isinstance(profile_config, dict):
            log.warning("Profile '%s' is not a dictionary", profile_name)
            return base

        # Merge profile config on top of base
        merged = base.copy()
        for key, value in profile_config.items():
            if isinstance(value, dict) and key in merged:
                if isinstance(merged[key], dict):
                    merged[key] = {**merged[key], **value}
                else:
                    merged[key] = value
            else:
                merged[key] = value

        log.info("Loaded profile: %s", profile_name)
        return merged


def load_config(project_dir: Path | None = None) -> ConfigFile:
    """Convenience function to load configuration.

    Args:
        project_dir: Project directory to search for config

    Returns:
        Loaded ConfigFile instance
    """
    return ConfigFile().load(project_dir)


def get_default_config() -> dict[str, Any]:
    """Return the default configuration template.

    Returns:
        Dictionary with default configuration options
    """
    return {
        "# Configuration file for anki-yaml-tool": None,
        "# Place this file in your project root or home directory": None,
        "defaults": {
            "output_dir": ".",
            "media_dir": "media",
            "verbose": 0,
        },
        "build": {
            "# Default options for the build command": None,
            "output": "deck.apkg",
        },
        "profiles": {
            "dev": {
                "# Development profile - verbose output": None,
                "verbose": 2,
            },
            "prod": {
                "# Production profile - quiet mode": None,
                "quiet": True,
                "output_dir": "dist",
            },
        },
    }


def generate_config_template() -> str:
    """Generate a YAML config file template.

    Returns:
        YAML string with commented template
    """
    template = """# anki-yaml-tool configuration file
# Place this file as .anki-yaml-tool.yaml in your project root

# Default options applied to all commands
defaults:
  output_dir: .
  media_dir: media

# Build command defaults
build:
  output: deck.apkg

# Profile-based configuration
# Use with: anki-yaml-tool --profile dev build ...
profiles:
  dev:
    # Development profile with verbose output
    verbose: 2

  prod:
    # Production profile with quiet mode
    quiet: true
    output_dir: dist
"""
    return template
