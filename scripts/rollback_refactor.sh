#!/bin/bash
# Rollback script for refactoring
CHECKPOINT_BRANCH="refactor/authoring-modularization"
CHECKPOINT_COMMIT=$(git log --format="%H" -n 1 --grep="Pre-refactor checkpoint")

echo "Available rollback points:"
git log --oneline --grep="checkpoint" | head -10

read -p "Enter commit hash to rollback to (or 'cancel'): " COMMIT_HASH

if [ "$COMMIT_HASH" = "cancel" ]; then
    echo "Rollback cancelled"
    exit 0
fi

git reset --hard $COMMIT_HASH
echo "Rolled back to $COMMIT_HASH"
