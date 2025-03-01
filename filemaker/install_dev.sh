#!/bin/bash
# Install the FileMaker Cloud provider in development mode

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

echo "Installing FileMaker Cloud provider in development mode..."

# Install development dependencies
pip install -r requirements-dev.txt

# Install the package in development mode
pip install -e .

# Verify installation
python validate_install.py

echo "Installation complete!"
echo "You can now use the FileMaker Cloud provider in your Airflow environment." 