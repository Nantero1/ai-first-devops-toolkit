#!/usr/bin/env python3
"""
Helper script for generating release notes template variables from git history.
Extracts commit history between tags and prepares data for LLM analysis.
"""

import subprocess
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional


def run_git_command(cmd: List[str]) -> str:
    """Run a git command and return the output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command {' '.join(cmd)}: {e}")
        return ""


def get_previous_tag() -> str:
    """Get the previous version tag."""
    # Try to get the previous tag
    previous_tag = run_git_command(["git", "describe", "--tags", "--abbrev=0", "HEAD~1"])
    if not previous_tag:
        # If no previous tag exists, use v0.0.0
        return "v0.0.0"
    return previous_tag


def get_commit_history(previous_tag: str) -> str:
    """Get commit history between previous tag and HEAD."""
    return run_git_command(
        [
            "git",
            "log",
            f"{previous_tag}..HEAD",
            "--pretty=format:%h|%s|%ad",
            "--date=short",
        ]
    )


def get_changed_files(previous_tag: str) -> str:
    """Get list of changed files between previous tag and HEAD."""
    return run_git_command(["git", "diff", "--name-only", f"{previous_tag}..HEAD"])


def get_commit_count(previous_tag: str) -> int:
    """Get the number of commits between previous tag and HEAD."""
    count_str = run_git_command(["git", "rev-list", "--count", f"{previous_tag}..HEAD"])
    return int(count_str) if count_str else 0


def create_template_vars(version: str, manual_instructions: Optional[str] = None) -> Dict:
    """Create template variables from git history."""
    previous_tag = get_previous_tag()
    commit_history = get_commit_history(previous_tag)
    changed_files = get_changed_files(previous_tag)
    commit_count = get_commit_count(previous_tag)

    template_vars = {
        "version": version,
        "previous_version": previous_tag,
        "commit_history": commit_history,
        "changed_files": changed_files,
        "commit_count": commit_count,
    }

    if manual_instructions:
        template_vars["manual_instructions"] = manual_instructions

    return template_vars


def save_template_vars(template_vars: Dict, output_file: str) -> None:
    """Save template variables to YAML file."""
    with open(output_file, "w") as f:
        yaml.dump(template_vars, f, default_flow_style=False, sort_keys=False)
    print(f"Template variables saved to {output_file}")


def main():
    """Main function for generating release notes template variables."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate-release-notes.py <version> [manual_instructions]")
        print("Example: python scripts/generate-release-notes.py 1.0.1")
        print("Example: python scripts/generate-release-notes.py 1.0.1 'This release includes...'")
        sys.exit(1)

    version = sys.argv[1]
    manual_instructions = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Generating template variables for version {version}...")

    # Create template variables
    template_vars = create_template_vars(version, manual_instructions)

    # Save to file
    output_file = "template-vars.yaml"
    save_template_vars(template_vars, output_file)

    # Print summary
    print(f"\nSummary:")
    print(f"- Version: {version}")
    print(f"- Previous tag: {template_vars['previous_version']}")
    print(f"- Commits: {template_vars['commit_count']}")
    print(
        f"- Changed files: {len(template_vars['changed_files'].splitlines()) if template_vars['changed_files'] else 0}"
    )

    if manual_instructions:
        print(f"- Manual instructions: {len(manual_instructions)} characters")

    print(f"\nTemplate variables ready for LLM analysis.")


if __name__ == "__main__":
    main()
