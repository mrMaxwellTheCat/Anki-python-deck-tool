"""Core deck building functionality using genanki.

This module provides the AnkiBuilder class for constructing Anki decks
from configuration and data.
"""

import hashlib
import re
from pathlib import Path
from typing import TypeAlias, TypedDict

import genanki

from anki_yaml_tool.core.exceptions import DeckBuildError


class ModelTemplate(TypedDict):
    """Type definition for a model template.

    Attributes:
        name: The template name.
        qfmt: The question format (HTML).
        afmt: The answer format (HTML).
    """

    name: str
    qfmt: str
    afmt: str


class ModelConfig(TypedDict):
    """Type definition for a model configuration.

    Attributes:
        name: The model name (required).
        fields: List of field names (required).
        templates: List of card templates (required).
        css: Optional CSS styling.
    """

    name: str
    fields: list[str]
    templates: list[ModelTemplate]


class ModelConfigComplete(ModelConfig, total=False):
    """Extended model config with optional fields.

    Attributes:
        css: Optional CSS styling for the model.
    """

    css: str


# Type aliases for improved type safety
ModelName: TypeAlias = str
"""Type alias for model names."""

FieldValue: TypeAlias = str
"""Type alias for field values."""

FieldValues: TypeAlias = list[FieldValue]
"""Type alias for a list of field values."""

TagList: TypeAlias = list[str]
"""Type alias for a list of tags."""

ModelMap: TypeAlias = dict[ModelName, genanki.Model]
"""Type alias for a dictionary mapping model names to genanki.Model instances."""

MediaFileList: TypeAlias = list[str]
"""Type alias for a list of media file paths."""


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
