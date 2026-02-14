# Project Roadmap

This document outlines the detailed development plan for the Anki Python Deck Tool. Our vision is to create a flexible, general-purpose tool for creating Anki decks from various sources, with support for multiple note types, media files, and both CLI and GUI interfaces.

## Vision Statement

Transform the Anki Python Deck Tool into a comprehensive, user-friendly solution for creating and managing Anki decks from structured data sources (primarily YAML), supporting diverse use cases from language learning to technical memorization, with both command-line and graphical interfaces.

## Core Principles

1. **Flexibility**: Support multiple note types, templates, and data formats
2. **Ease of Use**: Simple for beginners, powerful for advanced users
3. **Quality**: Well-tested, type-safe, and properly documented code
4. **Extensibility**: Plugin architecture for custom processors and validators
5. **Cross-Platform**: Works seamlessly on Windows, macOS, and Linux

## 1. Infrastructure (CI/CD, Packaging)

- [x] **Packaging Upgrade**
  - [x] Create `requirements.txt` for consistent environment setup.
  - [x] Update `pyproject.toml` with modern build system configuration.
  - [x] Set up optional extras for dev dependencies.
  - [ ] Evaluate `poetry` or `uv` for advanced dependency management (current setup is sufficient).

- [x] **GitHub Actions Workflows**
  - [x] Create `.github/workflows/ci.yml` for Continuous Integration.
    - [x] Job: Run `ruff` linting and formatting check.
    - [x] Job: Run `mypy` static type checking.
    - [x] Job: Run `pytest` suite on Ubuntu-latest, Windows-latest, and macOS-latest.
    - [x] Job: Upload coverage to Codecov.
  - [x] Create `.github/workflows/release.yml` for automated releases.
    - [x] Trigger on tag push (v\*).
    - [x] Build distribution (wheel/sdist).
    - [x] Publish to PyPI.
  - [x] Create `.github/workflows/security.yml` for security scanning.
    - [x] Job: Run `bandit` for security linting.
    - [x] Job: Run `pip-audit` for dependency vulnerability scanning.
  - [x] Create `.github/workflows/build_release.yml` for executable building.
    - [x] Build standalone executables for Windows, macOS, and Linux.
  - [x] Set up Dependabot for automated dependency updates.

- [x] **Local Development Experience**
  - [x] Configure `ruff` and `mypy` in `pyproject.toml` with strict rules.
  - [x] Add `.pre-commit-config.yaml` to enforce linting before commit.
  - [x] Add `Makefile` for common tasks (`make test`, `make lint`, `make build-exe`, etc.).

## 2. Code Quality & Standards

- [x] **Static Type Checking**
  - [x] Configure `mypy` settings in `pyproject.toml`.
  - [x] Add type hints to all public functions.
  - [x] Eliminate all `Any` types in core modules.
  - [x] Add generic type support for Deck definitions.

- [x] **Docstrings & Documentation**
  - [x] Add Google-style docstrings to all public APIs.
  - [x] Document exception handling in functions.
  - [x] Add clear help strings to CLI commands.

- [x] **Refactoring**
  - [x] **Error Handling**: Custom exceptions (`AnkiConnectError`, `ConfigValidationError`, etc.).
  - [x] **Decouple Parser**: Extract configuration loading into `src/anki_yaml_tool/core/config.py`.
  - [x] **Media Handler**: Create dedicated `src/anki_yaml_tool/core/media.py` for media file operations.
  - [x] **Validator Module**: Create `src/anki_yaml_tool/core/validators.py` for schema validation.

## 3. Testing Strategy

- [x] **Unit Tests: Core Logic**
  - [x] `builder.py`: Test `stable_id` generation consistency.
  - [x] `builder.py`: Test `add_note` logic, field mapping, and tag handling.
  - [x] `builder.py`: Test handling of empty or missing fields.
  - [x] `connector.py`: Mock `requests.post` to simulate AnkiConnect responses.
  - [x] `exceptions.py`: Test all custom exception types.
  - [x] `cli.py`: Comprehensive CLI command tests.
  - [x] Add tests for config loading and validation.
  - [x] Add tests for media file handling.
  - [x] Add tests for interactive terminal UI (`tests/test_interactive.py`) ✅

- [x] **Integration Tests**
  - [x] Test the full pipeline: YAML Input → Builder → `.apkg` file creation.
  - [x] Test multiple note types in one deck.
  - [x] Test handling of invalid YAML configurations (graceful failure).
  - [x] Test media file inclusion in generated packages.

  **Implementation:** Tests added in `tests/test_integration.py` covering:
  - Full pipeline tests with real YAML parsing and `.apkg` file generation
  - Multiple note type handling in single deck builds
  - Invalid YAML error handling with proper exception catching
  - Media file inclusion verification in package generation

- [x] **Fixture Management**
  - [x] Create example YAML files for testing various scenarios (in `examples/` directory).
  - [x] Add fixtures for different note types (basic, language-learning, technical).
  - [x] Add test media files (images, audio).

- [x] **Coverage Goals**
  - [x] Achieve >90% code coverage (currently at 97.49%).
  - [x] Set up coverage reporting in CI (Codecov integration).

## 3.1 Bug Fixes & Critical Improvements

Priority fixes identified from code analysis. These issues cause functional failures or security concerns.

### Critical (Fix Immediately)

- [x] **Fix: Silent Media Errors** (`cli.py:910-911`, `cli.py:1013-1014`)
  - [x] Add proper logging for media file processing errors instead of silently ignoring them
  - [x] Provide clear error messages when media files fail to process
  - [x] Implemented: Added specific exception handling (KeyError, AnkiConnectError, generic Exception)
  - [x] Logging with WARNING level and user-facing messages via click.echo

- [x] **Fix: WSL Path Conversion Silent Fallback** (`connector.py:100-104`)
  - [x] Improve error handling for WSL path conversion
  - [x] Add warning when path conversion fails instead of silent fallback
  - [x] Implemented: Added logging WARNING when path conversion fails
  - Location: `src/anki_yaml_tool/core/connector.py`

- [x] **Fix: Pass media_folder to AnkiBuilder in build command** (`cli.py:152`)
  - Pass `media_folder` parameter to `AnkiBuilder` constructor in simple build command
  - Enable automatic media discovery for non-batch builds
  - Location: `src/anki_yaml_tool/cli.py`
  - **Status: Completed** - Fixed by converting CLI string path to Path object and passing it to AnkiBuilder

### High Priority

- [x] **Fix: Concurrency in Batch Build** (`cli.py:1046`)
  - [x] Increase `max_workers` in ThreadPoolExecutor to allow parallel push operations
  - [x] Current value of 1 eliminates concurrency benefits
  - [x] Implemented: max_workers increased to 4 (configurable 1-8)
  - Location: `src/anki_yaml_tool/cli.py`

- [x] **Fix: Robust Note Update Handling** (`pusher.py:77-145`)
  - [x] Handle `update_note_fields` failures gracefully when note doesn't exist
  - [x] Fallback to creating new note instead of aborting entire process
  - [x] Implemented: Added fallback from update to create operation
  - Location: `src/anki_yaml_tool/core/pusher.py`

- [x] **Fix: Path Traversal in Export** (`exporter.py:192-225`)
  - [x] Move validation BEFORE attempting to retrieve media files
  - [x] Improve validation logic for path traversal attacks
  - [x] Implemented: Validation moved before file retrieval
  - Location: `src/anki_yaml_tool/core/exporter.py`

### Medium Priority

- [x] **Improve: HTML Validation Regex** (`validators.py:195-196`)
  - [x] Fix regex to handle tags with `>` in attributes
  - [x] Handle self-closing tags properly (`<br/>`)
  - [x] Handle HTML5 void elements correctly
  - [x] Implemented: Regex improved with state machine approach
  - Location: `src/anki_yaml_tool/core/validators.py`

- [x] **Improve: LaTeX Math Delimiter Conversion** (`builder.py:136-139`)
  - [x] Handle escaped delimiters (`\#`, `\$`)
  - [x] Handle `$` in URLs or code properly
  - [x] Implemented: Handles escaped delimiters and URLs
  - Location: `src/anki_yaml_tool/core/builder.py`


- [x] **Improve: Configurable Timeouts** (`connector.py:56`)
  - [x] Add timeout configuration per operation type
  - [x] Allow longer timeouts for large imports and sync operations
  - [x] Implemented: timeout_short and timeout_long configurable
  - Location: `src/anki_yaml_tool/core/connector.py`

- [x] **Improve: Use requests.Session()** (`connector.py`)
  - [x] Implement persistent HTTP connections using Session
  - [x] Improve performance for multiple AnkiConnect operations
  - [x] Implemented: Session persistent connection implemented
  - Location: `src/anki_yaml_tool/core/connector.py`

### Lower Priority (Tech Debt)

- [ ] **Refactor: Extract Duplicate Push Logic** (`cli.py:813-1156`)
  - Extract duplicated push logic into shared function
  - Reduce ~100 lines of duplicated code
  - Location: `src/anki_yaml_tool/cli.py`

- [ ] **Refactor: Consistent Exception Handling**
  - Establish consistent exception handling patterns across modules
  - Reduce coupling between CLI and core modules

- [ ] **Refactor: Extract Constants**
  - Extract magic numbers (timeouts, extensions) to constants
  - Add centralized configuration
  - Locations: `connector.py`, `media.py`

- [ ] **Refactor: Fix Circular Import** (`interactive.py:99-108`)
  - Avoid importing CLI functions directly in interactive module
  - Use proper abstraction layer

- [ ] **Improve: Input Validation** (`config.py`)
  - Add warning when specified media folder doesn't exist
  - Validate tags against Anki special characters

## 4. Feature Implementation Plan

### 4.1 Multiple Note Types Support

- [x] **Architecture Changes**
  - [x] Design multi-model support: allow multiple configs in a single build.
  - [x] Update CLI to accept multiple `--config` arguments.
  - [x] Update data format to specify which model each note uses.

- [x] **Implementation**
  - [x] Extend `AnkiBuilder` to manage multiple models simultaneously.
  - [x] Add model selection logic when processing notes.
  - [x] Update documentation with multi-model examples.

### 4.2 Media Support

- [x] **Schema Update**
  - [x] Allow a `media` field in data YAML.
  - [x] Support media references in field content.

- [x] **Discovery & Validation**
  - [x] Implement automatic media file discovery.
  - [x] Support relative/absolute paths.
  - [x] Add validation for referenced media.
  - [x] Provide clear error messages for missing media.

- [x] **Implementation**
  - [x] Create `MediaHandler` in `media.py`.
  - [x] Wire up CLI to use `add_media()`.
  - [x] Add `--media-dir` option.

### 4.3 Data Validation & Integrity

- [x] **Schema Validation**
  - [x] Integrate `pydantic` for config and data models.
  - [x] Define schemas for config and data files.
  - [x] Provide detailed validation errors.

- [x] **Consistency Checks**
  - [x] Warn about duplicate note IDs.
  - [x] Validate field names match.
  - [x] Check for empty required fields.

- [x] **HTML Validation**
  - [x] Basic checks for unclosed HTML tags.
  - [x] Warn about common formatting issues.

- [x] **CLI Command**
  - [x] Add `anki-yaml-tool validate` command.
  - [x] Support `--strict` mode.

### 4.4 CLI Enhancements

- [x] **Verbose Mode**
  - [x] Add `-v/--verbose` flag for detailed logging.
  - [x] Integrate Python `logging` module with configurable levels.
  - [x] Log deck building progress, file operations, and API calls.

- [x] **Init Command**
  - [x] Add `anki-yaml-tool init [project-name]` to scaffold new projects.
  - [x] Generate example config, data files, and directory structure.
  - [x] Support different templates (basic, language-learning, technical).
  - [x] **Interactive terminal UI**: provide a guided menu when invoked without arguments (tests added)

- [x] **Batch Processing**
  - [x] Support wildcard patterns for processing multiple files (e.g., `--data data/*.yaml`).
  - [x] Add `--merge` flag to combine multiple data files into one deck.
  - [x] Progress indicators for batch operations.

- [x] **Configuration Files**
  - [x] Support `.anki-yaml-tool.yaml` config file in project root.
  - [x] Allow setting default values for common options.
  - [x] Support profile-based configurations (dev, prod).

- [x] **Directory-Based Batch Processing**
  - [x] Added `--input-dir` option to `batch-build` command
  - [x] Added `--recursive` flag for subdirectory scanning
  - [x] Added `--pattern` option for custom filename matching
  - [x] Added `--hierarchical` flag for directory-based deck naming
  - [x] Implemented `scan_directory_for_decks()` and `get_deck_name_from_path()` utilities
    - [x] Add progress tracking for multi-deck builds
    - [x] Support filtering by deck name pattern
    - [x] Handle errors gracefully (skip invalid pairs, report at end)

  **Implementation:** Progress tracking added via `tqdm` library, `--deck-filter` option implemented in CLI, error handling with summary reporting at end of batch operations.

  - [ ] **CLI Interface**
    - [ ] `anki-yaml-tool build --input-dir ./decks`
    - [ ] `anki-yaml-tool build --input-dir ./decks --deck-filter "spanish*"`
    - [ ] `anki-yaml-tool build --input-dir ./decks --output-dir ./builds`
    - [ ] Support `--push` flag for build + push in one command
  - [ ] **Integration with Existing Features**
    - [ ] Works with media file support (scan directories for media)
    - [ ] Compatible with validation command
    - [ ] Respects existing error handling and exceptions

### 4.5 Advanced YAML Features

- [ ] **YAML Includes**
  - [ ] Support `!include` directive to split large files.
  - [ ] Allow including config fragments and data fragments.

- [ ] **Variables & Templates**
  - [ ] Support YAML anchors and aliases for reusing content.
  - [ ] Add Jinja2-style templating for dynamic content.
  - [ ] Environment variable substitution in YAML.

- [ ] **Conditional Content**
  - [ ] Support conditional inclusion based on tags or custom flags.
  - [ ] Enable/disable notes or entire sections dynamically.

### 4.6 Bidirectional Sync (Pull from Anki)

Enable pulling existing decks and note types from Anki Desktop into YAML format for editing, then pushing changes back. This creates a full round-trip workflow for Anki deck management.

- [x] **Architecture & Design**
  - [x] Design YAML serialization format for pulled decks (initial format: `config.yaml`, `data.yaml`, `media/`)
  - [x] Define mapping from Anki model structure to config YAML
  - [x] Specify field mapping and template extraction
  - [x] Handle media file export and organization (media saved via `retrieveMediaFile`)
  - [ ] Design conflict resolution strategy for round-trip edits (planned)

- [x] **AnkiConnect Integration**
  - [x] Implement `get_deck_names()` method (uses `deckNames` action)
  - [x] Implement `get_model_names()` method (uses `modelNames` action)
  - [x] Implement `export_deck()` method (manual extraction using `findNotes` + `notesInfo`)
  - [x] Implement `get_notes()` method for deck content extraction
  - [x] Implement `get_model()` method for note type definitions
  - [x] Add comprehensive error handling for read operations

- [x] **YAML Export Format**
  - [x] Design data file structure (match current format)
  - [x] Design config file structure (fields, templates, CSS)
  - [x] Handle special characters and escaping (use readable YAML dumper; preserves Unicode and multiline strings)
  - [x] Preserve note IDs for update tracking
  - [x] Export media file references (saved under `media/`)

- [x] **CLI Commands**
  - [x] `anki-yaml-tool pull --deck "Spanish Vocabulary" --output ./decks/spanish`
  - [x] `anki-yaml-tool pull --all-decks --output ./decks`
  - [x] `anki-yaml-tool pull --list-decks` (shows available decks)
  - [ ] `anki-yaml-tool pull --model "Basic" --output ./configs` (pending: model-only export)

- [ ] **Round-Trip Workflow**
  - [ ] Pull deck from Anki → Edit YAML files → Build → Push back (push-by-id/update not yet implemented)
  - [x] Preserve note IDs to update existing notes instead of duplicating
  - [ ] Handle deleted notes (mark as deleted in YAML or skip)
  - [ ] Support incremental updates (only push changed notes)

- [ ] **Deck Synchronization (Replace Mode)**
  - [ ] Add `--sync/--replace` flag to push commands to enable sync mode
  - [ ] Implement logic to compare YAML note IDs with existing Anki deck notes
  - [ ] Delete notes in Anki that are not present in the new YAML file
  - [ ] Update existing notes that have matching IDs
  - [ ] Add new notes from YAML that don't exist in Anki
  - [ ] Provide summary of changes: added, updated, deleted notes
  - [ ] Add `--dry-run` flag to preview changes without applying them
  - [ ] Handle orphan notes (notes in Anki without ID match in YAML)

- **Implementation Approach:**
  - Use AnkiConnect's `deleteNotes` action to remove old cards
  - Use `updateNoteFields` for existing notes with matching IDs
  - Use `addNote` for new notes from YAML
  - Require note IDs in YAML for sync mode to work properly
  - Add validation warning if sync mode is attempted without IDs in YAML

- [x] **Implementation Considerations**
  - **Feasibility**: HIGH (AnkiConnect supports required read operations)
  - **Existing Infrastructure**: Generic `invoke()` method available in `AnkiConnector` (read wrappers implemented)
  - **Testing**: Unit tests added for connector/extractor/exporter/CLI (`tests/test_connector_pull.py`, `tests/test_exporter.py`, `tests/test_cli_pull.py`)

**Status note:** Initial pull/export implementation complete (connector read wrappers, `src/anki_yaml_tool/core/exporter.py`, `pull` CLI, tests). YAML output uses a human-readable dumper to preserve Unicode and multiline content. See `src/anki_yaml_tool/core/connector.py`, `src/anki_yaml_tool/core/exporter.py`, and `tests/` for details.

**Next steps (recommended):**
1. Implement push-by-id/update logic so edited YAML can be pushed back without duplicating notes (high priority for round-trip).
2. Add integration tests that simulate a pull → edit → build → push round-trip.
3. Implement `--model` export and richer model serialization (fields, templates, CSS examples).
4. Add conflict resolution strategy (e.g., keep remote ID, detect changed fields, provide an interactive merge tool).
5. Document the pull workflow and add examples to `examples/` and README.




### 4.7 File Watching Mode

Automatically rebuild and push decks when input files change, enabling real-time workflow during card creation.

- [ ] **Technology Selection**
  - [ ] Evaluate `watchdog` library for cross-platform file monitoring
  - [ ] Alternative: `watchfiles` (Rust-based, faster)
  - [ ] Ensure compatibility with Windows, macOS, and Linux

- [ ] **Architecture Design**
  - [ ] Define watch scope (single file, directory, recursive)
  - [ ] Design debouncing logic (handle rapid successive saves)
  - [ ] Specify rebuild trigger events (modify, create, delete)
  - [ ] Handle errors without crashing the watcher

- [ ] **Implementation**
  - [ ] Create `FileWatcher` class in `src/anki_yaml_tool/core/watcher.py`
  - [ ] Implement file change detection with debouncing (e.g., 500ms delay)
  - [ ] Integrate with existing build/push workflow
  - [ ] Add graceful shutdown on Ctrl+C
  - [ ] Implement smart rebuilding (only changed deck if directory input)

- [ ] **CLI Command**
  - [ ] `anki-yaml-tool watch --data data.yaml --config config.yaml --push`
  - [ ] `anki-yaml-tool watch --input-dir ./decks --push`
  - [ ] Support `--no-push` flag for build-only mode
  - [ ] Display file change events in real-time

- [ ] **User Experience**
  - [ ] Clear console output showing detected changes
  - [ ] Success/error notifications for each rebuild
  - [ ] Option to suppress verbose output
  - [ ] Visual indicator that watcher is active

- [ ] **Error Handling**
  - [ ] Continue watching after build errors (don't crash)
  - [ ] Display error messages without breaking watch loop
  - [ ] Retry on transient AnkiConnect errors
  - [ ] Graceful handling of file access errors (file locked, etc.)

- [ ] **Integration Considerations**
  - Works with single files or directory-based batch processing
  - Compatible with auto-push to Anki
  - Respects existing validation and error handling

## 5. Graphical User Interface (GUI)

### 5.1 Technology Selection

- [ ] **Evaluate Frameworks**
  - [ ] PySide6/PyQt6 (native desktop applications)
  - [ ] Tkinter (built-in, simple but limited)
  - [ ] Electron + Python backend (web technologies)
  - [ ] Streamlit/NiceGUI (web-based local UI)
  - [ ] Tauri + Python (modern, lightweight)

- [ ] **Decision Criteria**
  - Cross-platform support (Windows, macOS, Linux)
  - Ease of development and maintenance
  - Package size and distribution complexity
  - User experience quality

### 5.2 GUI Features (Phase 1)

- [ ] **Core Functionality**
  - [ ] File pickers for config and data files
  - [ ] Output path selector
  - [ ] Deck name input
  - [ ] Build button with progress bar
  - [ ] Success/error notifications

- [ ] **Advanced Features**
  - [ ] Visual YAML editor with syntax highlighting
  - [ ] Real-time validation feedback
  - [ ] Preview of generated cards
  - [ ] Recent projects list

### 5.3 GUI Modes & Workflows

Define the core interaction modes for the GUI application, providing both manual control and automated workflows.

- [ ] **Mode Architecture**
  - [ ] Design mode switching interface
  - [ ] Define shared state between modes
  - [ ] Implement mode persistence (remember last used mode)

- [ ] **Manual Mode**
  - [ ] File/directory picker for input(s) (data + config or directory)
  - [ ] Output location selector with options:
    - Custom path (save .apkg file to specific location)
    - Internal tmp directory (for auto-push + auto-cleanup)
  - [ ] Toggle for auto-push after build
  - [ ] Build button with progress bar
  - [ ] Push button (enabled after successful build)
  - [ ] Remember last used paths and settings
  - [ ] "Build Again" button (rebuilds with same inputs if files changed)

- [ ] **Watch Mode**
  - [ ] Input/output configuration panel (same as manual mode)
  - [ ] "Start Watching" / "Stop Watching" toggle button
  - [ ] Auto-push toggle (independent control)
  - [ ] Real-time file change indicators
  - [ ] Live status display:
    - "Watching for changes..."
    - "Building deck..."
    - "Pushing to Anki..."
    - "Build successful" / "Error: [message]"
  - [ ] Auto-scroll log of build events
  - [ ] Smart rebuilding (only changed deck if directory input)

- [ ] **Shared Features (Both Modes)**
  - [ ] Project management: Save/load input/output configurations
  - [ ] Recent projects dropdown
  - [ ] Deck name input field
  - [ ] Validation feedback (before build/watch starts)
  - [ ] Success/error notifications (system tray or GUI alerts)

- [ ] **Input Type Support**
  - [ ] Single deck: Select one data file + one config file
  - [ ] Directory: Select directory for batch processing
  - [ ] Both modes handle both input types seamlessly

- [ ] **User Experience Enhancements**
  - [ ] Keyboard shortcuts (Ctrl+B for build, Ctrl+W for watch)
  - [ ] Drag-and-drop support for file selection
  - [ ] Settings panel for defaults (AnkiConnect URL, timeouts)
  - [ ] Dark mode support

### 5.4 GUI Features (Phase 2)

- [ ] **Editor Integration**
  - [ ] Built-in config editor with templates
  - [ ] Visual card designer (WYSIWYG)
  - [ ] Media library browser
  - [ ] Tag management interface

- [ ] **Batch Operations**
  - [ ] Multi-file project management
  - [ ] Batch build and push
  - [ ] Import/export project settings

## 6. Distribution & Packaging

### 6.1 PyPI Package

- [x] **Basic Package**
  - [x] Published on PyPI as `anki-yaml-tool`
  - [x] Automated releases via GitHub Actions
  - [x] Semantic versioning strategy
  - [ ] Changelog automation

### 6.2 Standalone Executables

- [x] **Basic Executable Building**
  - [x] Build with PyInstaller (via `make build-exe` and `scripts/build.py`)
  - [x] Support for custom icons (assets/icon.ico for Windows, assets/icon.icns for macOS)
  - [x] Automated executable building via GitHub Actions workflow

- [ ] **Windows Distribution**
  - [x] Build standalone .exe with PyInstaller
  - [ ] Create installer with Inno Setup or NSIS
  - [ ] Code signing for trusted installation

- [ ] **macOS Distribution**
  - [x] Build standalone executable
  - [ ] Create .app bundle
  - [ ] DMG installer
  - [ ] Notarization for Gatekeeper

- [ ] **Linux Distribution**
  - [x] Build standalone executable
  - [ ] AppImage for universal compatibility
  - [ ] Snap package
  - [ ] Debian/Ubuntu .deb package
  - [ ] Fedora/RHEL .rpm package

### 6.3 Alternative Distribution

- [ ] **Docker Image**
  - [ ] Lightweight image for CLI usage
  - [ ] Include all dependencies
  - [ ] Easy integration with CI/CD

- [ ] **Web Service**
  - [ ] Host as a web service for team usage
  - [ ] Authentication and user management
  - [ ] Shared deck repositories

## 7. Plugin & Extension System

### 7.1 Architecture

- [ ] **Plugin Interface**
  - [ ] Define plugin API for custom processors
  - [ ] Hook points: pre-build, post-build, field transformation
  - [ ] Plugin discovery mechanism

- [ ] **Built-in Plugins**
  - [ ] Markdown to HTML converter
  - [ ] LaTeX/MathJax formatter
  - [ ] Image processing (resize, compress)
  - [ ] Audio processing (normalize, convert formats)

### 7.2 Extension Points

- [ ] **Custom Note Types**
  - [ ] Plugin system for specialized note types
  - [ ] Template library for common patterns

- [ ] **Data Sources**
  - [ ] CSV import plugin
  - [ ] JSON import plugin
  - [ ] Spreadsheet (Excel) import plugin
  - [ ] API/web scraping plugin framework

## 8. Documentation

- [x] **Developer Guide**
  - [x] Add `CONTRIBUTING.md` with dev environment setup.
  - [x] Add architecture documentation.
  - [ ] Document plugin development.

- [x] **User Documentation**
  - [x] Enhanced `README.md` with comprehensive usage guide.
  - [ ] Create user manual with screenshots.
  - [ ] Video tutorials for common workflows.

- [ ] **Architecture Diagram**
  - [ ] Add Mermaid diagram showing data flow.
  - [ ] Component interaction diagram.
  - [ ] Class hierarchy diagram.

- [x] **Examples**
  - [x] Create `examples/` directory with diverse use cases:
    - [x] Basic example (simple card model)
    - [x] Language learning (vocabulary, grammar)
    - [x] Technical memorization (programming, math)
    - [x] Medical terminology
    - [x] Historical dates and events
    - [x] Cloze deletion examples
    - [ ] Image occlusion examples
    - [x] Audio pronunciation cards

- [ ] **API Documentation**
  - [ ] Auto-generate from docstrings using Sphinx or MkDocs.
  - [ ] Host on Read the Docs or GitHub Pages.

## 9. Community & Ecosystem

### 9.1 Community Building

- [ ] **Communication Channels**
  - [ ] GitHub Discussions for Q&A and feature requests
  - [ ] Discord or Slack community
  - [ ] Twitter/social media presence

- [ ] **Documentation Site**
  - [ ] Dedicated website with tutorials
  - [ ] Blog for updates and tips
  - [ ] Gallery of example decks

### 9.2 Template & Deck Repository

- [ ] **Shared Repository**
  - [ ] GitHub repo for community templates
  - [ ] Pre-made note type configurations
  - [ ] Example datasets for learning

- [ ] **Template Manager**
  - [ ] CLI command to browse and install templates
  - [ ] Rating and review system
  - [ ] Version management

## Implementation Timeline

### Phase 1: Foundation (✅ Completed)

- ✅ Basic CLI functionality (`build` and `push` commands)
- ✅ YAML-based deck building with field mapping
- ✅ AnkiConnect integration for deck pushing
- ✅ Custom exception hierarchy for error handling
- ✅ Comprehensive test suite (96.77% coverage)
- ✅ CI/CD setup across Windows, macOS, and Linux
- ✅ Security scanning (bandit, pip-audit)
- ✅ Automated releases to PyPI
- ✅ Executable building capability (PyInstaller)
- ✅ Basic examples directory (basic, language-learning, technical)
- ✅ Codecov integration

### Phase 2: Core Enhancements (In Progress)

**Next priorities:**

- [x] Multiple note type support (allow multiple configs in one build)
- [x] Media file handling (integrate existing `add_media()` functionality)
- [x] Schema validation (integrate pydantic for type-safe configs)
- [x] Enhanced CLI features (validate command, multiple configs)
- [x] Additional examples (medical terminology, cloze deletion, historical dates, audio cards)

### Phase 3: Advanced Features (Planned)

- Directory-based batch processing (recursive deck building)
- Bidirectional sync (pull decks from Anki to YAML)
- File watching mode (auto-rebuild on file changes)
- GUI development (framework evaluation and implementation with manual + watch modes)
- Plugin system (custom processors and validators)
- Advanced YAML features (includes, templates, variables)
- Integration tests

### Phase 4: Distribution & Growth (Planned)

- Full distribution packages (installers for Windows/macOS/Linux)
- Community building (GitHub Discussions, documentation site)
- Template repository and manager
- API documentation site
- Advanced integrations

## Success Metrics

- **Adoption**: 1000+ PyPI downloads per month
- **Quality**: >90% test coverage, <5 open critical bugs
- **Community**: 100+ GitHub stars, active contributors
- **Documentation**: Complete API docs, 20+ examples
- **Stability**: Semantic versioning, stable public API

---

_This roadmap is a living document and will be updated as the project evolves._
