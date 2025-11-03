# Databricks Notebook Test Framework

A Python-based automated testing framework for Databricks notebooks with **native serverless support** and **Databricks Asset Bundle integration**.

## Features

- ✅ **Serverless-first** - Automatic inline environment management for dependencies
- ✅ **Databricks Asset Bundles** - Auto-detects bundle projects and resolves workspace paths
- ✅ Simple, intuitive test pattern with setup/test/cleanup lifecycle
- ✅ Execute tests remotely on Databricks (serverless or cluster)
- ✅ **Parallel test execution** for faster test runs
- ✅ Clean developer workflow for writing tests
- ✅ JUnit XML results compatible with CI/CD pipelines
- ✅ Parameterized testing support
- ✅ Automatic test discovery (pytest-style patterns)
- ✅ CLI-driven with rich output
- ✅ Run multiple test classes in a single notebook
- ✅ Zero external test framework dependencies

## Installation

```bash
# Install from source
pip install -e .
```

Or from PyPI (once published):

```bash
pip install dbx_test
```

## Quick Start

### 1. Create a Test Notebook

Create a test notebook (e.g., `tests/my_notebook_test.py`):

```python
from dbx_test import NotebookTestFixture

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

### 2. Scaffold Your Project

```bash
# Creates test file + config automatically
dbx_test scaffold my_feature

# For bundle projects, this detects the bundle and provides bundle-specific tips
```

### 3. Configure Your Environment

Create `config/test_config.yml`:

```yaml
workspace:
  # Use Databricks CLI profile
  profile: "default"
  
cluster:
  # Option 1: Use serverless (recommended, fastest)
  # Leave empty for serverless with inline dependencies
  
  # Install dependencies automatically
  libraries:
    - whl: "git+https://github.com/your-org/your-package.git"
    - pypi:
        package: "pandas==2.0.0"
  
  # Option 2: Use pre-created environment (serverless)
  # environment_key: "my_environment"
  
  # Option 3: Use existing cluster
  # cluster_id: "1234-567890-abcdef"
  
execution:
  timeout: 600
  parallel: false
  
reporting:
  output_dir: ".dbx-test-results"
  formats: ["junit", "console"]
```

### 4. Run Tests

**For Databricks Asset Bundle Projects:**

```bash
# Auto-detects bundle and resolves workspace path
dbx_test run --target dev --profile my-profile

# With custom subdirectory
dbx_test run --target dev --tests-dir src/tests --profile my-profile
```

**For Non-Bundle Projects:**

```bash
# Run tests from workspace path
dbx_test run --tests-dir /Workspace/Users/you@company.com/tests --profile my-profile

# Or from Repos
dbx_test run --tests-dir /Repos/production/my-project/tests --profile my-profile
```

**Test Discovery**: Automatically finds all notebooks matching `test_*` or `*_test` patterns (just like pytest!)

## Databricks Asset Bundle Support

The framework automatically detects Databricks Asset Bundle projects and simplifies test execution:

**Example Bundle Structure:**
```
my_bundle/
├── databricks.yml
├── src/
│   └── my_code.py
└── tests/
    ├── test_feature_a.py
    └── test_feature_b.py
```

**Example databricks.yml:**
```yaml
bundle:
  name: my_project

targets:
  dev:
    workspace:
      host: https://your-workspace.cloud.databricks.com/
```

**Run Tests:**
```bash
# Framework auto-detects the bundle and constructs the workspace path
dbx_test run --target dev --profile my-profile

# Resolves to: /Workspace/Users/you@company.com/.bundle/my_project/dev/files/tests
```

**Benefits:**
- ✅ No manual workspace path configuration
- ✅ Works seamlessly with `databricks bundle deploy`
- ✅ Automatic path resolution based on target
- ✅ Supports custom test directories

## Serverless Compute with Inline Dependencies

The framework automatically creates inline environments for serverless compute:

```yaml
cluster:
  # Dependencies are automatically installed in serverless environment
  libraries:
    - whl: "git+https://github.com/your-org/your-package.git"
    - pypi:
        package: "pandas==2.0.0"
    - whl: "/Workspace/Shared/wheels/custom-1.0.0-py3-none-any.whl"
```

**How it works:**
1. Framework detects serverless compute (no cluster_id specified)
2. Creates inline environment with your dependencies
3. Executes tests with all libraries installed
4. Cleans up automatically

**For production**, you can pre-create environments:
```yaml
cluster:
  environment_key: "production_test_env"  # Reference pre-created environment
```

See [Serverless Environments Guide](docs/serverless_environments.md) for details.

## Interactive Notebook Development

```python
# Run tests directly in a Databricks notebook
from dbx_test import NotebookTestFixture, run_notebook_tests
import json

class TestMyData(NotebookTestFixture):
    def run_setup(self):
        self.df = spark.createDataFrame([(1, "Alice")], ["id", "name"])
    
    def test_count(self):
        assert self.df.count() == 1

# Run tests (automatically discovers all test classes)
results = run_notebook_tests()

# Return results to CLI (required for remote execution)
dbutils.notebook.exit(json.dumps(results))
```

**📘 See [Notebook Usage Guide](docs/notebook_usage.md) for detailed examples and patterns.**

## CLI Commands

### `dbx_test run`

Execute tests remotely on Databricks.

**Options:**
- `--target TARGET` - Databricks Asset Bundle target (auto-detects workspace path)
- `--profile PROFILE` - Databricks CLI profile to use
- `--tests-dir DIR` - Directory containing tests (workspace path or relative for bundles)
- `--env ENV` - Environment (dev/test/prod)
- `--parallel` - Enable parallel execution
- `--output-format FORMAT` - Output format (junit/console/json/html)
- `--config PATH` - Path to config file (default: config/test_config.yml)
- `--verbose` - Enable verbose output

**Examples:**

```bash
# Bundle project
dbx_test run --target dev --profile my-profile

# Workspace path
dbx_test run --tests-dir /Workspace/Users/you@company.com/tests --profile my-profile

# With multiple output formats
dbx_test run --target dev --profile prod \
  --output-format junit \
  --output-format html
```

### `dbx_test scaffold`

Create a new test notebook from template.

```bash
# Create test and config files
dbx_test scaffold my_feature

# Detects bundle projects and provides bundle-specific instructions
```

### `dbx_test upload`

Upload test notebooks to Databricks workspace.

```bash
# Upload local tests to workspace
dbx_test upload --tests-dir tests \
  --workspace-path /Workspace/Users/you@company.com/tests \
  --profile dev
```

## Configuration

See [Configuration Guide](docs/configuration.md) for detailed configuration options.

## Documentation

### Getting Started
- [Quick Start Guide](QUICKSTART.md) - Get started in 5 minutes
- [Installation](docs/installation.md) - Detailed installation instructions

### Core Features
- [Databricks Asset Bundle Support](docs/configuration.md#databricks-asset-bundles) - Auto-detection and path resolution
- [Serverless Environments](docs/serverless_environments.md) - Inline dependencies for serverless 🚀
- [Installing Libraries](docs/installing_libraries.md) - PyPI, wheels, and Git repos
- [Pytest-Style Discovery](docs/pytest_discovery.md) - Automatic test discovery 🔍
- [Notebook Usage Guide](docs/notebook_usage.md) - Run tests in notebooks 📘
- [Workspace Tests](docs/workspace_tests.md) - Run tests from workspace 🔄

### Advanced Topics
- [Multiple Test Classes](docs/multiple_test_classes.md) - Multiple test classes per notebook
- [Parallel Execution](docs/parallel_execution.md) - Faster test runs
- [Testing Application Code](docs/testing_application_code.md) - Test `src/` from `tests/` 📦
- [Cluster Configuration](docs/cluster_configuration.md) - Serverless vs cluster options

### Integration
- [Databricks CLI Authentication](docs/databricks_cli_auth.md) - Authentication setup
- [CI/CD Integration](docs/ci_cd_integration.md) - GitHub Actions, Azure DevOps, etc.

### Examples
- [Testing src/ Code Example](examples/src_code_example/) - Real workspace pattern

## Architecture

```
src/dbx_test/
├── cli.py                 # CLI entry point
├── config.py              # Configuration management
├── runner_remote.py       # Remote Databricks execution (serverless/cluster)
├── notebook_runner.py     # Notebook test execution
├── testing.py             # Test fixture base class
├── reporting.py           # Report generation
├── artifacts.py           # Artifact management
├── bundle.py              # Databricks Asset Bundle integration
└── utils/                 # Utility functions
    ├── databricks.py      # Databricks API helpers (inline environments)
    ├── notebook.py        # Notebook parsing
    └── validation.py      # Validation utilities
```

## Why This Framework?

### ✅ Serverless-First Design
- Automatic inline environment creation
- No cluster management overhead
- Fast startup times
- Cost-effective pay-per-use model

### ✅ Databricks Asset Bundle Native
- Auto-detects bundle projects
- Resolves workspace paths automatically
- Seamless integration with `databricks bundle deploy`
- No manual path configuration

### ✅ Developer-Friendly
- Pytest-style test discovery
- Simple test patterns (setup → test → cleanup)
- Rich CLI output
- Works in notebooks and CI/CD

### ✅ Production-Ready
- JUnit XML for CI/CD integration
- Parallel execution support
- Comprehensive error reporting
- Battle-tested on real projects

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md).
