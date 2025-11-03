# Quick Start Guide

Get started with the Databricks Notebook Test Framework in 5 minutes.

## Prerequisites

- Python 3.10+
- Databricks workspace (for remote testing)
- 5 minutes ⏱️

## Step 1: Install (30 seconds)

```bash
# Clone or download the repository
git clone https://github.com/yourusername/dbx_test.git
cd dbx_test

# Install
pip install -e .
```

## Step 2: Create Your First Test (2 minutes)

```bash
# Create tests directory
mkdir tests

# Generate test scaffold
dbx_test scaffold my_first_test
```

This creates `tests/my_first_test_test.py`. Edit it:

```python
from dbx_test import NotebookTestFixture


class TestMyFirstTest(NotebookTestFixture):
    def run_setup(self):
        """Create test data."""
        self.df = spark.createDataFrame([
            (1, "Alice", 100),
            (2, "Bob", 200),
        ], ["id", "name", "amount"])
        self.df.createOrReplaceTempView("test_data")
    
    def test_row_count(self):
        """Test we have 2 rows."""
        result = spark.sql("SELECT * FROM test_data")
        assert result.count() == 2, "Expected 2 rows"
    
    def test_total_amount(self):
        """Test total amount is 300."""
        result = spark.sql("SELECT SUM(amount) as total FROM test_data")
        total = result.collect()[0]["total"]
        assert total == 300, f"Expected 300, got {total}"
    
    def run_cleanup(self):
        """Clean up."""
        spark.sql("DROP VIEW IF EXISTS test_data")
```

## Step 3: Run Locally (1 minute)

```bash
# Run your test locally (requires PySpark for local testing)
pip install pyspark

# Run the test
dbx_test run --local --tests-dir tests
```

You'll see output like:

```
Discovered 1 test notebook(s)
Running tests locally...

╭─────────────────────────────────────╮
│ Databricks Notebook Test Results   │
╰─────────────────────────────────────╯

╭─────────── Summary ───────────╮
│ Total: 2  Passed: 2  Failed: 0 │
╰───────────────────────────────╯

✓ All tests passed!
```

## Step 4: Configure Remote Testing (1 minute)

Configure Databricks CLI:

```bash
# Install and configure Databricks CLI
pip install databricks-cli
databricks configure --token
```

Or create `config/test_config.yml`:

```yaml
workspace:
  profile: "DEFAULT"  # Uses Databricks CLI profile

cluster:
  cluster_id: "your-cluster-id"  # Or leave empty for serverless
  
reporting:
  output_dir: ".dbx_test-results"
  formats: ["console", "junit"]
```

## Step 5: Run on Databricks (30 seconds)

```bash
# Run remotely using Databricks CLI authentication
dbx_test run --remote --tests-dir /Workspace/Users/user@email.com/project/tests

# Or specify a profile
dbx_test run --remote --profile dev \
  --tests-dir /Workspace/Users/user@email.com/project/tests

# With multiple output formats
dbx_test run --remote \
  --tests-dir /Workspace/Users/user@email.com/project/tests \
  --output-format console \
  --output-format junit \
  --output-format json
```

## What's Next?

### Learn More

- **Writing Tests**: Read the [Writing Tests Guide](docs/writing_tests.md)
- **Configuration**: See [Configuration Guide](docs/configuration.md)
- **CI/CD**: Set up [CI/CD Integration](docs/ci_cd_integration.md)

### Try More Examples

```bash
# Discover all tests (pytest-style: test_* and *_test)
dbx_test discover --tests-dir tests

# Generate HTML report (local tests)
dbx_test run --local --tests-dir tests --output-format html

# Run tests in parallel (remote)
dbx_test run --remote --parallel \
  --tests-dir /Workspace/Users/user@email.com/project/tests

# Verbose output
dbx_test run --remote --verbose \
  --tests-dir /Workspace/Users/user@email.com/project/tests

# Run workspace tests (tests already in Databricks)
dbx_test run --remote --workspace-tests \
  --tests-dir /Workspace/Users/user@email.com/project/tests
```

### Create More Tests

```bash
# Generate more test scaffolds
dbx_test scaffold customer_analysis
dbx_test scaffold sales_pipeline
dbx_test scaffold data_quality
```

## Common Commands

```bash
# Local testing (from local tests/ directory)
dbx_test run --local --tests-dir tests

# Remote testing (from workspace)
dbx_test run --remote \
  --tests-dir /Workspace/Users/user@email.com/project/tests

# With specific profile
dbx_test run --remote --profile prod \
  --tests-dir /Workspace/Users/user@email.com/project/tests

# Workspace tests (tests already in Databricks)
dbx_test run --remote --workspace-tests --profile dev \
  --tests-dir /Workspace/Users/user@email.com/project/tests

# Discover tests (local)
dbx_test discover --tests-dir tests

# Multiple output formats
dbx_test run --remote \
  --tests-dir /Workspace/Users/user@email.com/project/tests \
  --output-format console \
  --output-format junit \
  --output-format json \
  --output-format html

# Upload notebooks to workspace
dbx_test upload --tests-dir tests \
  --workspace-path /Workspace/Users/user@email.com/project/tests \
  --profile dev

# Create new test
dbx_test scaffold my_test

# Help
dbx_test --help
dbx_test run --help
```

## Troubleshooting

### "Command not found: dbx_test"

```bash
# Reinstall
pip install -e .
```

### "Cannot connect to Databricks"

```bash
# Check Databricks CLI configuration
databricks workspace list

# Or set environment variables
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-token"

# Verify config
cat config/test_config.yml
```

### "No module named 'pyspark'"

```bash
# For local testing only
pip install pyspark
```

## Example Project Structure

```
my-databricks-project/
├── notebooks/              # Your production notebooks
│   ├── etl_pipeline.py
│   └── analytics.py
├── tests/                  # Test notebooks
│   ├── etl_pipeline_test.py
│   └── analytics_test.py
├── config/                 # Test configuration
│   └── test_config.yml
├── .dbx_test-results/     # Test results (gitignored)
└── pyproject.toml         # Project config
```

## Best Practices

1. **Keep tests independent** - Each test should work standalone
2. **Use descriptive names** - `test_customer_count_matches_expected` not `test1`
3. **Clean up resources** - Always implement `run_cleanup()`
4. **Test one thing** - Each test method should test one specific behavior
5. **Use assertions with messages** - `assert x == y, "Clear message"`

## Real-World Example

Here's a complete real-world test:

```python
from dbx_test import NotebookTestFixture


class TestCustomerETL(NotebookTestFixture):
    """Test customer ETL pipeline."""
    
    def run_setup(self):
        """Create test customers."""
        from pyspark.sql import SparkSession
        
        # Get or create spark session (for local testing)
        self.spark = SparkSession.builder \
            .appName("TestCustomerETL") \
            .master("local[*]") \
            .getOrCreate()
        
        # Bronze layer (raw data)
        self.raw_customers = self.spark.createDataFrame([
            (1, "alice@email.com", "2024-01-01", "active"),
            (2, "bob@email.com", "2024-01-02", "active"),
            (3, "charlie@email.com", "2024-01-03", "inactive"),
        ], ["id", "email", "signup_date", "status"])
        
        self.raw_customers.write.format("delta")\
            .mode("overwrite")\
            .saveAsTable("test_bronze_customers")
        
        # Run transformation (your actual ETL code)
        self.spark.sql("""
            CREATE OR REPLACE TABLE test_silver_customers AS
            SELECT 
                id,
                LOWER(email) as email,
                signup_date,
                status,
                CASE 
                    WHEN status = 'active' THEN 1 
                    ELSE 0 
                END as is_active
            FROM test_bronze_customers
        """)
    
    def test_all_customers_loaded(self):
        """All customers should be in silver table."""
        bronze_count = self.spark.table("test_bronze_customers").count()
        silver_count = self.spark.table("test_silver_customers").count()
        assert bronze_count == silver_count, "Row count mismatch"
    
    def test_emails_normalized(self):
        """Emails should be lowercase."""
        silver = self.spark.table("test_silver_customers")
        uppercase_emails = silver.filter("email != LOWER(email)").count()
        assert uppercase_emails == 0, "Found non-lowercase emails"
    
    def test_active_flag_correct(self):
        """is_active flag should match status."""
        incorrect = self.spark.sql("""
            SELECT * FROM test_silver_customers
            WHERE (status = 'active' AND is_active != 1)
               OR (status != 'active' AND is_active != 0)
        """).count()
        assert incorrect == 0, "is_active flag incorrect"
    
    def test_no_null_emails(self):
        """Email should never be null."""
        null_emails = self.spark.sql("""
            SELECT * FROM test_silver_customers WHERE email IS NULL
        """).count()
        assert null_emails == 0, "Found null emails"
    
    def run_cleanup(self):
        """Clean up test tables."""
        self.spark.sql("DROP TABLE IF EXISTS test_bronze_customers")
        self.spark.sql("DROP TABLE IF EXISTS test_silver_customers")
        self.spark.stop()
```

Run it:

```bash
# Run locally
dbx_test run --local --tests-dir tests

# Or run remotely on Databricks
dbx_test run --remote --profile dev \
  --tests-dir /Workspace/Users/user@email.com/project/tests
```

## Success! 🎉

You now have a working test framework! Continue learning:

- [Full Documentation](docs/)
- [Example Tests](tests/)
- [Contributing Guide](CONTRIBUTING.md)

## Get Help

- Check the [documentation](docs/)
- Open an issue on GitHub
- Read the [FAQ](docs/faq.md)

Happy testing! 🚀

