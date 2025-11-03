# Pytest-Style Test Discovery

The framework now uses **pytest-style automatic test discovery** - no pattern configuration needed!

## How It Works

Just like pytest, the framework automatically discovers test files matching these patterns:

- **`test_*.py`** - Files starting with `test_`
  - `test_example.py`
  - `test_data_validation.py`
  - `test_my_feature.py`

- **`*_test.py`** - Files ending with `_test`
  - `example_test.py`
  - `data_validation_test.py`
  - `my_feature_test.py`

## Automatic & Recursive

- ✅ **No configuration needed** - Just name your files correctly
- ✅ **Recursive search** - Finds tests in all subdirectories
- ✅ **Both patterns** - Matches both `test_*` and `*_test`
- ✅ **Workspace support** - Works for both local and workspace tests

## Examples

### Directory Structure

```
my_project/
├── tests/
│   ├── test_auth.py           ← Found!
│   ├── test_database.py        ← Found!
│   ├── integration/
│   │   ├── test_api.py         ← Found!
│   │   └── test_webhooks.py    ← Found!
│   ├── unit/
│   │   ├── validation_test.py  ← Found!
│   │   └── parser_test.py      ← Found!
│   └── helper.py               ← Skipped (doesn't match pattern)
```

### Running Tests

```bash
# Discovers all test_* and *_test files automatically
dbx_test run --local

# Same automatic discovery for remote tests
dbx_test run --remote --profile dev

# Workspace tests also use automatic discovery
dbx_test run --remote --workspace-tests \
  --tests-dir "/Workspace/Repos/my-repo/tests"
```

### Output

```
Discovering tests matching: test_* or *_test

Found 6 test notebook(s):
  • tests/test_auth.py
  • tests/test_database.py
  • tests/integration/test_api.py
  • tests/integration/test_webhooks.py
  • tests/unit/validation_test.py
  • tests/unit/parser_test.py

Running tests...
```

## Migration from Pattern-Based Discovery

### Before (Old Way)
```bash
# Had to specify pattern
dbx_test run --remote --pattern "test_*"
dbx_test run --remote --pattern "*integration*"
```

### After (New Way)
```bash
# No pattern needed! Automatic discovery
dbx_test run --remote

# Just use descriptive names
# test_integration.py or integration_test.py
```

## Best Practices

### ✅ DO: Use Clear Names

```
test_user_authentication.py    # Clear what it tests
test_data_pipeline.py          # Clear what it tests
api_integration_test.py        # Clear what it tests
```

### ❌ DON'T: Use Non-Standard Names

```
check_users.py          # Won't be discovered
validate_data.py        # Won't be discovered
tests_for_api.py        # Won't be discovered (wrong pattern)
```

## Databricks Notebooks

In Databricks workspace, notebooks don't show `.py` extension in the UI, but the discovery still works:

### Workspace Structure
```
/Workspace/Users/me/tests/
├── test_feature_a       ← Found!
├── test_feature_b       ← Found!
├── validation_test      ← Found!
└── helpers              ← Skipped
```

### Running
```bash
dbx_test run --remote --workspace-tests \
  --profile adb \
  --tests-dir "/Workspace/Users/me/tests"
```

## Configuration

The `test_pattern` setting in `config/test_config.yml` is now **deprecated** but kept for backwards compatibility:

```yaml
paths:
  workspace_root: "/Workspace/tests"
  # test_pattern is no longer needed!
  # Discovery is automatic: test_* and *_test
```

## FAQ

### Q: Can I still use custom patterns?
**A:** No, the framework now uses pytest-style discovery only. This makes it more predictable and follows Python testing conventions.

### Q: What if I have test files not matching the pattern?
**A:** Rename them to follow pytest conventions:
- `my_tests.py` → `test_my_feature.py` or `my_feature_test.py`

### Q: Does this work for workspace tests?
**A:** Yes! Automatic discovery works everywhere:
- Local tests (`--local`)
- Remote tests (`--remote`)
- Workspace tests (`--remote --workspace-tests`)

### Q: Can I have both patterns in the same directory?
**A:** Yes! You can mix:
```
tests/
├── test_feature.py      ← Found!
├── feature_test.py      ← Found!
└── another_test.py      ← Found!
```

## Summary

✨ **Just name your test files with `test_*` or `*_test` and the framework finds them automatically!**

No configuration, no patterns, no hassle - just like pytest! 🎉

