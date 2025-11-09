# Git Sync Fix: Repository Size Issue

## Problem
GitHub push operations failing with HTTP 500 errors due to repository size (6.3GB) exceeding GitHub's limits.

## Root Cause
- Repository pack size: 6.17 GiB
- Large files in git history (backup files, model files)
- GitHub rejects pushes over ~2-5GB

## Solution Options

### Option 1: Clean Git History (Recommended)
Remove large files from git history to reduce repository size.

**Steps:**
1. Install BFG Repo-Cleaner or git-filter-repo
2. Remove large files from history
3. Force push (requires coordination if others use repo)

**Commands:**
```bash
# Using git-filter-repo (recommended)
pip install git-filter-repo

# Remove large backup files
git filter-repo --path backups/ --invert-paths

# Remove large model files if they were ever committed
git filter-repo --path 'static/models/lora/*.safetensors' --invert-paths

# Force push (WARNING: rewrites history)
git push origin --force --all
```

### Option 2: Use Git LFS for Large Files
Track large files with Git LFS instead of regular git.

**Steps:**
1. Install Git LFS
2. Track large file patterns
3. Migrate existing large files

**Commands:**
```bash
# Install Git LFS
brew install git-lfs  # macOS
# or: apt-get install git-lfs  # Linux

# Initialize Git LFS
git lfs install

# Track large file patterns
git lfs track "*.safetensors"
git lfs track "backups/*.tar.gz"
git lfs track "backups/*.sql"

# Add .gitattributes
git add .gitattributes
git commit -m "Add Git LFS tracking for large files"

# Migrate existing files (if needed)
git lfs migrate import --include="*.safetensors,backups/*.tar.gz"
```

### Option 3: Exclude Large Files and Clean Up
Ensure large files are properly ignored and remove from tracking.

**Steps:**
1. Verify .gitignore excludes large files
2. Remove tracked large files
3. Clean up git history

**Commands:**
```bash
# Remove large files from tracking (keep local files)
git rm --cached backups/canonicalization_20251004/blog_backup_20251004_082022.tar.gz
git rm --cached static/models/lora/*.safetensors 2>/dev/null || true

# Commit removal
git commit -m "Remove large files from git tracking"

# Verify .gitignore includes these patterns
# *.safetensors
# backups/*.tar.gz
# backups/*.sql
```

### Option 4: Split Repository
Move large files/assets to separate repository or storage.

**Steps:**
1. Create separate repository for large assets
2. Use submodules or external storage
3. Update references

## Immediate Workaround

For now, you can:
1. **Work locally** - All commits are safe locally
2. **Use backup** - Full backup at `/Users/autojenny/Documents/projects/blog_backup_20251109_102151`
3. **Push later** - After cleaning repository size

## Recommended Action Plan

1. **Immediate**: Use Option 3 to remove currently tracked large files
2. **Short-term**: Implement Option 2 (Git LFS) for any large files that need versioning
3. **Long-term**: Clean history with Option 1 if repository size still too large

## Verification

After cleanup, verify repository size:
```bash
git count-objects -vH
# Should show size-pack < 1GB ideally
```

## Notes

- **Force push warning**: Options 1 and 2 may require force push, which rewrites history
- **Backup first**: Always backup before cleaning git history
- **Coordinate**: If others use the repo, coordinate before force pushing
- **GitHub limits**: Individual files > 100MB require Git LFS

