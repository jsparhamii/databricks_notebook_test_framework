"""
Databricks API helper functions.
"""

import time
from typing import Dict, Any, Optional, List
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.workspace import ImportFormat
from databricks.sdk.service.jobs import RunResultState, RunLifeCycleState
from pathlib import Path
from rich.console import Console

console = Console()


class DatabricksHelper:
    """Helper class for Databricks API operations."""
    
    def __init__(self, **auth_config):
        """
        Initialize Databricks helper.
        
        Args:
            **auth_config: Authentication configuration to pass to WorkspaceClient.
                          Can include: host, token, profile, or nothing (uses defaults)
        """
        self.client = WorkspaceClient(**auth_config)
        self.host = auth_config.get("host", self.client.config.host)
    
    def upload_notebook(
        self,
        local_path: Path,
        workspace_path: str,
        overwrite: bool = True
    ) -> str:
        """Upload notebook to Databricks workspace."""
        with open(local_path, "rb") as f:
            content = f.read()
        
        # Determine format
        if local_path.suffix == ".ipynb":
            format = ImportFormat.JUPYTER
        elif local_path.suffix == ".py":
            format = ImportFormat.SOURCE
        else:
            format = ImportFormat.AUTO
        
        try:
            self.client.workspace.import_(
                path=workspace_path,
                format=format,
                content=content,
                overwrite=overwrite,
            )
            return workspace_path
        except Exception as e:
            raise RuntimeError(f"Failed to upload notebook to {workspace_path}: {e}")
    
    def notebook_exists(self, workspace_path: str) -> bool:
        """Check if notebook exists in workspace."""
        try:
            self.client.workspace.get_status(workspace_path)
            return True
        except Exception:
            return False
    
    def _get_or_create_environment(self, libraries: List[Dict[str, str]]) -> str:
        """
        Get or create an environment for the given libraries.
        Returns the environment key to use.
        
        Args:
            libraries: List of library specifications
            
        Returns:
            Environment key string
        """
        import hashlib
        import json
        
        # Convert libraries to dependency list
        dependencies = []
        for lib in libraries:
            if 'pypi' in lib:
                dependencies.append(lib['pypi']['package'])
            elif 'whl' in lib:
                dependencies.append(lib['whl'])
        
        if not dependencies:
            raise ValueError("No valid dependencies found in libraries")
        
        # Create a deterministic environment name based on dependencies
        # This allows reuse across runs with same dependencies
        deps_str = json.dumps(sorted(dependencies), sort_keys=True)
        deps_hash = hashlib.md5(deps_str.encode()).hexdigest()[:8]
        env_name = f"dbx_test_auto_{deps_hash}"
        
        # Check if environment already exists by trying to use it
        # If it exists, Databricks will accept it; if not, creation will be attempted
        print(f"Checking for existing environment: {env_name}")
        
        # For now, raise an error with helpful instructions
        # Automatic environment creation via API is not yet available
        raise RuntimeError(
            f"\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  Automatic environment creation is not yet available.\n"
            f"  Please create an environment manually in your workspace:\n"
            f"\n"
            f"  1. Go to Databricks workspace → Compute → Environments\n"
            f"  2. Click 'Create Environment'\n"
            f"  3. Name: {env_name}\n"
            f"  4. Client: 1\n"
            f"  5. Add dependencies:\n"
            f"     {chr(10).join(f'     - {dep}' for dep in dependencies)}\n"
            f"\n"
            f"  Then update your config with:\n"
            f"    cluster:\n"
            f"      environment_key: \"{env_name}\"\n"
            f"\n"
            f"  Or create with any name and update config accordingly.\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
    
    def run_notebook(
        self,
        notebook_path: str,
        cluster_spec: Optional[Dict[str, Any]] = None,
        cluster_id: Optional[str] = None,
        use_serverless: bool = False,
        parameters: Optional[Dict[str, str]] = None,
        timeout: int = 600,
        libraries: Optional[List[Dict[str, str]]] = None,
        environment_key: Optional[str] = None,
    ) -> str:
        """
        Run a notebook directly and return run ID.
        Uses submit_run API to execute notebook without creating a job.
        This allows us to retrieve notebook output via dbutils.notebook.exit().
        
        Args:
            notebook_path: Path to notebook in workspace
            cluster_spec: New cluster specification (if creating new cluster)
            cluster_id: Existing cluster ID to use
            use_serverless: Use serverless compute
            parameters: Notebook parameters
            timeout: Timeout in seconds
            libraries: List of library specifications to install
            environment_key: Environment key for serverless (alternative to libraries)
        
        Returns:
            Run ID string
        """
        from databricks.sdk.service.jobs import NotebookTask, SubmitTask, Source
        
        # Build notebook task
        # Use WORKSPACE source for files deployed via bundles
        notebook_task = NotebookTask(
            notebook_path=notebook_path,
            source=Source.WORKSPACE,
            base_parameters=parameters or {},
        )
        
        # Build the task with compute configuration
        task = SubmitTask(
            task_key="test_run",
            notebook_task=notebook_task,
            timeout_seconds=timeout,
        )
        
        # Prepare job-level environments (for serverless)
        job_environments = None
        
        # Handle libraries and environments
        if use_serverless:
            # For serverless, use environment (either pre-created or inline)
            if environment_key:
                # Use pre-created environment by key only
                task.environment_key = environment_key
            elif libraries:
                # Create inline environment at job level (not task level)
                # Convert libraries to pip dependencies format
                dependencies = []
                for lib in libraries:
                    if 'pypi' in lib:
                        dependencies.append(lib['pypi']['package'])
                    elif 'whl' in lib:
                        dependencies.append(lib['whl'])
                
                if dependencies:
                    # Set environment_key on task to reference the inline environment
                    task.environment_key = "default"
                    
                    # Define environment at job level using SDK classes
                    from databricks.sdk.service.jobs import JobEnvironment
                    from databricks.sdk.service.compute import Environment
                    
                    job_environments = [
                        JobEnvironment(
                            environment_key="default",
                            spec=Environment(
                                client="1",
                                dependencies=dependencies
                            )
                        )
                    ]
        else:
            # For clusters, use libraries directly
            if libraries:
                from databricks.sdk.service.compute import Library, PythonPyPiLibrary, MavenLibrary
                
                task_libraries = []
                for lib in libraries:
                    if 'pypi' in lib:
                        # PyPI library
                        task_libraries.append(Library(pypi=PythonPyPiLibrary(package=lib['pypi']['package'])))
                    elif 'whl' in lib:
                        # Wheel library
                        task_libraries.append(Library(whl=lib['whl']))
                    elif 'jar' in lib:
                        # JAR library
                        task_libraries.append(Library(jar=lib['jar']))
                    elif 'maven' in lib:
                        # Maven library
                        task_libraries.append(Library(maven=MavenLibrary(coordinates=lib['maven']['coordinates'])))
                    else:
                        # Try to pass as-is (for any other format)
                        task_libraries.append(Library(**lib))
                
                task.libraries = task_libraries
        
        # Configure compute
        if use_serverless:
            # Use serverless compute
            if job_environments:
                run = self.client.jobs.submit(
                    run_name=f"dbx-test-{int(time.time())}",
                    tasks=[task],
                    environments=job_environments,
                )
            else:
                run = self.client.jobs.submit(
                    run_name=f"dbx-test-{int(time.time())}",
                    tasks=[task],
                )
        elif cluster_id:
            # Use existing cluster
            task.existing_cluster_id = cluster_id
            run = self.client.jobs.submit(
                run_name=f"dbx-test-{int(time.time())}",
                tasks=[task],
            )
        elif cluster_spec:
            # Create new cluster
            task.new_cluster = cluster_spec
            run = self.client.jobs.submit(
                run_name=f"dbx-test-{int(time.time())}",
                tasks=[task],
            )
        else:
            # Default to serverless
            run = self.client.jobs.submit(
                run_name=f"dbx-test-{int(time.time())}",
                tasks=[task],
            )
        
        return str(run.run_id)
    
    def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """Get status of a run."""
        run = self.client.jobs.get_run(run_id=int(run_id))
        
        state = run.state
        if not state:
            return {
                "state": "UNKNOWN",
                "life_cycle_state": "UNKNOWN",
                "result_state": None,
            }
        
        return {
            "state": state.life_cycle_state.value if state.life_cycle_state else "UNKNOWN",
            "life_cycle_state": state.life_cycle_state.value if state.life_cycle_state else "UNKNOWN",
            "result_state": state.result_state.value if state.result_state else None,
            "state_message": state.state_message or "",
        }
    
    def wait_for_run(
        self,
        run_id: str,
        timeout: int = 600,
        poll_interval: int = 10,
    ) -> Dict[str, Any]:
        """Wait for run to complete and return final status."""
        start_time = time.time()
        
        while True:
            status = self.get_run_status(run_id)
            
            # Check if terminal state
            if status["life_cycle_state"] in ["TERMINATED", "SKIPPED", "INTERNAL_ERROR"]:
                return status
            
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Run {run_id} did not complete within {timeout} seconds"
                )
            
            time.sleep(poll_interval)
    
    def get_run_output(self, run_id: str) -> Optional[str]:
        """
        Get output from a notebook run.
        Retrieves the result from dbutils.notebook.exit().
        """
        try:
            run = self.client.jobs.get_run(run_id=int(run_id))
            
            # For submit_run, we need to get the output from the specific task
            if run.tasks and len(run.tasks) > 0:
                # Get the first (and usually only) task
                task_run = run.tasks[0]
                if task_run.run_id:
                    # Get output from the task run
                    output = self.client.jobs.get_run_output(run_id=task_run.run_id)
                    if output.notebook_output and output.notebook_output.result:
                        return output.notebook_output.result
            
            # Fallback: try to get output directly (for older API style)
            output = self.client.jobs.get_run_output(run_id=int(run_id))
            if output.notebook_output and output.notebook_output.result:
                return output.notebook_output.result
            
            return None
        except Exception as e:
            print(f"Warning: Could not fetch run output: {e}")
            return None
    
    def list_notebooks(self, workspace_path: str, pattern: str = None) -> List[str]:
        """
        List notebooks in a workspace directory matching pytest-style patterns.
        
        Automatically discovers notebooks matching:
        - test_* (starts with test_)
        - *_test (ends with _test)
        
        Args:
            workspace_path: Workspace directory path
            pattern: Deprecated, kept for compatibility
        
        Returns:
            List of notebook paths
        """
        try:
            from fnmatch import fnmatch
            
            notebooks = []
            objects = self.client.workspace.list(workspace_path)
            
            for obj in objects:
                if obj.object_type and obj.object_type.value in ["NOTEBOOK", "FILE"]:
                    # Get notebook name (without path)
                    notebook_name = obj.path.split("/")[-1]
                    
                    # Only include Python files (.py extension or no extension for notebooks)
                    # Skip non-Python files like .yml, .json, .md, etc.
                    if "." in notebook_name:
                        # Has extension - must be .py
                        if not notebook_name.endswith(".py"):
                            continue
                    
                    # Pytest-style discovery: test_* or *_test (without .py extension)
                    name_without_ext = notebook_name.replace(".py", "")
                    if name_without_ext.startswith("test_") or name_without_ext.endswith("_test"):
                        notebooks.append(obj.path)
                elif obj.object_type and obj.object_type.value == "DIRECTORY":
                    # Recursively list subdirectories
                    notebooks.extend(self.list_notebooks(obj.path, pattern))
            
            return notebooks
        except Exception as e:
            # Check if it's a directory not found error
            error_str = str(e).lower()
            if "does not exist" in error_str or "not found" in error_str:
                raise FileNotFoundError(f"Workspace directory not found: {workspace_path}. Please verify the path exists in your Databricks workspace.")
            raise RuntimeError(f"Error listing notebooks in {workspace_path}: {e}")

