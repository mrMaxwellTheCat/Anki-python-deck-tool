# Build Scripts

This directory contains scripts for building standalone executables of the Anki Python Deck Tool.

## Prerequisites

Make sure you have the development dependencies installed:

```bash
pip install -e ".[dev]"
```

This will install PyInstaller and other required tools.

## Building Executables

To build standalone executables for your platform:

```bash
python build_scripts/build_executable.py
```

This will:
1. Create PyInstaller spec files
2. Build both CLI (`anki-tool`) and GUI (`anki-tool-gui`) executables
3. Package them with documentation into a distribution archive

The output will be in the `dist/` directory.

## Platform-Specific Builds

The build script automatically detects your platform and creates appropriate executables:

- **Windows**: `anki-tool.exe` and `anki-tool-gui.exe`, packaged as `.zip`
- **macOS**: `anki-tool` and `anki-tool-gui`, packaged as `.tar.gz`
- **Linux**: `anki-tool` and `anki-tool-gui`, packaged as `.tar.gz`

## Automated Builds

The `.github/workflows/build-executables.yml` workflow automatically builds executables for all platforms when a version tag is pushed:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The executables will be attached to the GitHub release.

## Manual Workflow Trigger

You can also manually trigger the build workflow from the GitHub Actions tab without creating a tag.
