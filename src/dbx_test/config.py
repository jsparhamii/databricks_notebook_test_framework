"""
Configuration management for the test framework.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class ClusterConfig:
    """Cluster configuration for remote execution."""
    
    # Option 1: Use existing cluster
    cluster_id: Optional[str] = None
    
    # Option 2: Use serverless (if cluster_id is None and size/spark_version not specified)
    # Serverless is used when cluster_id is None and no cluster specs are provided
    
    # Option 3: Create new cluster (if cluster_id is None but size/spark_version specified)
    size: Optional[str] = None  # S, M, L, XL
    spark_version: Optional[str] = None
    node_type_id: Optional[str] = None
    driver_node_type_id: Optional[str] = None
    num_workers: Optional[int] = None
    autoscale_min_workers: Optional[int] = None
    autoscale_max_workers: Optional[int] = None
    cluster_policy_id: Optional[str] = None
    spark_conf: Dict[str, str] = field(default_factory=dict)
    spark_env_vars: Dict[str, str] = field(default_factory=dict)
    custom_tags: Dict[str, str] = field(default_factory=dict)
    
    # Libraries to install on cluster (for non-serverless)
    # For serverless, these will be converted to an inline environment
    libraries: List[Dict[str, str]] = field(default_factory=list)
    
    # Environment key for serverless compute (pre-created environment)
    # If not specified but libraries are provided, an inline environment will be created
    environment_key: Optional[str] = None
    
    def use_serverless(self) -> bool:
        """Check if we should use serverless compute."""
        return (
            self.cluster_id is None and
            self.size is None and
            self.spark_version is None
        )
    
    def use_existing_cluster(self) -> bool:
        """Check if we should use an existing cluster."""
        return self.cluster_id is not None
    
    def get_cluster_spec(self) -> Optional[Dict[str, Any]]:
        """
        Convert to Databricks cluster specification.
        
        Returns:
            None if using serverless or existing cluster,
            cluster spec dict if creating new cluster
        """
        # If using existing cluster or serverless, no spec needed
        if self.use_existing_cluster() or self.use_serverless():
            return None
        
        # Default spark version if not specified
        spark_version = self.spark_version or "13.3.x-scala2.12"
        
        spec: Dict[str, Any] = {
            "spark_version": spark_version,
            "spark_conf": self.spark_conf,
            "spark_env_variables": self.spark_env_vars,
            "custom_tags": {
                **self.custom_tags,
                "created_by": "dbx-test-framework",
            },
        }
        
        # Apply T-shirt sizing if size is specified
        if self.size:
            if self.size == "S":
                spec["num_workers"] = 1
                spec["node_type_id"] = self.node_type_id or "i3.xlarge"
            elif self.size == "M":
                spec["autoscale"] = {
                    "min_workers": 2,
                    "max_workers": 4
                }
                spec["node_type_id"] = self.node_type_id or "i3.xlarge"
            elif self.size == "L":
                spec["autoscale"] = {
                    "min_workers": 4,
                    "max_workers": 8
                }
                spec["node_type_id"] = self.node_type_id or "i3.2xlarge"
            elif self.size == "XL":
                spec["autoscale"] = {
                    "min_workers": 8,
                    "max_workers": 16
                }
                spec["node_type_id"] = self.node_type_id or "i3.4xlarge"
        
        # Override with explicit settings
        if self.num_workers is not None:
            spec["num_workers"] = self.num_workers
            spec.pop("autoscale", None)
        elif self.autoscale_min_workers and self.autoscale_max_workers:
            spec["autoscale"] = {
                "min_workers": self.autoscale_min_workers,
                "max_workers": self.autoscale_max_workers,
            }
            spec.pop("num_workers", None)
        
        if self.driver_node_type_id:
            spec["driver_node_type_id"] = self.driver_node_type_id
        
        if self.cluster_policy_id:
            spec["policy_id"] = self.cluster_policy_id
        
        return spec


@dataclass
class WorkspaceConfig:
    """Databricks workspace configuration."""
    
    host: Optional[str] = None
    token: Optional[str] = None
    token_env: Optional[str] = None
    profile: Optional[str] = None  # Databricks CLI profile name
    
    def get_auth_config(self) -> Dict[str, Any]:
        """
        Get authentication configuration for Databricks SDK.
        
        Returns a dict that can be passed to WorkspaceClient.
        Uses the following priority:
        1. Explicit token in config
        2. Token from environment variable
        3. Databricks CLI profile (default if not specified)
        4. Default Databricks SDK authentication chain
        """
        config = {}
        
        # Add host if specified
        if self.host:
            config["host"] = self.host
        
        # Add profile if specified (Databricks CLI profile)
        if self.profile:
            config["profile"] = self.profile
        
        # Add token if explicitly provided
        if self.token:
            config["token"] = self.token
        elif self.token_env:
            token = os.environ.get(self.token_env)
            if token:
                config["token"] = token
        
        # If nothing is specified, SDK will use default auth chain:
        # 1. Environment variables (DATABRICKS_HOST, DATABRICKS_TOKEN)
        # 2. ~/.databrickscfg (default profile)
        # 3. Azure CLI
        # 4. OAuth
        
        return config


@dataclass
class ExecutionConfig:
    """Test execution configuration."""
    
    timeout: int = 600  # seconds
    max_retries: int = 2
    parallel: bool = False
    max_parallel_jobs: int = 5
    poll_interval: int = 10  # seconds


@dataclass
class PathsConfig:
    """Path configuration."""
    
    workspace_root: str = "/Workspace/Repos/production"
    test_pattern: str = "**/*_test.py"
    local_tests_dir: str = "tests"


@dataclass
class ReportingConfig:
    """Reporting configuration."""
    
    output_dir: str = ".dbx-test-results"
    formats: List[str] = field(default_factory=lambda: ["junit", "console", "json"])
    fail_on_error: bool = True
    verbose: bool = False


class TestConfig:
    """Main configuration class for the test framework."""
    
    def __init__(
        self,
        workspace: WorkspaceConfig,
        cluster: ClusterConfig,
        execution: ExecutionConfig,
        paths: PathsConfig,
        reporting: ReportingConfig,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        self.workspace = workspace
        self.cluster = cluster
        self.execution = execution
        self.paths = paths
        self.reporting = reporting
        self.parameters = parameters or {}
    
    @classmethod
    def from_yaml(cls, config_path: str) -> "TestConfig":
        """Load configuration from YAML file."""
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, "r") as f:
            data = yaml.safe_load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestConfig":
        """Create configuration from dictionary."""
        # Handle None or missing data
        if data is None:
            data = {}
        
        workspace_data = data.get("workspace") or {}
        workspace = WorkspaceConfig(
            host=workspace_data.get("host"),
            token=workspace_data.get("token"),
            token_env=workspace_data.get("token_env"),
            profile=workspace_data.get("profile"),
        )
        
        cluster_data = data.get("cluster") or {}
        cluster = ClusterConfig(
            cluster_id=cluster_data.get("cluster_id"),
            size=cluster_data.get("size"),
            spark_version=cluster_data.get("spark_version"),
            node_type_id=cluster_data.get("node_type_id"),
            driver_node_type_id=cluster_data.get("driver_node_type_id"),
            num_workers=cluster_data.get("num_workers"),
            autoscale_min_workers=cluster_data.get("autoscale_min_workers"),
            autoscale_max_workers=cluster_data.get("autoscale_max_workers"),
            cluster_policy_id=cluster_data.get("cluster_policy_id"),
            spark_conf=cluster_data.get("spark_conf", {}),
            spark_env_vars=cluster_data.get("spark_env_vars", {}),
            custom_tags=cluster_data.get("custom_tags", {}),
            libraries=cluster_data.get("libraries", []),
            environment_key=cluster_data.get("environment_key"),
        )
        
        execution_data = data.get("execution") or {}
        execution = ExecutionConfig(
            timeout=execution_data.get("timeout", 600),
            max_retries=execution_data.get("max_retries", 2),
            parallel=execution_data.get("parallel", False),
            max_parallel_jobs=execution_data.get("max_parallel_jobs", 5),
            poll_interval=execution_data.get("poll_interval", 10),
        )
        
        paths_data = data.get("paths") or {}
        paths = PathsConfig(
            workspace_root=paths_data.get("workspace_root", "/Workspace/Repos/production"),
            test_pattern=paths_data.get("test_pattern", "**/*_test.py"),
            local_tests_dir=paths_data.get("local_tests_dir", "tests"),
        )
        
        reporting_data = data.get("reporting") or {}
        reporting = ReportingConfig(
            output_dir=reporting_data.get("output_dir", ".dbx-test-results"),
            formats=reporting_data.get("formats", ["junit", "console", "json"]),
            fail_on_error=reporting_data.get("fail_on_error", True),
            verbose=reporting_data.get("verbose", False),
        )
        
        parameters = data.get("parameters") or {}
        
        return cls(
            workspace=workspace,
            cluster=cluster,
            execution=execution,
            paths=paths,
            reporting=reporting,
            parameters=parameters,
        )
    
    @classmethod
    def get_default(cls) -> "TestConfig":
        """Get default configuration."""
        return cls(
            workspace=WorkspaceConfig(),
            cluster=ClusterConfig(),
            execution=ExecutionConfig(),
            paths=PathsConfig(),
            reporting=ReportingConfig(),
        )

