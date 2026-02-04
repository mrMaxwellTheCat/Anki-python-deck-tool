# Project Roadmap

This document outlines the detailed development plan for the Anki Python Deck Tool.

## 1. Infrastructure (CI/CD, Packaging)

- [ ] **Packaging Upgrade**
    - [x] Create `requirements.txt` for consistent environment setup.
    - [ ] Evaluate `poetry` or `uv` for modern dependency management.
    - [ ] Create `pyproject.toml` configuration for build system (Hatchling/Flit) if moving away from setuptools.

- [ ] **GitHub Actions Workflows**
    - [ ] Create `.github/workflows/ci.yml` for Continuous Integration.
        - [ ] Job: Run `ruff` linting and formatting check (`ruff check .`, `ruff format --check .`).
        - [ ] Job: Run `mypy` static type checking (`mypy src`).
        - [ ] Job: Run `pytest` suite on Ubuntu-latest, Windows-latest, and macOS-latest.
    - [ ] Create `.github/workflows/release.yml` for automated releases.
        - [ ] Trigger on tag push (v*).
        - [ ] Build distribution (wheel/sdist).
        - [ ] Publish to PyPI (or TestPyPI initially).

- [ ] **Local Development Experience**
    - [ ] Configure `ruff.toml` or `pyproject.toml` with strict rules (select `["E", "F", "B", "I"]`).
    - [ ] Add `.pre-commit-config.yaml` to enforce linting before commit.
    - [ ] Add a `Makefile` or `Justfile` for common tasks (`make test`, `make lint`).

## 2. Code Quality & Standards

- [ ] **Static Type Checking**
    - [ ] Configure `mypy.ini` or strict settings in `pyproject.toml`.
    - [ ] Eliminate all `Any` types in key modules (`src/anki_tool/core/builder.py`, `src/anki_tool/core/connector.py`).
    - [ ] Add generic type support for Deck definitions and internal data structures.

- [ ] **Docstrings & Documentation**
    - [ ] Add Google-style docstrings to `AnkiConnector` API methods, explaining parameters and exceptions.
    - [ ] Document the `AnkiBuilder` class attributes and state management.
    - [ ] Ensure all public CLI commands have clear help strings.

- [ ] **Refactoring**
    - [ ] **Desacouple Parser**: Extract configuration loading logic from `cli.py` into a new `ConfigLoader` class in `src/anki_tool/core/config.py`.
    - [ ] **Error Handling**: Replace generic `Exception` raises with custom exceptions (e.g., `AnkiConnectError`, `ConfigValidationError`, `MediaMissingError`).
    - [ ] **Path Handling**: Replace all `os.path` usage with `pathlib.Path`.

## 3. Testing Strategy

- [ ] **Unit Tests: Core Logic**
    - [ ] `builder.py`: Test `stable_id` generation consistency (does the same string always yield the same ID?).
    - [ ] `builder.py`: Test `add_note` logic, ensuring fields are mapped correctly from YAML to Anki model.
    - [ ] `builder.py`: Test handling of empty or missing fields in note data.
    - [ ] `connector.py`: Mock `requests.post` to simulate successful AnkiConnect responses.
    - [ ] `connector.py`: Test retry logic or failure handling when Anki is unreachable.

- [ ] **Integration Tests**
    - [ ] Test the full pipeline: YAML Input -> Builder -> `.apkg` file creation (verify file existence and non-zero size).
    - [ ] Test how the system behaves with invalid YAML configurations (should fail gracefully).

- [ ] **Fixture Management**
    - [ ] Create a set of "golden" YAML files for testing fields, tags, and media references.

## 4. Feature Implementation Plan

- [ ] **Media Support**
    - [ ] **Schema Update**: Allow a `media` field in the data YAML (list of filenames).
    - [ ] **Discovery**: Implement automatic media file discovery relative to the YAML data file or a configured media directory.
    - [ ] **Validation**: Add a check to verify all referenced media files exist before starting the build.
    - [ ] **Implementation**: Wire up `cli.py` to call `builder.add_media()` for found files.

- [ ] **Data Validation & integrity**
    - [ ] **Schema Validation**: Integrate `pydantic` or `jsonschema` to validate `configs/*.yaml` and `data/*.yaml`.
    - [ ] **Consistency Checks**: Warn user about duplicate Note IDs within the same build run.
    - [ ] **HTML Validation**: Basic checks for broken HTML tags in field content.
    - [ ] **CLI Command**: Add `anki-tool validate --data <m>` to run checks without building.

- [ ] **CLI Enhancements**
    - [ ] **Verbose Mode**: Add `-v/--verbose` flag to print detailed logs (using `logging` module).
    - [ ] **Init Command**: Add `anki-tool init` to scaffold a new project with example config and data files.
    - [ ] **Wildcard Support**: Support processing multiple data files at once (e.g., `--data data/*.yaml`).

- [ ] **Graphical User Interface (GUI) - Long Term**
    - [ ] Evaluate frameworks (PySide6, Tkinter, or a web-based local UI with Streamlit/NiceGUI).
    - [ ] Design a simple file picker for Config and Data files.
    - [ ] Add a progress bar for the deck building and pushing process.

## 5. Documentation

- [ ] **Developer Guide**: Add a `CONTRIBUTING.md` explanation how to set up the dev environment.
- [ ] **Architecture Diagram**: Add a Mermaid diagram to the README showing the flow of data.
- [ ] **Examples**: Create a dedicated `examples/` directory with advanced usage patterns (Cloze deletion, multiple references, etc.).
