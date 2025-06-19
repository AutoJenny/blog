#!/bin/bash

# Navigation Module Merge Script
# Merges modules/nav/ from workflow-navigation branch to MAIN_HUB branch
# Follows the firewall protocol: DO NOT EDIT modules/nav/ in MAIN_HUB directly

set -e  # Exit on any error

# Enhanced logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Error handling function
handle_error() {
    local exit_code=$?
    local line_number=$1
    log "❌ ERROR: Script failed at line $line_number with exit code $exit_code"
    log "Current branch: $(git branch --show-current 2>/dev/null || echo 'unknown')"
    log "Git status:"
    git status --porcelain 2>/dev/null || echo "Unable to get git status"
    log "Recent git log:"
    git log --oneline -3 2>/dev/null || echo "Unable to get git log"
    
    # Cleanup on error
    if [ -n "$TEMP_BRANCH" ] && git show-ref --verify --quiet refs/heads/"$TEMP_BRANCH" 2>/dev/null; then
        log "Cleaning up temporary branch $TEMP_BRANCH..."
        git checkout MAIN_HUB 2>/dev/null || true
        git branch -D "$TEMP_BRANCH" 2>/dev/null || true
    fi
    
    if [ "$STASHED" = true ]; then
        log "Restoring stashed changes..."
        git stash pop 2>/dev/null || true
    fi
    
    exit $exit_code
}

# Set up error trapping
trap 'handle_error $LINENO' ERR

echo "=== Navigation Module Merge Script ==="
echo "Source: workflow-navigation branch"
echo "Target: MAIN_HUB branch"
echo "Directory: modules/nav/"
echo "AUTO-APPROVE: Enabled (no confirmation required)"
echo ""

# Check if we're in a git repository
log "Step 1: Checking git repository..."
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    log "❌ Error: Not in a git repository"
    exit 1
fi
log "✅ Git repository found"

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
log "Current branch: $CURRENT_BRANCH"

# Ensure we're on MAIN_HUB branch
log "Step 2: Verifying we're on MAIN_HUB branch..."
if [ "$CURRENT_BRANCH" != "MAIN_HUB" ]; then
    log "❌ Error: Must be on MAIN_HUB branch to perform merge"
    log "Current branch: $CURRENT_BRANCH"
    log "Please checkout MAIN_HUB first: git checkout MAIN_HUB"
    exit 1
fi
log "✅ On MAIN_HUB branch"

# Check for uncommitted changes
log "Step 3: Checking for uncommitted changes..."
if ! git diff-index --quiet HEAD --; then
    log "⚠️  Warning: You have uncommitted changes"
    log "Stashing changes for safety..."
    git stash push -m "Auto-stash before nav module merge"
    STASHED=true
    log "✅ Changes stashed"
else
    STASHED=false
    log "✅ No uncommitted changes"
fi

# Check if workflow-navigation branch exists
log "Step 4: Verifying workflow-navigation branch exists..."
if ! git show-ref --verify --quiet refs/heads/workflow-navigation; then
    log "❌ Error: workflow-navigation branch does not exist"
    log "Available branches:"
    git branch -a
    exit 1
fi
log "✅ workflow-navigation branch exists"

# Check if modules/nav/ exists in workflow-navigation
log "Step 5: Verifying modules/nav/ exists in workflow-navigation..."
if ! git show workflow-navigation:modules/nav/ > /dev/null 2>&1; then
    log "❌ Error: modules/nav/ does not exist in workflow-navigation branch"
    log "Files in workflow-navigation:"
    git ls-tree -r --name-only workflow-navigation | head -20
    exit 1
fi
log "✅ modules/nav/ exists in workflow-navigation"

# Create temporary branch for safe merging
TEMP_BRANCH="nav-merge-$(date +%Y%m%d-%H%M%S)"
log "Step 6: Creating temporary branch: $TEMP_BRANCH"
git checkout -b "$TEMP_BRANCH"
log "✅ Temporary branch created"

# Fetch latest changes from workflow-navigation
log "Step 7: Fetching latest changes from workflow-navigation..."
git fetch origin workflow-navigation:workflow-navigation
log "✅ Latest changes fetched"

# Show what we're about to merge
log "Step 8: Analyzing changes to be merged..."
log "Files in workflow-navigation modules/nav/:"
git ls-tree -r --name-only workflow-navigation modules/nav/ | head -10

log "Files in current modules/nav/:"
if git ls-tree -r --name-only HEAD modules/nav/ > /dev/null 2>&1; then
    git ls-tree -r --name-only HEAD modules/nav/ | head -10
else
    log "No modules/nav/ in current branch"
fi

# Merge only the modules/nav/ directory from workflow-navigation
log "Step 9: Merging modules/nav/ from workflow-navigation..."
git checkout workflow-navigation -- modules/nav/
log "✅ Files checked out from workflow-navigation"

# Check what files were changed
log "Step 10: Analyzing changes..."
log "=== Files Changed ==="
git status --porcelain modules/nav/

# Verify only navigation module files were touched
CHANGED_FILES=$(git status --porcelain | grep -v "^M.*modules/nav/" | grep -v "^A.*modules/nav/" | grep -v "^D.*modules/nav/" || true)
if [ -n "$CHANGED_FILES" ]; then
    log "❌ Error: Files outside modules/nav/ were changed:"
    echo "$CHANGED_FILES"
    log "Aborting merge for safety"
    git checkout MAIN_HUB
    git branch -D "$TEMP_BRANCH"
    if [ "$STASHED" = true ]; then
        git stash pop
    fi
    exit 1
fi
log "✅ Only modules/nav/ files were changed"

# Show diff of changes
log "Step 11: Showing changes to be merged..."
log "=== Changes to be merged ==="
git diff HEAD modules/nav/

# Auto-approve the merge (no confirmation required)
log "Step 12: Auto-approving merge (no confirmation required)..."
log "✅ Merge automatically approved"

# Commit the changes
log "Step 13: Committing navigation module merge..."
git add modules/nav/
git commit -m "Merge navigation module from workflow-navigation branch

- Source: workflow-navigation branch
- Target: MAIN_HUB branch  
- Directory: modules/nav/
- Following firewall protocol: DO NOT EDIT in MAIN_HUB directly
- Auto-approved merge

This merge updates the navigation module with latest changes from the owning branch."
log "✅ Changes committed to temporary branch"

# Switch back to MAIN_HUB and merge the temporary branch
log "Step 14: Switching back to MAIN_HUB..."
git checkout MAIN_HUB
log "✅ Switched to MAIN_HUB"

log "Step 15: Merging temporary branch into MAIN_HUB..."
git merge "$TEMP_BRANCH" --no-ff -m "Merge navigation module updates from workflow-navigation

- Merged: modules/nav/ directory
- Source: workflow-navigation branch
- Protocol: Firewall-compliant merge
- Auto-approved"
log "✅ Temporary branch merged into MAIN_HUB"

# Clean up temporary branch
log "Step 16: Cleaning up temporary branch..."
git branch -D "$TEMP_BRANCH"
log "✅ Temporary branch deleted"

# Restore stashed changes if any
if [ "$STASHED" = true ]; then
    log "Step 17: Restoring stashed changes..."
    git stash pop
    log "✅ Stashed changes restored"
fi

# Final verification
log "Step 18: Final verification..."
log "Current branch: $(git branch --show-current)"
log "Recent commits:"
git log --oneline -3

echo ""
log "✅ Navigation module merge completed successfully!"
log "✅ Source: workflow-navigation branch"
log "✅ Target: MAIN_HUB branch"
log "✅ Directory: modules/nav/"
log "✅ Protocol: Firewall-compliant"
log "✅ Auto-approved merge"
echo ""
log "The navigation module has been updated in MAIN_HUB from workflow-navigation."
log "Remember: DO NOT EDIT modules/nav/ directly in MAIN_HUB - all changes must come from workflow-navigation branch." 