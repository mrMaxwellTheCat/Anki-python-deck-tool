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


def load_deck_file(
    deck_path: Path | str,
) -> tuple[ModelConfigComplete, list[dict[str, str | list[str]]], str, Path | None]:
    """Load a single deck file containing both configuration and data.

    Args:
        deck_path: Path to the deck YAML file.

    Returns:
        A tuple containing:
        - The loaded and validated model configuration
        - A list of dictionaries containing note data
        - The deck name
        - The media folder path (relative to deck file) or None

    Raises:
        ConfigValidationError: If the deck file has invalid configuration.
        DataValidationError: If the deck file has invalid data.
        FileNotFoundError: If the deck file doesn't exist.
    """
    path = Path(deck_path)

    if not path.exists():
        raise FileNotFoundError(f"Deck file not found: {deck_path}")

    with open(path, encoding="utf-8") as f:
        raw_deck = yaml.safe_load(f)

    if not raw_deck:
        raise ConfigValidationError("Deck file is empty", str(deck_path))

    if not isinstance(raw_deck, dict):
        raise ConfigValidationError(
            "Deck file must contain a dictionary with 'config' and 'data' keys",
            str(deck_path),
        )

    # Extract config section
    if "config" not in raw_deck:
        raise ConfigValidationError(
            "Deck file missing 'config' section", str(deck_path)
        )

    config_section = raw_deck["config"]
    if not isinstance(config_section, dict):
        raise ConfigValidationError(
            "'config' section must be a dictionary", str(deck_path)
        )

    # Extract deck-name from config section
    deck_name = config_section.get("deck-name", "Generated Deck")
    if not isinstance(deck_name, str):
        deck_name = str(deck_name)

    # Extract media-folder from config section
    media_folder = config_section.get("media-folder")
    media_folder_path = None
    if media_folder:
        if not isinstance(media_folder, str):
            media_folder = str(media_folder)
        # Resolve relative to deck file location
        resolved_path = (path.parent / media_folder).resolve()
        # Only return the path if it actually exists
        if resolved_path.exists():
            media_folder_path = resolved_path

    # Validate model config using Pydantic
    try:
        validated_config = ModelConfigSchema(**config_section)
        model_config = cast(ModelConfigComplete, validated_config.model_dump())
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            msg = error["msg"]
            error_messages.append(f"{field}: {msg}")

        raise ConfigValidationError(
            "Invalid configuration:\n  " + "\n  ".join(error_messages),
            str(deck_path),
        ) from e

    # Extract data section
    if "data" not in raw_deck:
        raise DataValidationError("Deck file missing 'data' section", str(deck_path))

    data_section = raw_deck["data"]
    if not isinstance(data_section, list):
        raise DataValidationError(
            "'data' section must be a list of notes", str(deck_path)
        )

    if not data_section:
        raise DataValidationError("'data' section is empty", str(deck_path))

    return model_config, data_section, deck_name, media_folder_path
