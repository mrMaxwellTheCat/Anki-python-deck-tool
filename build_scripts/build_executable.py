#!/usr/bin/env python3
"""Build script for creating standalone executables with PyInstaller.

This script creates platform-specific executables for the Anki Python Deck Tool.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_platform_name() -> str:
    """Get standardized platform name.

    Returns:
        Platform name: 'windows', 'macos', or 'linux'.
    """
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    else:
        return "linux"


def create_spec_files() -> None:
    """Create PyInstaller spec files for CLI and GUI."""
    # Get project root
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"

    # CLI spec file
    cli_spec = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{src_path / "anki_tool" / "cli.py"}'],
    pathex=['{src_path}'],
    binaries=[],
    datas=[],
    hiddenimports=['yaml', 'genanki', 'requests', 'click'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='anki-tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""

    # GUI spec file
    gui_spec = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{src_path / "anki_tool" / "gui.py"}'],
    pathex=['{src_path}'],
    binaries=[],
    datas=[],
    hiddenimports=['yaml', 'genanki', 'requests', 'tkinter'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='anki-tool-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""

    # Write spec files
    (project_root / "build_scripts" / "anki-tool.spec").write_text(cli_spec)
    (project_root / "build_scripts" / "anki-tool-gui.spec").write_text(gui_spec)
    print("✓ Created PyInstaller spec files")


def build_executables() -> None:
    """Build standalone executables using PyInstaller."""
    project_root = Path(__file__).parent.parent
    build_scripts_dir = project_root / "build_scripts"
    dist_dir = project_root / "dist"

    # Clean previous builds
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    build_dir = project_root / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir)

    print("Building executables...")

    # Build CLI
    print("\n→ Building CLI executable...")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            str(build_scripts_dir / "anki-tool.spec"),
        ],
        check=True,
    )

    # Build GUI
    print("\n→ Building GUI executable...")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            str(build_scripts_dir / "anki-tool-gui.spec"),
        ],
        check=True,
    )

    print("\n✓ Executables built successfully!")
    print(f"  Output directory: {dist_dir}")


def create_distribution_package() -> None:
    """Create platform-specific distribution package."""
    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist"
    platform_name = get_platform_name()

    # TODO: Parse version from pyproject.toml to maintain single source of truth
    version = "0.1.0"

    package_name = f"anki-tool-{version}-{platform_name}"
    package_dir = dist_dir / package_name

    # Create package directory
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True)

    # Copy executables
    print(f"\nCreating distribution package: {package_name}")

    if platform_name == "windows":
        shutil.copy(dist_dir / "anki-tool.exe", package_dir)
        shutil.copy(dist_dir / "anki-tool-gui.exe", package_dir)
    else:
        shutil.copy(dist_dir / "anki-tool", package_dir)
        shutil.copy(dist_dir / "anki-tool-gui", package_dir)
        # Make executables on Unix-like systems
        os.chmod(package_dir / "anki-tool", 0o755)
        os.chmod(package_dir / "anki-tool-gui", 0o755)

    # Copy README and LICENSE
    shutil.copy(project_root / "README.md", package_dir)
    shutil.copy(project_root / "LICENSE", package_dir)

    # Create archive
    print("Creating archive...")
    if platform_name == "windows":
        archive_name = shutil.make_archive(
            str(dist_dir / package_name), "zip", dist_dir, package_name
        )
    else:
        archive_name = shutil.make_archive(
            str(dist_dir / package_name), "gztar", dist_dir, package_name
        )

    print(f"✓ Distribution package created: {archive_name}")


def main() -> None:
    """Main build script entry point."""
    print("=" * 60)
    print("Anki Python Deck Tool - Build Script")
    print("=" * 60)
    print(f"Platform: {platform.system()} ({get_platform_name()})")
    print(f"Python: {sys.version}")
    print("=" * 60)

    try:
        # Step 1: Create spec files
        print("\n[1/3] Creating PyInstaller spec files...")
        create_spec_files()

        # Step 2: Build executables
        print("\n[2/3] Building executables...")
        build_executables()

        # Step 3: Create distribution package
        print("\n[3/3] Creating distribution package...")
        create_distribution_package()

        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL!")
        print("=" * 60)

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
