# Quick Reference: Running Tests in Databricks Notebooks

## Installation (One-Time Setup)

```python
# In your Databricks notebook
%pip install /dbfs/FileStore/wheels/databricks_notebook_test_framework-0.1.0-py3-none-any.whl
```

## Basic Pattern

```python
from databricks_notebook_test_framework import NotebookTestFixture, run_notebook_tests

class TestMyFeature(NotebookTestFixture):
    def run_setup(self):
        # Setup code (runs once before all tests)
        self.df = spark.createDataFrame([(1, "Alice")], ["id", "name"])
    
    def test_something(self):
        # Your test (starts with "test_")
        assert self.df.count() == 1
    
    def run_cleanup(self):
        # Cleanup code (runs once after all tests)
        pass

# Run all tests in the notebook
run_notebook_tests()
```

## Common Patterns

### Pattern 1: Data Validation
```python
class TestData(NotebookTestFixture):
    def test_no_nulls(self):
        nulls = spark.table("my_table").filter("col IS NULL").count()
        assert nulls == 0
```

### Pattern 2: ETL Testing
```python
class TestETL(NotebookTestFixture):
    def run_setup(self):
        spark.sql("CREATE TABLE test_table AS SELECT * FROM source")
    
    def test_row_count(self):
        count = spark.table("test_table").count()
        assert count > 0
    
    def run_cleanup(self):
        spark.sql("DROP TABLE test_table")
```

### Pattern 3: Schema Validation
```python
class TestSchema(NotebookTestFixture):
    def test_columns(self):
        df = spark.table("my_table")
        required = {"id", "name", "email"}
        actual = set(df.columns)
        assert required <= actual
```

## Running Options

```python
# Run all tests
run_notebook_tests()

# Run specific test class
run_notebook_tests(TestMyFeature)

# Get boolean result
from databricks_notebook_test_framework import quick_test
passed = quick_test(TestMyFeature)

# Get detailed results
from databricks_notebook_test_framework import NotebookRunner
runner = NotebookRunner()
results = runner.run()
print(f"Passed: {results['passed']}/{results['total']}")
```

## Assertions

```python
# Simple assertions
assert condition, "Error message"

# Common patterns
assert df.count() == expected_count, f"Expected {expected_count} rows"
assert col in df.columns, f"Missing column {col}"
assert value > 0, f"Value must be positive, got {value}"
assert df.filter("col IS NULL").count() == 0, "Found null values"
```

## Output Example

```
============================================================
Running TestMyFeature
============================================================

Running test_something...
  ✓ PASSED

============================================================
SUMMARY
============================================================
Total Tests: 1
✓ Passed: 1
✗ Failed: 0
✗ Errors: 0

🎉 All tests passed!
============================================================
```

## Upload Wheel to DBFS (First Time)

```bash
# From your local machine
databricks fs cp dist/databricks_notebook_test_framework-0.1.0-py3-none-any.whl \
  dbfs:/FileStore/wheels/
```

## Tips

1. **Keep tests simple** - One assertion per test method
2. **Clean up** - Always implement `run_cleanup()`
3. **Descriptive names** - Use clear test method names
4. **Setup once** - Use `run_setup()` for common initialization
5. **Assert with messages** - Include helpful error messages

## Need Help?

- Full Guide: `docs/notebook_usage.md`
- Example Notebook: `examples/notebook_test_example.py`
- CLI Testing: `dbx-test --help`

