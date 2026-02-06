# Anki Python Deck Tool - Just Commands
# Use PowerShell on Windows for better compatibility
set shell := ["powershell.exe", "-c"]

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

# Run all checks
all: format lint lint-fix type-check test

# Build and push a specific example deck
_build-push-example NAME:
    @python scripts/print_color.py "36" "🔨 Building {{NAME}} example..."
    @python -m anki_yaml_tool.cli build --file examples/{{NAME}}/deck.yaml --output examples/{{NAME}}/deck.apkg
    @python scripts/print_color.py "33" "📤 Pushing to Anki..."
    @python -m anki_yaml_tool.cli push --apkg examples/{{NAME}}/deck.apkg
    @python scripts/print_color.py "32" "✅ Done!"
    @python -c "print()"

# Build and push audio example
example-audio:
    @just _build-push-example audio

# Build and push basic example
example-basic:
    @just _build-push-example basic

# Build and push cloze example
example-cloze:
    @just _build-push-example cloze

# Build and push historical example
example-historical:
    @just _build-push-example historical

# Build and push language learning example
example-language-learning:
    @just _build-push-example language-learning

# Build and push math example
example-math:
    @just _build-push-example math

# Build and push medical example
example-medical:
    @just _build-push-example medical

# Build and push technical example
example-technical:
    @just _build-push-example technical

# Build and push test example
example-test:
    @just _build-push-example test

# Build and push all example decks
examples: example-audio example-basic example-cloze example-historical example-language-learning example-math example-medical example-technical example-test
