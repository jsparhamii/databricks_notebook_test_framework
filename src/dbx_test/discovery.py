"""
Test discovery engine for finding and analyzing test notebooks.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import fnmatch
from rich.console import Console
from rich.table import Table

from dbx_test.utils.notebook import NotebookParser
from dbx_test.utils.validation import validate_directory_exists


class TestDiscovery:
    """Discover test notebooks in a directory tree."""
    
    def __init__(self, root_dir: str, pattern: str = "**/*_test.py"):
        """
        Initialize test discovery.
        
        Args:
            root_dir: Root directory to search for tests
            pattern: Glob pattern to match test files
        """
        self.root_dir = Path(root_dir)
        self.pattern = pattern
        self.console = Console()
    
    def discover(self) -> List[Dict[str, Any]]:
        """
        Discover all test notebooks matching the pattern.
        
        Returns:
            List of test notebook information dictionaries
        """
        if not self.root_dir.exists():
            self.console.print(f"[yellow]Warning: Directory {self.root_dir} does not exist[/yellow]")
            return []
        
        test_files = []
        
        # Support multiple patterns
        patterns = self.pattern.split(",") if "," in self.pattern else [self.pattern]
        
        for pattern in patterns:
            pattern = pattern.strip()
            
            # Find matching files
            if "**" in pattern:
                # Recursive search
                for file_path in self.root_dir.rglob(pattern.replace("**", "*").lstrip("*/")):
                    if self._is_valid_test_file(file_path):
                        test_files.append(file_path)
            else:
                # Non-recursive search
                for file_path in self.root_dir.glob(pattern):
                    if self._is_valid_test_file(file_path):
                        test_files.append(file_path)
        
        # Remove duplicates
        test_files = list(set(test_files))
        
        # Parse each test file
        test_info = []
        for file_path in sorted(test_files):
            try:
                info = NotebookParser.get_notebook_info(file_path)
                if info["is_test"] and info["test_classes"]:
                    test_info.append(info)
            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not parse {file_path}: {e}[/yellow]")
        
        return test_info
    
    def _is_valid_test_file(self, file_path: Path) -> bool:
        """Check if file is a valid test file."""
        if not file_path.is_file():
            return False
        
        if file_path.suffix not in [".py", ".ipynb"]:
            return False
        
        # Skip hidden files and __pycache__
        if file_path.name.startswith(".") or "__pycache__" in file_path.parts:
            return False
        
        return True
    
    def filter_tests(
        self,
        tests: List[Dict[str, Any]],
        name_filter: Optional[str] = None,
        tag_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filter tests by name or tags.
        
        Args:
            tests: List of test info dictionaries
            name_filter: Wildcard pattern to filter by test name
            tag_filter: Tag to filter by (not implemented yet)
        
        Returns:
            Filtered list of tests
        """
        filtered = tests
        
        if name_filter:
            filtered = [
                test for test in filtered
                if fnmatch.fnmatch(test["name"], name_filter)
            ]
        
        if tag_filter:
            # TODO: Implement tag filtering when tags are added to notebooks
            pass
        
        return filtered
    
    def print_summary(self, tests: List[Dict[str, Any]]) -> None:
        """Print a summary table of discovered tests."""
        if not tests:
            self.console.print("[yellow]No tests discovered[/yellow]")
            return
        
        table = Table(title="Discovered Tests")
        table.add_column("Notebook", style="cyan", no_wrap=True)
        table.add_column("Classes", style="magenta")
        table.add_column("Tests", justify="right", style="green")
        table.add_column("Parameters", style="blue")
        
        total_tests = 0
        for test in tests:
            classes = ", ".join(test["test_classes"])
            test_count = test["test_count"]
            params = ", ".join(test["parameters"]) if test["parameters"] else "-"
            
            table.add_row(
                test["name"],
                classes,
                str(test_count),
                params,
            )
            total_tests += test_count
        
        self.console.print(table)
        self.console.print(f"\n[bold green]Total: {len(tests)} notebooks, {total_tests} tests[/bold green]")
    
    def get_test_by_name(self, tests: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
        """Get a specific test by name."""
        for test in tests:
            if test["name"] == name:
                return test
        return None

