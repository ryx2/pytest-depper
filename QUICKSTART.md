# Quick Start Guide

Get started with pytest-depper in 5 minutes!

## Installation

```bash
cd pytest-depper
pip install -e .
```

## Try the Example Project

### 1. Run all tests normally

```bash
cd examples/sample_project
pytest -v
```

You should see 17 tests pass:

```
tests/test_auth.py::test_register_user PASSED
tests/test_auth.py::test_register_duplicate_user PASSED
... (15 more tests)
===================== 17 passed in 0.05s =======================
```

### 2. Use pytest-depper to analyze dependencies

```bash
# Analyze what tests would run (without actually running them)
pytest-depper --list-only
```

Since we're on the main branch with no changes, it will say "No Python files changed."

### 3. Make a change and see pytest-depper in action

```bash
# Make a small change to auth.py
echo "# Updated auth service" >> src/auth.py

# See which tests are affected
pytest-depper --debug
```

You'll see:

```
=== Dependency Analysis ===

Changed file: src/auth.py
  Dependencies: {'src/models.py'}
  Files that depend on this: {'tests/test_auth.py'}
  Direct test coverage: {'tests/test_auth.py'}

Found 1 affected test files:
  ✓ tests/test_auth.py
```

### 4. Run only the affected tests

```bash
pytest --depper -v
```

Output:

```
Depper: Found 1 changed files
  - src/auth.py

Depper: 1 test files affected by changes
Depper: Selected 6 tests, deselected 11 tests

tests/test_auth.py::test_register_user PASSED
tests/test_auth.py::test_register_duplicate_user PASSED
tests/test_auth.py::test_register_admin PASSED
tests/test_auth.py::test_get_user_exists PASSED
tests/test_auth.py::test_get_user_not_exists PASSED
tests/test_auth.py::test_get_admin PASSED

===================== 6 passed in 0.02s =======================
```

**Result:** Only 6/17 tests ran (65% reduction) 🎉

### 5. Compare with running all tests

```bash
# Revert the change
git checkout src/auth.py

# Now change a widely-used file
echo "# Updated validators" >> src/validators.py

# See what's affected
pytest-depper
```

You'll see all 17 tests are affected because validators.py is imported by everything.

```
Found 3 affected test files:
  ✓ tests/test_auth.py
  ✓ tests/test_models.py
  ✓ tests/test_validators.py
```

This demonstrates the **precision** of dependency analysis!

## Use in Your Own Project

### Quick Test

```bash
# Navigate to your project
cd ~/your-project

# Run pytest-depper analysis
pytest-depper --debug
```

### Run with Pytest

```bash
# Run only affected tests
pytest --depper

# Compare to a different branch
pytest --depper --depper-base-branch=develop

# Run all tests if no changes detected (safe mode for CI)
pytest --depper --depper-run-all-on-error
```

## Integration with CI/CD

Add to your `.github/workflows/test.yml`:

```yaml
- name: Run affected tests
  run: |
    pip install pytest-depper
    pytest --depper --depper-run-all-on-error
```

## Configuration Options

### Customize Test Patterns

Create a `conftest.py` in your project:

```python
from pytest_depper import DependencyAnalyzer

def pytest_configure(config):
    # Customize how tests are detected
    DependencyAnalyzer.test_patterns = [
        "test_",
        "_test.py",
        "/tests/",
        "/specs/",  # Custom pattern
    ]
```

### Customize Exclusions

```python
def pytest_configure(config):
    # Customize what directories to skip
    DependencyAnalyzer.exclusion_patterns = [
        "venv",
        ".venv",
        "node_modules",
        "migrations",  # Custom exclusion
    ]
```

## Common Scenarios

### Scenario 1: Feature Branch Development

```bash
# Create a feature branch
git checkout -b feature/new-endpoint

# Make your changes
vim src/api/endpoints.py

# Run only affected tests during development
pytest --depper
```

**Benefit:** Fast feedback loop during development

### Scenario 2: Pull Request Review

```bash
# Check out a PR
git fetch origin pull/123/head:pr-123
git checkout pr-123

# See what tests should run
pytest-depper --list-only

# Run the tests
pytest --depper
```

**Benefit:** Faster PR verification

### Scenario 3: Large Refactoring

```bash
# After a large refactor
git diff --name-only origin/main | head

# Check affected tests
pytest-depper --debug

# Run them with detailed output
pytest --depper -vv
```

**Benefit:** Confidence that refactoring is safe

## Comparison with Other Tools

| Tool | pytest-depper | pytest-testmon | pytest-picked |
|------|---------------|----------------|---------------|
| Setup required | None | Cache build | None |
| Fresh clones work | ✅ Yes | ❌ No | ✅ Yes |
| Transitive deps | ✅ Yes | ✅ Yes | ❌ No |
| Git integration | ✅ Built-in | ⚠️ Manual | ✅ Built-in |

## Troubleshooting

### "No changed files detected"

- Make sure you're on a branch, not main
- Check that your changes are committed: `git diff --name-only origin/main`
- Use `--depper-run-all-on-error` to run all tests as fallback

### "No tests affected"

- This might indicate missing test coverage
- Check with `pytest-depper --debug` to see the dependency analysis
- Verify that your tests import the code they're testing

### Tests are being skipped unexpectedly

- Use `--depper-debug` to see detailed dependency info
- Check that imports are at the top level (not inside functions)
- Verify test file naming matches patterns (default: `test_*.py` or `*_test.py`)

## Next Steps

- Read the [full README](README.md) for detailed documentation
- Check out [CONTRIBUTING.md](CONTRIBUTING.md) to contribute
- Report issues at https://github.com/yourusername/pytest-depper/issues

---

Happy testing! 🚀
