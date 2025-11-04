# Testing Application Code Example

This example demonstrates how to test application code with the Databricks Notebook Test Framework.

## Structure

```
src_code_example/
├── src/
│   └── example          # Application code (functions to test)
└── tests/
    └── test_example     # Test notebook
```

## Application Code (`src/example`)

Contains a simple function to test:

```python
def sum_column(df, col_name, new_col_name=None):
    """Sum a column in a DataFrame."""
    if new_col_name is None:
        new_col_name = col_name
    result = df.groupBy().sum(col_name).withColumnRenamed(f"sum({col_name})", new_col_name)
    return result
```

## Test Notebook (`tests/test_example`)

Tests the `sum_column` function:

```python
# Import the source code
# MAGIC %run "../src/example"

from dbx_test import NotebookTestFixture, run_notebook_tests
import json

class TestMyFirstTest(NotebookTestFixture):
    def __init__(self):
        super().__init__()
        
        # Create test data
        self.df = spark.createDataFrame([
            (1, "Alice", 100),
            (2, "Bob", 200),
        ], ["id", "name", "amount"])
        self.df.createOrReplaceTempView("test_data")

    def test_sum_column(self):
        """Test the sum_column function."""
        result = sum_column(self.df.select("amount"), "amount", "total")      
        assert result.collect()[0]["total"] == 300

    def test_row_count(self):
        """Test we have 2 rows."""
        result = spark.sql("SELECT * FROM test_data")
        assert result.count() == 2

    def test_total_amount(self):
        """Test total amount."""
        result = spark.sql("SELECT SUM(amount) as total FROM test_data")
        total = result.collect()[0]["total"] + 1  # Intentional error
        assert total == 300, f"Expected 300, got {total}"

    def run_cleanup(self):
        """Clean up."""
        spark.sql("DROP VIEW IF EXISTS test_data")

# Run tests and return results
results = run_notebook_tests(TestMyFirstTest)
dbutils.notebook.exit(json.dumps(results))
```

## Key Points

### 1. Using `%run` to Import Code

```python
# MAGIC %run "../src/example"
```

This magic command imports all functions and classes from the source notebook.

### 2. Test Class Initialization

The test class uses `__init__` instead of `run_setup()`:

```python
def __init__(self):
    super().__init__()
    # Setup code here
```

### 3. Test Methods

Each test method:
- Starts with `test_`
- Contains assertions
- Has a docstring describing what it tests

### 4. Cleanup

Use `run_cleanup()` to clean up resources:

```python
def run_cleanup(self):
    spark.sql("DROP VIEW IF EXISTS test_data")
```

### 5. Returning Results

Always end with:

```python
results = run_notebook_tests(TestMyFirstTest)
dbutils.notebook.exit(json.dumps(results))
```

## Installation Requirements

### Installing dbx_test

**Important:** The `dbx_test` package must be installed on the Databricks cluster for remote test execution.

#### Option 1: Install from PyPI (Recommended)

```bash
pip install dbx_test
```

#### Option 2: Install from Source

```bash
git clone https://github.com/yourusername/dbx_test.git
cd dbx_test
pip install -e .
```

### Configure Cluster Libraries

When running tests remotely, you need to ensure `dbx_test` is available on the cluster. You can do this by:

1. **Using the scaffolding configuration**: The scaffold command generates a `config/test_config.yml` file with a `libraries` section where you can specify `dbx_test`:

```yaml
cluster:
  libraries:
    - pypi:
        package: "dbx_test"
```

2. **Install on an existing cluster**: Add `dbx_test` as a library to your cluster through the Databricks UI (Libraries → Install New → PyPI → `dbx_test`)

3. **Use serverless compute with environment**: Create a Databricks environment with `dbx_test` pre-installed (recommended for consistent execution)

## Running the Tests

### From CLI (Remote Execution)

```bash
# Run workspace tests
dbx_test run --remote --workspace-tests --profile adb \
  --tests-dir "/Workspace/Users/your.name@databricks.com/dbx_test/test"
```

**Note:** When using remote execution, the notebooks must already be in your Databricks workspace at the specified path.

## Expected Output

```
Running 1 notebook(s) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

Test Results:

test_example: 3 test(s)
  ✓ test_sum_column (0.55s)
  ✓ test_row_count (1.33s)
  ✗ test_total_amount (FAILED)
    Expected 300, got 301

Test Execution Summary:
Total: 3, Passed: 2, Failed: 1

❌ Some tests failed
```

## Workspace Structure

For this example to work, the notebooks should be in your Databricks workspace:

```
/Workspace/Users/your.name@databricks.com/dbx_test/
├── src/
│   └── example              # Application code notebook
└── test/
    └── test_example         # Test notebook
```

**Getting Notebooks into Your Workspace:**

You can upload notebooks to your workspace using:

1. **Databricks UI**: Upload → Import notebooks
2. **Databricks CLI**: `databricks workspace import <local-file> <workspace-path>`
3. **Git/Repos**: Use Databricks Repos to sync from your Git repository (recommended for team workflows)

## Tips

1. **Use `%run` for imports**: It's the Databricks way to import from other notebooks
2. **Keep application code separate**: Store reusable functions in `src/`
3. **Test behavior, not implementation**: Test what the function does, not how
4. **Clean up after tests**: Always implement `run_cleanup()` for resources
5. **Return results**: Always use `dbutils.notebook.exit(json.dumps(results))`

## Common Patterns

### Testing DataFrame Transformations

```python
def test_transformation(self):
    input_df = spark.createDataFrame([...])
    result_df = my_transformation(input_df)
    assert result_df.count() == expected_count
    assert result_df.columns == expected_columns
```

### Testing SQL Queries

```python
def test_query(self):
    result = spark.sql("SELECT * FROM my_table")
    assert result.count() > 0
    assert "required_column" in result.columns
```

### Testing Aggregations

```python
def test_aggregation(self):
    result = my_aggregation(self.df)
    total = result.collect()[0]["total"]
    assert total == expected_value
```

## Troubleshooting

### Import Errors

If you get import errors, make sure:
- The `%run` path is correct (relative to test notebook)
- The source notebook exists in the workspace
- The path uses forward slashes

### Test Not Running

Make sure:
- Test method starts with `test_`
- Test class inherits from `NotebookTestFixture`
- You're passing the class to `run_notebook_tests()`

### No Results Returned

Make sure you have:
```python
results = run_notebook_tests(TestMyFirstTest)
dbutils.notebook.exit(json.dumps(results))
```

## Next Steps

1. **Install dbx_test on your cluster**: Ensure `dbx_test` is available for remote execution (see [Installation Requirements](#installation-requirements))
2. Create your own application code in `src/`
3. Write tests in `tests/`
4. Upload to Databricks workspace (using UI, CLI, or Repos)
5. Run with `dbx_test` CLI
6. Integrate with CI/CD pipeline
