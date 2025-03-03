#!/bin/bash

# Version bump script for the filemaker provider
# Handles patch, minor, major version bumps and version reset

# Usage function
usage() {
  echo "Usage: bump_version.sh [patch|minor|major|reset VERSION]"
  echo "  patch: Increases the patch version (e.g., 2.1.1 -> 2.1.2)"
  echo "  minor: Increases the minor version (e.g., 2.1.1 -> 2.2.0)"
  echo "  major: Increases the major version (e.g., 2.1.1 -> 3.0.0)"
  echo "  reset VERSION: Resets to the specified version (e.g., reset 2.0.0)"
  exit 1
}

# Directory check and navigation
check_directory() {
  if [ $(basename "$PWD") != "filemaker" ]; then
    echo "Not in filemaker directory, navigating there..."
    cd "$(dirname "$0")" || { echo "Error: filemaker directory not found"; exit 1; }
  fi
}

# Function to update provider.yaml
update_provider_yaml() {
  echo "Checking if version $VERSION is already in provider.yaml..."
  if ! grep -q "  - $VERSION" provider.yaml; then
    echo "Adding version $VERSION to provider.yaml..."
    cp provider.yaml provider.yaml.bak
    
    # Find the line number of "versions:"
    VERSIONS_LINE=$(grep -n "^versions:" provider.yaml | cut -d':' -f1)
    
    if [ -z "$VERSIONS_LINE" ]; then
      echo "Error: Could not find 'versions:' line in provider.yaml"
      return 1
    fi
    
    # Add the new version at the top of the versions list
    (
      head -n "$VERSIONS_LINE" provider.yaml
      echo "  - $VERSION"
      tail -n +$((VERSIONS_LINE + 1)) provider.yaml
    ) > provider.yaml.new
    
    mv provider.yaml.new provider.yaml
    echo "provider.yaml updated successfully with version $VERSION at the top of the list."
  else
    echo "Version $VERSION already exists in provider.yaml, skipping update."
  fi
}

# Function to perform version bump
bump_version() {
  local BUMP_TYPE="$1"
  echo "Bumping $BUMP_TYPE version using bump2version..."
  bump2version --config-file=.bumpversion.cfg --allow-dirty "$BUMP_TYPE" || { 
    echo "Error: Failed to bump version"; 
    exit 1; 
  }
}

# Function to compare version strings
version_greater_than() {
  local VER1=$1
  local VER2=$2
  
  # Remove v prefix if present
  VER1=${VER1#v}
  VER2=${VER2#v}
  
  # Compare using sort
  if [ "$(echo -e "$VER1\n$VER2" | sort -V | tail -n1)" = "$VER1" ] && [ "$VER1" != "$VER2" ]; then
    return 0
  else
    return 1
  fi
}

# Function to clean up git tags and branches with versions greater than reset version
cleanup_git_artifacts() {
  local RESET_VERSION="$1"
  local SHOULD_CLEANUP="$2"
  
  if [ "$SHOULD_CLEANUP" != "y" ] && [ "$SHOULD_CLEANUP" != "Y" ]; then
    echo "Skipping cleanup of git tags and branches."
    return
  fi
  
  echo "Looking for git tags and branches with versions greater than $RESET_VERSION..."
  
  # Check if git is available and we're in a git repository
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Warning: Not in a git repository, skipping git cleanup."
    return
  fi
  
  # Find and delete tags
  local HIGHER_TAGS=()
  for TAG in $(git tag); do
    # Skip tags that don't match the version pattern
    if [[ $TAG =~ ^v?[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
      if version_greater_than "$TAG" "$RESET_VERSION"; then
        HIGHER_TAGS+=("$TAG")
      fi
    fi
  done
  
  if [ ${#HIGHER_TAGS[@]} -gt 0 ]; then
    echo "Found ${#HIGHER_TAGS[@]} tags with versions greater than $RESET_VERSION:"
    printf "  %s\n" "${HIGHER_TAGS[@]}"
    
    echo "Do you want to delete these tags? (y/n): "
    read DELETE_TAGS
    if [ "$DELETE_TAGS" = "y" ] || [ "$DELETE_TAGS" = "Y" ]; then
      for TAG in "${HIGHER_TAGS[@]}"; do
        echo "Deleting local tag $TAG..."
        git tag -d "$TAG"
        
        # Check if the tag exists on the remote
        if git ls-remote --tags origin | grep -q "refs/tags/$TAG"; then
          echo "Deleting remote tag $TAG..."
          git push --delete origin "$TAG"
        fi
      done
    else
      echo "Skipping tag deletion."
    fi
  else
    echo "No tags found with versions greater than $RESET_VERSION."
  fi
  
  # Find and delete branches
  local HIGHER_BRANCHES=()
  for BRANCH in $(git branch -a | sed 's/^\*//;s/^[[:space:]]*//'); do
    # Process only release/ branches 
    if [[ $BRANCH =~ release/v([0-9]+\.[0-9]+\.[0-9]+)$ ]]; then
      local BRANCH_VERSION="${BASH_REMATCH[1]}"
      if version_greater_than "$BRANCH_VERSION" "$RESET_VERSION"; then
        HIGHER_BRANCHES+=("$BRANCH")
      fi
    fi
  done
  
  if [ ${#HIGHER_BRANCHES[@]} -gt 0 ]; then
    echo "Found ${#HIGHER_BRANCHES[@]} branches with versions greater than $RESET_VERSION:"
    printf "  %s\n" "${HIGHER_BRANCHES[@]}"
    
    echo "Do you want to delete these branches? (y/n): "
    read DELETE_BRANCHES
    if [ "$DELETE_BRANCHES" = "y" ] || [ "$DELETE_BRANCHES" = "Y" ]; then
      for BRANCH in "${HIGHER_BRANCHES[@]}"; do
        # Handle both local and remote branches
        if [[ $BRANCH == remotes/origin/* ]]; then
          local REMOTE_BRANCH=${BRANCH#remotes/origin/}
          echo "Deleting remote branch $REMOTE_BRANCH..."
          git push --delete origin "$REMOTE_BRANCH"
        else
          echo "Deleting local branch $BRANCH..."
          git branch -D "$BRANCH"
        fi
      done
    else
      echo "Skipping branch deletion."
    fi
  else
    echo "No branches found with versions greater than $RESET_VERSION."
  fi
}

# Function to reset version
reset_version() {
  local NEW_VERSION="$1"
  
  # Check if resetting to a lower version
  local CURRENT_VERSION=$(grep -o '"[0-9]\+\.[0-9]\+\.[0-9]\+"' version.py | tr -d '"')
  local SHOULD_CLEANUP="n"
  
  if version_greater_than "$CURRENT_VERSION" "$NEW_VERSION"; then
    echo "Warning: You are resetting from $CURRENT_VERSION to a lower version $NEW_VERSION."
    echo "Do you want to clean up git tags and branches with higher versions? (y/n): "
    read SHOULD_CLEANUP
  fi
  
  echo "Resetting version to $NEW_VERSION..."
  
  # Use bump2version to set the version with --new-version flag to ensure all files are updated
  echo "Using bump2version to set version to $NEW_VERSION in all configured files..."
  bump2version --config-file=.bumpversion.cfg --new-version="$NEW_VERSION" --allow-dirty patch || {
    echo "Warning: bump2version failed, falling back to manual updates";
    
    # Fallback: Update version.py
    sed -i '' "s/__version__ = \"[0-9]\+\.[0-9]\+\.[0-9]\+\"/__version__ = \"$NEW_VERSION\"/" version.py
    
    # Update __init__.py
    if [ -f "src/airflow/providers/filemaker/__init__.py" ]; then
      echo "Updating __init__.py with version $NEW_VERSION..."
      sed -i '' "s/__version__ = \"[0-9]\+\.[0-9]\+\.[0-9]\+\"/__version__ = \"$NEW_VERSION\"/" src/airflow/providers/filemaker/__init__.py
    else
      echo "Warning: __init__.py not found at expected location"
    fi
    
    # Update pyproject.toml if it exists
    if [ -f "pyproject.toml" ]; then
      echo "Updating pyproject.toml with version $NEW_VERSION..."
      sed -i '' "s/version = \"[0-9]\+\.[0-9]\+\.[0-9]\+\"/version = \"$NEW_VERSION\"/" pyproject.toml
    fi
    
    # Update .bumpversion.cfg manually since bump2version failed
    sed -i '' "s/current_version = [0-9]\+\.[0-9]\+\.[0-9]\+/current_version = $NEW_VERSION/" .bumpversion.cfg
  }
  
  # Update version.txt (not handled by bump2version)
  echo "VERSION=$NEW_VERSION" > version.txt
  
  # Set the VERSION variable for provider.yaml update
  VERSION="$NEW_VERSION"
  
  # Clean up git artifacts if requested
  cleanup_git_artifacts "$NEW_VERSION" "$SHOULD_CLEANUP"
}

# Update version in all dependent files
update_version_in_files() {
  echo "Extracting current version from version.py..."
  VERSION=$(grep -o '"[0-9]\+\.[0-9]\+\.[0-9]\+"' version.py | tr -d '"')

  
  # Note: No need to update setup.py, __init__.py or pyproject.toml
  # as they are already updated by bump2version via .bumpversion.cfg
}

# Main logic
main() {
  # Parameter validation
  if [ "$1" = "reset" ] && [ -z "$2" ]; then
    echo "Error: reset option requires a VERSION parameter"
    usage
  fi

  # Directory check
  check_directory

  # Perform version bump or reset
  if [ "$1" = "reset" ]; then
    # Reset logic
    reset_version "$2"
  else
    # Bump logic
    bump_version "$1"
    update_version_in_files
  fi

  # Update provider.yaml
  update_provider_yaml

  echo "✅ Version operation completed. Current version is $VERSION"
}

# Entry point
if [ $# -lt 1 ] || [[ ! "$1" =~ ^(patch|minor|major|reset)$ ]]; then
  usage
fi

main "$@" 