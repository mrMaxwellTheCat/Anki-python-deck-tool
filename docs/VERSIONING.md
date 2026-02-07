# Semantic Versioning Strategy

This document outlines the versioning strategy for the Anki Python Deck Tool, following [Semantic Versioning 2.0.0](https://semver.org/).

## Overview

We use Semantic Versioning (SemVer) with the format `MAJOR.MINOR.PATCH`:

- **MAJOR**: Incompatible API changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

## Current Version

**Version**: `0.1.0`
**Status**: Initial public release

## Version Format

```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
```

### Examples

- `1.0.0` - Major release
- `1.1.0` - Minor feature addition
- `1.1.1` - Patch/bug fix
- `2.0.0-beta.1` - Pre-release version
- `1.0.0+20250206` - Build metadata

## Versioning Rules

### MAJOR Version (X.0.0)

Increment when making **incompatible changes**:

#### API Breaking Changes
- Removing CLI commands or options
- Changing CLI option names or behavior
- Removing or renaming public API functions
- Changing function signatures in breaking ways
- Removing support for Python versions

#### Data Format Changes
- Incompatible YAML schema changes
- Changes requiring migration of existing files
- Removal of required fields

#### Examples
```
0.x.x → 1.0.0  # First stable release
1.x.x → 2.0.0  # Removed --old-format option
2.x.x → 3.0.0  # Changed YAML schema (requires migration)
```

### MINOR Version (x.Y.0)

Increment when adding **new features** (backward compatible):

#### New Functionality
- New CLI commands (`validate`, `init`, `watch`, etc.)
- New CLI options that don't break existing usage
- New configuration fields (with defaults)
- Support for new media types
- New validation rules (non-breaking)

#### Enhancements
- Performance improvements
- New examples added
- Enhanced error messages
- Better documentation

#### Examples
```
0.1.0 → 0.2.0  # Added validate command
0.2.0 → 0.3.0  # Added multiple model support
0.3.0 → 0.4.0  # Added watch mode
```

### PATCH Version (x.x.Z)

Increment for **bug fixes** (backward compatible):

#### Bug Fixes
- Fixing incorrect behavior
- Correcting error messages
- Fixing crashes or exceptions
- Resolving edge cases

#### Minor Updates
- Documentation fixes
- Dependency updates (non-breaking)
- Test improvements
- Code refactoring (no API changes)

#### Examples
```
0.1.0 → 0.1.1  # Fixed Windows path handling
0.1.1 → 0.1.2  # Fixed media validation error
0.1.2 → 0.1.3  # Updated dependencies
```

## Pre-release Versions

Use for testing before stable release:

### Pre-release Identifiers

- **alpha** (`0.2.0-alpha.1`): Early testing, unstable
- **beta** (`0.2.0-beta.1`): Feature complete, testing
- **rc** (`1.0.0-rc.1`): Release candidate, nearly stable

### Pre-release Rules

```
0.2.0-alpha.1   # First alpha
0.2.0-alpha.2   # Second alpha
0.2.0-beta.1    # First beta
0.2.0-beta.2    # Second beta
0.2.0-rc.1      # Release candidate
0.2.0           # Stable release
```

## Version Lifecycle

### Phase 0: Initial Development (0.x.x)

**Current Phase**: Building toward 1.0.0

Rules:
- Major version 0 indicates "in development"
- Minor version changes MAY include breaking changes
- No backward compatibility guarantees
- Public API not yet stable

Rationale:
- Allows rapid iteration
- Flexibility to refine API
- User expectations set appropriately

### Phase 1: Stable Release (1.0.0+)

**Target**: When core features are complete and API is stable

Criteria for 1.0.0:
- [x] Core CLI commands (build, push, validate)
- [x] Multiple note type support
- [x] Media file handling
- [x] Comprehensive test suite (>90% coverage)
- [x] Complete documentation
- [ ] At least 3 months in production use
- [ ] No major known bugs
- [ ] Stable public API

### Phase 2: Mature Product (2.0.0+)

**Future**: Major feature additions or rewrites

Potential triggers:
- GUI application (major new feature)
- Plugin system (architectural change)
- Database integration (new paradigm)
- Breaking CLI redesign

## Versioning Workflow

### 1. Development

**Branch**: `main`
**Version**: Always `X.Y.Z-dev` in development

```bash
# pyproject.toml during development
version = "0.2.0-dev"
```

### 2. Preparing Release

**Create release branch**: `release/vX.Y.Z`

Steps:
1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Run full test suite
4. Build and test package
5. Tag commit: `git tag -a vX.Y.Z -m "Release X.Y.Z"`

### 3. Release

**Trigger**: Push tag to GitHub

```bash
git tag v0.2.0
git push origin v0.2.0
```

**Automated Actions**:
- GitHub Actions builds package
- Runs all tests across platforms
- Publishes to PyPI
- Creates GitHub Release
- Builds executables

### 4. Post-Release

**Branch**: Back to `main`
**Version**: Bump to next development version

```bash
# If released 0.2.0, bump to:
version = "0.3.0-dev"  # or 0.2.1-dev for hotfix
```

## Version Numbering Guidelines

### Deciding Version Increment

Ask these questions:

1. **Does it break existing functionality?**
   - Yes → MAJOR version
   - No → Continue

2. **Does it add new features?**
   - Yes → MINOR version
   - No → Continue

3. **Does it fix bugs or improve existing code?**
   - Yes → PATCH version

### Examples

#### Scenario 1: Add new command
```python
# Add 'anki-yaml-tool watch' command
# Answer: New feature → MINOR version
0.1.0 → 0.2.0
```

#### Scenario 2: Fix validation bug
```python
# Fix: Validation incorrectly rejects valid HTML
# Answer: Bug fix → PATCH version
0.1.0 → 0.1.1
```

#### Scenario 3: Change CLI syntax
```python
# Change: --config to --model (breaking change)
# Answer: Breaking change → MAJOR version
0.9.0 → 1.0.0
```

#### Scenario 4: Add optional field
```python
# Add optional 'pronunciation' field to YAML (with default)
# Answer: New feature, backward compatible → MINOR version
0.2.0 → 0.3.0
```

## CHANGELOG Management

### Format

Follow [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

## [Unreleased]
### Added
- New feature descriptions

### Changed
- Changes to existing features

### Fixed
- Bug fixes

## [0.2.0] - 2025-02-15
### Added
- Multiple model configuration support
- Validation command with strict mode

### Fixed
- Windows path handling issue
```

### Update Process

1. **During Development**: Add changes to `[Unreleased]` section
2. **At Release**: Move `[Unreleased]` to versioned section
3. **Add Release Date**: Include YYYY-MM-DD date
4. **Create New Unreleased**: For next development cycle

## Backward Compatibility

### Compatibility Promise

**For versions 1.0.0+**:
- MINOR and PATCH versions maintain backward compatibility
- Existing YAML files continue to work
- Existing CLI commands continue to work
- Existing Python API continues to work

### Deprecation Policy

**For versions 1.0.0+**:

1. **Announce Deprecation**: Mark feature as deprecated in MINOR version
2. **Grace Period**: Maintain for at least one MINOR version
3. **Remove**: Remove in next MAJOR version

Example:
```
v1.2.0 - Deprecate --old-option (still works, warning shown)
v1.3.0 - Still supported (final version with support)
v2.0.0 - Remove --old-option (breaking change)
```

### Deprecation Warnings

```python
# Example deprecation warning
warnings.warn(
    "The --old-option flag is deprecated and will be removed in v2.0.0. "
    "Use --new-option instead.",
    DeprecationWarning,
    stacklevel=2
)
```

## Version Metadata

### In Code

```python
# src/anki_yaml_tool/__init__.py
__version__ = "0.1.0"
```

### In pyproject.toml

```toml
[project]
name = "anki-yaml-tool"
version = "0.1.0"
```

### In CLI

```bash
$ anki-yaml-tool --version
anki-yaml-tool 0.1.0
```

## Release Checklist

Before each release:

- [ ] All tests pass (`just test`)
- [ ] Coverage meets threshold (>90%)
- [ ] Linting passes (`just lint`)
- [ ] Type checking passes (`just type-check`)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in `pyproject.toml`
- [ ] Tag created: `vX.Y.Z`
- [ ] GitHub Release created
- [ ] PyPI package published
- [ ] Executables built and attached to release

## Version History

### Current Version: 0.1.0

#### Phase 0 Roadmap (Development)

- `0.1.0` - Initial release (✅ Complete)
  - Basic build and push commands
  - YAML-based deck building
  - AnkiConnect integration

- `0.2.0` - Validation & Multiple Models (✅ Complete)
  - Multiple note type support
  - Validate command
  - Media support
  - Enhanced validation

- `0.3.0` - CLI Enhancements (Planned)
  - Verbose mode
  - Init command
  - Batch processing

- `0.4.0` - Advanced Features (Planned)
  - Watch mode
  - Bidirectional sync

- `0.5.0` - GUI (Planned)
  - Desktop application
  - Visual deck editor

### Target Version: 1.0.0

#### Criteria

- Core features complete
- API stable
- 3+ months in production
- >90% test coverage
- Complete documentation
- Active community

#### Estimated Timeline

**Target**: Q3 2025

## Communication

### Where to Communicate Versions

1. **CHANGELOG.md** - Detailed change log
2. **GitHub Releases** - Release notes
3. **Documentation** - Version-specific docs
4. **PyPI** - Package metadata
5. **README.md** - Badges and current version

### Version Badges

```markdown
![Version](https://img.shields.io/pypi/v/anki-yaml-tool)
![Python](https://img.shields.io/pypi/pyversions/anki-yaml-tool)
```

## Questions and Answers

### Q: When should I bump to 1.0.0?

**A**: When the API is stable, core features are complete, and you're ready to commit to backward compatibility.

### Q: Can I skip versions?

**A**: Yes, you can skip PATCH or MINOR versions, but always document why.

### Q: What about 0.x.x versions?

**A**: During 0.x.x, anything may change. Use for development until API stabilizes.

### Q: How do I handle security fixes?

**A**: Release as PATCH version immediately, backport to supported MAJOR versions if needed.

---

## References

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [PEP 440 – Version Identification](https://peps.python.org/pep-0440/)
