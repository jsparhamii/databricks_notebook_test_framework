"""
Test result reporting in multiple formats.
"""

import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
from junit_xml import TestSuite, TestCase
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


class TestReporter:
    """Generate test reports in multiple formats."""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize reporter.
        
        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.console = Console()
    
    def generate_junit_xml(
        self,
        results: Dict[str, Any],
        output_path: Path,
    ) -> None:
        """
        Generate JUnit XML report.
        
        Args:
            results: Test results dictionary
            output_path: Output file path
        """
        test_cases = []
        
        for test_result in results.get("tests", []):
            test_name = f"{test_result['notebook']}::{test_result['test_name']}"
            
            test_case = TestCase(
                name=test_name,
                classname=test_result.get("class_name", test_result["notebook"]),
                elapsed_sec=test_result.get("duration", 0),
                timestamp=test_result.get("timestamp"),
            )
            
            if test_result["status"] == "failed":
                test_case.add_failure_info(
                    message=test_result.get("error_message", "Test failed"),
                    output=test_result.get("error_traceback", ""),
                )
            elif test_result["status"] == "skipped":
                test_case.add_skipped_info(
                    message=test_result.get("skip_reason", "Test skipped"),
                )
            
            test_cases.append(test_case)
        
        # Create test suite
        summary = results.get("summary", {})
        test_suite = TestSuite(
            name="Databricks Notebook Tests",
            test_cases=test_cases,
            timestamp=results.get("run_timestamp"),
        )
        
        # Write XML
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(TestSuite.to_xml_string([test_suite]))
    
    def generate_json_report(
        self,
        results: Dict[str, Any],
        output_path: Path,
    ) -> None:
        """
        Generate JSON report.
        
        Args:
            results: Test results dictionary
            output_path: Output file path
        """
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
    
    def generate_html_report(
        self,
        results: Dict[str, Any],
        output_path: Path,
    ) -> None:
        """
        Generate HTML report.
        
        Args:
            results: Test results dictionary
            output_path: Output file path
        """
        summary = results.get("summary", {})
        tests = results.get("tests", [])
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Databricks Notebook Test Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 5px;
        }}
        .summary {{
            background-color: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-item {{
            display: inline-block;
            margin: 0 20px;
        }}
        .passed {{ color: #27ae60; }}
        .failed {{ color: #e74c3c; }}
        .skipped {{ color: #f39c12; }}
        table {{
            width: 100%;
            background-color: white;
            border-collapse: collapse;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #34495e;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .status-badge {{
            padding: 4px 8px;
            border-radius: 3px;
            font-weight: bold;
        }}
        .status-passed {{
            background-color: #27ae60;
            color: white;
        }}
        .status-failed {{
            background-color: #e74c3c;
            color: white;
        }}
        .status-skipped {{
            background-color: #f39c12;
            color: white;
        }}
        .error-message {{
            background-color: #ffe6e6;
            padding: 10px;
            border-left: 4px solid #e74c3c;
            margin-top: 10px;
            font-family: monospace;
            white-space: pre-wrap;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Databricks Notebook Test Report</h1>
        <p>Generated: {results.get('run_timestamp', 'N/A')}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <div class="summary-item">
            <strong>Total:</strong> {summary.get('total', 0)}
        </div>
        <div class="summary-item passed">
            <strong>Passed:</strong> {summary.get('passed', 0)}
        </div>
        <div class="summary-item failed">
            <strong>Failed:</strong> {summary.get('failed', 0)}
        </div>
        <div class="summary-item skipped">
            <strong>Skipped:</strong> {summary.get('skipped', 0)}
        </div>
        <div class="summary-item">
            <strong>Duration:</strong> {summary.get('duration', 0):.2f}s
        </div>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>Notebook</th>
                <th>Test</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Message</th>
            </tr>
        </thead>
        <tbody>
"""
        
        for test in tests:
            status = test["status"]
            status_class = f"status-{status}"
            message = test.get("error_message", "")
            
            html += f"""
            <tr>
                <td>{test['notebook']}</td>
                <td>{test['test_name']}</td>
                <td><span class="status-badge {status_class}">{status.upper()}</span></td>
                <td>{test.get('duration', 0):.2f}s</td>
                <td>{message}</td>
            </tr>
"""
            
            if status == "failed" and test.get("error_traceback"):
                html += f"""
            <tr>
                <td colspan="5">
                    <div class="error-message">{test['error_traceback']}</div>
                </td>
            </tr>
"""
        
        html += """
        </tbody>
    </table>
</body>
</html>
"""
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
    
    def print_console_report(self, results: Dict[str, Any]) -> None:
        """Print test report to console."""
        summary = results.get("summary", {})
        tests = results.get("tests", [])
        
        # Print header
        self.console.print("\n")
        self.console.print(Panel(
            "[bold]Databricks Notebook Test Results[/bold]",
            style="bold blue",
        ))
        
        # Print summary
        summary_text = Text()
        summary_text.append(f"Total: {summary.get('total', 0)}  ", style="bold")
        summary_text.append(f"Passed: {summary.get('passed', 0)}  ", style="bold green")
        summary_text.append(f"Failed: {summary.get('failed', 0)}  ", style="bold red")
        summary_text.append(f"Skipped: {summary.get('skipped', 0)}  ", style="bold yellow")
        summary_text.append(f"Duration: {summary.get('duration', 0):.2f}s", style="bold")
        
        self.console.print(Panel(summary_text, title="Summary", border_style="green"))
        
        # Print detailed results table
        if tests:
            table = Table(title="Test Details")
            table.add_column("Notebook", style="cyan")
            table.add_column("Test", style="magenta")
            table.add_column("Status", justify="center")
            table.add_column("Duration", justify="right")
            table.add_column("Message", style="dim")
            
            for test in tests:
                status = test["status"]
                if status == "passed":
                    status_display = "[green]✓ PASSED[/green]"
                elif status == "failed":
                    status_display = "[red]✗ FAILED[/red]"
                elif status == "skipped":
                    status_display = "[yellow]⊘ SKIPPED[/yellow]"
                else:
                    status_display = status
                
                message = test.get("error_message", "")[:50]
                
                table.add_row(
                    test["notebook"],
                    test["test_name"],
                    status_display,
                    f"{test.get('duration', 0):.2f}s",
                    message,
                )
            
            self.console.print(table)
        
        # Print failures in detail
        failed_tests = [t for t in tests if t["status"] == "failed"]
        if failed_tests:
            self.console.print("\n[bold red]Failed Tests Details:[/bold red]")
            for test in failed_tests:
                self.console.print(f"\n[red]✗ {test['notebook']}::{test['test_name']}[/red]")
                if test.get("error_message"):
                    self.console.print(f"  Message: {test['error_message']}")
                if self.verbose and test.get("error_traceback"):
                    self.console.print(f"  Traceback:\n{test['error_traceback']}")
        
        self.console.print("\n")
    
    def generate_summary_text(self, results: Dict[str, Any]) -> str:
        """Generate plain text summary."""
        summary = results.get("summary", {})
        
        text = "=" * 60 + "\n"
        text += "DATABRICKS NOTEBOOK TEST RESULTS\n"
        text += "=" * 60 + "\n\n"
        text += f"Timestamp: {results.get('run_timestamp', 'N/A')}\n"
        text += f"Total Tests: {summary.get('total', 0)}\n"
        text += f"Passed: {summary.get('passed', 0)}\n"
        text += f"Failed: {summary.get('failed', 0)}\n"
        text += f"Skipped: {summary.get('skipped', 0)}\n"
        text += f"Duration: {summary.get('duration', 0):.2f}s\n"
        text += "=" * 60 + "\n"
        
        return text

