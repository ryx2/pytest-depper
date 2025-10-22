# Sample Project

This is a sample project to demonstrate **pytest-depper** in action.

## Project Structure

```
sample_project/
├── src/
│   ├── __init__.py
│   ├── models.py       # User and Admin models
│   ├── validators.py   # Email and username validation
│   └── auth.py         # Authentication service
└── tests/
    ├── __init__.py
    ├── test_models.py      # Tests for models (4 tests)
    ├── test_validators.py  # Tests for validators (7 tests)
    └── test_auth.py        # Tests for auth service (6 tests)
```

Total: **17 tests**

## Dependency Graph

```
auth.py
  ├─ imports models.py (User, Admin)
  │   └─ imports validators.py (validate_email)
  └─ tested by test_auth.py (6 tests)

models.py
  ├─ imports validators.py (validate_email)
  └─ tested by test_models.py (4 tests)
       and test_auth.py (6 tests indirectly)

validators.py
  └─ tested by test_validators.py (7 tests)
       and test_models.py (4 tests indirectly)
       and test_auth.py (6 tests indirectly)
```

## Demonstrating pytest-depper

### Scenario 1: Change validators.py

If you modify `src/validators.py`:

```bash
# Without pytest-depper: runs all 17 tests
pytest

# With pytest-depper: runs only affected tests
pytest --depper
```

**Expected affected tests:**
- `test_validators.py` (7 tests) - directly imports validators
- `test_models.py` (4 tests) - models imports validators
- `test_auth.py` (6 tests) - auth imports models, which imports validators

**Result: 17/17 tests** (all tests are affected because validators is used everywhere)

### Scenario 2: Change models.py

If you modify `src/models.py`:

```bash
pytest --depper
```

**Expected affected tests:**
- `test_models.py` (4 tests) - directly tests models
- `test_auth.py` (6 tests) - auth service imports models

**Result: 10/17 tests** (~41% reduction)

### Scenario 3: Change auth.py

If you modify `src/auth.py`:

```bash
pytest --depper
```

**Expected affected tests:**
- `test_auth.py` (6 tests) - directly tests auth

**Result: 6/17 tests** (~65% reduction)

### Scenario 4: Add a new function to validators.py

If you add a new function `validate_password()` to `validators.py` that isn't used anywhere:

```python
# src/validators.py
def validate_password(password: str) -> str:
    """Validate a password."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    return password
```

**Expected affected tests:**
- `test_validators.py` (7 tests) - if you add a test for it
- Or potentially none - if no code imports it yet

This demonstrates the **precision** of pytest-depper's dependency analysis.

## Running the Demo

1. **Install pytest-depper**:
   ```bash
   cd ../..  # Back to repo root
   pip install -e .
   ```

2. **Run all tests normally**:
   ```bash
   cd examples/sample_project
   pytest -v
   ```

   Output:
   ```
   ======================== 17 passed in 0.03s =========================
   ```

3. **Make a change** (e.g., modify `src/validators.py`):
   ```bash
   # Add a comment or change a docstring
   echo "# Updated validators" >> src/validators.py
   git add src/validators.py
   ```

4. **Run with pytest-depper**:
   ```bash
   pytest --depper --depper-debug
   ```

   Output will show:
   - Which files changed
   - Dependency graph analysis
   - Which tests are affected
   - How many tests were deselected

## Comparing with pytest-testmon

To compare with pytest-testmon:

```bash
# Install testmon
pip install pytest-testmon

# First run (builds cache)
pytest --testmon

# Make a change
echo "# Updated" >> src/auth.py

# Second run (uses cache)
pytest --testmon

# vs pytest-depper (no cache needed)
pytest --depper
```

pytest-depper works immediately without needing a cache build step.
