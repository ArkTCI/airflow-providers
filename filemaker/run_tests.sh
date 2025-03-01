#!/bin/bash
# Run tests for the FileMaker Cloud provider

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Running tests for FileMaker Cloud provider..."

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}${SCRIPT_DIR}/src"
echo "PYTHONPATH set to: $PYTHONPATH"

# Install requirements
echo "Installing test requirements..."
pip install -r "${SCRIPT_DIR}/requirements.txt"
pip install -r "${SCRIPT_DIR}/requirements-dev.txt"

# Check if .env file exists and source it
if [ -f "${SCRIPT_DIR}/.env" ]; then
    echo "Loading credentials from .env file..."
    export $(grep -v '^#' "${SCRIPT_DIR}/.env" | xargs)
    echo "Loaded environment variables from .env file"
fi

# Run unit tests
echo "Running unit tests..."
python -m pytest "${SCRIPT_DIR}/tests/unit" -v

# Check if we have FileMaker credentials
if [ -n "$FILEMAKER_HOST" ] && [ -n "$FILEMAKER_DATABASE" ] && [ -n "$FILEMAKER_USERNAME" ] && [ -n "$FILEMAKER_PASSWORD" ]; then
    echo ""
    echo "FileMaker credentials found, running integration tests..."
    echo "Host: $FILEMAKER_HOST"
    echo "Database: $FILEMAKER_DATABASE"
    echo "Username: $FILEMAKER_USERNAME"
    echo "Password: $(echo "$FILEMAKER_PASSWORD" | sed 's/./*/g')"
    
    echo ""
    echo "============================================================"
    echo "NOTICE: Authentication uses AWS Cognito with FMID tokens"
    echo "============================================================"
    echo "The tests will authenticate with FileMaker Cloud using:"
    echo "1. AWS Cognito authentication with fixed pool credentials"
    echo "2. FMID token format (Authorization: FMID <token>)"
    echo "============================================================"
    
    # Run integration tests
    echo ""
    echo "Running integration tests..."
    python -m pytest "${SCRIPT_DIR}/tests/integration" -v
else
    echo ""
    echo "FileMaker credentials not set. Skipping integration tests."
    echo "To run integration tests, create a .env file with the following variables:"
    echo "FILEMAKER_HOST=https://your-filemaker-host.com"
    echo "FILEMAKER_DATABASE=your-database"
    echo "FILEMAKER_USERNAME=your-username"
    echo "FILEMAKER_PASSWORD=your-password"
    echo ""
    echo "Note: The FILEMAKER_HOST must include the https:// protocol"
fi

echo "Tests completed." 