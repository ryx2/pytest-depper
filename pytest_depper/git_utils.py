"""Git utilities for finding changed files."""

import ast
import os
import re
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


def _get_symbol_at_line(file_path: Path, line_number: int) -> str | None:
    """Get the function or class name at a specific line number.

    Args:
        file_path: Path to the Python file
        line_number: Line number to check

    Returns:
        Name of the function or class at that line, or None if not in a function/class
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)

        # Find all function and class definitions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # Check if the line is within this definition
                if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                    if node.lineno <= line_number <= (node.end_lineno or node.lineno):
                        return node.name

        return None
    except Exception:
        return None


def get_changed_symbols(
    base_branch: str = "main",
    project_root: Path | None = None,
) -> dict[str, set[str]]:
    """Get functions and classes that changed compared to base branch.

    Args:
        base_branch: Branch to compare against (default: 'main')
        project_root: Root directory of the project (default: current directory)

    Returns:
        Dictionary mapping file paths to sets of changed symbol names (functions/classes)

    Example:
        >>> changed = get_changed_symbols(base_branch="main")
        >>> print(changed)
        {'calculator.py': {'add', 'subtract'}}
    """
    if project_root is None:
        project_root = Path.cwd()

    # Determine the appropriate git command based on context
    if os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
        cmd = f"git diff -U0 origin/{base_branch}...HEAD"
    else:
        cmd = f"git diff -U0 origin/{base_branch}"

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=project_root)

    if result.returncode != 0:
        # Fallback: try without 'origin/' prefix
        cmd_fallback = f"git diff -U0 {base_branch}"
        result = subprocess.run(cmd_fallback, shell=True, capture_output=True, text=True, cwd=project_root)

        if result.returncode != 0:
            print(f"Warning: Git diff failed: {result.stderr}")
            return {}

    # Parse the diff output to find changed lines
    changed_symbols: dict[str, set[str]] = {}
    current_file = None

    for line in result.stdout.split('\n'):
        # Track which file we're looking at
        if line.startswith('+++'):
            # Extract filename: +++ b/path/to/file.py
            match = re.match(r'\+\+\+ b/(.+\.py)$', line)
            if match:
                current_file = match.group(1)
                if current_file not in changed_symbols:
                    changed_symbols[current_file] = set()

        # Parse changed line numbers: @@ -old_start,old_count +new_start,new_count @@
        elif line.startswith('@@') and current_file:
            match = re.match(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', line)
            if match:
                new_start = int(match.group(1))
                new_count = int(match.group(2)) if match.group(2) else 1

                # For each changed line, find which function/class it belongs to
                file_path = project_root / current_file
                if file_path.exists():
                    for line_num in range(new_start, new_start + new_count):
                        symbol = _get_symbol_at_line(file_path, line_num)
                        if symbol:
                            changed_symbols[current_file].add(symbol)

    # Remove files with no identified symbols
    return {f: symbols for f, symbols in changed_symbols.items() if symbols}


def get_changed_files_and_symbols(
    base_branch: str = "main",
    project_root: Path | None = None,
) -> tuple[list[str], dict[str, set[str]]]:
    """Get both changed files and their changed symbols.

    Args:
        base_branch: Branch to compare against (default: 'main')
        project_root: Root directory of the project (default: current directory)

    Returns:
        Tuple of (list of changed files, dict of file -> changed symbols)
    """
    changed_files = get_changed_files(base_branch=base_branch, project_root=project_root)
    changed_symbols = get_changed_symbols(base_branch=base_branch, project_root=project_root)

    return changed_files, changed_symbols
