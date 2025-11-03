# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Test coverage reporting
- Delta Lake version diffing helpers
- SLA threshold checks (fail if runtime > X seconds)
- Automatic cluster cost tagging
- Interactive test runner (TUI)
- Test data generators
- Mock framework for external dependencies

## [0.1.0] - 2025-01-XX

### Added
- Initial release of Databricks Notebook Test Framework
- Core test discovery engine with glob pattern matching
- Local test execution using Nutter
- Remote test execution on Databricks clusters
- Multiple cluster size configurations (S, M, L, XL)
- JUnit XML report generation for CI/CD integration
- Rich console output with color-coded results
- JSON report generation
- HTML report generation
- CLI tool with following commands:
  - `dbx_test run` - Execute tests locally or remotely
  - `dbx_test discover` - Discover test notebooks
  - `dbx_test report` - Generate reports from previous runs
  - `dbx_test upload` - Upload notebooks to Databricks workspace
  - `dbx_test scaffold` - Generate test notebook templates
- YAML-based configuration system
- Support for parameterized testing
- Parallel test execution (remote)
- Artifact management and result storage
- Test timeout and retry configuration
- Databricks SDK integration for workspace operations
- Support for both .py and .ipynb test notebooks
- Comprehensive example test notebooks
- GitHub Actions workflow examples
- Azure DevOps pipeline examples
- Complete documentation suite:
  - Installation guide
  - Configuration guide
  - Writing tests guide
  - CI/CD integration guide
  - Quick start guide
  - Contributing guidelines

### Features in Detail

#### Test Discovery
- Recursive directory scanning
- Multiple glob pattern support
- Automatic Nutter class detection
- Test parameter extraction
- Test method enumeration

#### Local Execution
- Nutter CLI integration
- Subprocess-based execution
- Timeout handling
- Output capturing and parsing
- Error handling and reporting

#### Remote Execution
- Databricks Jobs API integration
- Cluster creation and management
- Notebook upload automation
- Job status polling
- Result retrieval
- Concurrent job execution
- Resource cleanup

#### Reporting
- JUnit XML format (CI/CD standard)
- JSON format (machine-readable)
- HTML format (human-readable)
- Rich console output with tables
- Test duration tracking
- Success/failure/skip statistics
- Error message capture
- Stack trace reporting

#### Configuration
- YAML configuration files
- Environment variable support
- Multiple environment configs
- Cluster size presets
- Spark configuration options
- Custom tags support
- Workspace path configuration
- Test pattern configuration
- Timeout and retry settings
- Parallel execution settings

#### CLI Features
- Click-based command interface
- Rich help messages
- Flag-based options
- Environment selection
- Pattern filtering
- Output format selection
- Verbose mode
- Configuration file override

### Documentation
- Comprehensive README with quick start
- Detailed installation instructions
- Configuration reference
- Test writing guide with examples
- CI/CD integration examples
- Contributing guidelines
- Quick start guide
- API documentation via docstrings

### Examples
- Basic test notebook (`example_test.py`)
- Integration test notebook (`integration_test.py`)
- GitHub Actions workflow
- Azure DevOps pipeline
- Configuration templates

### Dependencies
- Python 3.10+
- databricks-sdk >= 0.20.0
- nutter >= 0.1.18
- pyyaml >= 6.0
- junit-xml >= 1.9
- rich >= 13.0.0
- click >= 8.0.0
- nbformat >= 5.0.0
- requests >= 2.31.0

## [0.0.1] - 2025-01-XX

### Added
- Project initialization
- Basic project structure
- Package configuration (pyproject.toml)
- MIT License
- README skeleton
- .gitignore configuration

---

## Version History

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- MAJOR version for incompatible API changes
- MINOR version for new functionality (backwards compatible)
- PATCH version for backwards compatible bug fixes

### Release Schedule

- Major releases: As needed for breaking changes
- Minor releases: Monthly (feature additions)
- Patch releases: As needed (bug fixes)

### Support Policy

- Latest major version: Full support
- Previous major version: Security fixes only
- Older versions: No support

### Upgrade Paths

#### From 0.0.x to 0.1.0
This is the first production-ready release. No upgrade path needed.

### Breaking Changes

None yet (first release).

### Deprecation Notices

None yet.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on:
- How to contribute
- Code style guidelines
- Pull request process
- Release process

## Links

- [Repository](https://github.com/yourusername/dbx_test)
- [Documentation](docs/)
- [Issue Tracker](https://github.com/yourusername/dbx_test/issues)
- [Releases](https://github.com/yourusername/dbx_test/releases)

