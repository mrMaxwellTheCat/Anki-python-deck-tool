"""Anki adapter protocol definition.

This module defines the ``AnkiAdapter`` protocol – a structural interface
for any object that can communicate with Anki.  ``AnkiConnector`` satisfies
this protocol via duck typing; no explicit subclassing is needed.

Using a Protocol decouples core business logic from the concrete AnkiConnect
implementation, making it easy to swap in fakes/mocks for testing or
alternative backends in the future.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AnkiAdapter(Protocol):
    """Structural interface for Anki communication backends.

    Any class that implements the methods below is considered an
    ``AnkiAdapter``, regardless of inheritance.
    """

    def import_package(self, apkg_path: Path) -> bool | None:
        """Import an .apkg file into Anki.

        Args:
            apkg_path: Path to the .apkg file to import.

        Raises:
            FileNotFoundError: If the .apkg file doesn't exist.
            AnkiConnectError: If the import fails.
        """
        ...

    def sync(self) -> None:
        """Trigger a sync with AnkiWeb.

        Raises:
            AnkiConnectError: If the sync fails.
        """
        ...

    def store_media_file(self, file_path: Path, filename: str | None = None) -> None:
        """Store a media file in Anki's media folder.

        Args:
            file_path: Path to the media file to store.
            filename: Optional custom filename.

        Raises:
            FileNotFoundError: If the media file doesn't exist.
            AnkiConnectError: If storing the file fails.
        """
        ...

    def get_deck_names(self) -> list[str]:
        """Return a sorted list of deck names available in Anki."""
        ...

    def get_model_names(self) -> list[str]:
        """Return a sorted list of model names available in Anki."""
        ...

    def get_notes(self, deck_name: str) -> list[dict[str, Any]]:
        """Retrieve full note information for all notes in a deck.

        Args:
            deck_name: Name of the deck to query.

        Returns:
            A list of note-info dictionaries.
        """
        ...

    def get_model(self, model_name: str) -> dict[str, Any]:
        """Retrieve model definition for a given model name.

        Args:
            model_name: Name of the Anki model.

        Returns:
            Dictionary with ``name``, ``fields``, ``templates``, and ``css``.
        """
        ...

    def retrieve_media_file(self, filename: str) -> bytes:
        """Retrieve a media file's raw bytes from Anki.

        Args:
            filename: Name of the media file.

        Returns:
            The file content as bytes.
        """
        ...

    def update_note_fields(self, note_id: int, fields: dict[str, str]) -> None:
        """Update the fields of an existing note.

        Args:
            note_id: The ID of the note to update.
            fields: Mapping of field names to new values.
        """
        ...

    def add_note(
        self,
        deck_name: str,
        model_name: str,
        fields: dict[str, str],
        tags: list[str] | None = None,
    ) -> int:
        """Add a note to Anki and return the created note id.

        Args:
            deck_name: Target deck name.
            model_name: Model (note type) name.
            fields: Mapping of field names to values.
            tags: Optional list of tags.

        Returns:
            The ID of the newly created note.
        """
        ...

    def delete_notes(self, note_ids: list[int]) -> None:
        """Delete notes from Anki by their IDs.

        Args:
            note_ids: List of note IDs to delete.
        """
        ...

    def get_note_tags(self, note_id: int) -> list[str]:
        """Get the tags for a specific note.

        Args:
            note_id: The ID of the note.

        Returns:
            List of tags for the note.
        """
        ...

    def close(self) -> None:
        """Release any underlying resources."""
        ...
