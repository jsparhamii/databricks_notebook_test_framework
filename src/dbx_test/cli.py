"""
Command-line interface for the test framework.
"""

import sys
import click
from pathlib import Path
from datetime import datetime
from rich.console import Console

from dbx_test import __version__
from dbx_test.config import TestConfig
from dbx_test.runner_remote import RemoteTestRunner
from dbx_test.reporting import TestReporter
from dbx_test.artifacts import ArtifactManager
from dbx_test.bundle import get_bundle_tests_dir, is_bundle_project


console = Console()


@click.group()
@click.version_option(version=__version__)
def cli():
    """
    Databricks Notebook Test Framework
    
    A comprehensive testing framework for Databricks notebooks.
    """
    pass


@cli.command()
@click.option(
    "--env",
    default="dev",
    help="Environment (dev/test/prod)",
)
@click.option(
    "--target",
    default=None,
    help="Databricks Asset Bundle target (auto-detects bundle project and resolves workspace path)",
)
@click.option(
    "--parallel",
    is_flag=True,
    help="Enable parallel test execution",
)
@click.option(
    "--output-format",
    multiple=True,
    default=["console", "junit"],
    help="Output format(s): console, junit, json, html",
)
@click.option(
    "--output-dir",
    default=None,
    help="Output directory for reports (overrides config file, default: .dbx-test-results)",
)
@click.option(
    "--config",
    default="config/test_config.yml",
    help="Path to configuration file",
)
@click.option(
    "--profile",
    default=None,
    help="Databricks CLI profile to use (overrides config file)",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
@click.option(
    "--tests-dir",
    default="tests",
    help="Directory containing test notebooks (workspace path starting with /Workspace/ or /Repos/, or relative path for bundle projects)",
)
@click.option(
    "--workspace-tests",
    is_flag=True,
    default=False,
    help="Tests are already in Databricks workspace (auto-detected for /Workspace/ and /Repos/ paths)",
)
def run(env, target, parallel, output_format, output_dir, config, profile, verbose, tests_dir, workspace_tests):
    """Execute test notebooks remotely on Databricks.
    
    Automatically discovers test notebooks matching pytest-style patterns:
    - test_*.py (files starting with test_)
    - *_test.py (files ending with _test)
    
    For Databricks Asset Bundle projects, use --target to automatically detect
    the remote workspace path for your tests.
    
    Examples:
        # Run tests from bundle project
        dbx_test run --target dev --profile my-profile
        
        # Run tests from specific workspace directory
        dbx_test run --tests-dir /Workspace/Users/user@company.com/tests --profile my-profile
        
        # Run tests with custom subdirectory in bundle
        dbx_test run --target dev --tests-dir src/tests --profile my-profile
    """
    
    # Handle bundle target if specified
    bundle_detected = False
    if target:
        if verbose:
            console.print(f"[dim]Detecting Databricks Asset Bundle with target: {target}[/dim]")
        
        # For bundle projects, if tests_dir is the default "tests", use root instead
        bundle_tests_dir_relative = tests_dir if tests_dir != "tests" else ""
        
        # Get bundle tests directory
        bundle_tests_dir, bundle_name = get_bundle_tests_dir(
            target=target,
            tests_dir_relative=bundle_tests_dir_relative,
            profile=profile,
        )
        
        if bundle_tests_dir:
            bundle_detected = True
            tests_dir = bundle_tests_dir
            workspace_tests = True  # Bundle tests are in workspace
            
            if verbose:
                console.print(f"[green]✓ Detected bundle project: {bundle_name}[/green]")
                console.print(f"[dim]  Target: {target}[/dim]")
                console.print(f"[dim]  Tests location: {tests_dir}[/dim]")
        else:
            console.print(f"[yellow]Warning: Could not detect bundle configuration for target '{target}'[/yellow]")
            console.print("[dim]Make sure you have a databricks.yml file with the specified target.[/dim]")
            sys.exit(1)
    
    try:
        # Load configuration
        config_path = Path(config)
        if config_path.exists():
            test_config = TestConfig.from_yaml(str(config_path))
            if verbose:
                console.print(f"[dim]Loaded configuration from {config}[/dim]")
        else:
            console.print(f"[red]Error: Configuration file not found: {config}[/red]")
            console.print("[dim]Run 'dbx_test scaffold <notebook_name>' to create one.[/dim]")
            sys.exit(1)
        
        # Override profile if specified via CLI
        if profile:
            test_config.workspace.profile = profile
            if verbose:
                console.print(f"[dim]Using Databricks profile: {profile}[/dim]")
        
        # Override parallel setting if specified
        if parallel:
            test_config.execution.parallel = True
        
        # Override output directory if specified
        if output_dir:
            test_config.reporting.output_dir = output_dir
            if verbose:
                console.print(f"[dim]Using output directory: {output_dir}[/dim]")
        
        # Auto-detect workspace paths (starts with /Workspace/ or /Repos/)
        is_workspace_path = tests_dir.startswith("/Workspace/") or tests_dir.startswith("/Repos/")
        
        # All tests run from workspace - either direct workspace path or bundle path
        if workspace_tests or is_workspace_path or target:
            if verbose:
                console.print(f"[dim]Running tests from workspace: {tests_dir}[/dim]")
            
            # Run workspace tests
            runner = RemoteTestRunner(test_config, verbose=verbose)
            
            console.print(f"\n[bold]Running tests from Databricks workspace: {tests_dir}[/bold]\n")
            
            # List notebooks in the workspace directory
            try:
                notebooks = runner.db_helper.list_notebooks(tests_dir)
                
                if not notebooks:
                    console.print(f"[yellow]No test notebooks found in {tests_dir}[/yellow]")
                    console.print("[dim]Looking for notebooks matching: test_* or *_test[/dim]")
                    sys.exit(0)
                
                console.print(f"[green]Found {len(notebooks)} test notebook(s):[/green]")
                for nb in notebooks:
                    console.print(f"  • {nb}")
                
                # Run tests directly from workspace
                results = runner.run_workspace_tests(tests_dir, notebooks)
                
                # Display detailed results
                console.print("\n[bold]Test Results:[/bold]\n")
                
                # Group results by notebook
                notebook_results = {}
                total_test_count = 0
                for result in results:
                    notebook = result.get("notebook", "unknown")
                    if notebook not in notebook_results:
                        notebook_results[notebook] = []
                    notebook_results[notebook].append(result)
                    total_test_count += 1
                
                # Display results for each notebook
                for notebook, tests in notebook_results.items():
                    notebook_name = notebook.split("/")[-1]
                    console.print(f"[cyan]{notebook_name}[/cyan]: {len(tests)} test(s)")
                    
                    for test in tests:
                        test_name = test.get("test_name", "unknown")
                        status = test.get("status", "unknown")
                        duration = test.get("duration", 0)
                        
                        if status == "passed":
                            console.print(f"  ✓ {test_name} [dim]({duration:.2f}s)[/dim]")
                        elif status == "failed":
                            console.print(f"  ✗ {test_name} [red](FAILED)[/red]")
                            error_msg = test.get("error_message")
                            if error_msg:
                                console.print(f"    [red]{error_msg}[/red]")
                        else:
                            console.print(f"  ! {test_name} [yellow](ERROR)[/yellow]")
                            error_msg = test.get("error_message")
                            if error_msg:
                                console.print(f"    [yellow]{error_msg}[/yellow]")
                    
                    console.print()
                
                # Summary
                console.print("[bold]Test Execution Summary:[/bold]")
                total = sum(1 for r in results if r.get("status") != "skipped")
                passed = sum(1 for r in results if r.get("status") == "passed")
                failed = sum(1 for r in results if r.get("status") == "failed")
                
                console.print(f"Total: {total}, Passed: [green]{passed}[/green], Failed: [red]{failed}[/red]")
                
                # Generate reports
                artifact_manager = ArtifactManager(test_config.reporting.output_dir)
                reporter = TestReporter(verbose=verbose)
                
                # Convert workspace test results to standard format
                formatted_results = {
                    "summary": {
                        "total": total,
                        "passed": passed,
                        "failed": failed,
                        "errors": 0,
                    },
                    "tests": results,
                    "timestamp": datetime.now().isoformat(),
                }
                
                # Save results
                artifact_manager.save_results(formatted_results)
                
                # Generate reports
                for fmt in output_format:
                    if fmt == "console":
                        pass  # Already displayed
                    elif fmt == "junit":
                        output_path = artifact_manager.save_report("", "report.xml")
                        reporter.generate_junit_xml(formatted_results, output_path)
                        console.print(f"\n[green]✓ JUnit report saved to: {output_path}[/green]")
                    elif fmt == "json":
                        output_path = artifact_manager.save_report("", "report.json")
                        reporter.generate_json_report(formatted_results, output_path)
                        console.print(f"[green]✓ JSON report saved to: {output_path}[/green]")
                    elif fmt == "html":
                        output_path = artifact_manager.save_report("", "report.html")
                        reporter.generate_html_report(formatted_results, output_path)
                        console.print(f"[green]✓ HTML report saved to: {output_path}[/green]")
                
                if failed > 0:
                    console.print("\n[red]❌ Some tests failed[/red]")
                    sys.exit(1)
                else:
                    console.print("\n[green]🎉 All tests passed![/green]")
                    
            except Exception as e:
                console.print(f"[red]Error running tests: {e}[/red]")
                if verbose:
                    import traceback
                    console.print(traceback.format_exc())
                sys.exit(1)
        else:
            # No valid test source specified
            console.print("[red]Error: Must specify either:[/red]")
            console.print("  • [cyan]--target <name>[/cyan] for bundle projects")
            console.print("  • [cyan]--tests-dir /Workspace/...[/cyan] for workspace paths")
            console.print("  • [cyan]--tests-dir /Repos/...[/cyan] for Repos paths")
            sys.exit(1)
                
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
def discover():
    """Discover test notebooks - removed in favor of automatic discovery.
    
    All test discovery is now automatic when running tests.
    Use: dbx_test run --target <target> --profile <profile>
    """
    console.print("[yellow]The 'discover' command has been removed.[/yellow]")
    console.print("[dim]Test discovery is now automatic when running tests.[/dim]")
    console.print("[dim]Use: dbx_test run --target <target> --profile <profile>[/dim]")


@cli.command()
@click.option(
    "--run-id",
    default=None,
    help="Run ID (default: latest)",
)
@click.option(
    "--format",
    "output_format",
    default="console",
    help="Output format: console, junit, json, html",
)
@click.option(
    "--output-dir",
    default=".dbx-test-results",
    help="Test results directory",
)
def report(run_id, output_format, output_dir):
    """Generate test report from previous run."""
    
    artifact_manager = ArtifactManager(output_dir)
    results = artifact_manager.load_results(run_id)
    
    if not results:
        if run_id:
            console.print(f"[red]Error: Results not found for run ID: {run_id}[/red]")
        else:
            console.print("[red]Error: No test results found[/red]")
        sys.exit(1)
    
    reporter = TestReporter()
    
    if output_format == "console":
        reporter.print_console_report(results)
    elif output_format == "junit":
        output_path = Path(output_dir) / "report.xml"
        reporter.generate_junit_xml(results, output_path)
        console.print(f"[green]JUnit report saved to: {output_path}[/green]")
    elif output_format == "json":
        output_path = Path(output_dir) / "report.json"
        reporter.generate_json_report(results, output_path)
        console.print(f"[green]JSON report saved to: {output_path}[/green]")
    elif output_format == "html":
        output_path = Path(output_dir) / "report.html"
        reporter.generate_html_report(results, output_path)
        console.print(f"[green]HTML report saved to: {output_path}[/green]")


@cli.command()
@click.option(
    "--tests-dir",
    default="tests",
    help="Directory containing test notebooks",
)
@click.option(
    "--workspace-path",
    required=True,
    help="Workspace path prefix",
)
@click.option(
    "--config",
    default="config/test_config.yml",
    help="Path to configuration file",
)
@click.option(
    "--profile",
    default=None,
    help="Databricks CLI profile to use (overrides config file)",
)
@click.option(
    "--pattern",
    default="**/*_test.py",
    help="Pattern to match test files",
)
def upload(tests_dir, workspace_path, config, profile, pattern):
    """Upload test notebooks to Databricks workspace."""
    
    # Load configuration
    config_path = Path(config)
    if not config_path.exists():
        console.print(f"[red]Error: Configuration file not found: {config}[/red]")
        sys.exit(1)
    
    test_config = TestConfig.from_yaml(str(config_path))
    
    # Override profile if specified via CLI
    if profile:
        test_config.workspace.profile = profile
        console.print(f"[dim]Using Databricks profile: {profile}[/dim]")
    
    # Discover tests
    tests_path = Path(tests_dir)
    if not tests_path.exists():
        console.print(f"[red]Error: Tests directory not found: {tests_dir}[/red]")
        sys.exit(1)
    
    discovery = TestDiscovery(str(tests_path), pattern)
    tests = discovery.discover()
    
    if not tests:
        console.print("[yellow]No tests to upload[/yellow]")
        return
    
    console.print(f"[cyan]Uploading {len(tests)} test notebook(s)...[/cyan]")
    
    # Initialize Databricks helper
    from dbx_test.utils.databricks import DatabricksHelper
    
    auth_config = test_config.workspace.get_auth_config()
    db_helper = DatabricksHelper(**auth_config)
    
    # Upload each test
    for test_info in tests:
        test_path = Path(test_info["path"])
        remote_path = f"{workspace_path}/{test_path.stem}"
        
        try:
            db_helper.upload_notebook(
                local_path=test_path,
                workspace_path=remote_path,
                overwrite=True,
            )
            console.print(f"[green]✓[/green] Uploaded {test_path.name} → {remote_path}")
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to upload {test_path.name}: {e}")
    
    console.print("[bold green]Upload complete![/bold green]")


@cli.command()
@click.argument("notebook_name")
@click.option(
    "--output-dir",
    default="tests",
    help="Output directory for test notebook",
)
def scaffold(notebook_name, output_dir):
    """Create a new test notebook from template."""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate test file name
    if not notebook_name.endswith("_test"):
        test_name = f"{notebook_name}_test"
    else:
        test_name = notebook_name
    
    test_file = output_path / f"{test_name}.py"
    
    if test_file.exists():
        console.print(f"[yellow]Warning: Test file already exists: {test_file}[/yellow]")
    else:
        # Generate template
        template = f'''"""
Unit tests for {notebook_name} notebook.
"""

from dbx_test import NotebookTestFixture


class Test{notebook_name.replace("_", " ").title().replace(" ", "")}(NotebookTestFixture):
    """Test suite for {notebook_name} notebook."""
    
    def run_setup(self):
        """Setup code runs before tests."""
        # Initialize test data
        self.test_data = spark.createDataFrame(
            [(1, "test1"), (2, "test2")],
            ["id", "value"]
        )
        self.test_data.createOrReplaceTempView("test_data")
    
    def test_example(self):
        """Example test case."""
        result = spark.sql("SELECT * FROM test_data")
        assert result.count() == 2, "Expected 2 rows in test data"
    
    def test_schema(self):
        """Test that schema is correct."""
        result = spark.sql("SELECT * FROM test_data")
        assert "id" in result.columns, "Expected 'id' column"
        assert "value" in result.columns, "Expected 'value' column"
    
    def test_data_quality(self):
        """Test data quality checks."""
        result = spark.sql("SELECT * FROM test_data WHERE id IS NULL")
        assert result.count() == 0, "Found null values in id column"
    
    def run_cleanup(self):
        """Cleanup runs after all tests."""
        spark.sql("DROP VIEW IF EXISTS test_data")


# Additional test fixtures can be added below
'''
        
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(template)
        
        console.print(f"[green]✓[/green] Created test notebook: {test_file}")
    
    # Create config file if it doesn't exist
    config_path = Path("config/test_config.yml")
    
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate default config
        config_template = '''# Databricks Notebook Test Framework Configuration

workspace:
  # Databricks CLI profile to use (can be overridden with --profile flag)
  profile: "default"

cluster:
  # Libraries to install for remote execution
  # Uncomment and modify as needed:
  # libraries:
  #   - pypi:
  #       package: "pandas==2.0.0"
  #   - whl: "git+https://github.com/your-org/your-package.git"
  #   - whl: "/path/to/your/package.whl"
  
  # Use serverless compute (default, fastest option)
  # Or specify a cluster:
  # cluster_id: "your-cluster-id"
  
  # Or use a pre-created environment (recommended for serverless):
  # environment_key: "your-environment-name"

execution:
  timeout: 600  # Timeout in seconds (10 minutes)
  max_retries: 2
  parallel: false  # Enable parallel execution for multiple tests
  # max_parallel_jobs: 5  # Maximum number of parallel jobs (default: 5)

reporting:
  output_dir: ".dbx-test-results"
  formats:
    - "console"  # Print results to console
    - "junit"    # Generate JUnit XML reports
    # - "json"   # Generate JSON reports
    # - "html"   # Generate HTML reports
  verbose: false
'''
        
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_template)
        
        console.print(f"[green]✓[/green] Created configuration file: {config_path}")
    
    # Show next steps
    console.print("\n[cyan]Next steps:[/cyan]")
    console.print(f"  1. Edit {test_file} and add your test cases")
    if not config_path.exists():
        console.print(f"  2. Configure settings in: {config_path}")
    console.print(f"  2. Run tests: dbx_test run --target dev --profile <your-profile>")
    
    # If bundle project detected, show bundle-specific instructions
    if is_bundle_project():
        console.print("\n[dim]💡 Tip: This appears to be a Databricks Asset Bundle project.[/dim]")
        console.print(f"[dim]   You can run tests with: [cyan]dbx_test run --target dev --profile <your-profile>[/cyan][/dim]")
    else:
        console.print("\n[dim]💡 For non-bundle projects:[/dim]")
        console.print(f"[dim]   Use workspace path: [cyan]dbx_test run --tests-dir /Workspace/Users/you@company.com/tests --profile <your-profile>[/cyan][/dim]")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()

