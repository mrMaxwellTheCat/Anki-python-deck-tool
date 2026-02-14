"""QSS stylesheet definitions for the Anki YAML Tool GUI.

This module contains the Qt Style Sheets (QSS) used to style the GUI
components with a modern, consistent look.
"""

# Base stylesheet for the application
MAIN_STYLESHEET = """
QMainWindow {
    background-color: #f5f5f5;
}

QWidget {
    font-family: "Segoe UI", "Ubuntu", "Sans-serif";
    font-size: 10pt;
}

QLabel {
    color: #333333;
    padding: 2px;
}

QLineEdit {
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 6px;
    background-color: white;
    selection-background-color: #0078d4;
}

QLineEdit:focus {
    border: 1px solid #0078d4;
}

QPushButton {
    background-color: #f0f0f0;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 6px 16px;
    color: #333333;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #e0e0e0;
    border: 1px solid #bbbbbb;
}

QPushButton:pressed {
    background-color: #d0d0d0;
}

QPushButton:disabled {
    background-color: #f5f5f5;
    color: #aaaaaa;
}

QPushButton#primary_button {
    background-color: #0078d4;
    color: white;
    border: 1px solid #006cbd;
    font-weight: bold;
}

QPushButton#primary_button:hover {
    background-color: #106ebe;
    border: 1px solid #0d5aa7;
}

QPushButton#primary_button:pressed {
    background-color: #005a9e;
}

QPushButton#primary_button:disabled {
    background-color: #c5c5c5;
    color: #888888;
}

QProgressBar {
    border: 1px solid #cccccc;
    border-radius: 4px;
    text-align: center;
    background-color: #f0f0f0;
}

QProgressBar::chunk {
    background-color: #107c10;
    border-radius: 3px;
}

QGroupBox {
    border: 1px solid #cccccc;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
    background-color: transparent;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 8px;
    color: #0078d4;
}

QFileDialog {
    font-size: 10pt;
}

QMessageBox {
    font-size: 10pt;
}

QMessageBox QLabel {
    font-size: 10pt;
    color: #333333;
}
"""

# Status message styles
STATUS_STYLES = """
QLabel#status_label {
    padding: 8px;
    border-radius: 4px;
}

QLabel#status_label.normal {
    background-color: transparent;
    color: #333333;
}

QLabel#status_label.success {
    background-color: #dff6dd;
    color: #107c10;
}

QLabel#status_label.error {
    background-color: #fde7e9;
    color: #a80000;
}

QLabel#status_label.warning {
    background-color: #fff4ce;
    color: #797673;
}
"""
