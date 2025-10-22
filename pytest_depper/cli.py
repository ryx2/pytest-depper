"""Command-line interface for pytest-depper.

This module provides a standalone CLI for analyzing dependencies
without running tests.
"""

import argparse
import sys
from pathlib import Path

from .analyzer import DependencyAnalyzer
from .git_utils import get_changed_files, get_current_branch


def main():
    """Run dependency analysis from the command line."""
    parser = argparse.ArgumentParser(
        description="Analyze code dependencies and determine which tests to run",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze changes compared to main branch
  pytest-depper

  # Compare to a different branch
  pytest-depper --base-branch develop

  # Show detailed dependency information
  pytest-depper --debug

  # Just list affected test files
  pytest-depper --list-only
        """,
    )

    parser.add_argument(
        "--base-branch",
        default="main",
        help="Base branch to compare against (default: main)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print detailed dependency analysis",
    )

    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only list affected test files, don't print details",
    )

    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Root directory of the project (default: current directory)",
    )

    args = parser.parse_args()

    # Get current branch
    current_branch = get_current_branch(args.project_root)
    print(f"Current branch: {current_branch}")
    print(f"Comparing to: {args.base_branch}")

    # Get changed files
    changed_files = get_changed_files(base_branch=args.base_branch, project_root=args.project_root)

    if not changed_files:
        print("\nNo Python files changed.")
        sys.exit(0)

    print(f"\nFound {len(changed_files)} changed files:")
    for f in changed_files:
        print(f"  - {f}")

    # Analyze dependencies
    print("\nAnalyzing dependencies...")
    analyzer = DependencyAnalyzer(project_root=args.project_root)

    # Print debug info if requested
    if args.debug:
        analyzer.print_dependency_info(changed_files)

    # Get affected tests
    affected_tests = analyzer.get_affected_tests(changed_files)

    if not affected_tests:
        print("\nNo tests are affected by these changes.")
        print("This may indicate missing test coverage.")
        sys.exit(0)

    print(f"\n{'=' * 60}")
    print(f"Found {len(affected_tests)} affected test files:")
    print(f"{'=' * 60}")

    for test in sorted(affected_tests):
        print(f"  ✓ {test}")

    if not args.list_only:
        print(f"\n{'=' * 60}")
        print("To run these tests with pytest:")
        print(f"{'=' * 60}")
        print("\n  pytest --depper")
        print("\nOr run manually:")
        print(f"\n  pytest {' '.join(sorted(affected_tests))}")

    sys.exit(0)


if __name__ == "__main__":
    main()
