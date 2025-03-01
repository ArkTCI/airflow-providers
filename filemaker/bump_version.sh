#!/bin/bash
# Script to bump the version of the FileMaker provider package
# Usage: ./bump_version.sh [patch|minor|major]

# Default to patch if no argument is provided
PART=${1:-patch}

# Validate the input
if [[ ! "$PART" =~ ^(patch|minor|major)$ ]]; then
    echo "Error: Version part must be one of: patch, minor, major"
    echo "Usage: ./bump_version.sh [patch|minor|major]"
    exit 1
fi

# Check if bump2version is installed
if ! command -v bump2version &> /dev/null; then
    echo "bump2version not found, installing..."
    pip install bump2version
fi

# Get the current version
CURRENT_VERSION=$(python -c "from airflow.providers.filemaker.version import __version__; print(__version__)")
echo "Current version: $CURRENT_VERSION"

# Bump the version
echo "Bumping $PART version..."
bump2version $PART --verbose

# Get the new version
NEW_VERSION=$(python -c "from airflow.providers.filemaker.version import __version__; print(__version__)")
echo "Version bumped to: $NEW_VERSION"

echo "Don't forget to push the changes with: git push && git push --tags" 