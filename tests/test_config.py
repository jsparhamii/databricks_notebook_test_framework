"""
Unit tests for the configuration module.
"""

import pytest
import os
import tempfile
from pathlib import Path
import yaml

from dbx_test.config import (
    ClusterConfig,
    WorkspaceConfig,
    ExecutionConfig,
    PathsConfig,
    ReportingConfig,
    TestConfig,
)


class TestClusterConfig:
    """Tests for ClusterConfig class."""
    
    def test_default_cluster_config(self):
        """Test default cluster config."""
        config = ClusterConfig()
        
        assert config.cluster_id is None
        assert config.size is None
        assert config.spark_version is None
        assert config.libraries == []
    
    def test_use_serverless(self):
        """Test detecting serverless mode."""
        config = ClusterConfig()
        assert config.use_serverless() is True
        
        config = ClusterConfig(cluster_id="cluster-123")
        assert config.use_serverless() is False
        
        config = ClusterConfig(size="M")
        assert config.use_serverless() is False
        
        config = ClusterConfig(spark_version="13.3.x-scala2.12")
        assert config.use_serverless() is False
    
    def test_use_existing_cluster(self):
        """Test detecting existing cluster mode."""
        config = ClusterConfig()
        assert config.use_existing_cluster() is False
        
        config = ClusterConfig(cluster_id="cluster-123")
        assert config.use_existing_cluster() is True
    
    def test_get_cluster_spec_serverless(self):
        """Test that serverless returns None spec."""
        config = ClusterConfig()
        assert config.get_cluster_spec() is None
    
    def test_get_cluster_spec_existing(self):
        """Test that existing cluster returns None spec."""
        config = ClusterConfig(cluster_id="cluster-123")
        assert config.get_cluster_spec() is None
    
    def test_get_cluster_spec_small(self):
        """Test creating small cluster spec."""
        config = ClusterConfig(size="S")
        spec = config.get_cluster_spec()
        
        assert spec is not None
        assert spec["num_workers"] == 1
        assert spec["node_type_id"] == "i3.xlarge"
        assert spec["spark_version"] == "13.3.x-scala2.12"
        assert "dbx-test-framework" in spec["custom_tags"]["created_by"]
    
    def test_get_cluster_spec_medium(self):
        """Test creating medium cluster spec."""
        config = ClusterConfig(size="M")
        spec = config.get_cluster_spec()
        
        assert spec is not None
        assert "autoscale" in spec
        assert spec["autoscale"]["min_workers"] == 2
        assert spec["autoscale"]["max_workers"] == 4
    
    def test_get_cluster_spec_large(self):
        """Test creating large cluster spec."""
        config = ClusterConfig(size="L")
        spec = config.get_cluster_spec()
        
        assert spec is not None
        assert spec["autoscale"]["min_workers"] == 4
        assert spec["autoscale"]["max_workers"] == 8
        assert spec["node_type_id"] == "i3.2xlarge"
    
    def test_get_cluster_spec_xlarge(self):
        """Test creating xlarge cluster spec."""
        config = ClusterConfig(size="XL")
        spec = config.get_cluster_spec()
        
        assert spec is not None
        assert spec["autoscale"]["min_workers"] == 8
        assert spec["autoscale"]["max_workers"] == 16
        assert spec["node_type_id"] == "i3.4xlarge"
    
    def test_get_cluster_spec_custom_workers(self):
        """Test custom number of workers overrides size."""
        config = ClusterConfig(size="M", num_workers=5)
        spec = config.get_cluster_spec()
        
        assert spec is not None
        assert spec["num_workers"] == 5
        assert "autoscale" not in spec
    
    def test_get_cluster_spec_custom_autoscale(self):
        """Test custom autoscale overrides size."""
        config = ClusterConfig(
            size="M",
            autoscale_min_workers=1,
            autoscale_max_workers=10,
        )
        spec = config.get_cluster_spec()
        
        assert spec is not None
        assert spec["autoscale"]["min_workers"] == 1
        assert spec["autoscale"]["max_workers"] == 10
        assert "num_workers" not in spec
    
    def test_get_cluster_spec_with_spark_conf(self):
        """Test adding spark configuration."""
        config = ClusterConfig(
            size="S",
            spark_conf={"spark.sql.shuffle.partitions": "200"},
        )
        spec = config.get_cluster_spec()
        
        assert spec["spark_conf"]["spark.sql.shuffle.partitions"] == "200"
    
    def test_get_cluster_spec_with_custom_tags(self):
        """Test adding custom tags."""
        config = ClusterConfig(
            size="S",
            custom_tags={"project": "test-framework", "env": "dev"},
        )
        spec = config.get_cluster_spec()
        
        assert spec["custom_tags"]["project"] == "test-framework"
        assert spec["custom_tags"]["env"] == "dev"
        assert "created_by" in spec["custom_tags"]


class TestWorkspaceConfig:
    """Tests for WorkspaceConfig class."""
    
    def test_default_workspace_config(self):
        """Test default workspace config."""
        config = WorkspaceConfig()
        
        assert config.host is None
        assert config.token is None
        assert config.token_env is None
        assert config.profile is None
    
    def test_get_auth_config_empty(self):
        """Test getting auth config with no settings."""
        config = WorkspaceConfig()
        auth = config.get_auth_config()
        
        assert auth == {}
    
    def test_get_auth_config_with_host(self):
        """Test getting auth config with host."""
        config = WorkspaceConfig(host="https://adb-123.azuredatabricks.net")
        auth = config.get_auth_config()
        
        assert auth["host"] == "https://adb-123.azuredatabricks.net"
    
    def test_get_auth_config_with_token(self):
        """Test getting auth config with explicit token."""
        config = WorkspaceConfig(
            host="https://adb-123.azuredatabricks.net",
            token="dapi123456",
        )
        auth = config.get_auth_config()
        
        assert auth["host"] == "https://adb-123.azuredatabricks.net"
        assert auth["token"] == "dapi123456"
    
    def test_get_auth_config_with_token_env(self):
        """Test getting auth config with token from environment."""
        os.environ["TEST_DATABRICKS_TOKEN"] = "dapi_from_env"
        
        config = WorkspaceConfig(token_env="TEST_DATABRICKS_TOKEN")
        auth = config.get_auth_config()
        
        assert auth["token"] == "dapi_from_env"
        
        # Cleanup
        del os.environ["TEST_DATABRICKS_TOKEN"]
    
    def test_get_auth_config_with_profile(self):
        """Test getting auth config with profile."""
        config = WorkspaceConfig(profile="adb")
        auth = config.get_auth_config()
        
        assert auth["profile"] == "adb"
    
    def test_token_priority(self):
        """Test that explicit token takes priority over env token."""
        os.environ["TEST_DATABRICKS_TOKEN"] = "dapi_from_env"
        
        config = WorkspaceConfig(
            token="dapi_explicit",
            token_env="TEST_DATABRICKS_TOKEN",
        )
        auth = config.get_auth_config()
        
        assert auth["token"] == "dapi_explicit"
        
        # Cleanup
        del os.environ["TEST_DATABRICKS_TOKEN"]


class TestExecutionConfig:
    """Tests for ExecutionConfig class."""
    
    def test_default_execution_config(self):
        """Test default execution config."""
        config = ExecutionConfig()
        
        assert config.timeout == 600
        assert config.max_retries == 2
        assert config.parallel is False
        assert config.max_parallel_jobs == 5
        assert config.poll_interval == 10
    
    def test_custom_execution_config(self):
        """Test custom execution config."""
        config = ExecutionConfig(
            timeout=1200,
            max_retries=5,
            parallel=True,
            max_parallel_jobs=10,
            poll_interval=5,
        )
        
        assert config.timeout == 1200
        assert config.max_retries == 5
        assert config.parallel is True
        assert config.max_parallel_jobs == 10
        assert config.poll_interval == 5


class TestPathsConfig:
    """Tests for PathsConfig class."""
    
    def test_default_paths_config(self):
        """Test default paths config."""
        config = PathsConfig()
        
        assert config.workspace_root == "/Workspace/Repos/production"
        assert config.test_pattern == "**/*_test.py"
        assert config.local_tests_dir == "tests"
    
    def test_custom_paths_config(self):
        """Test custom paths config."""
        config = PathsConfig(
            workspace_root="/Workspace/Users/test",
            test_pattern="**/test_*.py",
            local_tests_dir="test",
        )
        
        assert config.workspace_root == "/Workspace/Users/test"
        assert config.test_pattern == "**/test_*.py"
        assert config.local_tests_dir == "test"


class TestReportingConfig:
    """Tests for ReportingConfig class."""
    
    def test_default_reporting_config(self):
        """Test default reporting config."""
        config = ReportingConfig()
        
        assert config.output_dir == ".dbx-test-results"
        assert "junit" in config.formats
        assert "console" in config.formats
        assert "json" in config.formats
        assert config.fail_on_error is True
        assert config.verbose is False
    
    def test_custom_reporting_config(self):
        """Test custom reporting config."""
        config = ReportingConfig(
            output_dir="test-results",
            formats=["junit"],
            fail_on_error=False,
            verbose=True,
        )
        
        assert config.output_dir == "test-results"
        assert config.formats == ["junit"]
        assert config.fail_on_error is False
        assert config.verbose is True


class TestTestConfig:
    """Tests for TestConfig class."""
    
    def test_create_default_config(self):
        """Test creating default config."""
        config = TestConfig.get_default()
        
        assert isinstance(config.workspace, WorkspaceConfig)
        assert isinstance(config.cluster, ClusterConfig)
        assert isinstance(config.execution, ExecutionConfig)
        assert isinstance(config.paths, PathsConfig)
        assert isinstance(config.reporting, ReportingConfig)
        assert config.parameters == {}
    
    def test_create_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "workspace": {
                "host": "https://adb-123.azuredatabricks.net",
                "profile": "adb",
            },
            "cluster": {
                "size": "M",
                "spark_version": "13.3.x-scala2.12",
            },
            "execution": {
                "timeout": 1200,
                "parallel": True,
            },
            "paths": {
                "workspace_root": "/Workspace/Users/test",
            },
            "reporting": {
                "output_dir": "results",
            },
            "parameters": {
                "env": "dev",
            },
        }
        
        config = TestConfig.from_dict(data)
        
        assert config.workspace.host == "https://adb-123.azuredatabricks.net"
        assert config.workspace.profile == "adb"
        assert config.cluster.size == "M"
        assert config.cluster.spark_version == "13.3.x-scala2.12"
        assert config.execution.timeout == 1200
        assert config.execution.parallel is True
        assert config.paths.workspace_root == "/Workspace/Users/test"
        assert config.reporting.output_dir == "results"
        assert config.parameters["env"] == "dev"
    
    def test_create_from_dict_empty(self):
        """Test creating config from empty dictionary."""
        config = TestConfig.from_dict({})
        
        assert isinstance(config.workspace, WorkspaceConfig)
        assert isinstance(config.cluster, ClusterConfig)
        assert isinstance(config.execution, ExecutionConfig)
        assert isinstance(config.paths, PathsConfig)
        assert isinstance(config.reporting, ReportingConfig)
    
    def test_create_from_dict_none(self):
        """Test creating config from None."""
        config = TestConfig.from_dict(None)
        
        assert isinstance(config.workspace, WorkspaceConfig)
        assert isinstance(config.cluster, ClusterConfig)
    
    def test_create_from_yaml(self):
        """Test creating config from YAML file."""
        yaml_content = """
workspace:
  host: https://adb-123.azuredatabricks.net
  profile: adb

cluster:
  size: M
  libraries:
    - pypi:
        package: pandas==2.0.0

execution:
  timeout: 1200
  parallel: true

paths:
  workspace_root: /Workspace/Users/test
  test_pattern: "**/*_test.py"

reporting:
  output_dir: results
  formats:
    - junit
    - json
"""
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            config_path = f.name
        
        try:
            config = TestConfig.from_yaml(config_path)
            
            assert config.workspace.host == "https://adb-123.azuredatabricks.net"
            assert config.workspace.profile == "adb"
            assert config.cluster.size == "M"
            assert len(config.cluster.libraries) == 1
            assert config.execution.timeout == 1200
            assert config.execution.parallel is True
            assert config.paths.workspace_root == "/Workspace/Users/test"
            assert config.reporting.output_dir == "results"
        finally:
            # Cleanup
            os.unlink(config_path)
    
    def test_create_from_yaml_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            TestConfig.from_yaml("/nonexistent/config.yml")
    
    def test_libraries_config(self):
        """Test configuring libraries."""
        data = {
            "cluster": {
                "libraries": [
                    {"pypi": {"package": "pandas==2.0.0"}},
                    {"whl": "/path/to/package.whl"},
                ],
            },
        }
        
        config = TestConfig.from_dict(data)
        
        assert len(config.cluster.libraries) == 2
        assert config.cluster.libraries[0]["pypi"]["package"] == "pandas==2.0.0"
        assert config.cluster.libraries[1]["whl"] == "/path/to/package.whl"
    
    def test_environment_key_config(self):
        """Test configuring environment key."""
        data = {
            "cluster": {
                "environment_key": "test-env",
            },
        }
        
        config = TestConfig.from_dict(data)
        
        assert config.cluster.environment_key == "test-env"

