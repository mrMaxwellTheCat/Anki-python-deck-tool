import os
import platform
import subprocess
import sys


def build():
    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_path = os.path.join(base_dir, "src", "anki_yaml_tool", "cli.py")
    assets_dir = os.path.join(base_dir, "assets")

    # Base command
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--name",
        "anki-yaml-tool",
        "--onefile",
        "--copy-metadata=anki-yaml-tool",
        f"--paths={os.path.join(base_dir, 'src')}",
    ]

    # Detect OS and Icon
    system = platform.system()
    icon_path = None

    if system == "Darwin":
        candidate = os.path.join(assets_dir, "icon.icns")
        if os.path.exists(candidate):
            icon_path = candidate
            print(f"Using macOS icon: {icon_path}")
    else:
        # Windows and Linux (Windows requires .ico)
        candidate = os.path.join(assets_dir, "icon.ico")
        if os.path.exists(candidate):
            icon_path = candidate
            print(f"Using icon: {icon_path}")

    if icon_path:
        cmd.append(f"--icon={icon_path}")
    else:
        print(
            f"No custom icon found for {system}. "
            "To add one, place 'icon.ico' (Windows/Linux) "
            "or 'icon.icns' (macOS) in 'assets/' directory."
        )

    # Add entry point
    cmd.append(src_path)

    # Run
    print("Building executable...")
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    build()
