"""Tests for verbose mode functionality.

This module contains tests for the -v/--verbose and -q/--quiet flags
and the logging configuration.
"""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from anki_yaml_tool.cli import cli
from anki_yaml_tool.core.logging_config import get_logger, setup_logging


@pytest.fixture
def runner():
    """Provide a Click CLI test runner."""
    return CliRunner()


class TestVerboseFlag:
    """Tests for the -v/--verbose flag."""

    def test_verbose_flag_in_help(self, runner):
        """Test that verbose flag appears in help."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "-v" in result.output
        assert "--verbose" in result.output
        assert "verbosity" in result.output.lower()

    def test_quiet_flag_in_help(self, runner):
        """Test that quiet flag appears in help."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "-q" in result.output
        assert "--quiet" in result.output

    def test_verbose_flag_accepted(self, runner):
        """Test that -v flag is accepted."""
        result = runner.invoke(cli, ["-v", "--help"])
        assert result.exit_code == 0

    def test_double_verbose_flag_accepted(self, runner):
        """Test that -vv flag is accepted."""
        result = runner.invoke(cli, ["-vv", "--help"])
        assert result.exit_code == 0

    def test_quiet_flag_accepted(self, runner):
        """Test that -q flag is accepted."""
        result = runner.invoke(cli, ["-q", "--help"])
        assert result.exit_code == 0


class TestLoggingConfiguration:
    """Tests for the logging configuration module."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "anki_yaml_tool.test"

    def test_get_logger_without_name(self):
        """Test get_logger with no name returns package logger."""
        logger = get_logger()
        assert logger is not None
        assert logger.name == "anki_yaml_tool"

    def test_setup_logging_default(self):
        """Test default logging setup (warning level)."""
        import logging

        setup_logging(verbosity=0, quiet=False)
        logger = get_logger()
        assert logger.level == logging.WARNING

    def test_setup_logging_verbose(self):
        """Test verbose logging setup (info level)."""
        import logging

        setup_logging(verbosity=1, quiet=False)
        logger = get_logger()
        assert logger.level == logging.INFO

    def test_setup_logging_debug(self):
        """Test debug logging setup (debug level)."""
        import logging

        setup_logging(verbosity=2, quiet=False)
        logger = get_logger()
        assert logger.level == logging.DEBUG

    def test_setup_logging_quiet(self):
        """Test quiet logging setup (error level only)."""
        import logging

        setup_logging(verbosity=0, quiet=True)
        logger = get_logger()
        assert logger.level == logging.ERROR


class TestVerboseBuildCommand:
    """Tests for verbose output in build command."""

    @patch("anki_yaml_tool.cli.AnkiBuilder")
    def test_build_with_verbose_shows_info(self, mock_builder, runner, tmp_path):
        """Test that build with -v shows info messages."""
        import yaml

        deck_data = {
            "config": {
                "name": "Test Model",
                "fields": ["Front", "Back"],
                "templates": [
                    {"name": "Card 1", "qfmt": "{{Front}}", "afmt": "{{Back}}"}
                ],
            },
            "data": [{"front": "Q", "back": "A"}],
        }

        deck_file = tmp_path / "deck.yaml"
        deck_file.write_text(yaml.dump(deck_data), encoding="utf-8")

        result = runner.invoke(
            cli,
            [
                "-v",
                "build",
                "--file",
                str(deck_file),
                "--output",
                str(tmp_path / "out.apkg"),
            ],
        )

        assert result.exit_code == 0
        # With -v, we should see info-level log messages
        assert "Loading deck file" in result.output or "Building deck" in result.output

    @patch("anki_yaml_tool.cli.AnkiBuilder")
    def test_build_quiet_suppresses_output(self, mock_builder, runner, tmp_path):
        """Test that build with -q suppresses non-essential output."""
        import yaml

        deck_data = {
            "config": {
                "name": "Test Model",
                "fields": ["Front", "Back"],
                "templates": [
                    {"name": "Card 1", "qfmt": "{{Front}}", "afmt": "{{Back}}"}
                ],
            },
            "data": [{"front": "Q", "back": "A"}],
        }

        deck_file = tmp_path / "deck.yaml"
        deck_file.write_text(yaml.dump(deck_data), encoding="utf-8")

        result = runner.invoke(
            cli,
            [
                "-q",
                "build",
                "--file",
                str(deck_file),
                "--output",
                str(tmp_path / "out.apkg"),
            ],
        )

        assert result.exit_code == 0
        # Quiet mode should not show verbose log messages
        # but will still show essential click.echo messages
        assert "Successfully created" in result.output
