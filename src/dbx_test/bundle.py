"""
Databricks Asset Bundle detection and utilities.
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from databricks.sdk import WorkspaceClient


def find_bundle_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find the root directory of a Databricks Asset Bundle project.
    
    Searches upward from start_path for databricks.yml or bundle.yml.
    
    Args:
        start_path: Starting directory (defaults to current directory)
        
    Returns:
        Path to bundle root directory, or None if not found
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()
    
    current = start_path
    
    # Search upward through parent directories
    while current != current.parent:
        # Check for bundle config files
        for config_name in ["databricks.yml", "bundle.yml"]:
            config_path = current / config_name
            if config_path.exists():
                return current
        
        current = current.parent
    
    return None


def load_bundle_config(bundle_root: Path) -> Dict[str, Any]:
    """
    Load the bundle configuration from databricks.yml or bundle.yml.
    
    Args:
        bundle_root: Path to bundle root directory
        
    Returns:
        Parsed bundle configuration
        
    Raises:
        FileNotFoundError: If no bundle config file found
        yaml.YAMLError: If config file is invalid YAML
    """
    for config_name in ["databricks.yml", "bundle.yml"]:
        config_path = bundle_root / config_name
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
    
    raise FileNotFoundError(f"No bundle config file found in {bundle_root}")


def get_bundle_name(config: Dict[str, Any]) -> Optional[str]:
    """
    Extract the bundle name from configuration.
    
    Args:
        config: Parsed bundle configuration
        
    Returns:
        Bundle name, or None if not found
    """
    return config.get('bundle', {}).get('name')


def get_target_config(config: Dict[str, Any], target: str) -> Optional[Dict[str, Any]]:
    """
    Get configuration for a specific target.
    
    Args:
        config: Parsed bundle configuration
        target: Target name (e.g., 'dev', 'prod')
        
    Returns:
        Target configuration, or None if target not found
    """
    targets = config.get('targets', {})
    return targets.get(target)


def resolve_workspace_path(
    path_template: str,
    bundle_name: Optional[str] = None,
    target: Optional[str] = None,
    workspace_client: Optional[WorkspaceClient] = None,
    profile: Optional[str] = None,
) -> str:
    """
    Resolve workspace path with variable interpolation.
    
    Supports variables like:
    - ${bundle.name}
    - ${bundle.target}
    - ${workspace.current_user.userName}
    
    Args:
        path_template: Path template with variables
        bundle_name: Bundle name for ${bundle.name}
        target: Target name for ${bundle.target}
        workspace_client: WorkspaceClient for fetching current user
        profile: Databricks profile name (alternative to workspace_client)
        
    Returns:
        Resolved path
    """
    resolved = path_template
    
    # Resolve bundle.name
    if bundle_name:
        resolved = resolved.replace('${bundle.name}', bundle_name)
    
    # Resolve bundle.target
    if target:
        resolved = resolved.replace('${bundle.target}', target)
    
    # Resolve workspace.current_user.userName
    if '${workspace.current_user.userName}' in resolved:
        if workspace_client is None and profile:
            workspace_client = WorkspaceClient(profile=profile)
        
        if workspace_client:
            try:
                current_user = workspace_client.current_user.me()
                user_name = current_user.user_name
                resolved = resolved.replace('${workspace.current_user.userName}', user_name)
            except Exception:
                # If we can't get current user, leave the variable as-is
                pass
    
    return resolved


def get_bundle_tests_dir(
    target: str,
    tests_dir_relative: str = "",
    profile: Optional[str] = None,
    bundle_root: Optional[Path] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Automatically determine the remote tests directory for a bundle target.
    
    Args:
        target: Target name (e.g., 'dev', 'prod')
        tests_dir_relative: Relative path to tests within bundle (default: "" for root)
        profile: Databricks profile name
        bundle_root: Bundle root directory (auto-detected if not provided)
        
    Returns:
        Tuple of (workspace_tests_dir, bundle_name) or (None, None) if not a bundle project
        
    Example:
        For a bundle with:
        - name: my_project
        - target dev root_path: /Workspace/Users/user@company.com/.bundle/${bundle.name}/dev
        - tests_dir_relative: "src/tests"
        
        Returns: ('/Workspace/Users/user@company.com/.bundle/my_project/dev/files/src/tests', 'my_project')
        
        If tests_dir_relative is empty, returns the files root:
        Returns: ('/Workspace/Users/user@company.com/.bundle/my_project/dev/files', 'my_project')
    """
    # Find bundle root
    if bundle_root is None:
        bundle_root = find_bundle_root()
    
    if bundle_root is None:
        return None, None
    
    try:
        # Load bundle config
        config = load_bundle_config(bundle_root)
        bundle_name = get_bundle_name(config)
        
        if not bundle_name:
            return None, None
        
        # Get target config
        target_config = get_target_config(config, target)
        if not target_config:
            return None, None
        
        # Get workspace root path
        workspace_config = target_config.get('workspace', {})
        root_path = workspace_config.get('root_path')
        
        # Create workspace client if profile provided
        workspace_client = None
        if profile:
            workspace_client = WorkspaceClient(profile=profile)
        
        # If root_path is not specified, use Databricks default pattern
        if not root_path:
            # Default pattern: /Workspace/Users/${current_user}/.bundle/${bundle_name}/${target}
            if workspace_client is None:
                workspace_client = WorkspaceClient(profile=profile) if profile else WorkspaceClient()
            
            try:
                current_user = workspace_client.current_user.me()
                user_name = current_user.user_name
                root_path = f"/Workspace/Users/{user_name}/.bundle/{bundle_name}/{target}"
            except Exception:
                # If we can't get current user, can't construct default path
                return None, None
        else:
            # Resolve variables in root_path
            root_path = resolve_workspace_path(
                root_path,
                bundle_name=bundle_name,
                target=target,
                workspace_client=workspace_client,
                profile=profile,
            )
        
        # Construct full tests path
        # Bundle files are deployed to {root_path}/files/
        if tests_dir_relative:
            tests_path = f"{root_path}/files/{tests_dir_relative}"
        else:
            # If no relative path specified, use the files root
            tests_path = f"{root_path}/files"
        
        return tests_path, bundle_name
        
    except Exception:
        # If any error occurs during bundle detection, return None
        return None, None


def is_bundle_project(start_path: Optional[Path] = None) -> bool:
    """
    Check if current directory (or start_path) is part of a Databricks Asset Bundle project.
    
    Args:
        start_path: Starting directory (defaults to current directory)
        
    Returns:
        True if bundle project detected, False otherwise
    """
    return find_bundle_root(start_path) is not None

