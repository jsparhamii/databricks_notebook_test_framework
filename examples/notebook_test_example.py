# Databricks notebook source
# MAGIC %md
# MAGIC # Example: Running Tests Directly in Databricks Notebooks
# MAGIC 
# MAGIC This notebook demonstrates how to write and run tests directly in a Databricks notebook.
# MAGIC 
# MAGIC ## Installation
# MAGIC 
# MAGIC First, install the framework from your wheel file uploaded to DBFS.

# COMMAND ----------

# MAGIC %pip install /dbfs/FileStore/wheels/databricks_notebook_test_framework-0.1.0-py3-none-any.whl

# COMMAND ----------

# Restart Python to use the newly installed package
dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import the Framework

# COMMAND ----------

from databricks_notebook_test_framework import NotebookTestFixture, run_notebook_tests

# COMMAND ----------

# MAGIC %md
# MAGIC ## Example 1: Simple Data Validation Test

# COMMAND ----------

class TestDataValidation(NotebookTestFixture):
    """Test basic data validation."""
    
    def run_setup(self):
        """Create test data."""
        self.df = spark.createDataFrame([
            (1, "Alice", 25, "alice@example.com"),
            (2, "Bob", 30, "bob@example.com"),
            (3, "Charlie", 35, "charlie@example.com"),
        ], ["id", "name", "age", "email"])
        
        print(f"Created test dataframe with {self.df.count()} rows")
    
    def test_row_count(self):
        """Should have exactly 3 rows."""
        count = self.df.count()
        assert count == 3, f"Expected 3 rows, got {count}"
    
    def test_no_null_values(self):
        """No columns should have null values."""
        for col in self.df.columns:
            null_count = self.df.filter(f"{col} IS NULL").count()
            assert null_count == 0, f"Column {col} has {null_count} null values"
    
    def test_age_range(self):
        """Age should be between 0 and 150."""
        invalid = self.df.filter("age < 0 OR age > 150").count()
        assert invalid == 0, f"Found {invalid} rows with invalid age"
    
    def test_email_format(self):
        """All emails should contain @ symbol."""
        invalid = self.df.filter("email NOT LIKE '%@%'").count()
        assert invalid == 0, f"Found {invalid} invalid email addresses"
    
    def run_cleanup(self):
        """Clean up resources."""
        print("Test cleanup completed")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run the Tests

# COMMAND ----------

# Run all tests in the notebook
results = run_notebook_tests()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Example 2: ETL Pipeline Test

# COMMAND ----------

class TestETLTransformation(NotebookTestFixture):
    """Test ETL transformation logic."""
    
    def run_setup(self):
        """Set up source and target tables."""
        # Create source table (bronze)
        source_data = spark.createDataFrame([
            (1, "Product A", "  100.50  ", "2024-01-01"),
            (2, "product b", "200.75", "2024-01-02"),
            (3, "Product C", "INVALID", "2024-01-03"),  # Invalid price
            (4, "PRODUCT D", "300.00", "invalid-date"),  # Invalid date
        ], ["id", "name", "price", "date"])
        
        source_data.write.mode("overwrite").saveAsTable("test_bronze_products")
        
        # Run transformation (silver)
        spark.sql("""
            CREATE OR REPLACE TABLE test_silver_products AS
            SELECT 
                id,
                UPPER(TRIM(name)) as name,
                CAST(price AS DOUBLE) as price,
                TRY_CAST(date AS DATE) as date
            FROM test_bronze_products
        """)
        
        print("ETL transformation completed")
    
    def test_data_quality_filtering(self):
        """Should have 4 rows (includes invalid data with nulls)."""
        bronze_count = spark.table("test_bronze_products").count()
        silver_count = spark.table("test_silver_products").count()
        
        assert bronze_count == 4, f"Source should have 4 rows, got {bronze_count}"
        assert silver_count == 4, f"Target should have 4 rows, got {silver_count}"
    
    def test_names_normalized(self):
        """All names should be uppercase and trimmed."""
        silver = spark.table("test_silver_products")
        
        # Check that all non-null names are uppercase
        lowercase_names = silver.filter(
            "name IS NOT NULL AND name != UPPER(name)"
        ).count()
        
        assert lowercase_names == 0, f"Found {lowercase_names} non-uppercase names"
    
    def test_price_conversion(self):
        """Valid prices should be converted to double."""
        silver = spark.table("test_silver_products")
        
        # Check that valid prices are numbers
        valid_prices = silver.filter(
            "price IS NOT NULL AND price > 0"
        ).count()
        
        assert valid_prices == 3, f"Expected 3 valid prices, got {valid_prices}"
    
    def test_date_parsing(self):
        """Valid dates should be parsed correctly."""
        silver = spark.table("test_silver_products")
        
        valid_dates = silver.filter("date IS NOT NULL").count()
        assert valid_dates == 3, f"Expected 3 valid dates, got {valid_dates}"
    
    def run_cleanup(self):
        """Drop test tables."""
        spark.sql("DROP TABLE IF EXISTS test_bronze_products")
        spark.sql("DROP TABLE IF EXISTS test_silver_products")
        print("Cleaned up test tables")

# COMMAND ----------

# Run the ETL tests
results = run_notebook_tests(TestETLTransformation)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Example 3: Multiple Test Classes

# COMMAND ----------

class TestSchemaValidation(NotebookTestFixture):
    """Test that schema meets requirements."""
    
    def run_setup(self):
        self.df = spark.createDataFrame(
            [(1, "test", 100.0, "2024-01-01")],
            ["id", "name", "amount", "date"]
        )
    
    def test_required_columns_exist(self):
        """All required columns should exist."""
        required = {"id", "name", "amount", "date"}
        actual = set(self.df.columns)
        
        missing = required - actual
        assert len(missing) == 0, f"Missing columns: {missing}"
    
    def test_column_types(self):
        """Column types should match requirements."""
        schema = {f.name: str(f.dataType) for f in self.df.schema.fields}
        
        assert "LongType" in schema["id"], "id should be numeric"
        assert "StringType" in schema["name"], "name should be string"
        assert "DoubleType" in schema["amount"], "amount should be double"


class TestBusinessRules(NotebookTestFixture):
    """Test business logic rules."""
    
    def run_setup(self):
        self.transactions = spark.createDataFrame([
            (1, 100.0, 10.0, "completed"),
            (2, 200.0, 20.0, "completed"),
            (3, 150.0, 15.0, "pending"),
        ], ["id", "amount", "tax", "status"])
    
    def test_tax_is_10_percent(self):
        """Tax should be exactly 10% of amount."""
        for row in self.transactions.collect():
            expected_tax = row["amount"] * 0.10
            assert row["tax"] == expected_tax, \
                f"Tax mismatch for transaction {row['id']}: " \
                f"expected {expected_tax}, got {row['tax']}"
    
    def test_valid_status_values(self):
        """Status should only be completed or pending."""
        valid_statuses = ["completed", "pending"]
        
        invalid = self.transactions.filter(
            ~self.transactions.status.isin(valid_statuses)
        ).count()
        
        assert invalid == 0, f"Found {invalid} invalid status values"


class TestPerformance(NotebookTestFixture):
    """Test performance requirements."""
    
    def test_handles_large_dataset(self):
        """Should process 1 million rows quickly."""
        import time
        
        # Create large dataset
        large_df = spark.range(1000000)
        
        start = time.time()
        count = large_df.count()
        duration = time.time() - start
        
        assert count == 1000000, f"Expected 1M rows, got {count}"
        assert duration < 10, f"Count took {duration:.2f}s, should be < 10s"

# COMMAND ----------

# Run all test classes defined in the notebook
results = run_notebook_tests()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Check Results Programmatically

# COMMAND ----------

# Get the results from the last run
if results['failed'] == 0 and results['errors'] == 0:
    print("✅ All tests passed!")
    print(f"Successfully ran {results['passed']} tests")
    
    # Could trigger downstream workflow
    # dbutils.notebook.run("production_pipeline", timeout_seconds=3600)
else:
    print("❌ Some tests failed!")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Errors: {results['errors']}")
    
    # Raise exception to stop workflow
    raise Exception("Tests failed - stopping workflow")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Example 4: Using Quick Test

# COMMAND ----------

from databricks_notebook_test_framework import quick_test

class TestQuick(NotebookTestFixture):
    """Quick validation test."""
    
    def test_basic_math(self):
        assert 1 + 1 == 2
    
    def test_spark_available(self):
        df = spark.range(10)
        assert df.count() == 10

# Returns True/False
passed = quick_test(TestQuick)
print(f"Quick test result: {'PASSED' if passed else 'FAILED'}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Example 5: Integration with Notebook Parameters

# COMMAND ----------

# Create widgets for parameters
dbutils.widgets.text("environment", "dev", "Environment")
dbutils.widgets.text("table_name", "test_data", "Table Name")

# COMMAND ----------

class TestWithParameters(NotebookTestFixture):
    """Test that uses notebook parameters."""
    
    def run_setup(self):
        """Get parameters from widgets."""
        self.env = dbutils.widgets.get("environment")
        self.table_name = dbutils.widgets.get("table_name")
        
        # Create environment-specific test data
        self.df = spark.createDataFrame(
            [(1, self.env, self.table_name)],
            ["id", "environment", "table"]
        )
        
        print(f"Testing in environment: {self.env}")
        print(f"Testing table: {self.table_name}")
    
    def test_environment_set(self):
        """Environment parameter should be set."""
        assert self.env in ["dev", "test", "prod"], \
            f"Invalid environment: {self.env}"
    
    def test_table_name_valid(self):
        """Table name should not be empty."""
        assert len(self.table_name) > 0, "Table name is empty"

# Run parameterized tests
run_notebook_tests(TestWithParameters)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC 
# MAGIC You've learned how to:
# MAGIC 
# MAGIC 1. Install the framework in a notebook
# MAGIC 2. Write test classes with `NotebookTestFixture`
# MAGIC 3. Run tests with `run_notebook_tests()`
# MAGIC 4. Test data validation, ETL logic, and business rules
# MAGIC 5. Use multiple test classes
# MAGIC 6. Check results programmatically
# MAGIC 7. Use notebook parameters in tests
# MAGIC 
# MAGIC **Next Steps:**
# MAGIC - Add tests to your production notebooks
# MAGIC - Use CLI for automated testing: `dbx-test run --remote`
# MAGIC - Set up CI/CD integration

