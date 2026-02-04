"""Tests for the AnkiConnector class."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from anki_tool.core.connector import AnkiConnector
from anki_tool.core.exceptions import AnkiConnectError


@patch("anki_tool.core.connector.requests.post")
def test_invoke_success(mock_post):
    """Test successful AnkiConnect API invocation."""
    mock_response = Mock()
    mock_response.json.return_value = {"result": "success", "error": None}
    mock_post.return_value = mock_response

    connector = AnkiConnector()
    result = connector.invoke("version")

    assert result == "success"
    mock_post.assert_called_once()


@patch("anki_tool.core.connector.requests.post")
def test_invoke_connection_error(mock_post):
    """Test handling of connection errors.

    Note: The connector wraps requests.exceptions.ConnectionError into
    AnkiConnectError, but the mock here raises a generic Exception to test
    unexpected error scenarios.
    """
    mock_post.side_effect = Exception("Connection refused")

    connector = AnkiConnector()

    # Testing generic exception handling (not AnkiConnectError specifically)
    with pytest.raises(Exception, match="Connection refused"):
        connector.invoke("version")


@patch("anki_tool.core.connector.requests.post")
def test_invoke_ankiconnect_error(mock_post):
    """Test handling of AnkiConnect API errors."""
    mock_response = Mock()
    mock_response.json.return_value = {"result": None, "error": "Invalid action"}
    mock_post.return_value = mock_response

    connector = AnkiConnector()

    with pytest.raises(AnkiConnectError) as exc_info:
        connector.invoke("invalid_action")

    assert "Invalid action" in str(exc_info.value)


@patch("anki_tool.core.connector.requests.post")
def test_import_package(mock_post, tmp_path):
    """Test importing an .apkg package."""
    mock_response = Mock()
    mock_response.json.return_value = {"result": None, "error": None}
    mock_post.return_value = mock_response

    # Create a dummy .apkg file
    apkg_file = tmp_path / "test_deck.apkg"
    apkg_file.write_text("fake apkg content")

    connector = AnkiConnector()
    connector.import_package(apkg_file)

    # Should call importPackage and reloadCollection
    assert mock_post.call_count == 2


def test_import_package_nonexistent_file():
    """Test that importing a nonexistent file raises FileNotFoundError."""
    connector = AnkiConnector()

    with pytest.raises(FileNotFoundError):
        connector.import_package(Path("/nonexistent/file.apkg"))


@patch("anki_tool.core.connector.requests.post")
def test_sync(mock_post):
    """Test triggering a sync with AnkiWeb."""
    mock_response = Mock()
    mock_response.json.return_value = {"result": None, "error": None}
    mock_post.return_value = mock_response

    connector = AnkiConnector()
    connector.sync()

    mock_post.assert_called_once()


@patch("anki_tool.core.connector.requests.post")
def test_store_media_file(mock_post, tmp_path):
    """Test storing a media file in Anki."""
    mock_response = Mock()
    mock_response.json.return_value = {"result": None, "error": None}
    mock_post.return_value = mock_response

    # Create a dummy media file
    media_file = tmp_path / "test_image.jpg"
    media_file.write_bytes(b"fake image data")

    connector = AnkiConnector()
    connector.store_media_file(media_file)

    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[1]["json"]["action"] == "storeMediaFile"


@patch("anki_tool.core.connector.requests.post")
def test_store_media_file_custom_filename(mock_post, tmp_path):
    """Test storing a media file with a custom filename."""
    mock_response = Mock()
    mock_response.json.return_value = {"result": None, "error": None}
    mock_post.return_value = mock_response

    # Create a dummy media file
    media_file = tmp_path / "original_name.jpg"
    media_file.write_bytes(b"fake image data")

    connector = AnkiConnector()
    connector.store_media_file(media_file, filename="custom_name.jpg")

    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[1]["json"]["params"]["filename"] == "custom_name.jpg"
