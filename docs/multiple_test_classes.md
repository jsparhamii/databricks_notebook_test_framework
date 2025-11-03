# Running Multiple Test Classes

The framework now supports running multiple test classes in a single call!

## Usage

### Run a Single Test Class

```python
from dbx_test import NotebookTestFixture, run_notebook_tests
import json

class TestMyFirstTest(NotebookTestFixture):
    def test_example(self):
        assert 1 + 1 == 2

# Run just this one class
results = run_notebook_tests(TestMyFirstTest)
dbutils.notebook.exit(json.dumps(results))
```

### Run Multiple Test Classes

```python
from dbx_test import NotebookTestFixture, run_notebook_tests
import json

class TestMyFirstTest(NotebookTestFixture):
    def test_addition(self):
        assert 1 + 1 == 2

class TestMySecondTest(NotebookTestFixture):
    def test_subtraction(self):
        assert 2 - 1 == 1

class TestMyThirdTest(NotebookTestFixture):
    def test_multiplication(self):
        assert 2 * 3 == 6

# Run multiple test classes
results = run_notebook_tests([TestMyFirstTest, TestMySecondTest, TestMyThirdTest])
dbutils.notebook.exit(json.dumps(results))
```

### Run All Test Classes (Auto-Discovery)

```python
from dbx_test import NotebookTestFixture, run_notebook_tests
import json

class TestMyFirstTest(NotebookTestFixture):
    def test_one(self):
        assert True

class TestMySecondTest(NotebookTestFixture):
    def test_two(self):
        assert True

# Auto-discover and run all classes
results = run_notebook_tests()
dbutils.notebook.exit(json.dumps(results))
```

## Complete Example

Here's a complete notebook with multiple test classes:

```python
# Databricks notebook source

from dbx_test import NotebookTestFixture, run_notebook_tests
import json

# COMMAND ----------

# Test Class 1: Data Validation
class TestDataValidation(NotebookTestFixture):
    def run_setup(self):
        self.df = spark.createDataFrame([
            (1, "Alice", 100),
            (2, "Bob", 200),
        ], ["id", "name", "amount"])
    
    def test_row_count(self):
        assert self.df.count() == 2, "Expected 2 rows"
    
    def test_columns(self):
        assert set(self.df.columns) == {"id", "name", "amount"}

# COMMAND ----------

# Test Class 2: Transformations
class TestTransformations(NotebookTestFixture):
    def run_setup(self):
        self.df = spark.createDataFrame([(1, 10), (2, 20)], ["id", "value"])
    
    def test_sum(self):
        total = self.df.selectExpr("sum(value) as total").collect()[0]["total"]
        assert total == 30
    
    def test_count(self):
        assert self.df.count() == 2

# COMMAND ----------

# Test Class 3: Aggregations
class TestAggregations(NotebookTestFixture):
    def run_setup(self):
        self.df = spark.createDataFrame([
            ("A", 100),
            ("A", 200),
            ("B", 150),
        ], ["group", "value"])
    
    def test_group_count(self):
        result = self.df.groupBy("group").count()
        assert result.count() == 2, "Expected 2 groups"
    
    def test_sum_by_group(self):
        result = self.df.groupBy("group").sum("value")
        a_sum = result.filter("group = 'A'").collect()[0]["sum(value)"]
        assert a_sum == 300

# COMMAND ----------

# Run all three test classes
results = run_notebook_tests([TestDataValidation, TestTransformations, TestAggregations])

# COMMAND ----------

# Return results to CLI
dbutils.notebook.exit(json.dumps(results))
```

## Output Structure

The results include all fixtures:

```json
{
  "total": 7,
  "passed": 7,
  "failed": 0,
  "errors": 0,
  "fixtures": [
    {
      "fixture_name": "TestDataValidation",
      "summary": {
        "total": 2,
        "passed": 2,
        "failed": 0,
        "errors": 0,
        "results": [
          {"name": "test_row_count", "status": "passed", "duration": 0.12},
          {"name": "test_columns", "status": "passed", "duration": 0.08}
        ]
      }
    },
    {
      "fixture_name": "TestTransformations",
      "summary": {
        "total": 2,
        "passed": 2,
        "failed": 0,
        "errors": 0,
        "results": [
          {"name": "test_sum", "status": "passed", "duration": 0.15},
          {"name": "test_count", "status": "passed", "duration": 0.05}
        ]
      }
    },
    {
      "fixture_name": "TestAggregations",
      "summary": {
        "total": 3,
        "passed": 3,
        "failed": 0,
        "errors": 0,
        "results": [
          {"name": "test_group_count", "status": "passed", "duration": 0.18},
          {"name": "test_sum_by_group", "status": "passed", "duration": 0.22}
        ]
      }
    }
  ]
}
```

## CLI Output

When running from the CLI with `--workspace-tests`:

```
test_multiple_classes: 7 test(s)
  ✓ TestDataValidation.test_row_count (0.12s)
  ✓ TestDataValidation.test_columns (0.08s)
  ✓ TestTransformations.test_sum (0.15s)
  ✓ TestTransformations.test_count (0.05s)
  ✓ TestAggregations.test_group_count (0.18s)
  ✓ TestAggregations.test_sum_by_group (0.22s)

Test Execution Summary:
Total: 7, Passed: 7, Failed: 0

🎉 All tests passed!
```

## Benefits

1. **Organized Tests** - Group related tests into separate classes
2. **Selective Execution** - Run only the classes you need
3. **Better Organization** - Logical separation of test concerns
4. **Flexible** - Mix and match test classes as needed
5. **Clear Results** - Results grouped by fixture for easy debugging

## Use Cases

### Organize by Feature

```python
results = run_notebook_tests([
    TestDataIngestion,
    TestDataTransformation,
    TestDataValidation,
    TestDataOutput
])
```

### Organize by Layer

```python
results = run_notebook_tests([
    TestBronzeLayer,
    TestSilverLayer,
    TestGoldLayer
])
```

### Organize by Type

```python
results = run_notebook_tests([
    TestUnitTests,
    TestIntegrationTests,
    TestDataQualityTests
])
```

## Tips

1. **Keep classes focused** - Each test class should test one aspect
2. **Use descriptive names** - Class names should indicate what they test
3. **Independent classes** - Each class should be able to run independently
4. **Share setup wisely** - Use `run_setup()` for class-specific setup
5. **Clean up** - Implement `run_cleanup()` in each class

## Comparison

### Before (Single Class Only)

```python
# Had to put all tests in one class
class TestEverything(NotebookTestFixture):
    def test_data_validation(self):
        ...
    def test_transformation(self):
        ...
    def test_aggregation(self):
        ...

results = run_notebook_tests(TestEverything)
```

### After (Multiple Classes)

```python
# Organized into logical groups
class TestDataValidation(NotebookTestFixture):
    def test_row_count(self):
        ...

class TestTransformations(NotebookTestFixture):
    def test_sum(self):
        ...

class TestAggregations(NotebookTestFixture):
    def test_group_count(self):
        ...

# Run all or specific classes
results = run_notebook_tests([TestDataValidation, TestTransformations, TestAggregations])
```

Much cleaner and more maintainable! 🎉

