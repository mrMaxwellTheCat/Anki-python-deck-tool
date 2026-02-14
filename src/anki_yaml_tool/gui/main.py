"""Main entry point for the Anki YAML Tool GUI.

This module provides the main() function that initializes the Qt
application and shows the main window.
"""

import logging
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from anki_yaml_tool.gui.window import AnkiDeckToolWindow

logger = logging.getLogger(__name__)


def main() -> int:
    """Initialize and run the GUI application.

    Sets up the Qt application, creates the main window, and runs
    the event loop. Handles exceptions gracefully with error dialogs.

    Returns:
        The exit code of the application (0 for success, non-zero for error).
    """
    # Create the Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Anki YAML Tool")
    app.setApplicationVersion("0.6.0")

    # Set up exception handling
    def exception_hook(
        exc_type: type, exc_value: Exception, exc_traceback: Exception
    ) -> None:
        """Handle uncaught exceptions.

        Args:
            exc_type: The exception class.
            exc_value: The exception instance.
            exc_traceback: The traceback object.
        """
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't show dialog for Ctrl+C
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.critical(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )
        error_msg = f"{exc_type.__name__}: {exc_value}"
        QMessageBox.critical(
            None,
            "Unexpected Error",
            f"An unexpected error occurred:\n\n{error_msg}\n\nPlease check the logs for details.",
        )

    sys.excepthook = exception_hook

    # Create and show the main window
    window = AnkiDeckToolWindow()
    window.show()

    # Run the event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
