# Anki Python Deck Tool - Just Commands

python := "uv run --link-mode=copy"

[private]
default: help

[private]
help:
    @just --list --unsorted

# Install dependencies
install:
    uv pip install -e .

# Install development dependencies
dev:
    uv pip install -e ".[dev]"

# Run tests
test:
    uv run pytest tests/ -v

# Run linting checks
lint:
    uv run ruff check .

# Run linting checks with auto-fix
lint-fix:
    uv run ruff check . --fix

# Format code
format:
    uv run ruff format .

# Run type checking
type-check:
    uv run mypy src --ignore-missing-imports

# Run all checks
all: format lint-fix lint type-check test

# Clean build artifacts
clean:
    uv run -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in ['build', 'dist', *pathlib.Path('.').rglob('*.egg-info'), *pathlib.Path('.').rglob('__pycache__')]]; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]"

# Build distribution packages
build:
    uv run -m build # FIX

# Build single-file executable
build-exe:
    uv run scripts/build.py

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
    uv run -m anki_yaml_tool.cli batch-build --input-dir examples --output-dir examples/tmp/ --push --delete-after
