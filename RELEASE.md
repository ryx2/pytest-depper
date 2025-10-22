# Release Guide for pytest-depper

This document contains instructions for monitoring the package and releasing new versions.

## 📊 Monitoring

### Download Statistics

Track package downloads at:
- **Primary**: https://pypistats.org/packages/pytest-depper
- **Alternative**: https://pepy.tech/project/pytest-depper

### GitHub Stats

Monitor project health:
- **Repository**: https://github.com/ryx2/pytest-depper
- **Stars**: https://github.com/ryx2/pytest-depper/stargazers
- **Issues**: https://github.com/ryx2/pytest-depper/issues
- **Pull Requests**: https://github.com/ryx2/pytest-depper/pulls

### PyPI Page

Official package page:
- https://pypi.org/project/pytest-depper/

## 🚀 Release Process

### 1. Prepare the Release

```bash
cd ~/pytest-depper

# Ensure you're on main with latest changes
git checkout main
git pull origin main

# Create a release branch
git checkout -b release/v0.2.0
```

### 2. Update Version

Edit `pyproject.toml` and update the version:

```toml
[project]
name = "pytest-depper"
version = "0.2.0"  # Update this line
```

### 3. Update Changelog

Create or update `CHANGELOG.md`:

```markdown
# Changelog

## [0.2.0] - 2025-XX-XX

### Added
- New feature description

### Fixed
- Bug fix description

### Changed
- Breaking change description

## [0.1.0] - 2025-10-22
- Initial release
```

### 4. Commit Version Bump

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"
git push origin release/v0.2.0
```

### 5. Merge to Main

Create and merge a PR, or merge locally:

```bash
git checkout main
git merge release/v0.2.0
git push origin main
```

### 6. Build the Package

```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info

# Build new distributions
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m build
```

### 7. Upload to PyPI

```bash
# Upload to PyPI (uses ~/.pypirc)
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m twine upload dist/*
```

### 8. Create GitHub Release

```bash
# Create a git tag
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0

# Create GitHub release with artifacts
gh release create v0.2.0 \
  dist/pytest_depper-0.2.0-py3-none-any.whl \
  dist/pytest_depper-0.2.0.tar.gz \
  --title "v0.2.0 - Release Title" \
  --notes-file RELEASE_NOTES.md
```

Or create release notes inline:

```bash
gh release create v0.2.0 dist/* \
  --title "v0.2.0 - New Features" \
  --notes "## What's New

### Added
- Feature 1
- Feature 2

### Fixed
- Bug 1
- Bug 2

Full changelog: https://github.com/ryx2/pytest-depper/compare/v0.1.0...v0.2.0"
```

### 9. Verify Release

Check that everything is live:

1. **PyPI**: https://pypi.org/project/pytest-depper/
2. **GitHub**: https://github.com/ryx2/pytest-depper/releases
3. **Install test**:
   ```bash
   pip install --upgrade pytest-depper
   pytest-depper --version
   ```

## 🔧 Hotfix Process

For urgent bug fixes:

```bash
# Create hotfix branch from main
git checkout -b hotfix/v0.1.1 main

# Make fixes
# ...

# Update version to 0.1.1 in pyproject.toml
# Commit and push
git add .
git commit -m "fix: critical bug description"

# Merge to main
git checkout main
git merge hotfix/v0.1.1
git push origin main

# Tag and release
git tag -a v0.1.1 -m "Hotfix v0.1.1"
git push origin v0.1.1

# Build and upload (same as steps 6-7 above)
```

## 📦 Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.2.0): New features, backwards compatible
- **PATCH** (0.1.1): Bug fixes, backwards compatible

## 🔐 Security

### PyPI Token Management

Your PyPI token is stored in `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-YOUR_SCOPED_TOKEN_HERE
```

**Important**:
- Use a **project-scoped token** (not "all projects")
- Token should only have permission for `pytest-depper`
- Rotate tokens periodically
- Never commit `.pypirc` to git

### Creating a New Scoped Token

1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Name: `pytest-depper-releases`
4. Scope: **"Project: pytest-depper"**
5. Copy token and update `~/.pypirc`

## 📝 Pre-Release Checklist

Before every release:

- [ ] All tests pass locally: `pytest`
- [ ] Linting passes: `ruff check pytest_depper`
- [ ] Type checking passes: `mypy pytest_depper`
- [ ] Version updated in `pyproject.toml`
- [ ] CHANGELOG.md updated
- [ ] README.md reflects any new features
- [ ] Example project still works
- [ ] Documentation is up to date

## 🐛 Troubleshooting

### "File already exists" on PyPI Upload

You tried to upload a version that already exists. Bump the version number.

### "Invalid credentials" on Upload

Your PyPI token expired or is invalid. Create a new one.

### Build Fails

```bash
# Clear cache and try again
rm -rf dist/ build/ *.egg-info .eggs/
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m build
```

### GitHub Release Fails

Make sure:
- Git tag exists: `git tag -l`
- You're authenticated: `gh auth status`
- Distribution files exist: `ls dist/`

## 📞 Support

For questions about releases:
- Open an issue: https://github.com/ryx2/pytest-depper/issues
- Discussion forum: https://github.com/ryx2/pytest-depper/discussions

---

Last updated: 2025-10-22
