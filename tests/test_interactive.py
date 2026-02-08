"""Tests for the interactive terminal UI."""

from unittest.mock import patch

from anki_yaml_tool.cli import cli
from anki_yaml_tool.core.interactive import run_interactive
from click.testing import CliRunner


def test_run_interactive_list_decks(monkeypatch):
    inputs = ["1", "x"]
    input_iter = iter(inputs)

    class FakeConnector:
        def get_deck_names(self):
            return ["Deck A", "Deck B"]

    # Patch AnkiConnector used inside run_interactive
    with patch(
        "anki_yaml_tool.core.interactive.AnkiConnector", return_value=FakeConnector()
    ):
        # Run interactive with deterministic inputs
        run_interactive(input_func=lambda: next(input_iter))


def test_cli_invoked_without_args_runs_interactive(monkeypatch):
    # Simulate user selecting list decks then exit
    runner = CliRunner()
    input_data = "1\nx\n"

    class FakeConnector:
        def get_deck_names(self):
            return ["Deck A", "Deck B"]

    with patch(
        "anki_yaml_tool.core.interactive.AnkiConnector", return_value=FakeConnector()
    ):
        result = runner.invoke(cli, [], input=input_data)

    assert result.exit_code == 0
    assert "Available decks:" in result.output
    assert "Deck A" in result.output
