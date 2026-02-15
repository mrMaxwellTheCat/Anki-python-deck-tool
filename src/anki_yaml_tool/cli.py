"""Command-line interface for Anki Python Deck Tool.

This module provides the CLI entry points for building and pushing Anki decks.
"""

import fnmatch
import sys
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from importlib.metadata import version
from pathlib import Path
from typing import cast

import click
import yaml

from anki_yaml_tool.core.batch import get_deck_name_from_path
from anki_yaml_tool.core.builder import AnkiBuilder, ModelConfigComplete
from anki_yaml_tool.core.config import load_deck_file
from anki_yaml_tool.core.connector import AnkiConnector
from anki_yaml_tool.core.exceptions import (
    AnkiConnectError,
    ConfigValidationError,
    DataValidationError,
    DeckBuildError,
    MediaMissingError,
)
from anki_yaml_tool.core.logging_config import get_logger, setup_logging
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

# Get logger for this module
log = get_logger("cli")


@click.group(invoke_without_command=True)
@click.version_option(version=version("anki-yaml-tool"), prog_name="anki-yaml-tool")
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity. Use -v for INFO, -vv for DEBUG.",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Suppress all output except errors.",
)
@click.option(
    "--profile",
    "-p",
    help="Configuration profile to use (e.g., dev, prod).",
)
@click.option(
    "--gui",
    "-g",
    is_flag=True,
    help="Launch the graphical user interface (GUI).",
)
@click.pass_context
def cli(
    ctx: click.Context, verbose: int, quiet: bool, profile: str | None, gui: bool
) -> None:
    """Anki Python Deck Tool - Build and push decks from YAML.

    When invoked without a subcommand this will launch a terminal-based
    interactive UI to guide the user. Use --gui to launch the graphical UI.
    """
    # Launch GUI if requested
    if gui:
        from anki_yaml_tool.gui.main import main as gui_main

        sys.exit(gui_main())
    from anki_yaml_tool.core.config_file import load_config
    from anki_yaml_tool.core.interactive import run_interactive

    ctx.ensure_object(dict)

    # Load config file
    config = load_config()
    ctx.obj["config"] = config

    # Get profile-specific or base config
    if profile:
        profile_config = config.get_profile(profile)
        ctx.obj["profile"] = profile
        ctx.obj["profile_config"] = profile_config

        # Apply profile settings if not overridden on command line
        if verbose == 0 and "verbose" in profile_config:
            verbose = profile_config["verbose"]
        if not quiet and profile_config.get("quiet", False):
            quiet = True

    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    setup_logging(verbosity=verbose, quiet=quiet)

    # If invoked without a subcommand, enter interactive mode
    if ctx.invoked_subcommand is None:
        # run_interactive will perform its own error handling and return
        run_interactive()
        # Exit after interactive finishes
        ctx.exit()


@cli.command()
@click.option(
    "--file",
    type=click.Path(exists=True),
    required=True,
    help="Path to deck YAML file (contains both config and data)",
)
@click.option(
    "--output",
    type=click.Path(),
    default="deck.apkg",
    help="Output .apkg path",
)
@click.option(
    "--deck-name",
    help="Name of the Anki deck (overrides deck file setting)",
)
@click.option(
    "--media-dir",
    type=click.Path(exists=True),
    help="Directory containing media files (overrides deck file setting)",
)
def build(file, output, deck_name, media_dir):
    """Build an .apkg file from YAML deck file."""
    try:
        # Load deck file
        log.info("Loading deck file: %s", file)
        model_config, items, file_deck_name, file_media_dir = load_deck_file(file)
        model_configs = cast(list[ModelConfigComplete], [model_config])
        log.debug("Loaded model config: %s", model_config.get("name", "unknown"))
        log.debug("Found %d notes in data section", len(items))

        # Use provided deck-name or fall back to file deck-name
        final_deck_name = deck_name if deck_name is not None else file_deck_name

        # Final fallback to filename if no name provided anywhere
        if final_deck_name is None:
            file_path = Path(file)
            if file_path.stem == "deck":
                final_deck_name = file_path.parent.name or "Deck"
            else:
                final_deck_name = file_path.stem

        # Use provided media-dir or fall back to file media-dir
        # Convert CLI string path to Path object for AnkiBuilder
        media_folder: Path | None = Path(media_dir) if media_dir else file_media_dir

        click.echo(f"Building deck '{final_deck_name}'...")
        log.info("Output file: %s", output)
        builder = AnkiBuilder(final_deck_name, model_configs, media_folder)

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

            # Create a case-insensitive lookup dictionary
            # Convert all data keys to lowercase for matching
            item_lower = {k.lower(): v for k, v in item.items()}

            # Map YAML keys to model fields in order
            field_values = [str(item_lower.get(f.lower(), "")) for f in fields]

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
            log.debug(
                "Added note with model '%s' and %d tags", target_model_name, len(tags)
            )

        log.info("Processed %d notes", len(items))

        # Add media files if media directory is provided
        if media_folder:
            media_path = media_folder
            click.echo(f"Discovering media files in {media_path}...")

            # Discover all media files in the directory
            discovered_files = discover_media_files(media_path)
            click.echo(f"Found {len(discovered_files)} media files")

            # Add all discovered media files
            for media_file in discovered_files:
                builder.add_media(media_file)
                log.debug("Added media file: %s", media_file.name)

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
    "--file",
    type=click.Path(exists=True),
    required=True,
    help="Path to deck YAML file (contains both config and data)",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Fail on warnings (e.g., missing fields or invalid HTML)",
)
def validate(file, strict):
    """Validate YAML deck file without building."""
    click.echo("Validating configuration and data...")
    log.info("Validating file: %s", file)
    log.debug("Strict mode: %s", strict)
    has_errors = False
    has_warnings = False

    try:
        # Load deck file
        try:
            log.debug("Loading deck file...")
            model_config, items, _, _ = load_deck_file(file)
            model_configs = [model_config]
            log.info("Loaded %d notes for validation", len(items))
        except (ConfigValidationError, DataValidationError) as e:
            click.echo(f"Error ({file}): {e}", err=True)
            has_errors = True
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
            _is_valid, missing = validate_note_fields(
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
    import base64
    import json
    import zipfile

    click.echo(f"Pushing {apkg} to Anki...")
    log.info("Connecting to AnkiConnect...")
    connector = AnkiConnector()

    try:
        apkg_path = Path(apkg)

        # Extract and store media files from apkg
        with zipfile.ZipFile(apkg_path, "r") as zf:
            if "media" in zf.namelist():
                media_map: dict[str, str] = json.loads(zf.read("media").decode("utf-8"))
                if media_map:
                    click.echo(f"Storing {len(media_map)} media files...")
                    log.info("Extracting and storing %d media files", len(media_map))

                    with click.progressbar(
                        media_map.items(), label="Storing media"
                    ) as items:  # type: ignore
                        for idx, filename in items:
                            try:
                                content = zf.read(idx)
                                encoded = base64.b64encode(content).decode("utf-8")
                                connector.invoke(
                                    "storeMediaFile", filename=filename, data=encoded
                                )
                                log.debug("Stored media file: %s", filename)
                            except KeyError:
                                log.warning("Media file %s not found in apkg", idx)
                            except Exception as e:
                                log.warning("Failed to store %s: %s", filename, e)

        # Import the package
        log.debug("Importing package: %s", apkg)
        connector.import_package(Path(apkg))
        log.info("Package imported successfully")

        if sync:
            log.info("Syncing with AnkiWeb...")
            connector.sync()
            log.debug("Sync completed")

        click.echo("Successfully imported into Anki")
    except AnkiConnectError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        raise click.Abort() from e


@cli.command()
@click.option("--list-decks", is_flag=True, help="List available decks in Anki")
@click.option("--deck", help="Name of the deck to pull")
@click.option("--all-decks", is_flag=True, help="Pull all available decks")
@click.option(
    "--output",
    type=click.Path(),
    default=".",
    help="Output directory for exported decks",
)
def pull(list_decks: bool, deck: str | None, all_decks: bool, output: str) -> None:
    """Pull decks and model definitions from a running Anki instance.

    Examples:
      - List decks: `anki-yaml-tool pull --list-decks`
      - Export a deck: `anki-yaml-tool pull --deck "Spanish" --output ./decks/spanish`
      - Export all decks: `anki-yaml-tool pull --all-decks --output ./decks`
    """
    from anki_yaml_tool.core.exporter import export_deck

    click.echo("Connecting to Anki...")
    connector = AnkiConnector()

    try:
        # Validate mutually exclusive options: --list-decks, --deck, --all-decks
        provided = int(list_decks) + int(bool(deck)) + int(all_decks)
        if provided == 0:
            click.echo(
                "Error: Must specify --deck or --all-decks or use --list-decks",
                err=True,
            )
            raise click.Abort()
        if provided > 1:
            click.echo(
                "Error: Options --list-decks, --deck, and --all-decks are mutually exclusive",
                err=True,
            )
            raise click.Abort()

        # List available decks
        if list_decks:
            click.echo("Available decks:")
            for name in connector.get_deck_names():
                click.echo(f"  - {name}")
            return

        out_path = Path(output)
        out_path.mkdir(parents=True, exist_ok=True)

        if all_decks:
            for name in connector.get_deck_names():
                click.echo(f"Exporting deck: {name}")
                export_deck(connector, name, out_path)
        else:
            # At this point --deck must be provided
            assert deck is not None
            click.echo(f"Exporting deck: {deck}")
            export_deck(connector, deck, out_path)

        click.echo("Pull completed successfully")

    except AnkiConnectError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        raise click.Abort() from e


@cli.command("push-yaml")
@click.option(
    "--dir",
    "deck_dir",
    type=click.Path(exists=True),
    required=True,
    help="Directory containing exported deck (config.yaml + data.yaml)",
)
@click.option("--deck-name", help="Optional override for target deck name")
@click.option(
    "--sync",
    "anki_sync",
    is_flag=True,
    help="Sync with AnkiWeb after pushing",
)
@click.option(
    "--replace",
    "replace",
    is_flag=True,
    help="Sync mode: delete notes in Anki that are not in YAML (bidirectional sync)",
)
@click.option(
    "--incremental",
    "incremental",
    is_flag=True,
    help="Only push notes that have changed (compare content before pushing)",
)
def push_yaml(
    deck_dir: str,
    deck_name: str | None,
    anki_sync: bool,
    replace: bool,
    incremental: bool,
) -> None:
    """Push notes from an exported deck directory back to Anki.

    Examples:
      - Basic push: anki-yaml-tool push-yaml --dir ./my-deck
      - Replace mode (sync): anki-yaml-tool push-yaml --dir ./my-deck --replace
      - Incremental: anki-yaml-tool push-yaml --dir ./my-deck --incremental

    The --replace flag enables bidirectional sync:
      - Notes in YAML are updated/created in Anki
      - Notes in Anki NOT present in YAML are DELETED

    The --incremental flag enables change detection:
      - Notes that haven't changed since last sync are skipped
      - Uses note ID and content hash for comparison
    """
    from anki_yaml_tool.core.pusher import push_deck_from_dir

    click.echo(f"Pushing YAML from {deck_dir} to Anki...")
    if replace:
        click.echo(
            click.style(
                "  Mode: REPLACE (notes not in YAML will be deleted)", fg="yellow"
            )
        )
    if incremental:
        click.echo(
            click.style(
                "  Mode: INCREMENTAL (only changed notes will be pushed)", fg="yellow"
            )
        )

    connector = AnkiConnector()

    try:
        stats = push_deck_from_dir(
            connector,
            Path(deck_dir),
            deck_name=deck_name,
            sync=anki_sync,
            replace=replace,
            incremental=incremental,
        )

        # Display summary
        click.echo("\n" + "=" * 40)
        click.echo(click.style("Push Summary:", fg="green", bold=True))

        added = stats.get("added", 0)
        updated = stats.get("updated", 0)
        deleted = stats.get("deleted", 0)
        unchanged = stats.get("unchanged", 0)
        failed = stats.get("failed", 0)

        if added > 0:
            click.echo(f"  {click.style('+', fg='green')} {added} added")
        if updated > 0:
            click.echo(f"  {click.style('~', fg='blue')} {updated} updated")
        if deleted > 0:
            click.echo(f"  {click.style('-', fg='red')} {deleted} deleted")
        if unchanged > 0:
            click.echo(f"  {click.style('=', fg='gray')} {unchanged} unchanged")
        if failed > 0:
            click.echo(f"  {click.style('!', fg='red')} {failed} failed")

        if added == 0 and updated == 0 and deleted == 0 and failed == 0:
            click.echo(click.style("  All notes already up to date!", fg="green"))

        click.echo("=" * 40)
        click.echo("Push completed successfully")

    except AnkiConnectError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        raise click.Abort() from e


@cli.command()
@click.option(
    "--file",
    "deck_file",
    type=click.Path(exists=True),
    required=True,
    help="Path to deck YAML file to watch",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(),
    default="deck.apkg",
    help="Output .apkg path",
)
@click.option(
    "--push",
    "auto_push",
    is_flag=True,
    help="Automatically push to Anki after building",
)
@click.option(
    "--debounce",
    "debounce_seconds",
    type=float,
    default=1.0,
    help="Seconds to wait after a change before rebuilding (default: 1.0)",
)
@click.option(
    "--deck-name",
    help="Name of the Anki deck (overrides deck file setting)",
)
@click.option(
    "--media-dir",
    type=click.Path(exists=True),
    help="Directory containing media files (overrides deck file setting)",
)
def watch(
    deck_file: str,
    output_file: str,
    auto_push: bool,
    debounce_seconds: float,
    deck_name: str | None,
    media_dir: str | None,
) -> None:
    """Watch a deck YAML file and automatically rebuild on changes.

    This command watches the specified YAML file for changes and automatically
    rebuilds the .apkg file when changes are detected. Optionally, it can also
    push the built deck to Anki.

    Examples:
      - Watch and rebuild: anki-yaml-tool watch --file ./deck.yaml
      - Watch, rebuild and push: anki-yaml-tool watch --file ./deck.yaml --push
      - Custom debounce time: anki-yaml-tool watch --file ./deck.yaml --debounce 2.0

    Note: This feature requires the watchdog package. Install it with:
      pip install anki-yaml-tool[watch]
    """
    from anki_yaml_tool.core.watcher import FileWatcher

    deck_path = Path(deck_file)

    # Validate the file exists
    if not deck_path.exists():
        click.echo(f"Error: File not found: {deck_file}", err=True)
        raise click.Abort()

    # Import builder components here to ensure they're available
    from typing import cast

    from anki_yaml_tool.core.builder import AnkiBuilder, ModelConfigComplete
    from anki_yaml_tool.core.config import load_deck_file
    from anki_yaml_tool.core.connector import AnkiConnector

    def build_and_push() -> None:
        """Build the deck and optionally push to Anki."""
        click.echo("\n" + "=" * 50)
        click.echo(
            click.style("Change detected! Building deck...", fg="cyan", bold=True)
        )
        click.echo("=" * 50)

        try:
            # Load deck file (same logic as build command)
            log.info("Loading deck file: %s", deck_file)
            model_config, items, file_deck_name, file_media_dir = load_deck_file(
                deck_file
            )
            model_configs = cast(list[ModelConfigComplete], [model_config])

            # Use provided deck-name or fall back to file deck-name
            final_deck_name = deck_name if deck_name is not None else file_deck_name

            # Final fallback to filename if no name provided anywhere
            if final_deck_name is None:
                if deck_path.stem == "deck":
                    final_deck_name = deck_path.parent.name or "Deck"
                else:
                    final_deck_name = deck_path.stem

            # Use provided media-dir or fall back to file media-dir
            media_folder: Path | None = Path(media_dir) if media_dir else file_media_dir

            click.echo(f"Building deck '{final_deck_name}' to {output_file}...")
            builder = AnkiBuilder(final_deck_name, model_configs, media_folder)

            # Map model names to their field lists
            model_fields_map = {cfg["name"]: cfg["fields"] for cfg in model_configs}
            first_model_name = model_configs[0]["name"]

            # Track media references
            all_media_refs: set[str] = set()

            for item in items:
                target_model_name = item.get(
                    "model", item.get("type", first_model_name)
                )
                if not isinstance(target_model_name, str):
                    target_model_name = str(target_model_name)

                if target_model_name not in model_fields_map:
                    target_model_name = first_model_name

                fields = model_fields_map[target_model_name]
                item_lower = {k.lower(): v for k, v in item.items()}
                field_values = [str(item_lower.get(f.lower(), "")) for f in fields]

                for field_value in field_values:
                    refs = get_media_references(field_value)
                    all_media_refs.update(refs)

                tags_raw = item.get("tags", [])
                tags = tags_raw if isinstance(tags_raw, list) else [str(tags_raw)]

                builder.add_note(field_values, tags=tags, model_name=target_model_name)

            # Build the package
            output_path = Path(output_file)
            builder.write_to_file(output_path)

            click.echo(
                click.style(f"Deck built successfully: {output_path}", fg="green")
            )

            # Optionally push to Anki
            if auto_push:
                click.echo("\nPushing to Anki...")
                connector = AnkiConnector()
                try:
                    result = connector.import_package(output_path)
                    if result:
                        click.echo(
                            click.style("Deck pushed to Anki successfully!", fg="green")
                        )
                    else:
                        click.echo(
                            click.style("Failed to push deck to Anki", fg="red"),
                            err=True,
                        )
                except AnkiConnectError as e:
                    click.echo(f"Error connecting to Anki: {e}", err=True)

        except FileNotFoundError as e:
            click.echo(f"Error: {e}", err=True)
        except DeckBuildError as e:
            click.echo(f"Error building deck: {e}", err=True)
        except Exception as e:
            click.echo(f"Unexpected error: {e}", err=True)
            log.exception("Error during watch rebuild")

    # Create and start the watcher
    try:
        watcher = FileWatcher(
            watch_path=deck_path,
            debounce_seconds=debounce_seconds,
        )

        click.echo(click.style("Starting file watcher...", fg="cyan"))
        click.echo(f"  Watching: {deck_file}")
        click.echo(f"  Output: {output_file}")
        if auto_push:
            click.echo(click.style("  Auto-push: enabled", fg="yellow"))
        click.echo(f"  Debounce: {debounce_seconds}s")
        click.echo("\nPress Ctrl+C to stop watching.")

        watcher.start(build_and_push)

        # Wait for keyboard interrupt
        import time

        try:
            while watcher.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            click.echo("\n" + click.style("Stopping watcher...", fg="yellow"))
        finally:
            watcher.stop()

    except ImportError as e:
        click.echo(
            click.style(
                "Error: watchdog package not installed.\n"
                "Install it with: pip install anki-yaml-tool[watch]",
                fg="red",
            ),
            err=True,
        )
        raise click.Abort() from e


@cli.command()
@click.argument("project_name", required=False, default="my-anki-deck")
@click.option(
    "--template",
    "-t",
    type=click.Choice(["basic", "language-learning", "technical"]),
    default="basic",
    help="Template type for the project.",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite existing directory.",
)
def init(project_name: str, template: str, force: bool) -> None:
    """Initialize a new Anki deck project.

    Creates a new directory with example deck.yaml, media folder, and README.

    PROJECT_NAME defaults to 'my-anki-deck' if not specified.
    """
    from anki_yaml_tool.templates import generate_readme, get_template

    log.info("Initializing project: %s with template: %s", project_name, template)

    # Create project directory
    project_path = Path(project_name)

    if project_path.exists() and not force:
        click.echo(
            f"Error: Directory '{project_name}' already exists. "
            "Use --force to overwrite.",
            err=True,
        )
        raise click.Abort()

    try:
        # Get template data
        template_data = get_template(template)
        log.debug("Loaded template: %s", template_data["description"])

        # Create directory structure
        project_path.mkdir(parents=True, exist_ok=True)
        media_path = project_path / "media"
        media_path.mkdir(exist_ok=True)
        log.debug("Created directories: %s, %s", project_path, media_path)

        # Generate deck.yaml
        config = template_data["config"].copy()
        config["deck-name"] = template_data["deck_name"]

        deck_data = {
            "config": config,
            "data": template_data["data"],
        }

        deck_file = project_path / "deck.yaml"
        with open(deck_file, "w", encoding="utf-8") as f:
            yaml.dump(
                deck_data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        log.info("Created deck file: %s", deck_file)

        # Generate README.md
        readme_content = generate_readme(template_data["deck_name"])
        readme_file = project_path / "README.md"
        readme_file.write_text(readme_content, encoding="utf-8")
        log.debug("Created README: %s", readme_file)

        # Success message
        click.echo(f"✓ Created project '{project_name}' with '{template}' template")
        click.echo(f"\n  Directory: {project_path.absolute()}")
        click.echo(f"  Deck file: {deck_file.name}")
        click.echo(f"  Media dir: {media_path.name}/")
        click.echo("\nNext steps:")
        click.echo(f"  1. cd {project_name}")
        click.echo("  2. Edit deck.yaml to customize your cards")
        click.echo("  3. anki-yaml-tool build --file deck.yaml")

    except KeyError as e:
        log.error("Template error: %s", e)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e
    except OSError as e:
        log.error("File system error: %s", e)
        click.echo(f"Error creating project: {e}", err=True)
        raise click.Abort() from e


@cli.command("batch-build")
@click.option(
    "--files",
    "-f",
    multiple=True,
    help="Deck files or glob patterns (can be specified multiple times)",
)
@click.option(
    "--input-dir",
    "-d",
    type=click.Path(exists=True),
    help="Directory to scan for deck.yaml files",
)
@click.option(
    "--recursive/--no-recursive",
    "-r/-R",
    default=True,
    help="Recursively scan subdirectories (default: True)",
)
@click.option(
    "--deck-filter",
    "-df",
    help="Filter decks by name pattern (supports wildcards: * matches any characters, ? matches single character). Example: --deck-filter 'spanish*'",
)
@click.option(
    "--pattern",
    default="deck.yaml",
    help="Filename pattern to match in directory scan (default: deck.yaml)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=".",
    help="Output directory for .apkg files",
)
@click.option(
    "--merge",
    is_flag=True,
    help="Merge all files into a single deck instead of building separately",
)
@click.option(
    "--deck-name",
    help="Name for merged deck (only used with --merge)",
)
@click.option(
    "--hierarchical",
    "-H",
    is_flag=True,
    help="Use directory structure for hierarchical deck names (e.g., lang::spanish)",
)
@click.option(
    "--push",
    "-p",
    is_flag=True,
    help="Push built decks to Anki after building",
)
@click.option(
    "--delete-after",
    is_flag=True,
    help="Delete .apkg files after successfully pushing to Anki (requires --push)",
)
@click.option(
    "--sync",
    is_flag=True,
    help="Sync with AnkiWeb after pushing (requires --push)",
)
@click.option(
    "--workers",
    "-w",
    type=int,
    default=None,
    help="Number of parallel workers for concurrent building (default: 4, use 1-8)",
)
def batch_build(
    files: tuple[str, ...],
    input_dir: str | None,
    recursive: bool,
    deck_filter: str | None,
    pattern: str,
    output_dir: str,
    merge: bool,
    deck_name: str | None,
    hierarchical: bool,
    push: bool,
    delete_after: bool,
    sync: bool,
    workers: int | None,
) -> None:
    """Build multiple decks from YAML files.

    Use --files for glob patterns or --input-dir for directory scanning.

    Examples:

        # Build all decks in examples directory using glob
        anki-yaml-tool batch-build -f "examples/*/deck.yaml"

        # Scan a directory for deck.yaml files
        anki-yaml-tool batch-build --input-dir ./decks

        # Scan with hierarchical deck names
        anki-yaml-tool batch-build -d ./decks -H

        # Merge multiple files into one deck
        anki-yaml-tool batch-build -f vocab1.yaml -f vocab2.yaml --merge --deck-name "All Vocab"
    """
    from anki_yaml_tool.core.batch import (
        expand_file_patterns,
        scan_directory_for_decks,
    )

    # Validate that at least one source is specified
    if not files and not input_dir:
        click.echo(
            "Error: Must specify either --files/-f or --input-dir/-d",
            err=True,
        )
        raise click.Abort()

    file_list: list[Path] = []
    base_dir: Path | None = None

    # Collect files from --files patterns
    if files:
        log.info("Batch build started with %d patterns", len(files))
        try:
            file_list.extend(expand_file_patterns(files))
        except Exception as e:
            click.echo(f"Error expanding file patterns: {e}", err=True)
            raise click.Abort() from e

    # Collect files from --input-dir scanning
    if input_dir:
        input_path = Path(input_dir)
        base_dir = input_path
        log.info(
            "Scanning directory: %s (recursive=%s, pattern=%s)",
            input_dir,
            recursive,
            pattern,
        )
        try:
            dir_files = list(scan_directory_for_decks(input_path, pattern, recursive))
            file_list.extend(dir_files)
        except NotADirectoryError as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort() from e

    if not file_list:
        click.echo("Error: No files found", err=True)
        raise click.Abort()

    # Remove duplicates and sort
    file_list = sorted(set(file_list))

    click.echo(f"Found {len(file_list)} deck files to process")

    # Apply deck name filter if specified
    if deck_filter:
        filtered_list = []
        for file_path in file_list:
            # Determine deck name for filtering
            # Priority: YAML deck-name > Hierarchical Name (if base_dir) > special deck.yaml handling > file stem
            try:
                _, _, file_deck_name, _ = load_deck_file(str(file_path))
                if file_deck_name:
                    deck_name_for_filter = file_deck_name
                elif base_dir:
                    deck_name_for_filter = get_deck_name_from_path(file_path, base_dir)
                elif file_path.stem == "deck":
                    deck_name_for_filter = file_path.parent.name or "Deck"
                else:
                    deck_name_for_filter = file_path.stem

                # Apply fnmatch pattern
                if fnmatch.fnmatch(deck_name_for_filter.lower(), deck_filter.lower()):
                    filtered_list.append(file_path)
                    log.debug(
                        "Deck '%s' matches filter '%s'",
                        deck_name_for_filter,
                        deck_filter,
                    )
                else:
                    log.debug(
                        "Deck '%s' does not match filter '%s'",
                        deck_name_for_filter,
                        deck_filter,
                    )
            except (ConfigValidationError, DataValidationError) as e:
                # Skip files that can't be loaded, but log the error
                log.warning("Skipping %s: %s", file_path.name, e)

        original_count = len(file_list)
        file_list = filtered_list
        click.echo(
            f"Filtered to {len(file_list)} decks matching pattern '{deck_filter}'"
        )
        if len(file_list) == 0:
            click.echo(
                f"Error: No decks match filter '{deck_filter}' (from {original_count} decks)",
                err=True,
            )
            raise click.Abort()

    log.debug("Files: %s", [str(f) for f in file_list])

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Default workers to 4 if not specified, cap at 8 to avoid overwhelming AnkiConnect
    if workers is None:
        workers = 4
    workers = min(max(workers, 1), 8)  # Ensure between 1-8

    if merge:
        # Merge mode: combine all files into one deck
        _batch_build_merged(file_list, output_path, deck_name, push, delete_after, sync)
    else:
        # Separate mode: build each file individually
        _batch_build_separate(
            file_list,
            output_path,
            base_dir if hierarchical else None,
            push,
            delete_after,
            sync,
            workers,
        )


def _batch_build_merged(
    file_list: list[Path],
    output_path: Path,
    deck_name: str | None,
    push: bool = False,
    delete_after: bool = False,
    sync: bool = False,
) -> None:
    """Build a merged deck from multiple files."""
    all_items: list[dict] = []
    model_configs: list[ModelConfigComplete] = []
    seen_models: set[str] = set()

    click.echo("Merging files...")

    with click.progressbar(file_list, label="Loading files") as files:
        for file_path in files:
            try:
                model_config, items, file_deck_name, _ = load_deck_file(str(file_path))

                # Track unique model configs
                model_name = model_config["name"]
                if model_name not in seen_models:
                    model_configs.append(model_config)
                    seen_models.add(model_name)
                    log.debug("Added model: %s", model_name)

                all_items.extend(items)
                log.debug("Loaded %d items from %s", len(items), file_path.name)

            except (ConfigValidationError, DataValidationError) as e:
                click.echo(f"\nWarning: Skipping {file_path.name}: {e}", err=True)

    if not all_items:
        click.echo("Error: No valid data found in any files", err=True)
        raise click.Abort()

    final_deck_name = deck_name or "Merged Deck"
    click.echo(
        f"\nBuilding merged deck '{final_deck_name}' with {len(all_items)} notes..."
    )

    builder = AnkiBuilder(final_deck_name, model_configs)

    model_fields_map = {cfg["name"]: cfg["fields"] for cfg in model_configs}
    first_model_name = model_configs[0]["name"]

    for item in all_items:
        target_model_name = item.get("model", item.get("type", first_model_name))
        if not isinstance(target_model_name, str):
            target_model_name = str(target_model_name)

        if target_model_name not in model_fields_map:
            target_model_name = first_model_name

        fields = model_fields_map[target_model_name]
        item_lower = {k.lower(): v for k, v in item.items()}
        field_values = [str(item_lower.get(f.lower(), "")) for f in fields]

        tags_raw = item.get("tags", [])
        tags: list[str] = tags_raw if isinstance(tags_raw, list) else [str(tags_raw)]

        if "id" in item:
            tags.append(f"id::{item['id']}")

        builder.add_note(field_values, tags=tags, model_name=target_model_name)

    output_file = (
        output_path / f"{final_deck_name.replace('::', '_').replace(' ', '_')}.apkg"
    )
    builder.write_to_file(output_file)
    click.echo(f"Successfully created {output_file}")

    if push:
        import base64
        import json
        import zipfile

        from anki_yaml_tool.core.connector import AnkiConnector

        click.echo(f"Pushing merged deck '{final_deck_name}' to Anki...")
        connector = AnkiConnector()

        try:
            # Extract and store media files
            with zipfile.ZipFile(output_file, "r") as zf:
                if "media" in zf.namelist():
                    media_map = json.loads(zf.read("media").decode("utf-8"))
                    if media_map:
                        click.echo(f"Storing {len(media_map)} media files...")
                        for idx, filename in media_map.items():
                            try:
                                content = zf.read(idx)
                                encoded = base64.b64encode(content).decode("utf-8")
                                connector.invoke(
                                    "storeMediaFile", filename=filename, data=encoded
                                )
                            except KeyError as e:
                                log.warning(
                                    "Media file %s not found in package: %s", idx, e
                                )
                                click.echo(
                                    f"Warning: Media file '{idx}' not found in package",
                                    err=True,
                                )
                            except AnkiConnectError as e:
                                log.warning(
                                    "Failed to store media file '%s': %s", filename, e
                                )
                                click.echo(
                                    f"Warning: Failed to store media file: {filename}",
                                    err=True,
                                )
                            except Exception as e:
                                log.warning(
                                    "Unexpected error storing media file '%s': %s",
                                    filename,
                                    e,
                                )
                                click.echo(
                                    f"Warning: Unexpected error with media file: {filename}",
                                    err=True,
                                )

            connector.import_package(output_file)
            click.echo("✅ Pushed successfully")

            if delete_after:
                output_file.unlink()
                log.info("Deleted: %s", output_file.name)

            if sync:
                click.echo("Syncing with AnkiWeb...")
                connector.sync()
                click.echo("✅ Sync complete")

        except Exception as e:
            click.echo(f"❌ Push failed: {e}", err=True)


def _batch_build_separate(
    file_list: list[Path],
    output_path: Path,
    base_dir: Path | None = None,
    push: bool = False,
    delete_after: bool = False,
    sync: bool = False,
    workers: int = 4,
) -> None:
    """Build each file as a separate deck.

    Args:
        file_list: List of deck files to build
        output_path: Directory for output files
        base_dir: Optional base directory for hierarchical deck naming
        push: Push built decks to Anki
        delete_after: Delete .apkg files after pushing
        sync: Sync with AnkiWeb after pushing
    """

    success_count = 0
    error_count = 0
    errors: list[tuple[str, str]] = []
    # Lock for thread-safe UI updates
    lock = threading.Lock()

    # Get deck names for display
    deck_names = []
    for file_path in file_list:
        if base_dir:
            name = get_deck_name_from_path(file_path, base_dir)
        elif file_path.stem == "deck":
            # Use parent directory name for deck.yaml files
            name = file_path.parent.name or "Deck"
        else:
            name = file_path.stem
        deck_names.append(name)

    # Status for each deck: empty, 🔨, 📤, ✅, ❌
    status = ["  " for _ in file_list]

    # Calculate max name length for table width
    max_name_len = max(len(name) for name in deck_names) if deck_names else 20
    max_name_len = max(max_name_len, 10)  # Minimum width
    table_height = len(file_list) + 4

    def print_table(first_time: bool = False):
        """Print the status table with cursor positioning."""
        with lock:
            if not first_time:
                # Move cursor up to redraw table
                sys.stdout.write(f"\033[{table_height}A")

            print(f"┌{'─' * (max_name_len + 2)}┬────────┐")
            print(f"│ {'Deck':<{max_name_len}} │ Status │")
            print(f"├{'─' * (max_name_len + 2)}┼────────┤")
            for name, s in zip(deck_names, status, strict=False):
                print(f"│ {name:<{max_name_len}} │   {s}   │")
            print(f"└{'─' * (max_name_len + 2)}┴────────┘")
            sys.stdout.flush()

    def push_deck(idx: int, output_file: Path, file_name: str) -> bool:
        """Push a deck to Anki in background thread. Returns True on success."""
        nonlocal success_count, error_count

        try:
            import base64
            import json
            import zipfile

            from anki_yaml_tool.core.connector import AnkiConnector

            connector = AnkiConnector()

            # Extract and store media files
            with zipfile.ZipFile(output_file, "r") as zf:
                if "media" in zf.namelist():
                    media_map = json.loads(zf.read("media").decode("utf-8"))
                    for media_idx, media_filename in media_map.items():
                        try:
                            content = zf.read(media_idx)
                            encoded = base64.b64encode(content).decode("utf-8")
                            connector.invoke(
                                "storeMediaFile", filename=media_filename, data=encoded
                            )
                        except KeyError as e:
                            log.warning(
                                "Media file %s not found in package: %s", media_idx, e
                            )
                        except AnkiConnectError as e:
                            log.warning(
                                "Failed to store media file '%s': %s", media_filename, e
                            )
                        except Exception as e:
                            log.warning(
                                "Unexpected error storing media file '%s': %s",
                                media_filename,
                                e,
                            )

            connector.import_package(output_file)
            log.info("Pushed: %s", output_file.name)

            # Delete after successful push if requested
            if delete_after:
                output_file.unlink()
                log.info("Deleted: %s", output_file.name)

            with lock:
                success_count += 1
                status[idx] = "✅"
            print_table()
            return True

        except Exception as e:
            with lock:
                error_count += 1
                status[idx] = "❌"
                errors.append((file_name, f"Push failed: {e}"))
            log.error("Push failed: %s: %s", file_name, e)
            print_table()
            return False

    # Print initial table
    print_table(first_time=True)

    # Use a thread pool for concurrent build operations
    # This allows building multiple decks in parallel
    push_futures: list[Future] = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for i, file_path in enumerate(file_list):
            # Show progress: Building deck X of Y...
            current_deck_name = deck_names[i] if i < len(deck_names) else file_path.stem
            click.echo(
                f"Building deck {i + 1} of {len(file_list)}: {current_deck_name}..."
            )

            # Update status to building
            with lock:
                status[i] = "🔨"
            print_table()

            try:
                # Load deck file and get media folder
                model_config, items, file_deck_name, media_folder = load_deck_file(
                    str(file_path)
                )

                # Priority: YAML deck-name > Hierarchical Name (if base_dir) > special deck.yaml handling > file stem
                if file_deck_name:
                    final_deck_name = file_deck_name
                elif base_dir:
                    final_deck_name = get_deck_name_from_path(file_path, base_dir)
                elif file_path.stem == "deck":
                    final_deck_name = file_path.parent.name or "Deck"
                else:
                    final_deck_name = file_path.stem

                # Pass media_folder to builder for automatic media discovery
                builder = AnkiBuilder(
                    final_deck_name, [model_config], media_folder=media_folder
                )

                fields = model_config["fields"]
                for item in items:
                    item_lower = {k.lower(): v for k, v in item.items()}
                    field_values = [str(item_lower.get(f.lower(), "")) for f in fields]

                    tags_raw = item.get("tags", [])
                    tags: list[str] = (
                        tags_raw if isinstance(tags_raw, list) else [str(tags_raw)]
                    )

                    if "id" in item:
                        tags.append(f"id::{item['id']}")

                    builder.add_note(field_values, tags=tags)

                # Determine output filename
                # Use sanitized deck name if possible, otherwise fallback to stem/parent
                safe_name = final_deck_name.replace("::", "_").replace(" ", "_")
                # Keep it somewhat descriptive of the original file if no deck-name was found
                if not file_deck_name:
                    if file_path.stem == "deck":
                        output_name = f"{file_path.parent.name}.apkg"
                    else:
                        output_name = f"{file_path.stem}.apkg"
                else:
                    output_name = f"{safe_name}.apkg"

                output_file = output_path / output_name
                builder.write_to_file(output_file)
                log.info("Built: %s -> %s", file_path.name, output_file.name)

                if push:
                    with lock:
                        status[i] = "📤"
                    print_table()
                    # Submit to thread pool
                    future = executor.submit(push_deck, i, output_file, file_path.name)
                    push_futures.append(future)
                else:
                    with lock:
                        success_count += 1
                        status[i] = "✅"
                    print_table()

            except (ConfigValidationError, DataValidationError, DeckBuildError) as e:
                with lock:
                    error_count += 1
                    status[i] = "❌"
                    errors.append((file_path.name, str(e)))
                log.error("Failed: %s: %s", file_path.name, e)
                print_table()

        # Executor context manager will wait for all futures to complete

    # Check potential exceptions from futures (though handled inside push_deck)
    for future in push_futures:
        try:
            future.result()
        except Exception:
            pass  # Already handled in push_deck

    # Final summary
    print()
    action = "built and pushed" if push else "built"
    if error_count == 0:
        click.echo(f"✅ Successfully {action} {success_count}/{len(file_list)} decks")
    else:
        click.echo(
            f"{action.capitalize()} {success_count}/{len(file_list)} decks, {error_count} failed"
        )
        for filename, error in errors:
            click.echo(f"  ❌ {filename}: {error}", err=True)

    if push and sync and success_count > 0:
        click.echo("\nSyncing with AnkiWeb...")
        try:
            from anki_yaml_tool.core.connector import AnkiConnector

            connector = AnkiConnector()
            connector.sync()
            click.echo("✅ Sync complete")
        except Exception as e:
            click.echo(f"❌ Sync failed: {e}", err=True)


def main():
    cli()


if __name__ == "__main__":
    main()
