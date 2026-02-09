import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import time

LOG_LEVEL = "WARN"  # Available: TRACE, DEBUG, INFO, WARN, ERROR, CRITICAL


def on_rm_error(func, path, exc_info):
    """
    Error handler for shutil.rmtree.
    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.
    If the error is for another reason it re-raises the error.
    """
    # Is the error an access error?
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    else:
        raise exc_info[1]


def clean_dir(dir_path):
    """Robustly clean a directory with retries."""
    if os.path.exists(dir_path):
        print(f"Cleaning {dir_path}...")
        for i in range(3):
            try:
                shutil.rmtree(dir_path, onerror=on_rm_error)
                break
            except PermissionError:
                if i < 2:
                    print(f"  Access denied. Retrying in 1s... ({i + 1}/3)")
                    time.sleep(1)
                else:
                    print(
                        f"  Warning: Could not fully clean {dir_path}. Build might fail."
                    )


def build():
    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_path = os.path.join(base_dir, "src", "anki_yaml_tool", "cli.py")
    assets_dir = os.path.join(base_dir, "assets")
    # build_dir = os.path.join(base_dir, "build") # Avoid using local build dir due to locks
    dist_dir = os.path.join(base_dir, "dist")

    # Create a temporary directory for build artifacts
    with tempfile.TemporaryDirectory() as temp_build_dir:
        print(f"Using temporary build directory: {temp_build_dir}")

        # Clean dist dir
        clean_dir(dist_dir)

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
            f"--workpath={temp_build_dir}",  # Use temp dir for build artifacts
            f"--distpath={dist_dir}",  # Output exe to dist folder
            f"--specpath={temp_build_dir}",  # Put spec file in temp dir too
            f"--log-level={LOG_LEVEL}",
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
        ret_code = subprocess.call(cmd)

        if ret_code != 0:
            print("Build failed.")
            sys.exit(ret_code)

        print(f"Build successful! Executable is in {dist_dir}")


if __name__ == "__main__":
    build()
