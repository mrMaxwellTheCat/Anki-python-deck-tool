"""Tests for the CLI module.

This module contains tests for the command-line interface, including
deck and package command groups.
"""

import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml
from anki_yaml_tool.cli_package import build_package, install_package
from click.testing import CliRunner

from anki_yaml_tool.cli import cli
from anki_yaml_tool.core.deck_service import (
    BuildResult,
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
        assert "deck" in result.output
        assert "package" in result.output


class TestPackageBuildCommand:
    """Tests for the package build command."""

    def test_build_help(self, runner):
        """Test that build command help is accessible."""
        result = runner.invoke(cli, ["package", "build", "--help"])
        assert result.exit_code == 0
        assert "Creates an .apkg file from YAML" in result.output

    def test_build_requires_file_option(self, runner):
        """Test that build command requires --file option."""
        result = runner.invoke(build_package, [])
        assert result.exit_code != 0

    @patch("anki_yaml_tool.cli_package.build_deck")
    def test_build_successful(self, mock_build, runner, temp_files):
        """Test successful deck build."""
        mock_build.return_value = BuildResult(
            output_path=Path(temp_files["output"]),
            deck_name="Test Deck",
            notes_processed=2,
        )

        result = runner.invoke(
            build_package,
            [
                "--file",
                temp_files["file"],
                "--output",
                temp_files["output"],
            ],
        )

        assert result.exit_code == 0
        assert "Notes: 2" in result.output
        assert f"Successfully built package: {temp_files['output']}" in result.output

        mock_build.assert_called_once_with(
            Path(temp_files["file"]),
            output_path=Path(temp_files["output"]),
        )

    def test_build_nonexistent_file(self, runner):
        """Test that nonexistent deck file is handled."""
        result = runner.invoke(
            build_package,
            [
                "--file",
                "nonexistent.yaml",
            ],
        )

        assert result.exit_code != 0


class TestPackageInstallCommand:
    """Tests for the package install command."""

    def test_install_help(self, runner):
        """Test that install command help is accessible."""
        result = runner.invoke(cli, ["package", "install", "--help"])
        assert result.exit_code == 0
        assert "Imports an .apkg file into Anki" in result.output

    def test_install_requires_file_option(self, runner):
        """Test that install command requires --file option."""
        result = runner.invoke(install_package, [])
        assert result.exit_code != 0

    @patch("anki_yaml_tool.cli_package.push_apkg")
    @patch("anki_yaml_tool.cli_package.AnkiConnector")
    def test_install_successful(self, mock_connector, mock_push, runner, tmp_path):
        """Test successful package install."""
        mock_instance = Mock()
        mock_connector.return_value = mock_instance

        apkg_file = tmp_path / "test.apkg"
        with zipfile.ZipFile(apkg_file, "w") as zf:
            zf.writestr("dummy", "data")

        result = runner.invoke(install_package, ["--file", str(apkg_file)])

        assert result.exit_code == 0
        assert f"Installing {apkg_file} into Anki" in result.output
        assert "Successfully installed package" in result.output
        mock_push.assert_called_once()
