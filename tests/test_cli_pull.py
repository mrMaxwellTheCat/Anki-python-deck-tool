"""Tests for the CLI pull command."""

from unittest.mock import patch

from anki_yaml_tool.cli import cli
from click.testing import CliRunner


def test_pull_list_decks(monkeypatch):
    runner = CliRunner()

    with patch(
        "anki_yaml_tool.core.connector.AnkiConnector.get_deck_names"
    ) as mock_get:
        mock_get.return_value = ["Deck A", "Deck B"]
        result = runner.invoke(cli, ["pull", "--list-decks"])

    assert result.exit_code == 0
    assert "Deck A" in result.output
    assert "Deck B" in result.output


def test_pull_deck_exports(monkeypatch, tmp_path):
    runner = CliRunner()

    # Patch exporter to avoid network operations
    with patch("anki_yaml_tool.core.exporter.export_deck") as mock_export:
        mock_export.return_value = tmp_path / "My_Deck"
        result = runner.invoke(
            cli, ["pull", "--deck", "My Deck", "--output", str(tmp_path)]
        )

    assert result.exit_code == 0
    assert "Exporting deck: My Deck" in result.output
    mock_export.assert_called_once()
