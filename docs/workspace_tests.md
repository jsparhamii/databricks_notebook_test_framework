# Running Tests from Databricks Workspace

## Overview

You can now run tests that are already in your Databricks workspace without uploading them locally. This is useful when:
- Your tests are developed directly in Databricks
- Tests are part of a Databricks Repos integration
- You want to run tests that are already deployed to the workspace

## Command

The framework automatically detects workspace paths (starting with `/Workspace/` or `/Repos/`), so you can simply run:

```bash
dbx_test run --remote --profile <profile> --tests-dir "<workspace_path>"
```

**Note**: The `--workspace-tests` flag is optional when using workspace paths. The framework auto-detects them!

### Parameters

- `--remote` - Required: Run tests remotely on Databricks
- `--workspace-tests` - Optional: Explicitly tell the framework tests are in workspace (auto-detected for /Workspace/ and /Repos/ paths)
- `--profile <profile>` - Databricks CLI profile to use (e.g., `adb`, `dev`, `prod`)
- `--tests-dir "<workspace_path>"` - Workspace path where your tests are located (must start with /Workspace/ or /Repos/)
- `--pattern` - Optional: Pattern to match test files (default: `test_*` or `*_test`)
- `--verbose` - Optional: Show detailed output

## Examples

### Example 1: Run All Tests in a Workspace Directory (Auto-Detection)

```bash
# The framework auto-detects the workspace path - no --workspace-tests needed!
dbx_test run --remote \
  --profile adb \
  --tests-dir "/Workspace/Users/james.parham@databricks.com/dbx_test" \
  --verbose
```

### Example 2: Run Tests in Databricks Repos

```bash
# Works with Repos paths too
dbx_test run --remote \
  --profile prod \
  --tests-dir "/Repos/my-repo/tests" \
  --verbose
```

### Example 3: Explicit Workspace Tests Flag (Optional)

```bash
# You can still use --workspace-tests explicitly if preferred
dbx_test run --remote --workspace-tests \
  --profile dev \
  --tests-dir "/Workspace/Repos/Staging/my-project/tests"
```

### Example 4: Running from Bundle Deployment Path

```bash
# Perfect for testing bundled applications
dbx_test run --remote \
  --profile aws-west \
  --tests-dir "/Workspace/Users/james.parham@databricks.com/.bundle/dbx_test_example/dev/files/src_code_example"
```

## Notebook Naming Convention

The framework automatically discovers notebooks matching pytest-style patterns:
- `test_*` (starts with test_)
- `*_test` (ends with _test)

Your notebooks should be named like:
- `test_my_feature`
- `my_feature_test`
- `test_integration`
- `integration_test`
- `data_validation_test`

**Note**: Databricks notebooks don't show the `.py` extension in the UI, but the discovery handles this automatically.

## How It Works

1. **Discovery**: Lists all notebooks in the workspace directory matching the pattern
2. **Execution**: Runs each notebook directly on Databricks (no upload needed)
3. **Results**: Collects test results and generates reports

## Complete Workflow

### Step 1: Create Tests in Databricks

In your Databricks workspace at `/Workspace/Users/james.parham@databricks.com/dbx_test`:

```python
# Notebook: my_feature_test
from dbx_test import NotebookTestFixture, run_notebook_tests

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
dbx_test run --remote --workspace-tests \
  --profile adb \
  --tests-dir "/Workspace/Users/james.parham@databricks.com/dbx_test" \
  --verbose
```

### Step 3: View Results

The framework will:
- Discover your test notebooks
- Execute them on Databricks
- Generate JUnit XML reports in `.dbx_test-results/`
- Display results in console

## Troubleshooting

### "Workspace directory not found"

**Error message:** `Workspace directory not found: /Workspace/... Please verify the path exists in your Databricks workspace.`

**Possible causes:**
1. Directory doesn't exist in the workspace
2. Typo in the path
3. Authentication issue

**Solution:**
- Verify path exists: `databricks workspace list "/Workspace/Users/james.parham@databricks.com"`
- Check parent directory: `databricks workspace list "/Workspace/Users"`
- Verify you can access the folder in Databricks UI
- Check profile: `databricks configure --token --profile <profile>`

### "No test notebooks found"

**Possible causes:**
1. Directory is empty
2. Notebook names don't match the pytest pattern (test_* or *_test)

**Solution:**
- Check your workspace directory in Databricks UI
- Ensure notebooks start with `test_` or end with `_test` (e.g., `test_my_feature`, `my_feature_test`)
- Use `--verbose` to see discovery details
- Verify notebooks exist in the exact path you specified

### "Error: Tests directory not found"

**This error means** you're trying to use a local path that doesn't exist.

**Solution:**
- For workspace tests, ensure the path starts with `/Workspace/` or `/Repos/`
- For local tests, verify the directory exists on your filesystem
- Example workspace path: `/Workspace/Users/james.parham@databricks.com/dbx_test`

### "Permission denied"

**Solution:**
- Ensure your Databricks token has workspace read/execute permissions
- Check if you can access the folder in Databricks UI
- Try running with `--verbose` to see more details

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
  output_dir: ".dbx_test-results"
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
        run: pip install dbx_test
      
      - name: Configure Databricks CLI
        run: |
          databricks configure --token << EOF
          ${{ secrets.DATABRICKS_HOST }}
          ${{ secrets.DATABRICKS_TOKEN }}
          EOF
      
      - name: Run workspace tests
        run: |
          dbx_test run --remote --workspace-tests \
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
# Simple and automatic!
dbx_test run --remote --profile <profile> --tests-dir "<workspace_path>"
```

**Key Benefits of Auto-Detection:**
- ✅ No need to remember the `--workspace-tests` flag
- ✅ Cleaner, simpler commands
- ✅ Works with both `/Workspace/` and `/Repos/` paths
- ✅ Backwards compatible - `--workspace-tests` still works if you prefer explicit flags

