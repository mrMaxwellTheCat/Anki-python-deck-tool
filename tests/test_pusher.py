"""Tests for pushing YAML decks back to Anki."""
from pathlib import Path

import yaml
from anki_yaml_tool.core.pusher import push_deck_from_dir


class FakeConnector:
    def __init__(self):
        self.updated = []
        self.added = []
        self.stored = []
        self.invoked = []

    def update_note_fields(self, nid, fields):
        self.updated.append((nid, fields))

    def add_note(self, deck_name, model_name, fields, tags=None):
        self.added.append((deck_name, model_name, fields, tags))
        return 999

    def store_media_file(self, file_path, filename=None):
        self.stored.append((str(file_path), filename))

    def invoke(self, action, **params):
        self.invoked.append((action, params))
        return None

    def sync(self):
        pass


def test_push_deck_from_dir(tmp_path: Path):
    deck_dir = tmp_path / "MyDeck"
    deck_dir.mkdir()

    # config.yaml
    cfg = {
        "name": "TestModel",
        "fields": ["Front", "Back"],
        "templates": [{"name": "Card 1", "qfmt": "{{Front}}", "afmt": "{{Back}}"}],
        "css": "",
    }
    (deck_dir / "config.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")

    # data.yaml with one existing note (note_id) and one new note
    data = [
        {
            "front": "Q1",
            "back": 'A1 <img src="img.jpg">',
            "tags": ["t1"],
            "note_id": 111,
        },
        {"front": "Q2", "back": "A2", "tags": ["t2"]},
    ]
    (deck_dir / "data.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")

    # media dir
    media_dir = deck_dir / "media"
    media_dir.mkdir()
    (media_dir / "img.jpg").write_bytes(b"IMG")

    from typing import cast

    from anki_yaml_tool.core.connector import AnkiConnector

    fake = FakeConnector()
    push_deck_from_dir(
        cast(AnkiConnector, fake), deck_dir, deck_name="TargetDeck", sync=True
    )

    # Existing note updated
    assert any(u[0] == 111 for u in fake.updated)
    # New note added
    assert any(a[0] == "TargetDeck" for a in fake.added)
    # Media stored
    assert any("img.jpg" in s[0] for s in fake.stored)
    # addTags invoked for note update
    assert any(inv[0] == "addTags" for inv in fake.invoked)
