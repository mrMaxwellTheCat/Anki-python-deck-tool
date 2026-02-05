"""Media file handling utilities.

This module provides functions for discovering, validating, and managing
media files for Anki decks.
"""

from pathlib import Path

from anki_tool.core.exceptions import MediaMissingError


def validate_media_file(file_path: Path | str) -> Path:
    """Validate that a media file exists.

    Args:
        file_path: Path to the media file.

    Returns:
        The validated Path object.

    Raises:
        MediaMissingError: If the media file doesn't exist.
    """
    path = Path(file_path)

    if not path.exists():
        raise MediaMissingError(f"Media file not found: {file_path}")

    if not path.is_file():
        raise MediaMissingError(f"Media path is not a file: {file_path}")

    return path


def discover_media_files(
    directory: Path | str, extensions: list[str] | None = None
) -> list[Path]:
    """Discover media files in a directory.

    Args:
        directory: Path to the directory to search.
        extensions: Optional list of file extensions to filter by
            (e.g., [".jpg", ".png", ".mp3"]). If None, finds all files.

    Returns:
        A list of discovered media file paths.

    Raises:
        FileNotFoundError: If the directory doesn't exist.
    """
    dir_path = Path(directory)

    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    if not dir_path.is_dir():
        raise FileNotFoundError(f"Path is not a directory: {directory}")

    # Common media extensions if none provided
    if extensions is None:
        extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".svg",
            ".mp3",
            ".wav",
            ".ogg",
            ".mp4",
            ".webm",
        ]

    media_files: list[Path] = []

    for ext in extensions:
        # Use glob to find files with the extension (case-insensitive)
        media_files.extend(dir_path.glob(f"*{ext}"))
        media_files.extend(dir_path.glob(f"*{ext.upper()}"))

    # Remove duplicates and sort
    return sorted(set(media_files))


def get_media_references(text: str) -> list[str]:
    """Extract media file references from HTML text.

    Finds references in img src, audio src, and [sound:...] tags.

    Args:
        text: The HTML text to search.

    Returns:
        A list of media filenames referenced in the text.
    """
    import re

    references: list[str] = []

    # Find img src="filename"
    img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
    references.extend(re.findall(img_pattern, text))

    # Find audio src="filename"
    audio_pattern = r'<audio[^>]+src=["\']([^"\']+)["\']'
    references.extend(re.findall(audio_pattern, text))

    # Find [sound:filename]
    sound_pattern = r"\[sound:([^\]]+)\]"
    references.extend(re.findall(sound_pattern, text))

    # Extract just the filename (remove path if present)
    filenames = [Path(ref).name for ref in references]

    return filenames


def validate_media_references(
    text: str, media_dir: Path | str, raise_on_missing: bool = True
) -> list[Path]:
    """Validate that all media files referenced in text exist.

    Args:
        text: The HTML text containing media references.
        media_dir: Directory where media files should be located.
        raise_on_missing: If True, raise an exception if files are missing.
            If False, return only the files that exist.

    Returns:
        A list of validated media file paths.

    Raises:
        MediaMissingError: If raise_on_missing is True and any files are missing.
    """
    dir_path = Path(media_dir)
    references = get_media_references(text)
    validated_files: list[Path] = []
    missing_files: list[str] = []

    for filename in references:
        file_path = dir_path / filename

        if file_path.exists():
            validated_files.append(file_path)
        else:
            missing_files.append(filename)

    if raise_on_missing and missing_files:
        raise MediaMissingError(
            f"Referenced media files not found: {', '.join(missing_files)}"
        )

    return validated_files
