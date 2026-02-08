"""Tests for AnkiConnector read methods (deck/model/notes/media retrieval)."""

from unittest.mock import Mock, patch

from anki_yaml_tool.core.connector import AnkiConnector


@patch("anki_yaml_tool.core.connector.requests.post")
def test_get_deck_names(mock_post):
    mock_resp = Mock()
    mock_resp.json.return_value = {"result": ["B", "A"], "error": None}
    mock_post.return_value = mock_resp

    c = AnkiConnector()
    names = c.get_deck_names()
    assert names == ["A", "B"]


@patch("anki_yaml_tool.core.connector.requests.post")
def test_get_model_names(mock_post):
    mock_resp = Mock()
    mock_resp.json.return_value = {"result": ["Model1"], "error": None}
    mock_post.return_value = mock_resp

    c = AnkiConnector()
    names = c.get_model_names()
    assert names == ["Model1"]


@patch("anki_yaml_tool.core.connector.requests.post")
def test_get_notes_empty(mock_post):
    # findNotes returns empty list
    mock_find = Mock()
    mock_find.json.return_value = {"result": [], "error": None}

    mock_post.return_value = mock_find

    c = AnkiConnector()
    notes = c.get_notes("EmptyDeck")
    assert notes == []


@patch("anki_yaml_tool.core.connector.requests.post")
def test_get_notes_success(mock_post):
    # Simulate two calls: findNotes -> notesInfo
    mock_find = Mock()
    mock_find.json.return_value = {"result": [101], "error": None}

    mock_notes = Mock()
    mock_notes.json.return_value = {
        "result": [
            {
                "noteId": 101,
                "fields": {"Front": {"value": "Q1"}, "Back": {"value": "A1"}},
                "tags": ["tag1"],
                "modelName": "Basic",
            }
        ],
        "error": None,
    }

    mock_post.side_effect = [mock_find, mock_notes]

    c = AnkiConnector()
    notes = c.get_notes("MyDeck")
    assert len(notes) == 1
    assert notes[0]["noteId"] == 101
    assert notes[0]["fields"]["Front"]["value"] == "Q1"


@patch("anki_yaml_tool.core.connector.requests.post")
def test_retrieve_media_file(mock_post):
    import base64

    content = b"fake-binary"
    encoded = base64.b64encode(content).decode("utf-8")

    mock_resp = Mock()
    mock_resp.json.return_value = {"result": encoded, "error": None}
    mock_post.return_value = mock_resp

    c = AnkiConnector()
    out = c.retrieve_media_file("image.jpg")
    assert out == content
