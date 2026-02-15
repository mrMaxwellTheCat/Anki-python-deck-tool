# Project Design & Specifications

**Status:** Refactoring Phase
**Last Updated:** 2026-02-15

---

## Project Vision

### Purpose
A standalone tool to manage Anki decks using local YAML files as the source of truth. It automates deck creation, updates, and synchronization.

### Roadmap
- **Current State:** A Python-based CLI tool (in refactoring).
- **Future State:** A standalone executable with a GUI for end-users.

### Target Audience
Users who want to manage Anki flashcards programmatically or via text files without manually using the Anki interface for every edit.

---

## System Architecture

### High-Level Flow
`YAML Files` -> `Parser/Validator` -> `Core Logic` -> `Anki Adapter` -> `genanki` -> `Anki Connect`

### Core Modules
1. **CLI Layer (`src/cli`):** Handles user input, commands, and output formatting.
2. **Core Logic (`src/core`):** Business logic, diffing algorithms (YAML vs. Anki state).
3. **Anki Adapter (`src/anki`):** Abstracted interface to communicate with Anki (currently via a specific Python module).
4. **Data Models (`src/models`):** Pydantic models or dataclasses defining Decks, Cards, and configuration.

### Key Dependencies
- **CLI Framework:** Click (explicit command structure & composability).
- **YAML Parser:** PyYAML
- **Anki Package Generation:** genanki.
- **Anki Communication:** AnkiConnect API via `requests`.

---

## CLI Design Guidelines

### Command Structure

The CLI is organized by resources followed by actions.

**Global Options:**
- `--verbose / -v`: Enable detailed logging.
- `--help`: Show help message.

#### Deck Management (`deck`)
Interacts directly with the local Anki collection.

- `create`: Creates a new deck from a YAML schema. Fails if the deck already exists to avoid accidental overwrites.
    - `--file / -f <path>` (Required): Source YAML file.
    - `--dry-run`: Validate YAML without creating deck.
- `update`: Updates an existing deck from a YAML schema. Fails if the deck does not exist.
    - `--file / -f <path>` (Required): Source YAML file.
    - `--prune`: Delete cards in Anki that are missing in YAML.
- `export`: Exports an existing Anki deck to a YAML file. Fails if the deck does not exist.
    - `--name / -n <string>` (Required): Name of the deck in Anki.
    - `--output / -o <path>` (Required): Destination YAML file.
- `watch`: Monitors a YAML file for changes and auto-updates. Fails if the deck does not exist at startup.
    - `--file / -f <path>` (Required): File to watch.

#### Package Management (`package`)
Handles standalone `.apkg` files without modifying the Anki collection directly.

- `build`: Creates an `.apkg` file from YAML.
    - `--file / -f <path>` (Required): Source YAML.
    - `--output / -o <path>`: Destination file (default: deck name).
- `install`: Imports an `.apkg` file into Anki.
    - `--file / -f <path>` (Required): Path to `.apkg`.

#### Miscellaneous
- `gui`: Launches the Graphical User Interface.

### Options & Flags
- **Naming:** Use kebab-case for long flags (e.g., `--deck-name`).
- **Short Flags:** Use single characters for common options (e.g., `-n` for name, `-f` for file).
- **Boolean Flags:** Should be toggleable (e.g., `--dry-run`, `--force`).
- **Inputs:** Prefer explicit flags over positional arguments for clarity.

### Output & Feedback
- **Success:** Minimal, confirmation messages (Green color).
- **Errors:** Clear, actionable error messages (Red color).
- **Verbose:** Use a `--verbose` flag for debugging info.

---

## YAML Schema Specifications

### Deck Structure
The YAML file must strictly follow this schema.

```yaml
deck-name: 'Example deck' # Name of the deck
config:
  fields: # Fields each note will have
    - field-1
    - field-2
    - field-3
  css: # CSS here; recommended | for multi-line
  templates: # Templates for the cards; each template will be a card type in anki
    - name: Card type 1 # Name of the card type
      qfmt: | # Question format
        {{field-1}}
      afmt: | # Answer format
        {{FrontSide}}
        <hr id=answer>
        <div class="destino">{{field-2}}</div>
  media-folder: "path/to/media/folder" # Optional; media files added to the deck
data:
  - field-1: 'field-1 value for note 1'
    field-2: 'field-2 value for note 1'
    field-3: 'field-3 value for note 1'
  - field-1: 'field-1 value for note 2'
    field-2: 'field-2 value for note 2'
    field-3: 'field-3 value for note 2'
```

### Validation Rules
1. `deck-name` is mandatory.
2. `data` list cannot be empty.
3. `fields` in `config` must be defined and non-empty.
4. `templates` in `config` must be defined and non-empty.
5. Media files referenced in fields must exist when `media-folder` is specified.

---

## Coding Standards & Conventions

### Python Guidelines
- **Style:** Follow PEP 8.
- **Type Hints:** **Mandatory** for all function signatures (arguments and return types). Use `typing` module or built-in types (Python 3.9+).
- **Docstrings:** **Mandatory** for all public modules, classes, and functions.
    - *Format:* Google Style or NumPy Style.
    - *Content:* Description, Args, Returns, Raises.

### Error Handling
- **Exceptions:** Use custom exception classes inheriting from `AnkiToolError`.
  - `ConfigValidationError`, `DataValidationError`, `DeckBuildError` for build issues.
  - `AnkiConnectError` for Anki communication failures.
- **Granularity:** Catch specific errors rather than bare `Exception`.
- **Fail Fast:** Validate inputs early (CLI arguments, YAML structure) before attempting logic.

### Anti-Patterns (Do NOT do this)
- ❌ **Hardcoding paths:** Always use `pathlib` and configurable paths.
- ❌ **God functions:** Functions should do one thing. If a function is >50 lines, split it.
- ❌ **Global state:** Avoid global variables; pass configuration via context or dependency injection.
- ❌ **Implicit actions:** Do not delete or overwrite data without explicit flags (`--force`) or confirmation.

---

## Development Tooling

### Package Manager: uv
**Decision:** Use `uv` for dependency management and environment handling.
**Rationale:**
*   **Performance:** Significantly faster dependency resolution than pip/poetry.
*   **Reproducibility:** Strict locking via `uv.lock` ensures consistent environments.
*   **Python Versioning:** Automatically manages Python versions.

### Workflow Commands
| Command | Purpose |
|---------|---------|
| `uv sync` | Install dependencies and create virtualenv. |
| `uv add <package>` | Add a dependency to `pyproject.toml`. |
| `uv run anki-yaml-tool [COMMAND]` | Run the CLI. |
| `uv run pytest` | Run the test suite. |
| `uv build` | Create distribution packages. |

---

## Architecture Decision Records (ADR)

### Logic Placement
**Decision:** Business logic must be decoupled from CLI code.
**Reason:** To facilitate the future migration to a GUI without rewriting core logic.
**Implication:** CLI functions should only parse arguments and call `deck_service` functions. The `deck_service.py` module is the central orchestrator for `build_deck()`, `validate_deck()`, and `push_apkg()`.

### Anki Communication
**Decision:** Use an Adapter pattern for Anki communication.
**Reason:** Anki integration might change (e.g., moving from a local library to AnkiConnect API).
**Implication:** Core logic uses the `AnkiAdapter` protocol; `AnkiConnector` is the concrete implementation using the AnkiConnect HTTP API.

---

## Testing Strategy

### Framework & Tools
- **Test Runner:** `pytest` with fixtures and parametrization.
- **Code Coverage:** `pytest-cov` (threshold: 80%).
- **Static Analysis:** `ruff` for linting and formatting, `mypy` for type checking.
- **Mocking:** `unittest.mock` for isolating HTTP calls, file I/O, and Anki interactions.

### Test Architecture
1. **Unit Tests:**
   - Isolated tests for core logic in `core/` (validators, config, builder, etc.).
   - YAML parser tests (includes, Jinja, env vars, anchors, conditionals).
   - Pusher tests (add/update/delete/incremental/replace modes).
2. **Integration Tests:**
   - CLI command validation using `click.testing.CliRunner`.
   - Connector tests mocking `requests.Session` instead of live Anki.
3. **Regression Tests:**
   - End-to-end flows from YAML input to generated `.apkg`.
   - Comparison of expected output for known valid/invalid YAML schemas.

### Guidelines
- **Threshold:** Maintain a minimum of 80% code coverage (excluding non-refactored code).
- **Automation:** Run `uv run pytest` before pushing. CI via GitHub Actions.
- **Fixtures:** Test data in `tests/fixtures/` (YAML samples, sample media).
- **Connector mocking:** Always mock `connector._session` (not `requests.post`) since the connector uses a `requests.Session`.

---

## Refactoring Checklist

- [x] Isolate CLI specific code: `build`, `validate`, `push`, `watch`, `batch_build` commands now delegate to `core/deck_service.py`.
- [x] Define Pydantic models for YAML data (`core/models.py`).
- [x] Implement the Anki Adapter interface (`core/adapter.py` + `core/connector.py`).
- [x] Add Type Hints to all legacy functions.
- [x] Write unit tests for the YAML parser.
- [x] Fix pre-existing test failures (connector mocking, Jinja template quoting).
- [x] Achieve 80% code coverage.
