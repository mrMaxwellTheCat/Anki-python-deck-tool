"""Tests for AnkiConnector read methods (deck/model/notes/media retrieval)."""

import base64

import pytest

from anki_yaml_tool.core.connector import AnkiConnector

from unittest.mock import Mock


@pytest.fixture
def connector() -> AnkiConnector:
    """Create a connector with a mocked session."""
    conn = AnkiConnector()
    conn._session = Mock()
    return conn


def _mock_response(result=None, error=None) -> Mock:
    resp = Mock()
    resp.json.return_value = {"result": result, "error": error}
    return resp


def test_get_deck_names(connector: AnkiConnector) -> None:
    connector._session.post.return_value = _mock_response(result=["B", "A"])

    names = connector.get_deck_names()
    assert names == ["A", "B"]


def test_get_model_names(connector: AnkiConnector) -> None:
    connector._session.post.return_value = _mock_response(result=["Model1"])

    names = connector.get_model_names()
    assert names == ["Model1"]


def test_get_notes_empty(connector: AnkiConnector) -> None:
    connector._session.post.return_value = _mock_response(result=[])

    notes = connector.get_notes("EmptyDeck")
    assert notes == []


def test_get_notes_success(connector: AnkiConnector) -> None:
    # Simulate two calls: findNotes -> notesInfo
    mock_find = _mock_response(result=[101])
    mock_notes = _mock_response(
        result=[
            {
                "noteId": 101,
                "fields": {"Front": {"value": "Q1"}, "Back": {"value": "A1"}},
                "tags": ["tag1"],
                "modelName": "Basic",
            }
        ]
    )
    connector._session.post.side_effect = [mock_find, mock_notes]

    notes = connector.get_notes("MyDeck")
    assert len(notes) == 1
    assert notes[0]["noteId"] == 101
    assert notes[0]["fields"]["Front"]["value"] == "Q1"


def test_retrieve_media_file(connector: AnkiConnector) -> None:
    content = b"fake-binary"
    encoded = base64.b64encode(content).decode("utf-8")

    connector._session.post.return_value = _mock_response(result=encoded)

    out = connector.retrieve_media_file("image.jpg")
    assert out == content
