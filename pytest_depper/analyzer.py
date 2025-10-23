"""Core dependency analysis engine for pytest-depper.

This module analyzes Python code at the AST level to build a complete dependency graph,
allowing precise determination of which tests are affected by code changes.
"""

import ast
import sys
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass
else:
    try:
        from importlib import metadata
    except ImportError:
        try:
            import importlib_metadata as metadata  # type: ignore
        except ImportError:
            metadata = None  # type: ignore


class DependencyAnalyzer:
    """Analyzes Python code dependencies to determine which tests need to run.

    Unlike tools that rely on coverage data from previous runs, this analyzer:
    - Dynamically builds a complete dependency graph from source code
    - Uses AST parsing to understand imports and dependencies
    - Works on both the current branch and comparison branch (e.g., main)
    - Requires no cached state or previous test runs

    This enables precise test selection: if you modify 8 lines in a 3000-line file
    with 2000 tests, only the ~20 tests that depend on those specific lines will run.
    """

    def __init__(
        self,
        project_root: Path = Path("."),
        exclusion_patterns: list[str] | None = None,
        test_patterns: list[str] | None = None,
    ) -> None:
        """Initialize the dependency analyzer.

        Args:
            project_root: Root directory of the project to analyze
            exclusion_patterns: Glob patterns for directories to skip (e.g., 'venv', '.git')
            test_patterns: Patterns to identify test files (e.g., 'test_', '_test.py')
        """
        self.project_root = project_root
        self.dependency_graph: dict[str, set[str]] = defaultdict(set)
        self.reverse_graph: dict[str, set[str]] = defaultdict(set)
        self.module_to_tests: dict[str, set[str]] = defaultdict(set)
        self._python_files: set[str] = set()

        # New: Track which specific symbols are imported
        # Maps: test_file -> source_file -> set of imported symbols
        # Example: {'test_add.py': {'calculator.py': {'add', 'subtract'}}}
        self.symbol_imports: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))

        # Configurable exclusion patterns
        self.exclusion_patterns = exclusion_patterns or [
            "venv",
            ".venv",
            "build",
            "dist",
            ".git",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "node_modules",
            ".tox",
        ]

        # Configurable test patterns
        self.test_patterns = test_patterns or ["test_", "_test.py", "/tests/", "/test/"]

        # Cache installed package names for performance
        self._installed_packages: set[str] = self._get_installed_packages()

        # Build the complete dependency graph
        self._scan_project()
        self._build_dependency_graph()
        self._map_tests_to_modules()

    def _get_installed_packages(self) -> set[str]:
        """Get a set of all installed package names using importlib.metadata."""
        try:
            if metadata is None:  # type: ignore
                return set()
            # Get all installed distributions and extract their names
            return {dist.metadata["Name"].lower() for dist in metadata.distributions()}  # type: ignore
        except Exception:
            # Fallback to empty set if metadata access fails
            return set()

    def _scan_project(self) -> None:
        """Scan project for all Python files."""
        for py_file in self.project_root.rglob("*.py"):
            # Skip excluded directories
            if any(skip in str(py_file) for skip in self.exclusion_patterns):
                continue
            self._python_files.add(str(py_file.relative_to(self.project_root)))

    def _build_dependency_graph(self) -> None:
        """Build complete forward and reverse dependency graphs."""
        for py_file in self._python_files:
            dependencies, symbols = self._extract_dependencies_and_symbols(Path(py_file))
            self.dependency_graph[py_file] = dependencies

            # Store symbol imports
            for source_file, imported_symbols in symbols.items():
                self.symbol_imports[py_file][source_file] = imported_symbols

            # Build reverse graph (who depends on this file)
            for dep in dependencies:
                self.reverse_graph[dep].add(py_file)

    def _extract_dependencies(self, file_path: Path) -> set[str]:
        """Extract all dependencies from a Python file using AST parsing.

        Args:
            file_path: Path to the Python file to analyze

        Returns:
            Set of file paths that this file depends on
        """
        dependencies, _ = self._extract_dependencies_and_symbols(file_path)
        return dependencies

    def _extract_dependencies_and_symbols(self, file_path: Path) -> tuple[set[str], dict[str, set[str]]]:
        """Extract dependencies and imported symbols from a Python file.

        Args:
            file_path: Path to the Python file to analyze

        Returns:
            Tuple of (set of file dependencies, dict mapping source files to imported symbols)
        """
        dependencies = set()
        symbol_imports: dict[str, set[str]] = defaultdict(set)

        try:
            full_path = self.project_root / file_path
            with open(full_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    # import module
                    for alias in node.names:
                        deps = self._resolve_import(alias.name, file_path)
                        dependencies.update(deps)
                        # Track that we import the entire module (use '*' to indicate whole module)
                        for dep in deps:
                            symbol_imports[dep].add('*')

                elif isinstance(node, ast.ImportFrom):
                    # from module import symbol1, symbol2
                    if node.module:
                        if node.level > 0:  # Relative import
                            deps = self._resolve_relative_import(node.module, node.level, file_path)
                        else:  # Absolute import
                            deps = self._resolve_import(node.module, file_path)
                        dependencies.update(deps)

                        # Track which specific symbols are imported
                        for dep in deps:
                            for alias in node.names:
                                if alias.name == '*':
                                    # from module import * - imports everything
                                    symbol_imports[dep].add('*')
                                else:
                                    # from module import specific_function
                                    symbol_imports[dep].add(alias.name)

                    elif node.level > 0:  # from . import something
                        deps = self._resolve_relative_import("", node.level, file_path)
                        dependencies.update(deps)
                        for dep in deps:
                            for alias in node.names:
                                if alias.name == '*':
                                    symbol_imports[dep].add('*')
                                else:
                                    symbol_imports[dep].add(alias.name)

        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")

        return dependencies, symbol_imports

    def _resolve_import(self, module_name: str, from_file: Path) -> set[str]:
        """Resolve an absolute import to file paths.

        Args:
            module_name: The module being imported (e.g., 'package.module')
            from_file: The file doing the importing

        Returns:
            Set of file paths that correspond to this import
        """
        resolved = set()
        parts = module_name.split(".")

        # Check if it's a standard library or third-party module
        if self._is_external_module(parts[0]):
            return resolved

        # Try different combinations
        for i in range(len(parts), 0, -1):
            module_parts = parts[:i]

            # Try as a module file
            module_path = "/".join(module_parts) + ".py"
            if module_path in self._python_files:
                resolved.add(module_path)

            # Try as a package
            init_path = "/".join(module_parts) + "/__init__.py"
            if init_path in self._python_files:
                resolved.add(init_path)

                # If we're importing from a package, include all specified submodules
                if i < len(parts):
                    submodule_path = "/".join(parts[: i + 1]) + ".py"
                    if submodule_path in self._python_files:
                        resolved.add(submodule_path)

        return resolved

    def _resolve_relative_import(self, module_name: str, level: int, from_file: Path) -> set[str]:
        """Resolve relative imports (e.g., 'from .. import foo').

        Args:
            module_name: The module name (empty for 'from . import')
            level: Number of dots in the import (1 for '.', 2 for '..', etc.)
            from_file: The file doing the importing

        Returns:
            Set of file paths that correspond to this import
        """
        resolved = set()

        # Get the package containing from_file
        current_path = from_file.parent

        # Go up 'level' directories
        for _ in range(level - 1):
            current_path = current_path.parent

        if module_name:
            # from ..module import something
            target_path = current_path / module_name.replace(".", "/")

            # Check for module.py
            module_file = str(target_path) + ".py"
            if module_file in self._python_files:
                resolved.add(module_file)

            # Check for module/__init__.py
            init_file = str(target_path / "__init__.py")
            if init_file in self._python_files:
                resolved.add(init_file)
        else:
            # from .. import something
            init_file = str(current_path / "__init__.py")
            if init_file in self._python_files:
                resolved.add(init_file)

        return resolved

    def _is_external_module(self, module_name: str) -> bool:
        """Check if a module is external (stdlib or third-party).

        Args:
            module_name: The top-level module name

        Returns:
            True if the module is external (not part of the project)
        """
        # Use sys.stdlib_module_names to check for standard library modules (Python 3.10+)
        if hasattr(sys, "stdlib_module_names") and module_name in sys.stdlib_module_names:
            return True

        # Check if it's an installed third-party package
        if module_name.lower() in self._installed_packages:
            return True

        # Check if it's a file in our project
        if any(f.startswith(module_name) for f in self._python_files):
            return False

        # Assume it's external if not found in project
        return True

    def _map_tests_to_modules(self) -> None:
        """Map test files to the modules they test.

        This builds a reverse index from source modules to test files,
        enabling quick lookup of which tests cover which code.
        """
        test_files = [f for f in self._python_files if self._is_test_file(f)]

        for test_file in test_files:
            # Get all dependencies of this test file (recursively)
            all_deps = self._get_all_dependencies(test_file)

            for dep in all_deps:
                if not self._is_test_file(dep):
                    self.module_to_tests[dep].add(test_file)

    def _is_test_file(self, file_path: str) -> bool:
        """Check if a file is a test file based on configured patterns.

        Args:
            file_path: Path to check

        Returns:
            True if the file matches any test pattern
        """
        return any(pattern in file_path for pattern in self.test_patterns)

    def _get_all_dependencies(self, file_path: str, visited: set[str] | None = None) -> set[str]:
        """Recursively get all dependencies of a file.

        Args:
            file_path: File to analyze
            visited: Set of already-visited files (for cycle detection)

        Returns:
            Set of all files that this file depends on (transitively)
        """
        if visited is None:
            visited = set()

        if file_path in visited:
            return set()

        visited.add(file_path)
        all_deps = set()

        # Get direct dependencies
        direct_deps = self.dependency_graph.get(file_path, set())
        all_deps.update(direct_deps)

        # Recursively get dependencies of dependencies
        for dep in direct_deps:
            all_deps.update(self._get_all_dependencies(dep, visited))

        return all_deps

    def _get_all_dependents(self, file_path: str, visited: set[str] | None = None) -> set[str]:
        """Recursively get all files that depend on this file.

        Args:
            file_path: File to analyze
            visited: Set of already-visited files (for cycle detection)

        Returns:
            Set of all files that depend on this file (transitively)
        """
        if visited is None:
            visited = set()

        if file_path in visited:
            return set()

        visited.add(file_path)
        all_dependents = set()

        # Get direct dependents
        direct_dependents = self.reverse_graph.get(file_path, set())
        all_dependents.update(direct_dependents)

        # Recursively get dependents of dependents
        for dep in direct_dependents:
            all_dependents.update(self._get_all_dependents(dep, visited))

        return all_dependents

    def get_affected_tests(self, changed_files: list[str]) -> set[str]:
        """Get all tests affected by the changed files.

        This is the main API for determining which tests need to run.

        Args:
            changed_files: List of files that have been modified

        Returns:
            Set of test file paths that should be run

        Example:
            >>> analyzer = DependencyAnalyzer()
            >>> changed = ["src/models/user.py"]
            >>> tests = analyzer.get_affected_tests(changed)
            >>> print(tests)
            {'tests/test_user.py', 'tests/test_auth.py'}
        """
        affected_tests = set()

        for changed_file in changed_files:
            # If it's a test file itself, include it
            if self._is_test_file(changed_file):
                affected_tests.add(changed_file)

            # Get all files that depend on this changed file (transitively)
            all_dependents = self._get_all_dependents(changed_file)

            # Filter for test files
            test_dependents = {f for f in all_dependents if self._is_test_file(f)}
            affected_tests.update(test_dependents)

            # Also check module_to_tests mapping
            if changed_file in self.module_to_tests:
                affected_tests.update(self.module_to_tests[changed_file])

        return affected_tests

    def get_affected_tests_by_symbols(self, changed_symbols: dict[str, set[str]]) -> set[str]:
        """Get tests affected by specific symbol changes (function/class level).

        This is more precise than file-level analysis. Only tests that import
        the changed symbols will be selected.

        Args:
            changed_symbols: Dict mapping file paths to sets of changed symbol names

        Returns:
            Set of test file paths that import the changed symbols

        Example:
            >>> analyzer = DependencyAnalyzer()
            >>> changed = {"calculator.py": {"add", "subtract"}}
            >>> tests = analyzer.get_affected_tests_by_symbols(changed)
            >>> print(tests)
            {'test_math.py'}  # Only if test_math imports 'add' or 'subtract'
        """
        affected_tests = set()

        for changed_file, changed_symbol_names in changed_symbols.items():
            # Find all test files that import from this file
            for test_file in self._python_files:
                if not self._is_test_file(test_file):
                    continue

                # Check if this test imports from the changed file
                if changed_file in self.symbol_imports[test_file]:
                    imported_symbols = self.symbol_imports[test_file][changed_file]

                    # Check if test imports any of the changed symbols
                    if '*' in imported_symbols:
                        # Test imports everything from this file
                        affected_tests.add(test_file)
                    elif imported_symbols & changed_symbol_names:
                        # Test imports at least one changed symbol
                        affected_tests.add(test_file)

        return affected_tests

    def print_dependency_info(self, changed_files: list[str]) -> None:
        """Print detailed dependency information for debugging.

        Args:
            changed_files: Files to analyze and print information about
        """
        print("\n=== Dependency Analysis ===")
        for changed_file in changed_files:
            print(f"\nChanged file: {changed_file}")

            # Show what this file depends on
            deps = self.dependency_graph.get(changed_file, set())
            if deps:
                print(f"  Dependencies: {deps}")

            # Show what depends on this file
            dependents = self._get_all_dependents(changed_file)
            if dependents:
                print(f"  Files that depend on this: {dependents}")

            # Show affected tests
            tests = self.module_to_tests.get(changed_file, set())
            if tests:
                print(f"  Direct test coverage: {tests}")

    def print_symbol_dependency_info(self, changed_symbols: dict[str, set[str]]) -> None:
        """Print detailed symbol-level dependency information for debugging.

        Args:
            changed_symbols: Dict mapping files to changed symbol names
        """
        print("\n=== Symbol-Level Dependency Analysis ===")
        for changed_file, symbols in changed_symbols.items():
            print(f"\nChanged file: {changed_file}")
            print(f"  Changed symbols: {symbols}")

            # Find tests that import these symbols
            affected_tests = []
            for test_file in self._python_files:
                if not self._is_test_file(test_file):
                    continue

                if changed_file in self.symbol_imports[test_file]:
                    imported_symbols = self.symbol_imports[test_file][changed_file]
                    if '*' in imported_symbols:
                        affected_tests.append(f"{test_file} (imports all)")
                    elif imported_symbols & symbols:
                        matching = imported_symbols & symbols
                        affected_tests.append(f"{test_file} (imports {matching})")

            if affected_tests:
                print(f"  Tests affected:")
                for test in affected_tests:
                    print(f"    ✓ {test}")
