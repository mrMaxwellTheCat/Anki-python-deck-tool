"""Tests for the AnkiConnector class."""

from pathlib import Path
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
    """Create a mock response object."""
    resp = Mock()
    resp.json.return_value = {"result": result, "error": error}
    return resp


def test_invoke_success(connector: AnkiConnector) -> None:
    """Test successful AnkiConnect API invocation."""
    connector._session.post.return_value = _mock_response(result="success")

    result = connector.invoke("version")

    assert result == "success"
    connector._session.post.assert_called_once()


def test_invoke_connection_error(connector: AnkiConnector) -> None:
    """Test handling of connection errors.

    The connector wraps requests.exceptions.ConnectionError into
    AnkiConnectError with a descriptive message.
    """
    import requests

    connector._session.post.side_effect = requests.exceptions.ConnectionError(
        "Connection refused"
    )

    with pytest.raises(AnkiConnectError, match="Could not connect to Anki"):
        connector.invoke("version")


def test_invoke_ankiconnect_error(connector: AnkiConnector) -> None:
    """Test handling of AnkiConnect API errors."""
    connector._session.post.return_value = _mock_response(error="Invalid action")

    with pytest.raises(AnkiConnectError) as exc_info:
        connector.invoke("invalid_action")

    assert "Invalid action" in str(exc_info.value)


def test_import_package(connector: AnkiConnector, tmp_path: Path) -> None:
    """Test importing an .apkg package."""
    connector._session.post.return_value = _mock_response()

    apkg_file = tmp_path / "test_deck.apkg"
    apkg_file.write_text("fake apkg content")

    connector.import_package(apkg_file)

    # Should call importPackage and reloadCollection
    assert connector._session.post.call_count == 2


def test_import_package_nonexistent_file() -> None:
    """Test that importing a nonexistent file raises FileNotFoundError."""
    connector = AnkiConnector()

    with pytest.raises(FileNotFoundError):
        connector.import_package(Path("/nonexistent/file.apkg"))


def test_sync(connector: AnkiConnector) -> None:
    """Test triggering a sync with AnkiWeb."""
    connector._session.post.return_value = _mock_response()

    connector.sync()

    connector._session.post.assert_called_once()


def test_store_media_file(connector: AnkiConnector, tmp_path: Path) -> None:
    """Test storing a media file in Anki."""
    connector._session.post.return_value = _mock_response()

    media_file = tmp_path / "test_image.jpg"
    media_file.write_bytes(b"fake image data")

    connector.store_media_file(media_file)

    connector._session.post.assert_called_once()
    call_args = connector._session.post.call_args
    assert call_args[1]["json"]["action"] == "storeMediaFile"


def test_store_media_file_custom_filename(
    connector: AnkiConnector, tmp_path: Path
) -> None:
    """Test storing a media file with a custom filename."""
    connector._session.post.return_value = _mock_response()

    media_file = tmp_path / "original_name.jpg"
    media_file.write_bytes(b"fake image data")

    connector.store_media_file(media_file, filename="custom_name.jpg")

    connector._session.post.assert_called_once()
    call_args = connector._session.post.call_args
    assert call_args[1]["json"]["params"]["filename"] == "custom_name.jpg"
