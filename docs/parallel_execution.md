# Parallel Test Execution

Speed up your test runs by executing tests in parallel!

## Overview

The framework now supports running test methods within a test class in parallel using Python's `ThreadPoolExecutor`. This can significantly reduce test execution time when you have many independent tests.

## When to Use Parallel Execution

✅ **Good for:**
- Tests that are independent and don't share state
- I/O-bound tests (database queries, API calls, file operations)
- Tests that take a long time individually
- Large test suites with many tests

❌ **Not recommended for:**
- Tests that share mutable state
- Tests that need to run in a specific order
- Tests that have dependencies on each other
- Tests that modify global resources

## Usage

### Basic Usage

```python
from dbx_test import NotebookTestFixture, run_notebook_tests
import json

class TestMyData(NotebookTestFixture):
    def run_setup(self):
        # Setup runs once before all tests
        self.df = spark.createDataFrame([
            (1, "Alice", 100),
            (2, "Bob", 200),
            (3, "Charlie", 300),
        ], ["id", "name", "amount"])
    
    def test_row_count(self):
        assert self.df.count() == 3
    
    def test_sum_amount(self):
        total = self.df.selectExpr("sum(amount)").collect()[0][0]
        assert total == 600
    
    def test_distinct_names(self):
        names = self.df.select("name").distinct().count()
        assert names == 3
    
    def test_max_amount(self):
        max_amt = self.df.selectExpr("max(amount)").collect()[0][0]
        assert max_amt == 300

# Run tests in parallel
results = run_notebook_tests(TestMyData, parallel=True)
dbutils.notebook.exit(json.dumps(results))
```

### Control Number of Workers

```python
# Use specific number of workers
results = run_notebook_tests(
    TestMyData,
    parallel=True,
    max_workers=4  # Use 4 parallel threads
)

# Let Python decide (uses CPU count)
results = run_notebook_tests(
    TestMyData,
    parallel=True,
    max_workers=None  # Default: auto
)
```

### Multiple Test Classes with Parallel Execution

```python
class TestDataValidation(NotebookTestFixture):
    def test_schema(self):
        # Test implementation
        pass
    
    def test_nulls(self):
        # Test implementation
        pass

class TestTransformations(NotebookTestFixture):
    def test_aggregations(self):
        # Test implementation
        pass
    
    def test_filters(self):
        # Test implementation
        pass

# Run all test classes with parallel execution within each class
results = run_notebook_tests(
    [TestDataValidation, TestTransformations],
    parallel=True,
    max_workers=4
)
```

## How It Works

1. **Setup runs once** - `run_setup()` executes before any tests
2. **Tests run in parallel** - All test methods execute concurrently using ThreadPoolExecutor
3. **Cleanup runs once** - `run_cleanup()` executes after all tests complete
4. **Results are collected** - Test results are gathered as they complete
5. **Results are sorted** - Final results are sorted by test name for consistency

## Output Format

### Sequential Output
```
Running TestMyData
============================================================

Running test_distinct_names...
  ✓ PASSED
Running test_max_amount...
  ✓ PASSED
Running test_row_count...
  ✓ PASSED
Running test_sum_amount...
  ✓ PASSED
```

### Parallel Output
```
Running TestMyData
Parallel execution enabled (max_workers=4)
============================================================

Running 4 tests in parallel (max_workers=4)...
  ✓ test_row_count PASSED
  ✓ test_sum_amount PASSED
  ✓ test_max_amount PASSED
  ✓ test_distinct_names PASSED
```

## Performance Comparison

### Example: 10 Tests, Each Taking 2 Seconds

**Sequential:**
```
Total time: 20 seconds (10 tests × 2 seconds)
```

**Parallel (4 workers):**
```
Total time: ~5 seconds (10 tests ÷ 4 workers × 2 seconds)
```

**Speedup: 4x faster!** 🚀

## Advanced Examples

### Example 1: I/O-Bound Tests

```python
class TestDataIngestion(NotebookTestFixture):
    def run_setup(self):
        self.base_path = "/mnt/data/"
    
    def test_read_customers(self):
        df = spark.read.parquet(f"{self.base_path}/customers")
        assert df.count() > 0
    
    def test_read_orders(self):
        df = spark.read.parquet(f"{self.base_path}/orders")
        assert df.count() > 0
    
    def test_read_products(self):
        df = spark.read.parquet(f"{self.base_path}/products")
        assert df.count() > 0
    
    def test_read_inventory(self):
        df = spark.read.parquet(f"{self.base_path}/inventory")
        assert df.count() > 0

# These I/O-bound tests benefit greatly from parallelization
results = run_notebook_tests(TestDataIngestion, parallel=True)
```

### Example 2: Complex Validation Tests

```python
class TestDataQuality(NotebookTestFixture):
    def run_setup(self):
        self.df = spark.table("production.sales")
    
    def test_no_null_customer_ids(self):
        null_count = self.df.filter("customer_id IS NULL").count()
        assert null_count == 0
    
    def test_valid_dates(self):
        invalid = self.df.filter("sale_date > current_date()").count()
        assert invalid == 0
    
    def test_positive_amounts(self):
        negative = self.df.filter("amount <= 0").count()
        assert negative == 0
    
    def test_valid_status(self):
        valid_statuses = ['pending', 'completed', 'cancelled']
        invalid = self.df.filter(~col("status").isin(valid_statuses)).count()
        assert invalid == 0
    
    def test_unique_ids(self):
        total = self.df.count()
        unique = self.df.select("id").distinct().count()
        assert total == unique

# Run quality checks in parallel
results = run_notebook_tests(TestDataQuality, parallel=True, max_workers=5)
```

### Example 3: Using NotebookRunner Directly

```python
from dbx_test import NotebookRunner

# Create runner with parallel enabled
runner = NotebookRunner(
    verbose=True,
    parallel=True,
    max_workers=8
)

# Run specific test class
results = runner.run(TestMyData)

# Or run multiple classes
results = runner.run([TestClass1, TestClass2, TestClass3])
```

## Thread Safety Considerations

When using parallel execution, ensure your tests are thread-safe:

### ✅ Safe Practices

```python
class TestThreadSafe(NotebookTestFixture):
    def run_setup(self):
        # Read-only setup is safe
        self.df = spark.table("my_table")
        self.expected_count = 1000
    
    def test_count(self):
        # Reading shared state is safe
        assert self.df.count() == self.expected_count
    
    def test_schema(self):
        # Each test creates its own local variables
        columns = self.df.columns
        assert "id" in columns
```

### ❌ Unsafe Practices

```python
class TestNotThreadSafe(NotebookTestFixture):
    def run_setup(self):
        self.counter = 0  # Shared mutable state
    
    def test_one(self):
        self.counter += 1  # Race condition!
        assert self.counter == 1
    
    def test_two(self):
        self.counter += 1  # Race condition!
        assert self.counter == 2
```

## Best Practices

1. **Keep tests independent** - Each test should be able to run in isolation
2. **Avoid shared mutable state** - Don't modify instance variables during tests
3. **Use read-only setup** - Setup should prepare read-only data
4. **Start with sequential** - Test your suite sequentially first, then enable parallel
5. **Monitor performance** - Use parallel execution for suites with many tests
6. **Choose appropriate worker count** - Start with 4-8 workers and adjust based on results

## Troubleshooting

### Tests Pass Sequentially But Fail in Parallel

This usually indicates a threading issue:
- Check for shared mutable state
- Look for race conditions
- Ensure tests don't depend on execution order

### No Performance Improvement

If parallel execution doesn't speed things up:
- Tests may be CPU-bound (parallel helps with I/O-bound tests)
- Too few tests (overhead of parallelization may exceed benefits)
- Worker count may be too low or too high

### Intermittent Failures

Random failures suggest:
- Race conditions in your code
- Shared resources being modified
- Non-deterministic test logic

## Configuration Summary

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `parallel` | `bool` | `False` | Enable parallel execution |
| `max_workers` | `int` or `None` | `None` | Number of parallel threads (None = auto) |
| `verbose` | `bool` | `True` | Print detailed output |

## Examples by Use Case

### Fast Unit Tests
```python
# Sequential is fine for fast tests
results = run_notebook_tests(TestFastTests, parallel=False)
```

### Slow Integration Tests
```python
# Parallel helps with slow tests
results = run_notebook_tests(TestSlowTests, parallel=True, max_workers=4)
```

### Data Quality Checks
```python
# Parallel is ideal for independent quality checks
results = run_notebook_tests(TestDataQuality, parallel=True, max_workers=10)
```

### Mixed Test Suite
```python
# Run fast tests sequentially, slow tests in parallel
fast_results = run_notebook_tests(TestFast, parallel=False)
slow_results = run_notebook_tests(TestSlow, parallel=True, max_workers=8)
```

## Summary

✅ **Benefits:**
- Faster test execution (2-10x speedup typical)
- Better resource utilization
- Same API as sequential execution
- Automatic result collection and ordering

⚠️ **Requirements:**
- Tests must be independent
- No shared mutable state
- Thread-safe code

🚀 **Perfect for:**
- Large test suites
- I/O-bound tests
- Data validation pipelines
- Quality checks

Try it out and watch your test suite speed up! 🎉

