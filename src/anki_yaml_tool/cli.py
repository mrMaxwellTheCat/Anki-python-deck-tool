"""Command-line interface for Anki Python Deck Tool.

This module provides the CLI entry points for building and pushing Anki decks.
"""

from importlib.metadata import version
from pathlib import Path

import click

from anki_yaml_tool.core.builder import AnkiBuilder
from anki_yaml_tool.core.config import load_deck_data, load_model_config
from anki_yaml_tool.core.connector import AnkiConnector
from anki_yaml_tool.core.exceptions import (
    AnkiConnectError,
    ConfigValidationError,
    DataValidationError,
    DeckBuildError,
    MediaMissingError,
)
from anki_yaml_tool.core.media import (
    discover_media_files,
    get_media_references,
    validate_media_file,
)
from anki_yaml_tool.core.validators import (
    check_duplicate_ids,
    validate_html_tags,
    validate_note_fields,
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
    multiple=True,
    help="Path to model config YAML (can be used multiple times)",
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
        # Load all configurations
        model_configs = [load_model_config(cfg) for cfg in config]
        items = load_deck_data(data)

        builder = AnkiBuilder(deck_name, model_configs)

        # Map model names to their field lists for easy lookup
        model_fields_map = {cfg["name"]: cfg["fields"] for cfg in model_configs}
        first_model_name = model_configs[0]["name"]

        # Track all media references found in notes
        all_media_refs: set[str] = set()

        for item in items:
            # Determine which model to use for this note
            # Look for 'model' or 'type' field, default to the first model
            target_model_name = item.get("model", item.get("type", first_model_name))
            if not isinstance(target_model_name, str):
                target_model_name = str(target_model_name)

            if target_model_name not in model_fields_map:
                click.echo(
                    f"Warning: Model '{target_model_name}' not found. "
                    f"Available: {', '.join(model_fields_map.keys())}. "
                    f"Defaulting to '{first_model_name}'.",
                    err=True,
                )
                target_model_name = first_model_name

            fields = model_fields_map[target_model_name]

            # Map YAML keys to model fields in order
            field_values = [str(item.get(f.lower(), "")) for f in fields]

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

            builder.add_note(field_values, tags=tags, model_name=target_model_name)

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
    "--data",
    type=click.Path(exists=True),
    required=True,
    help="Path to data YAML file",
)
@click.option(
    "--config",
    type=click.Path(exists=True),
    required=True,
    multiple=True,
    help="Path to model config YAML",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Fail on warnings (e.g., missing fields or invalid HTML)",
)
def validate(data, config, strict):
    """Validate YAML data and configuration without building."""
    click.echo("Validating configuration and data...")
    has_errors = False
    has_warnings = False

    try:
        # 1. Load and validate configurations
        model_configs = []
        for cfg_path in config:
            try:
                model_configs.append(load_model_config(cfg_path))
            except ConfigValidationError as e:
                click.echo(f"Config Error ({cfg_path}): {e}", err=True)
                has_errors = True

        if has_errors:
            click.echo("Validation failed due to configuration errors.", err=True)
            raise click.Abort()

        # 2. Load data
        try:
            items = load_deck_data(data)
        except DataValidationError as e:
            click.echo(f"Data Error: {e}", err=True)
            raise click.Abort() from e

        # 3. Perform consistency checks
        model_names = {cfg["name"] for cfg in model_configs}
        model_fields_map = {cfg["name"]: cfg["fields"] for cfg in model_configs}
        first_model_name = model_configs[0]["name"]

        # Check for duplicate IDs
        duplicates = check_duplicate_ids(items)
        if duplicates:
            msg = "Duplicate note IDs found:"
            click.echo(click.style(msg, fg="yellow"), err=True)
            for id_, count in duplicates.items():
                click.echo(f"  - ID '{id_}' appears {count} times", err=True)
            has_warnings = True

        # Validate each note
        for i, item in enumerate(items):
            note_ref = f"Note #{i + 1}"
            if "id" in item:
                note_ref += f" (ID: {item['id']})"

            # Check model existence
            target_model_name_raw = item.get(
                "model", item.get("type", first_model_name)
            )
            target_model_name = (
                target_model_name_raw
                if isinstance(target_model_name_raw, str)
                else str(target_model_name_raw)
            )

            if target_model_name not in model_names:
                click.echo(
                    click.style(
                        f"Error in {note_ref}: Model '{target_model_name}' not found.",
                        fg="red",
                    ),
                    err=True,
                )
                has_errors = True
                continue

            # Check fields
            fields = model_fields_map[target_model_name]
            is_valid, missing = validate_note_fields(
                item, fields, validate_missing="warn"
            )
            if missing:
                click.echo(
                    click.style(
                        f"Warning in {note_ref}: Missing fields: {', '.join(missing)}",
                        fg="yellow",
                    ),
                    err=True,
                )
                has_warnings = True

            # HTML Validation
            for field in fields:
                content = str(item.get(field.lower(), ""))
                html_warnings = validate_html_tags(content)
                for warning in html_warnings:
                    click.echo(
                        click.style(
                            f"Warning in {note_ref}, field '{field}': {warning}",
                            fg="yellow",
                        ),
                        err=True,
                    )
                    has_warnings = True

        if has_errors:
            click.echo(
                click.style("\nValidation failed with errors.", fg="red"), err=True
            )
            raise click.Abort()

        if strict and has_warnings:
            click.echo(
                click.style(
                    "\nValidation failed due to warnings in strict mode.", fg="red"
                ),
                err=True,
            )
            raise click.Abort()

        if has_warnings:
            click.echo(click.style("\nValidation passed with warnings.", fg="yellow"))
        else:
            click.echo(click.style("\nValidation passed successfully!", fg="green"))

    except (ConfigValidationError, DataValidationError) as e:
        click.echo(f"Error: {e}", err=True)
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
