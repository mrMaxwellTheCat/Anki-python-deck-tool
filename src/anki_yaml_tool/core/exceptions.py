"""Custom exceptions for the `anki_yaml_tool` package.

This module defines domain-specific exceptions used across `anki_yaml_tool` to provide clearer error handling throughout the application.
"""

__all__ = [
    "AnkiToolError",
    "ConfigValidationError",
    "DataValidationError",
    "MediaMissingError",
    "AnkiConnectError",
    "DeckBuildError",
]


class AnkiToolError(Exception):
    """Base exception for all `anki_yaml_tool` errors."""

    pass


class ConfigValidationError(AnkiToolError):
    """Raised when a configuration file is invalid or malformed.

    Args:
        message: Description of the validation error.
        config_path: Optional path to the invalid config file.
    """

    def __init__(self, message: str, config_path: str | None = None):
        self.config_path = config_path
        if config_path:
            message = f"{message} (config: '{config_path}')"
        super().__init__(message)


class DataValidationError(AnkiToolError):
    """Raised when data file content is invalid or malformed.

    Args:
        message: Description of the validation error.
        data_path: Optional path to the invalid data file.
    """

    def __init__(self, message: str, data_path: str | None = None):
        self.data_path = data_path
        if data_path:
            message = f"{message} (data: {data_path})"
        super().__init__(message)


class MediaMissingError(AnkiToolError):
    """Raised when a referenced media file cannot be found.

    Args:
        message: Description of the missing media.
        media_path: Path to the missing media file.
    """

    def __init__(self, message: str, media_path: str | None = None):
        self.media_path = media_path
        if media_path:
            message = f"{message} (media: {media_path})"
        super().__init__(message)


class AnkiConnectError(AnkiToolError):
    """Raised when communication with AnkiConnect fails.

    Args:
        message: Description of the connection error.
        action: Optional AnkiConnect action that failed.
    """

    def __init__(self, message: str, action: str | None = None):
        self.action = action
        if action:
            message = f"{message} (action: {action})"
        super().__init__(message)


class DeckBuildError(AnkiToolError):
    """Raised when deck building fails.

    Args:
        message: Description of the build error.
    """

    pass
