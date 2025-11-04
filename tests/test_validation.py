"""
Unit tests for the validation utilities.
"""

import pytest
import tempfile
from pathlib import Path

from dbx_test.utils.validation import (
    validate_file_exists,
    validate_directory_exists,
    validate_pattern,
    validate_environment,
    validate_databricks_host,
    validate_cluster_size,
)


class TestValidateFileExists:
    """Tests for validate_file_exists."""
    
    def test_valid_file(self):
        """Test with a valid file."""
        with tempfile.NamedTemporaryFile() as f:
            file_path = Path(f.name)
            # Should not raise
            validate_file_exists(file_path)
    
    def test_nonexistent_file(self):
        """Test with a nonexistent file."""
        file_path = Path("/nonexistent/file.txt")
        with pytest.raises(FileNotFoundError, match="File not found"):
            validate_file_exists(file_path)


class TestValidateDirectoryExists:
    """Tests for validate_directory_exists."""
    
    def test_valid_directory(self):
        """Test with a valid directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            # Should not raise
            validate_directory_exists(dir_path)
    
    def test_nonexistent_directory(self):
        """Test with a nonexistent directory."""
        dir_path = Path("/nonexistent/directory")
        with pytest.raises(FileNotFoundError, match="Directory not found"):
            validate_directory_exists(dir_path)
    
    def test_file_instead_of_directory(self):
        """Test with a file instead of directory."""
        with tempfile.NamedTemporaryFile() as f:
            file_path = Path(f.name)
            with pytest.raises(ValueError, match="Path is not a directory"):
                validate_directory_exists(file_path)


class TestValidatePattern:
    """Tests for validate_pattern."""
    
    def test_valid_pattern(self):
        """Test with a valid pattern."""
        # Should not raise
        validate_pattern("**/*.py")
        validate_pattern("test_*.py")
        validate_pattern("**/test_*")
    
    def test_empty_pattern(self):
        """Test with an empty pattern."""
        with pytest.raises(ValueError, match="Pattern cannot be empty"):
            validate_pattern("")


class TestValidateEnvironment:
    """Tests for validate_environment."""
    
    def test_valid_environment(self):
        """Test with a valid environment."""
        valid_envs = ["dev", "staging", "prod"]
        # Should not raise
        validate_environment("dev", valid_envs)
        validate_environment("staging", valid_envs)
        validate_environment(None, valid_envs)  # None is allowed
    
    def test_invalid_environment(self):
        """Test with an invalid environment."""
        valid_envs = ["dev", "staging", "prod"]
        with pytest.raises(ValueError, match="Invalid environment"):
            validate_environment("unknown", valid_envs)


class TestValidateDatabricksHost:
    """Tests for validate_databricks_host."""
    
    def test_valid_https_host(self):
        """Test with a valid HTTPS host."""
        # Should not raise
        validate_databricks_host("https://adb-123.azuredatabricks.net")
        validate_databricks_host("https://dbc-abc123.cloud.databricks.com")
    
    def test_valid_http_host(self):
        """Test with a valid HTTP host (for testing)."""
        # Should not raise
        validate_databricks_host("http://localhost:8080")
    
    def test_empty_host(self):
        """Test with an empty host."""
        with pytest.raises(ValueError, match="Databricks host cannot be empty"):
            validate_databricks_host("")
    
    def test_invalid_host_no_protocol(self):
        """Test with a host without protocol."""
        with pytest.raises(ValueError, match="Must start with https:// or http://"):
            validate_databricks_host("adb-123.azuredatabricks.net")
    
    def test_invalid_host_wrong_protocol(self):
        """Test with a host with wrong protocol."""
        with pytest.raises(ValueError, match="Must start with https:// or http://"):
            validate_databricks_host("ftp://adb-123.azuredatabricks.net")


class TestValidateClusterSize:
    """Tests for validate_cluster_size."""
    
    def test_valid_sizes(self):
        """Test with valid cluster sizes."""
        # Should not raise
        validate_cluster_size("S")
        validate_cluster_size("M")
        validate_cluster_size("L")
        validate_cluster_size("XL")
    
    def test_invalid_size(self):
        """Test with an invalid cluster size."""
        with pytest.raises(ValueError, match="Invalid cluster size"):
            validate_cluster_size("XXL")
        
        with pytest.raises(ValueError, match="Invalid cluster size"):
            validate_cluster_size("small")
        
        with pytest.raises(ValueError, match="Invalid cluster size"):
            validate_cluster_size("m")  # lowercase


class TestValidationIntegration:
    """Integration tests for validation utilities."""
    
    def test_validate_databricks_config(self):
        """Test validating a complete Databricks configuration."""
        # Valid configuration
        host = "https://adb-123.azuredatabricks.net"
        cluster_size = "M"
        pattern = "**/*_test.py"
        
        # Should not raise
        validate_databricks_host(host)
        validate_cluster_size(cluster_size)
        validate_pattern(pattern)
    
    def test_validate_paths_config(self):
        """Test validating paths configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tests_dir = Path(tmpdir)
            
            # Should not raise
            validate_directory_exists(tests_dir)
            validate_pattern("**/*.py")
    
    def test_chain_validations(self):
        """Test chaining multiple validations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            
            # Create a test file
            test_file = dir_path / "test_example.py"
            test_file.write_text("# test content")
            
            # Chain validations
            validate_directory_exists(dir_path)
            validate_file_exists(test_file)
            validate_pattern("test_*.py")
            validate_cluster_size("M")

