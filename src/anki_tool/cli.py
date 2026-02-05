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
    MediaMissingError,
)
from anki_tool.core.media import (
    discover_media_files,
    get_media_references,
    validate_media_file,
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
@click.option(
    "--media-dir",
    type=click.Path(exists=True),
    help="Directory containing media files to include",
)
def build(data, config, output, deck_name, media_dir):
    """Build an .apkg file from YAML data."""
    click.echo(f"Building deck '{deck_name}'...")

    try:
        # Load configuration and data using the config module
        model_config = load_model_config(config)
        items = load_deck_data(data)

        builder = AnkiBuilder(deck_name, model_config)

        # Track all media references found in notes
        all_media_refs: set[str] = set()

        for item in items:
            # Map YAML keys to model fields in order
            field_values = [
                str(item.get(f.lower(), "")) for f in model_config["fields"]
            ]

            # Extract media references from all field values
            for field_value in field_values:
                refs = get_media_references(field_value)
                all_media_refs.update(refs)

            # Get tags, ensuring it's always a list
            tags_raw = item.get("tags", [])
            tags: list[str] = (
                tags_raw if isinstance(tags_raw, list) else [str(tags_raw)]
            )

            if "id" in item:
                tags.append(f"id::{item['id']}")

            builder.add_note(field_values, tags=tags)

        # Add media files if media directory is provided
        if media_dir:
            media_path = Path(media_dir)
            click.echo(f"Discovering media files in {media_path}...")

            # Discover all media files in the directory
            discovered_files = discover_media_files(media_path)
            click.echo(f"Found {len(discovered_files)} media files")

            # Add all discovered media files
            for media_file in discovered_files:
                builder.add_media(media_file)

            # Validate that all referenced media files exist
            if all_media_refs:
                click.echo(f"Validating {len(all_media_refs)} media references...")
                missing_refs = []

                for ref in all_media_refs:
                    ref_path = media_path / ref
                    try:
                        validate_media_file(ref_path)
                    except MediaMissingError:
                        missing_refs.append(ref)

                if missing_refs:
                    msg = (
                        f"Warning: {len(missing_refs)} "
                        "referenced media files not found:"
                    )
                    click.echo(msg, err=True)
                    for ref in missing_refs:
                        click.echo(f"  - {ref}", err=True)

        elif all_media_refs:
            click.echo(
                f"Warning: Found {len(all_media_refs)} media references "
                "but no --media-dir specified",
                err=True,
            )

        builder.write_to_file(Path(output))
        click.echo(f"Successfully created {output}")

    except (
        ConfigValidationError,
        DataValidationError,
        DeckBuildError,
        MediaMissingError,
    ) as e:
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
