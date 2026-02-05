"""Core deck building functionality using genanki.

This module provides the AnkiBuilder class for constructing Anki decks
from configuration and data.
"""

import hashlib
import re
from pathlib import Path
from typing import Any

import genanki

from anki_tool.core.exceptions import DeckBuildError


class AnkiBuilder:
    """Builder for creating Anki deck packages (.apkg files).

    Args:
        deck_name: Name of the deck to create.
        model_config: Dictionary containing model configuration (name,
            fields, templates, css).

    Attributes:
        deck_name: Name of the deck.
        model_config: Model configuration dictionary.
        model: The genanki Model instance.
        deck: The genanki Deck instance.
        media_files: List of media file paths to include in the package.
    """

    def __init__(self, deck_name: str, model_config: dict[str, Any]):
        self.deck_name = deck_name
        self.model_config = model_config
        self.model = self._build_model()
        self.deck = genanki.Deck(self.stable_id(deck_name), deck_name)
        self.media_files: list[str] = []

    @staticmethod
    def stable_id(name: str) -> int:
        """Generate a stable numeric ID from a string name.

        Uses MD5 hash to create consistent IDs across runs for the same name.

        Args:
            name: The name to generate an ID from.

        Returns:
            An integer ID derived from the name's hash.
        """
        digest = hashlib.md5(name.encode("utf-8")).hexdigest()
        return int(digest[:8], 16)

    @staticmethod
    def convert_math_delimiters(text: str) -> str:
        r"""Convert LaTeX-style math delimiters to Anki LaTeX format.

        Converts:
        - $$...$$ to \[...\] (display math)
        - $...$ to \(...\) (inline math)

        Args:
            text: The text containing math delimiters.

        Returns:
            Text with math delimiters converted to Anki LaTeX format.
        """
        # First replace block math $$ ... $$ (must be done before inline)
        text = re.sub(r"\$\$(.*?)\$\$", r"\\[\1\\]", text, flags=re.DOTALL)
        # Then replace inline math $ ... $
        text = re.sub(r"\$(.*?)\$", r"\\(\1\\)", text)
        return text

    def _build_model(self) -> genanki.Model:
        """Build the genanki Model from configuration.

        Returns:
            A configured genanki.Model instance.

        Raises:
            DeckBuildError: If model configuration is invalid.
        """
        try:
            return genanki.Model(
                self.stable_id(self.model_config["name"]),
                self.model_config["name"],
                fields=[{"name": f} for f in self.model_config["fields"]],
                templates=self.model_config["templates"],
                css=self.model_config.get("css", ""),
            )
        except (KeyError, TypeError) as e:
            raise DeckBuildError(f"Invalid model configuration: {e}") from e

    def add_note(self, field_values: list[str], tags: list[str] | None = None) -> None:
        """Add a note to the deck.

        Args:
            field_values: List of field values in the same order as model fields.
            tags: Optional list of tags to apply to the note.
        """
        # Convert math delimiters in all field values
        converted_values = [
            self.convert_math_delimiters(value) for value in field_values
        ]
        note = genanki.Note(model=self.model, fields=converted_values, tags=tags or [])
        self.deck.add_note(note)

    def add_media(self, file_path: Path) -> None:
        """Add a media file to the deck package.

        Args:
            file_path: Path to the media file to include.
        """
        if file_path.exists():
            self.media_files.append(str(file_path.absolute()))

    def write_to_file(self, output_path: Path) -> None:
        """Write the deck package to an .apkg file.

        Args:
            output_path: Path where the .apkg file should be written.

        Raises:
            DeckBuildError: If writing the package fails.
        """
        try:
            package = genanki.Package(self.deck)
            package.media_files = self.media_files
            package.write_to_file(str(output_path))
        except Exception as e:
            raise DeckBuildError(f"Failed to write package: {e}") from e
