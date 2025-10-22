# Contributing to pytest-depper

Thank you for your interest in contributing to pytest-depper! This document provides guidelines for contributing to the project.

## Development Setup

1. **Fork and clone the repository**

```bash
git clone https://github.com/ryx2/pytest-depper.git
cd pytest-depper
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install development dependencies**

```bash
pip install -e ".[dev]"
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/test_analyzer.py

# Run with verbose output
pytest -v
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Format code with black
black pytest_depper tests

# Lint with ruff
ruff check pytest_depper tests

# Type checking with mypy
mypy pytest_depper
```

### Running the Plugin Locally

To test the plugin on a real project:

```bash
# Install in editable mode
pip install -e .

# Navigate to a test project
cd /path/to/your/project

# Run pytest with depper
pytest --depper --depper-debug
```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Your Changes

- Write clear, concise code
- Add docstrings to all public functions and classes
- Follow the existing code style
- Add type hints where appropriate

### 3. Add Tests

All new features should include tests:

```python
# tests/test_your_feature.py
def test_your_feature():
    """Test description."""
    # Arrange
    analyzer = DependencyAnalyzer()

    # Act
    result = analyzer.your_feature()

    # Assert
    assert result == expected
```

### 4. Update Documentation

- Update README.md if you're adding new features
- Add docstrings to new functions/classes
- Update examples if relevant

### 5. Run Quality Checks

Before committing, ensure:

```bash
# All tests pass
pytest

# Code is formatted
black pytest_depper tests

# No linting errors
ruff check pytest_depper tests

# Type checking passes
mypy pytest_depper
```

### 6. Commit Your Changes

Use clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add support for custom exclusion patterns"

# or
git commit -m "fix: handle circular imports correctly"

# or
git commit -m "docs: update README with new examples"
```

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

### 7. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:

- Clear title describing the change
- Description of what changed and why
- Reference to any related issues
- Screenshots/examples if relevant

## Code Style Guidelines

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use type hints for function signatures
- Maximum line length: 120 characters
- Use descriptive variable names

Example:

```python
def get_affected_tests(
    self,
    changed_files: list[str]
) -> set[str]:
    """Get all tests affected by the changed files.

    Args:
        changed_files: List of files that have been modified

    Returns:
        Set of test file paths that should be run
    """
    affected_tests = set()
    # Implementation...
    return affected_tests
```

### Documentation Style

- Use Google-style docstrings
- Include type information in docstrings
- Provide examples for public APIs

Example:

```python
def resolve_import(self, module_name: str, from_file: Path) -> set[str]:
    """Resolve an absolute import to file paths.

    Args:
        module_name: The module being imported (e.g., 'package.module')
        from_file: The file doing the importing

    Returns:
        Set of file paths that correspond to this import

    Example:
        >>> analyzer = DependencyAnalyzer()
        >>> paths = analyzer.resolve_import('myapp.models', Path('myapp/views.py'))
        >>> print(paths)
        {'myapp/models.py', 'myapp/models/__init__.py'}
    """
```

## Testing Guidelines

### Test Structure

```python
def test_feature_name():
    """Test that feature does X when Y happens."""
    # Arrange - Set up test data
    analyzer = DependencyAnalyzer(project_root=Path("test_project"))
    changed_files = ["src/models.py"]

    # Act - Execute the feature
    result = analyzer.get_affected_tests(changed_files)

    # Assert - Verify the outcome
    assert "tests/test_models.py" in result
```

### Test Coverage

- Aim for >80% code coverage
- Test both happy paths and edge cases
- Include integration tests for key workflows

### Test Data

Place test fixtures in `tests/fixtures/`:

```
tests/
  fixtures/
    sample_project/
      src/
        models.py
        views.py
      tests/
        test_models.py
```

## Reporting Issues

When reporting bugs, please include:

1. **Description** - What happened vs. what you expected
2. **Reproduction** - Minimal code to reproduce the issue
3. **Environment** - Python version, OS, pytest version
4. **Error messages** - Full traceback if applicable

Example:

```markdown
## Bug: Circular imports cause infinite loop

**Description:**
When two modules import each other, the dependency analyzer enters an infinite loop.

**Reproduction:**
```python
# a.py
from b import foo

# b.py
from a import bar
```

**Environment:**
- Python 3.11
- pytest-depper 0.1.0
- Ubuntu 22.04

**Error:**
```
RecursionError: maximum recursion depth exceeded
```
```

## Feature Requests

We welcome feature requests! Please:

1. Search existing issues first
2. Describe the use case
3. Explain why it would be useful
4. Provide examples if possible

## Questions?

- Open a [GitHub Discussion](https://github.com/ryx2/pytest-depper/discussions)
- Check the [README](README.md) for documentation
- Look at existing [issues](https://github.com/ryx2/pytest-depper/issues)

## License

By contributing to pytest-depper, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to pytest-depper! 🎉
