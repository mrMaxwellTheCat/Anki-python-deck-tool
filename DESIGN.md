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
- **CLI Framework:** Click (Chosen for explicit command structure).
- **YAML Parser:** PyYAML (Chosen for reliable parsing).
- **Anki Interaction:** genanki (Chosen for generating Anki packages).

---

## CLI Design Guidelines

### Command Structure

The CLI is organized by resources (`deck`, `package`) followed by actions.

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
  media-folder: "path/to/media/folder" # Optional; if specified, media files in this folder will be added to the anki deck
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

---

## Coding Standards & Conventions

### Python Guidelines
- **Style:** Follow PEP 8.
- **Type Hints:** **Mandatory** for all function signatures (arguments and return types). Use `typing` module or built-in types (Python 3.9+).
- **Docstrings:** **Mandatory** for all public modules, classes, and functions.
    - *Format:* Google Style or NumPy Style.
    - *Content:* Description, Args, Returns, Raises.

### Error Handling
- **Exceptions:** Use custom exception classes inheriting from a base `ProjectError`.
- **Granularity:** Catch specific errors (e.g., `FileNotFoundError`, `AnkiConnectionError`) rather than bare `Exception`.
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
*   **Python Versioning:** Automatically manages Python versions, ensuring the project runs on the specified version (e.g., 3.12) regardless of the host's system Python.

### Workflow Commands
*   **Setup:** `uv sync` (Installs dependencies and creates virtualenv).
*   **Add Dependency:** `uv add <package>` (Adds to `pyproject.toml` and updates lockfile).
*   **Run CLI:** `uv run anki-tool deck create ...` (Executes inside the virtualenv).
*   **Build:** `uv build` (Creates distribution packages).

## Architecture Decision Records (ADR) - Snapshot

### Logic Placement
**Decision:** Business logic must be decoupled from CLI code.
**Reason:** To facilitate the future migration to a GUI without rewriting core logic.
**Implication:** CLI functions should only parse arguments and call Core functions.

### Anki Communication
**Decision:** Use an Adapter pattern for Anki communication.
**Reason:** Anki integration might change (e.g., moving from a local library to AnkiConnect API).
**Implication:** Core logic should not import Anki libraries directly; it should use an interface.

---

## Testing Strategy

### Framework & Tools
- **Test Runner:** `pytest` for its powerful fixture system and extensive plugin ecosystem.
- **Code Coverage:** `pytest-cov` to track and maintain code quality.
- **Static Analysis:** `ruff` for linting and formatting, `mypy` for static type checking.

### Test Architecture
1. **Unit Tests:**
   - Isolated tests for core logic in `src/core`.
   - Validation of Pydantic models in `src/models`.
   - Parser logic for YAML files.
2. **Integration Tests:**
   - CLI command validation using `click.testing.CliRunner`.
   - Interaction between the Core logic and the Anki Adapter (using mocks/fakes for Anki Connect).
3. **Regression Tests:**
   - End-to-end flows from YAML input to generated `.apkg` or Anki Connect calls.
   - Comparison of expected output for known valid/invalid YAML schemas.

### Guidelines
- **Threshold:** Maintain a minimum of 80% code coverage.
- **Automation:**
  - Run `just test` (if using justfile) or `uv run pytest` before pushing.
  - Integration with GitHub Actions for every PR.
- **Fixtures:** Keep test data in `tests/fixtures` (YAML samples, sample media).

---

## Refactoring Checklist

- [ ] Isolate CLI specific code into `src/cli`.
- [ ] Define Pydantic models for YAML data.
- [ ] Implement the Anki Adapter interface.
- [ ] Add Type Hints to all legacy functions.
- [ ] Write unit tests for the YAML parser.
