# Database Schema Analysis: Header Images

## Tables Involved

### `post` Table
**Relevant Columns**:
- `header_image_id` (INTEGER, FK to `image.id` or `images.id`)
- `header_image_caption` (TEXT)
- `header_image_title` (TEXT)
- `header_image_width` (INTEGER)
- `header_image_height` (INTEGER)
- `recipe_week_number` (INTEGER, NULL for non-recipe posts)

**Issues**:
1. ⚠️ **RISK**: `header_image_id` can point to either `image.id` or `images.id`
   - No FK constraint specifies which table
   - Creates ambiguity in queries
2. ⚠️ **RISK**: Metadata stored in `post` table (caption, title, width, height)
   - Duplicates data that should be in `images` table
   - Risk of inconsistency

### `image` Table (OLD SCHEMA - Singular)
**Relevant Columns**:
- `id` (SERIAL PRIMARY KEY)
- `path` (VARCHAR) - **Note**: Not `file_path`
- `filename` (VARCHAR)
- `alt_text` (TEXT)
- `caption` (TEXT)
- `image_prompt` (TEXT)

**Status**: Legacy table, being phased out

### `images` Table (NEW SCHEMA - Plural)
**Relevant Columns**:
- `id` (SERIAL PRIMARY KEY)
- `file_path` (VARCHAR) - **Note**: Different column name than `image.path`
- `filename` (VARCHAR)
- `original_filename` (VARCHAR)
- `alt_text` (TEXT)
- `caption` (TEXT)
- `image_prompt` (TEXT)
- `width` (INTEGER)
- `height` (INTEGER)

**Status**: Current schema, should be used for new records

### `post_images` Table (LINKING TABLE)
**Purpose**: Links posts to images with type information.

**Relevant Columns**:
- `id` (SERIAL PRIMARY KEY)
- `post_id` (INTEGER, FK to `post.id`)
- `image_id` (INTEGER, FK to `images.id` or `image.id`)
- `image_type` (VARCHAR) - Values: `'header_optimized'`, `'header_watermarked'`, `'section_optimized'`, etc.
- `section_id` (INTEGER, FK to `post_section.id`, NULL for header images)

**Critical Constraints**:
- `UNIQUE(post_id, image_type, section_id)` - Prevents duplicate links
- `section_id IS NULL` for header images

**Issues**:
1. ⚠️ **HIGH RISK**: `image_id` can point to either `image.id` or `images.id`
   - No FK constraint specifies which table
   - Queries must check both tables
2. ⚠️ **RISK**: No validation that `image_type` matches actual image type
   - Could have `header_optimized` pointing to raw image

## Query Patterns

### Finding Header Image (Current Implementation)

**Pattern 1: New Schema (Preferred)**
```sql
SELECT i.file_path, i.filename, i.alt_text, i.caption, i.width, i.height
FROM post_images pi
JOIN images i ON pi.image_id = i.id
WHERE pi.post_id = %s 
  AND pi.section_id IS NULL 
  AND pi.image_type = 'header_optimized'
LIMIT 1
```

**Pattern 2: Old Schema (Fallback)**
```sql
SELECT i.path as file_path, i.filename, i.alt_text, i.caption, NULL as width, NULL as height
FROM post_images pi
JOIN image i ON pi.image_id = i.id
WHERE pi.post_id = %s 
  AND pi.section_id IS NULL 
  AND pi.image_type = 'header_optimized'
LIMIT 1
```

**Pattern 3: Direct FK (Legacy)**
```sql
SELECT i.path, i.filename, i.alt_text, i.caption
FROM post p
JOIN image i ON p.header_image_id = i.id
WHERE p.id = %s
```

## Schema Inconsistencies

### Issue 1: Dual Schema Support
**Problem**: Code must support both `image` and `images` tables indefinitely.

**Impact**:
- More complex queries (must check both tables)
- Risk of missing data if query only checks one table
- Maintenance burden

**Current State**: 
- New code uses `images` table
- Old code uses `image` table
- Backfill script uses `image` table

### Issue 2: Column Name Mismatch
**Problem**: 
- `image.path` vs `images.file_path`
- Different column names for same concept

**Impact**:
- Queries must handle both column names
- Code must normalize column names
- Risk of bugs if wrong column name used

### Issue 3: Missing FK Constraints
**Problem**: `post.header_image_id` and `post_images.image_id` have no FK constraints specifying which table.

**Impact**:
- Database can't enforce referential integrity
- Risk of orphaned records
- Queries must handle both tables

### Issue 4: Metadata Duplication
**Problem**: Header image metadata stored in both `post` table and `images`/`image` table.

**Impact**:
- Risk of inconsistency
- Unclear which is source of truth
- More complex updates

## Migration Status

### Completed
- ✅ `images` table created
- ✅ `post_images` linking table created
- ✅ New code writes to `images` table

### In Progress
- ⚠️ Old code still uses `image` table
- ⚠️ Backfill script uses `image` table
- ⚠️ Some queries check both tables

### Not Started
- ❌ Migration of existing `image` records to `images` table
- ❌ Removal of `image` table
- ❌ FK constraints to specify which table

## Recommendations

1. **IMMEDIATE**:
   - Document which posts use which schema
   - Add FK constraints (even if they allow both tables temporarily)
   - Standardize on `file_path` column name in queries

2. **SHORT TERM**:
   - Create migration script to move all `image` records to `images` table
   - Update all queries to use `images` table only
   - Remove `image` table after migration

3. **MEDIUM TERM**:
   - Consolidate metadata storage (remove duplication)
   - Add validation that `image_type` matches actual image type
   - Add database-level constraints for data integrity

