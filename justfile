# Anki Python Deck Tool - Just Commands
# Use PowerShell on Windows for better compatibility
set shell := ["powershell.exe", "-Command"]

[private]
default: help

[private]
help:
    @just --list --unsorted

# Install dependencies
install:
    python -m pip install -e .

# Install development dependencies
dev:
    python -m pip install -e ".[dev]"
    python -m pre_commit install

# Run tests
test:
    python -m pytest tests/ -v

# Run linting checks
lint:
    python -m ruff check .

# Run linting checks with auto-fix
lint-fix:
    python -m ruff check . --fix

# Format code
format:
    python -m ruff format .

# Run type checking
type-check:
    python -m mypy src --ignore-missing-imports

# Run all checks
all: format lint-fix lint type-check test

# Clean build artifacts
clean:
    python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in ['build', 'dist', *pathlib.Path('.').rglob('*.egg-info'), *pathlib.Path('.').rglob('__pycache__')]]; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]"

# Build distribution packages
build:
    python -m build

# Build single-file executable
build-exe:
    python scripts/build.py

# Install executable system-wide (Windows)
[windows]
install-system-wide:
    powershell -ExecutionPolicy Bypass -File scripts/install-system-wide.ps1

# Install executable system-wide (Unix)
[unix]
install-system-wide:
    bash scripts/install-system-wide.sh

# Build and install executable
build-install: build-exe install-system-wide

# Build, push, and clean example decks
examples:
    python -m anki_yaml_tool.cli batch-build --input-dir examples --output-dir examples --push --delete-after
