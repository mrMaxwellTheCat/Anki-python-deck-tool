"""Pydantic models and type definitions for YAML deck data.

This module is the single source of truth for all data structures used to
represent Anki deck configurations, note data, and complete deck files.

Two families of types are provided:

* **Pydantic models** (``ModelTemplate``, ``ModelConfigSchema``, ``NoteData``,
  ``DeckFileSchema``) – used for validation when loading YAML files.
* **TypedDict bridges** (``ModelTemplateDict``, ``ModelConfigDict``) – plain
  dict types consumed by ``AnkiBuilder`` and other code that operates on
  already-validated data.
"""

from typing import Any, TypeAlias, TypedDict

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ───────────────────────── Type Aliases ─────────────────────────

ModelName: TypeAlias = str
"""Type alias for model names."""

FieldValue: TypeAlias = str
"""Type alias for field values."""

FieldValues: TypeAlias = list[FieldValue]
"""Type alias for a list of field values."""

TagList: TypeAlias = list[str]
"""Type alias for a list of tags."""

MediaFileList: TypeAlias = list[str]
"""Type alias for a list of media file paths."""


# ────────────────────── TypedDict Bridges ──────────────────────


class ModelTemplateDict(TypedDict):
    """Plain-dict representation of a card template.

    Used by ``AnkiBuilder`` which passes templates directly to *genanki*.
    """

    name: str
    qfmt: str
    afmt: str


class ModelConfigDict(TypedDict):
    """Plain-dict representation of a model configuration (required keys).

    Attributes:
        name: The model name.
        fields: List of field names.
        templates: List of card templates.
    """

    name: str
    fields: list[str]
    templates: list[ModelTemplateDict]


class ModelConfigDictComplete(ModelConfigDict, total=False):
    """Extended model config with optional keys.

    Attributes:
        css: Optional CSS styling for the model.
    """

    css: str


# ─────────────────────── Pydantic Models ───────────────────────


class ModelTemplate(BaseModel):
    """Schema for a card template.

    Attributes:
        name: The template name.
        qfmt: The question format (HTML template).
        afmt: The answer format (HTML template).
    """

    name: str = Field(..., min_length=1, description="Template name")
    qfmt: str = Field(..., min_length=1, description="Question format (HTML)")
    afmt: str = Field(..., min_length=1, description="Answer format (HTML)")

    @field_validator("name", "qfmt", "afmt")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace from string fields."""
        return v.strip()


class ModelConfigSchema(BaseModel):
    """Schema for a model configuration.

    Attributes:
        name: The model name.
        fields: List of field names (must be unique).
        templates: List of card templates (at least one required).
        css: Optional CSS styling for the cards.
    """

    name: str = Field(..., min_length=1, description="Model name")
    fields: list[str] = Field(..., min_length=1, description="List of field names")
    templates: list[ModelTemplate] | None = Field(
        default=None, description="List of card templates"
    )
    css: str = Field(default="", description="CSS styling")

    @field_validator("name", "css")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace from string fields."""
        return v.strip()

    @field_validator("fields")
    @classmethod
    def validate_fields(cls, v: list[str]) -> list[str]:
        """Validate that fields are non-empty and unique."""
        if not v:
            raise ValueError("At least one field is required")

        # Strip whitespace from each field
        stripped = [f.strip() for f in v]

        # Check for empty fields
        if any(not f for f in stripped):
            raise ValueError("Field names cannot be empty")

        # Check for duplicate fields
        if len(stripped) != len(set(stripped)):
            raise ValueError("Field names must be unique")

        return stripped

    @field_validator("templates")
    @classmethod
    def validate_templates(
        cls, v: list[ModelTemplate] | None
    ) -> list[ModelTemplate] | None:
        """Validate that template names are unique."""
        if v is None:
            return None

        if not v:
            # We allow empty list if provided (though Schema field previously enforced min_length=1)
            # But since field is optional now, empty list is fine? No, let's keep it consistent.
            # If templates is provided, it should probably not be empty.
            # But the field definition allows None.
            # If the user provides `templates: []`, this validator runs.
            # If the user omits `templates`, `v` is `None`.
            return []

        names = [t.name for t in v]

        if len(names) != len(set(names)):
            raise ValueError("Template names must be unique")

        return v


class NoteData(BaseModel):
    """Schema for a note's data.

    Attributes:
        tags: Optional list of tags for the note.
        id: Optional unique identifier for the note.

    Note: Other fields are dynamically validated based on the model config.
    """

    model_config = {"extra": "allow"}  # Allow additional fields for note content

    tags: list[str] = Field(default_factory=list, description="List of tags")
    id: str | None = Field(default=None, description="Optional note ID")

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v: list[str] | str | None) -> list[str]:
        """Ensure tags is always a list of strings."""
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        # Filter out empty and None values, convert to strings
        return [str(tag).strip() for tag in v if tag is not None and str(tag).strip()]


class DeckFileSchema(BaseModel):
    """Schema for a complete deck YAML file.

    Validates the top-level structure of a deck file containing both
    configuration and data sections.

    Attributes:
        deck_name: Optional name for the deck.
        config: Model configuration section.
        data: List of note data dictionaries (at least one required).
        media_folder: Optional path to a media folder.
    """

    model_config = ConfigDict(populate_by_name=True)

    deck_name: str | None = Field(
        default=None, alias="deck-name", description="Name of the deck"
    )
    config: ModelConfigSchema = Field(..., description="Model configuration")
    data: list[dict[str, Any]] = Field(
        ..., min_length=1, description="List of note data dictionaries"
    )
    media_folder: str | None = Field(
        default=None, alias="media-folder", description="Path to media folder"
    )
