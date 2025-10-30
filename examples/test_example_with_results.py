# Databricks notebook source
# MAGIC %md
# MAGIC # Test Example - With Results Return
# MAGIC
# MAGIC This notebook demonstrates how to write tests that return results to the CLI.

# COMMAND ----------

# Install the framework (if not already installed)
# %pip install /dbfs/FileStore/wheels/databricks_notebook_test_framework-0.1.0-py3-none-any.whl

# COMMAND ----------

from databricks_notebook_test_framework import NotebookTestFixture, run_notebook_tests
import json

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test Class Definition

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
        print("✓ Test data created")
    
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
        nulls = spark.sql("""
            SELECT * FROM test_data 
            WHERE id IS NULL OR name IS NULL OR amount IS NULL
        """).count()
        assert nulls == 0, f"Found {nulls} null values"
    
    def test_valid_ids(self):
        """IDs should be positive."""
        invalid = spark.sql("SELECT * FROM test_data WHERE id <= 0").count()
        assert invalid == 0, f"Found {invalid} invalid IDs"
    
    def run_cleanup(self):
        """Cleanup test data."""
        spark.sql("DROP VIEW IF EXISTS test_data")
        print("✓ Test data cleaned up")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run Tests

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

# MAGIC %md
# MAGIC ## Return Results to CLI
# MAGIC
# MAGIC This cell returns results in JSON format for CLI integration.
# MAGIC When running via CLI with `--workspace-tests`, this allows detailed
# MAGIC test results to be captured and displayed.

# COMMAND ----------

# Return results as JSON string for CLI to parse
# This enables the CLI to show individual test results
dbutils.notebook.exit(json.dumps(results))

