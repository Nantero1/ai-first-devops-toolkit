#!/usr/bin/env python3
"""
Local release script for testing before GitHub Actions release.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, check=True):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/release.py <version>")
        print("Example: python scripts/release.py 1.0.0")
        sys.exit(1)

    version = sys.argv[1]

    # Validate version format
    if not version.replace(".", "").isdigit():
        print("Error: Version must be in format X.Y.Z (e.g., 1.0.0)")
        sys.exit(1)

    print(f"Preparing release v{version}...")

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("Error: pyproject.toml not found. Run this script from the project root.")
        sys.exit(1)

    # Run tests
    print("\n1. Running tests...")
    run_command("uv run pytest tests/unit/ -v")

    # Update version in pyproject.toml
    print(f"\n2. Updating version to {version}...")
    with open("pyproject.toml", "r") as f:
        content = f.read()

    # Simple version replacement (assumes version is on its own line)
    import re

    content = re.sub(r'version = ".*"', f'version = "{version}"', content)

    with open("pyproject.toml", "w") as f:
        f.write(content)

    # Build package
    print("\n3. Building package...")
    run_command("uv run build")

    # Check if dist/ directory was created
    if not Path("dist").exists():
        print("Error: Build failed - dist/ directory not created")
        sys.exit(1)

    print(f"\n✅ Release v{version} prepared successfully!")
    print("\nNext steps:")
    print("1. Review the built package in dist/")
    print("2. Test installation: pip install dist/*.whl")
    print("3. If satisfied, run: uv run twine upload dist/*")
    print("4. Create a GitHub release manually or use the GitHub Actions workflow")


if __name__ == "__main__":
    main()
