"""Main window for Anki YAML Tool GUI.

This module provides the main application window with all UI components
for building Anki decks from YAML configuration files.
"""

import logging
from pathlib import Path
from typing import Any, cast

from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from anki_yaml_tool.core.builder import AnkiBuilder
from anki_yaml_tool.core.config import load_deck_file
from anki_yaml_tool.core.exceptions import (
    ConfigValidationError,
    DataValidationError,
    DeckBuildError,
)
from anki_yaml_tool.gui.styles import MAIN_STYLESHEET
from anki_yaml_tool.gui.widgets import (
    FilePathSelector,
    StatusLabel,
    show_error_dialog,
)

logger = logging.getLogger(__name__)


class BuildThread(QThread):
    """Thread for running the deck build process without blocking the UI.

    This thread handles the deck building in the background, emitting
    progress updates and completion signals.
    """

    progress = Signal(int)
    finished = Signal(bool, str)  # success: bool, message: str

    def __init__(
        self,
        config_path: Path,
        data_path: Path | None,
        output_dir: Path,
        deck_name: str | None = None,
    ) -> None:
        """Initialize the BuildThread.

        Args:
            config_path: Path to the configuration YAML file.
            data_path: Path to the data YAML file (optional).
            output_dir: Directory to save the output deck.
            deck_name: Optional deck name override.
        """
        super().__init__()
        self._config_path = config_path
        self._data_path = data_path
        self._output_dir = output_dir
        self._deck_name = deck_name

    def run(self) -> None:
        """Execute the deck build process."""
        try:
            self.progress.emit(10)

            # Load deck file
            logger.info(f"Loading deck from {self._config_path}")
            model_config, items, file_deck_name, file_media_dir = load_deck_file(
                self._config_path
            )

            self.progress.emit(30)

            # Use provided deck-name or fall back to file deck-name
            final_deck_name = self._deck_name if self._deck_name else file_deck_name

            # Final fallback to filename if no name provided anywhere
            if final_deck_name is None:
                if self._config_path.stem == "deck":
                    final_deck_name = self._config_path.parent.name or "Deck"
                else:
                    final_deck_name = self._config_path.stem

            # Get media folder
            media_folder = file_media_dir

            model_configs = cast("list[dict[str, Any]]", [model_config])

            self.progress.emit(50)

            # Create builder
            builder = AnkiBuilder(final_deck_name, model_configs, media_folder)

            # Map model names to their field lists for easy lookup
            model_fields_map = {cfg["name"]: cfg["fields"] for cfg in model_configs}
            first_model_name = model_configs[0]["name"]

            self.progress.emit(60)

            # Add notes
            for idx, item in enumerate(items):
                # Determine which model to use for this note
                target_model_name = item.get(
                    "model", item.get("type", first_model_name)
                )
                if not isinstance(target_model_name, str):
                    target_model_name = str(target_model_name)

                if target_model_name not in model_fields_map:
                    logger.warning(
                        f"Model '{target_model_name}' not found. "
                        f"Defaulting to '{first_model_name}'."
                    )
                    target_model_name = first_model_name

                fields = model_fields_map[target_model_name]

                # Create a case-insensitive lookup dictionary
                item_lower = {k.lower(): v for k, v in item.items()}

                # Map YAML keys to model fields in order
                field_values = [str(item_lower.get(f.lower(), "")) for f in fields]

                # Get tags
                tags_raw = item.get("tags", [])
                tags: list[str] = (
                    tags_raw if isinstance(tags_raw, list) else [str(tags_raw)]
                )

                if "id" in item:
                    tags.append(f"id::{item['id']}")

                builder.add_note(field_values, tags=tags, model_name=target_model_name)

                # Update progress for each note batch
                if idx % 10 == 0:
                    progress_value = 60 + int((idx / len(items)) * 20)
                    self.progress.emit(progress_value)

            self.progress.emit(80)

            # Write to file
            output_path = self._output_dir / f"{final_deck_name.replace(' ', '_')}.apkg"
            builder.write_to_file(output_path)

            self.progress.emit(100)
            self.finished.emit(True, f"Deck built successfully: {output_path}")

        except (ConfigValidationError, DataValidationError, DeckBuildError) as e:
            logger.error(f"Build error: {e}")
            self.finished.emit(False, str(e))
        except Exception as e:
            logger.exception("Unexpected error during build")
            self.finished.emit(False, f"Unexpected error: {e}")


class AnkiDeckToolWindow(QMainWindow):
    """Main application window for Anki YAML Tool.

    Provides a GUI for selecting configuration, data, and output
    files, then building Anki decks from YAML files.
    """

    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()
        self._build_thread: BuildThread | None = None
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        self.setWindowTitle("Anki YAML Tool")
        self.setMinimumSize(600, 500)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Configuration File Section
        config_group = QGroupBox("Configuration File")
        config_layout = QVBoxLayout(config_group)
        self._config_selector = FilePathSelector(
            label="Configuration File:",
            file_filter="YAML Files (*.yaml *.yml);;All Files (*)",
        )
        config_layout.addWidget(self._config_selector)
        main_layout.addWidget(config_group)

        # Data File Section
        data_group = QGroupBox("Data File (optional)")
        data_layout = QVBoxLayout(data_group)
        self._data_selector = FilePathSelector(
            label="Data File:",
            file_filter="YAML Files (*.yaml *.yml);;All Files (*)",
        )
        data_layout.addWidget(self._data_selector)
        main_layout.addWidget(data_group)

        # Output Directory Section
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout(output_group)
        self._output_selector = FilePathSelector(
            label="Output Directory:",
            is_directory=True,
        )
        self._output_selector.set_path(str(Path.cwd()))
        output_layout.addWidget(self._output_selector)
        main_layout.addWidget(output_group)

        # Deck Name Section
        deck_name_group = QGroupBox("Deck Options")
        deck_name_layout = QVBoxLayout(deck_name_group)

        deck_name_label = QLabel("Deck Name (optional, overrides config):")
        deck_name_layout.addWidget(deck_name_label)

        self._deck_name_edit = QLineEdit()
        self._deck_name_edit.setPlaceholderText("Use name from config file...")
        deck_name_layout.addWidget(self._deck_name_edit)
        main_layout.addWidget(deck_name_group)

        # Build Button and Progress
        button_layout = QVBoxLayout()

        self._build_button = QPushButton("Build Deck")
        self._build_button.setObjectName("primary_button")
        self._build_button.clicked.connect(self._on_build_clicked)
        button_layout.addWidget(self._build_button)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setVisible(False)
        button_layout.addWidget(self._progress_bar)

        main_layout.addLayout(button_layout)

        # Status Area
        self._status_label = StatusLabel()
        main_layout.addWidget(self._status_label)

        # Add stretch to push everything up
        main_layout.addStretch()

    def _apply_styles(self) -> None:
        """Apply the stylesheet to the application."""
        self.setStyleSheet(MAIN_STYLESHEET)

    def _on_build_clicked(self) -> None:
        """Handle the Build Deck button click."""
        config_path = self._config_selector.path()

        if not config_path:
            show_error_dialog(self, "Error", "Please select a configuration file.")
            return

        config_path_obj = Path(config_path)
        if not config_path_obj.exists():
            show_error_dialog(
                self, "Error", f"Configuration file not found: {config_path}"
            )
            return

        # Get optional data path
        data_path_str = self._data_selector.path()
        data_path = Path(data_path_str) if data_path_str else None
        if data_path and not data_path.exists():
            show_error_dialog(self, "Error", f"Data file not found: {data_path}")
            return

        # Get output directory
        output_dir_str = self._output_selector.path()
        if not output_dir_str:
            show_error_dialog(self, "Error", "Please select an output directory.")
            return
        output_dir = Path(output_dir_str)
        if not output_dir.exists():
            show_error_dialog(
                self, "Error", f"Output directory not found: {output_dir}"
            )
            return

        # Get optional deck name
        deck_name = self._deck_name_edit.text().strip() or None

        # Disable UI during build
        self._set_ui_enabled(False)
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        self._status_label.set_normal("Building deck...")

        # Start build in background thread
        self._build_thread = BuildThread(
            config_path=config_path_obj,
            data_path=data_path,
            output_dir=output_dir,
            deck_name=deck_name,
        )
        self._build_thread.progress.connect(self._on_build_progress)
        self._build_thread.finished.connect(self._on_build_finished)
        self._build_thread.start()

    @Slot(int)
    def _on_build_progress(self, value: int) -> None:
        """Handle build progress updates.

        Args:
            value: Progress percentage (0-100).
        """
        self._progress_bar.setValue(value)

    @Slot(bool, str)
    def _on_build_finished(self, success: bool, message: str) -> None:
        """Handle build completion.

        Args:
            success: True if build succeeded, False otherwise.
            message: Status or error message.
        """
        self._build_thread = None
        self._set_ui_enabled(True)
        self._progress_bar.setVisible(False)

        if success:
            self._status_label.set_success(message)
        else:
            self._status_label.set_error(message)
            show_error_dialog(self, "Build Failed", message)

    def _set_ui_enabled(self, enabled: bool) -> None:
        """Enable or disable UI elements during build.

        Args:
            enabled: True to enable, False to disable.
        """
        self._config_selector.set_enabled(enabled)
        self._data_selector.set_enabled(enabled)
        self._output_selector.set_enabled(enabled)
        self._deck_name_edit.setEnabled(enabled)
        self._build_button.setEnabled(enabled)
