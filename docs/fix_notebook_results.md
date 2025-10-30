# How to Return Test Results from Your Notebook

Your notebook needs to return the test results as JSON for the CLI to capture them.

## Current Issue

The CLI shows:
```
test_example:
  ✓ all_tests (0.00s)
```

This means the notebook ran successfully but didn't return individual test results.

## Solution: Update Your Notebook

Add these lines at the **END** of your test notebook:

### Step 1: Import JSON

```python
import json
```

### Step 2: Run Tests and Capture Results

```python
# Run tests and capture results
results = run_notebook_tests()
```

### Step 3: Return Results to CLI

```python
# IMPORTANT: Return results as JSON
# This allows the CLI to show individual test results
dbutils.notebook.exit(json.dumps(results))
```

## Complete Example

Here's what your `test_example` notebook should look like:

```python
# Databricks notebook source

# Import the framework
from databricks_notebook_test_framework import NotebookTestFixture, run_notebook_tests
import json

# COMMAND ----------

# Define your test class
class TestExample(NotebookTestFixture):
    """Example test class with multiple tests."""
    
    def run_setup(self):
        """Setup test data."""
        self.df = spark.createDataFrame([
            (1, "Alice", 100),
            (2, "Bob", 200),
            (3, "Charlie", 150),
        ], ["id", "name", "amount"])
        self.df.createOrReplaceTempView("test_data")
    
    def test_row_count(self):
        """Test that we have 3 rows."""
        count = spark.table("test_data").count()
        assert count == 3, f"Expected 3 rows, got {count}"
    
    def test_total_amount(self):
        """Test that total amount is correct."""
        total = spark.sql("SELECT SUM(amount) as total FROM test_data").collect()[0]["total"]
        assert total == 450, f"Expected 450, got {total}"
    
    def test_has_columns(self):
        """Test that required columns exist."""
        columns = set(spark.table("test_data").columns)
        required = {"id", "name", "amount"}
        assert required <= columns, f"Missing columns: {required - columns}"
    
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
print(f"Total: {results['total']}, Passed: {results['passed']}, Failed: {results['failed']}")
print("="*60)

# COMMAND ----------

# CRITICAL: Return results as JSON for CLI
# Without this line, the CLI won't see individual test results
dbutils.notebook.exit(json.dumps(results))
```

## Expected CLI Output

After adding the JSON return, you should see:

```
Found 1 test notebook(s):
  • /Workspace/Users/james.parham@databricks.com/dbx_test/test/test_example

Test Results:

test_example:
  ✓ TestExample.test_row_count (0.12s)
  ✓ TestExample.test_total_amount (0.08s)
  ✓ TestExample.test_has_columns (0.05s)

Test Execution Summary:
Total: 3, Passed: 3, Failed: 0

🎉 All tests passed!
```

## Key Points

1. **Import json** at the top of your notebook
2. **Call `run_notebook_tests()`** to execute tests and get results
3. **Always end with** `dbutils.notebook.exit(json.dumps(results))`
4. The last command cell should ONLY have the `dbutils.notebook.exit()` line

## Testing Locally vs Remotely

### In Databricks UI (Interactive):
```python
# Just run this, results print to console
results = run_notebook_tests()
```

### From CLI (Remote):
```python
# Run tests
results = run_notebook_tests()

# Return to CLI (REQUIRED for detailed results)
dbutils.notebook.exit(json.dumps(results))
```

## Troubleshooting

### Problem: Still seeing "all_tests" instead of individual tests

**Cause:** Notebook is not returning JSON results

**Solution:** Make sure the LAST cell in your notebook is:
```python
import json
dbutils.notebook.exit(json.dumps(results))
```

### Problem: "NameError: name 'results' is not defined"

**Cause:** Haven't run `results = run_notebook_tests()` before the exit

**Solution:** Make sure you have this line before the exit:
```python
results = run_notebook_tests()
dbutils.notebook.exit(json.dumps(results))
```

### Problem: Tests run but return empty results

**Cause:** The `results` variable is None or empty

**Solution:** Make sure `run_notebook_tests()` is being called and returns data:
```python
results = run_notebook_tests()
print(f"DEBUG: Results = {results}")  # Check what's returned
dbutils.notebook.exit(json.dumps(results))
```

## Quick Fix Template

Add this cell at the END of your notebook:

```python
# Cell: Return Results
import json

# Run all tests
results = run_notebook_tests()

# Return to CLI
dbutils.notebook.exit(json.dumps(results))
```

## Example Result Object

The `results` dictionary looks like this:

```python
{
    "total": 3,
    "passed": 3,
    "failed": 0,
    "errors": 0,
    "fixtures": [
        {
            "fixture_name": "TestExample",
            "summary": {
                "total": 3,
                "passed": 3,
                "failed": 0,
                "errors": 0,
                "results": [
                    {
                        "name": "test_row_count",
                        "status": "passed",
                        "duration": 0.123,
                        "error_message": None,
                        "error_traceback": None
                    },
                    # ... more test results
                ]
            }
        }
    ]
}
```

## Next Steps

1. Open your `test_example` notebook in Databricks
2. Add the `import json` at the top
3. Make sure you call `results = run_notebook_tests()`
4. Add `dbutils.notebook.exit(json.dumps(results))` as the last line
5. Run the CLI command again

You should then see all 3 individual tests in the CLI output! 🎉

