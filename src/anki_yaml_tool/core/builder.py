"""Core deck building functionality using genanki.

This module provides the AnkiBuilder class for constructing Anki decks
from configuration and data.
"""

import hashlib
import re
from pathlib import Path
from typing import TypeAlias

import genanki  # type: ignore

from anki_yaml_tool.core.exceptions import DeckBuildError
from anki_yaml_tool.core.models import (
    FieldValues,
    MediaFileList,
    ModelConfigDictComplete,
    ModelName,
    TagList,
)

# Re-export for backward compatibility
ModelConfigComplete = ModelConfigDictComplete

# Type alias for genanki Model map (depends on genanki, so stays here)
ModelMap: TypeAlias = dict[ModelName, genanki.Model]
"""Type alias for a dictionary mapping model names to genanki.Model instances."""


class AnkiBuilder:
    """Builder for creating Anki deck packages (.apkg files).

    Args:
        deck_name: Name of the deck to create.
        model_configs: List of dictionaries containing model configurations.

    Attributes:
        deck_name: Name of the deck.
        model_configs: List of model configuration dictionaries.
        models: Dictionary mapping model names to genanki.Model instances.
        deck: The genanki Deck instance.
        media_files: List of media file paths to include in the package.
    """

    def __init__(
        self,
        deck_name: str,
        model_configs: list[ModelConfigComplete],
        media_folder: Path | None = None,
    ):
        self.deck_name: str = deck_name
        if not model_configs:
            raise DeckBuildError("At least one model configuration is required")
        self.model_configs: list[ModelConfigComplete] = model_configs
        self.models: ModelMap = self._build_models()
        self.deck: genanki.Deck = genanki.Deck(self.stable_id(deck_name), deck_name)
        self.media_files: MediaFileList = []
        self.media_folder: Path | None = media_folder
        self.media_files_set: set[str] = set()

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
        - Preserves already converted \(...\) and \[...\]
        - Does not convert escaped \$ or # in text
        - Does not convert $ in URLs or query parameters

        Args:
            text: The text containing math delimiters.

        Returns:
            Text with math delimiters converted to Anki LaTeX format.
        """
        # Use unique placeholders to protect already converted Anki-style delimiters
        # We use different markers for opening and closing to avoid confusion
        placeholder_inline_open = "__ANKILATEX_INLINE_OPEN__"
        placeholder_inline_close = "__ANKILATEX_INLINE_CLOSE__"
        placeholder_block_open = "__ANKILATEX_BLOCK_OPEN__"
        placeholder_block_close = "__ANKILATEX_BLOCK_CLOSE__"

        # Protect escaped characters first: \$ and \#
        # These should not be converted
        placeholder_escaped_dollar = "__ANKILATEX_ESCAPED_DOLLAR__"
        placeholder_escaped_hash = "__ANKILATEX_ESCAPED_HASH__"

        # Protect escaped \$ (single backslash before dollar sign)
        text = re.sub(r"\\\$", placeholder_escaped_dollar, text)
        # Protect escaped \#
        text = re.sub(r"\\#", placeholder_escaped_hash, text)

        # Protect already converted Anki-style delimiters \(...\) and \[...\]
        text = re.sub(
            r"\\\((.*?)\\\)",
            lambda m: placeholder_inline_open + m.group(1) + placeholder_inline_close,
            text,
            flags=re.DOTALL,
        )
        text = re.sub(
            r"\\\[(.*?)\\\]",
            lambda m: placeholder_block_open + m.group(1) + placeholder_block_close,
            text,
            flags=re.DOTALL,
        )

        # Helper function to check if we're in a URL context
        def is_in_url_context(pos: int, txt: str) -> bool:
            """Check if position is likely within a URL or query string."""
            if pos == 0:
                return False

            prefix = txt[:pos]

            # Check for URL scheme
            url_scheme_match = re.search(r"https?://[^\s]*", prefix)
            if url_scheme_match:
                scheme_end = url_scheme_match.end()
                # Check if current position is within the URL
                if pos <= scheme_end:
                    return True
                # Check for query parameters or path after scheme
                remaining = prefix[scheme_end:]
                if "?" in remaining or "&" in remaining:
                    # Find the last query indicator
                    last_indicator = max(remaining.rfind("?"), remaining.rfind("&"))
                    if last_indicator != -1:
                        # Check if we're within a reasonable distance
                        if pos - scheme_end - last_indicator - 1 < 100:
                            return True

            # Check for file paths that might look like URLs
            # but be more conservative - only if clearly a path
            if re.search(r"^[a-zA-Z]:[/\\]", prefix) or prefix.startswith("/"):
                # This is likely a file path, not a URL with query params
                return False

            return False

        # Replace block math $ ... $ with \[...\]
        def replace_block_math(match):
            content = match.group(1)
            start_pos = match.start()
            # Check if preceded by backslash (escaped)
            if start_pos > 0 and text[start_pos - 1] == "\\":
                return match.group(0)  # Don't convert, it's escaped
            return "\\[" + content + "\\]"

        text = re.sub(r"\$\$([^$]+?)\$\$", replace_block_math, text, flags=re.DOTALL)

        # Replace inline math $ ... $ with \(...\)
        def replace_inline_math(match):
            content = match.group(1)
            start_pos = match.start()

            # Check if preceded by backslash (escaped like \$)
            # The placeholder was already applied, so check if the char before is the placeholder
            if start_pos > 0 and text[start_pos - 1] == "\\":
                return match.group(0)  # Don't convert, it's escaped

            # Check if in URL context
            if is_in_url_context(start_pos, text):
                return match.group(0)  # Don't convert, likely in URL

            return "\\(" + content + "\\)"

        # Replace $...$ but not escaped \$, not in URLs
        # Use a more precise pattern that excludes \$ by checking it's not preceded by \
        text = re.sub(r"(?<!\\)\$([^$\n]+?)\$", replace_inline_math, text)

        # Restore protected Anki-style delimiters
        text = text.replace(placeholder_inline_open, "\\(")
        text = text.replace(placeholder_inline_close, "\\)")
        text = text.replace(placeholder_block_open, "\\[")
        text = text.replace(placeholder_block_close, "\\]")

        # Restore escaped characters
        text = text.replace(placeholder_escaped_dollar, "\\$")
        text = text.replace(placeholder_escaped_hash, "\\#")

        return text

    def _build_models(self) -> ModelMap:
        """Build genanki Models from configurations.

        Returns:
            A dictionary mapping model names to genanki.Model instances.

        Raises:
            DeckBuildError: If any model configuration is invalid.
        """
        models: ModelMap = {}
        for config in self.model_configs:
            try:
                model_name: ModelName = config["name"]
                models[model_name] = genanki.Model(
                    self.stable_id(model_name),
                    model_name,
                    fields=[{"name": f} for f in config["fields"]],
                    templates=config["templates"],
                    css=config.get("css", ""),
                )
            except (KeyError, TypeError) as e:
                raise DeckBuildError(f"Invalid model configuration: {e}") from e
        return models

    def add_note(
        self,
        field_values: FieldValues,
        tags: TagList | None = None,
        model_name: ModelName | None = None,
    ) -> None:
        """Add a note to the deck.

        Args:
            field_values: List of field values in the same order as model fields.
            tags: Optional list of tags to apply to the note.
            model_name: Name of the model to use. If None, uses the first model.

        Raises:
            DeckBuildError: If the specified model_name is not found.
        """
        if model_name is None:
            # Default to the first model
            model: genanki.Model = list(self.models.values())[0]
        elif model_name in self.models:
            model = self.models[model_name]
        else:
            raise DeckBuildError(f"Model '{model_name}' not found in builder")

        # Convert math delimiters and scan for media in all field values
        converted_values: FieldValues = []
        for value in field_values:
            converted = self.convert_math_delimiters(value)
            converted_values.append(converted)

            # Scan for media if media_folder is set
            if self.media_folder:
                # Matches [sound:file.mp3] or [img:image.png]
                # format: [type:filename]
                media_matches = re.findall(r"\[(sound|img):(.+?)\]", converted)
                for _, filename in media_matches:
                    media_path = self.media_folder / filename
                    if media_path.exists():
                        self.add_media(media_path)

        note: genanki.Note = genanki.Note(
            model=model, fields=converted_values, tags=tags or []
        )
        self.deck.add_note(note)

    def add_media(self, file_path: Path) -> None:
        """Add a media file to the deck package.

        Args:
            file_path: Path to the media file to include.
        """
        if file_path.exists():
            abs_path = str(file_path.absolute())
            if abs_path not in self.media_files_set:
                self.media_files.append(abs_path)
                self.media_files_set.add(abs_path)

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
