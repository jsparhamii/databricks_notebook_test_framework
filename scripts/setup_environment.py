#!/usr/bin/env python3
"""
One-time setup: Create dbx_test environment in Databricks.
This only needs to be run once per workspace.
"""

print("=" * 70)
print("Creating dbx_test environment in Databricks workspace...")
print("=" * 70)
print()
print("Since the Databricks Environment API is not yet public,")
print("please create the environment manually:")
print()
print("1. Open your Databricks workspace in a browser")
print("2. Go to: Compute → Environments → Create Environment")
print("3. Fill in:")
print("   - Name: dbx_test_env")
print("   - Client: 1")
print("   - Dependencies:")
print("     • git+https://github.com/jsparhamii/dbx_test.git")
print()
print("4. Click 'Create'")
print()
print("Once created, the framework will use it automatically!")
print("=" * 70)

