"""Command-line interface for Anki Python Deck Tool.

This module provides the CLI entry points for building and pushing Anki decks.
"""

from importlib.metadata import version
from pathlib import Path

import click

from anki_tool.core.builder import AnkiBuilder
from anki_tool.core.config import load_deck_data, load_model_config
from anki_tool.core.connector import AnkiConnector
from anki_tool.core.exceptions import (
    AnkiConnectError,
    ConfigValidationError,
    DataValidationError,
    DeckBuildError,
)


@click.group()
@click.version_option(version=version("anki-yaml-tool"), prog_name="anki-yaml-tool")
def cli():
    """Anki Python Deck Tool - Build and push decks from YAML."""
    pass


@cli.command()
@click.option(
    "--data",
    type=click.Path(exists=True),
    required=True,
    help="Path to data YAML file",
)
@click.option(
    "--config",
    type=click.Path(exists=True),
    required=True,
    help="Path to model config YAML",
)
@click.option(
    "--output",
    type=click.Path(),
    default="deck.apkg",
    help="Output .apkg path",
)
@click.option("--deck-name", default="Generated Deck", help="Name of the Anki deck")
def build(data, config, output, deck_name):
    """Build an .apkg file from YAML data."""
    click.echo(f"Building deck '{deck_name}'...")

    try:
        # Load configuration and data using the config module
        model_config = load_model_config(config)
        items = load_deck_data(data)

        builder = AnkiBuilder(deck_name, model_config)

        for item in items:
            # Map YAML keys to model fields in order
            field_values = [
                str(item.get(f.lower(), "")) for f in model_config["fields"]
            ]

            # Get tags, ensuring it's always a list
            tags_raw = item.get("tags", [])
            tags: list[str] = (
                tags_raw if isinstance(tags_raw, list) else [str(tags_raw)]
            )

            if "id" in item:
                tags.append(f"id::{item['id']}")

            builder.add_note(field_values, tags=tags)

        builder.write_to_file(Path(output))
        click.echo(f"Successfully created {output}")

    except (ConfigValidationError, DataValidationError, DeckBuildError) as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        raise click.Abort() from e


@cli.command()
@click.option(
    "--apkg",
    type=click.Path(exists=True),
    required=True,
    help="Path to .apkg file",
)
@click.option("--sync", is_flag=True, help="Sync with AnkiWeb after import")
def push(apkg, sync):
    """Push an .apkg file to a running Anki instance."""
    click.echo(f"Pushing {apkg} to Anki...")
    connector = AnkiConnector()

    try:
        connector.import_package(Path(apkg))
        if sync:
            connector.sync()
        click.echo("Successfully imported into Anki")
    except AnkiConnectError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        raise click.Abort() from e


def main():
    cli()


if __name__ == "__main__":
    main()
