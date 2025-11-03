#!/usr/bin/env python3
"""
Quick script to create a Databricks environment for dbx_test.
Run this once to set up your environment, then use it in your tests.
"""

from databricks.sdk import WorkspaceClient
import sys

def create_dbx_test_environment(profile="aws-west", env_name="dbx_test_env"):
    """Create a Databricks environment with dbx_test library."""
    
    print(f"Creating environment '{env_name}' on profile '{profile}'...")
    
    try:
        w = WorkspaceClient(profile=profile)
        
        # Create environment
        env = w.workspace.environments.create(
            name=env_name,
            spec={
                "client": "1",
                "dependencies": [
                    "git+https://github.com/jsparhamii/dbx_test.git"
                ]
            }
        )
        
        print(f"✓ Environment '{env_name}' created successfully!")
        print(f"  Environment ID: {env.environment_id}")
        print(f"\nUpdate your config/test_config.yml:")
        print(f"  cluster:")
        print(f"    environment_key: \"{env_name}\"")
        
        return env
        
    except Exception as e:
        print(f"✗ Error creating environment: {e}")
        print(f"\nPlease create the environment manually:")
        print(f"1. Go to Databricks workspace")
        print(f"2. Compute → Environments → Create")
        print(f"3. Name: {env_name}")
        print(f"4. Add dependency: git+https://github.com/jsparhamii/dbx_test.git")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create Databricks environment for dbx_test")
    parser.add_argument("--profile", default="aws-west", help="Databricks CLI profile")
    parser.add_argument("--name", default="dbx_test_env", help="Environment name")
    
    args = parser.parse_args()
    
    create_dbx_test_environment(args.profile, args.name)

