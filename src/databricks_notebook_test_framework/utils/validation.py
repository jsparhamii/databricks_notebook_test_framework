"""
Validation utilities.
"""

from pathlib import Path
from typing import List, Optional


def validate_file_exists(file_path: Path) -> None:
    """Validate that a file exists."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")


def validate_directory_exists(dir_path: Path) -> None:
    """Validate that a directory exists."""
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    if not dir_path.is_dir():
        raise ValueError(f"Path is not a directory: {dir_path}")


def validate_pattern(pattern: str) -> None:
    """Validate glob pattern."""
    if not pattern:
        raise ValueError("Pattern cannot be empty")


def validate_environment(env: Optional[str], valid_envs: List[str]) -> None:
    """Validate environment name."""
    if env and env not in valid_envs:
        raise ValueError(
            f"Invalid environment: {env}. Valid options: {', '.join(valid_envs)}"
        )


def validate_databricks_host(host: str) -> None:
    """Validate Databricks host URL."""
    if not host:
        raise ValueError("Databricks host cannot be empty")
    if not (host.startswith("https://") or host.startswith("http://")):
        raise ValueError(
            f"Invalid Databricks host URL: {host}. Must start with https:// or http://"
        )


def validate_cluster_size(size: str) -> None:
    """Validate cluster size."""
    valid_sizes = ["S", "M", "L", "XL"]
    if size not in valid_sizes:
        raise ValueError(
            f"Invalid cluster size: {size}. Valid options: {', '.join(valid_sizes)}"
        )

