# Example: Testing Application Code from src/

This example demonstrates how to test application code in `src/` from tests in `tests/`.

## Project Structure

```
src_code_example/
├── src/
│   └── transformations.py    # Your application code
└── tests/
    └── test_transformations_test.py   # Tests for your code
```

## Files

- **`src/transformations.py`** - Example data transformation functions
- **`tests/test_transformations_test.py`** - Tests for those functions

## How It Works

The test file adds the `src/` directory to Python's path:

```python
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Now you can import from src/
from transformations import clean_customer_data
```

## Running the Tests

### Local

```bash
cd /path/to/databricks_notebooks_test_framework
dbx-test run --local --tests-dir examples/src_code_example/tests
```

### Remote

```bash
dbx-test run --remote --tests-dir examples/src_code_example/tests --profile dev
```

## Key Points

1. **Path Management**: Tests add `src/` to Python path
2. **Import Pattern**: Import functions/classes from your modules
3. **Test Pattern**: Use `NotebookTestFixture` as usual
4. **Separation**: Keep application code separate from test code

## See Also

- Full documentation: `docs/testing_application_code.md`
- More examples with validators, aggregations, etc.

