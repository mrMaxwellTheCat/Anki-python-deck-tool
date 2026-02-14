"""File watching module for automatic deck building.

This module provides file system monitoring capabilities to automatically
rebuild and optionally push Anki decks when source files change.
"""

import signal
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path

from anki_yaml_tool.core.logging_config import get_logger

log = get_logger("watcher")

# Default patterns to ignore (temporary files, editor swaps, etc.)
DEFAULT_IGNORE_PATTERNS = [
    # Editor temporary files
    "*.swp",
    "*.swo",
    "*~",
    ".*.swp",
    ".*.swo",
    # Backup files
    "*.bak",
    "*.tmp",
    # Python cache
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    # IDE files
    ".vscode",
    ".idea",
    "*.DS_Store",
    # Git
    ".git",
    # Cache files
    ".cache",
    "*.egg-info",
]


class DebouncedCallback:
    """A callback that debounces rapid calls.

    This prevents multiple executions when multiple file change events
    fire in quick succession (e.g., when saving a file).
    """

    def __init__(self, callback: Callable[[], None], debounce_seconds: float = 1.0):
        """Initialize the debounced callback.

        Args:
            callback: The function to call after the debounce period
            debounce_seconds: Minimum time between callback executions
        """
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def trigger(self) -> None:
        """Trigger the callback after the debounce period."""
        with self._lock:
            # Cancel any existing timer
            if self._timer is not None:
                self._timer.cancel()

            # Schedule a new timer
            self._timer = threading.Timer(self.debounce_seconds, self._execute)
            self._timer.start()

    def _execute(self) -> None:
        """Execute the callback."""
        try:
            self.callback()
        except Exception as e:
            log.error("Error in debounced callback: %s", e)

    def cancel(self) -> None:
        """Cancel any pending callback."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None


class FileWatcher:
    """Watches files for changes and triggers callbacks.

    This class uses the watchdog library to monitor file system changes
    and provides debouncing to avoid rapid successive rebuilds.
    """

    def __init__(
        self,
        watch_path: Path,
        ignore_patterns: list[str] | None = None,
        debounce_seconds: float = 1.0,
    ):
        """Initialize the file watcher.

        Args:
            watch_path: Path to file or directory to watch
            ignore_patterns: List of glob patterns to ignore
            debounce_seconds: Time to wait after a change before triggering
        """
        self.watch_path = watch_path
        self.ignore_patterns = ignore_patterns or DEFAULT_IGNORE_PATTERNS
        self.debounce_seconds = debounce_seconds

        self._observer = None
        self._debounced_callback: DebouncedCallback | None = None
        self._running = False
        self._stop_event = threading.Event()

    def _should_ignore(self, path: str) -> bool:
        """Check if a path should be ignored based on ignore patterns.

        Args:
            path: The file path to check

        Returns:
            True if the path matches any ignore pattern
        """
        path_obj = Path(path)
        name = path_obj.name

        for pattern in self.ignore_patterns:
            # Check if it's a directory pattern
            if "/" in pattern or "\\" in pattern:
                # Check if the path contains this directory
                if pattern.rstrip("/*").rstrip("\\*") in path_obj.parts:
                    return True
            else:
                # Simple filename pattern
                if pattern.startswith("*"):
                    # Glob pattern
                    import fnmatch

                    if fnmatch.fnmatch(name, pattern):
                        return True
                elif name == pattern:
                    return True

        return False

    def _on_file_changed(self, event) -> None:
        """Handle file change events.

        Args:
            event: The watchdog event object
        """
        # Get the file path from the event
        if hasattr(event, "src_path"):
            file_path = event.src_path
        elif hasattr(event, "path"):
            file_path = event.path
        else:
            return

        # Skip directories
        if hasattr(event, "is_directory") and event.is_directory:
            return

        # Check if we should ignore this file
        if self._should_ignore(file_path):
            log.debug("Ignoring change to: %s", file_path)
            return

        # Check if the changed file is our target or related
        if self.watch_path.is_file():
            # Watch a specific file
            if Path(file_path) != self.watch_path:
                return
        else:
            # Watch a directory - check if it's a YAML file
            if not file_path.endswith((".yaml", ".yml")):
                return

        log.info("File change detected: %s", file_path)
        if self._debounced_callback:
            self._debounced_callback.trigger()

    def start(self, on_change: Callable[[], None]) -> None:
        """Start watching for file changes.

        Args:
            on_change: Callback function to call when files change
        """
        try:
            from watchdog.observers import Observer
        except ImportError:
            raise ImportError(
                "watchdog is not installed. Install it with: "
                "pip install anki-yaml-tool[watch]"
            ) from None

        # Create the debounced callback
        self._debounced_callback = DebouncedCallback(on_change, self.debounce_seconds)

        # Determine what to watch
        if self.watch_path.is_file():
            watch_dir = self.watch_path.parent
        else:
            watch_dir = self.watch_path

        # Create and configure the observer
        from watchdog.events import FileSystemEventHandler

        class WatchHandler(FileSystemEventHandler):
            def __init__(self, watcher: FileWatcher):
                self.watcher = watcher

            def on_modified(self, event):
                self.watcher._on_file_changed(event)

            def on_created(self, event):
                self.watcher._on_file_changed(event)

        self._observer = Observer()
        handler = WatchHandler(self)
        self._observer.schedule(handler, str(watch_dir), recursive=False)
        self._observer.start()
        self._running = True

        log.info("Watching %s for changes...", self.watch_path)

    def stop(self) -> None:
        """Stop watching for file changes."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None

        if self._debounced_callback:
            self._debounced_callback.cancel()

        self._running = False
        log.info("Stopped watching for changes")

    def is_running(self) -> bool:
        """Check if the watcher is currently running."""
        return self._running


def wait_for_keyboard_interrupt() -> None:
    """Wait for keyboard interrupt (Ctrl+C) in a cross-platform way."""
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


def run_watcher(
    file_path: Path,
    on_change: Callable[[], None],
    debounce_seconds: float = 1.0,
    ignore_patterns: list[str] | None = None,
) -> None:
    """Run a file watcher with keyboard interrupt handling.

    This is a convenience function that sets up the watcher and handles
    Ctrl+C gracefully.

    Args:
        file_path: Path to file or directory to watch
        on_change: Callback function to call when files change
        debounce_seconds: Time to wait after a change before triggering
        ignore_patterns: List of glob patterns to ignore
    """
    watcher = FileWatcher(
        watch_path=file_path,
        ignore_patterns=ignore_patterns,
        debounce_seconds=debounce_seconds,
    )

    # Handle shutdown signals
    def shutdown_handler(signum, frame):
        log.info("Shutting down watcher...")
        watcher.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        watcher.start(on_change)
        wait_for_keyboard_interrupt()
    finally:
        watcher.stop()
