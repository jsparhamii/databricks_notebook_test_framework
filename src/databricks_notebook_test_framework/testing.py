"""
Notebook testing base class implementation.

This module provides the NotebookTestFixture base class for organizing
and executing tests in Databricks notebooks.
"""

import inspect
import time
import traceback
from typing import List, Dict, Any, Optional, Callable
from abc import ABC


class TestResult:
    """Represents the result of a single test."""
    
    def __init__(
        self,
        test_name: str,
        status: str,
        duration: float,
        error_message: Optional[str] = None,
        error_traceback: Optional[str] = None,
    ):
        self.test_name = test_name
        self.status = status
        self.duration = duration
        self.error_message = error_message
        self.error_traceback = error_traceback
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.test_name,
            "status": self.status,
            "duration": self.duration,
            "error_message": self.error_message,
            "error_traceback": self.error_traceback,
        }


class NotebookTestFixture(ABC):
    """
    Base class for notebook test fixtures.
    
    Provides a pattern for organizing notebook tests with setup, test methods, and cleanup.
    
    Usage:
        class TestMyNotebook(NotebookTestFixture):
            def run_setup(self):
                # Setup code
                pass
            
            def test_something(self):
                # Test code
                assert True, "Test failed"
            
            def run_cleanup(self):
                # Cleanup code
                pass
    """
    
    def __init__(self):
        """Initialize the test fixture."""
        self.results: List[TestResult] = []
        self._setup_executed = False
        self._cleanup_executed = False
    
    def run_setup(self):
        """Override this method to provide setup logic."""
        pass
    
    def run_cleanup(self):
        """Override this method to provide cleanup logic."""
        pass
    
    def _execute_setup(self) -> bool:
        """Execute the setup method."""
        if self._setup_executed:
            return True
        
        try:
            self.run_setup()
            self._setup_executed = True
            return True
        except Exception as e:
            print(f"Setup failed: {e}")
            traceback.print_exc()
            return False
    
    def _execute_cleanup(self):
        """Execute the cleanup method."""
        if self._cleanup_executed:
            return
        
        try:
            self.run_cleanup()
            self._cleanup_executed = True
        except Exception as e:
            print(f"Cleanup failed: {e}")
            traceback.print_exc()
    
    def _get_test_methods(self) -> List[Callable]:
        """Get all test methods (methods starting with 'test_')."""
        test_methods = []
        for name in dir(self):
            if name.startswith("test_") and callable(getattr(self, name)):
                method = getattr(self, name)
                if not name.startswith("test__"):  # Skip private test methods
                    test_methods.append((name, method))
        return test_methods
    
    def _execute_test(self, test_name: str, test_method: Callable) -> TestResult:
        """Execute a single test method."""
        start_time = time.time()
        
        try:
            test_method()
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status="passed",
                duration=duration,
            )
        except AssertionError as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status="failed",
                duration=duration,
                error_message=str(e),
                error_traceback=traceback.format_exc(),
            )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status="error",
                duration=duration,
                error_message=f"Unexpected error: {str(e)}",
                error_traceback=traceback.format_exc(),
            )
    
    def execute_tests(self) -> List[TestResult]:
        """
        Execute all tests in the fixture.
        
        Returns:
            List of TestResult objects
        """
        self.results = []
        
        # Execute setup
        if not self._execute_setup():
            print(f"Skipping tests due to setup failure")
            return self.results
        
        # Get and execute test methods
        test_methods = self._get_test_methods()
        
        for test_name, test_method in test_methods:
            print(f"Running {test_name}...")
            result = self._execute_test(test_name, test_method)
            self.results.append(result)
            
            if result.status == "passed":
                print(f"  ✓ PASSED")
            elif result.status == "failed":
                print(f"  ✗ FAILED: {result.error_message}")
            else:
                print(f"  ✗ ERROR: {result.error_message}")
        
        # Execute cleanup
        self._execute_cleanup()
        
        return self.results
    
    def get_results(self) -> Dict[str, Any]:
        """
        Get test results summary.
        
        Returns:
            Dictionary with test results
        """
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "passed")
        failed = sum(1 for r in self.results if r.status == "failed")
        errors = sum(1 for r in self.results if r.status == "error")
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "results": [r.to_dict() for r in self.results],
        }


def discover_fixtures(module_or_globals) -> List[type]:
    """
    Discover all NotebookTestFixture subclasses in a module or globals dict.
    
    Args:
        module_or_globals: Module object or globals() dict
    
    Returns:
        List of NotebookTestFixture subclasses
    """
    fixtures = []
    
    if isinstance(module_or_globals, dict):
        items = module_or_globals.items()
    else:
        items = inspect.getmembers(module_or_globals)
    
    for name, obj in items:
        if (inspect.isclass(obj) and 
            issubclass(obj, NotebookTestFixture) and 
            obj is not NotebookTestFixture):
            fixtures.append(obj)
    
    return fixtures


def run_tests(module_or_globals) -> Dict[str, Any]:
    """
    Discover and run all tests in a module or globals dict.
    
    Args:
        module_or_globals: Module object or globals() dict
    
    Returns:
        Dictionary with aggregated test results
    """
    fixtures = discover_fixtures(module_or_globals)
    
    all_results = []
    fixture_summaries = []
    
    for fixture_class in fixtures:
        print(f"\n{'='*60}")
        print(f"Running {fixture_class.__name__}")
        print(f"{'='*60}\n")
        
        fixture = fixture_class()
        results = fixture.execute_tests()
        summary = fixture.get_results()
        
        fixture_summaries.append({
            "fixture_name": fixture_class.__name__,
            "summary": summary,
        })
        
        all_results.extend(results)
    
    # Aggregate results
    total = len(all_results)
    passed = sum(1 for r in all_results if r.status == "passed")
    failed = sum(1 for r in all_results if r.status == "failed")
    errors = sum(1 for r in all_results if r.status == "error")
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Errors: {errors}")
    print(f"{'='*60}\n")
    
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "fixtures": fixture_summaries,
        "all_results": [r.to_dict() for r in all_results],
    }


# Legacy alias for backwards compatibility (will be removed in future versions)
NutterFixture = NotebookTestFixture

