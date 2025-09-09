#!/bin/bash

# Deploy script for Herbert application
# Run this on the server after rsync

set -e  # Exit on any error

echo "Starting Herbert deployment..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Working directory: $(pwd)"

# Remove any existing venv to start fresh
echo "Removing existing virtual environment..."
rm -rf venv

# Create new virtual environment
echo "Creating new virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Verify we're in the right venv
echo "Python location: $(which python)"
echo "Python version: $(python --version)"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install project dependencies
echo "Installing project dependencies..."
pip install -e .

# Verify psycopg2-binary is installed
echo "Checking psycopg2 installation..."
python -c "import psycopg2; print('psycopg2 version:', psycopg2.__version__)"

# Test the build_search script imports
echo "Testing build_search script imports..."
python -c "
import sys
sys.path.insert(0, 'src')
try:
    from herbert.build_search import main
    print('✓ build_search imports successfully')
except ImportError as e:
    print('✗ Import failed:', e)
    exit(1)
"

# Cleanup unnecessary files
echo "Cleaning up temporary and cache files..."

# Remove Python bytecode files
find . -name "*.pyc" -delete
echo "  ✓ Removed .pyc files"

# Remove __pycache__ directories
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
echo "  ✓ Removed __pycache__ directories"

# Remove editor backup files
find . -name "*~" -delete 2>/dev/null || true
find . -name "*.bak" -delete 2>/dev/null || true
find . -name ".*.swp" -delete 2>/dev/null || true
echo "  ✓ Removed editor backup files"

# Remove any .DS_Store files (macOS)
find . -name ".DS_Store" -delete 2>/dev/null || true
echo "  ✓ Removed .DS_Store files"

echo "✓ Deployment complete!"
echo "To run the build script:"
echo "  source venv/bin/activate"
echo "  python src/herbert/build_search.py"
