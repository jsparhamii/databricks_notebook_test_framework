# Testing Application Code: Complete Example

## 📁 Project Structure

Your typical Databricks project structure:

```
my_databricks_project/
├── src/                          # Your application code
│   ├── __init__.py
│   ├── data_processing/
│   │   ├── __init__.py
│   │   ├── transformations.py   # Functions to test
│   │   ├── validators.py        # Functions to test
│   │   └── aggregations.py      # Functions to test
│   └── utils/
│       └── helpers.py
├── tests/                        # Your tests
│   ├── test_transformations_test.py
│   ├── test_validators_test.py
│   └── test_aggregations_test.py
├── config/
│   └── test_config.yml
└── pyproject.toml
```

## 🎯 The Key Pattern

### In your test files, add this at the top:

```python
import sys
from pathlib import Path

# Add src/ to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Now you can import your application code
from data_processing.transformations import clean_customer_data
```

## 📝 Complete Working Example

### Step 1: Create Your Application Code

**File: `src/data_processing/transformations.py`**

```python
"""Data transformation functions."""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def clean_customer_data(df: DataFrame) -> DataFrame:
    """Clean customer data by standardizing formats."""
    return df.select(
        "id",
        F.upper(F.trim(df.name)).alias("name"),
        F.lower(F.trim(df.email)).alias("email"),
        F.regexp_replace(df.phone, r"[^\d]", "").alias("phone")
    )


def calculate_total_revenue(df: DataFrame) -> float:
    """Calculate total revenue from transactions."""
    return df.select(F.sum("amount").alias("total")).collect()[0]["total"]
```

### Step 2: Create Your Tests

**File: `tests/test_transformations_test.py`**

```python
"""Tests for transformations module."""

# Add src/ to path
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import framework
from databricks_notebook_test_framework import NotebookTestFixture

# Import YOUR code
from data_processing.transformations import clean_customer_data, calculate_total_revenue


class TestCleanCustomerData(NotebookTestFixture):
    """Test the clean_customer_data function."""
    
    def run_setup(self):
        """Create test data."""
        self.raw_customers = spark.createDataFrame([
            (1, "  alice smith  ", "Alice.Smith@EXAMPLE.COM  ", "(555) 123-4567"),
            (2, "bob jones", "  BOB@example.com", "555-234-5678"),
        ], ["id", "name", "email", "phone"])
        
        # Call your function
        self.cleaned = clean_customer_data(self.raw_customers)
    
    def test_names_are_uppercase(self):
        """Names should be uppercase."""
        for row in self.cleaned.collect():
            assert row["name"] == row["name"].upper(), f"Name not uppercase: {row['name']}"
    
    def test_emails_are_lowercase(self):
        """Emails should be lowercase."""
        for row in self.cleaned.collect():
            assert row["email"] == row["email"].lower(), f"Email not lowercase: {row['email']}"
    
    def test_phones_are_digits_only(self):
        """Phone numbers should contain only digits."""
        for row in self.cleaned.collect():
            assert row["phone"].isdigit(), f"Phone has non-digits: {row['phone']}"


class TestCalculateTotalRevenue(NotebookTestFixture):
    """Test the calculate_total_revenue function."""
    
    def run_setup(self):
        """Create test transactions."""
        self.transactions = spark.createDataFrame([
            (1, 100.0),
            (2, 200.0),
            (3, 150.0),
        ], ["id", "amount"])
    
    def test_correct_total(self):
        """Should calculate correct total."""
        total = calculate_total_revenue(self.transactions)
        assert total == 450.0, f"Expected 450.0, got {total}"
    
    def test_handles_empty_dataframe(self):
        """Should handle empty dataframe."""
        empty_df = spark.createDataFrame([], ["id", "amount"])
        total = calculate_total_revenue(empty_df)
        assert total is None or total == 0, "Empty dataframe should return 0 or None"
```

### Step 3: Run Your Tests

#### Option A: CLI (Local)

```bash
cd my_databricks_project
dbx-test run --local --tests-dir tests
```

#### Option B: CLI (Remote)

```bash
dbx-test run --remote --tests-dir tests --profile dev
```

#### Option C: In Databricks Notebook

```python
# Cell 1: Setup paths
import sys
sys.path.insert(0, "/Workspace/Repos/my-repo/my_databricks_project/src")

# Cell 2: Install framework
%pip install /dbfs/FileStore/wheels/databricks_notebook_test_framework-0.1.0-py3-none-any.whl

# Cell 3: Import and test
from databricks_notebook_test_framework import NotebookTestFixture, run_notebook_tests
from data_processing.transformations import clean_customer_data

class TestMyCode(NotebookTestFixture):
    def run_setup(self):
        self.raw = spark.createDataFrame([(1, "  Alice  ")], ["id", "name"])
        self.cleaned = clean_customer_data(self.raw)
    
    def test_name_trimmed(self):
        row = self.cleaned.collect()[0]
        assert row["name"] == "ALICE"

run_notebook_tests()
```

## 🎨 More Complex Example

### Application Code with Multiple Modules

**File: `src/data_processing/validators.py`**

```python
"""Data validation functions."""

def validate_schema(df, required_columns):
    """Validate dataframe has required columns."""
    actual = set(df.columns)
    required = set(required_columns)
    missing = required - actual
    
    return {
        "valid": len(missing) == 0,
        "missing": list(missing)
    }


def validate_no_nulls(df, columns):
    """Validate columns have no nulls."""
    null_counts = {}
    for col in columns:
        count = df.filter(f"{col} IS NULL").count()
        if count > 0:
            null_counts[col] = count
    
    return {
        "valid": len(null_counts) == 0,
        "null_counts": null_counts
    }
```

**File: `tests/test_validators_test.py`**

```python
"""Tests for validators module."""

import sys
from pathlib import Path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from databricks_notebook_test_framework import NotebookTestFixture
from data_processing.validators import validate_schema, validate_no_nulls


class TestValidateSchema(NotebookTestFixture):
    """Test schema validation."""
    
    def run_setup(self):
        self.df = spark.createDataFrame(
            [(1, "Alice", "alice@example.com")],
            ["id", "name", "email"]
        )
    
    def test_valid_schema(self):
        """Should pass with all required columns."""
        result = validate_schema(self.df, ["id", "name", "email"])
        assert result["valid"] is True
        assert len(result["missing"]) == 0
    
    def test_detects_missing_columns(self):
        """Should detect missing columns."""
        result = validate_schema(self.df, ["id", "name", "email", "phone"])
        assert result["valid"] is False
        assert "phone" in result["missing"]


class TestValidateNoNulls(NotebookTestFixture):
    """Test null validation."""
    
    def run_setup(self):
        self.df = spark.createDataFrame([
            (1, "Alice", "alice@example.com"),
            (2, None, "bob@example.com"),
        ], ["id", "name", "email"])
    
    def test_detects_nulls(self):
        """Should detect null values."""
        result = validate_no_nulls(self.df, ["name", "email"])
        assert result["valid"] is False
        assert "name" in result["null_counts"]
        assert result["null_counts"]["name"] == 1
    
    def test_passes_without_nulls(self):
        """Should pass when no nulls."""
        result = validate_no_nulls(self.df, ["id"])
        assert result["valid"] is True
```

## 🚀 Running the Tests

### Discover Tests

```bash
$ dbx-test discover --tests-dir tests

Discovered test notebooks:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┓
┃ Notebook                   ┃ Classes┃ Tests ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━┩
│ test_transformations_test  │ 2      │ 5     │
│ test_validators_test       │ 2      │ 4     │
└────────────────────────────┴────────┴───────┘
```

### Run Tests

```bash
$ dbx-test run --local --tests-dir tests

============================================================
Running TestCleanCustomerData
============================================================

Running test_names_are_uppercase...
  ✓ PASSED
Running test_emails_are_lowercase...
  ✓ PASSED
Running test_phones_are_digits_only...
  ✓ PASSED

============================================================
Running TestCalculateTotalRevenue
============================================================

Running test_correct_total...
  ✓ PASSED
Running test_handles_empty_dataframe...
  ✓ PASSED

============================================================
SUMMARY
============================================================
Total Tests: 9
✓ Passed: 9
✗ Failed: 0
✗ Errors: 0

🎉 All tests passed!
============================================================
```

## 💡 Best Practices

### 1. Create a Test Helper

**File: `tests/test_helpers.py`**

```python
"""Helper functions for tests."""

import sys
from pathlib import Path


def setup_src_path():
    """Add src directory to Python path."""
    src_path = Path(__file__).parent.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
```

**Use in tests:**

```python
from test_helpers import setup_src_path
setup_src_path()

from data_processing.transformations import clean_customer_data
```

### 2. Use Shared Base Classes

**File: `tests/base_test.py`**

```python
"""Base test classes."""

from databricks_notebook_test_framework import NotebookTestFixture


class BaseDataTest(NotebookTestFixture):
    """Base class for data tests with common setup."""
    
    def run_setup(self):
        """Create test database."""
        self.test_db = "test_database"
        spark.sql(f"CREATE DATABASE IF NOT EXISTS {self.test_db}")
        spark.sql(f"USE {self.test_db}")
    
    def run_cleanup(self):
        """Drop test database."""
        spark.sql(f"DROP DATABASE IF EXISTS {self.test_db} CASCADE")
```

**Use in tests:**

```python
from base_test import BaseDataTest

class TestMyFeature(BaseDataTest):
    # Automatically gets test database setup/cleanup
    pass
```

### 3. Keep Tests Focused

```python
# Good: One assertion per test
def test_name_is_uppercase(self):
    assert row["name"] == row["name"].upper()

def test_name_is_trimmed(self):
    assert row["name"] == row["name"].strip()

# Bad: Multiple assertions
def test_name(self):
    assert row["name"] == row["name"].upper()
    assert row["name"] == row["name"].strip()
    assert len(row["name"]) > 0
```

## 📚 Full Documentation

See the complete guide: **[docs/testing_application_code.md](../docs/testing_application_code.md)**

Includes:
- Detailed examples with validators, aggregations
- Advanced patterns
- Databricks notebook integration
- CI/CD setup
- Troubleshooting

## 🔗 Working Example

See the working example in: **[examples/src_code_example/](../examples/src_code_example/)**

```bash
# Try it yourself
cd examples/src_code_example
dbx-test run --local --tests-dir tests
```

## 📝 Summary

1. **Add src/ to path** in test files
2. **Import your functions** from src/
3. **Write tests** using `NotebookTestFixture`
4. **Run tests** with `dbx-test` CLI or in notebooks

That's it! You can now test any Python code in your Databricks projects! 🎉

