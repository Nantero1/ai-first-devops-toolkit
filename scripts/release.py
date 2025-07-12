#!/usr/bin/env python3
"""
Local release script for testing before GitHub Actions release.
Follows Python packaging best practices.
"""

import re
import subprocess
import sys
import tomllib
from pathlib import Path


def run_command(cmd: list[str], check: bool = True, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=capture_output, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def validate_version(version: str) -> bool:
    """Validate semantic versioning format."""
    # Semantic versioning regex: X.Y.Z[-prerelease][+build]
    pattern = r"^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$"
    return bool(re.match(pattern, version))


def get_current_version() -> str:
    """Get current version from pyproject.toml."""
    try:
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
        return data["project"]["version"]
    except (KeyError, FileNotFoundError) as e:
        print(f"Error reading version from pyproject.toml: {e}")
        sys.exit(1)


def update_version(version: str) -> None:
    """Update version in pyproject.toml using Python."""
    try:
        with open("pyproject.toml") as f:
            content = f.read()

        # More precise approach: find the [project] section and update version there
        # This ensures we only update the project version, not dependency versions

        # Split content into lines for easier processing
        lines = content.split("\n")
        updated_lines = []
        in_project_section = False
        version_updated = False

        for line in lines:
            # Check if we're entering the [project] section
            if line.strip() == "[project]":
                in_project_section = True
                updated_lines.append(line)
            # Check if we're leaving the [project] section
            elif line.strip().startswith("[") and line.strip() != "[project]":
                in_project_section = False
                updated_lines.append(line)
            # If we're in the [project] section and this is the version line
            elif in_project_section and line.strip().startswith("version ="):
                # Update the version
                updated_lines.append(f'version = "{version}"')
                version_updated = True
                print(f'Found and updated version line: {line.strip()} -> version = "{version}"')
            else:
                updated_lines.append(line)

        if not version_updated:
            print("Error: Project version line not found in [project] section")
            return

        # Write the updated content back
        updated_content = "\n".join(updated_lines)

        with open("pyproject.toml", "w") as f:
            f.write(updated_content)

        print(f"Successfully updated project version to {version}")

    except Exception as e:
        print(f"Error updating version: {e}")
        sys.exit(1)


def check_git_status() -> None:
    """Check if git repository is clean."""
    result = run_command(["git", "status", "--porcelain"], check=False)
    if result.stdout.strip():
        print("❌ Git repository is not clean. Please commit or stash changes first.")
        print("Uncommitted changes:")
        print(result.stdout)
        sys.exit(1)
    print("✅ Git repository is clean")


def check_tag_exists(version: str) -> bool:
    """Check if git tag already exists."""
    result = run_command(["git", "tag", "-l", f"v{version}"], check=False)
    return bool(result.stdout.strip())


def run_tests() -> None:
    """Run the test suite."""
    print("\n1. Running tests...")
    run_command(["uv", "run", "pytest", "tests/unit/", "-v"])


def run_linting() -> None:
    """Run linting checks."""
    print("\n2. Running linting...")
    run_command(["uv", "run", "ruff", "check", "*.py"])
    run_command(["uv", "run", "ruff", "format", "--check", "*.py"])
    run_command(["uv", "run", "mypy", "llm_ci_runner/"])


def check_security() -> None:
    """Check for security vulnerabilities."""
    print("\n3. Checking for security vulnerabilities...")
    run_command(["uv", "run", "pip-audit"])


def validate_package_metadata() -> None:
    """Validate package metadata."""
    print("\n4. Validating package metadata...")
    try:
        with open("pyproject.toml", "rb") as f:
            tomllib.load(f)
        print("✅ pyproject.toml is valid")
    except Exception as e:
        print(f"❌ Invalid pyproject.toml: {e}")
        sys.exit(1)


def build_package() -> None:
    """Build the package."""
    print("\n5. Building package...")
    run_command(["uv", "run", "python", "-m", "build"])

    # Verify build output
    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("❌ Build failed - dist/ directory not created")
        sys.exit(1)

    wheel_files = list(dist_dir.glob("*.whl"))
    if not wheel_files:
        print("❌ Build failed - no wheel files found")
        sys.exit(1)

    print(f"✅ Package built successfully: {wheel_files[0].name}")


def test_package_installation() -> None:
    """Test that the package can be installed."""
    print("\n6. Testing package installation...")

    dist_dir = Path("dist")
    wheel_files = list(dist_dir.glob("*.whl"))
    wheel_file = wheel_files[0]

    # Test installation
    result = run_command(["uv", "run", "pip", "install", str(wheel_file), "--force-reinstall"])

    if result.returncode == 0:
        print("✅ Package installation test passed")
    else:
        print("❌ Package installation test failed")
        sys.exit(1)


def create_git_tag(version: str, dry_run: bool = False) -> None:
    """Create git tag for the release."""
    if dry_run:
        print(f"\n7. [DRY RUN] Would create tag v{version}")
        return

    print(f"\n7. Creating git tag v{version}...")

    # Add the version change
    run_command(["git", "add", "pyproject.toml"])
    run_command(["git", "commit", "-m", f"chore: bump version to {version} [skip ci]"])

    # Create tag
    run_command(["git", "tag", "-a", f"v{version}", "-m", f"Release v{version}"])

    print("✅ Git tag created successfully")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/release.py <version> [--dry-run]")
        print("Example: python scripts/release.py 1.0.0")
        print("Example: python scripts/release.py 1.0.0 --dry-run")
        sys.exit(1)

    version = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("🔍 DRY RUN MODE - No actual changes will be made")

    # Validate version format
    if not validate_version(version):
        print(f"❌ Invalid version format: {version}")
        print("Version must follow semantic versioning (e.g., 1.0.0, 1.0.0-alpha.1)")
        sys.exit(1)

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ pyproject.toml not found. Run this script from the project root.")
        sys.exit(1)

    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    print(f"Target version: {version}")

    if current_version == version:
        print("⚠️  Version is already set to target version")

    # Check git status
    check_git_status()

    # Check if tag already exists
    if check_tag_exists(version):
        print(f"❌ Tag v{version} already exists")
        sys.exit(1)

    print(f"\n🚀 Preparing release v{version}...")

    # Run all validation steps
    run_tests()
    run_linting()
    check_security()
    validate_package_metadata()

    # Update version
    print(f"\n5. Updating version to {version}...")
    update_version(version)

    # Build and test package
    build_package()
    test_package_installation()

    # Create git tag
    create_git_tag(version, dry_run)

    print(f"\n🎉 Release v{version} prepared successfully!")

    if dry_run:
        print("\nThis was a dry run. To perform the actual release:")
        print(f"1. Run: python scripts/release.py {version}")
        print("2. Push the tag: git push origin v{version}")
        print("3. Push the commit: git push origin main")
    else:
        print("\nNext steps:")
        print("1. Review the built package in dist/")
        print("2. Push the tag: git push origin v{version}")
        print("3. Push the commit: git push origin main")
        print("4. Create a GitHub release manually or use the GitHub Actions workflow")
        print("5. Publish to PyPI: uv run twine upload dist/*")


if __name__ == "__main__":
    main()
