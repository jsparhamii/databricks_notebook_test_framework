# Databricks CLI Authentication Guide

The framework now supports **Databricks CLI authentication**, making it easier to connect to your workspaces without managing tokens manually.

## Quick Start

### 1. Install Databricks CLI

```bash
pip install databricks-cli
```

### 2. Configure Authentication

```bash
databricks configure --token
```

You'll be prompted for:
- **Databricks Host**: Your workspace URL (e.g., `https://your-workspace.cloud.databricks.com`)
- **Token**: Your personal access token

### 3. Run Tests

That's it! The framework will automatically use your CLI configuration:

```bash
dbx_test run --remote
```

## Authentication Methods

The framework supports multiple authentication methods with the following priority:

### Priority 1: Explicit Configuration

Specify in `config/test_config.yml`:

```yaml
workspace:
  host: "https://your-workspace.cloud.databricks.com"
  token: "dapi..."
```

**Note**: Not recommended for production (tokens in files).

### Priority 2: Environment Variables

```bash
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi..."
```

Leave workspace config empty or omit the file entirely.

### Priority 3: Databricks CLI Profile (RECOMMENDED)

```yaml
workspace:
  profile: "DEFAULT"  # Uses ~/.databrickscfg
```

Or use environment variable:
```bash
export DATABRICKS_CONFIG_PROFILE="dev"
```

### Priority 4: Default Authentication Chain

If nothing is specified, the Databricks SDK uses its default authentication chain:
1. Environment variables (`DATABRICKS_HOST`, `DATABRICKS_TOKEN`)
2. `~/.databrickscfg` default profile
3. Azure CLI (on Azure)
4. OAuth flow

## Using Multiple Profiles

If you work with multiple Databricks workspaces, use profiles:

### Setup Multiple Profiles

```bash
# Configure dev profile
databricks configure --token --profile dev

# Configure prod profile  
databricks configure --token --profile prod
```

This creates `~/.databrickscfg`:

```ini
[DEFAULT]
host = https://default-workspace.cloud.databricks.com
token = dapi...

[dev]
host = https://dev-workspace.cloud.databricks.com
token = dapi...

[prod]
host = https://prod-workspace.cloud.databricks.com
token = dapi...
```

### Use Specific Profile

**Method 1: In Config File**

```yaml
workspace:
  profile: "dev"
```

**Method 2: Environment Variable**

```bash
export DATABRICKS_CONFIG_PROFILE="dev"
dbx_test run --remote
```

**Method 3: Multiple Config Files**

```bash
# config/test_config_dev.yml
workspace:
  profile: "dev"

# config/test_config_prod.yml
workspace:
  profile: "prod"
```

Run with:
```bash
dbx_test run --remote --config config/test_config_dev.yml
dbx_test run --remote --config config/test_config_prod.yml
```

## Authentication Examples

### Example 1: Default Profile (Simplest)

**~/.databrickscfg:**
```ini
[DEFAULT]
host = https://your-workspace.cloud.databricks.com
token = dapi...
```

**config/test_config.yml:**
```yaml
# Leave workspace section empty or omit entirely
cluster:
  size: "M"
  spark_version: "13.3.x-scala2.12"
```

**Run:**
```bash
dbx_test run --remote
```

### Example 2: Named Profile

**~/.databrickscfg:**
```ini
[dev]
host = https://dev-workspace.cloud.databricks.com
token = dapi...
```

**config/test_config.yml:**
```yaml
workspace:
  profile: "dev"
```

**Run:**
```bash
dbx_test run --remote
```

### Example 3: Environment Variables Only

**No config file needed!**

```bash
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi..."

dbx_test run --remote --tests-dir tests
```

### Example 4: Azure with CLI

If using Azure Databricks with Azure CLI:

```bash
# Login to Azure
az login

# The SDK will automatically use Azure CLI authentication
dbx_test run --remote
```

## Generating Databricks Token

### Via Web UI

1. Log into your Databricks workspace
2. Click your user profile → **User Settings**
3. Go to **Access Tokens** tab
4. Click **Generate New Token**
5. Give it a name and optional expiration
6. Copy the token (you won't see it again!)

### Using the Token

```bash
# Configure CLI with token
databricks configure --token

# Or set environment variable
export DATABRICKS_TOKEN="your-token-here"
```

## Security Best Practices

### ✅ DO

- Use Databricks CLI profiles for local development
- Use environment variables in CI/CD pipelines
- Set token expiration dates
- Use separate tokens for dev/prod
- Store tokens in secrets managers (Azure Key Vault, AWS Secrets Manager, etc.)

### ❌ DON'T

- Commit tokens to version control
- Share tokens between users
- Use admin tokens for automated testing
- Store tokens in plain text config files in repos

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run Databricks Tests
  env:
    DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
    DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
  run: |
    dbx_test run --remote
```

### Azure DevOps

```yaml
- script: |
    export DATABRICKS_HOST=$(DATABRICKS_HOST)
    export DATABRICKS_TOKEN=$(DATABRICKS_TOKEN)
    dbx_test run --remote
  displayName: 'Run Tests'
```

### Jenkins

```groovy
withCredentials([
    string(credentialsId: 'databricks-host', variable: 'DATABRICKS_HOST'),
    string(credentialsId: 'databricks-token', variable: 'DATABRICKS_TOKEN')
]) {
    sh 'dbx_test run --remote'
}
```

## Troubleshooting

### "Cannot find authentication configuration"

**Solution 1**: Configure Databricks CLI
```bash
databricks configure --token
```

**Solution 2**: Set environment variables
```bash
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi..."
```

**Solution 3**: Add to config file
```yaml
workspace:
  host: "https://your-workspace.cloud.databricks.com"
  token: "dapi..."
```

### "Profile 'dev' not found"

Check your `~/.databrickscfg` file:
```bash
cat ~/.databrickscfg
```

Create the profile:
```bash
databricks configure --token --profile dev
```

### "Token has expired"

Generate a new token and update:
```bash
databricks configure --token
```

### "Permission denied"

- Ensure your token has the necessary permissions
- Check that your user has access to the workspace
- Verify the workspace URL is correct

## Summary

The framework now seamlessly integrates with Databricks CLI, making authentication much easier:

✅ **No manual token management**
✅ **Supports multiple workspaces** via profiles
✅ **Works with Azure CLI** authentication
✅ **Compatible with CI/CD** pipelines
✅ **Follows Databricks SDK** best practices

Just configure once with `databricks configure --token` and you're ready to test! 🚀

