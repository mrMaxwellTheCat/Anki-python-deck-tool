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
        - [x] Trigger on tag push (v*).
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
    - [x] Add VSCode tasks configuration (`.vscode/tasks.json`) for local workflows.

## 2. Code Quality & Standards

- [x] **Static Type Checking**
    - [x] Configure `mypy` settings in `pyproject.toml`.
    - [x] Add type hints to all public functions.
    - [ ] Eliminate all `Any` types in core modules.
    - [ ] Add generic type support for Deck definitions.

- [x] **Docstrings & Documentation**
    - [x] Add Google-style docstrings to all public APIs.
    - [x] Document exception handling in functions.
    - [x] Add clear help strings to CLI commands.

- [x] **Refactoring**
    - [x] **Error Handling**: Custom exceptions (`AnkiConnectError`, `ConfigValidationError`, etc.).
    - [ ] **Decouple Parser**: Extract configuration loading into `src/anki_tool/core/config.py`.
    - [ ] **Media Handler**: Create dedicated `src/anki_tool/core/media.py` for media file operations.
    - [ ] **Validator Module**: Create `src/anki_tool/core/validators.py` for schema validation.

## 3. Testing Strategy

- [x] **Unit Tests: Core Logic**
    - [x] `builder.py`: Test `stable_id` generation consistency.
    - [x] `builder.py`: Test `add_note` logic, field mapping, and tag handling.
    - [x] `builder.py`: Test handling of empty or missing fields.
    - [x] `connector.py`: Mock `requests.post` to simulate AnkiConnect responses.
    - [x] `exceptions.py`: Test all custom exception types.
    - [x] `cli.py`: Comprehensive CLI command tests.
    - [ ] Add tests for config loading and validation.
    - [ ] Add tests for media file handling.

- [ ] **Integration Tests**
    - [ ] Test the full pipeline: YAML Input → Builder → `.apkg` file creation.
    - [ ] Test multiple note types in one deck.
    - [ ] Test handling of invalid YAML configurations (graceful failure).
    - [ ] Test media file inclusion in generated packages.

- [x] **Fixture Management**
    - [x] Create example YAML files for testing various scenarios (in `examples/` directory).
    - [x] Add fixtures for different note types (basic, language-learning, technical).
    - [ ] Add test media files (images, audio).

- [x] **Coverage Goals**
    - [x] Achieve >90% code coverage (currently at 96.77%).
    - [x] Set up coverage reporting in CI (Codecov integration).

## 4. Feature Implementation Plan

### 4.1 Multiple Note Types Support

- [ ] **Architecture Changes**
    - [ ] Design multi-model support: allow multiple configs in a single build.
    - [ ] Update CLI to accept multiple `--config` arguments or a single config with multiple models.
    - [ ] Update data format to specify which model each note uses.

- [ ] **Implementation**
    - [ ] Extend `AnkiBuilder` to manage multiple models simultaneously.
    - [ ] Add model selection logic when processing notes.
    - [ ] Update documentation with multi-model examples.

### 4.2 Media Support

- [ ] **Schema Update**
    - [ ] Allow a `media` field in data YAML (list of filenames or paths).
    - [ ] Support media references in field content (e.g., `<img src="image.jpg">`).

- [ ] **Discovery & Validation**
    - [ ] Implement automatic media file discovery from configured directories.
    - [ ] Support relative paths from YAML file location or absolute paths.
    - [ ] Add validation to verify all referenced media files exist.
    - [ ] Provide clear error messages for missing media.

- [ ] **Implementation**
    - [ ] Create `MediaHandler` class in `src/anki_tool/core/media.py`.
    - [ ] Wire up CLI to call `builder.add_media()` for discovered files.
    - [ ] Add `--media-dir` option to specify media directory.

### 4.3 Data Validation & Integrity

- [ ] **Schema Validation**
    - [ ] Integrate `pydantic` for type-safe config and data models.
    - [ ] Define schemas for config files (ModelConfig) and data files (NoteData).
    - [ ] Provide detailed validation error messages.

- [ ] **Consistency Checks**
    - [ ] Warn about duplicate note IDs within the same build.
    - [ ] Validate field names match between config and data.
    - [ ] Check for empty required fields.

- [ ] **HTML Validation**
    - [ ] Basic checks for unclosed HTML tags in field content.
    - [ ] Warn about common formatting issues.

- [ ] **CLI Command**
    - [ ] Add `anki-yaml-tool validate` command to run checks without building.
    - [ ] Support `--strict` mode for failing on warnings.

### 4.4 CLI Enhancements

- [ ] **Verbose Mode**
    - [ ] Add `-v/--verbose` flag for detailed logging.
    - [ ] Integrate Python `logging` module with configurable levels.
    - [ ] Log deck building progress, file operations, and API calls.

- [ ] **Init Command**
    - [ ] Add `anki-yaml-tool init [project-name]` to scaffold new projects.
    - [ ] Generate example config, data files, and directory structure.
    - [ ] Support different templates (basic, language-learning, technical).

- [ ] **Batch Processing**
    - [ ] Support wildcard patterns for processing multiple files (e.g., `--data data/*.yaml`).
    - [ ] Add `--merge` flag to combine multiple data files into one deck.
    - [ ] Progress indicators for batch operations.

- [ ] **Configuration Files**
    - [ ] Support `.anki-yaml-tool.yaml` config file in project root.
    - [ ] Allow setting default values for common options.
    - [ ] Support profile-based configurations (dev, prod).

- [ ] **Directory-Based Batch Processing**
    - [ ] **Architecture Design**
        - [ ] Define directory structure conventions
        - [ ] Design deck identification strategy (see options below)
        - [ ] Specify file naming conventions for data vs config files
        - [ ] Define sub-deck creation from nested directories
        - [ ] Handle file discovery and filtering (ignore non-YAML files)
    - [ ] **Directory Organization Strategies (To Be Decided)**
        - **Option A: One directory per deck**
            - Each subdirectory contains `data.yaml` and `config.yaml`
            - Directory name maps to deck name
            - Nested directories create sub-decks in Anki hierarchy
        - **Option B: Filename-based identification**
            - Files named like `spanish_data.yaml` + `spanish_config.yaml`
            - All files can coexist in same directory
            - Pair files by matching prefixes
        - **Option C: Content-based metadata**
            - YAML files contain `deck_name` and `type` metadata fields
            - Most flexible but requires schema changes
            - Allows multiple decks in single directory without naming conventions
    - [ ] **Implementation**
        - [ ] Add `--input-dir` option to `build` command
        - [ ] Implement recursive directory scanning
        - [ ] Create file pairing logic (data + config)
        - [ ] Add progress tracking for multi-deck builds
        - [ ] Support filtering by deck name pattern
        - [ ] Handle errors gracefully (skip invalid pairs, report at end)
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

- [ ] **Architecture & Design**
    - [ ] Design YAML serialization format for pulled decks
    - [ ] Define mapping from Anki model structure to config YAML
    - [ ] Specify field mapping and template extraction
    - [ ] Handle media file export and organization
    - [ ] Design conflict resolution strategy for round-trip edits

- [ ] **AnkiConnect Integration**
    - [ ] Implement `get_deck_names()` method (uses `deckNames` action)
    - [ ] Implement `get_model_names()` method (uses `modelNames` action)
    - [ ] Implement `export_deck()` method (uses `exportPackage` or manual extraction)
    - [ ] Implement `get_notes()` method for deck content extraction
    - [ ] Implement `get_model()` method for note type definitions
    - [ ] Add comprehensive error handling for read operations

- [ ] **YAML Export Format**
    - [ ] Design data file structure (match current format)
    - [ ] Design config file structure (fields, templates, CSS)
    - [ ] Handle special characters and escaping
    - [ ] Preserve note IDs for update tracking
    - [ ] Export media file references

- [ ] **CLI Commands**
    - [ ] `anki-yaml-tool pull --deck "Spanish Vocabulary" --output ./decks/spanish`
    - [ ] `anki-yaml-tool pull --all-decks --output ./decks`
    - [ ] `anki-yaml-tool pull --list-decks` (shows available decks)
    - [ ] `anki-yaml-tool pull --model "Basic" --output ./configs`

- [ ] **Round-Trip Workflow**
    - [ ] Pull deck from Anki → Edit YAML files → Build → Push back
    - [ ] Preserve note IDs to update existing notes instead of duplicating
    - [ ] Handle deleted notes (mark as deleted in YAML or skip)
    - [ ] Support incremental updates (only push changed notes)

- [ ] **Implementation Considerations**
    - **Feasibility**: HIGH (AnkiConnect supports required read operations)
    - **Existing Infrastructure**: Generic `invoke()` method available in `AnkiConnector`
    - **Testing**: Follow existing patterns in `test_connector.py`

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
    - [ ] Create `FileWatcher` class in `src/anki_tool/core/watcher.py`
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
    - [ ] Semantic versioning strategy
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
    - [ ] Add architecture documentation.
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
      - [ ] Medical terminology
      - [ ] Historical dates and events
      - [ ] Cloze deletion examples
      - [ ] Image occlusion examples
      - [ ] Audio pronunciation cards

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
- ✅ Development tooling (VSCode tasks, Makefile, pre-commit hooks)
- ✅ Basic examples directory (basic, language-learning, technical)
- ✅ Codecov integration

### Phase 2: Core Enhancements (In Progress)
**Next priorities:**
- Multiple note type support (allow multiple configs in one build)
- Media file handling (integrate existing `add_media()` functionality)
- Schema validation (integrate pydantic for type-safe configs)
- Enhanced CLI features (verbose mode, init command, batch processing)
- Additional examples (medical terminology, cloze deletion, audio cards)

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

*This roadmap is a living document and will be updated as the project evolves.*
