#!/usr/bin/env python3
"""
Script to simplify the version bumping process for the FileMaker provider package.
This script handles both version file updates and Git tagging in one step.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# Path to the version file
VERSION_FILE = Path("src/airflow/providers/filemaker/version.py")

def get_current_version():
    """Read the current version from the version file."""
    with open(VERSION_FILE, "r") as f:
        content = f.read()
    
    # Extract version using regex
    match = re.search(r'__version__ = "([0-9]+\.[0-9]+\.[0-9]+)"', content)
    if not match:
        print("Error: Could not find version in version.py")
        sys.exit(1)
    
    return match.group(1)

def bump_version(current_version, bump_type):
    """Bump the version according to the specified bump type."""
    major, minor, patch = map(int, current_version.split("."))
    
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        return current_version

def update_version_file(new_version):
    """Update the version in the version file."""
    with open(VERSION_FILE, "r") as f:
        content = f.read()
    
    # Replace version
    updated_content = re.sub(
        r'__version__ = "[0-9]+\.[0-9]+\.[0-9]+"',
        f'__version__ = "{new_version}"',
        content
    )
    
    with open(VERSION_FILE, "w") as f:
        f.write(updated_content)

def git_commit_and_tag(current_version, new_version):
    """Commit the version change and create a tag."""
    try:
        # Stage the version file
        subprocess.run(["git", "add", str(VERSION_FILE)], check=True)
        
        # Commit the change
        subprocess.run(
            ["git", "commit", "-m", f"Bump version: {current_version} → {new_version}"],
            check=True
        )
        
        # Create a tag
        subprocess.run(["git", "tag", f"v{new_version}"], check=True)
        
        print(f"Created commit and tag for version {new_version}")
        print("Run 'git push && git push --tags' to push changes to remote")
        
    except subprocess.CalledProcessError as e:
        print(f"Error in Git operations: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Bump version for the FileMaker provider package")
    parser.add_argument(
        "bump_type",
        choices=["major", "minor", "patch"],
        help="Type of version bump to perform"
    )
    parser.add_argument(
        "--no-git", 
        action="store_true", 
        help="Skip Git commit and tag operations"
    )
    
    args = parser.parse_args()
    
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    
    new_version = bump_version(current_version, args.bump_type)
    print(f"New version: {new_version}")
    
    update_version_file(new_version)
    print(f"Updated version in {VERSION_FILE}")
    
    if not args.no_git:
        git_commit_and_tag(current_version, new_version)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 