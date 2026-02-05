# Documentation Directory

This directory contains technical documentation, implementation summaries, and setup guides for the Anki Python Deck Tool project.

## Purpose

All project-specific documentation that doesn't fit in the root directory goes here. This keeps the root clean and organized.

## What Goes Here

### ✅ Documentation Files

- **Implementation summaries** - Summaries of major implementation phases
- **Setup guides** - Detailed setup instructions for various integrations
- **Technical notes** - Architecture decisions, migration guides, etc.
- **Branch management** - Notes on branch cleanup, merge strategies
- **Tool configuration** - Extended documentation for VSCode, CI/CD, etc.

### ❌ NOT for Root Directory

Files that should be created here instead of root:
- `*_SUMMARY.md` - Implementation or cleanup summaries
- `*_SETUP.md` - Setup guides for tools or services
- `*_GUIDE.md` - Technical guides and how-tos
- `*_NOTES.md` - Development notes and decisions

## Root Directory Reserved For

The root directory should only contain these standard documentation files:
- `README.md` - Main project documentation
- `CONTRIBUTING.md` - Contribution guidelines
- `CHANGELOG.md` - Version history
- `CODE_OF_CONDUCT.md` - Community standards
- `SECURITY.md` - Security policy
- `ROADMAP.md` - Project roadmap
- `LICENSE` - License file

## Current Documentation

| File                        | Description                                           |
|-----------------------------|-------------------------------------------------------|
| `VSCODE_TASKS_SETUP.md`     | Complete guide to VSCode tasks for running CI locally |
| `BRANCH_CLEANUP_SUMMARY.md` | Summary of branch cleanup and merge decisions         |
| `VSCODE_TASKS.md`           | Quick reference for VSCode task usage                 |

## Adding New Documentation

When creating new documentation:

1. **Check if it belongs in root** - Is it one of the standard files listed above?
2. **If no, create it here** in `docs/`
3. **Use descriptive names** - e.g., `CODECOV_SETUP_GUIDE.md`, `INTEGRATION_TEST_SUMMARY.md`
4. **Update this README** - Add entry to "Current Documentation" table
5. **Link from relevant places** - Reference from README, CONTRIBUTING, etc.

## Documentation Structure

```
docs/
├── README.md                      # This file
├── VSCODE_TASKS_SETUP.md          # VSCode tasks complete guide
├── VSCODE_TASKS.md                # VSCode tasks quick reference
├── BRANCH_CLEANUP_SUMMARY.md      # Branch management summary
└── [future documentation files]

Related documentation:
├── .vscode/README.md              # VSCode-specific setup
├── .github/copilot-instructions.md # AI assistant guidelines
└── README.md (root)               # Main project docs
```

## For AI Assistants

If you're an AI assistant (GitHub Copilot, Claude, etc.) working on this project:

**Rule**: When asked to create implementation summaries, setup guides, or technical documentation, **always create them in this `docs/` directory**, not in the root.

Example:
- ❌ Bad: `PYPI_SETUP_GUIDE.md` (in root)
- ✅ Good: `docs/PYPI_SETUP_GUIDE.md`

See `.github/copilot-instructions.md` for complete guidelines.

---

**Maintained by**: Project contributors
**Last Updated**: 2025-02-05
