# Test Result Formats

The framework now supports **two different JSON result formats** from notebooks, depending on how you call `run_notebook_tests()`.

## Format 1: Auto-Discovery (Recommended)

### Notebook Code
```python
from databricks_notebook_test_framework import NotebookTestFixture, run_notebook_tests
import json

class TestMyFirstTest(NotebookTestFixture):
    def test_row_count(self):
        assert True
    
    def test_sum_column(self):
        assert True

# Auto-discover all test classes in the notebook
results = run_notebook_tests()
dbutils.notebook.exit(json.dumps(results))
```

### JSON Output Structure
```json
{
  "total": 2,
  "passed": 2,
  "failed": 0,
  "errors": 0,
  "fixtures": [
    {
      "fixture_name": "TestMyFirstTest",
      "summary": {
        "total": 2,
        "passed": 2,
        "failed": 0,
        "errors": 0,
        "results": [
          {
            "name": "test_row_count",
            "status": "passed",
            "duration": 0.213,
            "error_message": null,
            "error_traceback": null
          },
          {
            "name": "test_sum_column",
            "status": "passed",
            "duration": 0.217,
            "error_message": null,
            "error_traceback": null
          }
        ]
      }
    }
  ]
}
```

### CLI Output
```
test_example:
  ✓ TestMyFirstTest.test_row_count (0.21s)
  ✓ TestMyFirstTest.test_sum_column (0.22s)

Test Execution Summary:
Total: 2, Passed: 2, Failed: 0
```

## Format 2: Specific Test Class

### Notebook Code
```python
from databricks_notebook_test_framework import NotebookTestFixture, run_notebook_tests
import json

class TestMyFirstTest(NotebookTestFixture):
    def test_row_count(self):
        assert True
    
    def test_sum_column(self):
        assert True

# Run only this specific test class
results = run_notebook_tests(TestMyFirstTest)
dbutils.notebook.exit(json.dumps(results))
```

### JSON Output Structure
```json
{
  "total": 2,
  "passed": 2,
  "failed": 0,
  "errors": 0,
  "results": [
    {
      "name": "test_row_count",
      "status": "passed",
      "duration": 0.213,
      "error_message": null,
      "error_traceback": null
    },
    {
      "name": "test_sum_column",
      "status": "passed",
      "duration": 0.217,
      "error_message": null,
      "error_traceback": null
    }
  ]
}
```

### CLI Output
```
test_example:
  ✓ test_row_count (0.21s)
  ✓ test_sum_column (0.22s)

Test Execution Summary:
Total: 2, Passed: 2, Failed: 0
```

## Key Differences

| Aspect | Auto-Discovery | Specific Class |
|--------|---------------|----------------|
| **Notebook Call** | `run_notebook_tests()` | `run_notebook_tests(TestClass)` |
| **JSON Structure** | Has `"fixtures"` key | Has `"results"` key at top level |
| **Test Names** | Include class name (e.g., `TestMyFirstTest.test_row_count`) | Just method name (e.g., `test_row_count`) |
| **Multiple Classes** | Supports multiple test classes | Only runs the specified class |
| **Use Case** | Standard workflow, CI/CD | Quick testing, debugging single class |

## Failed Test Example

### Your Actual Output
```json
{
  "total": 3,
  "passed": 2,
  "failed": 1,
  "errors": 0,
  "results": [
    {
      "name": "test_row_count",
      "status": "passed",
      "duration": 0.213,
      "error_message": null,
      "error_traceback": null
    },
    {
      "name": "test_sum_column",
      "status": "passed",
      "duration": 0.217,
      "error_message": null,
      "error_traceback": null
    },
    {
      "name": "test_total_amount",
      "status": "failed",
      "duration": 0.141,
      "error_message": "Expected 300, got 301",
      "error_traceback": "Traceback (most recent call last):\n  File \"/local_disk0/.ephemeral_nfs/envs/pythonEnv-34bd5766-3f20-41b8-ae3e-cd2cecebecc2/lib/python3.12/site-packages/databricks_notebook_test_framework/testing.py\", line 119, in _execute_test\n    test_method()\n  File \"/home/spark-34bd5766-3f20-41b8-ae3e-cd/.ipykernel/4442/command-8197133219891574-1925392434\", line 31, in test_total_amount\n    assert total == 300, f\"Expected 300, got {total}\"\n           ^^^^^^^^^^^^\nAssertionError: Expected 300, got 301\n"
    }
  ]
}
```

### Expected CLI Output (After Fix)
```
test_example:
  ✓ test_row_count (0.21s)
  ✓ test_sum_column (0.22s)
  ✗ test_total_amount (0.14s)
    Error: Expected 300, got 301

Test Execution Summary:
Total: 3, Passed: 2, Failed: 1

❌ Some tests failed
```

## Parser Update

The CLI parser (`runner_remote.py`) now handles both formats:

```python
# Format 1: Auto-discovery with fixtures
if "fixtures" in results_dict:
    for fixture in results_dict["fixtures"]:
        fixture_name = fixture.get("fixture_name", "Unknown")
        test_results = fixture["summary"]["results"]
        # Include class name in test name
        for test in test_results:
            name = f"{fixture_name}.{test['name']}"
            # ...

# Format 2: Specific class with flat results
elif "results" in results_dict:
    test_results = results_dict["results"]
    # Use test name as-is
    for test in test_results:
        name = test["name"]
        # ...
```

## Recommendation

Use **Format 1 (Auto-Discovery)** for most cases:
```python
results = run_notebook_tests()
dbutils.notebook.exit(json.dumps(results))
```

This is more flexible and works better with multiple test classes in a single notebook.

Use **Format 2 (Specific Class)** only when:
- Debugging a single test class
- You have multiple classes but only want to run one
- You need simpler test names without class prefixes

