# Databricks Notebook Test Framework - Documentation

Welcome to the comprehensive documentation for the Databricks Notebook Test Framework.

## Documentation Index

### Getting Started

1. **[Quick Start](../QUICKSTART.md)** - Get up and running in 5 minutes
2. **[Installation](installation.md)** - Detailed installation instructions
3. **[Configuration](configuration.md)** - Complete configuration reference

### Core Guides

4. **[Writing Tests](writing_tests.md)** - Best practices for writing effective tests
5. **[CI/CD Integration](ci_cd_integration.md)** - Integrate with GitHub Actions, Azure DevOps, etc.

### Reference

6. **[CLI Reference](#cli-reference)** - Command-line interface documentation
7. **[Configuration Schema](#configuration-schema)** - YAML configuration options
8. **[API Reference](#api-reference)** - Python API documentation

### Contributing

9. **[Contributing Guide](../CONTRIBUTING.md)** - How to contribute to the project
10. **[Changelog](../CHANGELOG.md)** - Version history and changes

---

## CLI Reference

### Global Options

```bash
dbx_test [OPTIONS] COMMAND [ARGS]...
```

**Options:**
- `--version` - Show version and exit
- `--help` - Show help message and exit

### Commands

#### `run` - Execute Tests

Run test notebooks locally or remotely.

```bash
dbx_test run [OPTIONS]
```

**Options:**
- `--local` - Run tests locally using nuttercli
- `--remote` - Run tests remotely on Databricks
- `--pattern TEXT` - Pattern to filter test notebooks
- `--env TEXT` - Environment (dev/test/prod)
- `--parallel` - Enable parallel test execution (remote only)
- `--output-format TEXT` - Output format(s): console, junit, json, html (multiple allowed)
- `--config PATH` - Path to configuration file (default: config/test_config.yml)
- `--verbose` - Enable verbose output
- `--tests-dir PATH` - Directory containing test notebooks (default: tests)

**Examples:**

```bash
# Run locally
dbx_test run --local

# Run remotely on dev environment
dbx_test run --remote --env dev

# Run with specific pattern
dbx_test run --local --pattern "*integration*"

# Run with multiple output formats
dbx_test run --remote --output-format junit --output-format html

# Run in parallel
dbx_test run --remote --parallel --env test
```

#### `discover` - Discover Tests

Discover all test notebooks in a directory.

```bash
dbx_test discover [OPTIONS]
```

**Options:**
- `--pattern TEXT` - Pattern to match test files (default: **/*_test.py)
- `--tests-dir PATH` - Directory containing test notebooks (default: tests)

**Example:**

```bash
dbx_test discover --tests-dir tests
```

#### `report` - Generate Reports

Generate test report from a previous run.

```bash
dbx_test report [OPTIONS]
```

**Options:**
- `--run-id TEXT` - Run ID (default: latest)
- `--format TEXT` - Output format: console, junit, json, html (default: console)
- `--output-dir PATH` - Test results directory (default: .dbx_test-results)

**Examples:**

```bash
# Show latest results
dbx_test report

# Generate HTML report
dbx_test report --format html

# Show specific run
dbx_test report --run-id 20250128_143022
```

#### `upload` - Upload Notebooks

Upload test notebooks to Databricks workspace.

```bash
dbx_test upload [OPTIONS]
```

**Options:**
- `--tests-dir PATH` - Directory containing test notebooks (default: tests)
- `--workspace-path TEXT` - Workspace path prefix (required)
- `--config PATH` - Path to configuration file (default: config/test_config.yml)
- `--pattern TEXT` - Pattern to match test files (default: **/*_test.py)

**Example:**

```bash
dbx_test upload --workspace-path "/Workspace/Repos/myuser/tests"
```

#### `scaffold` - Create Test Template

Create a new test notebook from template.

```bash
dbx_test scaffold [OPTIONS] NOTEBOOK_NAME
```

**Options:**
- `--output-dir PATH` - Output directory for test notebook (default: tests)

**Example:**

```bash
dbx_test scaffold my_new_test
```

---

## Configuration Schema

Complete YAML configuration schema:

```yaml
workspace:
  host: string              # Required: Databricks workspace URL
  token: string             # Optional: Direct token (not recommended)
  token_env: string         # Optional: Environment variable name (default: DATABRICKS_TOKEN)

cluster:
  size: string              # T-shirt size: S, M, L, XL (default: M)
  spark_version: string     # Spark version (default: 13.3.x-scala2.12)
  node_type_id: string      # Optional: Node type
  driver_node_type_id: string  # Optional: Driver node type
  num_workers: int          # Optional: Fixed number of workers
  autoscale_min_workers: int   # Optional: Min workers for autoscaling
  autoscale_max_workers: int   # Optional: Max workers for autoscaling
  cluster_policy_id: string    # Optional: Cluster policy ID
  spark_conf:               # Optional: Spark configuration
    key: value
  spark_env_vars:           # Optional: Environment variables
    key: value
  custom_tags:              # Optional: Custom tags
    key: value

execution:
  timeout: int              # Timeout per test in seconds (default: 600)
  max_retries: int          # Maximum retry attempts (default: 2)
  parallel: boolean         # Enable parallel execution (default: false)
  max_parallel_jobs: int    # Max concurrent jobs (default: 5)
  poll_interval: int        # Poll interval for status (default: 10)

paths:
  workspace_root: string    # Workspace root path (default: /Workspace/Repos/production)
  test_pattern: string      # Glob pattern for tests (default: **/*_test.py)
  local_tests_dir: string   # Local tests directory (default: tests)

reporting:
  output_dir: string        # Output directory (default: .dbx_test-results)
  formats: list             # Report formats (default: [junit, console, json])
  fail_on_error: boolean    # Fail on test errors (default: true)
  verbose: boolean          # Verbose output (default: false)

parameters:                 # Optional: Default parameters for all tests
  key: value
```

---

## API Reference

### Main Classes

#### `TestConfig`

Configuration management class.

```python
from dbx_test import TestConfig

# Load from YAML
config = TestConfig.from_yaml("config/test_config.yml")

# Create from dictionary
config = TestConfig.from_dict(config_dict)

# Get default configuration
config = TestConfig.get_default()
```

#### `TestDiscovery`

Test discovery engine.

```python
from dbx_test import TestDiscovery

# Initialize
discovery = TestDiscovery(root_dir="tests", pattern="**/*_test.py")

# Discover tests
tests = discovery.discover()

# Filter tests
filtered = discovery.filter_tests(tests, name_filter="*integration*")

# Print summary
discovery.print_summary(tests)
```

#### `LocalTestRunner`

Local test execution.

```python
from dbx_test import LocalTestRunner

# Initialize
runner = LocalTestRunner(verbose=True)

# Check if Nutter is installed
if runner.check_nutter_installed():
    # Run tests
    results = runner.run_tests(
        test_notebooks=tests,
        parameters={"env": "dev"},
        timeout=600
    )
```

#### `RemoteTestRunner`

Remote test execution on Databricks.

```python
from dbx_test import RemoteTestRunner

# Initialize
runner = RemoteTestRunner(config=test_config, verbose=True)

# Run tests
results = runner.run_tests(
    test_notebooks=tests,
    parameters={"env": "dev"}
)
```

#### `TestReporter`

Report generation.

```python
from dbx_test import TestReporter

# Initialize
reporter = TestReporter(verbose=True)

# Generate JUnit XML
reporter.generate_junit_xml(results, output_path)

# Generate HTML report
reporter.generate_html_report(results, output_path)

# Print console report
reporter.print_console_report(results)
```

---

## Troubleshooting

### Common Issues

**Issue**: Tests not discovered
- Check file naming (must end with `_test.py`)
- Verify class inherits from `NutterFixture`
- Check test methods start with `test_`

**Issue**: Cannot connect to Databricks
- Verify `DATABRICKS_TOKEN` environment variable
- Check workspace URL format
- Verify token hasn't expired

**Issue**: Tests timeout
- Increase timeout in configuration
- Optimize test queries
- Use smaller test datasets

**Issue**: Parallel execution fails
- Check `max_parallel_jobs` setting
- Verify workspace has sufficient resources
- Try sequential execution first

---

## Examples

### Basic Test

```python
from nutter.testing import NutterFixture

class TestExample(NutterFixture):
    def run_setup(self):
        self.df = spark.createDataFrame([(1, "a")], ["id", "value"])
    
    def test_count(self):
        assert self.df.count() == 1
    
    def run_cleanup(self):
        pass
```

### Integration Test

```python
class TestIntegration(NutterFixture):
    def run_setup(self):
        # Create bronze table
        spark.sql("CREATE TABLE bronze AS SELECT * FROM source")
        # Transform to silver
        spark.sql("CREATE TABLE silver AS SELECT * FROM bronze WHERE valid = 1")
    
    def test_no_data_loss(self):
        bronze_count = spark.table("bronze").count()
        silver_count = spark.table("silver").count()
        assert silver_count <= bronze_count
    
    def run_cleanup(self):
        spark.sql("DROP TABLE IF EXISTS bronze")
        spark.sql("DROP TABLE IF EXISTS silver")
```

---

## Additional Resources

- [Nutter Documentation](https://github.com/microsoft/nutter)
- [Databricks SDK Documentation](https://databricks-sdk-py.readthedocs.io/)
- [Example Tests](../tests/)
- [Configuration Examples](../config/)

---

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/dbx_test/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/dbx_test/discussions)
- **Contributing**: See [CONTRIBUTING.md](../CONTRIBUTING.md)

---

Last Updated: 2025-01-28

