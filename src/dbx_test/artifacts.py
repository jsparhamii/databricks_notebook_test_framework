"""
Artifact management for test results.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class ArtifactManager:
    """Manage test result artifacts."""
    
    def __init__(self, output_dir: str = ".dbx-test-results"):
        """
        Initialize artifact manager.
        
        Args:
            output_dir: Directory to store test artifacts
        """
        self.output_dir = Path(output_dir)
        self.current_run_dir = None
    
    def initialize_run(self, run_id: Optional[str] = None) -> Path:
        """
        Initialize a new test run directory.
        
        Args:
            run_id: Optional run ID, otherwise uses timestamp
        
        Returns:
            Path to the run directory
        """
        if run_id is None:
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.current_run_dir = self.output_dir / run_id
        self.current_run_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.current_run_dir / "logs").mkdir(exist_ok=True)
        (self.current_run_dir / "reports").mkdir(exist_ok=True)
        
        return self.current_run_dir
    
    def save_results(self, results: Dict[str, Any], filename: str = "results.json") -> Path:
        """
        Save test results as JSON.
        
        Args:
            results: Test results dictionary
            filename: Output filename
        
        Returns:
            Path to saved file
        """
        if self.current_run_dir is None:
            self.initialize_run()
        
        output_path = self.current_run_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        
        return output_path
    
    def save_log(self, log_content: str, filename: str = "run.log") -> Path:
        """
        Save log content.
        
        Args:
            log_content: Log text
            filename: Log filename
        
        Returns:
            Path to saved file
        """
        if self.current_run_dir is None:
            self.initialize_run()
        
        output_path = self.current_run_dir / "logs" / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(log_content)
        
        return output_path
    
    def save_report(self, report_content: str, filename: str) -> Path:
        """
        Save report content.
        
        Args:
            report_content: Report content
            filename: Report filename
        
        Returns:
            Path to saved file
        """
        if self.current_run_dir is None:
            self.initialize_run()
        
        output_path = self.current_run_dir / "reports" / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        return output_path
    
    def load_results(self, run_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Load results from a previous run.
        
        Args:
            run_id: Run ID, or None for latest
        
        Returns:
            Results dictionary or None
        """
        if run_id:
            results_path = self.output_dir / run_id / "results.json"
        else:
            # Get latest run
            results_path = self.get_latest_results_path()
        
        if results_path and results_path.exists():
            with open(results_path, "r", encoding="utf-8") as f:
                return json.load(f)
        
        return None
    
    def get_latest_results_path(self) -> Optional[Path]:
        """Get path to latest results file."""
        if not self.output_dir.exists():
            return None
        
        run_dirs = [d for d in self.output_dir.iterdir() if d.is_dir()]
        if not run_dirs:
            return None
        
        latest_dir = max(run_dirs, key=lambda d: d.stat().st_mtime)
        results_path = latest_dir / "results.json"
        
        if results_path.exists():
            return results_path
        
        return None
    
    def list_runs(self) -> List[Dict[str, Any]]:
        """List all test runs."""
        if not self.output_dir.exists():
            return []
        
        runs = []
        for run_dir in sorted(self.output_dir.iterdir(), reverse=True):
            if not run_dir.is_dir():
                continue
            
            results_path = run_dir / "results.json"
            if results_path.exists():
                with open(results_path, "r", encoding="utf-8") as f:
                    results = json.load(f)
                
                runs.append({
                    "run_id": run_dir.name,
                    "timestamp": datetime.fromtimestamp(run_dir.stat().st_mtime),
                    "total_tests": results.get("summary", {}).get("total", 0),
                    "passed": results.get("summary", {}).get("passed", 0),
                    "failed": results.get("summary", {}).get("failed", 0),
                })
        
        return runs
    
    def cleanup_old_runs(self, keep_last: int = 10) -> None:
        """
        Clean up old test runs, keeping only the most recent.
        
        Args:
            keep_last: Number of runs to keep
        """
        if not self.output_dir.exists():
            return
        
        run_dirs = sorted(
            [d for d in self.output_dir.iterdir() if d.is_dir()],
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )
        
        for run_dir in run_dirs[keep_last:]:
            shutil.rmtree(run_dir)
    
    def get_run_summary(self, run_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get summary of a test run."""
        results = self.load_results(run_id)
        if results:
            return results.get("summary")
        return None

