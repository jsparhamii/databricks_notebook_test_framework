# Databricks Notebook Test Framework

A Python-based automated testing framework for Databricks notebooks.

## Features

- ✅ Simple, intuitive test pattern with setup/test/cleanup lifecycle
- ✅ Execute unit tests in notebooks locally *and* remotely in Databricks
- ✅ Clean developer workflow for writing tests
- ✅ JUnit XML results compatible with CI/CD pipelines
- ✅ Parameterized testing support
- ✅ Test discovery and orchestration for multiple notebooks
- ✅ CLI-driven with rich output
- ✅ Parallel test execution (optional)
- ✅ Zero external test framework dependencies

## Installation

```bash
# Install from source
pip install -e .
```

Or from PyPI (once published):

```bash
pip install databricks-notebook-test-framework
```

## Quick Start

### 1. Create a Test Notebook

Create a test notebook (e.g., `tests/my_notebook_test.py`):

```python
from databricks_notebook_test_framework import NotebookTestFixture

class TestMyNotebook(NotebookTestFixture):
    def run_setup(self):
        """Setup code runs before tests"""
        self.data = spark.createDataFrame([(1, "a"), (2, "b")], ["id", "value"])
        self.data.createOrReplaceTempView("test_data")
    
    def test_row_count(self):
        """Test that we have expected row count"""
        result = spark.sql("SELECT * FROM test_data")
        assert result.count() == 2, "Expected 2 rows"
    
    def test_schema(self):
        """Test that schema is correct"""
        result = spark.sql("SELECT * FROM test_data")
        assert "id" in result.columns
        assert "value" in result.columns
    
    def run_cleanup(self):
        """Cleanup runs after all tests"""
        spark.sql("DROP VIEW IF EXISTS test_data")
```

### 2. Configure Your Environment

The framework uses Databricks CLI authentication by default. If you have the Databricks CLI configured, you're ready to go!

**Option A: Use Databricks CLI (Recommended)**

```bash
# Configure Databricks CLI (if not already done)
databricks configure --token

# Or use a specific profile
databricks configure --token --profile dev
```

Then create `config/test_config.yml`:

```yaml
workspace:
  # Use Databricks CLI profile (optional, uses DEFAULT if not specified)
  profile: "DEFAULT"  # or "dev", "prod", etc.
  
cluster:
  # Use existing cluster (recommended for development)
  cluster_id: "1234-567890-abcdef"
  
  # OR leave empty to use serverless compute (default)
  # OR specify size to create new cluster:
  # size: "M"
  # spark_version: "13.3.x-scala2.12"
  
execution:
  timeout: 600
  max_retries: 2
  parallel: false
  
paths:
  workspace_root: "/Workspace/Repos/production"
  test_pattern: "**/*_test.py"
  
reporting:
  output_dir: ".dbx-test-results"
  formats: ["junit", "console", "json"]
```

### 3. Run Tests

**A. Command-Line (CI/CD and Automated Testing)**

```bash
# Discover and run all tests (pytest-style: test_* and *_test)
dbx-test run --local

# Run remotely on Databricks
dbx-test run --remote

# Use specific Databricks CLI profile
dbx-test run --remote --profile prod

# Run tests from specific directory
dbx-test run --remote --tests-dir tests/integration

# Run tests already in workspace (no upload)
dbx-test run --remote --workspace-tests --tests-dir "/Workspace/Repos/my-repo/tests"
```

**Test Discovery**: Automatically finds all notebooks matching `test_*` or `*_test` patterns (just like pytest!)

**B. In Databricks Notebook (Interactive Development)**

```python
# Install the framework
%pip install /dbfs/FileStore/wheels/databricks_notebook_test_framework-0.1.0-py3-none-any.whl

# Write and run tests
from databricks_notebook_test_framework import NotebookTestFixture, run_notebook_tests

class TestMyData(NotebookTestFixture):
    def run_setup(self):
        self.df = spark.createDataFrame([(1, "Alice")], ["id", "name"])
    
    def test_count(self):
        assert self.df.count() == 1

# Run tests immediately
run_notebook_tests()
```

**📘 See [Notebook Usage Guide](docs/notebook_usage.md) for detailed examples and patterns.**

## CLI Commands

### `dbx-test run`

Execute tests locally or remotely.

**Automatic Test Discovery** (pytest-style):
- Finds all notebooks named `test_*` (e.g., `test_my_feature`)
- Finds all notebooks named `*_test` (e.g., `my_feature_test`)
- Recursively searches subdirectories

**Options:**
- `--local` - Run tests locally (requires PySpark)
- `--remote` - Run tests remotely on Databricks
- `--workspace-tests` - Tests are already in workspace (don't upload)
- `--profile PROFILE` - Databricks CLI profile to use (overrides config)
- `--env ENV` - Environment (dev/test/prod)
- `--parallel` - Enable parallel execution
- `--output-format FORMAT` - Output format (junit/console/json/html)
- `--config PATH` - Path to config file (default: config/test_config.yml)
- `--tests-dir DIR` - Directory containing tests (default: tests)

### `dbx-test discover`

Discover all test notebooks in the repository.

### `dbx-test report`

Generate test report from previous run.

### `dbx-test upload`

Upload test notebooks to Databricks workspace.

### `dbx-test scaffold`

Create a new test notebook from template.

## Configuration

See [Configuration Guide](docs/configuration.md) for detailed configuration options.

## Documentation

- [Quick Start Guide](QUICKSTART.md) - Get started in 5 minutes
- [Pytest-Style Discovery](docs/pytest_discovery.md) - Automatic test discovery (test_* and *_test) 🔍
- [Notebook Usage Guide](docs/notebook_usage.md) - Run tests directly in Databricks notebooks 📘
- [Workspace Tests](docs/workspace_tests.md) - Run tests already in Databricks workspace 🔄
- [Notebook Results](docs/notebook_results.md) - Return detailed results from notebooks to CLI 📊
- [Testing Application Code](docs/testing_application_code.md) - Test code in `src/` from `tests/` 📦
- [Writing Tests](docs/writing_tests.md) - Best practices for writing tests
- [Configuration Guide](docs/configuration.md) - Detailed configuration options
- [Databricks CLI Authentication](docs/databricks_cli_auth.md) - Authentication setup
- [Cluster Configuration](docs/cluster_configuration.md) - Compute options (existing/serverless/new)
- [CI/CD Integration](docs/ci_cd_integration.md) - GitHub Actions, Azure DevOps, etc.
- [Example Notebook](examples/notebook_test_example.py) - Complete notebook example
- [Example: Testing src/ Code](examples/src_code_example/) - Test application code pattern
- [Example: Notebook with Results](examples/test_example_with_results.py) - Notebook that returns results

## Architecture

```
src/databricks_notebook_test_framework/
├── cli.py                 # CLI entry point
├── config.py              # Configuration management
├── discovery.py           # Test discovery engine
├── runner_local.py        # Local test execution
├── runner_remote.py       # Remote Databricks execution
├── notebook_runner.py     # Notebook test execution
├── testing.py             # Test fixture base class
├── reporting.py           # Report generation
├── artifacts.py           # Artifact management
└── utils/                 # Utility functions
    ├── notebook.py        # Notebook parsing
    ├── databricks.py      # Databricks API helpers
    └── validation.py      # Validation utilities
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md).

