# Databricks Notebook Test Framework Documentation

Comprehensive documentation for the dbx_test framework - a **serverless-first** testing solution with **Databricks Asset Bundle** integration.

## Table of Contents

### Getting Started
1. [Quick Start Guide](../QUICKSTART.md) - Get up and running in 5 minutes
2. [Installation](installation.md) - Detailed installation instructions
3. [Configuration](configuration.md) - Configure your test environment

### Core Features

#### Databricks Asset Bundle Support
- **Auto-Detection**: Framework automatically detects `databricks.yml`
- **Path Resolution**: Automatically resolves workspace paths based on target
- **Seamless Integration**: Works with `databricks bundle deploy`

**Example:**
```bash
dbx_test run --target dev --profile my-profile
# Auto-resolves to: /Workspace/Users/you@company.com/.bundle/project/dev/files/tests
```

#### Serverless Compute (Recommended)
- [Serverless Environments](serverless_environments.md) - Inline dependency management 🚀
- [Installing Libraries](installing_libraries.md) - PyPI, wheels, Git repos

**Features:**
- ✅ Automatic inline environment creation
- ✅ Dependency installation on-the-fly
- ✅ Fast startup times
- ✅ Cost-effective pay-per-use

#### Test Discovery & Execution
- [Pytest-Style Discovery](pytest_discovery.md) - Automatic `test_*` and `*_test` patterns 🔍
- [Workspace Tests](workspace_tests.md) - Run tests from Databricks workspace 🔄
- [Parallel Execution](parallel_execution.md) - Faster test runs with parallel jobs

#### Writing Tests
- [Notebook Usage Guide](notebook_usage.md) - Run tests in Databricks notebooks 📘
- [Multiple Test Classes](multiple_test_classes.md) - Multiple classes per notebook
- [Testing Application Code](testing_application_code.md) - Test `src/` from `tests/` 📦
- [Notebook Results](notebook_results.md) - Return results from notebooks to CLI 📊

### Configuration & Setup

- [Configuration Guide](configuration.md) - Detailed config options
- [Databricks CLI Authentication](databricks_cli_auth.md) - Set up authentication
- [Cluster Configuration](cluster_configuration.md) - Serverless vs cluster options

### Integration

- [CI/CD Integration](ci_cd_integration.md) - GitHub Actions, Azure DevOps, Jenkins

### Examples

- [Testing src/ Code](../examples/src_code_example/) - Real-world workspace pattern

## Quick Reference

### Basic Commands

```bash
# Bundle project
dbx_test run --target dev --profile my-profile

# Workspace path
dbx_test run --tests-dir /Workspace/Users/you@company.com/tests --profile my-profile

# Create new test
dbx_test scaffold my_feature

# Upload tests
dbx_test upload --tests-dir tests \
  --workspace-path /Workspace/Users/you@company.com/tests \
  --profile my-profile
```

### Configuration Example

```yaml
workspace:
  profile: "default"

cluster:
  # Serverless with inline dependencies
  libraries:
    - whl: "git+https://github.com/org/repo.git"
    - pypi:
        package: "pandas==2.0.0"

execution:
  timeout: 600
  parallel: false

reporting:
  output_dir: ".dbx-test-results"
  formats: ["console", "junit"]
```

### Test Template

```python
from dbx_test import NotebookTestFixture

class TestMyFeature(NotebookTestFixture):
    def run_setup(self):
        """Setup runs before tests"""
        self.data = spark.createDataFrame([(1, "a")], ["id", "val"])
        self.data.createOrReplaceTempView("test_data")
    
    def test_example(self):
        """Test something"""
        result = spark.sql("SELECT * FROM test_data")
        assert result.count() == 1
    
    def run_cleanup(self):
        """Cleanup runs after tests"""
        spark.sql("DROP VIEW IF EXISTS test_data")
```

## Architecture Overview

```
Remote Execution on Databricks
    ↓
Serverless Compute (Recommended)
    ↓
Inline Environment
    • Auto-created with dependencies
    • Libraries installed on-the-fly
    • Clean execution environment
    ↓
Test Execution
    • Parallel or sequential
    • Rich output and reporting
    • JUnit XML for CI/CD
```

## Key Concepts

### 1. Serverless-First Design

The framework is optimized for Databricks serverless compute:

- **Automatic Environment Management**: Creates inline environments with your dependencies
- **Fast Startup**: No cluster management overhead
- **Cost-Effective**: Pay only for actual test execution time
- **Scalable**: Automatically handles parallelism

### 2. Databricks Asset Bundle Native

Seamless integration with Databricks Asset Bundles:

- **Auto-Detection**: Finds `databricks.yml` automatically
- **Path Resolution**: Resolves workspace paths based on target
- **Deployment Integration**: Works with `databricks bundle deploy`
- **Multi-Target Support**: Easy dev/staging/prod testing

### 3. Pytest-Style Discovery

Familiar test discovery patterns:

- Files starting with `test_*` (e.g., `test_feature.py`)
- Files ending with `*_test` (e.g., `feature_test.py`)
- Recursive directory search
- Automatic notebook detection

### 4. Remote Execution Only

**Why remote-only?**

- ✅ **Consistency**: Tests run in the same environment as production
- ✅ **Features**: Access to all Databricks features (Delta, MLflow, etc.)
- ✅ **Simplicity**: No local Spark setup required
- ✅ **Reality**: Tests match actual deployment environment

## Common Use Cases

### 1. Bundle Project Testing

```bash
# Deploy
databricks bundle deploy --target dev

# Test
dbx_test run --target dev --profile my-profile
```

### 2. Workspace Testing

```bash
# Upload
dbx_test upload --tests-dir tests \
  --workspace-path /Workspace/Users/you@company.com/tests \
  --profile my-profile

# Test
dbx_test run --tests-dir /Workspace/Users/you@company.com/tests \
  --profile my-profile
```

### 3. CI/CD Pipeline

```bash
dbx_test run --target dev --profile ci \
  --output-format junit \
  --output-format html
```

### 4. Interactive Development

```python
# In a Databricks notebook
from dbx_test import run_notebook_tests
import json

# Your test classes here...

results = run_notebook_tests()
dbutils.notebook.exit(json.dumps(results))
```

## Best Practices

### 1. Use Serverless Compute
- Faster startup times
- Lower costs for testing
- Automatic scaling

### 2. Leverage Asset Bundles
- Simplified deployment
- Environment consistency
- Easy multi-environment testing

### 3. Install Dependencies via Config
```yaml
cluster:
  libraries:
    - whl: "git+https://github.com/org/your-package.git"
```

### 4. Use Parallel Execution for Large Test Suites
```yaml
execution:
  parallel: true
  max_parallel_jobs: 5
```

### 5. Generate Multiple Report Formats
```yaml
reporting:
  formats:
    - "console"  # For development
    - "junit"    # For CI/CD
    - "html"     # For reports
```

## Troubleshooting

### Common Issues

**Bundle not detected?**
- Check `databricks.yml` exists in project root
- Use `--verbose` flag for debugging

**Dependencies not installing?**
- Verify library syntax in config
- Check workspace permissions
- Consider pre-created environments for production

**Tests not found?**
- Ensure files match `test_*` or `*_test` pattern
- Check workspace path is correct
- Use `--verbose` to see discovery process

**Authentication fails?**
```bash
databricks auth profiles
databricks workspace list /
```

## Further Reading

- [Configuration Reference](configuration.md) - All config options
- [API Documentation](../README.md#architecture) - Framework architecture
- [Examples](../examples/) - Real-world examples

## Support

- **Issues**: [GitHub Issues](https://github.com/jsparhamii/dbx_test/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jsparhamii/dbx_test/discussions)
- **Examples**: See `examples/` directory

---

**Ready to get started?** → [Quick Start Guide](../QUICKSTART.md)
