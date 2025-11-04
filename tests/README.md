# Test Suite for dbx_test Framework

This directory contains comprehensive unit tests for the dbx_test framework.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and pytest configuration
├── test_testing.py          # Tests for NotebookTestFixture and testing core
├── test_config.py           # Tests for configuration management
├── test_discovery.py        # Tests for test discovery functionality
├── test_reporting.py        # Tests for test reporting in multiple formats
├── test_validation.py       # Tests for validation utilities
└── test_notebook.py         # Tests for notebook parsing utilities
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_testing.py
```

### Run Specific Test Class

```bash
pytest tests/test_testing.py::TestNotebookTestFixture
```

### Run Specific Test

```bash
pytest tests/test_testing.py::TestNotebookTestFixture::test_initialization
```

### Run Tests with Specific Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run tests that require Databricks
pytest -m requires_databricks
```

### Run Tests with Coverage

```bash
# Install pytest-cov first
pip install pytest-cov

# Run tests with coverage report
pytest --cov=dbx_test --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run Tests in Verbose Mode

```bash
pytest -v
```

### Run Tests with Output

```bash
# Show print statements
pytest -s

# Show local variables on failure
pytest -l
```

## Test Categories

### Unit Tests

Pure unit tests that don't require external dependencies:
- `test_testing.py` - Core testing functionality
- `test_config.py` - Configuration classes
- `test_validation.py` - Validation utilities
- `test_notebook.py` - Notebook parsing

### Integration Tests

Tests that may require external services (marked with `@pytest.mark.integration`):
- Tests that interact with file system
- Tests that require actual notebooks

### Slow Tests

Tests that take significant time to run (marked with `@pytest.mark.slow`):
- Parallel execution tests
- Large file processing tests

## Writing New Tests

### Test File Template

```python
"""
Unit tests for [module name].
"""

import pytest
from dbx_test.module import ClassToTest


class TestClassName:
    """Tests for ClassName."""
    
    def test_feature(self):
        """Test a specific feature."""
        # Arrange
        obj = ClassToTest()
        
        # Act
        result = obj.method()
        
        # Assert
        assert result == expected
```

### Using Fixtures

```python
def test_with_temp_dir(temp_dir):
    """Test using temporary directory fixture."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("content")
    assert test_file.exists()
```

### Marking Tests

```python
@pytest.mark.integration
def test_integration_feature():
    """Integration test."""
    pass

@pytest.mark.slow
def test_slow_operation():
    """Slow test."""
    pass

@pytest.mark.requires_databricks
def test_databricks_connection():
    """Test requiring Databricks connection."""
    pass
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -e ".[dev]"
    pytest --cov=dbx_test --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Test Coverage Goals

- **Overall coverage**: > 80%
- **Core modules** (`testing.py`, `config.py`): > 90%
- **Utility modules**: > 80%

## Common Issues

### Import Errors

If you get import errors, make sure you've installed the package:

```bash
pip install -e .
```

### Missing Dependencies

Install test dependencies:

```bash
pip install -e ".[dev]"
```

### Test Failures

1. Check that you're in the project root directory
2. Ensure all dependencies are installed
3. Check that pytest.ini is in the project root
4. Run with verbose mode: `pytest -v`

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure tests pass: `pytest`
3. Check coverage: `pytest --cov=dbx_test`
4. Add appropriate markers (`@pytest.mark.*`)
5. Update this README if adding new test categories

## Test Data

Test data and fixtures are created in memory or in temporary directories. No persistent test data is committed to the repository.

## Performance

- Fast unit tests: < 0.1s per test
- Slow tests: Marked with `@pytest.mark.slow`
- Total test suite: Should complete in < 60s

## Debugging Tests

### Run with PDB on Failure

```bash
pytest --pdb
```

### Run with PDB on First Failure

```bash
pytest -x --pdb
```

### Show Print Statements

```bash
pytest -s
```

### Verbose Output

```bash
pytest -vv
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)

