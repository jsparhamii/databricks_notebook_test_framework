# Quick Start Guide

Get up and running with dbx_test in 5 minutes! This guide focuses on **serverless compute** and **Databricks Asset Bundle** integration.

## 1. Installation

```bash
pip install dbx_test
```

Or install from source:

```bash
git clone https://github.com/jsparhamii/dbx_test.git
cd dbx_test
pip install -e .
```

## 2. Setup Databricks Authentication

Configure Databricks CLI with your workspace:

```bash
databricks configure --token

# Enter your workspace URL: https://your-workspace.cloud.databricks.com
# Enter your token: dapi...
```

For multiple workspaces, use profiles:

```bash
databricks configure --token --profile dev
databricks configure --token --profile prod
```

## 3. Create Your First Test

### Option A: Use Scaffold (Recommended)

```bash
# Creates test file + config automatically
dbx_test scaffold my_feature

# Output:
# ✓ Created test notebook: tests/my_feature_test.py
# ✓ Created configuration file: config/test_config.yml
```

### Option B: Manual Creation

Create `tests/my_feature_test.py`:

```python
from dbx_test import NotebookTestFixture

class TestMyFeature(NotebookTestFixture):
    """Test suite for my feature."""
    
    def run_setup(self):
        """Setup code runs before tests."""
        # Create test data
        self.test_data = spark.createDataFrame(
            [(1, "Alice", 100), (2, "Bob", 200)],
            ["id", "name", "amount"]
        )
        self.test_data.createOrReplaceTempView("test_data")
    
    def test_row_count(self):
        """Test that we have the expected number of rows."""
        result = spark.sql("SELECT * FROM test_data")
        assert result.count() == 2, "Expected 2 rows in test data"
    
    def test_total_amount(self):
        """Test that total amount is correct."""
        result = spark.sql("SELECT SUM(amount) as total FROM test_data").collect()
        total = result[0]["total"]
        assert total == 300, f"Expected total of 300, got {total}"
    
    def test_schema(self):
        """Test that schema has required columns."""
        result = spark.sql("SELECT * FROM test_data")
        assert "id" in result.columns, "Missing 'id' column"
        assert "name" in result.columns, "Missing 'name' column"
        assert "amount" in result.columns, "Missing 'amount' column"
    
    def run_cleanup(self):
        """Cleanup runs after all tests."""
        spark.sql("DROP VIEW IF EXISTS test_data")
```

## 4. Configure

Create `config/test_config.yml`:

```yaml
workspace:
  # Databricks CLI profile
  profile: "default"

cluster:
  # Serverless with automatic library installation
  libraries:
    - whl: "git+https://github.com/your-org/your-package.git"
    # Add more dependencies as needed:
    # - pypi:
    #     package: "pandas==2.0.0"

execution:
  timeout: 600
  parallel: false

reporting:
  output_dir: ".dbx-test-results"
  formats:
    - "console"
    - "junit"
```

## 5. Run Tests

### For Databricks Asset Bundle Projects

If your project has a `databricks.yml` file:

```bash
# Auto-detects bundle and resolves workspace path
dbx_test run --target dev --profile default

# That's it! Framework automatically:
# 1. Detects your bundle project
# 2. Resolves workspace path based on target
# 3. Installs dependencies via inline environment
# 4. Runs tests on serverless compute
```

### For Non-Bundle Projects

After deploying tests to workspace:

```bash
# Upload tests first
dbx_test upload --tests-dir tests \
  --workspace-path /Workspace/Users/you@company.com/my-project/tests \
  --profile default

# Run tests
dbx_test run \
  --tests-dir /Workspace/Users/you@company.com/my-project/tests \
  --profile default
```

## 6. View Results

Test output is displayed in the console:

```
Running tests from Databricks workspace: /Workspace/Users/...

Found 1 test notebook(s):
  • .../tests/my_feature_test

Test Results:

my_feature_test: 3 test(s)
  ✓ TestMyFeature.test_row_count (1.2s)
  ✓ TestMyFeature.test_total_amount (0.8s)
  ✓ TestMyFeature.test_schema (0.5s)

Test Execution Summary:
Total: 3, Passed: 3, Failed: 0

✓ JUnit report saved to: .dbx-test-results/20241103_120000/reports/report.xml

🎉 All tests passed!
```

JUnit XML report is automatically generated for CI/CD integration.

## Working with Databricks Asset Bundles

### Typical Bundle Structure

```
my_project/
├── databricks.yml
├── src/
│   └── my_module.py
└── tests/
    ├── test_feature_a.py
    └── test_feature_b.py
```

### Bundle Configuration

`databricks.yml`:

```yaml
bundle:
  name: my_project

targets:
  dev:
    workspace:
      host: https://your-workspace.cloud.databricks.com/
    default: true
```

### Deploy and Test

```bash
# Deploy bundle
databricks bundle deploy --target dev

# Run tests (auto-detects bundle)
dbx_test run --target dev --profile default

# Framework automatically resolves to:
# /Workspace/Users/you@company.com/.bundle/my_project/dev/files/tests
```

## Serverless with Dependencies

The framework automatically manages dependencies on serverless compute:

```yaml
# config/test_config.yml
cluster:
  libraries:
    # Git repository
    - whl: "git+https://github.com/org/repo.git"
    - whl: "git+https://github.com/org/repo.git@v1.0.0"
    
    # PyPI packages
    - pypi:
        package: "pandas==2.0.0"
    
    # Workspace wheels
    - whl: "/Workspace/Shared/wheels/custom-1.0.0-py3-none-any.whl"
```

The framework creates an inline environment and installs all dependencies automatically!

## Next Steps

### Learn More
- **[Notebook Usage](docs/notebook_usage.md)** - Run tests interactively in notebooks
- **[Configuration Guide](docs/configuration.md)** - Advanced configuration options
- **[Serverless Environments](docs/serverless_environments.md)** - Managing dependencies
- **[Testing Application Code](docs/testing_application_code.md)** - Test `src/` code from `tests/`

### Advanced Features
- **[Parallel Execution](docs/parallel_execution.md)** - Run tests faster
- **[Multiple Test Classes](docs/multiple_test_classes.md)** - Multiple classes per notebook
- **[CI/CD Integration](docs/ci_cd_integration.md)** - GitHub Actions, Azure DevOps

### Examples
- **[src/ Code Testing Example](examples/src_code_example/)** - Real-world pattern

## Common Workflows

### Development Workflow

```bash
# 1. Create test
dbx_test scaffold new_feature

# 2. Edit test file
vim tests/new_feature_test.py

# 3. Deploy bundle (if using bundles)
databricks bundle deploy --target dev

# 4. Run tests
dbx_test run --target dev --profile default

# 5. Fix issues and repeat
```

### CI/CD Workflow

```bash
# In GitHub Actions / Azure Pipelines
dbx_test run --target dev --profile ci_profile \
  --output-format junit \
  --output-format html
```

### Interactive Development

Open a Databricks notebook and run tests directly:

```python
from dbx_test import NotebookTestFixture, run_notebook_tests
import json

class TestInteractive(NotebookTestFixture):
    def run_setup(self):
        self.data = spark.range(100)
    
    def test_count(self):
        assert self.data.count() == 100

results = run_notebook_tests()
dbutils.notebook.exit(json.dumps(results))
```

## Troubleshooting

### Tests not found?

Check test naming:
- Files must start with `test_` or end with `_test`
- Example: `test_my_feature.py` or `my_feature_test.py`

### Authentication issues?

```bash
# Verify CLI is configured
databricks auth profiles

# Test authentication
databricks workspace list /
```

### Bundle not detected?

- Ensure `databricks.yml` exists in project root
- Check target name matches: `dbx_test run --target <name>`
- Use `--verbose` flag for debugging

### Dependencies not installing?

- Check library syntax in config
- For production, use pre-created environments
- See [Serverless Environments Guide](docs/serverless_environments.md)

## Getting Help

- **Documentation**: See `docs/` directory
- **Examples**: See `examples/` directory
- **Issues**: [GitHub Issues](https://github.com/jsparhamii/dbx_test/issues)

Happy testing! 🚀
