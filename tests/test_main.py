"""Tests for __main__ module entry point."""

import subprocess
import sys


def test_main_module_entry_point() -> None:
    """Test that the package can be run as a module with -m flag."""
    # Run the module and check it executes without error
    # Use --help to get a quick successful execution
    result = subprocess.run(
        [sys.executable, "-m", "gpx", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    # Should exit successfully with help output
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower() or "gpx" in result.stdout.lower()


def test_main_module_version() -> None:
    """Test that the package shows version when run with --version."""
    result = subprocess.run(
        [sys.executable, "-m", "gpx", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    # Should exit successfully
    assert result.returncode == 0
