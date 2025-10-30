# Notebook Usage Feature

This document summarizes the notebook testing feature added to the framework.

## Overview

The framework now supports running tests directly in Databricks notebooks for interactive development and debugging. This complements the CLI-based testing workflow and provides immediate feedback during development.

## New Components

### 1. `notebook_runner.py` Module

**Location**: `src/databricks_notebook_test_framework/notebook_runner.py`

**Key Classes and Functions:**

- **`NotebookRunner`** - Main class for running tests in notebooks
  - `run(test_fixture_class=None)` - Run specific or all test fixtures
  - Automatic test discovery when no class specified
  - Verbose output with summaries

- **`run_notebook_tests(test_fixture_class=None, verbose=True)`** - Convenience function
  - Simplest way to run tests interactively
  - One-liner: `run_notebook_tests()`
  - Can run all tests or specific test class

- **`quick_test(test_class)`** - Returns True/False for pass/fail
  - Useful for simple assertions
  - Boolean result for conditional logic

- **`install_notebook_package(package_path)`** - Helper for installation
  - Install wheel from DBFS or local path
  - Shows success/failure messages

### 2. Documentation

**`docs/notebook_usage.md`** - Complete guide with:
- Installation methods (DBFS, PyPI, helper function)
- 4 different usage patterns
- 5 complete examples:
  1. Data validation
  2. ETL pipeline testing
  3. Multiple test classes
  4. Using widgets/parameters
  5. Integration with notebook workflows
- Troubleshooting section
- Comparison: CLI vs Notebook usage
- Best practices

### 3. Example Notebook

**`examples/notebook_test_example.py`** - Runnable Databricks notebook with:
- Installation cell
- 5 progressive examples
- Real-world test scenarios
- Parameter integration
- Result checking

## Usage Patterns

### Pattern 1: Simple One-Liner (Recommended)

```python
from databricks_notebook_test_framework import NotebookTestFixture, run_notebook_tests

class TestMyFeature(NotebookTestFixture):
    def test_something(self):
        assert True

run_notebook_tests()  # Discovers and runs all tests
```

### Pattern 2: Run Specific Test Class

```python
run_notebook_tests(TestMyFeature)  # Run only this class
```

### Pattern 3: NotebookRunner for Control

```python
from databricks_notebook_test_framework import NotebookRunner

runner = NotebookRunner(verbose=True)
results = runner.run(TestMyFeature)
print(f"Passed: {results['passed']}/{results['total']}")
```

### Pattern 4: Quick Boolean Test

```python
from databricks_notebook_test_framework import quick_test

passed = quick_test(TestMyFeature)
assert passed, "Tests failed!"
```

## Installation Options

### Option 1: From DBFS (Recommended)

```bash
# Upload wheel to DBFS
databricks fs cp dist/databricks_notebook_test_framework-0.1.0-py3-none-any.whl \
  dbfs:/FileStore/wheels/
```

Then in notebook:
```python
%pip install /dbfs/FileStore/wheels/databricks_notebook_test_framework-0.1.0-py3-none-any.whl
```

### Option 2: Using Helper

```python
from databricks_notebook_test_framework import install_notebook_package

install_notebook_package("/dbfs/FileStore/wheels/databricks_notebook_test_framework-0.1.0-py3-none-any.whl")
```

### Option 3: From PyPI (if published)

```python
%pip install databricks-notebook-test-framework
```

## Key Benefits

1. **Interactive Development**
   - Write and test code in the same notebook
   - Immediate feedback on changes
   - Easy debugging with full notebook context

2. **No Configuration Required**
   - No YAML config files needed
   - No CLI setup
   - Just import and run

3. **Perfect for**
   - Exploratory data analysis with tests
   - Rapid prototyping
   - Learning the framework
   - Ad-hoc validation
   - Development and debugging

4. **Integrates with Databricks**
   - Uses notebook's Spark session
   - Supports widgets/parameters
   - Works with notebook workflows
   - Can trigger downstream jobs based on results

## Example Output

```
============================================================
Running TestDataQuality
============================================================

Running test_no_null_emails...
  ✓ PASSED
Running test_valid_ages...
  ✓ PASSED
Running test_email_format...
  ✓ PASSED

============================================================
SUMMARY
============================================================
Total Tests: 3
✓ Passed: 3
✗ Failed: 0
✗ Errors: 0

🎉 All tests passed!
============================================================
```

## Workflow Integration

### Development → Production Flow

1. **Development** (Notebook)
   ```python
   # Develop and test interactively
   run_notebook_tests()
   ```

2. **CI/CD** (CLI)
   ```bash
   # Automated testing in pipeline
   dbx-test run --remote --profile prod
   ```

### Conditional Workflow

```python
# Run tests
results = run_notebook_tests()

# Trigger based on results
if results['failed'] == 0:
    dbutils.notebook.run("production_pipeline", timeout_seconds=3600)
else:
    raise Exception("Tests failed - stopping workflow")
```

## Updated Package Exports

The `__init__.py` now exports:

```python
__all__ = [
    "TestConfig",
    "TestDiscovery",
    "LocalTestRunner",
    "RemoteTestRunner",
    "TestReporter",
    "NotebookTestFixture",      # Base class
    "run_tests",                 # Module-level runner
    "NotebookRunner",            # Notebook runner class
    "run_notebook_tests",        # Simple notebook function
    "quick_test",                # Boolean result
    "install_notebook_package",  # Helper for installation
]
```

## Documentation Updates

- **README.md**: Added notebook usage section
- **docs/notebook_usage.md**: Complete guide (new)
- **examples/notebook_test_example.py**: Runnable example (new)

## Comparison: CLI vs Notebook

| Feature | CLI (`dbx-test`) | Notebook (`run_notebook_tests`) |
|---------|-----------------|--------------------------------|
| **Use Case** | CI/CD, batch testing | Interactive development |
| **Setup** | Config file required | No config needed |
| **Reports** | JUnit XML, HTML, JSON | Console output |
| **Execution** | Scheduled/automated | Immediate/interactive |
| **Discovery** | File-based | In-notebook classes |
| **Best For** | Production, CI/CD | Development, debugging |
| **Learning Curve** | Higher | Lower |

## Real-World Scenarios

### Scenario 1: Data Quality Checks

```python
# Run quality checks in notebook
class TestDataQuality(NotebookTestFixture):
    def test_no_nulls(self):
        assert df.filter("col IS NULL").count() == 0

run_notebook_tests()
```

### Scenario 2: ETL Validation

```python
# Test transformation logic
class TestETL(NotebookTestFixture):
    def run_setup(self):
        # Create bronze table
        ...
    
    def test_silver_quality(self):
        # Validate silver table
        ...

run_notebook_tests()
```

### Scenario 3: Environment-Specific Testing

```python
# Use notebook widgets
dbutils.widgets.text("env", "dev")

class TestWithEnv(NotebookTestFixture):
    def run_setup(self):
        self.env = dbutils.widgets.get("env")
        # Load env-specific data
    
    def test_env_config(self):
        assert self.env in ["dev", "test", "prod"]

run_notebook_tests()
```

## Next Steps

Users can:
1. Try the example notebook: `examples/notebook_test_example.py`
2. Read the complete guide: `docs/notebook_usage.md`
3. Start adding tests to existing notebooks
4. Transition to CLI for production/CI/CD

## Summary

The notebook testing feature makes the framework more accessible and developer-friendly while maintaining the robust CLI-based workflow for production use. It provides a natural development loop: **develop in notebook → test in notebook → automate with CLI**.

