"""Pytest plugin for intelligent test selection based on code dependencies."""

import os
from pathlib import Path

import pytest

from .analyzer import DependencyAnalyzer
from .git_utils import get_changed_files


def pytest_addoption(parser):
    """Add command-line options for pytest-depper."""
    group = parser.getgroup("depper")
    group.addoption(
        "--depper",
        action="store_true",
        default=False,
        help="Enable smart test selection based on changed files",
    )
    group.addoption(
        "--depper-base-branch",
        action="store",
        default="main",
        help="Base branch to compare against (default: main)",
    )
    group.addoption(
        "--depper-debug",
        action="store_true",
        default=False,
        help="Print detailed dependency analysis information",
    )
    group.addoption(
        "--depper-run-all-on-error",
        action="store_true",
        default=False,
        help="Run all tests if no changed files are detected",
    )


def pytest_configure(config):
    """Register the depper plugin markers."""
    config.addinivalue_line("markers", "depper: marks tests for depper smart selection")


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on dependency analysis.

    This is the main entry point for the plugin. It:
    1. Checks if --depper flag is enabled
    2. Finds changed files using git
    3. Analyzes dependencies
    4. Deselects tests that are not affected by changes
    """
    if not config.getoption("--depper"):
        return

    # Get configuration
    base_branch = config.getoption("--depper-base-branch")
    debug = config.getoption("--depper-debug")
    run_all_on_error = config.getoption("--depper-run-all-on-error")

    # Get project root (where pytest is running from)
    project_root = Path(config.rootpath)

    # Find changed files
    changed_files = get_changed_files(base_branch=base_branch, project_root=project_root)

    if not changed_files:
        if run_all_on_error:
            print("\nNo changed files detected. Running all tests (--depper-run-all-on-error enabled).")
            return
        else:
            print("\nNo changed files detected. Deselecting all tests.")
            print("Use --depper-run-all-on-error to run all tests when no changes are detected.")
            for item in items:
                item.add_marker(pytest.mark.skip(reason="No files changed"))
            return

    print(f"\nDepper: Found {len(changed_files)} changed files")
    if debug:
        for f in changed_files:
            print(f"  - {f}")

    # Analyze dependencies
    try:
        analyzer = DependencyAnalyzer(project_root=project_root)
    except Exception as e:
        print(f"\nDepper: Error during dependency analysis: {e}")
        if run_all_on_error:
            print("Running all tests due to error.")
            return
        else:
            print("Deselecting all tests due to error.")
            for item in items:
                item.add_marker(pytest.mark.skip(reason=f"Depper analysis error: {e}"))
            return

    # Print debug info if requested
    if debug:
        analyzer.print_dependency_info(changed_files)

    # Get affected tests
    affected_tests = analyzer.get_affected_tests(changed_files)

    if not affected_tests:
        print("\nDepper: No tests affected by these changes")
        if run_all_on_error:
            print("Running all tests (--depper-run-all-on-error enabled).")
            return
        else:
            print("Deselecting all tests. This may indicate missing test coverage.")
            for item in items:
                item.add_marker(pytest.mark.skip(reason="No tests affected by changes"))
            return

    print(f"Depper: {len(affected_tests)} test files affected by changes")

    # Convert test file paths to a set for faster lookup
    affected_test_set = set(affected_tests)

    # Filter items to only include affected tests
    selected = []
    deselected = []

    for item in items:
        # Get the file path for this test item, relative to project root
        test_file = Path(item.fspath).relative_to(project_root)
        test_file_str = str(test_file)

        if test_file_str in affected_test_set:
            selected.append(item)
        else:
            deselected.append(item)

    # Modify the items list in place
    items[:] = selected

    # Mark deselected items
    config.hook.pytest_deselected(items=deselected)

    # Print summary
    print(f"Depper: Selected {len(selected)} tests, deselected {len(deselected)} tests")

    if debug and selected:
        print("\nSelected test files:")
        selected_files = sorted(set(str(Path(item.fspath).relative_to(project_root)) for item in selected))
        for f in selected_files:
            print(f"  ✓ {f}")


def pytest_report_header(config):
    """Add depper information to the pytest header."""
    if config.getoption("--depper"):
        base_branch = config.getoption("--depper-base-branch")
        return [
            f"depper: smart test selection enabled (base branch: {base_branch})",
        ]
