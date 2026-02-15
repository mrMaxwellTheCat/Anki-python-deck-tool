"""AnkiConnect integration for pushing decks to Anki.

This module provides the AnkiConnector class for communicating with
Anki via the AnkiConnect add-on API.

``AnkiConnector`` satisfies the :class:`~anki_yaml_tool.core.adapter.AnkiAdapter`
protocol via structural subtyping – no explicit inheritance is required.
"""

import base64
import logging
from pathlib import Path
from typing import cast

import requests

from anki_yaml_tool.core.exceptions import AnkiConnectError

# Logger for this module
logger = logging.getLogger("anki_yaml_tool.core.connector")

# Type alias for JSON values returned by AnkiConnect
JSONValue = dict[str, "JSONValue"] | list["JSONValue"] | str | int | float | bool | None


class AnkiConnector:
    """Client for interacting with AnkiConnect API.

    Args:
        url: The URL where AnkiConnect is listening (default: http://127.0.0.1:8765).
        timeout_short: Timeout for quick operations in seconds (default: 30).
        timeout_long: Timeout for long operations like imports in seconds (default: 120).

    Raises:
        AnkiConnectError: If communication with AnkiConnect fails.
    """

    def __init__(
        self,
        url: str = "http://127.0.0.1:8765",
        timeout_short: int = 30,
        timeout_long: int = 120,
    ):
        """Initialize the AnkiConnect client.

        Args:
            url: The URL where AnkiConnect is listening.
            timeout_short: Timeout for quick operations in seconds.
            timeout_long: Timeout for long operations like imports in seconds.
        """
        self.url = url
        self.timeout_short = timeout_short
        self.timeout_long = timeout_long
        self._session = requests.Session()

    def invoke(self, action: str, **params: JSONValue | int) -> JSONValue:
        """Invoke an AnkiConnect API action.

        Args:
            action: The AnkiConnect action name.
            **params: Parameters to pass to the action. Use '_timeout' to specify
                a custom timeout in seconds.

        Returns:
            The result from AnkiConnect.

        Raises:
            AnkiConnectError: If the connection fails or AnkiConnect returns an error.
        """
        timeout: int = self.timeout_short
        if "_timeout" in params:
            timeout = int(params.pop("_timeout"))  # type: ignore[arg-type]

        payload = {
            "action": action,
            "version": 6,
            "params": params,
        }
        try:
            response = self._session.post(self.url, json=payload, timeout=timeout)
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

    def import_package(self, apkg_path: Path) -> bool | None:
        """Import an .apkg file into Anki.

        Args:
            apkg_path: Path to the .apkg file to import.

        Raises:
            FileNotFoundError: If the .apkg file doesn't exist.
            AnkiConnectError: If the import fails.
        """
        if not apkg_path.exists():
            raise FileNotFoundError(f"Package not found: {apkg_path}")

        path_str = str(apkg_path.absolute())

        # If we're in WSL and the path is on a Windows mount, convert it to a Windows path
        # so that Anki (running on Windows) can find it.
        if path_str.startswith("/mnt/") and Path("/usr/bin/wslpath").exists():
            try:
                import subprocess

                path_str = (
                    subprocess.check_output(["wslpath", "-w", path_str])
                    .decode("utf-8")
                    .strip()
                )
            except Exception as e:
                logger.warning(
                    f"WSL path conversion failed for '{path_str}'. "
                    f"Falling back to original path. Error: {e}"
                )

        self.invoke("importPackage", path=path_str, _timeout=self.timeout_long)
        self.invoke("reloadCollection")
        return True

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
        self.invoke(
            "storeMediaFile",
            filename=filename,
            data=encoded,
            _timeout=self.timeout_long,
        )

    def close(self) -> None:
        """Close the underlying requests session.

        Should be called when done using the connector to release resources.
        """
        self._session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

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
        note: dict[str, int | dict[str, str]] = {"id": note_id, "fields": fields}
        self.invoke("updateNoteFields", note=cast(JSONValue, note))

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

        result = self.invoke("addNote", note=note)  # type: ignore[arg-type]
        if not isinstance(result, int):
            raise AnkiConnectError("Unexpected response from addNote", action="addNote")
        return result

    def delete_notes(self, note_ids: list[int]) -> None:
        """Delete notes from Anki by their IDs.

        Uses AnkiConnect's `deleteNotes` action.

        Args:
            note_ids: List of note IDs to delete.

        Raises:
            AnkiConnectError: If the delete operation fails.
        """
        if not note_ids:
            return
        self.invoke("deleteNotes", notes=note_ids)  # type: ignore[arg-type]

    def get_note_tags(self, note_id: int) -> list[str]:
        """Get the tags for a specific note.

        Uses AnkiConnect's `getNoteTags` action.

        Args:
            note_id: The ID of the note to get tags for.

        Returns:
            List of tags for the note.
        """
        result = self.invoke("getNoteTags", note=note_id)
        if not isinstance(result, list):
            return []
        return [str(t) for t in result]
