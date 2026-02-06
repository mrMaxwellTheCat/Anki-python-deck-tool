"""Tests for the CLI module.

This module contains tests for the command-line interface, including
build and push commands.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml
from click.testing import CliRunner

from anki_yaml_tool.cli import build, cli, push, validate
from anki_yaml_tool.core.exceptions import (
    AnkiConnectError,
    DeckBuildError,
)


@pytest.fixture
def runner():
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_deck():
    """Provide sample deck data with config and data sections."""
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
            "css": ".card { font-family: arial; }",
        },
        "data": [
            {"front": "Question 1", "back": "Answer 1", "tags": ["test"]},
            {"front": "Question 2", "back": "Answer 2", "tags": ["test", "basic"]},
        ],
    }


@pytest.fixture
def temp_files(tmp_path, sample_deck):
    """Create temporary deck file."""
    deck_file = tmp_path / "deck.yaml"
    output_file = tmp_path / "output.apkg"

    deck_file.write_text(yaml.dump(sample_deck), encoding="utf-8")

    return {
        "file": str(deck_file),
        "output": str(output_file),
        "dir": tmp_path,
    }


class TestCLIGroup:
    """Tests for the main CLI group."""

    def test_cli_group_exists(self, runner):
        """Test that the main CLI group is accessible."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Anki Python Deck Tool" in result.output

    def test_cli_shows_commands(self, runner):
        """Test that the CLI shows available commands."""
        result = runner.invoke(cli, ["--help"])
        assert "build" in result.output
        assert "push" in result.output


class TestBuildCommand:
    """Tests for the build command."""

    def test_build_help(self, runner):
        """Test that build command help is accessible."""
        result = runner.invoke(build, ["--help"])
        assert result.exit_code == 0
        assert "Build an .apkg file from YAML deck file" in result.output

    def test_build_requires_file_option(self, runner):
        """Test that build command requires --file option."""
        result = runner.invoke(build, [])
        assert result.exit_code != 0

    @patch("anki_yaml_tool.cli.AnkiBuilder")
    def test_build_successful(self, mock_builder, runner, temp_files):
        """Test successful deck build."""
        mock_instance = Mock()
        mock_builder.return_value = mock_instance

        result = runner.invoke(
            build,
            [
                "--file",
                temp_files["file"],
                "--output",
                temp_files["output"],
                "--deck-name",
                "Test Deck",
            ],
        )

        assert result.exit_code == 0
        assert "Building deck 'Test Deck'" in result.output
        assert f"Successfully created {temp_files['output']}" in result.output

        # Check that builder was called with a list of configs
        called_args, _ = mock_builder.call_args
        assert called_args[0] == "Test Deck"
        assert isinstance(called_args[1], list)
        assert called_args[1][0]["name"] == "Test Model"

        assert mock_instance.add_note.call_count == 2
        mock_instance.write_to_file.assert_called_once()

    @patch("anki_yaml_tool.cli.AnkiBuilder")
    def test_build_with_tags(self, mock_builder, runner, temp_files):
        """Test that tags are properly passed to notes."""
        mock_instance = Mock()
        mock_builder.return_value = mock_instance

        result = runner.invoke(
            build,
            [
                "--file",
                temp_files["file"],
                "--output",
                temp_files["output"],
            ],
        )

        assert result.exit_code == 0
        # Check that tags were passed
        calls = mock_instance.add_note.call_args_list
        assert len(calls) == 2
        assert "test" in calls[0][1]["tags"]
        assert "basic" in calls[1][1]["tags"]

    @patch("anki_yaml_tool.cli.AnkiBuilder")
    def test_build_with_id_tag(self, mock_builder, runner, tmp_path):
        """Test that id field is converted to id:: tag."""
        mock_instance = Mock()
        mock_builder.return_value = mock_instance

        deck_data = {
            "config": {
                "name": "Test Model",
                "fields": ["Front", "Back"],
                "templates": [
                    {"name": "Card 1", "qfmt": "{{Front}}", "afmt": "{{Back}}"}
                ],
            },
            "data": [{"front": "Q", "back": "A", "id": "test_123", "tags": ["basic"]}],
        }

        deck_file = tmp_path / "deck.yaml"
        deck_file.write_text(yaml.dump(deck_data), encoding="utf-8")

        result = runner.invoke(
            build,
            [
                "--file",
                str(deck_file),
                "--output",
                str(tmp_path / "out.apkg"),
            ],
        )

        assert result.exit_code == 0
        calls = mock_instance.add_note.call_args_list
        assert "id::test_123" in calls[0][1]["tags"]
        assert "basic" in calls[0][1]["tags"]

    def test_build_empty_config(self, runner, tmp_path):
        """Test that empty config section raises ConfigValidationError."""
        deck_data = {
            "config": None,
            "data": [{"front": "Q", "back": "A"}],
        }
        deck_file = tmp_path / "deck.yaml"
        deck_file.write_text(yaml.dump(deck_data), encoding="utf-8")

        result = runner.invoke(
            build,
            [
                "--file",
                str(deck_file),
                "--output",
                str(tmp_path / "out.apkg"),
            ],
        )

        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_build_empty_data(self, runner, tmp_path):
        """Test that empty data section raises DataValidationError."""
        deck_data = {
            "config": {
                "name": "Test",
                "fields": ["Front"],
                "templates": [
                    {"name": "Card 1", "qfmt": "{{Front}}", "afmt": "{{Front}}"}
                ],
            },
            "data": None,
        }
        deck_file = tmp_path / "deck.yaml"
        deck_file.write_text(yaml.dump(deck_data), encoding="utf-8")

        result = runner.invoke(
            build,
            [
                "--file",
                str(deck_file),
                "--output",
                str(tmp_path / "out.apkg"),
            ],
        )

        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_build_nonexistent_file(self, runner):
        """Test that nonexistent deck file is handled."""
        result = runner.invoke(
            build,
            [
                "--file",
                "nonexistent.yaml",
                "--output",
                "output.apkg",
            ],
        )

        assert result.exit_code != 0

    def test_build_default_output_path(self, runner, temp_files):
        """Test that build uses default output path when not specified."""
        with patch("anki_yaml_tool.cli.AnkiBuilder") as mock_builder:
            mock_instance = Mock()
            mock_builder.return_value = mock_instance

            result = runner.invoke(
                build,
                [
                    "--file",
                    temp_files["file"],
                ],
            )

            assert result.exit_code == 0
            # Check that write_to_file was called with Path("deck.apkg")
            call_args = mock_instance.write_to_file.call_args[0]
            assert call_args[0] == Path("deck.apkg")

    def test_build_default_deck_name(self, runner, temp_files):
        """Test that build uses default deck name when not specified."""
        with patch("anki_yaml_tool.cli.AnkiBuilder") as mock_builder:
            mock_instance = Mock()
            mock_builder.return_value = mock_instance

            result = runner.invoke(
                build,
                [
                    "--file",
                    temp_files["file"],
                ],
            )

            assert result.exit_code == 0
            assert "Building deck 'Generated Deck'" in result.output
            mock_builder.assert_called_once()
            assert mock_builder.call_args[0][0] == "Generated Deck"

    @patch("anki_yaml_tool.cli.AnkiBuilder")
    def test_build_handles_deck_build_error(self, mock_builder, runner, temp_files):
        """Test that DeckBuildError is handled gracefully."""
        mock_builder.side_effect = DeckBuildError("Build failed")

        result = runner.invoke(
            build,
            [
                "--file",
                temp_files["file"],
            ],
        )

        assert result.exit_code == 1
        assert "Error: Build failed" in result.output

    def test_build_handles_unexpected_error(self, runner, temp_files):
        """Test that unexpected errors are handled."""
        with patch("anki_yaml_tool.cli.AnkiBuilder") as mock_builder:
            mock_builder.side_effect = Exception("Unexpected error")

            result = runner.invoke(
                build,
                [
                    "--file",
                    temp_files["file"],
                ],
            )

            assert result.exit_code == 1
            assert "Unexpected error" in result.output

    @patch("anki_yaml_tool.cli.AnkiBuilder")
    def test_build_case_insensitive_fields(self, mock_builder, runner, tmp_path):
        """Test that field matching is case-insensitive.

        Ensures that data keys with different casing than field names
        are properly matched (e.g., 'Concept' field matches 'concept' data key).
        """
        mock_instance = Mock()
        mock_builder.return_value = mock_instance

        # Define fields with capitalized names
        deck_data = {
            "config": {
                "name": "Test Model",
                "fields": ["Concept", "Code", "Language"],
                "templates": [
                    {
                        "name": "Card 1",
                        "qfmt": "{{Concept}}",
                        "afmt": "{{Code}} {{Language}}",
                    }
                ],
            },
            # Use capitalized keys in data (matching field names exactly)
            "data": [
                {
                    "Concept": "List Comprehension",
                    "Code": "[x**2 for x in nums]",
                    "Language": "python",
                }
            ],
        }

        deck_file = tmp_path / "deck.yaml"
        deck_file.write_text(yaml.dump(deck_data), encoding="utf-8")

        result = runner.invoke(
            build,
            [
                "--file",
                str(deck_file),
                "--output",
                str(tmp_path / "out.apkg"),
            ],
        )

        assert result.exit_code == 0

        # Verify that add_note was called with correct field values
        calls = mock_instance.add_note.call_args_list
        assert len(calls) == 1

        # Check that field values were correctly extracted
        field_values = calls[0][0][0]
        assert field_values[0] == "List Comprehension"
        assert field_values[1] == "[x**2 for x in nums]"
        assert field_values[2] == "python"


class TestValidateCommand:
    """Tests for the validate command."""

    def test_validate_successful(self, runner, temp_files):
        """Test successful validation."""
        result = runner.invoke(
            validate,
            ["--file", temp_files["file"]],
        )
        assert result.exit_code == 0
        assert "Validation passed successfully!" in result.output

    def test_validate_with_warnings(self, runner, tmp_path):
        """Test validation with warnings (missing fields)."""
        deck_data = {
            "config": {
                "name": "Model",
                "fields": ["Front", "Back"],
                "templates": [{"name": "T", "qfmt": "{{Front}}", "afmt": "{{Back}}"}],
            },
            "data": [{"front": "Q1"}],  # Missing 'back' field
        }

        deck_path = tmp_path / "deck.yaml"
        deck_path.write_text(yaml.dump(deck_data))

        result = runner.invoke(
            validate,
            ["--file", str(deck_path)],
        )
        assert result.exit_code == 0
        assert "Validation passed with warnings." in result.output
        assert "Missing fields: back" in result.output

    def test_validate_strict_mode(self, runner, tmp_path):
        """Test validation strict mode failing on warnings."""
        deck_data = {
            "config": {
                "name": "Model",
                "fields": ["Front", "Back"],
                "templates": [{"name": "T", "qfmt": "{{Front}}", "afmt": "{{Back}}"}],
            },
            "data": [{"front": "Q1"}],
        }

        deck_path = tmp_path / "deck.yaml"
        deck_path.write_text(yaml.dump(deck_data))

        result = runner.invoke(
            validate,
            ["--file", str(deck_path), "--strict"],
        )
        assert result.exit_code != 0
        assert "Validation failed due to warnings in strict mode." in result.output

    def test_validate_unclosed_html(self, runner, tmp_path):
        """Test validation warning for unclosed HTML tags."""
        deck_data = {
            "config": {
                "name": "Model",
                "fields": ["F"],
                "templates": [{"name": "T", "qfmt": "{{F}}", "afmt": "{{F}}"}],
            },
            "data": [{"f": "<b>Bold text"}],  # Unclosed <b>
        }

        deck_path = tmp_path / "deck.yaml"
        deck_path.write_text(yaml.dump(deck_data))

        result = runner.invoke(
            validate,
            ["--file", str(deck_path)],
        )
        assert result.exit_code == 0
        assert "Unclosed tag: <b>" in result.output

    def test_validate_duplicate_ids(self, runner, tmp_path):
        """Test validation warning for duplicate IDs."""
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

        deck_path = tmp_path / "deck.yaml"
        deck_path.write_text(yaml.dump(deck_data))

        result = runner.invoke(
            validate,
            ["--file", str(deck_path)],
        )
        assert result.exit_code == 0
        assert "Duplicate note IDs found:" in result.output
        assert "ID 'dup' appears 2 times" in result.output


class TestPushCommand:
    """Tests for the push command."""

    def test_push_help(self, runner):
        """Test that push command help is accessible."""
        result = runner.invoke(push, ["--help"])
        assert result.exit_code == 0
        assert "Push an .apkg file to a running Anki instance" in result.output

    def test_push_requires_apkg_option(self, runner):
        """Test that push command requires --apkg option."""
        result = runner.invoke(push, [])
        assert result.exit_code != 0

    @patch("anki_yaml_tool.cli.AnkiConnector")
    def test_push_successful(self, mock_connector, runner, tmp_path):
        """Test successful package push."""
        mock_instance = Mock()
        mock_connector.return_value = mock_instance

        apkg_file = tmp_path / "test.apkg"
        apkg_file.write_text("fake apkg", encoding="utf-8")

        result = runner.invoke(push, ["--apkg", str(apkg_file)])

        assert result.exit_code == 0
        assert f"Pushing {apkg_file} to Anki" in result.output
        assert "Successfully imported into Anki" in result.output
        mock_instance.import_package.assert_called_once_with(Path(apkg_file))
        mock_instance.sync.assert_not_called()

    @patch("anki_yaml_tool.cli.AnkiConnector")
    def test_push_with_sync(self, mock_connector, runner, tmp_path):
        """Test push with sync flag."""
        mock_instance = Mock()
        mock_connector.return_value = mock_instance

        apkg_file = tmp_path / "test.apkg"
        apkg_file.write_text("fake apkg", encoding="utf-8")

        result = runner.invoke(push, ["--apkg", str(apkg_file), "--sync"])

        assert result.exit_code == 0
        assert "Successfully imported into Anki" in result.output
        mock_instance.import_package.assert_called_once()
        mock_instance.sync.assert_called_once()

    def test_push_nonexistent_file(self, runner):
        """Test that push handles nonexistent .apkg file."""
        result = runner.invoke(push, ["--apkg", "nonexistent.apkg"])
        assert result.exit_code != 0

    @patch("anki_yaml_tool.cli.AnkiConnector")
    def test_push_handles_ankiconnect_error(self, mock_connector, runner, tmp_path):
        """Test that AnkiConnectError is handled gracefully."""
        mock_instance = Mock()
        mock_instance.import_package.side_effect = AnkiConnectError("Connection failed")
        mock_connector.return_value = mock_instance

        apkg_file = tmp_path / "test.apkg"
        apkg_file.write_text("fake apkg", encoding="utf-8")

        result = runner.invoke(push, ["--apkg", str(apkg_file)])

        assert result.exit_code == 1
        assert "Error: Connection failed" in result.output

    @patch("anki_yaml_tool.cli.AnkiConnector")
    def test_push_handles_sync_error(self, mock_connector, runner, tmp_path):
        """Test that sync errors are handled."""
        mock_instance = Mock()
        mock_instance.sync.side_effect = AnkiConnectError("Sync failed")
        mock_connector.return_value = mock_instance

        apkg_file = tmp_path / "test.apkg"
        apkg_file.write_text("fake apkg", encoding="utf-8")

        result = runner.invoke(push, ["--apkg", str(apkg_file), "--sync"])

        assert result.exit_code == 1
        assert "Error: Sync failed" in result.output

    @patch("anki_yaml_tool.cli.AnkiConnector")
    def test_push_handles_unexpected_error(self, mock_connector, runner, tmp_path):
        """Test that unexpected errors are handled."""
        mock_instance = Mock()
        mock_instance.import_package.side_effect = Exception("Unexpected error")
        mock_connector.return_value = mock_instance

        apkg_file = tmp_path / "test.apkg"
        apkg_file.write_text("fake apkg", encoding="utf-8")

        result = runner.invoke(push, ["--apkg", str(apkg_file)])

        assert result.exit_code == 1
        assert "Unexpected error" in result.output
