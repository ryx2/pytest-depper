"""Git utilities for finding changed files."""

import os
import subprocess
from pathlib import Path


def get_changed_files(
    base_branch: str = "main",
    file_extensions: list[str] | None = None,
    project_root: Path | None = None,
) -> list[str]:
    """Get list of changed files compared to a base branch.

    Args:
        base_branch: Branch to compare against (default: 'main')
        file_extensions: List of file extensions to filter (e.g., ['.py'])
        project_root: Root directory of the project (default: current directory)

    Returns:
        List of changed file paths relative to project root

    Example:
        >>> changed = get_changed_files(base_branch="main", file_extensions=[".py"])
        >>> print(changed)
        ['src/models/user.py', 'tests/test_user.py']
    """
    if project_root is None:
        project_root = Path.cwd()

    if file_extensions is None:
        file_extensions = [".py"]

    # Determine the appropriate git command based on context
    if os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
        # In GitHub Actions PR context
        cmd = f"git diff --name-only origin/{base_branch}...HEAD"
    else:
        # Local development
        cmd = f"git diff --name-only origin/{base_branch}"

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=project_root)

    if result.returncode != 0:
        # Fallback: try without 'origin/' prefix
        cmd_fallback = f"git diff --name-only {base_branch}"
        result = subprocess.run(cmd_fallback, shell=True, capture_output=True, text=True, cwd=project_root)

        if result.returncode != 0:
            print(f"Warning: Git command failed: {result.stderr}")
            return []

    all_changed_files = result.stdout.strip().split("\n")

    # Filter for specified file extensions and files that exist
    filtered_files = [
        f
        for f in all_changed_files
        if any(f.endswith(ext) for ext in file_extensions) and (project_root / f).exists()
    ]

    return filtered_files


def has_unstaged_changes(project_root: Path | None = None) -> bool:
    """Check if there are unstaged changes in the git repository.

    Args:
        project_root: Root directory of the project (default: current directory)

    Returns:
        True if there are unstaged changes
    """
    if project_root is None:
        project_root = Path.cwd()

    result = subprocess.run(
        "git diff --quiet",
        shell=True,
        capture_output=True,
        cwd=project_root,
    )

    # git diff --quiet returns 1 if there are differences
    return result.returncode != 0


def get_current_branch(project_root: Path | None = None) -> str:
    """Get the name of the current git branch.

    Args:
        project_root: Root directory of the project (default: current directory)

    Returns:
        Name of the current branch
    """
    if project_root is None:
        project_root = Path.cwd()

    result = subprocess.run(
        "git branch --show-current",
        shell=True,
        capture_output=True,
        text=True,
        cwd=project_root,
    )

    if result.returncode != 0:
        return "unknown"

    return result.stdout.strip()
