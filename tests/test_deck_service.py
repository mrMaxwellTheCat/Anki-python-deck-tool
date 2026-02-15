"""Tests for the deck_service module.

This module contains unit tests for the build_deck, validate_deck,
and push_apkg service functions.
"""

from unittest.mock import Mock

import pytest
import yaml
from anki_yaml_tool.core.deck_service import (
    BuildResult,
    ValidationIssue,
    ValidationResult,
    build_deck,
    push_apkg,
    validate_deck,
)
from anki_yaml_tool.core.exceptions import (
    ConfigValidationError,
)


@pytest.fixture
def sample_deck_yaml():
    """Provide minimal valid deck YAML content."""
    return {
        "config": {
            "name": "Test Model",
            "fields": ["Front", "Back"],
            "templates": [
                {
                    "name": "Card 1",
                    "qfmt": "{{Front}}",
                    "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
                }
            ],
        },
        "data": [
            {"front": "Question 1", "back": "Answer 1"},
            {"front": "Question 2", "back": "Answer 2"},
        ],
    }


@pytest.fixture
def deck_file(tmp_path, sample_deck_yaml):
    """Create a temporary deck YAML file."""
    path = tmp_path / "deck.yaml"
    path.write_text(yaml.dump(sample_deck_yaml), encoding="utf-8")
    return path


class TestBuildDeck:
    """Tests for the build_deck service function."""

    def test_build_deck_success(self, deck_file, tmp_path):
        """Test building a deck from valid YAML."""
        output = tmp_path / "output.apkg"
        result = build_deck(deck_file, output_path=output)

        assert isinstance(result, BuildResult)
        assert result.output_path == output
        assert result.notes_processed == 2
        assert result.deck_name is not None
        assert output.exists()

    def test_build_deck_with_deck_name_override(self, deck_file, tmp_path):
        """Test that deck_name_override takes precedence."""
        output = tmp_path / "output.apkg"
        result = build_deck(
            deck_file, output_path=output, deck_name_override="My Custom Deck"
        )
        assert result.deck_name == "My Custom Deck"

    def test_build_deck_uses_file_deck_name(self, tmp_path):
        """Test that deck-name from YAML is used when no override."""
        deck_data = {
            "deck-name": "YAML Deck Name",
            "config": {
                "name": "Model",
                "fields": ["F"],
                "templates": [{"name": "T", "qfmt": "{{F}}", "afmt": "{{F}}"}],
            },
            "data": [{"f": "value"}],
        }
        deck_file = tmp_path / "deck.yaml"
        deck_file.write_text(yaml.dump(deck_data), encoding="utf-8")

        output = tmp_path / "out.apkg"
        result = build_deck(deck_file, output_path=output)
        assert result.deck_name == "YAML Deck Name"

    def test_build_deck_fallback_deck_name(self, tmp_path):
        """Test fallback deck name uses parent directory for deck.yaml."""
        subdir = tmp_path / "MyDeck"
        subdir.mkdir()
        deck_data = {
            "config": {
                "name": "Model",
                "fields": ["F"],
                "templates": [{"name": "T", "qfmt": "{{F}}", "afmt": "{{F}}"}],
            },
            "data": [{"f": "value"}],
        }
        deck_file = subdir / "deck.yaml"
        deck_file.write_text(yaml.dump(deck_data), encoding="utf-8")

        output = tmp_path / "out.apkg"
        result = build_deck(deck_file, output_path=output)
        assert result.deck_name == "MyDeck"

    def test_build_deck_with_media(self, tmp_path):
        """Test building a deck with media directory."""
        media_dir = tmp_path / "media"
        media_dir.mkdir()
        (media_dir / "image.png").write_bytes(b"PNG_DATA")

        deck_data = {
            "config": {
                "name": "Model",
                "fields": ["F"],
                "templates": [{"name": "T", "qfmt": "{{F}}", "afmt": "{{F}}"}],
            },
            "data": [{"f": '<img src="image.png">'}],
        }
        deck_file = tmp_path / "deck.yaml"
        deck_file.write_text(yaml.dump(deck_data), encoding="utf-8")

        output = tmp_path / "out.apkg"
        result = build_deck(
            deck_file, output_path=output, media_dir_override=str(media_dir)
        )
        assert result.media_files >= 1

    def test_build_deck_invalid_config(self, tmp_path):
        """Test that invalid config raises ConfigValidationError."""
        deck_data = {
            "config": {"name": ""},  # Invalid: missing fields and templates
            "data": [{"f": "value"}],
        }
        deck_file = tmp_path / "deck.yaml"
        deck_file.write_text(yaml.dump(deck_data), encoding="utf-8")

        with pytest.raises(ConfigValidationError):
            build_deck(deck_file, output_path=tmp_path / "out.apkg")

    def test_build_deck_missing_file(self, tmp_path):
        """Test that missing deck file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            build_deck(tmp_path / "nonexistent.yaml")


class TestValidateDeck:
    """Tests for the validate_deck service function."""

    def test_validate_deck_passes(self, deck_file):
        """Test that valid YAML passes validation."""
        result = validate_deck(deck_file)
        assert isinstance(result, ValidationResult)
        assert not result.has_errors

    def test_validate_deck_duplicate_ids(self, tmp_path):
        """Test that duplicate IDs are reported."""
        deck_data = {
            "config": {
                "name": "Model",
                "fields": ["F"],
                "templates": [{"name": "T", "qfmt": "{{F}}", "afmt": "{{F}}"}],
            },
            "data": [
                {"f": "1", "id": "dup"},
                {"f": "2", "id": "dup"},
            ],
        }
        deck_file = tmp_path / "deck.yaml"
        deck_file.write_text(yaml.dump(deck_data), encoding="utf-8")

        result = validate_deck(deck_file)
        assert result.has_warnings
        assert any("dup" in i.message for i in result.issues)

    def test_validate_deck_missing_fields(self, tmp_path):
        """Test that missing required fields produce warnings."""
        deck_data = {
            "config": {
                "name": "Model",
                "fields": ["Front", "Back"],
                "templates": [{"name": "T", "qfmt": "{{Front}}", "afmt": "{{Back}}"}],
            },
            "data": [{"front": "Q1"}],  # Missing 'back'
        }
        deck_file = tmp_path / "deck.yaml"
        deck_file.write_text(yaml.dump(deck_data), encoding="utf-8")

        result = validate_deck(deck_file)
        assert result.has_warnings
        assert any("back" in i.message.lower() for i in result.issues)

    def test_validate_deck_strict_mode(self, tmp_path):
        """Test that strict mode does NOT affect the returned result."""
        deck_data = {
            "config": {
                "name": "Model",
                "fields": ["Front", "Back"],
                "templates": [{"name": "T", "qfmt": "{{Front}}", "afmt": "{{Back}}"}],
            },
            "data": [{"front": "Q1"}],  # Missing 'back' → warning
        }
        deck_file = tmp_path / "deck.yaml"
        deck_file.write_text(yaml.dump(deck_data), encoding="utf-8")

        result = validate_deck(deck_file, strict=True)
        # strict is checked by CLI, not by deck_service
        assert result.has_warnings
        assert not result.has_errors

    def test_validate_deck_invalid_model(self, tmp_path):
        """Test that notes referencing unknown model produce errors."""
        deck_data = {
            "config": {
                "name": "Model",
                "fields": ["F"],
                "templates": [{"name": "T", "qfmt": "{{F}}", "afmt": "{{F}}"}],
            },
            "data": [{"f": "value", "model": "NonExistent"}],
        }
        deck_file = tmp_path / "deck.yaml"
        deck_file.write_text(yaml.dump(deck_data), encoding="utf-8")

        result = validate_deck(deck_file)
        assert result.has_errors
        assert any("NonExistent" in i.message for i in result.issues)

    def test_validate_deck_html_warnings(self, tmp_path):
        """Test that unclosed HTML tags are warned about."""
        deck_data = {
            "config": {
                "name": "Model",
                "fields": ["F"],
                "templates": [{"name": "T", "qfmt": "{{F}}", "afmt": "{{F}}"}],
            },
            "data": [{"f": "<b>unclosed"}],
        }
        deck_file = tmp_path / "deck.yaml"
        deck_file.write_text(yaml.dump(deck_data), encoding="utf-8")

        result = validate_deck(deck_file)
        assert result.has_warnings
        assert any("Unclosed" in i.message for i in result.issues)


class TestPushApkg:
    """Tests for the push_apkg service function."""

    def test_push_apkg_calls_connector(self, tmp_path):
        """Test that push_apkg calls import_package on the connector."""
        import zipfile

        apkg_file = tmp_path / "test.apkg"
        with zipfile.ZipFile(apkg_file, "w") as zf:
            zf.writestr("dummy", "data")

        mock_connector = Mock()

        push_apkg(apkg_file, mock_connector)
        mock_connector.import_package.assert_called_once()

    def test_push_apkg_with_sync(self, tmp_path):
        """Test that push_apkg triggers sync when requested."""
        import zipfile

        apkg_file = tmp_path / "test.apkg"
        with zipfile.ZipFile(apkg_file, "w") as zf:
            zf.writestr("dummy", "data")

        mock_connector = Mock()

        push_apkg(apkg_file, mock_connector, sync=True)
        mock_connector.import_package.assert_called_once()
        mock_connector.sync.assert_called_once()


class TestValidationResult:
    """Tests for the ValidationResult dataclass."""

    def test_empty_result(self):
        """Test that an empty result has no errors or warnings."""
        result = ValidationResult()
        assert not result.has_errors
        assert not result.has_warnings

    def test_result_with_errors(self):
        """Test has_errors property."""
        result = ValidationResult(issues=[ValidationIssue("error", "Something wrong")])
        assert result.has_errors
        assert not result.has_warnings

    def test_result_with_warnings(self):
        """Test has_warnings property."""
        result = ValidationResult(issues=[ValidationIssue("warning", "Something off")])
        assert not result.has_errors
        assert result.has_warnings
