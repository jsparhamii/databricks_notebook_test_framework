# Contributing to Databricks Notebook Test Framework

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/yourusername/dbx_test.git
cd dbx_test
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install with development dependencies
pip install -e ".[dev]"
pip install nutter
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

## Development Guidelines

### Code Style

We follow PEP 8 with some modifications:

- Line length: 100 characters
- Use Black for formatting
- Use type hints where possible
- Write docstrings for all public functions/classes

```bash
# Format code
black src/

# Check style
flake8 src/

# Type checking
mypy src/
```

### Project Structure

```
src/dbx_test/
├── __init__.py           # Package initialization
├── cli.py                # CLI implementation
├── config.py             # Configuration management
├── discovery.py          # Test discovery
├── runner_local.py       # Local execution
├── runner_remote.py      # Remote execution
├── reporting.py          # Report generation
├── artifacts.py          # Artifact management
└── utils/                # Utility modules
    ├── notebook.py       # Notebook parsing
    ├── databricks.py     # Databricks API
    └── validation.py     # Validation utilities
```

### Testing Your Changes

```bash
# Run local tests
dbx_test run --local --tests-dir tests

# Run specific test
dbx_test run --local --pattern "*example*"
```

### Documentation

- Update relevant documentation in `docs/`
- Add docstrings to new functions/classes
- Update README.md if adding new features
- Include examples for new functionality

## Types of Contributions

### Bug Fixes

1. Check if the bug is already reported in Issues
2. Create a new issue if needed
3. Reference the issue in your PR
4. Include steps to reproduce
5. Add tests that demonstrate the fix

### New Features

1. Open an issue to discuss the feature first
2. Wait for approval from maintainers
3. Implement the feature with tests
4. Update documentation
5. Submit PR with detailed description

### Documentation

- Fix typos, clarify explanations
- Add examples
- Improve guides
- Update API documentation

### Examples

- Add new example notebooks
- Demonstrate best practices
- Show advanced usage patterns

## Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Examples:**

```
feat(cli): add --parallel flag for concurrent execution

Adds support for parallel test execution to speed up CI/CD pipelines.
Tests can now run concurrently on Databricks.

Closes #42
```

```
fix(runner): handle timeout errors gracefully

Previously, timeout errors would crash the runner. Now they're
caught and reported properly in the test results.

Fixes #37
```

## Pull Request Process

### 1. Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Commit messages follow guidelines
- [ ] No merge conflicts with main branch

### 2. PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Code refactoring

## Testing
How was this tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Backwards compatible

## Related Issues
Closes #XX
```

### 3. Review Process

1. Automated checks must pass
2. At least one maintainer review required
3. Address review comments
4. Squash commits if requested
5. Maintainer will merge when approved

## Development Workflow

### Adding a New Feature

1. **Design Phase**
   ```bash
   # Create feature branch
   git checkout -b feature/new-feature
   ```

2. **Implementation**
   ```python
   # Add your code with proper structure
   # src/dbx_test/new_feature.py
   
   class NewFeature:
       """Clear docstring explaining the feature."""
       
       def __init__(self, config: Config):
           self.config = config
       
       def process(self) -> Result:
           """Process with clear return type."""
           pass
   ```

3. **Testing**
   ```python
   # tests/test_new_feature.py
   
   def test_new_feature():
       """Test the new feature."""
       feature = NewFeature(config)
       result = feature.process()
       assert result.success
   ```

4. **Documentation**
   ```markdown
   # docs/new_feature.md
   
   # New Feature Guide
   
   ## Overview
   Brief description
   
   ## Usage
   Code examples
   
   ## Configuration
   Configuration options
   ```

5. **Submit**
   ```bash
   git add .
   git commit -m "feat: add new feature for X"
   git push origin feature/new-feature
   # Create PR on GitHub
   ```

### Fixing a Bug

1. **Reproduce**
   - Write a test that demonstrates the bug
   - Verify the test fails

2. **Fix**
   - Implement the fix
   - Verify the test now passes

3. **Submit**
   ```bash
   git commit -m "fix: resolve issue with X"
   # Include issue number in commit message
   ```

## Code Review Guidelines

### For Reviewers

- Be constructive and respectful
- Focus on code quality and maintainability
- Suggest improvements, not just problems
- Approve when ready, request changes if needed

### For Contributors

- Respond to all comments
- Ask for clarification if needed
- Don't take criticism personally
- Update PR based on feedback

## Release Process

Maintainers will handle releases:

1. Version bump in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release tag
4. Publish to PyPI
5. Create GitHub release

## Getting Help

- **Questions**: Open a discussion on GitHub
- **Bugs**: Open an issue with detailed reproduction steps
- **Features**: Open an issue to discuss before implementing
- **Chat**: Join our community channel (if available)

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers
- Focus on what's best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Personal or political attacks
- Publishing others' private information

### Enforcement

Violations may result in:
1. Warning
2. Temporary ban
3. Permanent ban

Report issues to project maintainers.

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to reach out:
- Open a discussion on GitHub
- Contact maintainers
- Check existing issues and PRs

Thank you for contributing! 🎉

