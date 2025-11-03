# Running Tests Directly in Databricks Notebooks

You can run tests directly in Databricks notebooks for interactive development and debugging. This is useful when:

- Developing and debugging tests interactively
- Running ad-hoc tests during development
- Testing code changes immediately
- Learning and experimenting with the framework

## Installation in Notebook

### Option 1: Install from DBFS (Recommended)

First, upload the wheel file to DBFS:

```bash
# From your local machine
databricks fs cp dist/dbx_test-0.1.0-py3-none-any.whl \
  dbfs:/FileStore/wheels/
```

Then in your Databricks notebook:

```python
%pip install /dbfs/FileStore/wheels/dbx_test-0.1.0-py3-none-any.whl
```

### Option 2: Install from PyPI

```python
%pip install dbx_test
```

### Option 3: Using the Helper Function

```python
from dbx_test import install_notebook_package

install_notebook_package("/dbfs/FileStore/wheels/dbx_test-0.1.0-py3-none-any.whl")
```

## Basic Usage

### Method 1: Simple One-Liner (Recommended)

```python
from dbx_test import NotebookTestFixture, run_notebook_tests

# Define your test class
class TestMyFeature(NotebookTestFixture):
    def run_setup(self):
        self.df = spark.createDataFrame([(1, "Alice"), (2, "Bob")], ["id", "name"])
    
    def test_count(self):
        assert self.df.count() == 2, "Expected 2 rows"
    
    def test_columns(self):
        assert self.df.columns == ["id", "name"], "Unexpected columns"

# Run all tests in the notebook
run_notebook_tests()
```

### Method 2: Run Specific Test Class

```python
from dbx_test import NotebookTestFixture, run_notebook_tests

class TestFeatureA(NotebookTestFixture):
    def test_something(self):
        assert True

class TestFeatureB(NotebookTestFixture):
    def test_something_else(self):
        assert True

# Run only TestFeatureA
run_notebook_tests(TestFeatureA)

# Run all tests
run_notebook_tests()
```

### Method 3: Using NotebookRunner for More Control

```python
from dbx_test import NotebookTestFixture, NotebookRunner

class TestMyFeature(NotebookTestFixture):
    def test_something(self):
        assert True

# Create runner
runner = NotebookRunner(verbose=True)

# Run specific class
results = runner.run(TestMyFeature)

# Or discover and run all
results = runner.run()

# Check results
print(f"Passed: {results['passed']}/{results['total']}")
```

### Method 4: Quick Test (Returns True/False)

```python
from dbx_test import NotebookTestFixture, quick_test

class TestQuick(NotebookTestFixture):
    def test_something(self):
        assert 1 + 1 == 2

# Returns True if all tests pass
passed = quick_test(TestQuick)
assert passed, "Tests failed!"
```

## Complete Examples

### Example 1: Data Validation Test

```python
from dbx_test import NotebookTestFixture, run_notebook_tests

class TestDataQuality(NotebookTestFixture):
    """Test data quality checks for customer data."""
    
    def run_setup(self):
        """Load test data."""
        self.customers = spark.createDataFrame([
            (1, "alice@example.com", 25, "active"),
            (2, "bob@example.com", 30, "active"),
            (3, "charlie@example.com", 35, "inactive"),
        ], ["id", "email", "age", "status"])
        
        self.customers.createOrReplaceTempView("customers")
    
    def test_no_null_emails(self):
        """Email should never be null."""
        null_count = spark.sql("""
            SELECT COUNT(*) as cnt 
            FROM customers 
            WHERE email IS NULL
        """).collect()[0]["cnt"]
        
        assert null_count == 0, f"Found {null_count} null emails"
    
    def test_valid_ages(self):
        """Age should be between 0 and 150."""
        invalid = spark.sql("""
            SELECT COUNT(*) as cnt 
            FROM customers 
            WHERE age < 0 OR age > 150
        """).collect()[0]["cnt"]
        
        assert invalid == 0, f"Found {invalid} invalid ages"
    
    def test_email_format(self):
        """Emails should contain @ symbol."""
        invalid = spark.sql("""
            SELECT COUNT(*) as cnt 
            FROM customers 
            WHERE email NOT LIKE '%@%'
        """).collect()[0]["cnt"]
        
        assert invalid == 0, f"Found {invalid} invalid emails"
    
    def run_cleanup(self):
        """Clean up test data."""
        spark.sql("DROP VIEW IF EXISTS customers")

# Run the tests
run_notebook_tests()
```

### Example 2: ETL Pipeline Test

```python
from dbx_test import NotebookTestFixture, run_notebook_tests

class TestETLPipeline(NotebookTestFixture):
    """Test the ETL transformation pipeline."""
    
    def run_setup(self):
        """Create source data and run transformation."""
        # Create bronze table
        raw_data = spark.createDataFrame([
            (1, "Product A", "100.50", "2024-01-01"),
            (2, "Product B", "200.75", "2024-01-02"),
            (3, "Product C", "INVALID", "2024-01-03"),
        ], ["id", "name", "price", "date"])
        
        raw_data.write.mode("overwrite").saveAsTable("bronze_products")
        
        # Run your ETL transformation
        spark.sql("""
            CREATE OR REPLACE TABLE silver_products AS
            SELECT 
                id,
                UPPER(name) as name,
                CAST(price AS DOUBLE) as price,
                DATE(date) as date
            FROM bronze_products
            WHERE price REGEXP '^[0-9]+\\.[0-9]+$'
        """)
    
    def test_invalid_records_filtered(self):
        """Invalid price records should be filtered out."""
        bronze_count = spark.table("bronze_products").count()
        silver_count = spark.table("silver_products").count()
        
        assert silver_count == 2, f"Expected 2 valid records, got {silver_count}"
        assert bronze_count == 3, f"Expected 3 source records, got {bronze_count}"
    
    def test_names_uppercase(self):
        """Product names should be uppercase."""
        lowercase_count = spark.sql("""
            SELECT COUNT(*) as cnt 
            FROM silver_products 
            WHERE name != UPPER(name)
        """).collect()[0]["cnt"]
        
        assert lowercase_count == 0, "Found lowercase names"
    
    def test_price_is_numeric(self):
        """All prices should be valid numbers."""
        silver = spark.table("silver_products")
        null_prices = silver.filter("price IS NULL").count()
        
        assert null_prices == 0, "Found null prices"
    
    def run_cleanup(self):
        """Drop test tables."""
        spark.sql("DROP TABLE IF EXISTS bronze_products")
        spark.sql("DROP TABLE IF EXISTS silver_products")

# Run tests
results = run_notebook_tests()

# Check if all passed
if results['failed'] == 0 and results['errors'] == 0:
    print("✅ All tests passed! Safe to promote to production.")
else:
    print("❌ Tests failed! Do not promote.")
```

### Example 3: Multiple Test Classes

```python
from dbx_test import NotebookTestFixture, run_notebook_tests

class TestSchemaValidation(NotebookTestFixture):
    """Test schema requirements."""
    
    def run_setup(self):
        self.df = spark.createDataFrame(
            [(1, "test", 10.5)], 
            ["id", "name", "value"]
        )
    
    def test_has_required_columns(self):
        expected = {"id", "name", "value"}
        actual = set(self.df.columns)
        assert expected == actual, f"Missing columns: {expected - actual}"
    
    def test_correct_types(self):
        types = {f.name: str(f.dataType) for f in self.df.schema.fields}
        assert types["id"] == "LongType()", "id should be LongType"
        assert types["value"] == "DoubleType()", "value should be DoubleType"


class TestBusinessLogic(NotebookTestFixture):
    """Test business rules."""
    
    def run_setup(self):
        self.orders = spark.createDataFrame([
            (1, 100.0, 10.0),
            (2, 200.0, 20.0),
        ], ["id", "amount", "tax"])
    
    def test_tax_calculation(self):
        """Tax should be 10% of amount."""
        for row in self.orders.collect():
            expected_tax = row["amount"] * 0.10
            assert row["tax"] == expected_tax, f"Tax mismatch for order {row['id']}"


class TestPerformance(NotebookTestFixture):
    """Test performance requirements."""
    
    def test_large_dataset_processing(self):
        """Should handle 1 million rows."""
        import time
        
        large_df = spark.range(1000000)
        
        start = time.time()
        result = large_df.count()
        duration = time.time() - start
        
        assert result == 1000000, "Row count mismatch"
        assert duration < 10, f"Query took {duration}s, should be < 10s"

# Run all test classes
run_notebook_tests()
```

## Output Example

When you run tests, you'll see output like:

```
============================================================
Running TestMyFeature
============================================================

Running test_count...
  ✓ PASSED
Running test_columns...
  ✓ PASSED

============================================================
SUMMARY
============================================================
Total Tests: 2
✓ Passed: 2
✗ Failed: 0
✗ Errors: 0

🎉 All tests passed!
============================================================
```

## Tips and Best Practices

### 1. Use Widgets for Parameters

```python
# Create widget
dbutils.widgets.text("env", "dev", "Environment")

class TestWithParams(NotebookTestFixture):
    def run_setup(self):
        self.env = dbutils.widgets.get("env")
        self.table = f"{self.env}_customers"
```

### 2. Test During Development

Create a test cell at the bottom of your notebook:

```python
# CELL: Run Tests
from dbx_test import run_notebook_tests

if __name__ == "__main__":
    run_notebook_tests()
```

### 3. Conditional Testing

```python
# Only run tests in dev/test environments
env = dbutils.widgets.get("env")

if env in ["dev", "test"]:
    run_notebook_tests()
else:
    print(f"Skipping tests in {env} environment")
```

### 4. Integration with Notebook Workflow

```python
from dbx_test import run_notebook_tests

# Run your main notebook code
main_result = run_etl_pipeline()

# Test the results
class TestPipelineResults(NotebookTestFixture):
    def test_output_exists(self):
        output_table = spark.table("output_table")
        assert output_table.count() > 0, "Output table is empty"

results = run_notebook_tests()

# Return results for notebook job
dbutils.notebook.exit(str(results))
```

### 5. Debugging Failed Tests

```python
from dbx_test import NotebookRunner

runner = NotebookRunner(verbose=True)
results = runner.run()

# Show detailed errors
for fixture in results.get('fixtures', []):
    for result in fixture['summary']['results']:
        if result['status'] != 'passed':
            print(f"\n{result['name']}:")
            print(result['error_traceback'])
```

## Comparison: CLI vs Notebook

| Feature | CLI (`dbx_test`) | Notebook (`run_notebook_tests`) |
|---------|-----------------|--------------------------------|
| **Use Case** | CI/CD, automated testing | Interactive development |
| **Setup** | Config file | In-notebook code |
| **Reports** | JUnit XML, HTML | Console output |
| **Execution** | Batch processing | Immediate feedback |
| **Best For** | Production testing | Development & debugging |

## Best Practices

1. **Development Flow**:
   - Develop tests in notebook using `run_notebook_tests()`
   - Debug and iterate quickly
   - Once stable, run via CLI for CI/CD

2. **Separate Test Notebooks**:
   - Keep test notebooks separate from production notebooks
   - Use naming convention: `*_test.py` or `test_*.py`

3. **Use Both Approaches**:
   - Notebook for rapid development
   - CLI for automated testing

4. **Clean Up Resources**:
   - Always implement `run_cleanup()`
   - Drop temporary tables/views
   - Clean test data

5. **Document Tests**:
   - Use docstrings for test classes and methods
   - Makes output more readable

## Troubleshooting

### "No test fixtures found"

Make sure your class inherits from `NotebookTestFixture`:

```python
from dbx_test import NotebookTestFixture

class TestMyFeature(NotebookTestFixture):  # Must inherit!
    def test_something(self):
        assert True
```

### "Module not found"

Reinstall the package in the notebook:

```python
%pip install --force-reinstall /dbfs/FileStore/wheels/dbx_test-0.1.0-py3-none-any.whl
dbutils.library.restartPython()
```

### "spark not defined"

The `spark` variable is automatically available in Databricks notebooks. If using custom Spark session:

```python
from pyspark.sql import SparkSession

class TestMyFeature(NotebookTestFixture):
    def run_setup(self):
        # Use the notebook's spark session
        self.df = spark.createDataFrame(...)
```

## Next Steps

- See [Writing Tests Guide](writing_tests.md) for test patterns
- See [CLI Usage](../README.md) for automated testing
- See [CI/CD Integration](ci_cd_integration.md) for production workflows

