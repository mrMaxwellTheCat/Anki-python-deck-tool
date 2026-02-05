"""Tests for custom exceptions."""

from anki_tool.core.exceptions import (
    AnkiConnectError,
    AnkiToolError,
    ConfigValidationError,
    DataValidationError,
    DeckBuildError,
    MediaMissingError,
)


def test_anki_tool_error():
    """Test base AnkiToolError exception."""
    error = AnkiToolError("Base error")
    assert str(error) == "Base error"
    assert isinstance(error, Exception)


def test_config_validation_error():
    """Test ConfigValidationError with path."""
    error = ConfigValidationError("Invalid config", config_path="configs/test.yaml")
    assert "Invalid config" in str(error)
    assert "configs/test.yaml" in str(error)
    assert error.config_path == "configs/test.yaml"


def test_config_validation_error_without_path():
    """Test ConfigValidationError without path."""
    error = ConfigValidationError("Invalid config")
    assert str(error) == "Invalid config"
    assert error.config_path is None


def test_data_validation_error():
    """Test DataValidationError with path."""
    error = DataValidationError("Invalid data", data_path="data/test.yaml")
    assert "Invalid data" in str(error)
    assert "data/test.yaml" in str(error)
    assert error.data_path == "data/test.yaml"


def test_media_missing_error():
    """Test MediaMissingError with path."""
    error = MediaMissingError("File not found", media_path="media/image.jpg")
    assert "File not found" in str(error)
    assert "media/image.jpg" in str(error)
    assert error.media_path == "media/image.jpg"


def test_ankiconnect_error():
    """Test AnkiConnectError with action."""
    error = AnkiConnectError("Connection failed", action="importPackage")
    assert "Connection failed" in str(error)
    assert "importPackage" in str(error)
    assert error.action == "importPackage"


def test_deck_build_error():
    """Test DeckBuildError."""
    error = DeckBuildError("Build failed")
    assert str(error) == "Build failed"
    assert isinstance(error, AnkiToolError)
