import base64
import requests
from pathlib import Path
from typing import Any, Dict, Optional


class AnkiConnector:
    def __init__(self, url: str = "http://127.0.0.1:8765"):
        self.url = url

    def invoke(self, action: str, **params) -> Any:
        payload = {
            "action": action,
            "version": 6,
            "params": params,
        }
        try:
            response = requests.post(self.url, json=payload, timeout=30)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Could not connect to Anki at {self.url}. Is Anki open with AnkiConnect installed?"
            )

        data = response.json()
        if data.get("error"):
            raise RuntimeError(f"AnkiConnect Error: {data['error']}")
        return data.get("result")

    def import_package(self, apkg_path: Path):
        """Imports an .apkg file into Anki."""
        if not apkg_path.exists():
            raise FileNotFoundError(f"Package not found: {apkg_path}")

        self.invoke("importPackage", path=str(apkg_path.absolute()))
        self.invoke("reloadCollection")

    def sync(self):
        """Triggers a sync in Anki."""
        self.invoke("sync")

    def store_media_file(self, file_path: Path, filename: Optional[str] = None):
        """Stores a media file in Anki's media folder."""
        if not filename:
            filename = file_path.name

        content = file_path.read_bytes()
        encoded = base64.b64encode(content).decode("utf-8")
        self.invoke("storeMediaFile", filename=filename, data=encoded)
