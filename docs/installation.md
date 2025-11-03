# Installation Guide

## Prerequisites

- Python 3.10 or higher
- pip package manager
- (Optional) Databricks workspace access for remote testing

## Installation Methods

### Method 1: Install from Source (Development)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/dbx_test.git
cd dbx_test
```

2. Install in editable mode:
```bash
pip install -e .
```

3. Install Nutter (required for local testing):
```bash
pip install nutter
```

4. Verify installation:
```bash
dbx_test --version
```

### Method 2: Install from PyPI (Once Published)

```bash
pip install dbx_test
pip install nutter
```

### Method 3: Install with Development Dependencies

For contributors and developers:

```bash
# Clone repository
git clone https://github.com/yourusername/dbx_test.git
cd dbx_test

# Install with dev dependencies
pip install -e ".[dev]"
```

## Verify Installation

Run the following commands to verify your installation:

```bash
# Check version
dbx_test --version

# Display help
dbx_test --help

# Test discovery (in a directory with tests)
dbx_test discover --tests-dir tests
```

## Configuration Setup

### 1. Create Configuration Directory

```bash
mkdir -p config
```

### 2. Create Configuration File

Create `config/test_config.yml`:

```yaml
workspace:
  host: "https://your-workspace.cloud.databricks.com"
  token_env: "DATABRICKS_TOKEN"

cluster:
  size: "M"
  spark_version: "13.3.x-scala2.12"

execution:
  timeout: 600
  parallel: false

paths:
  workspace_root: "/Workspace/Repos/production/tests"
  test_pattern: "**/*_test.py"

reporting:
  output_dir: ".dbx_test-results"
  formats: ["junit", "console"]
```

### 3. Set Environment Variables

For local development:

```bash
# Linux/Mac
export DATABRICKS_TOKEN="your-token-here"
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"

# Windows (PowerShell)
$env:DATABRICKS_TOKEN="your-token-here"
$env:DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
```

For persistent configuration, add to your shell profile:

```bash
# ~/.bashrc or ~/.zshrc
export DATABRICKS_TOKEN="your-token-here"
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
```

## Setting Up Databricks Authentication

### Method 1: Personal Access Token (Recommended for Development)

1. Go to Databricks workspace
2. Click on your user profile → User Settings
3. Navigate to Access Tokens
4. Click "Generate New Token"
5. Copy the token and set as environment variable

### Method 2: Azure AD Authentication (Enterprise)

For Azure Databricks with AAD:

```yaml
workspace:
  host: "https://adb-xxx.azuredatabricks.net"
  # Use Azure CLI authentication
  token_env: "DATABRICKS_TOKEN"
```

Then authenticate:

```bash
az login
az account get-access-token --resource 2ff814a6-3304-4ab8-85cb-cd0e6f879c1d
```

### Method 3: AWS IAM Authentication

For AWS Databricks:

```yaml
workspace:
  host: "https://xxx.cloud.databricks.com"
  # Configure AWS credentials
  token_env: "DATABRICKS_TOKEN"
```

## Create Your First Test

### 1. Create Tests Directory

```bash
mkdir -p tests
```

### 2. Generate Test Scaffold

```bash
dbx_test scaffold my_first_notebook
```

This creates `tests/my_first_notebook_test.py` with a template.

### 3. Run Your Test Locally

```bash
dbx_test run --local --tests-dir tests
```

### 4. Run Your Test Remotely

```bash
dbx_test run --remote --tests-dir tests --config config/test_config.yml
```

## Troubleshooting

### Issue: Command not found: dbx_test

**Solution:**
- Ensure installation completed successfully
- Check that Python scripts directory is in PATH
- Try: `python -m dbx_test.cli --help`

### Issue: ModuleNotFoundError: No module named 'nutter'

**Solution:**
```bash
pip install nutter
```

### Issue: Permission denied when installing

**Solution:**
```bash
# Use --user flag
pip install --user -e .

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
pip install -e .
```

### Issue: Cannot connect to Databricks workspace

**Solution:**
- Verify `DATABRICKS_TOKEN` is set correctly
- Check workspace URL format (should include https://)
- Verify token has not expired
- Check network connectivity

### Issue: Import errors with Databricks SDK

**Solution:**
```bash
pip install --upgrade databricks-sdk
```

## IDE Setup

### VS Code

1. Install Python extension
2. Create `.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": false,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".dbx_test-results": true
  }
}
```

### PyCharm

1. Open project
2. Configure Python interpreter (File → Settings → Project → Python Interpreter)
3. Mark `tests` directory as Test Sources Root
4. Configure code style to use Black formatter

## Docker Setup (Optional)

For containerized testing:

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install -e .
RUN pip install nutter

# Copy application
COPY . .

# Run tests
CMD ["dbx_test", "run", "--local", "--tests-dir", "tests"]
```

Build and run:

```bash
docker build -t dbx_test .
docker run -e DATABRICKS_TOKEN=$DATABRICKS_TOKEN dbx_test
```

## Next Steps

- Read the [Writing Tests Guide](writing_tests.md)
- Configure your environment: [Configuration Guide](configuration.md)
- Set up CI/CD: [CI/CD Integration Guide](ci_cd_integration.md)
- Explore [Example Tests](../tests/)

## Getting Help

- Check the [FAQ](faq.md)
- Open an issue on GitHub
- Read the [Troubleshooting Guide](troubleshooting.md)

