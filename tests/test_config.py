"""Tests for the configuration loading module."""

from pathlib import Path

import pytest
from anki_yaml_tool.core.config import load_deck_data, load_deck_file, load_model_config
from anki_yaml_tool.core.exceptions import ConfigValidationError, DataValidationError


def test_load_model_config_success(tmp_path):
    """Test loading a valid model configuration."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
name: "Test Model"
fields:
  - "Front"
  - "Back"
templates:
  - name: "Card 1"
    qfmt: "{{Front}}"
    afmt: "{{FrontSide}}<hr>{{Back}}"
css: ".card { font-size: 20px; }"
"""
    )

    config = load_model_config(config_file)

    assert config["name"] == "Test Model"
    assert config["fields"] == ["Front", "Back"]
    assert len(config["templates"]) == 1
    assert config["templates"][0]["name"] == "Card 1"
    assert config["css"] == ".card { font-size: 20px; }"


def test_load_model_config_nonexistent_file():
    """Test loading a configuration file that doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_model_config(Path("/nonexistent/config.yaml"))


def test_load_model_config_empty_file(tmp_path):
    """Test loading an empty configuration file."""
    config_file = tmp_path / "empty_config.yaml"
    config_file.write_text("")

    with pytest.raises(ConfigValidationError) as exc_info:
        load_model_config(config_file)

    assert "empty" in str(exc_info.value).lower()


def test_load_model_config_missing_required_fields(tmp_path):
    """Test loading a configuration file with missing required fields."""
    config_file = tmp_path / "invalid_config.yaml"
    config_file.write_text(
        """
name: "Test Model"
fields:
  - "Front"
"""
    )

    with pytest.raises(ConfigValidationError) as exc_info:
        load_model_config(config_file)

    # Pydantic error message includes "Field required" or similar
    error_msg = str(exc_info.value).lower()
    assert "templates" in error_msg
    assert "required" in error_msg or "missing" in error_msg


def test_load_model_config_without_css(tmp_path):
    """Test loading a configuration file without optional CSS field."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
name: "Test Model"
fields:
  - "Front"
  - "Back"
templates:
  - name: "Card 1"
    qfmt: "{{Front}}"
    afmt: "{{FrontSide}}<hr>{{Back}}"
"""
    )

    config = load_model_config(config_file)

    assert config["name"] == "Test Model"
    # Pydantic includes css field with default empty string
    assert config.get("css") == ""


def test_load_deck_data_success(tmp_path):
    """Test loading valid deck data."""
    data_file = tmp_path / "data.yaml"
    data_file.write_text(
        """
- front: "Question 1"
  back: "Answer 1"
  tags: ["tag1", "tag2"]

- front: "Question 2"
  back: "Answer 2"
"""
    )

    items = load_deck_data(data_file)

    assert len(items) == 2
    assert items[0]["front"] == "Question 1"
    assert items[0]["back"] == "Answer 1"
    assert items[0]["tags"] == ["tag1", "tag2"]
    assert items[1]["front"] == "Question 2"
    assert items[1]["back"] == "Answer 2"


def test_load_deck_data_nonexistent_file():
    """Test loading a data file that doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_deck_data(Path("/nonexistent/data.yaml"))


def test_load_deck_data_empty_file(tmp_path):
    """Test loading an empty data file."""
    data_file = tmp_path / "empty_data.yaml"
    data_file.write_text("")

    with pytest.raises(DataValidationError) as exc_info:
        load_deck_data(data_file)

    assert "empty" in str(exc_info.value).lower()


def test_load_deck_data_invalid_format(tmp_path):
    """Test loading a data file with invalid format (not a list)."""
    data_file = tmp_path / "invalid_data.yaml"
    data_file.write_text(
        """
front: "Question 1"
back: "Answer 1"
"""
    )

    with pytest.raises(DataValidationError) as exc_info:
        load_deck_data(data_file)

    assert "must contain a list" in str(exc_info.value).lower()


def test_load_model_config_with_string_path(tmp_path):
    """Test loading a model configuration using a string path."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
name: "Test Model"
fields:
  - "Front"
templates:
  - name: "Card 1"
    qfmt: "{{Front}}"
    afmt: "{{Back}}"
"""
    )

    config = load_model_config(str(config_file))

    assert config["name"] == "Test Model"


def test_load_deck_data_with_string_path(tmp_path):
    """Test loading deck data using a string path."""
    data_file = tmp_path / "data.yaml"
    data_file.write_text(
        """
- front: "Question 1"
  back: "Answer 1"
"""
    )

    items = load_deck_data(str(data_file))

    assert len(items) == 1
    assert items[0]["front"] == "Question 1"


def test_load_deck_file_success(tmp_path):
    """Test loading a valid single-file deck."""
    deck_file = tmp_path / "deck.yaml"
    deck_file.write_text(
        """
config:
  name: "Test Model"
  deck-name: "Test Deck"
  fields:
    - "Front"
    - "Back"
  templates:
    - name: "Card 1"
      qfmt: "{{Front}}"
      afmt: "{{FrontSide}}<hr>{{Back}}"
  css: ".card { font-size: 20px; }"

data:
  - front: "Question 1"
    back: "Answer 1"
    tags: ["tag1"]
  - front: "Question 2"
    back: "Answer 2"
"""
    )

    model_config, items, deck_name, media_folder = load_deck_file(deck_file)

    assert model_config["name"] == "Test Model"
    assert model_config["fields"] == ["Front", "Back"]
    assert len(model_config["templates"]) == 1
    assert deck_name == "Test Deck"
    assert media_folder is None
    assert len(items) == 2
    assert items[0]["front"] == "Question 1"


def test_load_deck_file_with_media_folder(tmp_path):
    """Test loading a deck file with media folder."""
    # Create media directory
    media_dir = tmp_path / "media"
    media_dir.mkdir()

    deck_file = tmp_path / "deck.yaml"
    deck_file.write_text(
        """
config:
  name: "Test Model"
  deck-name: "Test Deck"
  media-folder: "./media/"
  fields:
    - "Front"
  templates:
    - name: "Card 1"
      qfmt: "{{Front}}"
      afmt: "{{Front}}"

data:
  - front: "Question 1"
"""
    )

    model_config, items, deck_name, media_folder = load_deck_file(deck_file)

    assert media_folder is not None
    assert media_folder == media_dir
    assert media_folder.exists()


def test_load_deck_file_media_folder_not_exists(tmp_path):
    """Test loading a deck file with media folder that doesn't exist."""
    deck_file = tmp_path / "deck.yaml"
    deck_file.write_text(
        """
config:
  name: "Test Model"
  deck-name: "Test Deck"
  media-folder: "./media/"
  fields:
    - "Front"
  templates:
    - name: "Card 1"
      qfmt: "{{Front}}"
      afmt: "{{Front}}"

data:
  - front: "Question 1"
"""
    )

    model_config, items, deck_name, media_folder = load_deck_file(deck_file)

    # Media folder should be None if it doesn't exist
    assert media_folder is None


def test_load_deck_file_nonexistent_file():
    """Test loading a deck file that doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_deck_file(Path("/nonexistent/deck.yaml"))


def test_load_deck_file_empty_file(tmp_path):
    """Test loading an empty deck file."""
    deck_file = tmp_path / "empty_deck.yaml"
    deck_file.write_text("")

    with pytest.raises(ConfigValidationError) as exc_info:
        load_deck_file(deck_file)

    assert "empty" in str(exc_info.value).lower()


def test_load_deck_file_missing_config_section(tmp_path):
    """Test loading a deck file without config section."""
    deck_file = tmp_path / "deck.yaml"
    deck_file.write_text(
        """
data:
  - front: "Question 1"
"""
    )

    with pytest.raises(ConfigValidationError) as exc_info:
        load_deck_file(deck_file)

    assert "config" in str(exc_info.value).lower()


def test_load_deck_file_missing_data_section(tmp_path):
    """Test loading a deck file without data section."""
    deck_file = tmp_path / "deck.yaml"
    deck_file.write_text(
        """
config:
  name: "Test Model"
  deck-name: "Test Deck"
  fields:
    - "Front"
  templates:
    - name: "Card 1"
      qfmt: "{{Front}}"
      afmt: "{{Front}}"
"""
    )

    with pytest.raises(DataValidationError) as exc_info:
        load_deck_file(deck_file)

    assert "data" in str(exc_info.value).lower()


def test_load_deck_file_empty_data_section(tmp_path):
    """Test loading a deck file with empty data section."""
    deck_file = tmp_path / "deck.yaml"
    deck_file.write_text(
        """
config:
  name: "Test Model"
  deck-name: "Test Deck"
  fields:
    - "Front"
  templates:
    - name: "Card 1"
      qfmt: "{{Front}}"
      afmt: "{{Front}}"

data: []
"""
    )

    with pytest.raises(DataValidationError) as exc_info:
        load_deck_file(deck_file)

    assert "empty" in str(exc_info.value).lower()


def test_load_deck_file_invalid_data_section(tmp_path):
    """Test loading a deck file with invalid data section (not a list)."""
    deck_file = tmp_path / "deck.yaml"
    deck_file.write_text(
        """
config:
  name: "Test Model"
  deck-name: "Test Deck"
  fields:
    - "Front"
  templates:
    - name: "Card 1"
      qfmt: "{{Front}}"
      afmt: "{{Front}}"

data:
  front: "Question 1"
"""
    )

    with pytest.raises(DataValidationError) as exc_info:
        load_deck_file(deck_file)

    assert "list" in str(exc_info.value).lower()


def test_load_deck_file_default_deck_name(tmp_path):
    """Test loading a deck file without explicit deck-name."""
    deck_file = tmp_path / "deck.yaml"
    deck_file.write_text(
        """
config:
  name: "Test Model"
  fields:
    - "Front"
  templates:
    - name: "Card 1"
      qfmt: "{{Front}}"
      afmt: "{{Front}}"

data:
  - front: "Question 1"
"""
    )

    model_config, items, deck_name, media_folder = load_deck_file(deck_file)

    assert deck_name == "Generated Deck"
