#!/bin/bash

# Stop on first error
set -e

echo "Setting up test environment..."

# Ensure we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Please activate your virtual environment first"
    exit 1
fi

# Install test dependencies if needed
if ! pip freeze | grep -q "pytest=="; then
    echo "Installing test dependencies..."
    pip install -r requirements.test.txt
fi

# Create test database if it doesn't exist
export FLASK_APP=app.py
export FLASK_ENV=testing
export TESTING=true

# Clean up previous test artifacts
echo "Cleaning up previous test artifacts..."
rm -rf .coverage htmlcov .pytest_cache

# Run tests with coverage
echo "Running tests..."
python -m pytest "$@"

# Show coverage report in terminal
echo -e "\nCoverage Report:"
coverage report

# Generate HTML coverage report
echo -e "\nGenerating HTML coverage report..."
coverage html

echo -e "\nTests completed. View detailed coverage report in htmlcov/index.html" 