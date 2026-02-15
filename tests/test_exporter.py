"""Tests for exporter module's deck export functionality."""

from pathlib import Path
from typing import cast

import yaml

from anki_yaml_tool.core.connector import AnkiConnector
from anki_yaml_tool.core.exporter import export_deck


class FakeConnector:
    def __init__(self):
        self._media = {"image.jpg": b"IMAGEBYTES"}

    def get_notes(self, deck_name: str):
        return [
            {
                "noteId": 42,
                "fields": {
                    "Front": {"value": "Question 1"},
                    "Back": {"value": 'Answer 1 <img src="image.jpg">'},
                },
                "tags": ["tag1"],
                "modelName": "TestModel",
            }
        ]

    def get_model(self, model_name: str):
        return {
            "name": model_name,
            "fields": ["Front", "Back"],
            "templates": [{"name": "Card 1", "qfmt": "{{Front}}", "afmt": "{{Back}}"}],
            "css": ".card { font-size: 12px }",
        }

    def retrieve_media_file(self, filename: str) -> bytes:
        return self._media[filename]


def test_export_deck(tmp_path: Path):
    conn = FakeConnector()
    deck_path = export_deck(cast(AnkiConnector, conn), "My Deck", tmp_path)

    assert deck_path.exists()
    cfg_file = deck_path / "config.yaml"
    data_file = deck_path / "data.yaml"
    media_dir = deck_path / "media"

    assert cfg_file.exists()
    assert data_file.exists()
    assert media_dir.exists()

    cfg = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
    data = yaml.safe_load(data_file.read_text(encoding="utf-8"))

    assert cfg["name"] == "TestModel"
    assert "Front" in cfg["fields"]
    assert isinstance(data, list)
    assert data[0]["front"] == "Question 1"
    assert data[0]["note_id"] == 42

    # Media saved
    assert (media_dir / "image.jpg").exists()
    assert (media_dir / "image.jpg").read_bytes() == b"IMAGEBYTES"
