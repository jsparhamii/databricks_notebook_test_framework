"""
Unit tests for the reporting module.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from dbx_test.reporting import TestReporter


class TestTestReporter:
    """Tests for TestReporter class."""
    
    @pytest.fixture
    def sample_results(self):
        """Create sample test results."""
        return {
            "run_timestamp": "2025-01-01T10:00:00",
            "summary": {
                "total": 5,
                "passed": 3,
                "failed": 1,
                "skipped": 1,
                "duration": 12.5,
            },
            "tests": [
                {
                    "notebook": "test_example",
                    "test_name": "test_one",
                    "class_name": "TestExample",
                    "status": "passed",
                    "duration": 2.3,
                    "timestamp": "2025-01-01T10:00:01",
                },
                {
                    "notebook": "test_example",
                    "test_name": "test_two",
                    "class_name": "TestExample",
                    "status": "passed",
                    "duration": 1.8,
                    "timestamp": "2025-01-01T10:00:03",
                },
                {
                    "notebook": "test_example",
                    "test_name": "test_three",
                    "class_name": "TestExample",
                    "status": "failed",
                    "duration": 3.2,
                    "error_message": "Assertion failed: Expected 10, got 5",
                    "error_traceback": "Traceback (most recent call last):\n  ...",
                    "timestamp": "2025-01-01T10:00:05",
                },
                {
                    "notebook": "test_another",
                    "test_name": "test_something",
                    "class_name": "TestAnother",
                    "status": "passed",
                    "duration": 4.1,
                    "timestamp": "2025-01-01T10:00:08",
                },
                {
                    "notebook": "test_another",
                    "test_name": "test_skipped",
                    "class_name": "TestAnother",
                    "status": "skipped",
                    "duration": 0.1,
                    "skip_reason": "Not applicable in this environment",
                    "timestamp": "2025-01-01T10:00:12",
                },
            ],
        }
    
    def test_initialization(self):
        """Test reporter initialization."""
        reporter = TestReporter()
        assert reporter.verbose is False
        
        reporter = TestReporter(verbose=True)
        assert reporter.verbose is True
    
    def test_generate_junit_xml(self, sample_results):
        """Test generating JUnit XML report."""
        reporter = TestReporter()
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            output_path = Path(f.name)
        
        try:
            reporter.generate_junit_xml(sample_results, output_path)
            
            # Verify file was created
            assert output_path.exists()
            
            # Verify XML content
            content = output_path.read_text()
            assert '<?xml version' in content
            assert 'testsuite' in content
            assert 'test_example::test_one' in content
            assert 'test_example::test_three' in content
            assert 'failure' in content.lower()
        finally:
            # Cleanup
            if output_path.exists():
                output_path.unlink()
    
    def test_generate_json_report(self, sample_results):
        """Test generating JSON report."""
        reporter = TestReporter()
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = Path(f.name)
        
        try:
            reporter.generate_json_report(sample_results, output_path)
            
            # Verify file was created
            assert output_path.exists()
            
            # Verify JSON content
            with open(output_path, "r") as f:
                data = json.load(f)
            
            assert data["summary"]["total"] == 5
            assert data["summary"]["passed"] == 3
            assert data["summary"]["failed"] == 1
            assert len(data["tests"]) == 5
        finally:
            # Cleanup
            if output_path.exists():
                output_path.unlink()
    
    def test_generate_html_report(self, sample_results):
        """Test generating HTML report."""
        reporter = TestReporter()
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = Path(f.name)
        
        try:
            reporter.generate_html_report(sample_results, output_path)
            
            # Verify file was created
            assert output_path.exists()
            
            # Verify HTML content
            content = output_path.read_text()
            assert '<!DOCTYPE html>' in content
            assert 'Databricks Notebook Test Report' in content
            assert 'test_example' in content
            assert 'test_one' in content
            # HTML uses <strong> tags, so check the actual format
            assert '<strong>Passed:</strong> 3' in content
            assert '<strong>Failed:</strong> 1' in content
            assert 'status-passed' in content
            assert 'status-failed' in content
        finally:
            # Cleanup
            if output_path.exists():
                output_path.unlink()
    
    def test_generate_html_report_includes_traceback(self, sample_results):
        """Test that HTML report includes error tracebacks."""
        reporter = TestReporter()
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = Path(f.name)
        
        try:
            reporter.generate_html_report(sample_results, output_path)
            
            content = output_path.read_text()
            assert 'error-message' in content
            assert 'Traceback' in content
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_print_console_report(self, sample_results, capsys):
        """Test printing console report."""
        reporter = TestReporter()
        reporter.print_console_report(sample_results)
        
        captured = capsys.readouterr()
        
        # Check summary
        assert "Total: 5" in captured.out
        assert "Passed: 3" in captured.out
        assert "Failed: 1" in captured.out
        assert "Skipped: 1" in captured.out
        
        # Check test names
        assert "test_one" in captured.out
        assert "test_three" in captured.out
    
    def test_print_console_report_verbose(self, sample_results, capsys):
        """Test printing verbose console report."""
        reporter = TestReporter(verbose=True)
        reporter.print_console_report(sample_results)
        
        captured = capsys.readouterr()
        
        # Check that tracebacks are included in verbose mode
        assert "Traceback" in captured.out
    
    def test_generate_summary_text(self, sample_results):
        """Test generating plain text summary."""
        reporter = TestReporter()
        text = reporter.generate_summary_text(sample_results)
        
        assert "DATABRICKS NOTEBOOK TEST RESULTS" in text
        assert "Total Tests: 5" in text
        assert "Passed: 3" in text
        assert "Failed: 1" in text
        assert "Skipped: 1" in text
        assert "Duration: 12.50s" in text
    
    def test_junit_xml_with_failures(self, sample_results):
        """Test that JUnit XML correctly reports failures."""
        reporter = TestReporter()
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            output_path = Path(f.name)
        
        try:
            reporter.generate_junit_xml(sample_results, output_path)
            
            content = output_path.read_text()
            
            # Check for failure element
            assert '<failure' in content
            assert 'Assertion failed: Expected 10, got 5' in content
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_junit_xml_with_skipped(self, sample_results):
        """Test that JUnit XML correctly reports skipped tests."""
        reporter = TestReporter()
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            output_path = Path(f.name)
        
        try:
            reporter.generate_junit_xml(sample_results, output_path)
            
            content = output_path.read_text()
            
            # Check for skipped element
            assert '<skipped' in content
            assert 'Not applicable in this environment' in content
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_console_report_with_no_tests(self, capsys):
        """Test console report with no tests."""
        reporter = TestReporter()
        results = {
            "run_timestamp": "2025-01-01T10:00:00",
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "duration": 0.0,
            },
            "tests": [],
        }
        
        reporter.print_console_report(results)
        
        captured = capsys.readouterr()
        assert "Total: 0" in captured.out


class TestTestReporterFormats:
    """Tests for different report formats."""
    
    def test_junit_xml_structure(self):
        """Test JUnit XML structure."""
        reporter = TestReporter()
        
        results = {
            "run_timestamp": "2025-01-01T10:00:00",
            "summary": {"total": 1, "passed": 1, "failed": 0, "skipped": 0},
            "tests": [
                {
                    "notebook": "test_basic",
                    "test_name": "test_simple",
                    "class_name": "TestBasic",
                    "status": "passed",
                    "duration": 1.0,
                    "timestamp": "2025-01-01T10:00:01",
                }
            ],
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            output_path = Path(f.name)
        
        try:
            reporter.generate_junit_xml(results, output_path)
            
            content = output_path.read_text()
            
            # Verify test case is present
            assert 'test_basic::test_simple' in content
            assert 'classname="TestBasic"' in content
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_html_report_styling(self):
        """Test that HTML report includes proper styling."""
        reporter = TestReporter()
        
        results = {
            "run_timestamp": "2025-01-01T10:00:00",
            "summary": {"total": 1, "passed": 1, "failed": 0, "skipped": 0, "duration": 1.0},
            "tests": [
                {
                    "notebook": "test_basic",
                    "test_name": "test_simple",
                    "status": "passed",
                    "duration": 1.0,
                }
            ],
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = Path(f.name)
        
        try:
            reporter.generate_html_report(results, output_path)
            
            content = output_path.read_text()
            
            # Verify styling is present
            assert '<style>' in content
            assert 'status-passed' in content
            assert 'font-family' in content
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_json_report_completeness(self):
        """Test that JSON report includes all data."""
        reporter = TestReporter()
        
        results = {
            "run_timestamp": "2025-01-01T10:00:00",
            "summary": {"total": 1, "passed": 1, "failed": 0, "skipped": 0},
            "tests": [
                {
                    "notebook": "test_basic",
                    "test_name": "test_simple",
                    "status": "passed",
                    "duration": 1.0,
                    "custom_field": "custom_value",
                }
            ],
            "metadata": {
                "environment": "test",
            },
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = Path(f.name)
        
        try:
            reporter.generate_json_report(results, output_path)
            
            with open(output_path, "r") as f:
                data = json.load(f)
            
            # Verify all data is preserved
            assert data["run_timestamp"] == "2025-01-01T10:00:00"
            assert data["tests"][0]["custom_field"] == "custom_value"
            assert data["metadata"]["environment"] == "test"
        finally:
            if output_path.exists():
                output_path.unlink()

