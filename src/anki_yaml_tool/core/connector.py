"""AnkiConnect integration for pushing decks to Anki.

This module provides the AnkiConnector class for communicating with
Anki via the AnkiConnect add-on API.
"""

import base64
from pathlib import Path
from typing import cast

import requests

from anki_yaml_tool.core.exceptions import AnkiConnectError

# Type alias for JSON values returned by AnkiConnect
JSONValue = dict[str, "JSONValue"] | list["JSONValue"] | str | int | float | bool | None


class AnkiConnector:
    """Client for interacting with AnkiConnect API.

    Args:
        url: The URL where AnkiConnect is listening (default: http://127.0.0.1:8765).

    Raises:
        AnkiConnectError: If communication with AnkiConnect fails.
    """

    def __init__(self, url: str = "http://127.0.0.1:8765"):
        """Initialize the AnkiConnect client.

        Args:
            url: The URL where AnkiConnect is listening.
        """
        self.url = url

    def invoke(self, action: str, **params) -> JSONValue:
        """Invoke an AnkiConnect API action.

        Args:
            action: The AnkiConnect action name.
            **params: Parameters to pass to the action.

        Returns:
            The result from AnkiConnect.

        Raises:
            AnkiConnectError: If the connection fails or AnkiConnect returns an error.
        """
        payload = {
            "action": action,
            "version": 6,
            "params": params,
        }
        try:
            response = requests.post(self.url, json=payload, timeout=30)
            response.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            raise AnkiConnectError(
                f"Could not connect to Anki at {self.url}. "
                "Is Anki open with AnkiConnect installed?",
                action=action,
            ) from e

        data = response.json()
        if data.get("error"):
            raise AnkiConnectError(f"AnkiConnect Error: {data['error']}", action=action)
        return cast(JSONValue, data.get("result"))

    def import_package(self, apkg_path: Path) -> None:
        """Import an .apkg file into Anki.

        Args:
            apkg_path: Path to the .apkg file to import.

        Raises:
            FileNotFoundError: If the .apkg file doesn't exist.
            AnkiConnectError: If the import fails.
        """
        if not apkg_path.exists():
            raise FileNotFoundError(f"Package not found: {apkg_path}")

        self.invoke("importPackage", path=str(apkg_path.absolute()))
        self.invoke("reloadCollection")

    def sync(self) -> None:
        """Trigger a sync with AnkiWeb.

        Raises:
            AnkiConnectError: If the sync fails.
        """
        self.invoke("sync")

    def store_media_file(self, file_path: Path, filename: str | None = None) -> None:
        """Store a media file in Anki's media folder.

        Args:
            file_path: Path to the media file to store.
            filename: Optional custom filename. If not provided, uses the
                original filename.

        Raises:
            FileNotFoundError: If the media file doesn't exist.
            AnkiConnectError: If storing the file fails.
        """
        if not filename:
            filename = file_path.name

        content = file_path.read_bytes()
        encoded = base64.b64encode(content).decode("utf-8")
        self.invoke("storeMediaFile", filename=filename, data=encoded)

    def get_deck_names(self) -> list[str]:
        """Return a sorted list of deck names available in Anki."""
        result = self.invoke("deckNames")
        if not isinstance(result, list):
            raise AnkiConnectError(
                "Unexpected response for deckNames", action="deckNames"
            )
        return sorted([str(x) for x in result])

    def get_model_names(self) -> list[str]:
        """Return a sorted list of model names available in Anki."""
        result = self.invoke("modelNames")
        if not isinstance(result, list):
            raise AnkiConnectError(
                "Unexpected response for modelNames", action="modelNames"
            )
        return sorted([str(x) for x in result])

    def get_notes(self, deck_name: str) -> list[dict]:
        """Retrieve full note information for all notes in a deck.

        Uses AnkiConnect's findNotes followed by notesInfo to obtain
        complete note data.
        """
        # Quote and escape the deck name so Anki's search parser handles
        # spaces, subdeck separators, and embedded quotes correctly.
        escaped_deck_name = deck_name.replace('"', r"\"")
        query = f'deck:"{escaped_deck_name}"'
        note_ids = self.invoke("findNotes", query=query)
        if not isinstance(note_ids, list):
            raise AnkiConnectError(
                "Unexpected response from findNotes", action="findNotes"
            )
        if not note_ids:
            return []
        notes = self.invoke("notesInfo", notes=note_ids)
        if not isinstance(notes, list):
            raise AnkiConnectError(
                "Unexpected response from notesInfo", action="notesInfo"
            )
        return [cast(dict, n) for n in notes]

    def get_model(self, model_name: str) -> dict:
        """Retrieve model definition (fields and templates) for a given model name."""
        fields = self.invoke("modelFieldNames", modelName=model_name)
        templates = self.invoke("modelTemplates", modelName=model_name)

        if not isinstance(fields, list):
            raise AnkiConnectError(
                "Unexpected response from modelFieldNames", action="modelFieldNames"
            )

        # templates is expected to be a list of dicts; fall back to empty
        templates_list = templates if isinstance(templates, list) else []

        return {
            "name": model_name,
            "fields": [str(f) for f in fields],
            "templates": templates_list,
            "css": "",
        }

    def retrieve_media_file(self, filename: str) -> bytes:
        """Retrieve a media file's raw bytes from Anki via AnkiConnect.

        Returns the file bytes. Expects AnkiConnect's `retrieveMediaFile`
        action to return base64-encoded string content.
        """
        data_b64 = self.invoke("retrieveMediaFile", filename=filename)
        if not isinstance(data_b64, str):
            raise AnkiConnectError(
                "Unexpected response from retrieveMediaFile", action="retrieveMediaFile"
            )
        try:
            return base64.b64decode(data_b64)
        except Exception as e:
            raise AnkiConnectError(
                f"Failed to decode media file {filename}: {e}"
            ) from e

    def update_note_fields(self, note_id: int, fields: dict[str, str]) -> None:
        """Update the fields of an existing note.

        This uses AnkiConnect's `updateNoteFields` action and expects a note
        id and a dict mapping model field names to values.
        """
        if not isinstance(note_id, int):
            raise ValueError("note_id must be an integer")
        self.invoke("updateNoteFields", note={"id": note_id, "fields": fields})

    def add_note(
        self,
        deck_name: str,
        model_name: str,
        fields: dict[str, str],
        tags: list[str] | None = None,
    ) -> int:
        """Add a note to Anki and return the created note id.

        Uses AnkiConnect's `addNote` action.
        """
        note = {"deckName": deck_name, "modelName": model_name, "fields": fields}
        if tags:
            note["tags"] = tags

        result = self.invoke("addNote", note=note)
        if not isinstance(result, int):
            raise AnkiConnectError("Unexpected response from addNote", action="addNote")
        return result
