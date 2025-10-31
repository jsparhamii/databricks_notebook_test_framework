#!/bin/bash
# Quick publish script for PyPI

set -e  # Exit on error

echo "🚀 Publishing databricks-notebook-test-framework to PyPI"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Run this script from the project root."
    exit 1
fi

# Check if twine and build are installed
if ! command -v twine &> /dev/null; then
    echo "📦 Installing twine..."
    pip install --upgrade twine
fi

if ! python -c "import build" &> /dev/null; then
    echo "📦 Installing build..."
    pip install --upgrade build
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ src/*.egg-info

# Get current version
VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
echo "📌 Current version: $VERSION"
echo ""

# Ask for confirmation
read -p "Publish version $VERSION to PyPI? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Publish cancelled"
    exit 1
fi

# Build the package
echo "🔨 Building package..."
python -m build
echo ""

# List built files
echo "📦 Built packages:"
ls -lh dist/
echo ""

# Ask which repository to upload to
echo "Select repository:"
echo "1) TestPyPI (test.pypi.org) - Recommended for testing"
echo "2) PyPI (pypi.org) - Production"
read -p "Enter choice (1 or 2): " -n 1 -r REPO_CHOICE
echo ""

if [ "$REPO_CHOICE" == "1" ]; then
    REPO="testpypi"
    echo "🧪 Uploading to TestPyPI..."
    python -m twine upload --repository testpypi dist/*
    echo ""
    echo "✅ Published to TestPyPI!"
    echo ""
    echo "Test installation with:"
    echo "pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple databricks-notebook-test-framework==$VERSION"
elif [ "$REPO_CHOICE" == "2" ]; then
    REPO="pypi"
    echo "🚀 Uploading to PyPI..."
    python -m twine upload dist/*
    echo ""
    echo "✅ Published to PyPI!"
    echo ""
    echo "Install with:"
    echo "pip install databricks-notebook-test-framework==$VERSION"
    echo ""
    echo "View at:"
    echo "https://pypi.org/project/databricks-notebook-test-framework/$VERSION/"
    echo ""
    echo "Don't forget to:"
    echo "1. Create a git tag: git tag -a v$VERSION -m 'Release version $VERSION'"
    echo "2. Push the tag: git push origin v$VERSION"
    echo "3. Create a GitHub release"
else
    echo "❌ Invalid choice"
    exit 1
fi

