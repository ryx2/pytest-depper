# pytest-depper

**Smart test selection based on AST-level code dependency analysis.**

Run only the tests you need, not all the tests you have.

[![PyPI version](https://badge.fury.io/py/pytest-depper.svg)](https://badge.fury.io/py/pytest-depper)
[![Python Versions](https://img.shields.io/pypi/pyversions/pytest-depper.svg)](https://pypi.org/project/pytest-depper/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## The Problem

Imagine you have a 3,000-line Python file with 2,000 individual tests covering various parts of it. You make a small change—just 8 lines. Should you run all 2,000 tests? **No.**

Most test selection tools either:
- Run everything (slow)
- Use coverage data from previous runs (requires pre-computed data, breaks with new code)
- Rely on naming conventions (fragile, incomplete)

## The Solution

**pytest-depper** analyzes your code's **actual import dependencies** at the AST level to determine exactly which tests are affected by your changes.

When you change those 8 lines, pytest-depper:
1. Diffs your branch against main to find changed files
2. Builds a complete dependency graph of your codebase using AST parsing
3. Traces which tests import (directly or transitively) the changed code
4. Runs only those ~20 affected tests instead of all 2,000

**No pre-computation. No cached state. No guessing.**

## Key Advantages Over Similar Tools

### vs pytest-testmon

| Feature | pytest-depper | pytest-testmon |
|---------|--------------|----------------|
| Requires previous run data | ❌ No | ✅ Yes (.testmon file) |
| Works on fresh branches | ✅ Yes | ❌ No (needs to build cache first) |
| AST-level analysis | ✅ Yes | ✅ Yes |
| Git integration | ✅ Built-in | ❌ Manual |
| Dependency graph visualization | ✅ Yes (`--depper-debug`) | ⚠️ Limited |

**Why this matters:** pytest-testmon requires running your full test suite at least once on the main branch to build its cache. If you check out a fresh branch or clone a new repo, you have no cache. pytest-depper works immediately by analyzing your code structure.

### vs pytest-picked

pytest-picked only looks at changed test files and changed source files—it doesn't analyze the dependency graph. If you change `models/user.py`, and `services/auth.py` imports it, and `tests/test_api.py` tests the auth service, pytest-picked won't detect this transitive relationship.

### vs Manual Test Selection

Running tests manually is error-prone. You might:
- Forget which tests cover which code
- Miss transitive dependencies (A imports B, B imports C, you changed C)
- Over-select tests out of caution (wasting time)

## Installation

```bash
pip install pytest-depper
```

Or with poetry:

```bash
poetry add --group dev pytest-depper
```

## Quick Start

### As a Pytest Plugin

Simply add the `--depper` flag to your pytest command:

```bash
# Run only tests affected by changes compared to main branch
pytest --depper

# Compare against a different branch
pytest --depper --depper-base-branch=develop

# Show detailed dependency analysis
pytest --depper --depper-debug
```

### As a Standalone CLI

Analyze dependencies without running tests:

```bash
# Show which tests would run
pytest-depper

# Compare to a different branch
pytest-depper --base-branch develop

# Show detailed dependency information
pytest-depper --debug
```

## How It Works

### Step 1: Find Changed Files

```bash
git diff --name-only origin/main...HEAD
```

Output:
```
src/models/user.py
src/utils/validators.py
```

### Step 2: Build Dependency Graph

pytest-depper parses all Python files in your project using AST analysis to understand imports:

```python
# src/models/user.py
from .base import BaseModel  # → src/models/base.py
from ..utils.validators import validate_email  # → src/utils/validators.py

# src/services/auth.py
from ..models.user import User  # → src/models/user.py

# tests/test_auth.py
from src.services.auth import AuthService  # → src/services/auth.py
```

This creates both forward and reverse dependency graphs:
- **Forward:** What does each file import?
- **Reverse:** What imports each file?

### Step 3: Trace Affected Tests

For each changed file, pytest-depper:
1. Finds all files that import it (directly or transitively)
2. Filters to only test files
3. Returns the minimal set of tests that must run

```
user.py changed
  ↓ imported by services/auth.py
    ↓ imported by tests/test_auth.py
      ✅ Run tests/test_auth.py

validators.py changed
  ↓ imported by models/user.py
    ↓ imported by services/auth.py
      ↓ imported by tests/test_auth.py
        ✅ Run tests/test_auth.py
  ↓ also imported by tests/test_validators.py
    ✅ Run tests/test_validators.py
```

**Result:** Only 2 test files run instead of your entire suite.

## Configuration

### Pytest Plugin Options

```bash
--depper
    Enable smart test selection (default: False)

--depper-base-branch=BRANCH
    Base branch to compare against (default: main)

--depper-debug
    Print detailed dependency analysis (default: False)

--depper-run-all-on-error
    Run all tests if no changed files detected or analysis fails (default: False)
```

### Programmatic Usage

```python
from pathlib import Path
from pytest_depper import DependencyAnalyzer

# Initialize analyzer
analyzer = DependencyAnalyzer(
    project_root=Path("."),
    exclusion_patterns=["venv", ".venv", "build"],
    test_patterns=["test_", "_test.py", "/tests/"]
)

# Get changed files (you provide this)
changed_files = ["src/models/user.py", "src/utils/validators.py"]

# Get affected tests
affected_tests = analyzer.get_affected_tests(changed_files)
print(f"Run these tests: {affected_tests}")

# Debug: Print dependency info
analyzer.print_dependency_info(changed_files)
```

## Real-World Example

### Before pytest-depper

```bash
$ pytest
======================== test session starts ========================
collected 2847 items

tests/test_auth.py::test_login PASSED                          [ 0%]
tests/test_auth.py::test_logout PASSED                         [ 0%]
tests/test_auth.py::test_register PASSED                       [ 0%]
... (2844 more tests) ...

===================== 2847 passed in 284.32s =======================
```

⏱️ **4 minutes 44 seconds**

### After pytest-depper

```bash
$ pytest --depper

Depper: Found 2 changed files
  - src/models/user.py
  - src/utils/validators.py

Depper: 2 test files affected by changes
Depper: Selected 23 tests, deselected 2824 tests

======================== test session starts ========================
collected 23 items

tests/test_auth.py::test_login PASSED                          [ 4%]
tests/test_auth.py::test_logout PASSED                         [ 8%]
tests/test_auth.py::test_register PASSED                       [12%]
tests/test_validators.py::test_email_validation PASSED         [16%]
... (19 more tests) ...

===================== 23 passed in 3.71s =======================
```

⏱️ **3.71 seconds**

**76x faster** for a typical small change.

## CI/CD Integration

### GitHub Actions

```yaml
name: Tests

on:
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Need full history for git diff

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest-depper

      - name: Run affected tests
        run: pytest --depper --depper-run-all-on-error
```

### GitLab CI

```yaml
test:
  script:
    - pip install -r requirements.txt
    - pip install pytest-depper
    - pytest --depper --depper-base-branch=$CI_MERGE_REQUEST_TARGET_BRANCH_NAME
```

## Advanced Usage

### Custom Test Patterns

```python
analyzer = DependencyAnalyzer(
    test_patterns=[
        "test_",           # files starting with test_
        "_test.py",        # files ending with _test.py
        "/tests/",         # files in tests/ directories
        "/integration/",   # custom: integration test directory
        "spec.py",         # custom: spec files
    ]
)
```

### Custom Exclusion Patterns

```python
analyzer = DependencyAnalyzer(
    exclusion_patterns=[
        "venv",
        ".venv",
        "node_modules",
        "build",
        "dist",
        ".git",
        "__pycache__",
        "migrations",  # custom: ignore migration files
        "scripts",     # custom: ignore utility scripts
    ]
)
```

### Debug Output

```bash
$ pytest --depper --depper-debug

=== Dependency Analysis ===

Changed file: src/models/user.py
  Dependencies: {'src/models/base.py', 'src/utils/validators.py'}
  Files that depend on this: {'src/services/auth.py', 'src/services/user_service.py', 'tests/test_auth.py', 'tests/test_user.py'}
  Direct test coverage: {'tests/test_user.py'}

Changed file: src/utils/validators.py
  Dependencies: set()
  Files that depend on this: {'src/models/user.py', 'tests/test_validators.py'}
  Direct test coverage: {'tests/test_validators.py'}

Depper: Selected 4 test files
  ✓ tests/test_auth.py
  ✓ tests/test_user.py
  ✓ tests/test_user_service.py
  ✓ tests/test_validators.py
```

## Limitations

### What pytest-depper CAN'T detect:

1. **Dynamic imports**
   ```python
   module = __import__("my_module")  # Not detected
   importlib.import_module("my_module")  # Not detected
   ```

2. **String-based references**
   ```python
   class_name = "UserModel"
   cls = globals()[class_name]  # Not detected
   ```

3. **Data-driven changes**
   - Changing a JSON config file won't trigger tests that read it
   - Modifying database migrations won't trigger related tests
   - Updating `.env` files won't trigger affected tests

4. **Indirect behavioral dependencies**
   - If you change a function's behavior but not its signature, tests that depend on that behavior will run only if they import the function

### Recommended approach:

- Use `--depper-run-all-on-error` in CI to be safe
- Run full test suite on main/develop branches
- Use pytest-depper for PR/feature branches to speed up development
- Combine with coverage tools to ensure you have adequate test coverage

## FAQ

**Q: Does this replace pytest-cov or coverage.py?**

A: No. pytest-depper selects which tests to run. Coverage tools measure how much of your code is tested. Use them together.

**Q: What if I rename a file?**

A: Git treats renames as delete + add. pytest-depper will see the new file as changed and run all tests that import it.

**Q: Does it work with monorepos?**

A: Yes. Set `project_root` to your package directory:

```python
analyzer = DependencyAnalyzer(project_root=Path("packages/my-package"))
```

**Q: What Python versions are supported?**

A: Python 3.8+. The AST analysis uses `sys.stdlib_module_names` (Python 3.10+) but falls back gracefully.

**Q: Can I use this with tox or nox?**

A: Yes:

```ini
# tox.ini
[testenv]
deps = pytest-depper
commands = pytest --depper
```

**Q: Why "depper"?**

A: **Dep**endency-based test runner, or "deeper" analysis. Plus it's short and memorable.

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repo
git clone https://github.com/ryx2/pytest-depper.git
cd pytest-depper

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linters
ruff check .
mypy pytest_depper
```

## License

MIT License. See [LICENSE](LICENSE) for details.

## Credits

Inspired by:
- [pytest-testmon](https://github.com/tarpas/pytest-testmon) - for the concept of dependency-based test selection
- [pytest-picked](https://github.com/anapaulagomes/pytest-picked) - for git integration with pytest

Built with ❤️ for developers who value their time.

---

**Star this repo** if pytest-depper saves you time!

**Report issues** at https://github.com/ryx2/pytest-depper/issues
