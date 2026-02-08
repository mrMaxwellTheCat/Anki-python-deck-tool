"""Tests for AnkiConnector update/add wrappers."""

from unittest.mock import Mock, patch

from anki_yaml_tool.core.connector import AnkiConnector


@patch("anki_yaml_tool.core.connector.requests.post")
def test_update_note_fields_calls_invoker(mock_post):
    mock_resp = Mock()
    mock_resp.json.return_value = {"result": None, "error": None}
    mock_post.return_value = mock_resp

    c = AnkiConnector()
    c.update_note_fields(123, {"Front": "Q"})

    call_args = mock_post.call_args
    assert call_args is not None
    assert call_args[1]["json"]["action"] == "updateNoteFields"
    params = call_args[1]["json"]["params"]
    assert params["note"]["id"] == 123


@patch("anki_yaml_tool.core.connector.requests.post")
def test_add_note_returns_id(mock_post):
    mock_resp = Mock()
    mock_resp.json.return_value = {"result": 555, "error": None}
    mock_post.return_value = mock_resp

    c = AnkiConnector()
    nid = c.add_note("Deck", "Model", {"Front": "Q"}, tags=["t1"])
    assert nid == 555


@patch("anki_yaml_tool.core.connector.requests.post")
def test_add_note_raises_on_unexpected_response(mock_post):
    import pytest
    from anki_yaml_tool.core.exceptions import AnkiConnectError

    mock_resp = Mock()
    # Simulate unexpected (non-integer) result
    mock_resp.json.return_value = {"result": None, "error": None}
    mock_post.return_value = mock_resp

    c = AnkiConnector()
    with pytest.raises(AnkiConnectError):
        c.add_note("D", "M", {"Front": "Q"})
