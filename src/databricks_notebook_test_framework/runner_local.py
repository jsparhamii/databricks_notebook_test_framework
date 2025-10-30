"""
Local test execution.
"""

import sys
import os
import json
import time
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn


class LocalTestRunner:
    """Execute tests locally using direct Python module execution."""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize local test runner.
        
        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.console = Console()
    
    def run_test(
        self,
        test_notebook: Path,
        parameters: Optional[Dict[str, str]] = None,
        timeout: int = 600,
    ) -> Dict[str, Any]:
        """
        Run a single test notebook locally.
        
        Args:
            test_notebook: Path to test notebook
            parameters: Optional parameters to pass
            timeout: Timeout in seconds
        
        Returns:
            Test result dictionary
        """
        start_time = time.time()
        
        try:
            # Load the test module
            spec = importlib.util.spec_from_file_location(
                test_notebook.stem,
                str(test_notebook)
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load module from {test_notebook}")
            
            module = importlib.util.module_from_spec(spec)
            
            # Add test directory to sys.path temporarily
            test_dir = str(test_notebook.parent)
            if test_dir not in sys.path:
                sys.path.insert(0, test_dir)
            
            try:
                # Execute the module
                spec.loader.exec_module(module)
                
                # Import our test framework
                from databricks_notebook_test_framework.testing import discover_fixtures
                
                # Discover all test fixtures in the module
                fixtures = discover_fixtures(module)
                
                if not fixtures:
                    return {
                        "notebook": test_notebook.stem,
                        "notebook_path": str(test_notebook),
                        "status": "failed",
                        "duration": time.time() - start_time,
                        "timestamp": datetime.now().isoformat(),
                        "error_message": "No test fixtures found in notebook",
                        "tests": [],
                    }
                
                # Run all fixtures
                all_test_results = []
                for fixture_class in fixtures:
                    if self.verbose:
                        self.console.print(f"[dim]Running {fixture_class.__name__}...[/dim]")
                    
                    fixture = fixture_class()
                    results = fixture.execute_tests()
                    
                    for result in results:
                        all_test_results.append({
                            "name": result.test_name,
                            "class_name": fixture_class.__name__,
                            "status": result.status,
                            "duration": result.duration,
                            "error_message": result.error_message,
                            "error_traceback": result.error_traceback,
                        })
                
                # Determine overall status
                any_failed = any(t["status"] in ["failed", "error"] for t in all_test_results)
                overall_status = "failed" if any_failed else "passed"
                
                duration = time.time() - start_time
                
                return {
                    "notebook": test_notebook.stem,
                    "notebook_path": str(test_notebook),
                    "status": overall_status,
                    "duration": duration,
                    "timestamp": datetime.now().isoformat(),
                    "tests": all_test_results,
                }
            
            finally:
                # Remove test directory from sys.path
                if test_dir in sys.path:
                    sys.path.remove(test_dir)
        
        except Exception as e:
            duration = time.time() - start_time
            return {
                "notebook": test_notebook.stem,
                "notebook_path": str(test_notebook),
                "status": "error",
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
        timeout: int = 600,
    ) -> Dict[str, Any]:
        """
        Run multiple test notebooks.
        
        Args:
            test_notebooks: List of test notebook info dictionaries
            parameters: Optional parameters to pass to all tests
            timeout: Timeout per test in seconds
        
        Returns:
            Aggregated results dictionary
        """
        all_results = []
        start_time = time.time()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
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
                
                result = self.run_test(test_path, parameters, timeout)
                
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
                        "error_message": result.get("error_message", ""),
                        "error_traceback": result.get("error_traceback", ""),
                    })
                
                progress.advance(task)
        
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
            "run_type": "local",
            "run_timestamp": datetime.now().isoformat(),
            "summary": summary,
            "tests": all_results,
        }

