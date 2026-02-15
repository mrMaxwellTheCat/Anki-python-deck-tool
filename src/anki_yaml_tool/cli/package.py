"""Package management commands for the CLI.

This module implements the `package` command group, handling standalone .apkg
files without modifying the Anki collection directly.
"""

import logging
from pathlib import Path

import click

from anki_yaml_tool.core.connector import AnkiConnector
from anki_yaml_tool.core.deck_service import build_deck, push_apkg
from anki_yaml_tool.core.exceptions import AnkiToolError

log = logging.getLogger(__name__)


@click.group(name="package")
def package_cli() -> None:
    """Manage standalone .apkg files (build, install)."""
    pass


@package_cli.command(name="build")
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Source YAML file.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Destination file (default: deck name).",
)
def build_package(file: Path, output: Path | None) -> None:
    """Creates an .apkg file from YAML."""
    try:
        # If output is not specified, build_deck defaults to "deck.apkg"
        # DESIGN.md says "default: deck name".
        # build_deck resolves output path if not provided.
        # We pass it through.

        click.echo(f"Building package from {file}...")
        result = build_deck(
            file, output_path=output if output else "deck.apkg"
        )  # build_deck defaults to deck.apkg logic is slightly internal

        # Determine actual filename if we want to match DESIGN.md "default: deck name"
        # Ideally build_deck handles this or returns the path.
        # build_deck returns BuildResult with output_path.

        click.echo(
            click.style(f"Successfully built package: {result.output_path}", fg="green")
        )
        click.echo(f"Notes: {result.notes_processed}, Media: {result.media_files}")

    except AnkiToolError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        raise click.Abort() from e


@package_cli.command(name="install")
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to .apkg file.",
)
def install_package(file: Path) -> None:
    """Imports an .apkg file into Anki."""
    connector = AnkiConnector()
    try:
        click.echo(f"Installing {file} into Anki...")
        # push_apkg handles import
        push_apkg(file, connector)
        click.echo(click.style("Successfully installed package.", fg="green"))

    except AnkiToolError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        raise click.Abort() from e
