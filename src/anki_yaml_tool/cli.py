"""Command-line interface for Anki Python Deck Tool.

This module provides the CLI entry points for building and pushing Anki decks.
"""

import fnmatch
import sys
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from importlib.metadata import version
from pathlib import Path

import click
import yaml

from anki_yaml_tool.core.batch import get_deck_name_from_path
from anki_yaml_tool.core.builder import AnkiBuilder, ModelConfigComplete
from anki_yaml_tool.core.config import load_deck_file
from anki_yaml_tool.core.connector import AnkiConnector
from anki_yaml_tool.core.deck_service import (
    BuildResult,
    ValidationResult,
    build_deck,
    push_apkg,
    validate_deck,
)
from anki_yaml_tool.core.exceptions import (
    AnkiConnectError,
    AnkiToolError,
    ConfigValidationError,
    DataValidationError,
    DeckBuildError,
)
from anki_yaml_tool.core.logging_config import get_logger, setup_logging

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
def build(file: str, output: str, deck_name: str | None, media_dir: str | None) -> None:
    """Build an .apkg file from YAML deck file."""
    try:
        click.echo("Building deck...")
        result: BuildResult = build_deck(
            deck_path=file,
            output_path=output,
            deck_name_override=deck_name,
            media_dir_override=media_dir,
        )

        click.echo(f"Deck '{result.deck_name}' — {result.notes_processed} notes")

        if result.media_files:
            click.echo(f"Added {result.media_files} media files")

        if result.missing_media_refs:
            click.echo(
                f"Warning: {len(result.missing_media_refs)} "
                "referenced media files not found:",
                err=True,
            )
            for ref in result.missing_media_refs:
                click.echo(f"  - {ref}", err=True)

        click.echo(f"Successfully created {result.output_path}")

    except AnkiToolError as e:
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
def validate(file: str, strict: bool) -> None:
    """Validate YAML deck file without building."""
    click.echo("Validating configuration and data...")
    try:
        result: ValidationResult = validate_deck(file, strict=strict)

        # Display issues
        for issue in result.issues:
            if issue.level == "error":
                click.echo(click.style(f"Error: {issue.message}", fg="red"), err=True)
            else:
                click.echo(
                    click.style(f"Warning: {issue.message}", fg="yellow"), err=True
                )

        if result.has_errors:
            click.echo(
                click.style("\nValidation failed with errors.", fg="red"), err=True
            )
            raise click.Abort()

        if strict and result.has_warnings:
            click.echo(
                click.style(
                    "\nValidation failed due to warnings in strict mode.", fg="red"
                ),
                err=True,
            )
            raise click.Abort()

        if result.has_warnings:
            click.echo(click.style("\nValidation passed with warnings.", fg="yellow"))
        else:
            click.echo(click.style("\nValidation passed successfully!", fg="green"))

    except AnkiToolError as e:
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
def push(apkg: str, sync: bool) -> None:
    """Push an .apkg file to a running Anki instance."""
    click.echo(f"Pushing {apkg} to Anki...")
    connector = AnkiConnector()

    try:
        push_apkg(apkg, connector, sync=sync)
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

    def build_and_push() -> None:
        """Build the deck and optionally push to Anki."""
        click.echo("\n" + "=" * 50)
        click.echo(
            click.style("Change detected! Building deck...", fg="cyan", bold=True)
        )
        click.echo("=" * 50)

        try:
            result = build_deck(
                deck_path=deck_file,
                output_path=output_file,
                deck_name_override=deck_name,
                media_dir_override=media_dir,
            )
            click.echo(
                click.style(
                    f"Deck '{result.deck_name}' built — {result.notes_processed} notes",
                    fg="green",
                )
            )

            # Optionally push to Anki
            if auto_push:
                click.echo("\nPushing to Anki...")
                connector = AnkiConnector()
                try:
                    push_apkg(output_file, connector)
                    click.echo(
                        click.style("Deck pushed to Anki successfully!", fg="green")
                    )
                except AnkiConnectError as e:
                    click.echo(f"Error connecting to Anki: {e}", err=True)

        except AnkiToolError as e:
            click.echo(f"Error: {e}", err=True)
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
        click.echo(f"Pushing merged deck '{final_deck_name}' to Anki...")
        connector = AnkiConnector()

        try:
            push_apkg(output_file, connector)
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

    def print_table(first_time: bool = False) -> None:
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

    def push_deck_to_anki(idx: int, output_file: Path, file_name: str) -> bool:
        """Push a deck to Anki in background thread. Returns True on success."""
        nonlocal success_count, error_count

        try:
            connector = AnkiConnector()
            push_apkg(output_file, connector)
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
                # Use hierarchical name as override when base_dir is set
                name_override = (
                    get_deck_name_from_path(file_path, base_dir)
                    if base_dir
                    else None
                )

                result = build_deck(
                    deck_path=file_path,
                    output_path=output_path / f"{current_deck_name.replace('::', '_').replace(' ', '_')}.apkg",
                    deck_name_override=name_override,
                )

                output_file = result.output_path
                log.info("Built: %s -> %s", file_path.name, output_file.name)

                if push:
                    with lock:
                        status[i] = "📤"
                    print_table()
                    # Submit to thread pool
                    future = executor.submit(
                        push_deck_to_anki, i, output_file, file_path.name
                    )
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
            connector = AnkiConnector()
            connector.sync()
            click.echo("✅ Sync complete")
        except Exception as e:
            click.echo(f"❌ Sync failed: {e}", err=True)


def main():
    cli()


if __name__ == "__main__":
    main()
