#!/bin/bash

# Script to safely create a git tag for the current version

# Extract the current version from version.py
VERSION=$(grep -o '"[0-9]\+\.[0-9]\+\.[0-9]\+"' version.py | tr -d '"')
TAG_NAME="v$VERSION"

echo "Checking for tag $TAG_NAME..."

# Check if the tag already exists locally
if git rev-parse "$TAG_NAME" >/dev/null 2>&1; then
  echo "Tag $TAG_NAME already exists locally."
  
  # Check if the tag exists on the remote
  if git ls-remote --tags origin | grep -q "refs/tags/$TAG_NAME"; then
    echo "Tag $TAG_NAME already exists on the remote."
    echo "✅ Release tag $TAG_NAME is already set up properly."
    exit 0
  else
    # Tag exists locally but not on remote - push it
    echo "Tag exists locally but not on remote. Pushing tag..."
    git push origin "$TAG_NAME"
    echo "✅ Pushed existing tag $TAG_NAME to remote."
    exit 0
  fi
fi

# Tag doesn't exist, create it
echo "Creating new tag $TAG_NAME..."
git tag -a "$TAG_NAME" -m "Release $TAG_NAME"

# Push the tag to the remote
echo "Pushing tag $TAG_NAME to remote..."
git push origin "$TAG_NAME"

echo "✅ Successfully created and pushed tag $TAG_NAME" 