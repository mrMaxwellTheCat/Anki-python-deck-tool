"""Graphical User Interface for Anki Python Deck Tool.

This module provides a simple GUI for users who prefer not to use the command line.
"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

import yaml

from anki_tool.core.builder import AnkiBuilder
from anki_tool.core.connector import AnkiConnector
from anki_tool.core.exceptions import (
    AnkiConnectError,
    ConfigValidationError,
    DataValidationError,
    DeckBuildError,
)


class AnkiToolGUI:
    """Main GUI window for Anki Python Deck Tool.

    Provides a graphical interface for building and pushing Anki decks.
    """

    def __init__(self, root: tk.Tk):
        """Initialize the GUI.

        Args:
            root: The root tkinter window.
        """
        self.root = root
        self.root.title("Anki Python Deck Tool")
        self.root.geometry("700x500")
        self.root.resizable(True, True)

        # Variables
        self.data_file_var = tk.StringVar()
        self.config_file_var = tk.StringVar()
        self.output_file_var = tk.StringVar(value="deck.apkg")
        self.deck_name_var = tk.StringVar(value="Generated Deck")
        self.sync_var = tk.BooleanVar(value=False)

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create and layout all GUI widgets."""
        # Create main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Anki Python Deck Tool",
            font=("Helvetica", 16, "bold"),
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Data file selection
        ttk.Label(main_frame, text="Data File (YAML):").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        ttk.Entry(main_frame, textvariable=self.data_file_var, width=50).grid(
            row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5
        )
        ttk.Button(main_frame, text="Browse...", command=self._browse_data_file).grid(
            row=1, column=2, pady=5
        )

        # Config file selection
        ttk.Label(main_frame, text="Config File (YAML):").grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        ttk.Entry(main_frame, textvariable=self.config_file_var, width=50).grid(
            row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5
        )
        ttk.Button(
            main_frame, text="Browse...", command=self._browse_config_file
        ).grid(row=2, column=2, pady=5)

        # Output file selection
        ttk.Label(main_frame, text="Output File (.apkg):").grid(
            row=3, column=0, sticky=tk.W, pady=5
        )
        ttk.Entry(main_frame, textvariable=self.output_file_var, width=50).grid(
            row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=5
        )
        ttk.Button(
            main_frame, text="Browse...", command=self._browse_output_file
        ).grid(row=3, column=2, pady=5)

        # Deck name
        ttk.Label(main_frame, text="Deck Name:").grid(
            row=4, column=0, sticky=tk.W, pady=5
        )
        ttk.Entry(main_frame, textvariable=self.deck_name_var, width=50).grid(
            row=4, column=1, sticky=(tk.W, tk.E), pady=5, padx=5
        )

        # Separator
        ttk.Separator(main_frame, orient="horizontal").grid(
            row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20
        )

        # Build button
        build_button = ttk.Button(
            main_frame,
            text="Build Deck",
            command=self._build_deck,
            style="Accent.TButton",
        )
        build_button.grid(row=6, column=0, columnspan=3, pady=10, ipadx=20, ipady=5)

        # Separator
        ttk.Separator(main_frame, orient="horizontal").grid(
            row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20
        )

        # Push section
        ttk.Label(
            main_frame, text="Push to Anki (Optional)", font=("Helvetica", 12, "bold")
        ).grid(row=8, column=0, columnspan=3, pady=(0, 10))

        # Sync checkbox
        ttk.Checkbutton(
            main_frame, text="Sync with AnkiWeb after import", variable=self.sync_var
        ).grid(row=9, column=0, columnspan=3, pady=5)

        # Push button
        push_button = ttk.Button(
            main_frame,
            text="Push to Anki",
            command=self._push_deck,
            style="Accent.TButton",
        )
        push_button.grid(row=10, column=0, columnspan=3, pady=10, ipadx=20, ipady=5)

        # Status bar
        self.status_label = ttk.Label(
            main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_label.grid(
            row=11, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(20, 0)
        )

        # Configure column weights for resizing
        main_frame.columnconfigure(1, weight=1)

    def _browse_data_file(self) -> None:
        """Open file dialog to select data YAML file."""
        filename = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")],
        )
        if filename:
            self.data_file_var.set(filename)

    def _browse_config_file(self) -> None:
        """Open file dialog to select config YAML file."""
        filename = filedialog.askopenfilename(
            title="Select Config File",
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")],
        )
        if filename:
            self.config_file_var.set(filename)

    def _browse_output_file(self) -> None:
        """Open file dialog to select output .apkg file location."""
        filename = filedialog.asksaveasfilename(
            title="Save Deck As",
            defaultextension=".apkg",
            filetypes=[("Anki Package", "*.apkg"), ("All files", "*.*")],
        )
        if filename:
            self.output_file_var.set(filename)

    def _update_status(self, message: str) -> None:
        """Update status bar message.

        Args:
            message: Status message to display.
        """
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def _build_deck(self) -> None:
        """Build the Anki deck from selected files."""
        data_file = self.data_file_var.get()
        config_file = self.config_file_var.get()
        output_file = self.output_file_var.get()
        deck_name = self.deck_name_var.get()

        # Validation
        if not data_file:
            messagebox.showerror("Error", "Please select a data file")
            return
        if not config_file:
            messagebox.showerror("Error", "Please select a config file")
            return
        if not output_file:
            messagebox.showerror("Error", "Please specify an output file")
            return
        if not deck_name:
            messagebox.showerror("Error", "Please enter a deck name")
            return

        try:
            self._update_status(f"Building deck '{deck_name}'...")

            # Load configuration
            with open(config_file, encoding="utf-8") as f:
                model_config = yaml.safe_load(f)

            if not model_config:
                raise ConfigValidationError("Config file is empty", config_file)

            # Load data
            with open(data_file, encoding="utf-8") as f:
                items = yaml.safe_load(f)

            if not items:
                raise DataValidationError("Data file is empty", data_file)

            builder = AnkiBuilder(deck_name, model_config)

            for item in items:
                # Map YAML keys to model fields in order
                field_values = [
                    str(item.get(f.lower(), "")) for f in model_config["fields"]
                ]
                tags = item.get("tags", [])
                if "id" in item:
                    tags.append(f"id::{item['id']}")

                builder.add_note(field_values, tags=tags)

            builder.write_to_file(Path(output_file))

            self._update_status(f"Successfully created {output_file}")
            messagebox.showinfo(
                "Success", f"Deck '{deck_name}' successfully created at:\n{output_file}"
            )

        except (ConfigValidationError, DataValidationError, DeckBuildError) as e:
            self._update_status("Build failed")
            messagebox.showerror("Build Error", str(e))
        except Exception as e:
            self._update_status("Build failed")
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred:\n{e}")

    def _push_deck(self) -> None:
        """Push the deck to Anki via AnkiConnect."""
        output_file = self.output_file_var.get()
        sync = self.sync_var.get()

        # Validation
        if not output_file:
            messagebox.showerror("Error", "Please specify the .apkg file to push")
            return

        if not Path(output_file).exists():
            messagebox.showerror(
                "Error", f"File not found: {output_file}\nPlease build the deck first."
            )
            return

        try:
            self._update_status(f"Pushing {output_file} to Anki...")
            connector = AnkiConnector()
            connector.import_package(Path(output_file))

            if sync:
                self._update_status("Syncing with AnkiWeb...")
                connector.sync()

            self._update_status("Successfully imported into Anki")
            messagebox.showinfo(
                "Success", f"Deck successfully imported into Anki{' and synced' if sync else ''}"
            )

        except AnkiConnectError as e:
            self._update_status("Push failed")
            messagebox.showerror(
                "AnkiConnect Error",
                f"Failed to connect to Anki:\n{e}\n\nMake sure Anki is running with the AnkiConnect add-on enabled.",
            )
        except Exception as e:
            self._update_status("Push failed")
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred:\n{e}")


def main() -> None:
    """Entry point for the GUI application."""
    root = tk.Tk()
    AnkiToolGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
