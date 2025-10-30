# Running Tests from Databricks Workspace

## Overview

You can now run tests that are already in your Databricks workspace without uploading them locally. This is useful when:
- Your tests are developed directly in Databricks
- Tests are part of a Databricks Repos integration
- You want to run tests that are already deployed to the workspace

## Command

```bash
dbx-test run --remote --workspace-tests --profile <profile> --tests-dir "<workspace_path>"
```

### Parameters

- `--remote` - Required: Run tests remotely on Databricks
- `--workspace-tests` - **New Flag**: Tells the framework tests are already in workspace (don't upload)
- `--profile <profile>` - Databricks CLI profile to use (e.g., `adb`, `dev`, `prod`)
- `--tests-dir "<workspace_path>"` - Workspace path where your tests are located
- `--pattern` - Optional: Pattern to match test files (default: `**/*_test.py`)
- `--verbose` - Optional: Show detailed output

## Examples

### Example 1: Run All Tests in a Workspace Directory

```bash
dbx-test run --remote --workspace-tests \
  --profile adb \
  --tests-dir "/Workspace/Users/james.parham@databricks.com/dbx_test" \
  --verbose
```

### Example 2: Run Tests with Custom Pattern

```bash
dbx-test run --remote --workspace-tests \
  --profile prod \
  --tests-dir "/Workspace/Repos/my-repo/tests" \
  --pattern "*integration*" \
  --verbose
```

### Example 3: Run Tests in a Repos Folder

```bash
dbx-test run --remote --workspace-tests \
  --profile dev \
  --tests-dir "/Repos/Staging/my-project/tests"
```

## Notebook Naming Convention

By default, the framework looks for notebooks matching the pattern `**/*_test.py`. Your notebooks should be named like:
- `my_feature_test`
- `integration_test`
- `data_validation_test`

**Note**: Databricks notebooks don't show the `.py` extension in the UI, but the pattern matching handles this automatically.

## How It Works

1. **Discovery**: Lists all notebooks in the workspace directory matching the pattern
2. **Execution**: Runs each notebook directly on Databricks (no upload needed)
3. **Results**: Collects test results and generates reports

## Complete Workflow

### Step 1: Create Tests in Databricks

In your Databricks workspace at `/Workspace/Users/james.parham@databricks.com/dbx_test`:

```python
# Notebook: my_feature_test
from databricks_notebook_test_framework import NotebookTestFixture, run_notebook_tests

class TestMyFeature(NotebookTestFixture):
    def run_setup(self):
        self.df = spark.range(10)
    
    def test_count(self):
        assert self.df.count() == 10

# Run tests
run_notebook_tests()
```

### Step 2: Run from Command Line

```bash
dbx-test run --remote --workspace-tests \
  --profile adb \
  --tests-dir "/Workspace/Users/james.parham@databricks.com/dbx_test" \
  --verbose
```

### Step 3: View Results

The framework will:
- Discover your test notebooks
- Execute them on Databricks
- Generate JUnit XML reports in `.dbx-test-results/`
- Display results in console

## Troubleshooting

### "No test notebooks found"

**Possible causes:**
1. Directory is empty
2. Notebook names don't match the pattern

**Solution:**
- Check your workspace directory in Databricks UI
- Ensure notebooks end with `_test` (e.g., `my_test`, not `my_test.py`)
- Use custom pattern: `--pattern "*test*"`
- Use `--verbose` to see discovery details

### "Error accessing workspace tests"

**Possible causes:**
1. Workspace path doesn't exist
2. Authentication issue

**Solution:**
- Verify path: `databricks workspace list "/Workspace/Users/james.parham@databricks.com"`
- Check profile: `databricks configure --token --profile adb`

### "Permission denied"

**Solution:**
- Ensure your Databricks token has workspace read/execute permissions
- Check if you can access the folder in Databricks UI

## Comparison: Local vs Workspace Tests

| Feature | Local Tests (`--tests-dir tests`) | Workspace Tests (`--workspace-tests`) |
|---------|----------------------------------|--------------------------------------|
| **Location** | Local filesystem | Databricks workspace |
| **Upload** | Yes (uploads to workspace) | No (runs in place) |
| **Development** | Edit locally | Edit in Databricks |
| **Use Case** | CI/CD, local development | Databricks-native development |
| **Repos Integration** | Yes (upload to Repos) | Yes (run from Repos) |

## Configuration

Your `config/test_config.yml`:

```yaml
workspace:
  profile: "adb"  # Default profile (can be overridden with --profile)

cluster:
  # Use serverless (default) or existing cluster
  # cluster_id: "your-cluster-id"

execution:
  timeout: 600
  max_retries: 2

paths:
  workspace_root: "/Workspace/Users/james.parham@databricks.com/dbx_test"
  test_pattern: "**/*_test.py"

reporting:
  output_dir: ".dbx-test-results"
  formats:
    - "console"
    - "junit"
  verbose: true
```

## Best Practices

1. **Naming Convention**: Use `_test` suffix for test notebooks
2. **Organization**: Keep tests in dedicated workspace folders
3. **Repos**: Consider using Databricks Repos for version control
4. **Documentation**: Add README notebooks explaining test structure
5. **Isolation**: Use separate folders for different test suites

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Run Databricks Tests

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Install framework
        run: pip install databricks-notebook-test-framework
      
      - name: Configure Databricks CLI
        run: |
          databricks configure --token << EOF
          ${{ secrets.DATABRICKS_HOST }}
          ${{ secrets.DATABRICKS_TOKEN }}
          EOF
      
      - name: Run workspace tests
        run: |
          dbx-test run --remote --workspace-tests \
            --profile DEFAULT \
            --tests-dir "/Workspace/Repos/my-repo/tests"
```

## Next Steps

1. **Try it**: Run tests from your workspace
2. **Organize**: Structure your workspace tests
3. **Automate**: Set up CI/CD to run workspace tests
4. **Iterate**: Develop and test directly in Databricks

## Summary

The `--workspace-tests` flag enables you to:
- ✅ Run tests already in Databricks workspace
- ✅ Skip the upload step for faster execution
- ✅ Test Databricks Repos-based projects
- ✅ Develop and test entirely in Databricks UI
- ✅ Integrate with existing workspace structures

**Command to remember:**
```bash
dbx-test run --remote --workspace-tests --profile <profile> --tests-dir "<workspace_path>"
```

