"""Configuration and data loading utilities.

This module provides functions for loading and validating configuration
and data files for Anki deck building.
"""

from pathlib import Path
from typing import cast

import yaml
from pydantic import ValidationError

from anki_yaml_tool.core.builder import ModelConfigComplete
from anki_yaml_tool.core.exceptions import ConfigValidationError, DataValidationError
from anki_yaml_tool.core.validators import ModelConfigSchema


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
        raw_config = yaml.safe_load(f)

    if not raw_config:
        raise ConfigValidationError("Config file is empty", str(config_path))

    # Use Pydantic for validation
    try:
        validated_config = ModelConfigSchema(**raw_config)
        # Convert Pydantic model back to dict for compatibility
        return cast(ModelConfigComplete, validated_config.model_dump())
    except ValidationError as e:
        # Convert Pydantic validation errors to ConfigValidationError
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            msg = error["msg"]
            error_messages.append(f"{field}: {msg}")

        raise ConfigValidationError(
            "Invalid configuration:\n  " + "\n  ".join(error_messages),
            str(config_path),
        ) from e


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
