# Configuration Guide

This guide covers all configuration options for the Databricks Notebook Test Framework.

## Configuration File Structure

The framework uses YAML for configuration. The default location is `config/test_config.yml`.

## Complete Configuration Reference

### Workspace Configuration

```yaml
workspace:
  # Databricks workspace URL (required)
  host: "https://your-workspace.cloud.databricks.com"
  
  # Authentication token (use one of these methods)
  # Method 1: Direct token (not recommended for production)
  token: "dapi..."
  
  # Method 2: Environment variable (recommended)
  token_env: "DATABRICKS_TOKEN"
```

**Authentication Best Practices:**
- For local development: Use `token_env` and set the environment variable
- For CI/CD: Use secrets management (GitHub Secrets, Azure Key Vault, etc.)
- Never commit tokens directly to version control

### Cluster Configuration

```yaml
cluster:
  # T-shirt sizing (S, M, L, XL)
  size: "M"
  
  # Spark version
  spark_version: "13.3.x-scala2.12"
  
  # Node types (optional, defaults based on size)
  node_type_id: "i3.xlarge"
  driver_node_type_id: "i3.xlarge"
  
  # Explicit worker configuration (overrides size)
  num_workers: 2
  # OR use autoscaling
  autoscale_min_workers: 2
  autoscale_max_workers: 4
  
  # Cluster policy (optional)
  cluster_policy_id: "ABC123DEF456"
  
  # Spark configuration
  spark_conf:
    "spark.databricks.delta.preview.enabled": "true"
    "spark.sql.adaptive.enabled": "true"
    "spark.sql.shuffle.partitions": "8"
  
  # Environment variables
  spark_env_vars:
    "ENV": "dev"
    "REGION": "us-west-2"
  
  # Custom tags
  custom_tags:
    project: "data-platform"
    team: "data-engineering"
    cost_center: "12345"
```

**Cluster Size Guide:**

| Size | Workers | Node Type | Use Case |
|------|---------|-----------|----------|
| S | 1 | i3.xlarge | Small datasets, quick tests |
| M | 2-4 (autoscale) | i3.xlarge | Medium datasets, most tests |
| L | 4-8 (autoscale) | i3.2xlarge | Large datasets, performance tests |
| XL | 8-16 (autoscale) | i3.4xlarge | Very large datasets, stress tests |

### Execution Configuration

```yaml
execution:
  # Timeout per test in seconds
  timeout: 600
  
  # Maximum retry attempts on failure
  max_retries: 2
  
  # Enable parallel execution (remote only)
  parallel: false
  
  # Maximum concurrent jobs when parallel is enabled
  max_parallel_jobs: 5
  
  # Poll interval for checking job status (seconds)
  poll_interval: 10
```

**Execution Tips:**
- Set `timeout` based on your longest-running test
- Use `parallel: true` for faster execution with many tests
- Limit `max_parallel_jobs` to avoid overwhelming your workspace

### Paths Configuration

```yaml
paths:
  # Workspace root path for uploading notebooks
  workspace_root: "/Workspace/Repos/production/tests"
  
  # Glob pattern to match test files
  test_pattern: "**/*_test.py"
  
  # Local tests directory
  local_tests_dir: "tests"
```

**Pattern Examples:**
- `**/*_test.py` - All Python test files recursively
- `**/*_test.ipynb` - All Jupyter notebook test files
- `integration/*_test.py` - Only integration tests
- `**/*_test.*` - Both .py and .ipynb files

### Reporting Configuration

```yaml
reporting:
  # Output directory for test results
  output_dir: ".dbx_test-results"
  
  # Report formats to generate
  formats:
    - "junit"    # JUnit XML for CI/CD
    - "console"  # Rich console output
    - "json"     # JSON format
    - "html"     # HTML report
  
  # Fail CI/CD pipeline on test failures
  fail_on_error: true
  
  # Verbose output
  verbose: false
```

### Parameters Configuration

```yaml
# Default parameters passed to all test notebooks
parameters:
  environment: "dev"
  region: "us-west-2"
  debug_mode: "false"
```

## Environment-Specific Configuration

You can create multiple configuration files for different environments:

```
config/
├── test_config.yml         # Default/dev
├── test_config_prod.yml    # Production
└── test_config_ci.yml      # CI/CD
```

Use with:
```bash
dbx_test run --remote --config config/test_config_prod.yml
```

## Configuration Overrides

### Command-line Overrides

Some settings can be overridden via CLI:

```bash
# Override parallel execution
dbx_test run --remote --parallel

# Override test pattern
dbx_test run --local --pattern "*integration*"

# Override verbose mode
dbx_test run --remote --verbose
```

### Environment Variables

The framework supports these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABRICKS_TOKEN` | Auth token | - |
| `DATABRICKS_HOST` | Workspace URL | - |
| `DBX_TEST_CONFIG` | Config file path | `config/test_config.yml` |

## Example Configurations

### Development Environment

```yaml
workspace:
  host: "https://dev-workspace.cloud.databricks.com"
  token_env: "DATABRICKS_TOKEN"

cluster:
  size: "S"
  spark_version: "13.3.x-scala2.12"

execution:
  timeout: 300
  parallel: false

parameters:
  environment: "dev"
```

### CI/CD Environment

```yaml
workspace:
  host: "https://ci-workspace.cloud.databricks.com"
  token_env: "DATABRICKS_TOKEN"

cluster:
  size: "M"
  spark_version: "13.3.x-scala2.12"
  cluster_policy_id: "ci-policy-id"
  custom_tags:
    ci_build: "true"

execution:
  timeout: 600
  max_retries: 3
  parallel: true
  max_parallel_jobs: 10

reporting:
  formats:
    - "junit"
    - "json"
  fail_on_error: true
```

### Production Validation

```yaml
workspace:
  host: "https://prod-workspace.cloud.databricks.com"
  token_env: "DATABRICKS_PROD_TOKEN"

cluster:
  size: "L"
  spark_version: "13.3.x-scala2.12"
  cluster_policy_id: "prod-policy-id"
  custom_tags:
    environment: "production"
    validated: "true"

execution:
  timeout: 1800
  max_retries: 1
  parallel: true
  max_parallel_jobs: 3

parameters:
  environment: "prod"
  validation_mode: "true"
```

## Troubleshooting

### Common Issues

**Issue: "Configuration file not found"**
- Solution: Ensure the config file exists at the specified path
- Use `--config` flag to specify custom path

**Issue: "Databricks token not found"**
- Solution: Set the `DATABRICKS_TOKEN` environment variable
- Or specify `token` directly in config (not recommended)

**Issue: "Cluster creation failed"**
- Solution: Check cluster policy compatibility
- Verify node type availability in your region
- Reduce cluster size

**Issue: "Timeout errors"**
- Solution: Increase `execution.timeout`
- Check notebook performance
- Reduce test data size

