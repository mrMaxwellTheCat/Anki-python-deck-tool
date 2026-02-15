"""Tests for the CLI module.

This module contains tests for the command-line interface, including
build and push commands.
"""

import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml
from anki_yaml_tool.cli import build, cli, push, validate
from anki_yaml_tool.core.deck_service import (
    BuildResult,
)
from anki_yaml_tool.core.exceptions import (
    AnkiConnectError,
    DeckBuildError,
)
from click.testing import CliRunner


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

    @patch("anki_yaml_tool.cli.build_deck")
    def test_build_successful(self, mock_build, runner, temp_files):
        """Test successful deck build."""
        mock_build.return_value = BuildResult(
            output_path=Path(temp_files["output"]),
            deck_name="Test Deck",
            notes_processed=2,
        )

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
        assert "Deck 'Test Deck'" in result.output
        assert "2 notes" in result.output
        assert f"Successfully created {temp_files['output']}" in result.output

        mock_build.assert_called_once_with(
            deck_path=temp_files["file"],
            output_path=temp_files["output"],
            deck_name_override="Test Deck",
            media_dir_override=None,
        )

    @patch("anki_yaml_tool.cli.build_deck")
    def test_build_with_tags(self, mock_build, runner, temp_files):
        """Test that build completes successfully with tagged notes."""
        mock_build.return_value = BuildResult(
            output_path=Path(temp_files["output"]),
            deck_name="Test",
            notes_processed=2,
        )

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
        assert "2 notes" in result.output

    @patch("anki_yaml_tool.cli.build_deck")
    def test_build_with_id_tag(self, mock_build, runner, tmp_path):
        """Test that build succeeds with notes that have IDs."""
        mock_build.return_value = BuildResult(
            output_path=tmp_path / "out.apkg",
            deck_name="Test",
            notes_processed=1,
        )

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
        mock_build.assert_called_once()

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

    @patch("anki_yaml_tool.cli.build_deck")
    def test_build_default_output_path(self, mock_build, runner, temp_files):
        """Test that build uses default output path when not specified."""
        mock_build.return_value = BuildResult(
            output_path=Path("deck.apkg"),
            deck_name="Test",
            notes_processed=2,
        )

        result = runner.invoke(
            build,
            [
                "--file",
                temp_files["file"],
            ],
        )

        assert result.exit_code == 0
        call_kwargs = mock_build.call_args[1]
        assert call_kwargs["output_path"] == "deck.apkg"

    @patch("anki_yaml_tool.cli.build_deck")
    def test_build_default_deck_name(self, mock_build, runner, temp_files):
        """Test that build delegates deck name resolution to deck_service."""
        expected_name = Path(temp_files["file"]).parent.name
        mock_build.return_value = BuildResult(
            output_path=Path("deck.apkg"),
            deck_name=expected_name,
            notes_processed=2,
        )

        result = runner.invoke(
            build,
            [
                "--file",
                temp_files["file"],
            ],
        )

        assert result.exit_code == 0
        assert f"Deck '{expected_name}'" in result.output
        # Verify deck_name_override is None when not specified
        call_kwargs = mock_build.call_args[1]
        assert call_kwargs["deck_name_override"] is None

    @patch("anki_yaml_tool.cli.build_deck")
    def test_build_handles_deck_build_error(self, mock_build, runner, temp_files):
        """Test that DeckBuildError is handled gracefully."""
        mock_build.side_effect = DeckBuildError("Build failed")

        result = runner.invoke(
            build,
            [
                "--file",
                temp_files["file"],
            ],
        )

        assert result.exit_code == 1
        assert "Error: Build failed" in result.output

    @patch("anki_yaml_tool.cli.build_deck")
    def test_build_handles_unexpected_error(self, mock_build, runner, temp_files):
        """Test that unexpected errors are handled."""
        mock_build.side_effect = Exception("Unexpected error")

        result = runner.invoke(
            build,
            [
                "--file",
                temp_files["file"],
            ],
        )

        assert result.exit_code == 1
        assert "Unexpected error" in result.output

    @patch("anki_yaml_tool.cli.build_deck")
    def test_build_case_insensitive_fields(self, mock_build, runner, tmp_path):
        """Test that build delegates to deck_service (which handles case insensitivity)."""
        mock_build.return_value = BuildResult(
            output_path=tmp_path / "out.apkg",
            deck_name="Test",
            notes_processed=1,
        )

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
        assert "1 notes" in result.output
        mock_build.assert_called_once()


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
        assert "Duplicate ID 'dup' appears 2 times" in result.output


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

    @patch("anki_yaml_tool.cli.push_apkg")
    @patch("anki_yaml_tool.cli.AnkiConnector")
    def test_push_successful(self, mock_connector, mock_push, runner, tmp_path):
        """Test successful package push."""
        mock_instance = Mock()
        mock_connector.return_value = mock_instance

        apkg_file = tmp_path / "test.apkg"
        with zipfile.ZipFile(apkg_file, "w") as zf:
            zf.writestr("dummy", "data")

        result = runner.invoke(push, ["--apkg", str(apkg_file)])

        assert result.exit_code == 0
        assert f"Pushing {apkg_file} to Anki" in result.output
        assert "Successfully imported into Anki" in result.output
        mock_push.assert_called_once()

    @patch("anki_yaml_tool.cli.push_apkg")
    @patch("anki_yaml_tool.cli.AnkiConnector")
    def test_push_with_sync(self, mock_connector, mock_push, runner, tmp_path):
        """Test push with sync flag."""
        mock_instance = Mock()
        mock_connector.return_value = mock_instance

        apkg_file = tmp_path / "test.apkg"
        with zipfile.ZipFile(apkg_file, "w") as zf:
            zf.writestr("dummy", "data")

        result = runner.invoke(push, ["--apkg", str(apkg_file), "--sync"])

        assert result.exit_code == 0
        assert "Successfully imported into Anki" in result.output
        mock_push.assert_called_once()
        # Verify sync=True was passed
        call_kwargs = mock_push.call_args[1]
        assert call_kwargs["sync"] is True

    def test_push_nonexistent_file(self, runner):
        """Test that push handles nonexistent .apkg file."""
        result = runner.invoke(push, ["--apkg", "nonexistent.apkg"])
        assert result.exit_code != 0

    @patch("anki_yaml_tool.cli.push_apkg")
    @patch("anki_yaml_tool.cli.AnkiConnector")
    def test_push_handles_ankiconnect_error(
        self, mock_connector, mock_push, runner, tmp_path
    ):
        """Test that AnkiConnectError is handled gracefully."""
        mock_push.side_effect = AnkiConnectError("Connection failed")
        mock_connector.return_value = Mock()

        apkg_file = tmp_path / "test.apkg"
        with zipfile.ZipFile(apkg_file, "w") as zf:
            zf.writestr("dummy", "data")

        result = runner.invoke(push, ["--apkg", str(apkg_file)])

        assert result.exit_code == 1
        assert "Error: Connection failed" in result.output

    @patch("anki_yaml_tool.cli.push_apkg")
    @patch("anki_yaml_tool.cli.AnkiConnector")
    def test_push_handles_sync_error(self, mock_connector, mock_push, runner, tmp_path):
        """Test that sync errors are handled."""
        mock_push.side_effect = AnkiConnectError("Sync failed")
        mock_connector.return_value = Mock()

        apkg_file = tmp_path / "test.apkg"
        with zipfile.ZipFile(apkg_file, "w") as zf:
            zf.writestr("dummy", "data")

        result = runner.invoke(push, ["--apkg", str(apkg_file), "--sync"])

        assert result.exit_code == 1
        assert "Error: Sync failed" in result.output

    @patch("anki_yaml_tool.cli.push_apkg")
    @patch("anki_yaml_tool.cli.AnkiConnector")
    def test_push_handles_unexpected_error(
        self, mock_connector, mock_push, runner, tmp_path
    ):
        """Test that unexpected errors are handled."""
        mock_push.side_effect = Exception("Unexpected error")
        mock_connector.return_value = Mock()

        apkg_file = tmp_path / "test.apkg"
        with zipfile.ZipFile(apkg_file, "w") as zf:
            zf.writestr("dummy", "data")

        result = runner.invoke(push, ["--apkg", str(apkg_file)])

        assert result.exit_code == 1
        assert "Unexpected error" in result.output
