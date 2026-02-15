"""Tests for the `push-yaml` CLI command."""

from unittest.mock import patch, Mock

from anki_yaml_tool.cli import cli
from click.testing import CliRunner


def test_cli_push_yaml_invokes_pusher(tmp_path):
    runner = CliRunner()
    # Create a temp dir to pass as --dir
    deck_dir = tmp_path / "deck"
    deck_dir.mkdir()
    # Create minimal files
    (deck_dir / "config.yaml").write_text(
        "name: Test\nfields: [Front]\ntemplates: []\n"
    )
    (deck_dir / "data.yaml").write_text("- front: Q\n")

    with (
        patch("anki_yaml_tool.cli.AnkiConnector") as mock_conn_cls,
        patch("anki_yaml_tool.core.pusher.push_deck_from_dir") as mock_push,
    ):
        mock_push.return_value = {"added": 1, "updated": 0, "deleted": 0}
        result = runner.invoke(cli, ["push-yaml", "--dir", str(deck_dir)])

    assert result.exit_code == 0, f"Output: {result.output}"
    mock_push.assert_called_once()
