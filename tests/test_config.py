"""Tests for the configuration loading module."""

from pathlib import Path

import pytest
from anki_tool.core.config import load_deck_data, load_model_config
from anki_tool.core.exceptions import ConfigValidationError, DataValidationError


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

    assert "missing required fields" in str(exc_info.value).lower()
    assert "templates" in str(exc_info.value).lower()


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
    assert "css" not in config or config.get("css") is None


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
