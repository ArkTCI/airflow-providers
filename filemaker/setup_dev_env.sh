#!/bin/bash
# Setup script for FileMaker provider development environment

set -e  # Exit immediately if a command exits with a non-zero status

echo "Setting up development environment for FileMaker provider..."

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "WARNING: Not running in a virtual environment!"
    echo "It's recommended to create and activate a virtual environment first."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. Please create a virtual environment and try again."
        exit 1
    fi
fi

# Install development dependencies
echo "Installing development dependencies..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install in development mode
echo "Installing package in development mode..."
pip install -e .

# Setup pre-commit hooks if available
if command -v pre-commit &> /dev/null; then
    echo "Setting up pre-commit hooks..."
    pre-commit install
else
    echo "pre-commit not available, skipping hook installation."
fi

# Run a simple test to verify installation
echo "Verifying installation..."
python -c "from filemaker import get_provider_info; print('Provider info available:', get_provider_info()['name'])"

echo "Development environment setup complete!"
echo "You can now run tests with: pytest"
echo "Or run the provider tests with: python test_provider.py" 