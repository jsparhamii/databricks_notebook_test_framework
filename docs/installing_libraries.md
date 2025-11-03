# Installing Libraries on Test Clusters

## Overview

When running tests remotely on Databricks, you need to ensure that required libraries (including `dbx_test` itself) are available on the cluster. This guide shows you how to configure library installation.

## Quick Start

Add the `libraries` configuration to your `config/test_config.yml`:

```yaml
cluster:
  libraries:
    - pypi:
        package: "dbx_test==0.1.0"
```

That's it! The `dbx_test` library will now be automatically installed on the cluster when running tests.

## Configuration Options

### Option 1: Install from PyPI (Recommended)

If your package is published on PyPI:

```yaml
cluster:
  libraries:
    - pypi:
        package: "dbx_test==0.1.0"
    - pypi:
        package: "pandas>=2.0.0"
    - pypi:
        package: "numpy>=1.24.0"
```

### Option 2: Install from Wheel File

Upload your wheel file to DBFS or workspace, then reference it:

```yaml
cluster:
  libraries:
    - whl: "dbfs:/FileStore/wheels/dbx_test-0.1.0-py3-none-any.whl"
    - whl: "/Workspace/Users/youruser@company.com/libs/custom_lib-1.0.0-py3-none-any.whl"
```

**To upload a wheel file:**

```bash
# Build the wheel
cd /Users/james.parham/development/dbx_test
python -m build

# Upload to DBFS
databricks fs cp dist/dbx_test-0.1.0-py3-none-any.whl dbfs:/FileStore/wheels/ --profile aws-west

# Or upload to workspace
databricks workspace import dist/dbx_test-0.1.0-py3-none-any.whl /Workspace/Users/youruser@company.com/libs/dbx_test-0.1.0-py3-none-any.whl --profile aws-west
```

### Option 3: Install from Git Repository

Install directly from a Git repository:

```yaml
cluster:
  libraries:
    - pypi:
        package: "git+https://github.com/jsparhamii/dbx_test.git"
    # Or specific branch/tag
    - pypi:
        package: "git+https://github.com/jsparhamii/dbx_test.git@main"
    - pypi:
        package: "git+https://github.com/jsparhamii/dbx_test.git@v0.1.0"
```

### Option 4: Install from Maven (for Java/Scala libraries)

```yaml
cluster:
  libraries:
    - maven:
        coordinates: "com.databricks:spark-xml_2.12:0.17.0"
```

### Option 5: Install from JAR

```yaml
cluster:
  libraries:
    - jar: "dbfs:/FileStore/jars/my-custom-lib.jar"
```

## Complete Configuration Example

```yaml
# config/test_config.yml

workspace:
  profile: "aws-west"

cluster:
  # Libraries to install
  libraries:
    # Core testing framework
    - pypi:
        package: "dbx_test==0.1.0"
    
    # Other dependencies your tests need
    - pypi:
        package: "pandas>=2.0.0"
    - pypi:
        package: "pyspark>=3.5.0"
    
    # Custom wheel from DBFS
    - whl: "dbfs:/FileStore/wheels/my_custom_lib-1.0.0-py3-none-any.whl"
  
  # Use serverless compute (recommended)
  # Libraries will be installed automatically

execution:
  timeout: 600
  parallel: false

reporting:
  output_dir: ".dbx-test-results"
  formats:
    - "console"
    - "junit"
```

## How It Works

1. **Configuration Loading**: When you run `dbx_test run --remote`, the framework loads your config file
2. **Job Submission**: The framework submits a notebook job to Databricks with the specified libraries
3. **Library Installation**: Databricks automatically installs the libraries before running your tests
4. **Test Execution**: Your test notebooks can now import and use the libraries

## Using with Databricks Asset Bundles

If you're using Databricks Asset Bundles (DAB), you might already have libraries configured in your `databricks.yml`. You can still use `dbx_test` configuration for test-specific libraries:

```yaml
# databricks.yml (your bundle config)
resources:
  jobs:
    my_job:
      libraries:
        - pypi:
            package: "my-production-lib==1.0.0"

# config/test_config.yml (your test config)
cluster:
  libraries:
    - pypi:
        package: "dbx_test==0.1.0"
    - pypi:
        package: "pytest>=7.0.0"
```

## Running Tests with Libraries

Once configured, just run your tests normally:

```bash
dbx_test run --remote \
  --tests-dir /Workspace/Users/james.parham@databricks.com/.bundle/my_app/dev/files/tests \
  --profile aws-west
```

The framework will:
1. ✅ Load the library configuration from `config/test_config.yml`
2. ✅ Submit the job with library installation instructions
3. ✅ Wait for libraries to install
4. ✅ Run your tests with all libraries available

## Troubleshooting

### "ImportError: No module named 'dbx_test'"

**Cause**: The library is not configured or failed to install

**Solution**:
1. Check your `config/test_config.yml` includes the library
2. Run with `--verbose` to see installation logs
3. Verify the library format matches Databricks SDK expectations

### "Library installation timeout"

**Cause**: Large libraries or slow network

**Solution**:
```yaml
execution:
  timeout: 1200  # Increase timeout to 20 minutes
```

### "Conflicting library versions"

**Cause**: Multiple versions of the same library specified

**Solution**:
```yaml
cluster:
  libraries:
    # Use specific versions
    - pypi:
        package: "pandas==2.0.3"  # Not "pandas>=2.0.0"
```

### "Wheel file not found"

**Cause**: Incorrect path or file not uploaded

**Solution**:
```bash
# Verify file exists
databricks fs ls dbfs:/FileStore/wheels/ --profile aws-west

# Re-upload if needed
databricks fs cp dist/dbx_test-0.1.0-py3-none-any.whl \
  dbfs:/FileStore/wheels/ --profile aws-west --overwrite
```

## Best Practices

1. **Pin Versions**: Use exact versions (`==`) for reproducibility
   ```yaml
   - pypi:
       package: "dbx_test==0.1.0"  # Good
   # - pypi:
   #     package: "dbx_test"  # Bad: unpredictable
   ```

2. **Use Wheel Files for Development**: Faster iteration for custom libraries
   ```yaml
   - whl: "dbfs:/FileStore/wheels/dbx_test-0.1.0-py3-none-any.whl"
   ```

3. **Group by Purpose**: Organize libraries logically
   ```yaml
   libraries:
     # Testing framework
     - pypi:
         package: "dbx_test==0.1.0"
     
     # Data processing
     - pypi:
         package: "pandas==2.0.3"
     - pypi:
         package: "numpy==1.24.3"
     
     # Custom libraries
     - whl: "dbfs:/FileStore/wheels/my_lib-1.0.0-py3-none-any.whl"
   ```

4. **Test Locally First**: Ensure libraries work together
   ```bash
   pip install dbx_test pandas numpy
   python -m pytest tests/
   ```

## Examples

### Example 1: Simple PyPI Installation

```yaml
cluster:
  libraries:
    - pypi:
        package: "dbx_test==0.1.0"
```

```bash
dbx_test run --remote --tests-dir /Workspace/Users/me/tests --profile prod
```

### Example 2: Development with Local Wheel

```bash
# Build wheel
cd /path/to/dbx_test
python -m build

# Upload to DBFS
databricks fs cp dist/dbx_test-0.1.0-py3-none-any.whl \
  dbfs:/FileStore/wheels/ --profile aws-west --overwrite
```

```yaml
cluster:
  libraries:
    - whl: "dbfs:/FileStore/wheels/dbx_test-0.1.0-py3-none-any.whl"
```

```bash
dbx_test run --remote --tests-dir /Workspace/Users/me/tests --profile aws-west
```

### Example 3: Git Repository (CI/CD)

```yaml
cluster:
  libraries:
    - pypi:
        package: "git+https://github.com/jsparhamii/dbx_test.git@${GIT_COMMIT}"
```

### Example 4: Multiple Dependencies

```yaml
cluster:
  libraries:
    # Framework
    - pypi:
        package: "dbx_test==0.1.0"
    
    # Data science stack
    - pypi:
        package: "pandas==2.0.3"
    - pypi:
        package: "numpy==1.24.3"
    - pypi:
        package: "scikit-learn==1.3.0"
    
    # Databricks libraries
    - pypi:
        package: "databricks-sdk>=0.20.0"
    
    # Custom wheel
    - whl: "dbfs:/FileStore/wheels/company_lib-2.1.0-py3-none-any.whl"
```

## Summary

To ensure `dbx_test` is available when running remote tests:

1. **Configure libraries** in `config/test_config.yml`
2. **Choose installation method**: PyPI, wheel, or Git
3. **Run tests** with `--remote` flag
4. **Libraries auto-install** on the cluster

The framework handles the rest!

