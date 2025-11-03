# Cluster Configuration Guide

The framework supports three ways to run tests on Databricks:

## 1. Existing Cluster (Recommended for Development)

Use an existing interactive or job cluster. This is **fastest** since the cluster is already running.

### Configuration

```yaml
cluster:
  cluster_id: "1234-567890-abcdef"
```

### How to Find Your Cluster ID

**Method 1: From Databricks UI**
1. Go to **Compute** in your workspace
2. Click on your cluster
3. Look at the URL: `https://<workspace>/compute/<cluster-id>/configuration`
4. Or look under **Advanced Options** → **Tags**

**Method 2: Using Databricks CLI**
```bash
databricks clusters list
```

**Method 3: Programmatically**
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
for cluster in w.clusters.list():
    print(f"{cluster.cluster_name}: {cluster.cluster_id}")
```

### Advantages
- ✅ Fastest - no cluster startup time
- ✅ Cheaper - reuse existing compute
- ✅ Consistent - same environment every time
- ✅ Great for development/debugging

### When to Use
- Local development and testing
- Debugging test failures
- Running tests frequently
- Using a shared development cluster

## 2. Serverless Compute (Default)

Databricks serverless compute automatically provisions and scales resources. This is the **simplest** option.

### Configuration

Leave cluster section empty or omit entirely:

```yaml
cluster: {}
```

Or just don't specify cluster at all:

```yaml
workspace:
  profile: "DEFAULT"

# No cluster section needed!

execution:
  timeout: 600
```

### Advantages
- ✅ No cluster management needed
- ✅ Fast startup (typically < 1 minute)
- ✅ Auto-scaling
- ✅ Pay only for what you use
- ✅ Ideal for CI/CD pipelines

### When to Use
- CI/CD pipelines
- Automated testing
- Production test runs
- When you don't have a running cluster

### Requirements
- Workspace must have serverless enabled
- Available in most regions
- Check with your workspace admin if unsure

## 3. New Cluster (Job-Specific)

Create a new cluster for each test run. Good for **isolation** but slowest.

### T-Shirt Sizing

Quick configuration using predefined sizes:

```yaml
cluster:
  size: "M"  # S, M, L, or XL
  spark_version: "13.3.x-scala2.12"
```

**Size Reference:**

| Size | Workers | Node Type | Use Case |
|------|---------|-----------|----------|
| S | 1 | i3.xlarge | Small datasets, quick tests |
| M | 2-4 (autoscale) | i3.xlarge | Medium datasets, most tests |
| L | 4-8 (autoscale) | i3.2xlarge | Large datasets, performance tests |
| XL | 8-16 (autoscale) | i3.4xlarge | Very large datasets, stress tests |

### Custom Configuration

Full control over cluster specs:

```yaml
cluster:
  spark_version: "13.3.x-scala2.12"
  node_type_id: "i3.xlarge"
  driver_node_type_id: "i3.2xlarge"
  
  # Fixed workers
  num_workers: 3
  
  # OR autoscaling
  # autoscale_min_workers: 2
  # autoscale_max_workers: 8
  
  # Cluster policy
  cluster_policy_id: "ABC123DEF456"
  
  # Spark configuration
  spark_conf:
    "spark.sql.shuffle.partitions": "8"
    "spark.databricks.delta.preview.enabled": "true"
  
  # Environment variables
  spark_env_vars:
    ENV: "test"
  
  # Custom tags
  custom_tags:
    project: "testing"
    team: "data-engineering"
```

### Advantages
- ✅ Complete isolation per test run
- ✅ Reproducible environment
- ✅ Custom configuration
- ✅ Specific Spark versions

### Disadvantages
- ❌ Slowest (5-10 minutes startup)
- ❌ Most expensive
- ❌ Overhead for small tests

### When to Use
- Need specific Spark version
- Need custom cluster configuration
- Require complete isolation
- Running infrequently

## Decision Guide

### Choose Existing Cluster When:
- 🔵 Developing and debugging locally
- 🔵 Running tests frequently (multiple times per day)
- 🔵 Have a dedicated test cluster
- 🔵 Need fastest feedback loop

### Choose Serverless When:
- 🟢 Running in CI/CD pipelines
- 🟢 Automated testing
- 🟢 Don't have an existing cluster
- 🟢 Want simplicity and auto-scaling

### Choose New Cluster When:
- 🔴 Need specific Spark version
- 🔴 Need custom cluster configuration
- 🔴 Require complete test isolation
- 🔴 Have specific compliance requirements

## Examples

### Example 1: Development Setup

```yaml
# config/test_config_dev.yml
workspace:
  profile: "dev"

cluster:
  cluster_id: "1234-567890-dev-cluster"

execution:
  timeout: 300
```

Run:
```bash
dbx_test run --remote --config config/test_config_dev.yml
```

### Example 2: CI/CD Pipeline (Serverless)

```yaml
# config/test_config_ci.yml
workspace:
  # Uses environment variables
  
# No cluster config - uses serverless

execution:
  timeout: 600
  parallel: true
  max_parallel_jobs: 5
```

In CI:
```bash
export DATABRICKS_HOST=$DATABRICKS_HOST
export DATABRICKS_TOKEN=$DATABRICKS_TOKEN
dbx_test run --remote --config config/test_config_ci.yml
```

### Example 3: Production Validation

```yaml
# config/test_config_prod.yml
workspace:
  profile: "prod"

cluster:
  size: "L"
  spark_version: "13.3.x-scala2.12"
  cluster_policy_id: "prod-policy-id"
  custom_tags:
    environment: "production"
    purpose: "validation"

execution:
  timeout: 1800
  max_retries: 1
```

### Example 4: Multiple Environments

```yaml
# config/test_config.yml
workspace:
  profile: "${ENV_PROFILE}"  # Set via environment variable

cluster:
  cluster_id: "${CLUSTER_ID}"  # Set via environment variable

execution:
  timeout: 600
```

Run with:
```bash
# Dev
export ENV_PROFILE="dev"
export CLUSTER_ID="1234-dev-cluster"
dbx_test run --remote

# Prod
export ENV_PROFILE="prod"
export CLUSTER_ID="5678-prod-cluster"
dbx_test run --remote
```

## Cost Optimization

### Development
```yaml
cluster:
  cluster_id: "shared-dev-cluster"  # Share a cluster
```
**Cost**: Lowest (reuse existing)

### CI/CD
```yaml
cluster: {}  # Serverless
```
**Cost**: Medium (pay for actual usage)

### Production
```yaml
cluster:
  size: "M"  # Right-size for workload
```
**Cost**: Predictable

## Troubleshooting

### "Cluster not found"
- Check cluster ID is correct
- Ensure cluster is running
- Verify you have access to the cluster

### "Serverless not available"
- Check if serverless is enabled in your workspace
- Contact your workspace admin
- Fall back to existing cluster or create new

### "Cluster startup timeout"
- Increase `execution.timeout` in config
- Consider using existing cluster instead
- Check cluster policy restrictions

### "Permission denied"
- Ensure you can restart/use the cluster
- Check cluster access controls
- Verify you're in the correct workspace

## Best Practices

1. **Development**: Use existing cluster for fast iteration
2. **CI/CD**: Use serverless for simplicity and auto-scaling
3. **Production**: Create new cluster with specific config for isolation
4. **Shared Clusters**: Tag appropriately and manage access
5. **Cost Control**: Turn off clusters when not in use
6. **Monitoring**: Track test execution costs by cluster

## Summary

| Method | Speed | Cost | Use Case |
|--------|-------|------|----------|
| **Existing Cluster** | ⚡️⚡️⚡️ Fastest | 💰 Lowest | Development |
| **Serverless** | ⚡️⚡️ Fast | 💰💰 Medium | CI/CD |
| **New Cluster** | ⚡️ Slowest | 💰💰💰 Highest | Isolation |

Choose the option that best fits your workflow and requirements! 🚀

