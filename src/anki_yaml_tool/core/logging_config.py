"""Logging configuration for Anki Python Deck Tool.

This module provides logging setup with configurable verbosity levels
for CLI commands.
"""

import logging

import click

# Custom log format
LOG_FORMAT = "%(levelname)s: %(message)s"
LOG_FORMAT_VERBOSE = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FORMAT_DEBUG = (
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)

# Logger for the package
logger = logging.getLogger("anki_yaml_tool")


class ClickHandler(logging.Handler):
    """Custom logging handler that uses click.echo for output.

    This handler supports colored output based on log level.
    """

    COLORS = {
        logging.DEBUG: "cyan",
        logging.INFO: None,  # Default color
        logging.WARNING: "yellow",
        logging.ERROR: "red",
        logging.CRITICAL: "bright_red",
    }

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record using click.echo."""
        try:
            msg = self.format(record)
            color = self.COLORS.get(record.levelno)
            if color:
                msg = click.style(msg, fg=color)
            click.echo(msg, err=record.levelno >= logging.WARNING)
        except (OSError, ValueError):
            self.handleError(record)


def setup_logging(verbosity: int = 0, quiet: bool = False) -> None:
    """Configure logging based on verbosity level.

    Args:
        verbosity: Number of -v flags passed (0=WARNING, 1=INFO, 2+=DEBUG)
        quiet: If True, suppress all output except errors
    """
    # Determine log level
    if quiet:
        level = logging.ERROR
    elif verbosity == 0:
        level = logging.WARNING
    elif verbosity == 1:
        level = logging.INFO
    else:  # verbosity >= 2
        level = logging.DEBUG

    # Determine format based on verbosity
    if verbosity >= 2:
        log_format = LOG_FORMAT_DEBUG
    elif verbosity == 1:
        log_format = LOG_FORMAT_VERBOSE
    else:
        log_format = LOG_FORMAT

    # Clear any existing handlers
    logger.handlers.clear()

    # Create and configure handler
    handler = ClickHandler()
    handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(handler)
    logger.setLevel(level)

    # Also configure the root logger to catch third-party logs at DEBUG level
    if verbosity >= 2:
        logging.basicConfig(
            level=logging.DEBUG,
            format=log_format,
            handlers=[handler],
        )


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger for the given name.

    Args:
        name: Logger name. If None, returns the package logger.

    Returns:
        Logger instance.
    """
    if name is None:
        return logger
    return logging.getLogger(f"anki_yaml_tool.{name}")
