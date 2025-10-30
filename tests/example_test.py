"""
Example test notebook demonstrating basic test patterns.
"""

from databricks_notebook_test_framework import NotebookTestFixture


class TestExampleNotebook(NotebookTestFixture):
    """
    Example test suite for a data transformation notebook.
    """
    
    def run_setup(self):
        """
        Setup code runs before tests.
        Initialize test data and temporary views/tables.
        """
        # Create sample test data
        self.test_data = spark.createDataFrame([
            (1, "Alice", 100, "2024-01-01"),
            (2, "Bob", 200, "2024-01-02"),
            (3, "Charlie", 150, "2024-01-03"),
            (4, "Diana", 300, "2024-01-04"),
        ], ["id", "name", "amount", "date"])
        
        # Register as temporary view
        self.test_data.createOrReplaceTempView("test_transactions")
        
        # Store expected results
        self.expected_row_count = 4
        self.expected_total_amount = 750
    
    def test_row_count(self):
        """Test that we have the expected number of rows."""
        result = spark.sql("SELECT * FROM test_transactions")
        actual_count = result.count()
        
        assert actual_count == self.expected_row_count, \
            f"Expected {self.expected_row_count} rows, got {actual_count}"
    
    def test_schema_validation(self):
        """Test that the schema contains expected columns."""
        result = spark.sql("SELECT * FROM test_transactions")
        columns = result.columns
        
        expected_columns = ["id", "name", "amount", "date"]
        for col in expected_columns:
            assert col in columns, f"Expected column '{col}' not found in schema"
    
    def test_data_types(self):
        """Test that columns have correct data types."""
        result = spark.sql("SELECT * FROM test_transactions")
        schema = result.schema
        
        # Get data types
        id_type = [f.dataType.simpleString() for f in schema.fields if f.name == "id"][0]
        amount_type = [f.dataType.simpleString() for f in schema.fields if f.name == "amount"][0]
        
        assert id_type in ["int", "bigint", "long"], \
            f"Expected 'id' to be integer type, got {id_type}"
        assert amount_type in ["int", "bigint", "long"], \
            f"Expected 'amount' to be integer type, got {amount_type}"
    
    def test_no_null_values(self):
        """Test that there are no null values in required columns."""
        result = spark.sql("""
            SELECT * FROM test_transactions 
            WHERE id IS NULL OR name IS NULL OR amount IS NULL
        """)
        
        null_count = result.count()
        assert null_count == 0, f"Found {null_count} rows with null values"
    
    def test_aggregation(self):
        """Test that aggregations work correctly."""
        result = spark.sql("""
            SELECT SUM(amount) as total_amount
            FROM test_transactions
        """)
        
        total = result.collect()[0]["total_amount"]
        assert total == self.expected_total_amount, \
            f"Expected total amount {self.expected_total_amount}, got {total}"
    
    def test_filter_logic(self):
        """Test that filtering works correctly."""
        result = spark.sql("""
            SELECT * FROM test_transactions
            WHERE amount > 150
        """)
        
        high_value_count = result.count()
        assert high_value_count == 2, \
            f"Expected 2 transactions with amount > 150, got {high_value_count}"
    
    def test_date_range(self):
        """Test date range filtering."""
        result = spark.sql("""
            SELECT * FROM test_transactions
            WHERE date >= '2024-01-02' AND date <= '2024-01-03'
        """)
        
        date_range_count = result.count()
        assert date_range_count == 2, \
            f"Expected 2 transactions in date range, got {date_range_count}"
    
    def run_cleanup(self):
        """
        Cleanup runs after all tests.
        Drop temporary views and clean up resources.
        """
        spark.sql("DROP VIEW IF EXISTS test_transactions")


class TestDataQuality(NotebookTestFixture):
    """
    Additional test suite for data quality checks.
    """
    
    def run_setup(self):
        """Setup test data with quality issues."""
        self.quality_data = spark.createDataFrame([
            (1, "Alice", 100, "alice@example.com"),
            (2, "Bob", 200, "bob@example.com"),
            (3, "Charlie", -50, "invalid-email"),  # Negative amount, invalid email
            (4, "Diana", 0, "diana@example.com"),  # Zero amount
        ], ["id", "name", "amount", "email"])
        
        self.quality_data.createOrReplaceTempView("test_quality")
    
    def test_positive_amounts(self):
        """Test that all amounts are positive."""
        result = spark.sql("""
            SELECT COUNT(*) as negative_count 
            FROM test_quality 
            WHERE amount <= 0
        """)
        
        negative_count = result.collect()[0]["negative_count"]
        assert negative_count == 0, \
            f"Found {negative_count} records with non-positive amounts"
    
    def test_email_format(self):
        """Test that email addresses are valid."""
        result = spark.sql("""
            SELECT COUNT(*) as invalid_count 
            FROM test_quality 
            WHERE email NOT LIKE '%@%.%'
        """)
        
        invalid_count = result.collect()[0]["invalid_count"]
        assert invalid_count == 0, \
            f"Found {invalid_count} records with invalid email format"
    
    def test_unique_ids(self):
        """Test that IDs are unique."""
        result = spark.sql("""
            SELECT id, COUNT(*) as count
            FROM test_quality
            GROUP BY id
            HAVING COUNT(*) > 1
        """)
        
        duplicate_count = result.count()
        assert duplicate_count == 0, \
            f"Found {duplicate_count} duplicate IDs"
    
    def run_cleanup(self):
        """Cleanup after tests."""
        spark.sql("DROP VIEW IF EXISTS test_quality")

