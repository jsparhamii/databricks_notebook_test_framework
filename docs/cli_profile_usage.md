# CLI Profile Usage Examples

## Quick Examples

### Switch Between Profiles Easily

```bash
# Dev testing
dbx-test run --remote --profile dev

# Staging validation
dbx-test run --remote --profile staging

# Production smoke tests
dbx-test run --remote --profile prod
```

### Combine with Other Options

```bash
# Run specific tests on prod
dbx-test run --remote --profile prod --pattern "*smoke*"

# Parallel execution on staging
dbx-test run --remote --profile staging --parallel

# Verbose output with custom config
dbx-test run --remote --profile dev --config custom_config.yml --verbose
```

## Benefits of CLI Profile Override

### 1. **One Config, Multiple Environments**

Create a single `config/test_config.yml` with cluster and execution settings:

```yaml
# config/test_config.yml
# No workspace section needed!

cluster:
  cluster_id: "shared-test-cluster"

execution:
  timeout: 600
  parallel: true
```

Then switch profiles via CLI:

```bash
dbx-test run --remote --profile dev    # Uses dev workspace
dbx-test run --remote --profile prod   # Uses prod workspace
```

### 2. **CI/CD Flexibility**

In your CI/CD pipeline:

```yaml
# GitHub Actions
- name: Run Tests
  env:
    TEST_PROFILE: ${{ matrix.profile }}
  run: |
    dbx-test run --remote --profile $TEST_PROFILE

strategy:
  matrix:
    profile: [dev, staging, prod]
```

### 3. **Quick Ad-Hoc Testing**

```bash
# Test on coworker's workspace
dbx-test run --remote --profile alice-workspace

# Test on different region
dbx-test run --remote --profile us-west-2

# Test on customer workspace
dbx-test run --remote --profile customer-demo
```

## Setup Multiple Profiles

Configure multiple Databricks workspaces:

```bash
# Dev workspace
databricks configure --token --profile dev
# Enter host: https://dev.cloud.databricks.com
# Enter token: dapi-dev-token

# Staging workspace
databricks configure --token --profile staging
# Enter host: https://staging.cloud.databricks.com
# Enter token: dapi-staging-token

# Production workspace
databricks configure --token --profile prod
# Enter host: https://prod.cloud.databricks.com
# Enter token: dapi-prod-token
```

This creates `~/.databrickscfg`:

```ini
[dev]
host = https://dev.cloud.databricks.com
token = dapi-dev-token

[staging]
host = https://staging.cloud.databricks.com
token = dapi-staging-token

[prod]
host = https://prod.cloud.databricks.com
token = dapi-prod-token
```

## Priority Order

The profile is determined in this order:

1. **CLI `--profile` flag** (highest priority)
2. **Config file `profile` setting**
3. **Environment variable** `DATABRICKS_CONFIG_PROFILE`
4. **DEFAULT profile** in `~/.databrickscfg`

### Example Priority

```yaml
# config/test_config.yml
workspace:
  profile: "dev"  # This is used...
```

```bash
# Unless you override with CLI:
dbx-test run --remote --profile prod  # This takes priority!
```

## Real-World Workflows

### Developer Workflow

```bash
# Morning: Test locally
dbx-test run --local

# Afternoon: Push to dev
dbx-test run --remote --profile dev

# Before PR: Validate on staging
dbx-test run --remote --profile staging --pattern "*integration*"
```

### Release Workflow

```bash
# 1. Run full test suite on staging
dbx-test run --remote --profile staging --verbose

# 2. If passed, smoke test on prod
dbx-test run --remote --profile prod --pattern "*smoke*"

# 3. Deploy to prod
# ...
```

### Multi-Region Testing

```bash
# Test in US
dbx-test run --remote --profile us-east-1

# Test in EU
dbx-test run --remote --profile eu-west-1

# Test in Asia
dbx-test run --remote --profile ap-south-1
```

## Upload Command

The upload command also supports `--profile`:

```bash
# Upload tests to dev workspace
dbx-test upload \
  --workspace-path "/Workspace/tests" \
  --profile dev

# Upload to prod workspace
dbx-test upload \
  --workspace-path "/Workspace/tests" \
  --profile prod
```

## Scripting Examples

### Bash Script

```bash
#!/bin/bash
# test_all_environments.sh

PROFILES=("dev" "staging" "prod")

for profile in "${PROFILES[@]}"; do
  echo "Testing on $profile..."
  dbx-test run --remote --profile "$profile" --pattern "*smoke*"
  
  if [ $? -ne 0 ]; then
    echo "Tests failed on $profile"
    exit 1
  fi
done

echo "All environments passed!"
```

### Python Script

```python
#!/usr/bin/env python3
import subprocess
import sys

profiles = ["dev", "staging", "prod"]

for profile in profiles:
    print(f"Testing on {profile}...")
    result = subprocess.run([
        "dbx-test", "run",
        "--remote",
        "--profile", profile,
        "--pattern", "*smoke*"
    ])
    
    if result.returncode != 0:
        print(f"Tests failed on {profile}")
        sys.exit(1)

print("All environments passed!")
```

### Makefile

```makefile
.PHONY: test-dev test-staging test-prod test-all

test-dev:
	dbx-test run --remote --profile dev

test-staging:
	dbx-test run --remote --profile staging

test-prod:
	dbx-test run --remote --profile prod --pattern "*smoke*"

test-all: test-dev test-staging test-prod
	@echo "All tests passed!"
```

Run with:
```bash
make test-dev
make test-staging
make test-all
```

## Tips and Tricks

### 1. **List Your Profiles**

```bash
# Check configured profiles
cat ~/.databrickscfg | grep '^\[' | tr -d '[]'
```

### 2. **Verify Profile**

```bash
# Test connection to a profile
databricks workspace list --profile dev
```

### 3. **Environment-Specific Tests**

```bash
# Run different test suites per environment
dbx-test run --remote --profile dev --pattern "*"           # All tests
dbx-test run --remote --profile staging --pattern "*integration*"  # Integration only
dbx-test run --remote --profile prod --pattern "*smoke*"    # Smoke tests only
```

### 4. **Default Profile Shortcut**

If you use one profile 90% of the time, set it as DEFAULT:

```ini
[DEFAULT]
host = https://your-main-workspace.cloud.databricks.com
token = dapi-token
```

Then just:
```bash
dbx-test run --remote  # Uses DEFAULT
```

Only specify `--profile` when you need a different one:
```bash
dbx-test run --remote --profile prod  # Override to prod
```

### 5. **Config File for Shared Settings**

Keep cluster/execution settings in config, but switch profiles:

```yaml
# config/shared_test_config.yml
cluster:
  size: "M"
  
execution:
  timeout: 600
  parallel: true

# No workspace section - use CLI profiles
```

```bash
dbx-test run --remote --profile dev --config config/shared_test_config.yml
dbx-test run --remote --profile prod --config config/shared_test_config.yml
```

## Summary

The `--profile` CLI option gives you:

✅ **Flexibility** - Switch workspaces without editing files
✅ **Simplicity** - One config file, many environments  
✅ **Speed** - Quick ad-hoc testing
✅ **CI/CD Ready** - Easy integration with pipelines
✅ **Team Friendly** - Share config files, customize profiles

Use it to make your testing workflow smooth and efficient! 🚀

