# Databricks notebook source
# MAGIC %md
# MAGIC # Test Example - Returns Results to CLI
# MAGIC 
# MAGIC This notebook demonstrates how to properly return test results to the CLI.

# COMMAND ----------

from databricks_notebook_test_framework import NotebookTestFixture, run_notebook_tests
import json

# COMMAND ----------

class TestExample(NotebookTestFixture):
    """Example test class with 3 tests."""
    
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

# Run tests
results = run_notebook_tests()

# COMMAND ----------

# Return results as JSON (REQUIRED for CLI to show individual tests)
dbutils.notebook.exit(json.dumps(results))

