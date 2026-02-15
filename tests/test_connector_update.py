"""Tests for AnkiConnector update/add wrappers."""

from unittest.mock import Mock

import pytest

from anki_yaml_tool.core.connector import AnkiConnector
from anki_yaml_tool.core.exceptions import AnkiConnectError


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


def test_update_note_fields_calls_invoker(connector: AnkiConnector) -> None:
    connector._session.post.return_value = _mock_response()

    connector.update_note_fields(123, {"Front": "Q"})

    call_args = connector._session.post.call_args
    assert call_args is not None
    assert call_args[1]["json"]["action"] == "updateNoteFields"
    params = call_args[1]["json"]["params"]
    assert params["note"]["id"] == 123


def test_add_note_returns_id(connector: AnkiConnector) -> None:
    connector._session.post.return_value = _mock_response(result=555)

    nid = connector.add_note("Deck", "Model", {"Front": "Q"}, tags=["t1"])
    assert nid == 555


def test_add_note_raises_on_unexpected_response(connector: AnkiConnector) -> None:
    connector._session.post.return_value = _mock_response(result=None)

    with pytest.raises(AnkiConnectError):
        connector.add_note("D", "M", {"Front": "Q"})
