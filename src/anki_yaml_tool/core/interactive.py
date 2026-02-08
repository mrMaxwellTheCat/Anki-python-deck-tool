"""Simple terminal-based interactive UI for `anki-yaml-tool`.

Provides a guided menu to let users list decks, pull a deck, build a .apkg
from a deck YAML, push an .apkg, or exit. The implementation keeps IO
separable for easier testing.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import click

from anki_yaml_tool.core.connector import AnkiConnector
from anki_yaml_tool.core.exceptions import AnkiConnectError
from anki_yaml_tool.core.exporter import export_deck


def _print_menu() -> None:
    click.echo("\n=== Anki YAML Tool — Interactive ===")
    click.echo("Choose an action:")
    click.echo("  1) List decks")
    click.echo("  2) Pull a deck to YAML")
    click.echo("  3) Build a .apkg from deck YAML file")
    click.echo("  4) Push a .apkg to Anki")
    click.echo("  x) Exit")


def _prompt(prompt_text: str, input_func: Callable[[], str]) -> str:
    click.echo(prompt_text, nl=False)
    try:
        return input_func().strip()
    except EOFError:
        # Cleanly abort interactive mode when stdin is closed
        raise click.Abort("Input closed") from None


def run_interactive(input_func: Callable[[], str] | None = None) -> None:
    """Run the interactive terminal UI.

    Args:
        input_func: Optional callable to read a user line. Defaults to built-in
            `input()` (wrapped) to make testing easier.
    """
    if input_func is None:
        # wrap built-in input to match Callable[[], str]
        def _default_input() -> str:
            return input()

        input_func = _default_input

    connector = AnkiConnector()

    try:
        while True:
            _print_menu()
            choice = _prompt("Enter selection: ", input_func)

            if choice in ("x", "X"):
                click.echo("Goodbye!")
                return

            if choice == "1":
                try:
                    decks = connector.get_deck_names()
                    click.echo("Available decks:")
                    for d in decks:
                        click.echo(f"  - {d}")
                except AnkiConnectError as e:
                    click.echo(f"Error contacting Anki: {e}", err=True)

            elif choice == "2":
                deck_name = _prompt("Deck name to pull: ", input_func)
                output = _prompt("Output directory (default: ./): ", input_func)
                if not output:
                    output = "."
                out_path = Path(output)
                try:
                    click.echo(f"Exporting '{deck_name}' to {out_path}...")
                    deck_path = export_deck(connector, deck_name, out_path)
                    click.echo(f"Exported to {deck_path}")
                except AnkiConnectError as e:
                    click.echo(f"Error pulling deck: {e}", err=True)
                except (click.Abort, OSError, FileNotFoundError) as e:
                    # Expected/known errors -- report to user but don't hide
                    # unexpected programmer errors.
                    click.echo(f"Error: {e}", err=True)

            elif choice == "3":
                deck_file = _prompt("Path to deck YAML file: ", input_func)
                if not deck_file:
                    click.echo("No file provided", err=True)
                    continue
                # Reuse existing build command logic by invoking the CLI programmatically
                click.echo("Building .apkg from YAML...")
                try:
                    # Import here to avoid circular imports at module level
                    from anki_yaml_tool.cli import build

                    # Click's programmatic invocation of a command requires a context,
                    # but for simplicity, call the function directly.
                    build(
                        file=deck_file,
                        output="deck.apkg",
                        deck_name=None,
                        media_dir=None,
                    )
                    click.echo("Build completed: deck.apkg")
                except (FileNotFoundError, click.Abort) as e:
                    click.echo(f"Build failed: {e}", err=True)

            elif choice == "4":
                apkg_path = _prompt("Path to .apkg file to push: ", input_func)
                if not apkg_path:
                    click.echo("No package provided", err=True)
                    continue
                sync_choice = _prompt("Sync after import? (y/N): ", input_func)
                sync = sync_choice.lower().startswith("y")
                try:
                    click.echo(f"Pushing {apkg_path}...")
                    from anki_yaml_tool.cli import push

                    push(apkg=apkg_path, sync=sync)
                    click.echo("Push completed")
                except (FileNotFoundError, AnkiConnectError, click.Abort) as e:
                    click.echo(f"Push failed: {e}", err=True)

            else:
                click.echo("Invalid selection, please try again.")
    except click.Abort as e:
        # Clean exit for EOF/input closure or user abort
        if str(e):
            click.echo(str(e))
        else:
            click.echo("Interactive session aborted.")
        return
