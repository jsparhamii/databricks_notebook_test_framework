# Using Environments with Serverless Compute

## Overview

Databricks Serverless compute requires **environments** to manage dependencies instead of directly specifying libraries. This guide shows you how to create and use environments with `dbx_test`.

## Why Environments?

- **Serverless Requirement**: Serverless tasks don't support the `libraries` field
- **Reusability**: Environments can be shared across multiple jobs and notebooks
- **Performance**: Dependencies are pre-installed and cached for faster execution
- **Consistency**: Same environment across all serverless tasks

## Quick Start

### Step 1: Create an Environment in Databricks

You can create environments via the Databricks UI or API.

#### Option A: Using Databricks UI

1. Go to your Databricks workspace
2. Click on **Compute** in the sidebar
3. Click on the **Environments** tab
4. Click **Create Environment**
5. Configure:
   - **Name**: `dbx_test_env`
   - **Python Version**: `3.10` or higher
   - **Libraries**: Add `git+https://github.com/jsparhamii/dbx_test.git`
6. Click **Create**

#### Option B: Using Databricks CLI/API

```bash
# Create environment using Databricks SDK
databricks environments create \
  --name dbx_test_env \
  --client aws-west \
  --spec '{
    "dependencies": [
      "git+https://github.com/jsparhamii/dbx_test.git",
      "pandas>=2.0.0"
    ]
  }'
```

### Step 2: Configure dbx_test

Update your `config/test_config.yml`:

```yaml
workspace:
  profile: "aws-west"

cluster:
  # Use the environment name you created
  environment_key: "dbx_test_env"
  
  # Serverless is used by default when no cluster settings are specified

execution:
  timeout: 600

reporting:
  output_dir: ".dbx-test-results"
  formats:
    - "console"
    - "junit"
```

### Step 3: Run Tests

```bash
dbx_test run --remote \
  --tests-dir /Workspace/Users/youruser@company.com/tests \
  --profile aws-west
```

That's it! Your tests will run on serverless compute with the environment's dependencies.

## Creating Environments

### Method 1: Databricks Workspace UI

The easiest way for quick setup:

1. Navigate to **Compute** → **Environments**
2. Click **Create Environment**
3. Fill in:
   - **Name**: `dbx_test_env`
   - **Description**: Environment for dbx_test framework
   - **Python Version**: `3.10+`
   - **Libraries**: 
     - `git+https://github.com/jsparhamii/dbx_test.git`
     - Any other dependencies your tests need

### Method 2: Databricks REST API

For automation and CI/CD:

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient(profile="aws-west")

# Create environment
env = w.environments.create(
    name="dbx_test_env",
    spec={
        "dependencies": [
            "git+https://github.com/jsparhamii/dbx_test.git",
            "pandas>=2.0.0",
            "numpy>=1.24.0",
        ],
        "python_version": "3.10",
    }
)

print(f"Environment created: {env.name}")
```

### Method 3: Databricks Asset Bundles (DAB)

Include in your `databricks.yml`:

```yaml
environments:
  dbx_test_env:
    spec:
      dependencies:
        - "git+https://github.com/jsparhamii/dbx_test.git"
        - "pandas>=2.0.0"
      python_version: "3.10"
      
resources:
  jobs:
    my_tests:
      tasks:
        - task_key: run_tests
          environment_key: dbx_test_env
          # ...rest of task config
```

## Environment Specifications

### Adding Dependencies

Environments support various dependency types:

```yaml
# In Databricks Environment Configuration
dependencies:
  # PyPI packages
  - "dbx_test==0.1.0"
  - "pandas>=2.0.0"
  - "numpy==1.24.3"
  
  # Git repositories
  - "git+https://github.com/jsparhamii/dbx_test.git"
  - "git+https://github.com/user/repo.git@branch"
  - "git+https://github.com/user/repo.git@v1.0.0"
  
  # Wheel files from DBFS
  - "/dbfs/FileStore/wheels/custom_lib-1.0.0-py3-none-any.whl"
```

### Python Version

Specify the Python version:

```yaml
python_version: "3.10"  # or "3.11"
```

### Environment Variables

You can also set environment variables:

```yaml
environment_variables:
  MY_CONFIG: "value"
  API_ENDPOINT: "https://api.example.com"
```

## Complete Example

### 1. Create Environment with Multiple Dependencies

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient(profile="aws-west")

env = w.environments.create(
    name="ml_test_env",
    spec={
        "dependencies": [
            # Testing framework
            "git+https://github.com/jsparhamii/dbx_test.git",
            
            # Data science stack
            "pandas==2.0.3",
            "numpy==1.24.3",
            "scikit-learn==1.3.0",
            
            # Databricks
            "databricks-sdk>=0.20.0",
            
            # Custom library from DBFS
            "/dbfs/FileStore/wheels/company_lib-1.0.0-py3-none-any.whl",
        ],
        "python_version": "3.10",
        "environment_variables": {
            "TEST_MODE": "true",
        }
    }
)

print(f"✓ Environment created: {env.name}")
```

### 2. Configure dbx_test

```yaml
# config/test_config.yml
workspace:
  profile: "aws-west"

cluster:
  environment_key: "ml_test_env"

execution:
  timeout: 900
  parallel: true
  max_parallel_jobs: 5

reporting:
  output_dir: ".dbx-test-results"
  formats:
    - "console"
    - "junit"
    - "html"
```

### 3. Run Tests

```bash
dbx_test run --remote \
  --tests-dir /Workspace/Users/james.parham@databricks.com/.bundle/my_project/dev/files/tests \
  --profile aws-west \
  --verbose
```

## Cluster vs Serverless with Libraries

### Serverless (with environment_key)

```yaml
cluster:
  environment_key: "dbx_test_env"
  # No other cluster settings = serverless
```

**Pros:**
- ✅ Fast startup (no cluster creation)
- ✅ Cost-effective (pay per use)
- ✅ Auto-scaling
- ✅ No cluster management

**Cons:**
- ❌ Requires pre-created environment
- ❌ Limited customization

### Cluster (with libraries)

```yaml
cluster:
  libraries:
    - pypi:
        package: "git+https://github.com/jsparhamii/dbx_test.git"
  
  # Option A: Use existing cluster
  cluster_id: "0123-456789-abc123"
  
  # Option B: Create new cluster
  size: "S"
  spark_version: "14.3.x-scala2.12"
```

**Pros:**
- ✅ More control over cluster configuration
- ✅ Can use custom node types
- ✅ Works with complex library setups

**Cons:**
- ❌ Slower startup (cluster creation)
- ❌ Higher cost (minimum cluster time)
- ❌ Requires cluster management

## Best Practices

### 1. Use Environments for Serverless

If using serverless (recommended for most use cases):
```yaml
cluster:
  environment_key: "your_environment_name"
  # Don't specify libraries here
```

### 2. Use Libraries for Clusters

If using a dedicated cluster:
```yaml
cluster:
  cluster_id: "0123-456789-abc123"  # or size: "S"
  libraries:
    - pypi:
        package: "git+https://github.com/jsparhamii/dbx_test.git"
```

### 3. Version Your Environments

Create versioned environments for reproducibility:
- `dbx_test_env_v1`
- `dbx_test_env_v2`
- `dbx_test_env_prod`

### 4. Share Environments Across Teams

Environments can be reused:
```yaml
# Team A
cluster:
  environment_key: "shared_ml_env"

# Team B
cluster:
  environment_key: "shared_ml_env"
```

### 5. Test Locally First

Before creating an environment, test dependencies locally:
```bash
pip install git+https://github.com/jsparhamii/dbx_test.git pandas
python -m pytest tests/
```

## Troubleshooting

### "Environment not found"

**Error:** `Environment 'dbx_test_env' does not exist`

**Solution:**
1. Check environment name: `databricks environments list --profile aws-west`
2. Verify you're using the correct workspace/profile
3. Create the environment if it doesn't exist

### "Environment creation failed"

**Error:** Dependency resolution conflicts

**Solution:**
```yaml
# Be explicit with versions
dependencies:
  - "pandas==2.0.3"  # Not "pandas>=2.0.0"
  - "numpy==1.24.3"  # Not "numpy"
```

### "Import error in test"

**Error:** `ModuleNotFoundError: No module named 'dbx_test'`

**Solution:**
1. Verify environment includes `dbx_test`:
   ```bash
   databricks environments get dbx_test_env --profile aws-west
   ```
2. Check environment status (should be "READY")
3. Update environment if needed

### "Slow test startup"

**Cause:** Environment not ready or needs rebuilding

**Solution:**
- Environments are cached after first use
- Subsequent runs will be faster
- Consider using a persistent cluster for development

## Migration Guide

### From Libraries to Environments

**Before (won't work with serverless):**
```yaml
cluster:
  libraries:
    - pypi:
        package: "git+https://github.com/jsparhamii/dbx_test.git"
```

**After (works with serverless):**
```yaml
cluster:
  environment_key: "dbx_test_env"
```

**Migration Steps:**
1. Create environment with your libraries
2. Update config to use `environment_key`
3. Remove `libraries` section (only needed for clusters)
4. Test with `--verbose` flag

## Summary

| Feature | Serverless + Environment | Cluster + Libraries |
|---------|-------------------------|---------------------|
| **Setup** | Create environment once | Configure each time |
| **Startup** | Fast (~30s) | Slower (2-5 min) |
| **Cost** | Pay per use | Minimum cluster time |
| **Management** | Minimal | More involved |
| **Best For** | Production, CI/CD | Development, debugging |

**Recommendation:** Use serverless with environments for production workloads, and clusters with libraries for development.

## Next Steps

1. **Create your environment** in Databricks workspace
2. **Update config** with `environment_key`
3. **Run tests** with `--remote` flag
4. **Monitor** execution in Databricks UI

Happy testing! 🚀

