"""Configuration and data loading utilities.

This module provides functions for loading and validating configuration
and data files for Anki deck building.
"""

from pathlib import Path
from typing import cast

import yaml

from anki_tool.core.builder import ModelConfigComplete
from anki_tool.core.exceptions import ConfigValidationError, DataValidationError


def load_model_config(config_path: Path | str) -> ModelConfigComplete:
    """Load and validate a model configuration from a YAML file.

    Args:
        config_path: Path to the configuration YAML file.

    Returns:
        The loaded and validated model configuration.

    Raises:
        ConfigValidationError: If the configuration file is empty or invalid.
        FileNotFoundError: If the configuration file doesn't exist.
    """
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(path, encoding="utf-8") as f:
        model_config = yaml.safe_load(f)

    if not model_config:
        raise ConfigValidationError("Config file is empty", str(config_path))

    # Validate required fields
    required_fields = {"name", "fields", "templates"}
    missing_fields = required_fields - set(model_config.keys())
    if missing_fields:
        raise ConfigValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            str(config_path),
        )

    return cast(ModelConfigComplete, model_config)


def load_deck_data(data_path: Path | str) -> list[dict[str, str | list[str]]]:
    """Load deck data from a YAML file.

    Args:
        data_path: Path to the data YAML file.

    Returns:
        A list of dictionaries containing note data.

    Raises:
        DataValidationError: If the data file is empty or invalid.
        FileNotFoundError: If the data file doesn't exist.
    """
    path = Path(data_path)

    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    with open(path, encoding="utf-8") as f:
        items = yaml.safe_load(f)

    if not items:
        raise DataValidationError("Data file is empty", str(data_path))

    if not isinstance(items, list):
        raise DataValidationError(
            "Data file must contain a list of notes",
            str(data_path),
        )

    return items  # type: ignore[return-value]
