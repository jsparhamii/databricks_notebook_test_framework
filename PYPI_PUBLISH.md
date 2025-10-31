# Publishing to PyPI

This guide explains how to publish the `databricks-notebook-test-framework` package to PyPI.

## Prerequisites

### 1. Update Project Metadata

Before publishing, update the following in `pyproject.toml`:

```toml
[project]
name = "databricks-notebook-test-framework"
version = "0.1.0"  # Update this for each release
authors = [
    {name = "Your Name", email = "your.email@example.com"}  # Update with your info
]

[project.urls]
Homepage = "https://github.com/yourusername/databricks-notebook-test-framework"  # Update with your repo
Documentation = "https://github.com/yourusername/databricks-notebook-test-framework/docs"
Repository = "https://github.com/yourusername/databricks-notebook-test-framework"
```

### 2. Install Required Tools

```bash
pip install --upgrade build twine
```

### 3. Create PyPI Account

1. Create an account at https://pypi.org/account/register/
2. Verify your email address
3. Enable 2FA (recommended)
4. Generate an API token at https://pypi.org/manage/account/token/

## Publishing Steps

### Step 1: Clean Previous Builds

```bash
rm -rf dist/ build/ src/*.egg-info
```

### Step 2: Update Version Number

Edit `pyproject.toml` and increment the version:

```toml
version = "0.1.0"  # Change to "0.1.1", "0.2.0", etc.
```

### Step 3: Update CHANGELOG

Document your changes in `CHANGELOG.md`:

```markdown
## [0.1.0] - 2025-10-30

### Added
- Pytest-style automatic test discovery
- Workspace test execution
- Multiple output formats (JUnit, JSON, HTML)
- Automatic wheel upload and installation
- Cluster configuration options
- CLI profile support

### Changed
- Removed Nutter dependency
- Simplified authentication

### Fixed
- Output format support for workspace tests
```

### Step 4: Build the Package

```bash
# Build both wheel and source distribution
python -m build

# This creates:
# - dist/databricks_notebook_test_framework-0.1.0-py3-none-any.whl
# - dist/databricks-notebook-test-framework-0.1.0.tar.gz
```

### Step 5: Test the Package Locally

```bash
# Install in a fresh virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate
pip install dist/databricks_notebook_test_framework-0.1.0-py3-none-any.whl

# Test the CLI
dbx-test --version

# Deactivate when done
deactivate
```

### Step 6: Upload to TestPyPI (Optional but Recommended)

TestPyPI is a separate instance of PyPI for testing:

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# You'll be prompted for credentials:
# Username: __token__
# Password: <your TestPyPI API token>
```

Test the installation from TestPyPI:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple databricks-notebook-test-framework
```

### Step 7: Upload to PyPI

Once you've verified everything works:

```bash
# Upload to PyPI
python -m twine upload dist/*

# You'll be prompted for credentials:
# Username: __token__
# Password: <your PyPI API token>
```

### Step 8: Verify the Upload

1. Visit https://pypi.org/project/databricks-notebook-test-framework/
2. Check that the metadata, description, and links are correct
3. Test installation:

```bash
pip install databricks-notebook-test-framework
```

### Step 9: Tag the Release in Git

```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

## Using API Tokens

### Create a PyPI API Token

1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Give it a name (e.g., "databricks-notebook-test-framework")
4. Set scope to "Entire account" or specific project
5. Copy the token (starts with `pypi-`)

### Store Token in `.pypirc`

Create/edit `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YourAPITokenHere

[testpypi]
username = __token__
password = pypi-YourTestPyPITokenHere
repository = https://test.pypi.org/legacy/
```

**Important**: Add `.pypirc` to your `.gitignore`!

## Automation with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

Add your PyPI token to GitHub Secrets:
1. Go to repository Settings → Secrets → Actions
2. Add new secret named `PYPI_API_TOKEN`
3. Paste your PyPI API token

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (1.0.0): Incompatible API changes
- **MINOR** version (0.1.0): Add functionality (backwards-compatible)
- **PATCH** version (0.0.1): Bug fixes (backwards-compatible)

Examples:
- `0.1.0` → `0.1.1`: Bug fix
- `0.1.0` → `0.2.0`: New feature
- `0.9.0` → `1.0.0`: First stable release

## Updating the Remote Runner

After publishing to PyPI, you can simplify the remote runner to use PyPI instead of uploading wheels:

```python
# Instead of building and uploading wheel:
libraries = [{"pypi": {"package": "databricks-notebook-test-framework"}}]

# Or specify a version:
libraries = [{"pypi": {"package": "databricks-notebook-test-framework==0.1.0"}}]
```

## Checklist Before Publishing

- [ ] All tests pass
- [ ] Documentation is up to date
- [ ] CHANGELOG.md is updated
- [ ] Version number is incremented
- [ ] Author information is correct
- [ ] GitHub repository URL is correct
- [ ] README.md has installation instructions
- [ ] LICENSE file exists
- [ ] No sensitive information in code
- [ ] Package builds successfully
- [ ] Tested locally from wheel

## Troubleshooting

### Error: "File already exists"

You can't upload the same version twice. Increment the version number in `pyproject.toml`.

### Error: "Invalid distribution"

Make sure you have a valid `README.md` and all required metadata in `pyproject.toml`.

### Error: "403 Forbidden"

Check your API token and make sure it has the correct permissions.

### Package not found after upload

It may take a few minutes for the package to be available. Clear pip cache:

```bash
pip cache purge
```

## Resources

- [PyPI Documentation](https://packaging.python.org/tutorials/packaging-projects/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Semantic Versioning](https://semver.org/)

