"""Custom widgets for the Anki YAML Tool GUI.

This module provides reusable widgets for the application including
file path selectors, status indicators, and progress displays.
"""

import logging
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class FilePathSelector(QWidget):
    """Widget for selecting file or directory paths.

    Provides a line edit for displaying the path and a browse button
    to open a file dialog.

    Signals:
        path_changed: Emitted when the path is changed via browse.
    """

    path_changed = Signal(str)

    def __init__(
        self,
        label: str,
        file_filter: str = "All Files (*)",
        is_directory: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the FilePathSelector.

        Args:
            label: The label text for the selector.
            file_filter: Filter string for the file dialog (e.g., "YAML Files (*.yaml)").
            is_directory: If True, select directories instead of files.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._file_filter = file_filter
        self._is_directory = is_directory

        self._setup_ui(label)

    def _setup_ui(self, label: str) -> None:
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Label
        self._label = QLabel(label)
        layout.addWidget(self._label)

        # Path input and browse button
        path_layout = QHBoxLayout()
        path_layout.setSpacing(8)

        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("Select a path...")
        self._path_edit.textChanged.connect(self._on_text_changed)
        path_layout.addWidget(self._path_edit, 1)

        self._browse_btn = QPushButton("Browse...")
        self._browse_btn.clicked.connect(self._on_browse_clicked)
        path_layout.addWidget(self._browse_btn)

        layout.addLayout(path_layout)

    def _on_text_changed(self, text: str) -> None:
        """Handle text changes in the path edit."""
        self.path_changed.emit(text)

    def _on_browse_clicked(self) -> None:
        """Open file/directory dialog and update path."""
        if self._is_directory:
            path = QFileDialog.getExistingDirectory(
                self,
                "Select Directory",
                self._path_edit.text() or str(Path.home()),
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select File",
                self._path_edit.text() or str(Path.home()),
                self._file_filter,
            )

        if path:
            self._path_edit.setText(path)
            self.path_changed.emit(path)

    def path(self) -> str:
        """Get the current path.

        Returns:
            The current path as a string.
        """
        return self._path_edit.text()

    def set_path(self, path: str) -> None:
        """Set the path.

        Args:
            path: The path to set.
        """
        self._path_edit.setText(path)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the widget.

        Args:
            enabled: True to enable, False to disable.
        """
        self._path_edit.setEnabled(enabled)
        self._browse_btn.setEnabled(enabled)


class StatusLabel(QLabel):
    """Label for displaying status messages with different severity levels.

    Provides visual feedback through different background colors for
    normal, success, warning, and error states.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the StatusLabel.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setObjectName("status_label")
        self.setProperty("normal", True)
        self._set_style("normal")
        self.setText("Ready")

    def _set_style(self, style: str) -> None:
        """Apply a style class to the label.

        Args:
            style: One of 'normal', 'success', 'warning', or 'error'.
        """
        colors = {
            "normal": ("transparent", "#333333"),
            "success": ("#dff6dd", "#107c10"),
            "warning": ("#fff4ce", "#797673"),
            "error": ("#fde7e9", "#a80000"),
        }
        bg_color, fg_color = colors.get(style, ("transparent", "#333333"))
        self.setStyleSheet(
            f"""
            QLabel#status_label {{
                padding: 8px;
                border-radius: 4px;
            }}
            QLabel#status_label.{style} {{
                background-color: {bg_color};
                color: {fg_color};
            }}
        """
        )

    def set_normal(self, message: str = "Ready") -> None:
        """Display a normal status message.

        Args:
            message: The message to display.
        """
        self.setText(message)
        self._set_style("normal")

    def set_success(self, message: str) -> None:
        """Display a success status message.

        Args:
            message: The message to display.
        """
        self.setText(message)
        self._set_style("success")

    def set_warning(self, message: str) -> None:
        """Display a warning status message.

        Args:
            message: The message to display.
        """
        self.setText(message)
        self._set_style("warning")

    def set_error(self, message: str) -> None:
        """Display an error status message.

        Args:
            message: The message to display.
        """
        self.setText(message)
        self._set_style("error")


def show_error_dialog(
    parent: QWidget, title: str, message: str, details: str | None = None
) -> None:
    """Show an error message dialog.

    Args:
        parent: Parent widget for the dialog.
        title: Dialog title.
        message: Main error message.
        details: Optional detailed error information.
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    if details:
        msg_box.setDetailedText(details)
    msg_box.exec()


def show_info_dialog(parent: QWidget, title: str, message: str) -> None:
    """Show an information message dialog.

    Args:
        parent: Parent widget for the dialog.
        title: Dialog title.
        message: Information message.
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Information)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.exec()


def show_warning_dialog(parent: QWidget, title: str, message: str) -> None:
    """Show a warning message dialog.

    Args:
        parent: Parent widget for the dialog.
        title: Dialog title.
        message: Warning message.
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Warning)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.exec()
