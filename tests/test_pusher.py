"""Tests for the pusher module — push YAML-exported decks back to Anki."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from anki_yaml_tool.core.pusher import (
    _compute_note_hash,
    _map_fields_for_model,
    _normalize_fields,
    push_deck_from_dir,
)
from anki_yaml_tool.core.exceptions import AnkiConnectError


# ──────────────────── helper function tests ────────────────────


class TestComputeNoteHash:
    def test_deterministic(self) -> None:
        h1 = _compute_note_hash(1, {"Front": "Q", "Back": "A"}, ["tag1"])
        h2 = _compute_note_hash(1, {"Front": "Q", "Back": "A"}, ["tag1"])
        assert h1 == h2

    def test_different_fields_yield_different_hash(self) -> None:
        h1 = _compute_note_hash(1, {"Front": "Q"}, [])
        h2 = _compute_note_hash(1, {"Front": "X"}, [])
        assert h1 != h2

    def test_none_note_id(self) -> None:
        h = _compute_note_hash(None, {"Front": "Q"}, ["t"])
        assert isinstance(h, str)


class TestNormalizeFields:
    def test_dict_value_extracts_value_key(self) -> None:
        result = _normalize_fields({"Front": {"value": "question"}})
        assert result == {"front": "question"}

    def test_plain_string(self) -> None:
        result = _normalize_fields({"Back": "answer"})
        assert result == {"back": "answer"}

    def test_none_becomes_empty_string(self) -> None:
        result = _normalize_fields({"Field": None})
        assert result == {"field": ""}

    def test_integer_to_string(self) -> None:
        result = _normalize_fields({"Num": 42})
        assert result == {"num": "42"}


class TestMapFieldsForModel:
    def test_maps_correct_fields(self) -> None:
        result = _map_fields_for_model(
            ["Front", "Back"], {"front": "Q", "back": "A", "extra": "x"}
        )
        assert result == {"Front": "Q", "Back": "A"}

    def test_missing_field_defaults_to_empty(self) -> None:
        result = _map_fields_for_model(["Front", "Back"], {"front": "Q"})
        assert result == {"Front": "Q", "Back": ""}

    def test_coerces_to_string(self) -> None:
        result = _map_fields_for_model(["Front"], {"front": 42})
        assert result == {"Front": "42"}


# ──────────────────── push_deck_from_dir tests ────────────────────


def _make_deck_dir(tmp_path: Path) -> Path:
    """Create a minimal deck directory with config + data."""
    deck_dir = tmp_path / "deck"
    deck_dir.mkdir()
    (deck_dir / "config.yaml").write_text(
        "name: Basic\nfields: [Front, Back]\ntemplates:\n"
        "  - name: Card 1\n    qfmt: '{{Front}}'\n    afmt: '{{Back}}'\n"
    )
    (deck_dir / "data.yaml").write_text("- front: Q1\n  back: A1\n")
    return deck_dir


@pytest.fixture
def connector() -> Mock:
    """Create a mock AnkiConnector."""
    mock = Mock()
    mock.add_note.return_value = 1001
    mock.get_notes.return_value = []
    return mock


class TestPushDeckFromDir:
    def test_missing_files_raises(self, tmp_path: Path, connector: Mock) -> None:
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        with pytest.raises(FileNotFoundError):
            push_deck_from_dir(connector, empty_dir)

    def test_add_new_notes(self, tmp_path: Path, connector: Mock) -> None:
        deck_dir = _make_deck_dir(tmp_path)
        stats = push_deck_from_dir(connector, deck_dir)

        assert stats["added"] == 1
        assert stats["updated"] == 0
        connector.add_note.assert_called_once()

    def test_update_existing_note(self, tmp_path: Path, connector: Mock) -> None:
        deck_dir = tmp_path / "deck"
        deck_dir.mkdir()
        (deck_dir / "config.yaml").write_text(
            "name: Basic\nfields: [Front, Back]\ntemplates:\n"
            "  - name: Card 1\n    qfmt: '{{Front}}'\n    afmt: '{{Back}}'\n"
        )
        (deck_dir / "data.yaml").write_text(
            "- front: Q1\n  back: A1\n  note_id: 999\n"
        )

        stats = push_deck_from_dir(connector, deck_dir)

        assert stats["updated"] == 1
        connector.update_note_fields.assert_called_once()

    def test_sync_triggers_connector_sync(
        self, tmp_path: Path, connector: Mock
    ) -> None:
        deck_dir = _make_deck_dir(tmp_path)
        push_deck_from_dir(connector, deck_dir, sync=True)

        connector.sync.assert_called_once()

    def test_custom_deck_name(self, tmp_path: Path, connector: Mock) -> None:
        deck_dir = _make_deck_dir(tmp_path)
        push_deck_from_dir(connector, deck_dir, deck_name="Custom")

        call_args = connector.add_note.call_args
        assert call_args[0][0] == "Custom"

    def test_media_upload(self, tmp_path: Path, connector: Mock) -> None:
        deck_dir = tmp_path / "deck"
        deck_dir.mkdir()
        (deck_dir / "config.yaml").write_text(
            "name: Basic\nfields: [Front, Back]\ntemplates:\n"
            "  - name: Card 1\n    qfmt: '{{Front}}'\n    afmt: '{{Back}}'\n"
        )
        # Reference an image in the field
        (deck_dir / "data.yaml").write_text(
            '- front: \'<img src="photo.jpg">\'\n  back: A1\n'
        )
        media_dir = deck_dir / "media"
        media_dir.mkdir()
        (media_dir / "photo.jpg").write_bytes(b"fake img")

        push_deck_from_dir(connector, deck_dir)

        connector.store_media_file.assert_called_once()

    def test_incremental_skips_unchanged(
        self, tmp_path: Path, connector: Mock
    ) -> None:
        deck_dir = tmp_path / "deck"
        deck_dir.mkdir()
        (deck_dir / "config.yaml").write_text(
            "name: Basic\nfields: [Front, Back]\ntemplates:\n"
            "  - name: Card 1\n    qfmt: '{{Front}}'\n    afmt: '{{Back}}'\n"
        )
        (deck_dir / "data.yaml").write_text(
            "- front: Q1\n  back: A1\n  note_id: 100\n"
        )

        # Simulate existing note with same content
        connector.get_notes.return_value = [
            {
                "noteId": 100,
                "fields": {"Front": {"value": "Q1"}, "Back": {"value": "A1"}},
                "tags": [],
                "modelName": "Basic",
            }
        ]

        stats = push_deck_from_dir(connector, deck_dir, incremental=True)
        assert stats["unchanged"] == 1
        assert stats["updated"] == 0

    def test_replace_deletes_extra_notes(
        self, tmp_path: Path, connector: Mock
    ) -> None:
        deck_dir = tmp_path / "deck"
        deck_dir.mkdir()
        (deck_dir / "config.yaml").write_text(
            "name: Basic\nfields: [Front, Back]\ntemplates:\n"
            "  - name: Card 1\n    qfmt: '{{Front}}'\n    afmt: '{{Back}}'\n"
        )
        (deck_dir / "data.yaml").write_text(
            "- front: Q1\n  back: A1\n  note_id: 100\n"
        )

        # Anki has note 100 and note 200 — note 200 should be deleted
        connector.get_notes.return_value = [
            {
                "noteId": 100,
                "fields": {"Front": {"value": "Q1"}, "Back": {"value": "A1"}},
                "tags": [],
            },
            {
                "noteId": 200,
                "fields": {"Front": {"value": "old"}, "Back": {"value": "old"}},
                "tags": [],
            },
        ]

        stats = push_deck_from_dir(connector, deck_dir, replace=True)
        assert stats["deleted"] == 1
        connector.delete_notes.assert_called_once_with([200])

    def test_update_error_fallback_to_add(
        self, tmp_path: Path, connector: Mock
    ) -> None:
        deck_dir = tmp_path / "deck"
        deck_dir.mkdir()
        (deck_dir / "config.yaml").write_text(
            "name: Basic\nfields: [Front, Back]\ntemplates:\n"
            "  - name: Card 1\n    qfmt: '{{Front}}'\n    afmt: '{{Back}}'\n"
        )
        (deck_dir / "data.yaml").write_text(
            "- front: Q1\n  back: A1\n  note_id: 999\n"
        )

        # Simulate "note not found" error on update
        connector.update_note_fields.side_effect = AnkiConnectError(
            "note not found", action="updateNoteFields"
        )
        connector.add_note.return_value = 1001

        stats = push_deck_from_dir(connector, deck_dir)
        # Should fall back to adding
        assert stats["added"] == 1
        connector.add_note.assert_called_once()

    def test_deleted_yaml_items(self, tmp_path: Path, connector: Mock) -> None:
        """Notes with _deleted: true should trigger deletion."""
        deck_dir = tmp_path / "deck"
        deck_dir.mkdir()
        (deck_dir / "config.yaml").write_text(
            "name: Basic\nfields: [Front, Back]\ntemplates:\n"
            "  - name: Card 1\n    qfmt: '{{Front}}'\n    afmt: '{{Back}}'\n"
        )
        (deck_dir / "data.yaml").write_text(
            "- front: Q1\n  note_id: 100\n  _deleted: true\n"
        )

        connector.get_notes.return_value = [
            {
                "noteId": 100,
                "fields": {"Front": {"value": "Q1"}, "Back": {"value": ""}},
                "tags": [],
            }
        ]

        stats = push_deck_from_dir(connector, deck_dir, replace=True)
        assert stats["deleted"] >= 1
