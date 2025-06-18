#!/bin/bash

# Navigation Module Merge Script
# Merges modules/nav/ from workflow-navigation branch to MAIN_HUB branch
# Follows the firewall protocol: DO NOT EDIT modules/nav/ in MAIN_HUB directly

set -e  # Exit on any error

echo "=== Navigation Module Merge Script ==="
echo "Source: workflow-navigation branch"
echo "Target: MAIN_HUB branch"
echo "Directory: modules/nav/"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Ensure we're on MAIN_HUB branch
if [ "$CURRENT_BRANCH" != "MAIN_HUB" ]; then
    echo "❌ Error: Must be on MAIN_HUB branch to perform merge"
    echo "Current branch: $CURRENT_BRANCH"
    echo "Please checkout MAIN_HUB first: git checkout MAIN_HUB"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  Warning: You have uncommitted changes"
    echo "Stashing changes for safety..."
    git stash push -m "Auto-stash before nav module merge"
    STASHED=true
else
    STASHED=false
fi

# Check if workflow-navigation branch exists
if ! git show-ref --verify --quiet refs/heads/workflow-navigation; then
    echo "❌ Error: workflow-navigation branch does not exist"
    exit 1
fi

# Create temporary branch for safe merging
TEMP_BRANCH="nav-merge-$(date +%Y%m%d-%H%M%S)"
echo "Creating temporary branch: $TEMP_BRANCH"
git checkout -b "$TEMP_BRANCH"

# Fetch latest changes from workflow-navigation
echo "Fetching latest changes from workflow-navigation..."
git fetch origin workflow-navigation:workflow-navigation

# Merge only the modules/nav/ directory from workflow-navigation
echo "Merging modules/nav/ from workflow-navigation..."
git checkout workflow-navigation -- modules/nav/

# Check what files were changed
echo ""
echo "=== Files Changed ==="
git status --porcelain modules/nav/

# Verify only navigation module files were touched
CHANGED_FILES=$(git status --porcelain | grep -v "^M.*modules/nav/" | grep -v "^A.*modules/nav/" | grep -v "^D.*modules/nav/" || true)
if [ -n "$CHANGED_FILES" ]; then
    echo "❌ Error: Files outside modules/nav/ were changed:"
    echo "$CHANGED_FILES"
    echo "Aborting merge for safety"
    git checkout MAIN_HUB
    git branch -D "$TEMP_BRANCH"
    if [ "$STASHED" = true ]; then
        git stash pop
    fi
    exit 1
fi

# Show diff of changes
echo ""
echo "=== Changes to be merged ==="
git diff HEAD modules/nav/

# Ask for confirmation
echo ""
read -p "Do you want to proceed with the merge? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Merge cancelled"
    git checkout MAIN_HUB
    git branch -D "$TEMP_BRANCH"
    if [ "$STASHED" = true ]; then
        git stash pop
    fi
    exit 0
fi

# Commit the changes
echo "Committing navigation module merge..."
git add modules/nav/
git commit -m "Merge navigation module from workflow-navigation branch

- Source: workflow-navigation branch
- Target: MAIN_HUB branch  
- Directory: modules/nav/
- Following firewall protocol: DO NOT EDIT in MAIN_HUB directly

This merge updates the navigation module with latest changes from the owning branch."

# Switch back to MAIN_HUB and merge the temporary branch
echo "Switching back to MAIN_HUB..."
git checkout MAIN_HUB

echo "Merging temporary branch into MAIN_HUB..."
git merge "$TEMP_BRANCH" --no-ff -m "Merge navigation module updates from workflow-navigation

- Merged: modules/nav/ directory
- Source: workflow-navigation branch
- Protocol: Firewall-compliant merge"

# Clean up temporary branch
echo "Cleaning up temporary branch..."
git branch -D "$TEMP_BRANCH"

# Restore stashed changes if any
if [ "$STASHED" = true ]; then
    echo "Restoring stashed changes..."
    git stash pop
fi

echo ""
echo "✅ Navigation module merge completed successfully!"
echo "✅ Source: workflow-navigation branch"
echo "✅ Target: MAIN_HUB branch"
echo "✅ Directory: modules/nav/"
echo "✅ Protocol: Firewall-compliant"
echo ""
echo "The navigation module has been updated in MAIN_HUB from workflow-navigation."
echo "Remember: DO NOT EDIT modules/nav/ directly in MAIN_HUB - all changes must come from workflow-navigation branch." 