#!/usr/bin/env python3
"""
Virtual Environment Optimizer

This script safely removes Python source files from a virtual environment
when compiled bytecode (.pyc files) exist and are newer than the source files.
This helps reduce image size while preserving functionality.
"""

import os
import sys
from pathlib import Path
from typing import List


def optimize_venv(venv_path: str) -> None:
    """
    Optimize virtual environment by removing source files when bytecode exists.

    Args:
        venv_path: Path to the virtual environment
    """
    venv_dir = Path(venv_path)
    if not venv_dir.exists():
        print(f"Virtual environment not found: {venv_path}")
        return

    removed_count = 0
    skipped_count = 0

    # Find all .py files in the virtual environment
    for py_file in venv_dir.rglob("*.py"):
        # Skip certain essential files that should never be removed
        if _should_skip_file(py_file):
            skipped_count += 1
            continue

        # Get corresponding .pyc file path
        pyc_file = py_file.with_suffix(".pyc")

        # Only remove .py file if .pyc exists and is newer
        if pyc_file.exists() and pyc_file.stat().st_mtime > py_file.stat().st_mtime:
            try:
                py_file.unlink()
                removed_count += 1
                print(f"Removed: {py_file}")
            except OSError as e:
                print(f"Failed to remove {py_file}: {e}")
        else:
            skipped_count += 1

    # Remove .pyi files (type stubs) as they're not needed at runtime
    pyi_removed = 0
    for pyi_file in venv_dir.rglob("*.pyi"):
        try:
            pyi_file.unlink()
            pyi_removed += 1
        except OSError as e:
            print(f"Failed to remove {pyi_file}: {e}")

    # Remove __pycache__ directories
    cache_removed = 0
    for cache_dir in venv_dir.rglob("__pycache__"):
        if cache_dir.is_dir():
            try:
                import shutil

                shutil.rmtree(cache_dir)
                cache_removed += 1
            except OSError as e:
                print(f"Failed to remove {cache_dir}: {e}")

    print(f"\nOptimization complete:")
    print(f"  - Removed {removed_count} .py files")
    print(f"  - Skipped {skipped_count} .py files")
    print(f"  - Removed {pyi_removed} .pyi files")
    print(f"  - Removed {cache_removed} __pycache__ directories")


def _should_skip_file(file_path: Path) -> bool:
    """
    Check if a file should be skipped during optimization.

    Args:
        file_path: Path to the file to check

    Returns:
        True if the file should be skipped
    """
    # Skip essential files that are needed for imports
    essential_patterns = [
        "__init__.py",
        "_virtualenv.py",
        "site.py",
        "distutils/",
        "setuptools/",
        "pip/",
        "wheel/",
        "uv/",
    ]

    file_str = str(file_path)
    for pattern in essential_patterns:
        if pattern in file_str:
            return True

    return False


if __name__ == "__main__":
    venv_path = sys.argv[1] if len(sys.argv) > 1 else "/app/.venv"
    optimize_venv(venv_path)
