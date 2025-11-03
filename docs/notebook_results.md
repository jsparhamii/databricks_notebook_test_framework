# Returning Test Results from Databricks Notebooks to CLI

## Overview

To get detailed test results from notebooks running in Databricks back to the CLI, your test notebooks need to return the results in a structured format.

## Step 1: Update Your Test Notebooks

Your test notebooks should call `run_notebook_tests()` and return the results:

```python
# Databricks notebook source
from dbx_test import NotebookTestFixture, run_notebook_tests
import json

class TestExample(NotebookTestFixture):
    def run_setup(self):
        self.df = spark.range(10)
    
    def test_count(self):
        assert self.df.count() == 10, "Expected 10 rows"
    
    def test_columns(self):
        assert "id" in self.df.columns, "Missing id column"

# Run tests and get results
results = run_notebook_tests()

# Return results to caller (for CLI integration)
dbutils.notebook.exit(json.dumps(results))
```

## Step 2: Results Format

The `run_notebook_tests()` function returns a dictionary like:

```python
{
    "total": 2,
    "passed": 2,
    "failed": 0,
    "errors": 0,
    "fixtures": [
        {
            "fixture_name": "TestExample",
            "summary": {
                "total": 2,
                "passed": 2,
                "failed": 0,
                "errors": 0,
                "results": [
                    {
                        "name": "test_count",
                        "status": "passed",
                        "duration": 0.123,
                        "error_message": None,
                        "error_traceback": None
                    },
                    {
                        "name": "test_columns",
                        "status": "passed",
                        "duration": 0.045,
                        "error_message": None,
                        "error_traceback": None
                    }
                ]
            }
        }
    ]
}
```

## Complete Example Notebook

```python
# Databricks notebook source

# COMMAND ----------
# MAGIC %md
# MAGIC # Test Example
# MAGIC This notebook contains tests and returns results to the CLI

# COMMAND ----------

from dbx_test import NotebookTestFixture, run_notebook_tests
import json

# COMMAND ----------

class TestDataProcessing(NotebookTestFixture):
    """Test data processing functions."""
    
    def run_setup(self):
        """Setup test data."""
        self.df = spark.createDataFrame([
            (1, "Alice", 100),
            (2, "Bob", 200),
            (3, "Charlie", 150),
        ], ["id", "name", "amount"])
        
        self.df.createOrReplaceTempView("test_data")
    
    def test_row_count(self):
        """Should have 3 rows."""
        count = spark.table("test_data").count()
        assert count == 3, f"Expected 3 rows, got {count}"
    
    def test_total_amount(self):
        """Total amount should be 450."""
        total = spark.sql("SELECT SUM(amount) as total FROM test_data").collect()[0]["total"]
        assert total == 450, f"Expected 450, got {total}"
    
    def test_no_nulls(self):
        """No columns should have nulls."""
        nulls = spark.sql("SELECT * FROM test_data WHERE id IS NULL OR name IS NULL OR amount IS NULL").count()
        assert nulls == 0, f"Found {nulls} null values"
    
    def run_cleanup(self):
        """Cleanup test data."""
        spark.sql("DROP VIEW IF EXISTS test_data")

# COMMAND ----------

# Run tests and capture results
print("="*60)
print("Running Tests...")
print("="*60)

results = run_notebook_tests()

print("\n" + "="*60)
print("Test Execution Complete")
print("="*60)
print(f"Total: {results['total']}")
print(f"Passed: {results['passed']}")
print(f"Failed: {results['failed']}")
print(f"Errors: {results['errors']}")
print("="*60)

# COMMAND ----------

# Return results as JSON string for CLI to parse
# This is crucial for CLI integration
dbutils.notebook.exit(json.dumps(results))
```

## How CLI Captures Results

The CLI will:
1. Run your notebook on Databricks
2. Wait for completion
3. Retrieve the notebook output (the JSON returned by `dbutils.notebook.exit()`)
4. Parse the JSON to extract individual test results
5. Display detailed results in the console
6. Generate JUnit XML reports

## Testing Locally vs Remote

### Local Testing (Interactive)
When running in a Databricks notebook interactively, just call:
```python
results = run_notebook_tests()
# Results are printed to console
```

### Remote Testing (CLI)
When running via CLI with `--workspace-tests`, add the exit line:
```python
results = run_notebook_tests()
dbutils.notebook.exit(json.dumps(results))
```

## Best Practice: Conditional Return

You can make your notebook work in both modes:

```python
# Run tests
results = run_notebook_tests()

# Only return results if running remotely (dbutils is available)
try:
    import json
    dbutils.notebook.exit(json.dumps(results))
except:
    # Running locally or interactively, just print results
    print(f"\nTest Results: {results}")
```

## CLI Output

When you run:
```bash
dbx_test run --remote --workspace-tests --profile adb \
  --tests-dir "/Workspace/Users/your.name@databricks.com/tests" \
  --pattern "test_*"
```

You'll see:
```
Running tests from Databricks workspace: /Workspace/Users/your.name@databricks.com/tests

Found 1 test notebook(s):
  • /Workspace/Users/your.name@databricks.com/tests/test_example

Running test_example...
  ✓ test_row_count (0.12s)
  ✓ test_total_amount (0.08s)
  ✓ test_no_nulls (0.05s)

Test Execution Summary:
Notebook: test_example
  Tests: 3
  Passed: 3 ✓
  Failed: 0
  Errors: 0
  Duration: 0.25s

Overall Summary:
Total Tests: 3
Passed: 3 ✓
Failed: 0
Errors: 0

🎉 All tests passed!
```

## Troubleshooting

### "Could not fetch run output"
This warning can appear but is usually harmless. The CLI will still capture results from the notebook exit.

### No Results Captured
Make sure your notebook ends with:
```python
import json
dbutils.notebook.exit(json.dumps(results))
```

### Malformed JSON
If the notebook crashes before returning results, the CLI will show the error. Check your notebook execution logs in Databricks.

## Next Steps

1. Update your test notebooks to return results
2. Run tests via CLI
3. View detailed results
4. Integrate into CI/CD pipelines

