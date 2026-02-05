"""Schema validation utilities using Pydantic.

This module provides Pydantic models for validating configuration
and data files, with detailed error messages.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


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
    templates: list[ModelTemplate] = Field(
        ..., min_length=1, description="List of card templates"
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
    def validate_templates(cls, v: list[ModelTemplate]) -> list[ModelTemplate]:
        """Validate that template names are unique."""
        if not v:
            raise ValueError("At least one template is required")

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


def validate_note_fields(
    note_data: dict,
    required_fields: list[str],
    validate_missing: Literal["error", "warn", "ignore"] = "warn",
    check_empty: bool = True,
) -> tuple[bool, list[str]]:
    """Validate that note data contains all required fields.

    Args:
        note_data: The note data dictionary.
        required_fields: List of required field names.
        validate_missing: How to handle missing fields:
            - "error": Return False if any fields are missing
            - "warn": Return True but include missing fields in the list
            - "ignore": Always return True with empty list
        check_empty: Whether to also check if required fields are empty.

    Returns:
        A tuple of (is_valid, missing_fields):
            - is_valid: True if validation passes, False otherwise
            - missing_fields: List of missing or empty field names
    """
    if validate_missing == "ignore":
        return True, []

    # Map keys to their original case for better error messages
    actual_keys = {k.lower(): k for k in note_data.keys()}
    required_lower = [f.lower() for f in required_fields]

    missing = []
    for field_lower in required_lower:
        if field_lower not in actual_keys:
            missing.append(field_lower)
        elif check_empty:
            value = note_data[actual_keys[field_lower]]
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(field_lower)

    if validate_missing == "error" and missing:
        return False, missing

    return True, missing


def check_duplicate_ids(notes: list[dict]) -> dict[str, int]:
    """Check for duplicate note IDs in a list of notes.

    Args:
        notes: List of note data dictionaries.

    Returns:
        A dictionary mapping duplicate IDs to their occurrence count.
    """
    from collections import Counter

    # Extract IDs, filtering out None values
    ids: list[str] = [note["id"] for note in notes if note.get("id")]
    counts = Counter(ids)

    # Return only IDs that appear more than once
    return {id_: count for id_, count in counts.items() if count > 1}


def validate_html_tags(text: str, check_unclosed: bool = True) -> list[str]:
    """Perform basic HTML validation on text content.

    Args:
        text: The HTML text to validate.
        check_unclosed: Whether to check for unclosed tags.

    Returns:
        A list of validation warnings/errors found.
    """
    import re

    warnings: list[str] = []

    if check_unclosed:
        # Find all opening and closing tags
        open_tags = re.findall(r"<(\w+)[^>]*(?<!/)>", text)
        close_tags = re.findall(r"</(\w+)>", text)

        # Self-closing tags that don't need a closing tag
        self_closing = {"img", "br", "hr", "input", "meta", "link"}

        # Filter out self-closing tags
        open_tags = [tag for tag in open_tags if tag.lower() not in self_closing]

        # Check if every opening tag has a corresponding closing tag
        from collections import Counter

        open_counts = Counter(open_tags)
        close_counts = Counter(close_tags)

        for tag, count in open_counts.items():
            if close_counts.get(tag, 0) < count:
                warnings.append(f"Unclosed tag: <{tag}>")

        for tag, count in close_counts.items():
            if open_counts.get(tag, 0) < count:
                warnings.append(f"Extra closing tag: </{tag}>")

    return warnings
