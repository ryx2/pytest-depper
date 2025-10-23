# pytest-depper: Run only the tests you need, not all the tests you have

**Smart test selection based on AST-level code dependency analysis.**

Diffs your current branch vs main, and then gets which tests hit those lines changed, and runs those. 

[![PyPI version](https://badge.fury.io/py/pytest-depper.svg)](https://badge.fury.io/py/pytest-depper)
[![Python Versions](https://img.shields.io/pypi/pyversions/pytest-depper.svg)](https://pypi.org/project/pytest-depper/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/pytest-depper)](https://pepy.tech/project/pytest-depper)
[![Downloads/Month](https://static.pepy.tech/badge/pytest-depper/month)](https://pepy.tech/project/pytest-depper)
[![Framework: pytest](https://img.shields.io/badge/framework-pytest-blue.svg)](https://pytest.org)
[![GitHub Stars](https://img.shields.io/github/stars/ryx2/pytest-depper.svg)](https://github.com/ryx2/pytest-depper/stargazers)

## The Problem

Imagine you have a 3,000-line Python file (you're a typical python dev) with 2,000 individual tests covering various parts of it. You make a small change—just 8 lines. Should you run all 2,000 tests? **No.**

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

pytest-depper uses **function-level change detection** with **static import analysis** to determine which tests need to run.

### Step 1: Detect Changed Functions/Classes

```bash
git diff -U0 origin/main...HEAD
```

Output shows changed line numbers:
```diff
+++ b/src/calculator.py
@@ -5,3 +5,4 @@
 def add(a, b):
+    # Added validation
     return a + b
```

pytest-depper maps changed lines to function/class names using AST:
```
Line 6 changed → Part of function 'add'
Changed symbols: {'add'}
```

### Step 2: Build Symbol Import Map

pytest-depper parses all Python files to track **which specific symbols** each test imports:

```python
# test_math.py
from calculator import add, subtract  # Imports: {'add', 'subtract'}

# test_multiply.py
from calculator import multiply  # Imports: {'multiply'}

# test_integration.py
import calculator  # Imports: {'*'} (entire module)
```

This creates a precise map:
```python
{
  'test_math.py': {'calculator.py': {'add', 'subtract'}},
  'test_multiply.py': {'calculator.py': {'multiply'}},
  'test_integration.py': {'calculator.py': {'*'}}
}
```

### Step 3: Match Changed Symbols to Test Imports

For each changed symbol, pytest-depper finds tests that import it:

```
'add' function changed in calculator.py

test_math.py imports 'add' → RUN ✅
test_multiply.py imports 'multiply' → SKIP ❌
test_integration.py imports '*' → RUN ✅ (imports entire module)
```

**Result:** Only tests that import the changed functions/classes will run.

### Example: 3000-Line File Scenario

```python
# models.py (3000 lines, 50 functions)
def validate_email(email): ...  # Changed (lines 145-150)
def validate_phone(phone): ...
def validate_address(addr): ...
# ... 47 more functions

# test_email.py
from models import validate_email  # Imports: {'validate_email'}

# test_phone.py
from models import validate_phone  # Imports: {'validate_phone'}

# test_integration.py
from models import *  # Imports: {'*'}
```

When only `validate_email` changes:
- ✅ `test_email.py` runs (imports the changed function)
- ✅ `test_integration.py` runs (imports everything with `*`)
- ❌ `test_phone.py` skipped (doesn't import the changed function)
- ❌ 45+ other test files skipped

**This is true function-level precision** - not just file-level dependency tracking.

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

pytest-depper uses **static import analysis**, not runtime coverage. This means it bases decisions on what tests import, not what they actually execute.

### What pytest-depper CAN'T detect:

1. **Imports that aren't used**
   ```python
   # test_multiply.py
   from calculator import add, multiply  # Imports both

   def test_multiply():
       assert multiply(2, 3) == 6  # Only uses multiply
   ```

   If `add` changes, this test will run even though it doesn't use `add`. This is intentional conservatism - better to run too many tests than too few.

2. **Dynamic imports**
   ```python
   module = __import__("my_module")  # Not detected
   importlib.import_module("my_module")  # Not detected
   ```

3. **Module-level imports (`import module`)**
   ```python
   import calculator  # Imports: {'*'} - everything

   def test_add():
       calculator.add(2, 3)  # Uses only add
   ```

   When you do `import calculator`, pytest-depper treats it as importing **everything** from that module. Any change to the module will trigger this test.

   **Recommendation:** Use `from module import specific_function` for better precision.

4. **String-based references**
   ```python
   class_name = "UserModel"
   cls = globals()[class_name]  # Not detected
   ```

5. **Data-driven changes**
   - Changing a JSON config file won't trigger tests that read it
   - Modifying database migrations won't trigger related tests
   - Updating `.env` files won't trigger affected tests

6. **Changes outside functions/classes**
   - Module-level constants
   - Global variables
   - Changes in blank lines or comments only

   These won't be detected as "symbol changes" and will fall back to file-level matching.

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
