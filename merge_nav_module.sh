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
    
    # Cleanup: try to return to MAIN_HUB and clean up temp branch
    if [[ "$(git branch --show-current 2>/dev/null)" != "MAIN_HUB" ]]; then
        log "🔄 Attempting cleanup..."
        git checkout MAIN_HUB 2>/dev/null || log "⚠️  Could not checkout MAIN_HUB"
        
        # Try to delete temp branch if it exists
        local temp_branch=$(git branch --list | grep "nav-merge-" | head -1 | tr -d ' *')
        if [[ -n "$temp_branch" ]]; then
            git branch -D "$temp_branch" 2>/dev/null || log "⚠️  Could not delete temp branch $temp_branch"
        fi
    fi
    
    exit $exit_code
}

# Set up error handling
trap 'handle_error $LINENO' ERR

# Configuration
SOURCE_BRANCH="workflow-navigation"
TARGET_BRANCH="MAIN_HUB"
NAV_MODULE_PATH="modules/nav"
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
TEMP_BRANCH="nav-merge-$TIMESTAMP"

log "🚀 Starting Navigation Module Merge Script"
log "AUTO-COMMIT: Enabled - All changes will be committed before merge"
log "Source: $SOURCE_BRANCH"
log "Target: $TARGET_BRANCH"
log "Temp Branch: $TEMP_BRANCH"

# Step 1: Verify we're on MAIN_HUB
log "Step 1: Verifying current branch..."
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "$TARGET_BRANCH" ]]; then
    log "❌ ERROR: Must be on $TARGET_BRANCH branch to start merge. Current: $CURRENT_BRANCH"
    exit 1
fi
log "✅ Currently on $TARGET_BRANCH"

# Step 2: Check for uncommitted changes and commit them
log "Step 2: Checking for uncommitted changes..."
if [[ -n "$(git status --porcelain)" ]]; then
    log "📝 Found uncommitted changes - committing them first..."
    git add .
    git commit -m "Auto-commit before nav module merge - $TIMESTAMP"
    log "✅ Changes committed successfully"
else
    log "✅ No uncommitted changes found"
fi

# Step 3: Verify source branch exists
log "Step 3: Verifying source branch exists..."
if ! git show-ref --verify --quiet refs/heads/$SOURCE_BRANCH; then
    log "❌ ERROR: Source branch $SOURCE_BRANCH does not exist"
    exit 1
fi
log "✅ Source branch $SOURCE_BRANCH exists"

# Step 4: Create temporary branch
log "Step 4: Creating temporary branch $TEMP_BRANCH..."
git checkout -b "$TEMP_BRANCH"
log "✅ Temporary branch created"

# Step 5: Remove existing nav module
log "Step 5: Removing existing nav module..."
if [[ -d "$NAV_MODULE_PATH" ]]; then
    rm -rf "$NAV_MODULE_PATH"
    log "✅ Existing nav module removed"
else
    log "ℹ️  No existing nav module found"
fi

# Step 6: Checkout nav module from source branch
log "Step 6: Checking out nav module from $SOURCE_BRANCH..."
git checkout "$SOURCE_BRANCH" -- "$NAV_MODULE_PATH"
log "✅ Nav module checked out from $SOURCE_BRANCH"

# Step 7: Stage the changes
log "Step 7: Staging nav module changes..."
git add "$NAV_MODULE_PATH"
log "✅ Changes staged"

# Step 8: Show what will be changed
log "Step 8: Showing changes to be applied..."
git diff --cached --name-only
log "✅ Changes preview complete"

# Step 9: Commit changes to temporary branch
log "Step 9: Committing changes to temporary branch..."
git commit -m "Merge nav module from $SOURCE_BRANCH - $TIMESTAMP"
log "✅ Changes committed to temporary branch"

# Step 10: Switch back to MAIN_HUB
log "Step 10: Switching back to $TARGET_BRANCH..."
git checkout "$TARGET_BRANCH"
log "✅ Switched to $TARGET_BRANCH"

# Step 11: Merge temporary branch into MAIN_HUB
log "Step 11: Merging temporary branch into $TARGET_BRANCH..."
git merge "$TEMP_BRANCH" --no-edit
log "✅ Merge completed successfully"

# Step 12: Clean up temporary branch
log "Step 12: Cleaning up temporary branch..."
git branch -D "$TEMP_BRANCH"
log "✅ Temporary branch deleted"

# Step 13: Final verification
log "Step 13: Final verification..."
if [[ -d "$NAV_MODULE_PATH" ]]; then
    log "✅ Nav module exists in $TARGET_BRANCH"
    log "📁 Nav module contents:"
    ls -la "$NAV_MODULE_PATH"
else
    log "❌ ERROR: Nav module not found after merge"
    exit 1
fi

# Step 14: Show final status
log "Step 14: Final status..."
git status --porcelain
log "✅ Merge completed successfully!"

log "🎉 NAVIGATION MODULE MERGE COMPLETE!"
log "📋 Summary:"
log "   - Source: $SOURCE_BRANCH"
log "   - Target: $TARGET_BRANCH"
log "   - Temp Branch: $TEMP_BRANCH (deleted)"
log "   - Nav Module: $NAV_MODULE_PATH (updated)"
log "   - Current Branch: $(git branch --show-current)"
log ""
log "🚀 Ready to test the updated navigation module!" 