"""
Remote test execution on Databricks.
"""

import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from dbx_test.config import TestConfig
from dbx_test.utils.databricks import DatabricksHelper


class RemoteTestRunner:
    """Execute tests remotely on Databricks."""
    
    def __init__(self, config: TestConfig, verbose: bool = False):
        """
        Initialize remote test runner.
        
        Args:
            config: Test configuration
            verbose: Enable verbose output
        """
        self.config = config
        self.verbose = verbose
        self.console = Console()
        
        # Initialize Databricks client using workspace auth config
        auth_config = config.workspace.get_auth_config()
        self.db_helper = DatabricksHelper(**auth_config)
    
    def run_test(
        self,
        test_notebook: Path,
        workspace_path: Optional[str] = None,
        parameters: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Run a single test notebook remotely.
        
        Args:
            test_notebook: Local path to test notebook
            workspace_path: Optional workspace path (otherwise auto-generated)
            parameters: Optional parameters to pass
        
        Returns:
            Test result dictionary
        """
        start_time = time.time()
        
        try:
            # Determine workspace path
            if workspace_path is None:
                workspace_path = f"{self.config.paths.workspace_root}/{test_notebook.stem}"
            
            # Upload notebook
            if self.verbose:
                self.console.print(f"[dim]Uploading {test_notebook.name} to {workspace_path}[/dim]")
            
            self.db_helper.upload_notebook(
                local_path=test_notebook,
                workspace_path=workspace_path,
                overwrite=True,
            )
            
            # Determine compute configuration
            cluster_spec = self.config.cluster.get_cluster_spec()
            cluster_id = self.config.cluster.cluster_id
            use_serverless = self.config.cluster.use_serverless()
            
            # Run notebook
            if self.verbose:
                if cluster_id:
                    self.console.print(f"[dim]Starting remote execution on cluster {cluster_id}...[/dim]")
                elif use_serverless:
                    self.console.print(f"[dim]Starting remote execution on serverless compute...[/dim]")
                else:
                    self.console.print(f"[dim]Starting remote execution on new cluster...[/dim]")
            
            run_id = self.db_helper.run_notebook(
                notebook_path=workspace_path,
                cluster_spec=cluster_spec,
                cluster_id=cluster_id,
                use_serverless=use_serverless,
                parameters=parameters,
                timeout=self.config.execution.timeout,
                libraries=self.config.cluster.libraries,
                environment_key=self.config.cluster.environment_key,
            )
            
            # Wait for completion
            if self.verbose:
                self.console.print(f"[dim]Waiting for run {run_id} to complete...[/dim]")
            
            final_status = self.db_helper.wait_for_run(
                run_id=run_id,
                timeout=self.config.execution.timeout,
                poll_interval=self.config.execution.poll_interval,
            )
            
            duration = time.time() - start_time
            
            # Get output
            output = self.db_helper.get_run_output(run_id)
            
            # Determine status
            result_state = final_status.get("result_state")
            if result_state == "SUCCESS":
                status = "passed"
            else:
                status = "failed"
            
            # Parse test results from output
            test_results = self._parse_test_output(output)
            
            return {
                "notebook": test_notebook.stem,
                "notebook_path": str(test_notebook),
                "workspace_path": workspace_path,
                "run_id": run_id,
                "status": status,
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
                "result_state": result_state,
                "state_message": final_status.get("state_message", ""),
                "tests": test_results,
                "output": output,
            }
        
        except TimeoutError as e:
            duration = time.time() - start_time
            return {
                "notebook": test_notebook.stem,
                "notebook_path": str(test_notebook),
                "status": "failed",
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
                "error_message": str(e),
                "tests": [],
            }
        
        except Exception as e:
            duration = time.time() - start_time
            return {
                "notebook": test_notebook.stem,
                "notebook_path": str(test_notebook),
                "status": "failed",
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
                "error_message": str(e),
                "error_traceback": str(e),
                "tests": [],
            }
    
    def run_tests(
        self,
        test_notebooks: List[Dict[str, Any]],
        parameters: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Run multiple test notebooks.
        
        Args:
            test_notebooks: List of test notebook info dictionaries
            parameters: Optional parameters to pass to all tests
        
        Returns:
            Aggregated results dictionary
        """
        all_results = []
        start_time = time.time()
        
        if self.config.execution.parallel:
            all_results = self._run_tests_parallel(test_notebooks, parameters)
        else:
            all_results = self._run_tests_sequential(test_notebooks, parameters)
        
        total_duration = time.time() - start_time
        
        # Calculate summary
        summary = {
            "total": len(all_results),
            "passed": sum(1 for r in all_results if r["status"] == "passed"),
            "failed": sum(1 for r in all_results if r["status"] == "failed"),
            "skipped": sum(1 for r in all_results if r["status"] == "skipped"),
            "errors": sum(1 for r in all_results if r["status"] == "error"),
            "duration": total_duration,
        }
        
        return {
            "run_type": "remote",
            "run_timestamp": datetime.now().isoformat(),
            "workspace": self.config.workspace.host,
            "summary": summary,
            "tests": all_results,
        }
    
    def _run_tests_sequential(
        self,
        test_notebooks: List[Dict[str, Any]],
        parameters: Optional[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        """Run tests sequentially."""
        all_results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        ) as progress:
            task = progress.add_task(
                f"Running {len(test_notebooks)} test(s)...",
                total=len(test_notebooks),
            )
            
            for test_info in test_notebooks:
                test_path = Path(test_info["path"])
                progress.update(
                    task,
                    description=f"Running {test_path.stem}...",
                )
                
                result = self.run_test(test_path, parameters=parameters)
                
                # Expand individual test results
                if result.get("tests"):
                    for test in result["tests"]:
                        all_results.append({
                            "notebook": result["notebook"],
                            "test_name": test["name"],
                            "class_name": test.get("class_name", ""),
                            "status": test["status"],
                            "duration": test.get("duration", 0),
                            "timestamp": result["timestamp"],
                            "run_id": result.get("run_id"),
                            "error_message": test.get("error_message", ""),
                            "error_traceback": test.get("error_traceback", ""),
                        })
                else:
                    # If no individual tests parsed, add notebook-level result
                    all_results.append({
                        "notebook": result["notebook"],
                        "test_name": "all_tests",
                        "status": result["status"],
                        "duration": result["duration"],
                        "timestamp": result["timestamp"],
                        "run_id": result.get("run_id"),
                        "error_message": result.get("error_message", ""),
                        "error_traceback": result.get("error_traceback", ""),
                    })
                
                progress.advance(task)
        
        return all_results
    
    def _run_tests_parallel(
        self,
        test_notebooks: List[Dict[str, Any]],
        parameters: Optional[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        """Run tests in parallel."""
        all_results = []
        max_workers = min(
            self.config.execution.max_parallel_jobs,
            len(test_notebooks),
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        ) as progress:
            task = progress.add_task(
                f"Running {len(test_notebooks)} test(s) in parallel...",
                total=len(test_notebooks),
            )
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all jobs
                future_to_test = {
                    executor.submit(
                        self.run_test,
                        Path(test_info["path"]),
                        None,
                        parameters,
                    ): test_info
                    for test_info in test_notebooks
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_test):
                    test_info = future_to_test[future]
                    try:
                        result = future.result()
                        
                        # Expand individual test results
                        if result.get("tests"):
                            for test in result["tests"]:
                                all_results.append({
                                    "notebook": result["notebook"],
                                    "test_name": test["name"],
                                    "status": test["status"],
                                    "duration": test.get("duration", 0),
                                    "timestamp": result["timestamp"],
                                    "run_id": result.get("run_id"),
                                    "error_message": test.get("error_message", ""),
                                })
                        else:
                            all_results.append({
                                "notebook": result["notebook"],
                                "test_name": "all_tests",
                                "status": result["status"],
                                "duration": result["duration"],
                                "timestamp": result["timestamp"],
                                "run_id": result.get("run_id"),
                                "error_message": result.get("error_message", ""),
                            })
                    
                    except Exception as e:
                        all_results.append({
                            "notebook": test_info["name"],
                            "test_name": "all_tests",
                            "status": "error",
                            "duration": 0,
                            "timestamp": datetime.now().isoformat(),
                            "error_message": str(e),
                        })
                    
                    progress.advance(task)
        
        return all_results
    
    def run_workspace_tests(
        self,
        workspace_path: str,
        notebooks: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Run tests that are already in the workspace (no upload).
        
        Args:
            workspace_path: Base workspace path containing tests
            notebooks: List of notebook paths to run
        
        Returns:
            List of test results
        """
        all_results = []
        
        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=self.console,
            ) as progress:
                task = progress.add_task(
                    f"Running {len(notebooks)} notebook(s)",
                    total=len(notebooks)
                )
                
                for notebook_path in notebooks:
                    try:
                        # Run the notebook directly from workspace (no upload)
                        if self.verbose:
                            self.console.print(f"[dim]Running workspace notebook: {notebook_path}[/dim]")
                        
                        # Determine compute configuration
                        cluster_spec = self.config.cluster.get_cluster_spec()
                        cluster_id = self.config.cluster.cluster_id
                        use_serverless = self.config.cluster.use_serverless()
                        
                        # Run notebook directly with framework library
                        run_id = self.db_helper.run_notebook(
                            notebook_path=notebook_path,
                            cluster_spec=cluster_spec if not cluster_id and not use_serverless else None,
                            cluster_id=cluster_id,
                            use_serverless=use_serverless,
                            parameters=self.config.parameters,
                            timeout=self.config.execution.timeout,
                            libraries=self.config.cluster.libraries,
                            environment_key=self.config.cluster.environment_key,
                        )
                        
                        # Wait for completion
                        status = self.db_helper.wait_for_run(
                            run_id=run_id,
                            timeout=self.config.execution.timeout,
                            poll_interval=self.config.execution.poll_interval,
                        )
                        
                        # Get output
                        output = self.db_helper.get_run_output(run_id)
                        
                        if self.verbose and not output:
                            self.console.print(f"[yellow]Warning: No output received from notebook.[/yellow]")
                            self.console.print(f"[dim]Make sure your notebook ends with: dbutils.notebook.exit(json.dumps(results))[/dim]")
                        
                        # Parse results
                        test_results = self._parse_test_output(output)
                        
                        # Add to results
                        result = {
                            "notebook": notebook_path,
                            "status": "passed" if status.get("result_state") == "SUCCESS" else "failed",
                            "duration": 0,  # Could calculate from run metadata
                            "timestamp": datetime.now().isoformat(),
                            "run_id": run_id,
                            "tests": test_results,
                            "error_message": status.get("state_message", "") if status.get("result_state") != "SUCCESS" else "",
                        }
                        
                        # Expand individual test results
                        if test_results:
                            for test in test_results:
                                all_results.append({
                                    "notebook": notebook_path,
                                    "test_name": test["name"],
                                    "status": test["status"],
                                    "duration": test.get("duration", 0),
                                    "timestamp": result["timestamp"],
                                    "run_id": run_id,
                                    "error_message": test.get("error_message", ""),
                                })
                        else:
                            all_results.append({
                                "notebook": notebook_path,
                                "test_name": "all_tests",
                                "status": result["status"],
                                "duration": result["duration"],
                                "timestamp": result["timestamp"],
                                "run_id": run_id,
                                "error_message": result.get("error_message", ""),
                            })
                    
                    except Exception as e:
                        self.console.print(f"[red]Error running {notebook_path}: {e}[/red]")
                        all_results.append({
                            "notebook": notebook_path,
                            "test_name": "all_tests",
                            "status": "error",
                            "duration": 0,
                            "timestamp": datetime.now().isoformat(),
                            "error_message": str(e),
                        })
                    
                    progress.advance(task)
        
        return all_results
    
    def _parse_test_output(self, output: Optional[str]) -> List[Dict[str, Any]]:
        """
        Parse test output to extract individual test results.
        
        The notebook should return results as JSON via dbutils.notebook.exit(json.dumps(results))
        
        Args:
            output: Output from notebook run (JSON string or plain text)
        
        Returns:
            List of test result dictionaries
        """
        if not output:
            return []
        
        # Try to parse as JSON first (from dbutils.notebook.exit())
        try:
            import json
            
            results_dict = json.loads(output)
            
            # Extract individual test results from fixtures
            all_tests = []
            
            # Format 1: Results from run_notebook_tests() with no arguments (auto-discovery)
            if "fixtures" in results_dict:
                for fixture in results_dict["fixtures"]:
                    fixture_name = fixture.get("fixture_name", "Unknown")
                    summary = fixture.get("summary", {})
                    test_results = summary.get("results", [])
                    
                    for test in test_results:
                        all_tests.append({
                            "name": f"{fixture_name}.{test['name']}",
                            "status": test.get("status", "unknown"),
                            "duration": test.get("duration", 0),
                            "error_message": test.get("error_message"),
                            "error_traceback": test.get("error_traceback"),
                        })
            
            # Format 2: Results from run_notebook_tests(TestClass) with specific class
            elif "results" in results_dict:
                test_results = results_dict.get("results", [])
                
                for test in test_results:
                    all_tests.append({
                        "name": test.get("name", "unknown"),
                        "status": test.get("status", "unknown"),
                        "duration": test.get("duration", 0),
                        "error_message": test.get("error_message"),
                        "error_traceback": test.get("error_traceback"),
                    })
            
            return all_tests
            
        except (json.JSONDecodeError, Exception) as e:
            # Fall back to parsing plain text output
            if self.verbose:
                self.console.print(f"[dim]Could not parse JSON output: {e}[/dim]")
            pass
        
        # Parse plain text output (fallback)
        results = []
        lines = output.split("\n")
        for line in lines:
            line = line.strip()
            
            if "✓ PASSED" in line or "PASSED:" in line:
                if "Running " in line:
                    test_name = line.split("Running ")[1].split("...")[0].strip()
                elif "PASSED:" in line:
                    test_name = line.split("PASSED:")[1].strip()
                else:
                    continue
                results.append({
                    "name": test_name,
                    "status": "passed",
                    "duration": 0,
                })
            elif "✗ FAILED" in line or "FAILED:" in line:
                if "Running " in line:
                    test_name = line.split("Running ")[1].split("...")[0].strip()
                elif "FAILED:" in line:
                    test_name = line.split("FAILED:")[1].strip()
                else:
                    continue
                results.append({
                    "name": test_name,
                    "status": "failed",
                    "duration": 0,
                })
        
        return results

