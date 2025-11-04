"""
Unit tests for the notebook parsing utilities.
"""

import pytest
import json
import tempfile
from pathlib import Path

from dbx_test.utils.notebook import NotebookParser


class TestNotebookParser:
    """Tests for NotebookParser class."""
    
    def test_is_notebook_py(self):
        """Test identifying Python notebooks."""
        assert NotebookParser.is_notebook(Path("test.py")) is True
        assert NotebookParser.is_notebook(Path("notebook.py")) is True
    
    def test_is_notebook_ipynb(self):
        """Test identifying Jupyter notebooks."""
        assert NotebookParser.is_notebook(Path("test.ipynb")) is True
        assert NotebookParser.is_notebook(Path("notebook.ipynb")) is True
    
    def test_is_not_notebook(self):
        """Test identifying non-notebooks."""
        assert NotebookParser.is_notebook(Path("readme.md")) is False
        assert NotebookParser.is_notebook(Path("config.yaml")) is False
        assert NotebookParser.is_notebook(Path("data.csv")) is False
    
    def test_is_test_notebook_suffix(self):
        """Test identifying test notebooks by _test suffix."""
        assert NotebookParser.is_test_notebook(Path("example_test.py")) is True
        assert NotebookParser.is_test_notebook(Path("data_processing_test.py")) is True
    
    def test_is_test_notebook_prefix(self):
        """Test identifying test notebooks by test_ prefix."""
        assert NotebookParser.is_test_notebook(Path("test_example.py")) is True
        assert NotebookParser.is_test_notebook(Path("test_data_processing.py")) is True
    
    def test_is_test_notebook_in_tests_dir(self):
        """Test identifying test notebooks in tests directory."""
        assert NotebookParser.is_test_notebook(Path("tests/example.py")) is True
        assert NotebookParser.is_test_notebook(Path("project/tests/notebook.py")) is True
    
    def test_is_not_test_notebook(self):
        """Test identifying non-test notebooks."""
        assert NotebookParser.is_test_notebook(Path("example.py")) is False
        assert NotebookParser.is_test_notebook(Path("data_processing.py")) is False


class TestExtractTestClasses:
    """Tests for extracting test class names."""
    
    def test_extract_single_class(self):
        """Test extracting a single test class."""
        content = """
from dbx_test import NotebookTestFixture

class TestExample(NotebookTestFixture):
    def test_something(self):
        assert True
"""
        classes = NotebookParser.extract_test_classes(content)
        assert len(classes) == 1
        assert "TestExample" in classes
    
    def test_extract_multiple_classes(self):
        """Test extracting multiple test classes."""
        content = """
from dbx_test import NotebookTestFixture

class TestFirst(NotebookTestFixture):
    def test_one(self):
        pass

class TestSecond(NotebookTestFixture):
    def test_two(self):
        pass
"""
        classes = NotebookParser.extract_test_classes(content)
        assert len(classes) == 2
        assert "TestFirst" in classes
        assert "TestSecond" in classes
    
    def test_extract_no_classes(self):
        """Test when no test classes are present."""
        content = """
def some_function():
    pass

class NotATestClass:
    pass
"""
        classes = NotebookParser.extract_test_classes(content)
        assert len(classes) == 0
    
    def test_extract_class_with_imports(self):
        """Test extracting class with various import styles."""
        content = """
from dbx_test import NotebookTestFixture, run_notebook_tests

class TestWithImports(NotebookTestFixture):
    def test_one(self):
        pass
"""
        classes = NotebookParser.extract_test_classes(content)
        assert "TestWithImports" in classes


class TestExtractTestMethods:
    """Tests for extracting test method names."""
    
    def test_extract_test_methods(self):
        """Test extracting test methods from a class."""
        content = """
class TestExample(NotebookTestFixture):
    def test_one(self):
        assert True
    
    def test_two(self):
        assert True
    
    def not_a_test(self):
        pass
"""
        methods = NotebookParser.extract_test_methods(content, "TestExample")
        assert len(methods) == 2
        assert "test_one" in methods
        assert "test_two" in methods
        assert "not_a_test" not in methods
    
    def test_extract_assertion_methods(self):
        """Test extracting assertion methods."""
        content = """
class TestExample(NotebookTestFixture):
    def test_one(self):
        pass
    
    def assertion_custom(self):
        pass
"""
        methods = NotebookParser.extract_test_methods(content, "TestExample")
        assert len(methods) == 2
        assert "test_one" in methods
        assert "assertion_custom" in methods
    
    def test_extract_no_methods(self):
        """Test when class has no test methods."""
        content = """
class TestExample(NotebookTestFixture):
    def run_setup(self):
        pass
    
    def run_cleanup(self):
        pass
"""
        methods = NotebookParser.extract_test_methods(content, "TestExample")
        assert len(methods) == 0
    
    def test_extract_methods_nonexistent_class(self):
        """Test extracting methods from nonexistent class."""
        content = """
class TestExample(NotebookTestFixture):
    def test_one(self):
        pass
"""
        methods = NotebookParser.extract_test_methods(content, "NonexistentClass")
        assert len(methods) == 0


class TestExtractParameters:
    """Tests for extracting notebook parameters."""
    
    def test_extract_single_parameter(self):
        """Test extracting a single parameter."""
        content = """
env = dbutils.widgets.get("environment")
"""
        params = NotebookParser.extract_parameters(content)
        assert len(params) == 1
        assert "environment" in params
    
    def test_extract_multiple_parameters(self):
        """Test extracting multiple parameters."""
        content = """
env = dbutils.widgets.get("environment")
region = dbutils.widgets.get("region")
debug = dbutils.widgets.get('debug_mode')
"""
        params = NotebookParser.extract_parameters(content)
        assert len(params) == 3
        assert "environment" in params
        assert "region" in params
        assert "debug_mode" in params
    
    def test_extract_no_parameters(self):
        """Test when no parameters are present."""
        content = """
x = 10
y = 20
result = x + y
"""
        params = NotebookParser.extract_parameters(content)
        assert len(params) == 0
    
    def test_extract_duplicate_parameters(self):
        """Test that duplicate parameters are deduplicated."""
        content = """
env = dbutils.widgets.get("environment")
env2 = dbutils.widgets.get("environment")
"""
        params = NotebookParser.extract_parameters(content)
        assert len(params) == 1
        assert "environment" in params


class TestParseFiles:
    """Tests for parsing different file types."""
    
    def test_parse_py_file(self):
        """Test parsing a Python file."""
        content = """
# This is a test notebook
from dbx_test import NotebookTestFixture

class TestExample(NotebookTestFixture):
    def test_one(self):
        assert True
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            file_path = Path(f.name)
        
        try:
            parsed_content = NotebookParser.parse_py(file_path)
            assert "TestExample" in parsed_content
            assert "test_one" in parsed_content
        finally:
            file_path.unlink()
    
    def test_parse_ipynb_file(self):
        """Test parsing a Jupyter notebook file."""
        notebook_content = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "from dbx_test import NotebookTestFixture\n"
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "class TestExample(NotebookTestFixture):\n",
                        "    def test_one(self):\n",
                        "        assert True\n"
                    ]
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ipynb", delete=False) as f:
            json.dump(notebook_content, f)
            file_path = Path(f.name)
        
        try:
            parsed_data = NotebookParser.parse_ipynb(file_path)
            assert len(parsed_data["cells"]) == 2
            assert parsed_data["nbformat"] == 4
        finally:
            file_path.unlink()


class TestGetNotebookInfo:
    """Tests for getting comprehensive notebook information."""
    
    def test_get_notebook_info_py(self):
        """Test getting info from a Python notebook."""
        content = """
from dbx_test import NotebookTestFixture

env = dbutils.widgets.get("environment")

class TestExample(NotebookTestFixture):
    def test_one(self):
        assert True
    
    def test_two(self):
        assert True
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix="_test.py", delete=False) as f:
            f.write(content)
            file_path = Path(f.name)
        
        try:
            info = NotebookParser.get_notebook_info(file_path)
            
            assert info["name"] == file_path.stem
            assert info["type"] == ".py"
            assert info["is_test"] is True
            assert "TestExample" in info["test_classes"]
            assert info["test_count"] == 2
            assert "environment" in info["parameters"]
            
            # Check test methods
            test_methods = [m for c, m in info["test_methods"]]
            assert "test_one" in test_methods
            assert "test_two" in test_methods
        finally:
            file_path.unlink()
    
    def test_get_notebook_info_ipynb(self):
        """Test getting info from a Jupyter notebook."""
        notebook_content = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "from dbx_test import NotebookTestFixture\n",
                        "\n",
                        "class TestJupyter(NotebookTestFixture):\n",
                        "    def test_notebook(self):\n",
                        "        assert True\n"
                    ]
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix="_test.ipynb", delete=False) as f:
            json.dump(notebook_content, f)
            file_path = Path(f.name)
        
        try:
            info = NotebookParser.get_notebook_info(file_path)
            
            assert info["type"] == ".ipynb"
            assert info["is_test"] is True
            assert "TestJupyter" in info["test_classes"]
            assert info["test_count"] == 1
        finally:
            file_path.unlink()
    
    def test_get_notebook_info_nonexistent_file(self):
        """Test getting info from nonexistent file."""
        with pytest.raises(FileNotFoundError):
            NotebookParser.get_notebook_info(Path("/nonexistent/file.py"))


class TestConvertNotebook:
    """Tests for notebook conversion."""
    
    def test_convert_ipynb_to_py(self):
        """Test converting Jupyter notebook to Python file."""
        notebook_content = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "x = 10\n",
                        "y = 20\n"
                    ]
                },
                {
                    "cell_type": "markdown",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "# This is markdown\n"
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "result = x + y\n"
                    ]
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ipynb", delete=False) as f:
            json.dump(notebook_content, f)
            ipynb_path = Path(f.name)
        
        try:
            py_path = NotebookParser.convert_ipynb_to_py(ipynb_path)
            
            assert py_path.exists()
            assert py_path.suffix == ".py"
            
            content = py_path.read_text()
            assert "x = 10" in content
            assert "result = x + y" in content
            # Markdown cell should not be in output
            assert "This is markdown" not in content
            
            # Cleanup
            py_path.unlink()
        finally:
            ipynb_path.unlink()
    
    def test_convert_ipynb_to_py_custom_output(self):
        """Test converting with custom output path."""
        notebook_content = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": ["print('hello')\n"]
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            ipynb_path = Path(tmpdir) / "notebook.ipynb"
            with open(ipynb_path, "w") as f:
                json.dump(notebook_content, f)
            
            custom_output = Path(tmpdir) / "custom_output.py"
            result_path = NotebookParser.convert_ipynb_to_py(ipynb_path, custom_output)
            
            assert result_path == custom_output
            assert custom_output.exists()
            assert "print('hello')" in custom_output.read_text()

