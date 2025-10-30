"""
Databricks Notebook Test Framework

A comprehensive testing framework for Databricks notebooks.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"

from databricks_notebook_test_framework.config import TestConfig
from databricks_notebook_test_framework.discovery import TestDiscovery
from databricks_notebook_test_framework.runner_local import LocalTestRunner
from databricks_notebook_test_framework.runner_remote import RemoteTestRunner
from databricks_notebook_test_framework.reporting import TestReporter
from databricks_notebook_test_framework.testing import NotebookTestFixture, run_tests
from databricks_notebook_test_framework.notebook_runner import (
    NotebookRunner,
    run_notebook_tests,
    quick_test,
    install_notebook_package,
)

__all__ = [
    "TestConfig",
    "TestDiscovery",
    "LocalTestRunner",
    "RemoteTestRunner",
    "TestReporter",
    "NotebookTestFixture",
    "run_tests",
    "NotebookRunner",
    "run_notebook_tests",
    "quick_test",
    "install_notebook_package",
]

