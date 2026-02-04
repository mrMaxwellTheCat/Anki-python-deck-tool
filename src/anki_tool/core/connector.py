"""AnkiConnect integration for pushing decks to Anki.

This module provides the AnkiConnector class for communicating with
Anki via the AnkiConnect add-on API.
"""

import base64
from pathlib import Path
from typing import Any

import requests

from anki_tool.core.exceptions import AnkiConnectError


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

    def invoke(self, action: str, **params) -> Any:
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
        return data.get("result")

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
