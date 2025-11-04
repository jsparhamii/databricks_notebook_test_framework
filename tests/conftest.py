"""
Pytest configuration and shared fixtures.
"""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_test_notebook():
    """Create a sample test notebook content."""
    return """
from dbx_test import NotebookTestFixture, run_notebook_tests
import json

class TestExample(NotebookTestFixture):
    def run_setup(self):
        self.data = [1, 2, 3, 4, 5]
    
    def test_sum(self):
        assert sum(self.data) == 15
    
    def test_length(self):
        assert len(self.data) == 5
    
    def test_max(self):
        assert max(self.data) == 5
    
    def run_cleanup(self):
        del self.data

# Run tests
results = run_notebook_tests(TestExample)
dbutils.notebook.exit(json.dumps(results))
"""


@pytest.fixture
def sample_config_dict():
    """Create a sample configuration dictionary."""
    return {
        "workspace": {
            "host": "https://adb-123.azuredatabricks.net",
            "profile": "adb",
        },
        "cluster": {
            "size": "M",
            "libraries": [
                {"pypi": {"package": "pandas==2.0.0"}},
                {"pypi": {"package": "dbx_test"}},
            ],
        },
        "execution": {
            "timeout": 600,
            "parallel": False,
        },
        "paths": {
            "workspace_root": "/Workspace/Repos/tests",
            "test_pattern": "**/*_test.py",
        },
        "reporting": {
            "output_dir": ".dbx-test-results",
            "formats": ["junit", "console", "json"],
        },
    }


@pytest.fixture
def sample_test_results():
    """Create sample test results."""
    return {
        "run_timestamp": "2025-01-01T10:00:00",
        "summary": {
            "total": 3,
            "passed": 2,
            "failed": 1,
            "skipped": 0,
            "duration": 5.5,
        },
        "tests": [
            {
                "notebook": "test_example",
                "test_name": "test_sum",
                "class_name": "TestExample",
                "status": "passed",
                "duration": 1.2,
                "timestamp": "2025-01-01T10:00:01",
            },
            {
                "notebook": "test_example",
                "test_name": "test_length",
                "class_name": "TestExample",
                "status": "passed",
                "duration": 0.8,
                "timestamp": "2025-01-01T10:00:02",
            },
            {
                "notebook": "test_example",
                "test_name": "test_max",
                "class_name": "TestExample",
                "status": "failed",
                "duration": 3.5,
                "error_message": "AssertionError: Expected 10, got 5",
                "error_traceback": "Traceback (most recent call last):\n  ...",
                "timestamp": "2025-01-01T10:00:03",
            },
        ],
    }


@pytest.fixture
def create_test_file(temp_dir):
    """Factory fixture to create test files."""
    def _create_file(filename, content):
        file_path = temp_dir / filename
        file_path.write_text(content)
        return file_path
    
    return _create_file


@pytest.fixture
def mock_databricks_workspace(monkeypatch):
    """Mock Databricks workspace interactions."""
    class MockWorkspaceClient:
        def __init__(self, *args, **kwargs):
            self.host = kwargs.get("host", "https://mock.databricks.com")
            self.token = kwargs.get("token", "mock-token")
        
        class workspace:
            @staticmethod
            def list(path):
                return []
            
            @staticmethod
            def get_status(path):
                return {"path": path, "object_type": "NOTEBOOK"}
        
        class jobs:
            @staticmethod
            def submit(run_name, tasks):
                return {"run_id": 12345}
            
            @staticmethod
            def get_run(run_id):
                return {
                    "run_id": run_id,
                    "state": {
                        "life_cycle_state": "TERMINATED",
                        "result_state": "SUCCESS",
                    },
                }
    
    # This is a simplified mock - in real tests you'd use unittest.mock
    return MockWorkspaceClient


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_databricks: mark test as requiring Databricks connection"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Mark slow tests
        if "slow" in item.nodeid or hasattr(item, "callspec") and "slow" in str(item.callspec):
            item.add_marker(pytest.mark.slow)

