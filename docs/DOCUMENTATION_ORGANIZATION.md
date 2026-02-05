# Documentation Organization Summary

## Overview

Reorganized project documentation and significantly improved AI assistant instructions to establish clear guidelines for file organization and code standards.

## Actions Completed

### 1. Improved AI Assistant Instructions ✅

**File**: `.github/copilot-instructions.md`

**Changes**:
- **Expanded from 78 to 375 lines** (4.8x increase)
- **Renamed** from "GitHub Copilot Instructions" to "AI Assistant Instructions" (works for all AI tools)
- **Added comprehensive new sections**:
  - Testing requirements and practices (maintain 80%+ coverage)
  - Dependencies documentation (core and dev deps listed)
  - Common pitfalls with code examples (before/after comparisons)
  - **File organization rules** (summaries go in docs/, not root)
  - Security considerations (input validation, dependency scanning)
  - Performance guidelines (benchmarks, optimization rules)
  - Git workflow (commit messages, PR process)
  - Quick reference table
- **Improved existing sections**:
  - Type hinting examples (Python 3.10+ style)
  - Error handling with custom exceptions
  - VSCode task integration
  - Project architecture details

**Key New Rule**:
> **IMPORTANT**: Do NOT create summary, setup, or implementation files in the root directory.
>
> **✅ Correct**: `docs/IMPLEMENTATION_SUMMARY.md`
> **❌ Wrong**: `IMPLEMENTATION_SUMMARY.md`

### 2. Created Claude Instructions ✅

**File**: `.claude-instructions.md` (new)

**Purpose**:
- Provides Claude-specific quick reference
- References the unified `.github/copilot-instructions.md` for full guidelines
- Ensures consistent instructions across all AI assistants
- Lists most important rules for quick access

**Benefits**:
- Single source of truth (copilot-instructions.md)
- Claude users get tailored quick start
- Consistent code standards across tools

### 3. Created Documentation Directory ✅

**Directory**: `docs/` (new)

**Purpose**: Centralized location for technical documentation, implementation summaries, and setup guides.

**Files Created**:
- `docs/README.md` - Explains directory purpose and organization

**Files Moved**:
- `BRANCH_CLEANUP_SUMMARY.md` → `docs/BRANCH_CLEANUP_SUMMARY.md`
- `VSCODE_TASKS_SETUP.md` → `docs/VSCODE_TASKS_SETUP.md`
- `VSCODE_TASKS.md` → `docs/VSCODE_TASKS.md`

**Result**: Root directory is now cleaner, containing only standard project files.

---

## Documentation Structure

### Before

```
/ (root)
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── ROADMAP.md
├── BRANCH_CLEANUP_SUMMARY.md       ❌ Should be in docs/
├── VSCODE_TASKS_SETUP.md           ❌ Should be in docs/
├── VSCODE_TASKS.md                 ❌ Should be in docs/
└── .github/
    └── copilot-instructions.md
```

### After

```
/ (root)
├── README.md                       ✅ Standard project files only
├── CONTRIBUTING.md
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── ROADMAP.md
├── .claude-instructions.md         ✅ New: Claude reference
├── .github/
│   └── copilot-instructions.md     ✅ Enhanced: 375 lines
└── docs/                           ✅ New: Technical documentation
    ├── README.md
    ├── BRANCH_CLEANUP_SUMMARY.md
    ├── VSCODE_TASKS_SETUP.md
    └── VSCODE_TASKS.md
```

---

## Root Directory Standards

**Reserved for these files only**:

| File                 | Purpose                    |
|----------------------|----------------------------|
| `README.md`          | Main project documentation |
| `CONTRIBUTING.md`    | Contribution guidelines    |
| `CHANGELOG.md`       | Version history            |
| `CODE_OF_CONDUCT.md` | Community standards        |
| `SECURITY.md`        | Security policy            |
| `ROADMAP.md`         | Project roadmap            |
| `LICENSE`            | License file               |

**Everything else** (summaries, guides, technical docs) → `docs/` directory

---

## New AI Assistant Guidelines

### File Organization

**Rule**: Create documentation in `docs/`, not root

```
✅ Good:
- docs/IMPLEMENTATION_SUMMARY.md
- docs/PYPI_SETUP_GUIDE.md
- docs/MIGRATION_NOTES.md

❌ Bad:
- IMPLEMENTATION_SUMMARY.md (in root)
- PYPI_SETUP_GUIDE.md (in root)
- MIGRATION_NOTES.md (in root)
```

### Code Standards

**Type Hints (Python 3.10+)**:
```python
# ❌ Old style
from typing import List, Optional
def foo(items: List[str]) -> Optional[int]:

# ✅ New style
def foo(items: list[str]) -> int | None:
```

**Exception Handling**:
```python
# ❌ Bad
try:
    build_deck()
except:
    pass

# ✅ Good
try:
    build_deck()
except ConfigValidationError as e:
    click.echo(f"Error: {e}", err=True)
    sys.exit(1)
```

**Imports**:
```python
# ❌ Bad
from .builder import AnkiBuilder
from typing import List, Dict

# ✅ Good
from anki_yaml_tool.core.builder import AnkiBuilder
```

---

## Testing Standards

### Requirements
- Minimum **80% code coverage** (currently at 96.77%)
- Write tests for all new features and bug fixes
- Use descriptive test names: `test_<feature>_<scenario>_<expected_result>`
- Mock external dependencies (filesystem, network, commands)

### Running Tests
```bash
# Quick test
pytest tests/

# With coverage
pytest tests/ --cov=anki_yaml_tool --cov-report=term-missing

# VSCode task (recommended)
Ctrl+Shift+P → "Tasks: Run Task" → "CI: Test - pytest with Coverage"
```

---

## Security Guidelines

### Input Validation
- Always validate YAML input (config and data files)
- Check file paths exist before reading
- Use `yaml.safe_load()`, never `yaml.load()`
- Sanitize user input before displaying

### Dependencies
- Security scans run weekly via GitHub Actions
- Review Dependabot PRs promptly
- Check for vulnerabilities with `pip-audit`
- Keep dependencies up to date

### AnkiConnect
- Runs on `127.0.0.1:8765` (localhost only)
- Never expose to internet
- Assume locally trusted

---

## Performance Guidelines

- Deck building should be **fast** (< 1 second for 100 cards)
- Minimize file I/O operations
- Cache parsed YAML where appropriate
- Use generators for large datasets
- Profile before optimizing

---

## Git Workflow

### Before Committing
1. Run `make all` or VSCode task "CI Workflow: Full Pipeline"
2. Ensure all tests pass
3. Verify coverage remains above 80%
4. Check no linting errors
5. Verify type checking passes

### Commit Messages
Use conventional commit format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

---

## Benefits of This Organization

### For Developers
✅ Clear guidelines for where to create files
✅ Cleaner root directory (easier to navigate)
✅ Comprehensive code standards in one place
✅ Consistent instructions across AI assistants
✅ Better security and testing practices

### For AI Assistants
✅ Explicit rules about file placement
✅ Code examples showing correct patterns
✅ Performance and security guidelines
✅ Testing requirements clearly documented
✅ Quick reference for common tasks

### For Project Maintainers
✅ Easier to review PRs (standards documented)
✅ Consistent code quality across contributions
✅ Documentation organized logically
✅ Security best practices enforced
✅ Performance benchmarks established

---

## Quick Reference

| Task               | Location                          |
|--------------------|-----------------------------------|
| Full AI guidelines | `.github/copilot-instructions.md` |
| Claude quick ref   | `.claude-instructions.md`         |
| Technical docs     | `docs/` directory                 |
| VSCode tasks       | `.vscode/tasks.json`              |
| User documentation | `README.md`                       |
| Contribution guide | `CONTRIBUTING.md`                 |

---

## Version History

- **v2.0** (2025-02-05): Major rewrite with comprehensive guidelines and docs/ structure
- **v1.0** (2024): Initial copilot-instructions.md (78 lines)

---

## Next Steps

Future improvements to documentation:
1. Add more examples to copilot-instructions.md
2. Create specific guides in docs/ (e.g., PYPI_SETUP_GUIDE.md, CODECOV_GUIDE.md)
3. Add architecture diagrams
4. Create video tutorials
5. Add troubleshooting guides

---

**Maintained by**: Project contributors
**Last Updated**: 2025-02-05
**Version**: 1.0
