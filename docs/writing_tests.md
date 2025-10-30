# Writing Tests Guide

This guide covers best practices for writing effective tests using Nutter in the Databricks Notebook Test Framework.

## Test Structure

### Basic Nutter Test Structure

```python
from nutter.testing import NutterFixture


class TestYourNotebook(NutterFixture):
    """Test suite for your notebook."""
    
    def run_setup(self):
        """Runs before all tests."""
        # Setup code here
        pass
    
    def test_something(self):
        """Individual test case."""
        # Test code here
        assert True, "Test failed message"
    
    def run_cleanup(self):
        """Runs after all tests."""
        # Cleanup code here
        pass
```

### Naming Conventions

- **Test files**: End with `_test.py` or `_test.ipynb`
- **Test classes**: Inherit from `NutterFixture`
- **Test methods**: Start with `test_`
- **Assertion methods**: Start with `assertion_` (optional, advanced)

## Writing Effective Tests

### 1. Test Data Setup

```python
def run_setup(self):
    """Create test data."""
    # Method 1: Create DataFrame
    self.test_data = spark.createDataFrame([
        (1, "Alice", 100),
        (2, "Bob", 200),
    ], ["id", "name", "amount"])
    
    # Method 2: Create temporary view
    self.test_data.createOrReplaceTempView("test_view")
    
    # Method 3: Create temporary table
    self.test_data.write.format("delta").mode("overwrite")\
        .saveAsTable("test_table")
```

### 2. Schema Validation

```python
def test_schema(self):
    """Validate DataFrame schema."""
    df = spark.table("my_table")
    
    # Check columns exist
    expected_columns = ["id", "name", "amount", "date"]
    for col in expected_columns:
        assert col in df.columns, f"Missing column: {col}"
    
    # Check data types
    schema = df.schema
    id_type = [f.dataType.simpleString() for f in schema.fields if f.name == "id"][0]
    assert id_type in ["int", "bigint"], f"Wrong type for id: {id_type}"
```

### 3. Row Count Validation

```python
def test_row_count(self):
    """Validate row count."""
    df = spark.table("my_table")
    actual_count = df.count()
    expected_count = 1000
    
    assert actual_count == expected_count, \
        f"Expected {expected_count} rows, got {actual_count}"
```

### 4. Data Quality Checks

```python
def test_no_nulls(self):
    """Check for null values in required columns."""
    df = spark.table("my_table")
    
    null_count = df.filter("id IS NULL OR name IS NULL").count()
    assert null_count == 0, f"Found {null_count} rows with null values"

def test_positive_amounts(self):
    """Validate business rules."""
    df = spark.table("my_table")
    
    negative_count = df.filter("amount < 0").count()
    assert negative_count == 0, f"Found {negative_count} negative amounts"

def test_unique_ids(self):
    """Check for duplicate IDs."""
    df = spark.sql("""
        SELECT id, COUNT(*) as count
        FROM my_table
        GROUP BY id
        HAVING COUNT(*) > 1
    """)
    
    duplicate_count = df.count()
    assert duplicate_count == 0, f"Found {duplicate_count} duplicate IDs"
```

### 5. Aggregation Tests

```python
def test_aggregation(self):
    """Test aggregated results."""
    result = spark.sql("""
        SELECT 
            date,
            COUNT(*) as total_orders,
            SUM(amount) as total_revenue
        FROM my_table
        GROUP BY date
    """)
    
    # Check specific values
    day1 = result.filter("date = '2024-01-01'").collect()[0]
    assert day1["total_orders"] == 10, "Expected 10 orders on 2024-01-01"
    assert day1["total_revenue"] == 1000, "Expected revenue of 1000"
```

### 6. Transformation Tests

```python
def test_transformation(self):
    """Test data transformation logic."""
    # Apply transformation
    transformed = spark.sql("""
        SELECT 
            id,
            name,
            amount,
            amount * 1.1 as amount_with_tax
        FROM test_data
    """)
    
    # Validate transformation
    for row in transformed.collect():
        expected_tax_amount = row["amount"] * 1.1
        actual_tax_amount = row["amount_with_tax"]
        assert abs(expected_tax_amount - actual_tax_amount) < 0.01, \
            f"Tax calculation incorrect for id {row['id']}"
```

### 7. Join Tests

```python
def test_join(self):
    """Test join operations."""
    # Create two test tables
    customers = spark.createDataFrame([
        (1, "Alice"),
        (2, "Bob"),
    ], ["id", "name"])
    
    orders = spark.createDataFrame([
        (1, 1, 100),
        (2, 1, 200),
        (3, 2, 150),
    ], ["order_id", "customer_id", "amount"])
    
    customers.createOrReplaceTempView("test_customers")
    orders.createOrReplaceTempView("test_orders")
    
    # Join
    result = spark.sql("""
        SELECT 
            c.name,
            COUNT(o.order_id) as order_count,
            SUM(o.amount) as total_amount
        FROM test_customers c
        LEFT JOIN test_orders o ON c.id = o.customer_id
        GROUP BY c.name
    """)
    
    # Validate
    alice = result.filter("name = 'Alice'").collect()[0]
    assert alice["order_count"] == 2, "Alice should have 2 orders"
    assert alice["total_amount"] == 300, "Alice's total should be 300"
```

## Advanced Patterns

### Parameterized Tests

```python
def run_setup(self):
    """Setup with parameters."""
    # Read widget parameters (works in Databricks)
    try:
        self.env = dbutils.widgets.get("environment")
    except:
        self.env = "dev"  # Default for local testing

def test_environment_specific(self):
    """Test that uses parameters."""
    if self.env == "prod":
        # Stricter validation for production
        assert self.data_quality_score > 0.99
    else:
        # Relaxed validation for dev
        assert self.data_quality_score > 0.90
```

### Delta Lake-Specific Tests

```python
def test_delta_version(self):
    """Test Delta table version."""
    from delta.tables import DeltaTable
    
    delta_table = DeltaTable.forName(spark, "my_delta_table")
    history = delta_table.history(1).collect()
    
    latest_version = history[0]["version"]
    assert latest_version > 0, "Table should have been updated"

def test_delta_schema_evolution(self):
    """Test schema evolution."""
    df = spark.table("my_delta_table")
    
    # Check that new column exists
    assert "new_column" in df.columns, "Schema evolution failed"
```

### Testing with Mock Data

```python
def run_setup(self):
    """Create realistic mock data."""
    from datetime import datetime, timedelta
    
    # Generate date range
    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") 
             for i in range(30)]
    
    # Create mock transactions
    mock_data = []
    for i, date in enumerate(dates):
        for j in range(10):
            mock_data.append((
                i * 10 + j,           # id
                f"customer_{j}",      # customer
                100 + (i * 10),       # amount
                date,                 # date
            ))
    
    self.test_data = spark.createDataFrame(
        mock_data,
        ["id", "customer", "amount", "date"]
    )
    self.test_data.createOrReplaceTempView("transactions")
```

### Error Handling Tests

```python
def test_handles_bad_data(self):
    """Test that pipeline handles bad data gracefully."""
    bad_data = spark.createDataFrame([
        (1, None, 100),        # Null name
        (2, "Bob", -50),       # Negative amount
        (None, "Charlie", 75), # Null id
    ], ["id", "name", "amount"])
    
    bad_data.createOrReplaceTempView("bad_data")
    
    # Your cleaning logic
    cleaned = spark.sql("""
        SELECT *
        FROM bad_data
        WHERE id IS NOT NULL
          AND name IS NOT NULL
          AND amount > 0
    """)
    
    # Should filter out all bad records
    assert cleaned.count() == 0, "Bad data should be filtered out"
```

## Best Practices

### 1. Keep Tests Independent

```python
# ✅ Good - Each test is independent
class TestGood(NutterFixture):
    def run_setup(self):
        self.df = spark.createDataFrame([...])
    
    def test_a(self):
        # Uses setup data, doesn't modify it
        result = self.df.count()
        assert result == 10
    
    def test_b(self):
        # Independent of test_a
        result = self.df.filter("amount > 100").count()
        assert result == 5

# ❌ Bad - Tests depend on each other
class TestBad(NutterFixture):
    def test_a(self):
        self.result = compute_something()
    
    def test_b(self):
        # Depends on test_a running first!
        assert self.result > 0
```

### 2. Use Descriptive Test Names

```python
# ✅ Good
def test_customer_orders_aggregated_correctly(self):
    """Test that customer order totals are calculated correctly."""
    pass

# ❌ Bad
def test_1(self):
    """Test."""
    pass
```

### 3. Write Clear Assertion Messages

```python
# ✅ Good
assert count == expected_count, \
    f"Expected {expected_count} rows, but got {count}"

# ❌ Bad
assert count == expected_count
```

### 4. Test One Thing Per Test

```python
# ✅ Good - Separate concerns
def test_row_count(self):
    assert df.count() == 100

def test_schema(self):
    assert "id" in df.columns

# ❌ Bad - Testing multiple things
def test_everything(self):
    assert df.count() == 100
    assert "id" in df.columns
    assert df.filter("amount > 0").count() > 0
```

### 5. Clean Up Resources

```python
def run_cleanup(self):
    """Always clean up test resources."""
    # Drop temporary views
    spark.sql("DROP VIEW IF EXISTS test_view")
    
    # Drop temporary tables
    spark.sql("DROP TABLE IF EXISTS test_table")
    
    # Clear cache if needed
    spark.catalog.clearCache()
```

## Testing Checklist

Before committing your tests, ensure:

- [ ] Tests have descriptive names
- [ ] Each test is independent
- [ ] Assertion messages are clear
- [ ] Test data is cleaned up
- [ ] Tests run successfully locally
- [ ] Tests handle edge cases
- [ ] Schema validation is included
- [ ] Data quality checks are present
- [ ] Business logic is validated

## Example: Complete Test Suite

See `tests/example_test.py` and `tests/integration_test.py` for complete examples.

## Troubleshooting

### Test Not Discovered
- Ensure file ends with `_test.py`
- Class must inherit from `NutterFixture`
- Methods must start with `test_`

### SparkSession Not Available
- Tests must run in Spark environment
- For local testing, ensure Spark is installed
- For remote testing, ensure proper cluster configuration

### Timeout Issues
- Reduce test data size
- Optimize queries
- Increase timeout in config

### Flaky Tests
- Ensure tests are independent
- Avoid time-dependent assertions
- Use explicit waits instead of sleeps

