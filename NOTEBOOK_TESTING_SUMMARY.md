# Databricks Notebook Testing - Feature Summary

## 🎉 What's New

You can now run tests **directly in Databricks notebooks** for interactive development! This complements the existing CLI-based testing workflow.

## ✅ What Was Added

### 1. New Module: `notebook_runner.py`

Location: `src/databricks_notebook_test_framework/notebook_runner.py`

**Main Features:**
- `run_notebook_tests()` - Simple one-liner to run tests
- `NotebookRunner` - Class for more control
- `quick_test()` - Returns True/False for pass/fail
- `install_notebook_package()` - Helper for installation

### 2. Complete Documentation

- **`docs/notebook_usage.md`** - Comprehensive guide with 5 real-world examples
- **`examples/notebook_test_example.py`** - Runnable Databricks notebook
- **`NOTEBOOK_FEATURE.md`** - Technical summary of the feature

### 3. Updated Files

- `src/databricks_notebook_test_framework/__init__.py` - Exports new functions
- `README.md` - Added notebook usage section
- Rebuilt wheel package (now 32 KB, includes `notebook_runner.py`)

## 🚀 Quick Usage

### In Your Databricks Notebook:

```python
# 1. Install the framework
%pip install /dbfs/FileStore/wheels/databricks_notebook_test_framework-0.1.0-py3-none-any.whl

# 2. Import
from databricks_notebook_test_framework import NotebookTestFixture, run_notebook_tests

# 3. Write tests
class TestMyData(NotebookTestFixture):
    def run_setup(self):
        self.df = spark.createDataFrame([(1, "Alice"), (2, "Bob")], ["id", "name"])
    
    def test_count(self):
        assert self.df.count() == 2, "Expected 2 rows"
    
    def test_columns(self):
        assert self.df.columns == ["id", "name"]
    
    def run_cleanup(self):
        # Clean up resources
        pass

# 4. Run tests
run_notebook_tests()
```

### Output:

```
============================================================
Running TestMyData
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

## 📦 Deployment

### Step 1: Upload Wheel to DBFS

```bash
# From your local machine
databricks fs cp dist/databricks_notebook_test_framework-0.1.0-py3-none-any.whl \
  dbfs:/FileStore/wheels/
```

### Step 2: Install in Notebook

```python
%pip install /dbfs/FileStore/wheels/databricks_notebook_test_framework-0.1.0-py3-none-any.whl
```

### Step 3: Use It!

```python
from databricks_notebook_test_framework import NotebookTestFixture, run_notebook_tests

# Write and run tests...
```

## 🎯 Use Cases

### Use Case 1: Interactive Development

```python
# Develop your data transformation
df = spark.read.table("customers")
transformed = df.filter("age > 18")

# Test it immediately
class TestTransform(NotebookTestFixture):
    def test_adult_filter(self):
        assert transformed.filter("age <= 18").count() == 0

run_notebook_tests()
```

### Use Case 2: Data Quality Checks

```python
class TestDataQuality(NotebookTestFixture):
    def run_setup(self):
        self.df = spark.table("production_data")
    
    def test_no_nulls(self):
        for col in self.df.columns:
            nulls = self.df.filter(f"{col} IS NULL").count()
            assert nulls == 0, f"Column {col} has {nulls} nulls"

run_notebook_tests()
```

### Use Case 3: Conditional Workflows

```python
# Run tests
results = run_notebook_tests()

# Trigger based on results
if results['failed'] == 0:
    dbutils.notebook.run("production_pipeline", timeout_seconds=3600)
else:
    raise Exception("Tests failed - stopping workflow")
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[docs/notebook_usage.md](docs/notebook_usage.md)** | Complete guide with examples |
| **[examples/notebook_test_example.py](examples/notebook_test_example.py)** | Runnable example notebook |
| **[NOTEBOOK_FEATURE.md](NOTEBOOK_FEATURE.md)** | Technical feature summary |
| **[README.md](README.md)** | Updated with notebook section |

## 🔄 Workflow: Development to Production

```
┌─────────────────────────────────────────┐
│  Development (Databricks Notebook)      │
│                                         │
│  • Write tests interactively            │
│  • Use run_notebook_tests()            │
│  • Get immediate feedback              │
│  • Debug in notebook context           │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│  CI/CD Pipeline (Command Line)          │
│                                         │
│  • dbx-test run --remote               │
│  • Automated on every commit           │
│  • Generate JUnit XML reports          │
│  • Integrate with GitHub Actions       │
└─────────────────────────────────────────┘
```

## 🆚 CLI vs Notebook Comparison

| Feature | CLI (`dbx-test`) | Notebook (`run_notebook_tests`) |
|---------|-----------------|--------------------------------|
| **Use Case** | Automated CI/CD | Interactive development |
| **Setup** | Config file | No config needed |
| **Output** | JUnit XML, HTML | Console |
| **Execution** | Batch/scheduled | Immediate |
| **Discovery** | File-based | In-notebook |
| **Best For** | Production | Development |

## 🎨 Available Functions

### Simple (Recommended)

```python
from databricks_notebook_test_framework import run_notebook_tests

# Run all tests
run_notebook_tests()

# Run specific class
run_notebook_tests(TestMyFeature)
```

### Advanced

```python
from databricks_notebook_test_framework import NotebookRunner

runner = NotebookRunner(verbose=True)
results = runner.run()  # Returns dict with results
```

### Quick Boolean

```python
from databricks_notebook_test_framework import quick_test

passed = quick_test(TestMyFeature)
assert passed, "Tests failed!"
```

## 📋 Real-World Examples

### Example 1: ETL Validation

```python
class TestETL(NotebookTestFixture):
    def run_setup(self):
        # Create test data
        spark.sql("CREATE OR REPLACE TABLE test_bronze AS SELECT * FROM bronze")
        
        # Run ETL
        spark.sql("""
            CREATE OR REPLACE TABLE test_silver AS
            SELECT id, UPPER(name) as name FROM test_bronze
        """)
    
    def test_row_count(self):
        bronze = spark.table("test_bronze").count()
        silver = spark.table("test_silver").count()
        assert bronze == silver
    
    def test_names_uppercase(self):
        lowercase = spark.sql("""
            SELECT COUNT(*) as cnt FROM test_silver 
            WHERE name != UPPER(name)
        """).collect()[0]["cnt"]
        assert lowercase == 0
    
    def run_cleanup(self):
        spark.sql("DROP TABLE IF EXISTS test_bronze")
        spark.sql("DROP TABLE IF EXISTS test_silver")

run_notebook_tests()
```

### Example 2: Schema Validation

```python
class TestSchema(NotebookTestFixture):
    def test_required_columns(self):
        df = spark.table("my_table")
        required = {"id", "name", "email", "created_at"}
        actual = set(df.columns)
        missing = required - actual
        assert len(missing) == 0, f"Missing columns: {missing}"
    
    def test_data_types(self):
        df = spark.table("my_table")
        schema = {f.name: str(f.dataType) for f in df.schema.fields}
        assert "LongType" in schema["id"]
        assert "StringType" in schema["email"]

run_notebook_tests()
```

### Example 3: Business Rules

```python
class TestBusinessRules(NotebookTestFixture):
    def test_no_future_dates(self):
        from datetime import datetime
        df = spark.table("transactions")
        future = df.filter(f"transaction_date > '{datetime.now()}'").count()
        assert future == 0, f"Found {future} future-dated transactions"
    
    def test_positive_amounts(self):
        df = spark.table("transactions")
        negative = df.filter("amount < 0").count()
        assert negative == 0, f"Found {negative} negative amounts"

run_notebook_tests()
```

## 🔧 Installation Methods

### Method 1: DBFS (Recommended)

```bash
# Upload wheel
databricks fs cp dist/databricks_notebook_test_framework-0.1.0-py3-none-any.whl \
  dbfs:/FileStore/wheels/
```

In notebook:
```python
%pip install /dbfs/FileStore/wheels/databricks_notebook_test_framework-0.1.0-py3-none-any.whl
```

### Method 2: Helper Function

```python
from databricks_notebook_test_framework import install_notebook_package

install_notebook_package("/dbfs/FileStore/wheels/databricks_notebook_test_framework-0.1.0-py3-none-any.whl")
```

### Method 3: Cluster Library

1. Go to your cluster configuration
2. Libraries → Install New
3. Upload the wheel file
4. All notebooks on cluster will have access

## ✨ Key Benefits

1. **No Configuration** - No YAML files, no CLI setup
2. **Immediate Feedback** - See test results instantly
3. **Interactive** - Debug with full notebook context
4. **Flexible** - Run all tests or specific classes
5. **Production-Ready** - Same test code works with CLI
6. **Databricks Native** - Uses notebook's Spark session

## 🎓 Next Steps

1. **Try the Example**: Run `examples/notebook_test_example.py` in Databricks
2. **Read the Guide**: See `docs/notebook_usage.md` for detailed patterns
3. **Add Tests**: Start adding tests to your existing notebooks
4. **Automate**: Use CLI for CI/CD once tests are stable

## 📦 Package Info

- **Version**: 0.1.0
- **Wheel Size**: 32 KB
- **New Module**: `notebook_runner.py`
- **Python**: 3.10+
- **Dependencies**: Same as CLI (databricks-sdk, pyyaml, etc.)

## 🎉 Summary

You now have **two ways** to use the framework:

1. **CLI** (`dbx-test`) - For CI/CD and automation
2. **Notebook** (`run_notebook_tests()`) - For interactive development

Both use the same test code (`NotebookTestFixture`), so you can develop in notebooks and run in CI/CD without changes!

---

**Happy Testing! 🚀**

