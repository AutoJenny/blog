# Implementation Plan: Schema Migration + Process Unification + Photo-harvesting Deprecation

## Purpose
This is a **step-by-step implementation guide** with checkpoints, testing reminders, and commit points. Use this during implementation to ensure nothing is missed.

## Pre-Implementation Checklist

### Before Starting
- [ ] **BACKUP DATABASE** - Full backup before any changes
- [ ] **BACKUP CODEBASE** - Git commit current state
- [ ] **CREATE BRANCH** - `git checkout -b refactor/unified-image-schema-and-process`
- [ ] **READ FULL PLAN** - Review `/docs/refactoring/10_DUAL_TABLE_RESOLUTION_PLAN.md`
- [ ] **VERIFY ENVIRONMENT** - Ensure staging/test environment available
- [ ] **NOTIFY TEAM** - If working with others, notify of refactoring work

---

## STAGE 1: Data Migration

### Step 1.1: Audit Current State
**Time**: 30 minutes  
**Risk**: Low (read-only)

- [ ] Run audit queries from plan (Step 1.1)
- [ ] Document results:
  - [ ] Count of records in `image` table: _____
  - [ ] Count of records in `images` table: _____
  - [ ] ID conflicts found: _____
  - [ ] `post_images` pointing to `image`: _____
  - [ ] `post_images` pointing to `images`: _____
  - [ ] `post.header_image_id` pointing to `image`: _____
  - [ ] `post.header_image_id` pointing to `images`: _____

**✅ CHECKPOINT**: Review audit results. If ID conflicts > 0, STOP and resolve first.

**COMMIT POINT**: 
```bash
git add docs/refactoring/
git commit -m "docs: Add audit results for image/images table migration"
```

---

### Step 1.2: Run Data Migration Script
**Time**: 1-2 hours  
**Risk**: Medium (modifies database)

- [ ] **VERIFY BACKUP EXISTS** - Confirm database backup completed
- [ ] Review `migrations/migrate_image_to_images.sql` script
- [ ] **TEST ON STAGING FIRST** - Run on staging database
- [ ] Verify staging migration:
  - [ ] All records migrated
  - [ ] No data loss
  - [ ] FK references updated
- [ ] **ONLY THEN**: Run on production
- [ ] Run migration script (in transaction)
- [ ] **VERIFY RESULTS**:
  - [ ] All records migrated: `SELECT COUNT(*) FROM image` = `SELECT COUNT(*) FROM images`
  - [ ] No orphaned references
  - [ ] FK references updated

**✅ CHECKPOINT**: If migration fails or data doesn't match, ROLLBACK immediately.

**COMMIT POINT**: 
```bash
git add migrations/migrate_image_to_images.sql
git commit -m "migration: Migrate data from image to images table"
```

---

### Step 1.3: Update Foreign Key References
**Time**: 30 minutes  
**Risk**: Low (updates references only)

- [ ] Run FK update queries from plan (Step 1.3)
- [ ] Verify updates:
  - [ ] `post_images.image_id` all point to `images` table
  - [ ] `post.header_image_id` all point to `images` table
- [ ] Run validation queries:
  - [ ] No orphaned `post_images.image_id`
  - [ ] No orphaned `post.header_image_id`

**✅ CHECKPOINT**: If orphaned records found, investigate and fix before proceeding.

**COMMIT POINT**: 
```bash
git commit -m "migration: Update FK references to images table"
```

---

## STAGE 2: Code Migration (Schema)

### Step 2.1: Find All References
**Time**: 30 minutes  
**Risk**: Low (read-only)

- [ ] Run migration helper script (or grep):
  ```bash
  grep -r "FROM image\b\|JOIN image\b\|INSERT INTO image\|UPDATE image" --include="*.py" --include="*.sql" | wc -l
  ```
- [ ] Document all files found
- [ ] Create list of files to update

**✅ CHECKPOINT**: Review file list. Ensure no critical files missed.

**COMMIT POINT**: 
```bash
git add docs/refactoring/
git commit -m "docs: Document image table references found"
```

---

### Step 2.2: Update Priority 1 Files
**Time**: 2-3 hours  
**Risk**: High (core publishing files)

**File 1: `blog-launchpad/publish/header_image_finder.py`**
- [ ] Change `JOIN image i` → `JOIN images i`
- [ ] Change `i.path` → `i.file_path`
- [ ] Test: Run header image finding for test post
- [ ] Verify: Header image found correctly

**✅ CHECKPOINT**: Test after each file update.

**File 2: `blueprints/header.py` - `api_generate_header_image`**
- [ ] Change `UPDATE image` → `UPDATE images`
- [ ] Change `INSERT INTO image` → `INSERT INTO images`
- [ ] Change `path` → `file_path` in column names
- [ ] Test: Generate header image for test post
- [ ] Verify: Image saved to `images` table
- [ ] Verify: `post_images` record created

**✅ CHECKPOINT**: Test header image generation works.

**File 3: `blueprints/header.py` - `api_optimize_header_image`**
- [ ] Change `UPDATE image` → `UPDATE images`
- [ ] Change `INSERT INTO image` → `INSERT INTO images`
- [ ] Change `path` → `file_path`
- [ ] Test: Optimize header image for test post
- [ ] Verify: Image saved to `images` table

**✅ CHECKPOINT**: Test optimization works.

**File 4: `blueprints/launchpad/publishing.py`**
- [ ] Change `JOIN image i` → `JOIN images i`
- [ ] Change `i.path` → `i.file_path`
- [ ] Test: Load post with header image
- [ ] Verify: Header image found correctly

**✅ CHECKPOINT**: Test publishing data loading works.

**COMMIT POINT** (after each file):
```bash
git add [file]
git commit -m "refactor: Update [file] to use images table"
```

**FULL TEST** after all Priority 1 files:
- [ ] Test: Generate header image → Optimize → Publish
- [ ] Verify: Full workflow works end-to-end
- [ ] Check logs: No errors related to image/images table

---

### Step 2.3: Update Priority 2 Files
**Time**: 2-3 hours  
**Risk**: Medium (supporting files)

**File 5: `scripts/backfill_recipe_header_post_images.py`**
- [ ] Change `JOIN image i` → `JOIN images i`
- [ ] Change `i.path` → `i.file_path`
- [ ] Test: Run backfill script (dry-run)
- [ ] Verify: Script finds correct records

**✅ CHECKPOINT**: Test backfill script works.

**Remaining Files**:
- [ ] Update each file from migration helper script results
- [ ] Test after each file (if possible)
- [ ] Document any issues found

**COMMIT POINT** (after Priority 2):
```bash
git add scripts/backfill_recipe_header_post_images.py [other files]
git commit -m "refactor: Update supporting files to use images table"
```

---

### Step 2.4: Update Path Normalization
**Time**: 1 hour  
**Risk**: Medium (affects path handling)

- [ ] Review all path normalization code
- [ ] Ensure all use `file_path` (not `path`)
- [ ] Ensure consistent normalization logic
- [ ] Test: Verify paths normalized correctly

**✅ CHECKPOINT**: Test path normalization works consistently.

**COMMIT POINT**:
```bash
git commit -m "refactor: Update path normalization to use file_path"
```

---

## STAGE 3: Testing (Schema Migration)

### Step 3.1: Unit Tests
**Time**: 1-2 hours  
**Risk**: Low (testing only)

- [ ] Test: `header_image_finder.get_header_image()`
  - [ ] Test with `images` table record
  - [ ] Test filesystem fallback
- [ ] Test: `api_generate_header_image()`
  - [ ] Test creates `images` table record
  - [ ] Test creates `post_images` record
- [ ] Test: Publishing data loading
  - [ ] Test loads header image from `images` table

**✅ CHECKPOINT**: All unit tests pass.

**COMMIT POINT**:
```bash
git commit -m "test: Add unit tests for images table migration"
```

---

### Step 3.2: Integration Tests
**Time**: 2-3 hours  
**Risk**: Low (testing only)

- [ ] Test: Full workflow
  - [ ] Generate header image
  - [ ] Optimize header image
  - [ ] Publish post
  - [ ] Verify header image appears correctly
- [ ] Test: Recipe post workflow
  - [ ] Generate header image
  - [ ] Publish recipe post
  - [ ] Verify header image in published post
- [ ] Test: Theme post workflow
  - [ ] Generate header image
  - [ ] Publish theme post
  - [ ] Verify header image in published post

**✅ CHECKPOINT**: All integration tests pass.

**COMMIT POINT**:
```bash
git commit -m "test: Add integration tests for images table migration"
```

---

### Step 3.3: Data Validation
**Time**: 30 minutes  
**Risk**: Low (read-only)

- [ ] Run validation queries from plan (Step 3.3)
- [ ] Verify:
  - [ ] No orphaned `post_images.image_id`
  - [ ] No orphaned `post.header_image_id`
  - [ ] All references point to `images` table

**✅ CHECKPOINT**: All validation queries pass.

**COMMIT POINT**:
```bash
git commit -m "docs: Add data validation results for images table migration"
```

---

## STAGE 4: Process Unification

### Step 4.1: Remove Photo-harvesting from Preview
**Time**: 1-2 hours  
**Risk**: High (affects preview rendering)

**File**: `blueprints/header.py::header_preview()` (lines 462-503)

- [ ] **BACKUP**: Copy current function
- [ ] Remove lines 462-487 (recipe conditionals + Photo-harvesting)
- [ ] Update image selection logic:
  - [ ] Priority 1: Database link (post_images)
  - [ ] Priority 2: Filesystem check
  - [ ] Remove Photo-harvesting priority
- [ ] Test: Preview recipe post
  - [ ] Verify: Images load correctly
  - [ ] Verify: No Photo-harvesting URLs
- [ ] Test: Preview theme post
  - [ ] Verify: Images load correctly
  - [ ] Verify: No Photo-harvesting URLs
  - [ ] Verify: Same behavior as recipe post

**✅ CHECKPOINT**: Recipe and theme previews work identically.

**COMMIT POINT**:
```bash
git add blueprints/header.py
git commit -m "refactor: Remove Photo-harvesting and recipe conditionals from preview"
```

---

### Step 4.2: Remove Photo-harvesting from Publishing
**Time**: 1-2 hours  
**Risk**: High (affects publishing)

**File**: `blueprints/launchpad/publishing.py::get_post_sections_with_images()` (lines 108-156)

- [ ] **BACKUP**: Copy current function
- [ ] Remove lines 108-156 (Photo-harvesting check)
- [ ] Update image selection:
  - [ ] Priority 1: Database link (post_images)
  - [ ] Priority 2: Filesystem check
- [ ] Test: Publish recipe post
  - [ ] Verify: Images load correctly
  - [ ] Verify: No Photo-harvesting URLs
- [ ] Test: Publish theme post
  - [ ] Verify: Images load correctly
  - [ ] Verify: No Photo-harvesting URLs
  - [ ] Verify: Same behavior as recipe post

**✅ CHECKPOINT**: Recipe and theme publishing works identically.

**COMMIT POINT**:
```bash
git add blueprints/launchpad/publishing.py
git commit -m "refactor: Remove Photo-harvesting from publishing"
```

---

### Step 4.3: Remove Photo-harvesting from Image Processing
**Time**: 1-2 hours  
**Risk**: High (affects image upload)

**File**: `blog-launchpad/clan_publisher.py::process_images()` (lines 502-558)

- [ ] **BACKUP**: Copy current function
- [ ] Remove lines 502-558 (Photo-harvesting URL handling)
- [ ] Add validation: Reject URLs (log warning or raise error)
- [ ] Test: Publish post with local images
  - [ ] Verify: Images upload correctly
- [ ] Test: Publish post with URL (should fail gracefully)
  - [ ] Verify: Error logged, post still publishes

**✅ CHECKPOINT**: Image processing works for local files only.

**COMMIT POINT**:
```bash
git add blog-launchpad/clan_publisher.py
git commit -m "refactor: Remove Photo-harvesting URL handling from image processing"
```

---

### Step 4.4: Unify Author Assignment
**Time**: 1 hour  
**Risk**: Medium (affects author display)

**Files**:
- `blueprints/header.py` (line 340)
- `blog-launchpad/clan_publisher.py` (line 1449)

- [ ] **BACKUP**: Copy current code
- [ ] Remove recipe-specific author assignment
- [ ] Use `post.author_id` from database
- [ ] Test: Preview recipe post
  - [ ] Verify: Author displays correctly
- [ ] Test: Preview theme post
  - [ ] Verify: Author displays correctly
- [ ] Test: Publish recipe post
  - [ ] Verify: Author in published post
- [ ] Test: Publish theme post
  - [ ] Verify: Author in published post

**✅ CHECKPOINT**: Author assignment works for all post types.

**COMMIT POINT**:
```bash
git add blueprints/header.py blog-launchpad/clan_publisher.py
git commit -m "refactor: Unify author assignment (remove recipe-specific logic)"
```

---

### Step 4.5: Unify Title Generation (Optional)
**Time**: 1-2 hours  
**Risk**: Medium (affects title generation)

**File**: `blueprints/header.py::api_compile_header_prompt()` (line 666)

- [ ] **DECISION**: Keep recipe-specific title or unify?
- [ ] If unify:
  - [ ] Remove recipe-specific title generation
  - [ ] Use same LLM-based generation for all
  - [ ] Test: Generate title for recipe post
  - [ ] Test: Generate title for theme post
  - [ ] Verify: Both work correctly

**✅ CHECKPOINT**: Title generation works (or decision made to keep separate).

**COMMIT POINT** (if unified):
```bash
git add blueprints/header.py
git commit -m "refactor: Unify title generation (remove recipe-specific logic)"
```

---

### Step 4.6: Consolidate Publishing Endpoints
**Time**: 30 minutes  
**Risk**: Low (endpoint consolidation)

**File**: `blog-launchpad/publish/publish_endpoint.py`

- [ ] **BACKUP**: Copy current file
- [ ] Remove `/recipe/<post_id>` endpoint (line 16)
- [ ] Update any references to use generic endpoint
- [ ] Test: Publish recipe post via generic endpoint
  - [ ] Verify: Publishes correctly
- [ ] Test: Publish theme post via generic endpoint
  - [ ] Verify: Publishes correctly

**✅ CHECKPOINT**: Single endpoint works for all post types.

**COMMIT POINT**:
```bash
git add blog-launchpad/publish/publish_endpoint.py
git commit -m "refactor: Consolidate publishing endpoints (remove recipe-specific endpoint)"
```

---

## STAGE 5: Photo-harvesting Deprecation

### Step 5.1: Identify All Components
**Time**: 30 minutes  
**Risk**: Low (read-only)

- [ ] Run search for Photo-harvesting references:
  ```bash
  grep -r "photo.*harvest\|Photo-harvesting\|selected_landscape\|photo_search_results" --include="*.py" --include="*.js" --include="*.html" | wc -l
  ```
- [ ] Document all files found
- [ ] Verify against plan's list (Step 5.1)

**✅ CHECKPOINT**: All Photo-harvesting components identified.

**COMMIT POINT**:
```bash
git add docs/refactoring/
git commit -m "docs: Document Photo-harvesting components to archive"
```

---

### Step 5.2: Archive Photo-harvesting Files
**Time**: 1 hour  
**Risk**: Low (creates archive, doesn't delete)

- [ ] **VERIFY BACKUP**: Confirm codebase backed up
- [ ] Run archive script:
  ```bash
  ./scripts/archive_photo_harvesting.sh
  ```
- [ ] Verify archive created:
  - [ ] Code files archived
  - [ ] Templates archived
  - [ ] Static files archived
  - [ ] README created
- [ ] Review archive contents

**✅ CHECKPOINT**: Archive created successfully, all files present.

**COMMIT POINT**:
```bash
git add ARCHIVED_PHOTO_HARVESTING/
git commit -m "archive: Archive Photo-harvesting code, templates, and static files"
```

---

### Step 5.3: Archive Photo-harvesting Data
**Time**: 30 minutes  
**Risk**: Low (creates archive, doesn't delete)

- [ ] Run data archive script:
  ```bash
  python3 scripts/archive_photo_harvesting_data.py
  ```
- [ ] Verify archive:
  - [ ] JSON files archived
  - [ ] Manifest created
  - [ ] Count matches expected

**✅ CHECKPOINT**: All Photo-harvesting data archived.

**COMMIT POINT**:
```bash
git add ARCHIVED_PHOTO_HARVESTING/data/
git commit -m "archive: Archive Photo-harvesting JSON data files"
```

---

### Step 5.4: Remove Photo-harvesting Code
**Time**: 2-3 hours  
**Risk**: High (deletes code)

**Delete Files**:
- [ ] Delete `utils/photo_apis.py`
- [ ] Delete `utils/photo_apis_adapter.py`
- [ ] Delete `utils/photo_harvesting_storage.py`
- [ ] Delete `utils/photo_search_store.py`
- [ ] Delete `blueprints/authoring_api_photography.py`
- [ ] Delete Photo-harvesting JS files
- [ ] Delete Photo-harvesting CSS files
- [ ] Delete Photo-harvesting templates

**Modify Files** (Remove Photo-harvesting routes/logic):
- [ ] `blueprints/header.py` - Remove photo-search routes (lines 3418-3706+)
- [ ] `blueprints/imaging.py` - Remove photo selection routes
- [ ] Verify: No Photo-harvesting imports remain
- [ ] Test: Verify app starts without errors

**✅ CHECKPOINT**: App starts, no Photo-harvesting imports fail.

**COMMIT POINT** (after deletions):
```bash
git add -A
git commit -m "refactor: Remove Photo-harvesting code files"
```

**COMMIT POINT** (after route removal):
```bash
git add blueprints/header.py blueprints/imaging.py
git commit -m "refactor: Remove Photo-harvesting routes"
```

---

### Step 5.5: Remove Photo-harvesting from Database
**Time**: 30 minutes  
**Risk**: Low (read-only check)

- [ ] Run database check queries (Step 5.5)
- [ ] Document any Photo-harvesting metadata found
- [ ] If found: Archive metadata (don't delete yet)
- [ ] Verify: No Photo-harvesting data in active use

**✅ CHECKPOINT**: No Photo-harvesting data in active use.

**COMMIT POINT**:
```bash
git add docs/refactoring/
git commit -m "docs: Document Photo-harvesting database cleanup"
```

---

### Step 5.6: Remove Environment Variables
**Time**: 15 minutes  
**Risk**: Low (removes unused vars)

- [ ] Check `.env` files for:
  - [ ] `PEXELS_API_KEY`
  - [ ] `UNSPLASH_ACCESS_KEY`
- [ ] Document in archive README
- [ ] Remove from `.env` files (or comment out)
- [ ] Verify: App works without these variables

**✅ CHECKPOINT**: App works without Photo-harvesting env vars.

**COMMIT POINT**:
```bash
git add .env* ARCHIVED_PHOTO_HARVESTING/README.md
git commit -m "refactor: Remove Photo-harvesting environment variables"
```

---

### Step 5.7: Update Documentation
**Time**: 1 hour  
**Risk**: Low (documentation only)

- [ ] Remove Photo-harvesting references from:
  - [ ] Pipeline documentation
  - [ ] Image generation documentation
  - [ ] API documentation
- [ ] Update process documentation
- [ ] Add note about Photo-harvesting deprecation

**✅ CHECKPOINT**: Documentation updated, no Photo-harvesting references.

**COMMIT POINT**:
```bash
git add docs/
git commit -m "docs: Remove Photo-harvesting references from documentation"
```

---

## STAGE 6: Final Testing & Validation

### Step 6.1: Comprehensive Testing
**Time**: 2-3 hours  
**Risk**: Low (testing only)

**Recipe Post Workflow**:
- [ ] Generate header image
- [ ] Optimize header image
- [ ] Preview post
- [ ] Publish post
- [ ] Verify: Header image appears
- [ ] Verify: No Photo-harvesting references
- [ ] Verify: Author displays correctly

**Theme Post Workflow**:
- [ ] Generate header image
- [ ] Optimize header image
- [ ] Preview post
- [ ] Publish post
- [ ] Verify: Header image appears
- [ ] Verify: No Photo-harvesting references
- [ ] Verify: Author displays correctly

**Comparison**:
- [ ] Recipe workflow = Theme workflow (identical behavior)
- [ ] No recipe-specific conditionals in code
- [ ] No Photo-harvesting code accessible

**✅ CHECKPOINT**: All workflows work identically, no differences.

---

### Step 6.2: Data Validation
**Time**: 30 minutes  
**Risk**: Low (read-only)

- [ ] Run all validation queries:
  - [ ] No orphaned references
  - [ ] All data in `images` table
  - [ ] No Photo-harvesting data in use
- [ ] Verify: Database state is clean

**✅ CHECKPOINT**: Database validation passes.

---

### Step 6.3: Code Validation
**Time**: 30 minutes  
**Risk**: Low (read-only)

- [ ] Search for remaining `image` table references:
  ```bash
  grep -r "FROM image\b\|JOIN image\b" --include="*.py" --include="*.sql" | grep -v "ARCHIVED\|migrations" | wc -l
  ```
  - [ ] Should be 0 (or only in migration scripts)
- [ ] Search for Photo-harvesting references:
  ```bash
  grep -r "photo.*harvest\|Photo-harvesting\|selected_landscape" --include="*.py" --include="*.js" | grep -v "ARCHIVED" | wc -l
  ```
  - [ ] Should be 0 (or only in archive)
- [ ] Search for recipe-specific conditionals in preview/publishing:
  ```bash
  grep -r "if.*recipe\|recipe.*if" blueprints/header.py blueprints/launchpad/publishing.py blog-launchpad/clan_publisher.py | grep -v "author_name\|title" | wc -l
  ```
  - [ ] Should be 0 (or only for author/title if kept separate)

**✅ CHECKPOINT**: No unwanted references remain.

---

## STAGE 7: Cleanup

### Step 7.1: Remove `image` Table
**Time**: 30 minutes  
**Risk**: High (drops table)

- [ ] **FINAL VERIFICATION**:
  - [ ] All data migrated
  - [ ] All code updated
  - [ ] All tests pass
  - [ ] No references to `image` table
- [ ] Run drop table script:
  ```sql
  DROP TABLE IF EXISTS image CASCADE;
  ```
- [ ] Verify: Table dropped
- [ ] Test: App still works

**✅ CHECKPOINT**: `image` table removed, app works.

**COMMIT POINT**:
```bash
git add migrations/
git commit -m "migration: Remove image table (migration complete)"
```

---

### Step 7.2: Final Documentation
**Time**: 1 hour  
**Risk**: Low (documentation only)

- [ ] Update schema documentation
- [ ] Update process documentation
- [ ] Create migration summary
- [ ] Update changelog

**✅ CHECKPOINT**: Documentation complete.

**COMMIT POINT**:
```bash
git add docs/
git commit -m "docs: Update documentation for unified schema and process"
```

---

### Step 7.3: Final Commit & Tag
**Time**: 15 minutes  
**Risk**: Low (git operations)

- [ ] Review all changes:
  ```bash
  git log --oneline [since start]
  ```
- [ ] Create summary commit message
- [ ] Final commit if needed
- [ ] Tag release:
  ```bash
  git tag -a v[version] -m "Unified image schema and process, Photo-harvesting deprecated"
  ```

**✅ CHECKPOINT**: All changes committed and tagged.

---

## Post-Implementation Checklist

### Immediate (Day 1)
- [ ] Monitor logs for errors
- [ ] Test published posts on clan.com
- [ ] Verify header images display correctly
- [ ] Check for any user-reported issues

### Short-term (Week 1)
- [ ] Monitor for any edge cases
- [ ] Verify no performance degradation
- [ ] Check database performance
- [ ] Review error logs

### Medium-term (Month 1)
- [ ] Verify no regressions
- [ ] Confirm process unification working
- [ ] Confirm Photo-harvesting fully removed
- [ ] Update team documentation

---

## Rollback Procedures

### If Issues Found During Implementation

**Stage 1-2 (Data/Code Migration)**:
```bash
# Restore database from backup
psql -d blog < backup_file.sql

# Revert code changes
git reset --hard [commit before migration]
```

**Stage 4-5 (Process Unification/Photo-harvesting)**:
```bash
# Revert code changes
git reset --hard [commit before changes]

# Restore Photo-harvesting files from archive (if needed)
cp ARCHIVED_PHOTO_HARVESTING/code/utils/* utils/
cp ARCHIVED_PHOTO_HARVESTING/code/blueprints/* blueprints/
# etc.
```

---

## Testing Reminders

**After Each File Change**:
- [ ] Test the specific functionality changed
- [ ] Check logs for errors
- [ ] Verify no regressions

**After Each Stage**:
- [ ] Run full test suite
- [ ] Test both recipe and theme posts
- [ ] Verify no differences between post types
- [ ] Check for Photo-harvesting references

**Before Committing**:
- [ ] All tests pass
- [ ] No errors in logs
- [ ] Code reviewed (if working with team)

---

## Success Validation

### Schema Migration ✅
- [ ] All data in `images` table
- [ ] All code uses `images` table
- [ ] `image` table removed
- [ ] No references to `image` table

### Process Unification ✅
- [ ] Recipe and theme previews identical
- [ ] Recipe and theme publishing identical
- [ ] No recipe-specific conditionals (except author/title if kept)
- [ ] Single publishing endpoint

### Photo-harvesting Deprecation ✅
- [ ] All Photo-harvesting code archived
- [ ] All Photo-harvesting code removed
- [ ] All Photo-harvesting data archived
- [ ] No Photo-harvesting references in codebase
- [ ] App works without Photo-harvesting

---

## Notes

- **Test frequently** - Don't wait until end
- **Commit often** - Small, logical commits
- **Verify at checkpoints** - Don't skip validation
- **Document issues** - Note any problems found
- **Ask for help** - If stuck, don't proceed blindly

---

## Estimated Timeline

- **Stage 1**: 2-4 hours
- **Stage 2**: 4-8 hours
- **Stage 3**: 2-3 hours
- **Stage 4**: 6-10 hours
- **Stage 5**: 4-6 hours
- **Stage 6**: 3-4 hours
- **Stage 7**: 1-2 hours

**Total**: 22-37 hours

---

## Ready to Start?

1. ✅ Review this implementation plan
2. ✅ Backup database
3. ✅ Create git branch
4. ✅ Start with Stage 1, Step 1.1
5. ✅ Follow checkpoints and commit points
6. ✅ Test at each stage
7. ✅ Don't skip validation steps

Good luck! 🚀

