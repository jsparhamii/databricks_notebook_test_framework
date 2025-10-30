"""
Notebook parsing and manipulation utilities.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import nbformat


class NotebookParser:
    """Parse and analyze notebook files."""
    
    @staticmethod
    def is_notebook(file_path: Path) -> bool:
        """Check if file is a notebook."""
        return file_path.suffix in [".ipynb", ".py"]
    
    @staticmethod
    def is_test_notebook(file_path: Path) -> bool:
        """Check if notebook is a test notebook."""
        name = file_path.stem
        return (
            name.endswith("_test")
            or name.startswith("test_")
            or "tests" in file_path.parts
        )
    
    @staticmethod
    def parse_ipynb(file_path: Path) -> Dict[str, Any]:
        """Parse .ipynb file."""
        with open(file_path, "r", encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)
        
        return {
            "cells": nb.cells,
            "metadata": nb.metadata,
            "nbformat": nb.nbformat,
            "nbformat_minor": nb.nbformat_minor,
        }
    
    @staticmethod
    def parse_py(file_path: Path) -> str:
        """Parse .py file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    
    @staticmethod
    def extract_test_classes(content: str) -> List[str]:
        """Extract test class names from notebook content."""
        # Look for classes that inherit from NotebookTestFixture
        pattern = r"class\s+(\w+)\s*\([^)]*NotebookTestFixture[^)]*\)"
        matches = re.findall(pattern, content)
        return matches
    
    @staticmethod
    def extract_test_methods(content: str, class_name: str) -> List[str]:
        """Extract test method names from a test class."""
        # Find the class definition
        class_pattern = rf"class\s+{class_name}\s*\([^)]*\):\s*(.*?)(?=\nclass\s|\Z)"
        class_match = re.search(class_pattern, content, re.DOTALL)
        
        if not class_match:
            return []
        
        class_body = class_match.group(1)
        
        # Find test methods (methods starting with "test_" or "assertion_")
        method_pattern = r"def\s+((?:test_|assertion_)\w+)\s*\("
        methods = re.findall(method_pattern, class_body)
        
        return methods
    
    @staticmethod
    def extract_parameters(content: str) -> List[str]:
        """Extract widget/parameter names from notebook."""
        # Look for dbutils.widgets.get calls
        widget_pattern = r'dbutils\.widgets\.get\(["\']([^"\']+)["\']\)'
        params = re.findall(widget_pattern, content)
        return list(set(params))
    
    @staticmethod
    def convert_ipynb_to_py(ipynb_path: Path, output_path: Optional[Path] = None) -> Path:
        """Convert .ipynb to .py file."""
        nb_data = NotebookParser.parse_ipynb(ipynb_path)
        
        # Extract code cells
        code_lines = []
        for cell in nb_data["cells"]:
            if cell.cell_type == "code":
                code_lines.append(cell.source)
                code_lines.append("\n")
        
        py_content = "\n".join(code_lines)
        
        # Determine output path
        if output_path is None:
            output_path = ipynb_path.with_suffix(".py")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(py_content)
        
        return output_path
    
    @staticmethod
    def get_notebook_info(file_path: Path) -> Dict[str, Any]:
        """Get comprehensive info about a notebook."""
        if not file_path.exists():
            raise FileNotFoundError(f"Notebook not found: {file_path}")
        
        # Read content
        if file_path.suffix == ".ipynb":
            nb_data = NotebookParser.parse_ipynb(file_path)
            content = "\n".join(
                cell.source for cell in nb_data["cells"] if cell.cell_type == "code"
            )
        else:
            content = NotebookParser.parse_py(file_path)
        
        # Extract info
        test_classes = NotebookParser.extract_test_classes(content)
        parameters = NotebookParser.extract_parameters(content)
        
        # Extract all test methods
        all_test_methods = []
        for class_name in test_classes:
            methods = NotebookParser.extract_test_methods(content, class_name)
            all_test_methods.extend([(class_name, method) for method in methods])
        
        return {
            "path": str(file_path),
            "name": file_path.stem,
            "type": file_path.suffix,
            "is_test": NotebookParser.is_test_notebook(file_path),
            "test_classes": test_classes,
            "test_methods": all_test_methods,
            "parameters": parameters,
            "test_count": len(all_test_methods),
        }

