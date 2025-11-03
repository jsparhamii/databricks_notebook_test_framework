# Testing Application Code from src/

This example shows how to test your application code (in `src/`) using the test framework (tests in `tests/`).

## Project Structure

```
my_databricks_project/
├── src/
│   ├── __init__.py
│   ├── data_processing/
│   │   ├── __init__.py
│   │   ├── transformations.py    # Your application code
│   │   ├── validators.py         # Your application code
│   │   └── aggregations.py       # Your application code
│   └── utils/
│       ├── __init__.py
│       └── helpers.py             # Your application code
├── tests/
│   ├── test_transformations.py   # Tests for transformations
│   ├── test_validators.py        # Tests for validators
│   └── test_aggregations.py      # Tests for aggregations
├── config/
│   └── test_config.yml
└── pyproject.toml
```

## Step 1: Create Your Application Code

### `src/data_processing/transformations.py`

```python
"""Data transformation functions."""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def clean_customer_data(df: DataFrame) -> DataFrame:
    """
    Clean customer data by standardizing formats.
    
    Args:
        df: Input dataframe with columns: id, name, email, phone
        
    Returns:
        Cleaned dataframe
    """
    return df.select(
        "id",
        F.upper(F.trim(df.name)).alias("name"),
        F.lower(F.trim(df.email)).alias("email"),
        F.regexp_replace(df.phone, r"[^\d]", "").alias("phone")
    )


def calculate_customer_lifetime_value(df: DataFrame) -> DataFrame:
    """
    Calculate customer lifetime value from transactions.
    
    Args:
        df: Dataframe with columns: customer_id, amount, date
        
    Returns:
        Dataframe with customer_id, total_value, transaction_count, first_purchase, last_purchase
    """
    return df.groupBy("customer_id").agg(
        F.sum("amount").alias("total_value"),
        F.count("*").alias("transaction_count"),
        F.min("date").alias("first_purchase"),
        F.max("date").alias("last_purchase")
    )


def enrich_with_demographics(customers: DataFrame, demographics: DataFrame) -> DataFrame:
    """
    Enrich customer data with demographic information.
    
    Args:
        customers: Customer dataframe
        demographics: Demographics dataframe
        
    Returns:
        Enriched customer dataframe
    """
    return customers.join(
        demographics,
        customers.id == demographics.customer_id,
        "left"
    ).drop(demographics.customer_id)
```

### `src/data_processing/validators.py`

```python
"""Data validation functions."""

from pyspark.sql import DataFrame
from typing import List, Dict, Any


def validate_schema(df: DataFrame, required_columns: List[str]) -> Dict[str, Any]:
    """
    Validate that dataframe has required columns.
    
    Args:
        df: Dataframe to validate
        required_columns: List of required column names
        
    Returns:
        Dict with validation results
    """
    actual_columns = set(df.columns)
    required_set = set(required_columns)
    
    missing = required_set - actual_columns
    extra = actual_columns - required_set
    
    return {
        "valid": len(missing) == 0,
        "missing_columns": list(missing),
        "extra_columns": list(extra),
        "message": "Schema valid" if len(missing) == 0 else f"Missing columns: {missing}"
    }


def validate_no_nulls(df: DataFrame, columns: List[str]) -> Dict[str, Any]:
    """
    Validate that specified columns have no null values.
    
    Args:
        df: Dataframe to validate
        columns: Columns to check for nulls
        
    Returns:
        Dict with validation results
    """
    null_counts = {}
    for col in columns:
        count = df.filter(f"{col} IS NULL").count()
        if count > 0:
            null_counts[col] = count
    
    return {
        "valid": len(null_counts) == 0,
        "null_counts": null_counts,
        "message": "No nulls found" if len(null_counts) == 0 else f"Nulls found: {null_counts}"
    }


def validate_email_format(df: DataFrame, email_column: str = "email") -> Dict[str, Any]:
    """
    Validate email format.
    
    Args:
        df: Dataframe to validate
        email_column: Name of email column
        
    Returns:
        Dict with validation results
    """
    invalid_count = df.filter(
        f"{email_column} NOT RLIKE '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{{2,}}$'"
    ).count()
    
    return {
        "valid": invalid_count == 0,
        "invalid_count": invalid_count,
        "message": "All emails valid" if invalid_count == 0 else f"Found {invalid_count} invalid emails"
    }
```

### `src/data_processing/aggregations.py`

```python
"""Data aggregation functions."""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def daily_sales_summary(df: DataFrame) -> DataFrame:
    """
    Create daily sales summary.
    
    Args:
        df: Transactions with columns: date, amount, customer_id
        
    Returns:
        Daily summary with total_sales, transaction_count, unique_customers
    """
    return df.groupBy("date").agg(
        F.sum("amount").alias("total_sales"),
        F.count("*").alias("transaction_count"),
        F.countDistinct("customer_id").alias("unique_customers")
    )


def top_customers_by_revenue(df: DataFrame, top_n: int = 10) -> DataFrame:
    """
    Get top N customers by revenue.
    
    Args:
        df: Transactions with columns: customer_id, amount
        top_n: Number of top customers to return
        
    Returns:
        Top N customers with total revenue
    """
    customer_revenue = df.groupBy("customer_id").agg(
        F.sum("amount").alias("total_revenue")
    )
    
    return customer_revenue.orderBy(F.desc("total_revenue")).limit(top_n)


def calculate_running_total(df: DataFrame, partition_by: str, order_by: str, value_col: str) -> DataFrame:
    """
    Calculate running total.
    
    Args:
        df: Input dataframe
        partition_by: Column to partition by
        order_by: Column to order by
        value_col: Column to sum
        
    Returns:
        Dataframe with running_total column added
    """
    window_spec = Window.partitionBy(partition_by).orderBy(order_by).rowsBetween(
        Window.unboundedPreceding, Window.currentRow
    )
    
    return df.withColumn("running_total", F.sum(value_col).over(window_spec))
```

## Step 2: Create Tests for Your Application Code

### `tests/test_transformations.py`

```python
"""Tests for data_processing.transformations module."""

# Add src/ to Python path so we can import our application code
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from dbx_test import NotebookTestFixture
from data_processing.transformations import (
    clean_customer_data,
    calculate_customer_lifetime_value,
    enrich_with_demographics
)


class TestCleanCustomerData(NotebookTestFixture):
    """Test the clean_customer_data function."""
    
    def run_setup(self):
        """Create test data."""
        # Create test customers with messy data
        self.raw_customers = spark.createDataFrame([
            (1, "  alice smith  ", "Alice.Smith@EXAMPLE.COM  ", "(555) 123-4567"),
            (2, "bob jones", "  BOB@example.com", "555-234-5678"),
            (3, "CHARLIE BROWN", "charlie@example.com", "5553456789"),
        ], ["id", "name", "email", "phone"])
        
        # Apply transformation
        self.cleaned = clean_customer_data(self.raw_customers)
    
    def test_names_are_uppercase_and_trimmed(self):
        """Names should be uppercase with no leading/trailing spaces."""
        for row in self.cleaned.collect():
            name = row["name"]
            assert name == name.upper(), f"Name not uppercase: {name}"
            assert name == name.strip(), f"Name has whitespace: '{name}'"
    
    def test_emails_are_lowercase_and_trimmed(self):
        """Emails should be lowercase with no leading/trailing spaces."""
        for row in self.cleaned.collect():
            email = row["email"]
            assert email == email.lower(), f"Email not lowercase: {email}"
            assert email == email.strip(), f"Email has whitespace: '{email}'"
    
    def test_phones_have_only_digits(self):
        """Phone numbers should contain only digits."""
        for row in self.cleaned.collect():
            phone = row["phone"]
            assert phone.isdigit(), f"Phone contains non-digits: {phone}"
            assert len(phone) == 10, f"Phone should be 10 digits, got {len(phone)}"
    
    def test_all_rows_preserved(self):
        """Should not lose any rows during cleaning."""
        assert self.raw_customers.count() == self.cleaned.count()


class TestCalculateCustomerLifetimeValue(NotebookTestFixture):
    """Test the calculate_customer_lifetime_value function."""
    
    def run_setup(self):
        """Create test transactions."""
        self.transactions = spark.createDataFrame([
            (1, 100.0, "2024-01-01"),
            (1, 150.0, "2024-01-15"),
            (1, 200.0, "2024-02-01"),
            (2, 50.0, "2024-01-10"),
            (2, 75.0, "2024-01-20"),
        ], ["customer_id", "amount", "date"])
        
        # Calculate CLV
        self.clv = calculate_customer_lifetime_value(self.transactions)
    
    def test_correct_total_value(self):
        """Total value should sum all transactions per customer."""
        customer_1 = self.clv.filter("customer_id = 1").collect()[0]
        customer_2 = self.clv.filter("customer_id = 2").collect()[0]
        
        assert customer_1["total_value"] == 450.0, "Customer 1 total incorrect"
        assert customer_2["total_value"] == 125.0, "Customer 2 total incorrect"
    
    def test_correct_transaction_count(self):
        """Transaction count should be accurate."""
        customer_1 = self.clv.filter("customer_id = 1").collect()[0]
        customer_2 = self.clv.filter("customer_id = 2").collect()[0]
        
        assert customer_1["transaction_count"] == 3, "Customer 1 count incorrect"
        assert customer_2["transaction_count"] == 2, "Customer 2 count incorrect"
    
    def test_date_ranges(self):
        """First and last purchase dates should be correct."""
        customer_1 = self.clv.filter("customer_id = 1").collect()[0]
        
        assert customer_1["first_purchase"] == "2024-01-01"
        assert customer_1["last_purchase"] == "2024-02-01"


class TestEnrichWithDemographics(NotebookTestFixture):
    """Test the enrich_with_demographics function."""
    
    def run_setup(self):
        """Create test customers and demographics."""
        self.customers = spark.createDataFrame([
            (1, "Alice", "alice@example.com"),
            (2, "Bob", "bob@example.com"),
            (3, "Charlie", "charlie@example.com"),
        ], ["id", "name", "email"])
        
        self.demographics = spark.createDataFrame([
            (1, 25, "CA", "USA"),
            (2, 30, "NY", "USA"),
            # Note: Customer 3 has no demographics
        ], ["customer_id", "age", "state", "country"])
        
        # Enrich
        self.enriched = enrich_with_demographics(self.customers, self.demographics)
    
    def test_all_customers_preserved(self):
        """Left join should preserve all customers."""
        assert self.enriched.count() == 3, "Should have all 3 customers"
    
    def test_demographics_added(self):
        """Demographics columns should be added."""
        columns = set(self.enriched.columns)
        assert "age" in columns
        assert "state" in columns
        assert "country" in columns
    
    def test_customer_without_demographics_has_nulls(self):
        """Customers without demographics should have null values."""
        charlie = self.enriched.filter("id = 3").collect()[0]
        assert charlie["age"] is None
        assert charlie["state"] is None
    
    def test_no_duplicate_customer_id_column(self):
        """Should not have duplicate customer_id column."""
        columns = self.enriched.columns
        customer_id_count = columns.count("customer_id")
        assert customer_id_count == 0, "customer_id column should be dropped"
```

### `tests/test_validators.py`

```python
"""Tests for data_processing.validators module."""

import sys
from pathlib import Path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from dbx_test import NotebookTestFixture
from data_processing.validators import (
    validate_schema,
    validate_no_nulls,
    validate_email_format
)


class TestValidateSchema(NotebookTestFixture):
    """Test the validate_schema function."""
    
    def run_setup(self):
        """Create test dataframe."""
        self.df = spark.createDataFrame([
            (1, "Alice", "alice@example.com"),
        ], ["id", "name", "email"])
    
    def test_valid_schema(self):
        """Should pass when all required columns present."""
        result = validate_schema(self.df, ["id", "name", "email"])
        assert result["valid"] is True
        assert len(result["missing_columns"]) == 0
    
    def test_missing_columns_detected(self):
        """Should detect missing columns."""
        result = validate_schema(self.df, ["id", "name", "email", "phone"])
        assert result["valid"] is False
        assert "phone" in result["missing_columns"]
    
    def test_extra_columns_reported(self):
        """Should report extra columns."""
        result = validate_schema(self.df, ["id", "name"])
        assert "email" in result["extra_columns"]


class TestValidateNoNulls(NotebookTestFixture):
    """Test the validate_no_nulls function."""
    
    def run_setup(self):
        """Create test dataframe with some nulls."""
        self.df = spark.createDataFrame([
            (1, "Alice", "alice@example.com"),
            (2, None, "bob@example.com"),
            (3, "Charlie", None),
        ], ["id", "name", "email"])
    
    def test_detects_nulls(self):
        """Should detect null values."""
        result = validate_no_nulls(self.df, ["name", "email"])
        assert result["valid"] is False
        assert "name" in result["null_counts"]
        assert "email" in result["null_counts"]
    
    def test_no_nulls_in_id_column(self):
        """Should pass when column has no nulls."""
        result = validate_no_nulls(self.df, ["id"])
        assert result["valid"] is True


class TestValidateEmailFormat(NotebookTestFixture):
    """Test the validate_email_format function."""
    
    def run_setup(self):
        """Create test dataframe with valid and invalid emails."""
        self.valid_df = spark.createDataFrame([
            (1, "alice@example.com"),
            (2, "bob.jones@company.co.uk"),
            (3, "charlie+test@domain.org"),
        ], ["id", "email"])
        
        self.invalid_df = spark.createDataFrame([
            (1, "not-an-email"),
            (2, "@example.com"),
            (3, "missing@domain"),
        ], ["id", "email"])
    
    def test_valid_emails_pass(self):
        """Should validate correct email formats."""
        result = validate_email_format(self.valid_df)
        assert result["valid"] is True
        assert result["invalid_count"] == 0
    
    def test_invalid_emails_detected(self):
        """Should detect invalid email formats."""
        result = validate_email_format(self.invalid_df)
        assert result["valid"] is False
        assert result["invalid_count"] == 3
```

### `tests/test_aggregations.py`

```python
"""Tests for data_processing.aggregations module."""

import sys
from pathlib import Path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from dbx_test import NotebookTestFixture
from data_processing.aggregations import (
    daily_sales_summary,
    top_customers_by_revenue,
    calculate_running_total
)


class TestDailySalesSummary(NotebookTestFixture):
    """Test the daily_sales_summary function."""
    
    def run_setup(self):
        """Create test transactions."""
        self.transactions = spark.createDataFrame([
            ("2024-01-01", 100.0, 1),
            ("2024-01-01", 150.0, 2),
            ("2024-01-01", 200.0, 1),  # Customer 1 buys twice
            ("2024-01-02", 50.0, 3),
            ("2024-01-02", 75.0, 3),   # Customer 3 buys twice
        ], ["date", "amount", "customer_id"])
        
        # Calculate summary
        self.summary = daily_sales_summary(self.transactions)
    
    def test_correct_daily_totals(self):
        """Daily totals should be correct."""
        day1 = self.summary.filter("date = '2024-01-01'").collect()[0]
        day2 = self.summary.filter("date = '2024-01-02'").collect()[0]
        
        assert day1["total_sales"] == 450.0, "Day 1 total incorrect"
        assert day2["total_sales"] == 125.0, "Day 2 total incorrect"
    
    def test_correct_transaction_counts(self):
        """Transaction counts should be accurate."""
        day1 = self.summary.filter("date = '2024-01-01'").collect()[0]
        
        assert day1["transaction_count"] == 3, "Day 1 count incorrect"
    
    def test_correct_unique_customers(self):
        """Unique customer counts should be accurate."""
        day1 = self.summary.filter("date = '2024-01-01'").collect()[0]
        day2 = self.summary.filter("date = '2024-01-02'").collect()[0]
        
        assert day1["unique_customers"] == 2, "Day 1 should have 2 unique customers"
        assert day2["unique_customers"] == 1, "Day 2 should have 1 unique customer"


class TestTopCustomersByRevenue(NotebookTestFixture):
    """Test the top_customers_by_revenue function."""
    
    def run_setup(self):
        """Create test transactions."""
        self.transactions = spark.createDataFrame([
            (1, 100.0),
            (1, 150.0),  # Customer 1: 250.0 total
            (2, 300.0),  # Customer 2: 300.0 total
            (3, 50.0),
            (3, 75.0),   # Customer 3: 125.0 total
            (4, 500.0),  # Customer 4: 500.0 total (highest)
        ], ["customer_id", "amount"])
        
        # Get top 3
        self.top3 = top_customers_by_revenue(self.transactions, top_n=3)
    
    def test_returns_correct_number(self):
        """Should return requested number of customers."""
        assert self.top3.count() == 3, "Should return top 3"
    
    def test_correct_order(self):
        """Should be ordered by revenue descending."""
        results = self.top3.collect()
        
        assert results[0]["customer_id"] == 4, "Customer 4 should be #1"
        assert results[1]["customer_id"] == 2, "Customer 2 should be #2"
        assert results[2]["customer_id"] == 1, "Customer 1 should be #3"
    
    def test_correct_revenue_values(self):
        """Revenue values should be correct."""
        customer_4 = self.top3.filter("customer_id = 4").collect()[0]
        assert customer_4["total_revenue"] == 500.0


class TestCalculateRunningTotal(NotebookTestFixture):
    """Test the calculate_running_total function."""
    
    def run_setup(self):
        """Create test data."""
        self.df = spark.createDataFrame([
            ("A", "2024-01-01", 10.0),
            ("A", "2024-01-02", 20.0),
            ("A", "2024-01-03", 30.0),
            ("B", "2024-01-01", 5.0),
            ("B", "2024-01-02", 10.0),
        ], ["category", "date", "value"])
        
        # Calculate running total
        self.result = calculate_running_total(
            self.df,
            partition_by="category",
            order_by="date",
            value_col="value"
        )
    
    def test_running_total_correct(self):
        """Running totals should be cumulative."""
        category_a = self.result.filter("category = 'A'").orderBy("date").collect()
        
        assert category_a[0]["running_total"] == 10.0, "First value should be 10"
        assert category_a[1]["running_total"] == 30.0, "Second should be 10+20=30"
        assert category_a[2]["running_total"] == 60.0, "Third should be 10+20+30=60"
    
    def test_partitioning_works(self):
        """Each partition should have its own running total."""
        category_b = self.result.filter("category = 'B'").orderBy("date").collect()
        
        assert category_b[0]["running_total"] == 5.0, "Category B should start at 5"
        assert category_b[1]["running_total"] == 15.0, "Category B second should be 5+10=15"
```

## Step 3: Run the Tests

### Option A: Using CLI (Recommended for CI/CD)

```bash
# Run all tests
dbx_test run --local --tests-dir tests

# Run specific test file
dbx_test run --local --pattern "*test_transformations*"

# Run remotely on Databricks
dbx_test run --remote --tests-dir tests --profile dev
```

### Option B: In Databricks Notebook

Create a notebook that imports and tests your code:

```python
# Cell 1: Setup path
import sys
from pathlib import Path

# Add src to path
src_path = "/Workspace/Repos/my-repo/my_databricks_project/src"
sys.path.insert(0, src_path)

# Cell 2: Install framework
%pip install /dbfs/FileStore/wheels/dbx_test-0.1.0-py3-none-any.whl

# Cell 3: Import your code
from data_processing.transformations import clean_customer_data

# Cell 4: Write and run tests
from dbx_test import NotebookTestFixture, run_notebook_tests

class TestTransformations(NotebookTestFixture):
    def run_setup(self):
        self.raw_data = spark.createDataFrame([
            (1, "  alice  ", "ALICE@EXAMPLE.COM"),
        ], ["id", "name", "email"])
        
        self.cleaned = clean_customer_data(self.raw_data)
    
    def test_name_uppercase(self):
        row = self.cleaned.collect()[0]
        assert row["name"] == "ALICE"

run_notebook_tests()
```

## Step 4: Configure pyproject.toml

```toml
[project]
name = "my-databricks-project"
version = "0.1.0"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
include = ["data_processing*", "utils*"]
```

## Expected Output

```bash
$ dbx_test run --local --tests-dir tests

Discovered 3 test notebook(s):
  - tests/test_transformations.py (3 classes, 10 tests)
  - tests/test_validators.py (3 classes, 7 tests)
  - tests/test_aggregations.py (3 classes, 9 tests)

Running tests locally...

============================================================
Running TestCleanCustomerData
============================================================

Running test_names_are_uppercase_and_trimmed...
  ✓ PASSED
Running test_emails_are_lowercase_and_trimmed...
  ✓ PASSED
Running test_phones_have_only_digits...
  ✓ PASSED
Running test_all_rows_preserved...
  ✓ PASSED

============================================================
Running TestCalculateCustomerLifetimeValue
============================================================

Running test_correct_total_value...
  ✓ PASSED
Running test_correct_transaction_count...
  ✓ PASSED
Running test_date_ranges...
  ✓ PASSED

[... more tests ...]

============================================================
SUMMARY
============================================================
Total Tests: 26
✓ Passed: 26
✗ Failed: 0
✗ Errors: 0

🎉 All tests passed!
============================================================
```

## Tips for Testing Application Code

1. **Path Management**: Always add `src/` to Python path at the start of test files
2. **Modular Code**: Keep functions small and testable
3. **Type Hints**: Use type hints for better IDE support and documentation
4. **Test Data**: Create realistic test data that covers edge cases
5. **Separate Concerns**: One test class per function/feature
6. **Clean Up**: Drop temp tables/views in `run_cleanup()`

## Common Patterns

### Pattern 1: Test Helper

Create a test helper to avoid repeating path setup:

```python
# tests/test_helpers.py
import sys
from pathlib import Path

def setup_src_path():
    """Add src/ to Python path."""
    src_path = Path(__file__).parent.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

# Use in tests
from test_helpers import setup_src_path
setup_src_path()
```

### Pattern 2: Shared Fixtures

```python
# tests/fixtures.py
from dbx_test import NotebookTestFixture

class BaseTestWithSpark(NotebookTestFixture):
    """Base test class with common setup."""
    
    def run_setup(self):
        # Common setup for all tests
        self.test_db = "test_database"
        spark.sql(f"CREATE DATABASE IF NOT EXISTS {self.test_db}")
    
    def run_cleanup(self):
        spark.sql(f"DROP DATABASE IF EXISTS {self.test_db} CASCADE")

# Use in tests
from tests.fixtures import BaseTestWithSpark

class TestMyFeature(BaseTestWithSpark):
    # Inherits setup/cleanup
    pass
```

This example shows the complete workflow for testing application code! 🎉

