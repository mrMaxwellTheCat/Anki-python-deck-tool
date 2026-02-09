"""Batch processing utilities for building multiple decks.

This module provides utilities for processing multiple deck files
using glob patterns and directory scanning.
"""

import glob
from collections.abc import Iterator
from pathlib import Path

from anki_yaml_tool.core.logging_config import get_logger

log = get_logger("batch")


def expand_file_patterns(patterns: tuple[str, ...]) -> list[Path]:
    """Expand glob patterns to a list of file paths.

    Args:
        patterns: Tuple of file paths or glob patterns

    Returns:
        List of resolved file paths (duplicates removed, sorted)

    Raises:
        FileNotFoundError: If no files match the patterns
    """
    files: set[Path] = set()

    for pattern in patterns:
        pattern_path = Path(pattern)

        # If it's a direct file path that exists, add it
        if pattern_path.exists() and pattern_path.is_file():
            files.add(pattern_path.resolve())
            log.debug("Found file: %s", pattern_path)
        else:
            # Try glob expansion
            matches = glob.glob(pattern, recursive=True)
            if matches:
                for match in matches:
                    match_path = Path(match)
                    if match_path.is_file():
                        files.add(match_path.resolve())
                        log.debug("Glob matched: %s", match_path)
            else:
                log.warning("No files matched pattern: %s", pattern)

    result = sorted(files)
    log.info("Expanded %d patterns to %d files", len(patterns), len(result))
    return result


def scan_directory_for_decks(
    directory: Path,
    pattern: str = "deck.yaml",
    recursive: bool = True,
) -> Iterator[Path]:
    """Scan a directory for deck files.

    Args:
        directory: Directory to scan
        pattern: Filename pattern to match (default: deck.yaml)
        recursive: Whether to scan subdirectories

    Yields:
        Paths to deck files found
    """
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    glob_pattern = f"**/{pattern}" if recursive else pattern
    log.info("Scanning %s for %s", directory, glob_pattern)

    for deck_file in directory.glob(glob_pattern):
        if deck_file.is_file():
            log.debug("Found deck file: %s", deck_file)
            yield deck_file


def get_deck_name_from_path(file_path: Path, base_dir: Path | None = None) -> str:
    """Generate a deck name from a file path.

    If base_dir is provided, uses the relative path to create
    hierarchical deck names (e.g., "language/spanish" -> "language::spanish").

    Args:
        file_path: Path to the deck file
        base_dir: Optional base directory for relative naming

    Returns:
        Generated deck name
    """
    if base_dir is not None:
        try:
            relative = file_path.parent.relative_to(base_dir)
            if relative != Path("."):
                parts = relative.parts
                return "::".join(parts)
        except ValueError:
            pass

    # Fall back to parent directory name or file stem
    return file_path.parent.name or file_path.stem or "Deck"
