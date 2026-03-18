# Database Schema Audit - Week Persistence V2

## Current State Analysis

### calendar_schedule Table Evolution

The `calendar_schedule` table has evolved through multiple migrations with conflicting structures:

#### Migration 1: `create_calendar_system.sql` (Original)
```sql
CREATE TABLE calendar_schedule (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    idea_id INTEGER REFERENCES calendar_ideas(id) ON DELETE CASCADE,
    event_id INTEGER REFERENCES calendar_events(id) ON DELETE CASCADE,
    post_id INTEGER REFERENCES post(id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'planned',
    scheduled_date DATE,
    notes TEXT,
    is_override BOOLEAN DEFAULT FALSE,
    original_idea_id INTEGER REFERENCES calendar_ideas(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CHECK (idea_id IS NOT NULL OR event_id IS NOT NULL)
);
```
**Indexes:**
- `idx_calendar_schedule_year_week` ON (year, week_number)
- `idx_calendar_schedule_status` ON (status)

**Issues:**
- No unique constraint on (year, week_number)
- Requires idea_id OR event_id (check constraint)
- Allows multiple entries per week

#### Migration 2: `create_calendar_themes_table.sql` (Theme Support Added)
```sql
ALTER TABLE calendar_schedule ADD COLUMN IF NOT EXISTS theme_id INTEGER REFERENCES calendar_themes(id) ON DELETE SET NULL;
```
**Changes:**
- Added `theme_id` column
- Copied theme references from `idea_id` to `theme_id` where appropriate

#### Migration 3: `cleanup_calendar_schedule_table.sql` (Simplified)
```sql
DROP TABLE calendar_schedule CASCADE;
CREATE TABLE calendar_schedule (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    post_id INTEGER REFERENCES post(id) ON DELETE SET NULL,
    scheduled_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```
**Changes:**
- Removed `idea_id`, `event_id`, `status`, `notes`, `is_override`, `original_idea_id`
- Only kept date and post-related fields
- **This migration DROPS the table, so if it ran, all previous structure is gone**

**Current State (Likely):**
The actual current state depends on which migrations ran and in what order. Based on code references, the current table likely has:
- `id`, `year`, `week_number`, `post_id`, `scheduled_date`, `created_at`, `updated_at`
- Possibly `theme_id` (from migration 2)
- Possibly `idea_id` (if migration 3 didn't run, or was added back)

### calendar_ideas Table
```sql
CREATE TABLE calendar_ideas (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL, -- 1-52 (perpetual, NO year)
    idea_title VARCHAR(255) NOT NULL,
    idea_description TEXT,
    seasonal_context TEXT,
    content_type VARCHAR(50),
    priority INTEGER DEFAULT 1, -- Note: may be VARCHAR in some migrations
    tags JSONB,
    is_recurring BOOLEAN DEFAULT TRUE,
    can_span_weeks BOOLEAN DEFAULT FALSE,
    max_weeks INTEGER DEFAULT 1,
    -- Additional columns from later migrations:
    is_evergreen BOOLEAN DEFAULT FALSE,
    evergreen_frequency VARCHAR(20) DEFAULT 'low-frequency',
    last_used_date DATE,
    usage_count INTEGER DEFAULT 0,
    evergreen_notes TEXT,
    sources JSONB DEFAULT '[]'::jsonb,
    important_notes JSONB DEFAULT '[]'::jsonb,
    item_classification VARCHAR(50) -- 'idea' or 'theme' (from add_item_classification.sql)
);
```
**Indexes:**
- `idx_calendar_ideas_week` ON (week_number)

**Key Points:**
- NO `year` column - ideas are perpetual
- Has `item_classification` to distinguish themes from ideas
- Themes were migrated to `calendar_themes` table

### calendar_themes Table
```sql
CREATE TABLE calendar_themes (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL, -- 1-52 (perpetual, NO year)
    theme_title VARCHAR(255) NOT NULL,
    theme_description TEXT,
    seasonal_context TEXT,
    priority VARCHAR(20) DEFAULT 'random' CHECK (priority IN ('random', 'mandatory')),
    tags JSONB,
    is_recurring BOOLEAN DEFAULT TRUE,
    can_span_weeks BOOLEAN DEFAULT FALSE,
    max_weeks INTEGER DEFAULT 1,
    is_evergreen BOOLEAN DEFAULT FALSE,
    evergreen_frequency VARCHAR(20) DEFAULT 'low-frequency',
    last_used_date DATE,
    usage_count INTEGER DEFAULT 0,
    evergreen_notes TEXT,
    sources JSONB DEFAULT '[]'::jsonb,
    important_notes JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```
**Indexes:**
- `idx_calendar_themes_week_number` ON (week_number)
- `idx_calendar_themes_priority` ON (priority)
- `idx_calendar_themes_evergreen` ON (is_evergreen)

**Key Points:**
- NO `year` column - themes are perpetual
- Similar structure to `calendar_ideas` but separate table

### calendar_events Table
```sql
CREATE TABLE calendar_events (
    id SERIAL PRIMARY KEY,
    event_title VARCHAR(255) NOT NULL,
    event_description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    week_number INTEGER, -- Calculated from start_date
    year INTEGER NOT NULL,
    content_type VARCHAR(50),
    priority INTEGER DEFAULT 1,
    tags JSONB,
    is_recurring BOOLEAN DEFAULT FALSE,
    can_span_weeks BOOLEAN DEFAULT FALSE,
    max_weeks INTEGER DEFAULT 1,
    advance_notice INTEGER, -- Days of advance notice (from add_event_advance_notice.sql)
    important_notes JSONB DEFAULT '[]'::jsonb, -- From add_important_notes.sql
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```
**Indexes:**
- `idx_calendar_events_year_week` ON (year, week_number)

**Key Points:**
- HAS `year` column - events are year-specific
- `week_number` is calculated, not enforced

### calendar_weeks Table
```sql
CREATE TABLE calendar_weeks (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL, -- 1-52
    year INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    month_name VARCHAR(10) NOT NULL,
    is_current_week BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(week_number, year) -- Only unique constraint in entire calendar system!
);
```
**Indexes:**
- `idx_calendar_weeks_year_week` ON (year, week_number)

**Key Points:**
- Master reference table
- Only table with proper unique constraint on (year, week_number)

## Foreign Key Relationships

### calendar_schedule
- `post_id` → `post(id)` ON DELETE SET NULL
- `theme_id` → `calendar_themes(id)` ON DELETE SET NULL (if column exists)
- `idea_id` → `calendar_ideas(id)` ON DELETE CASCADE (if column exists, from original)
- `event_id` → `calendar_events(id)` ON DELETE CASCADE (if column exists, from original)

### calendar_ideas
- `id` referenced by:
  - `calendar_idea_categories(idea_id)`
  - `calendar_schedule(idea_id)` (if exists)
  - `calendar_schedule(original_idea_id)` (if exists)

### calendar_themes
- `id` referenced by:
  - `calendar_schedule(theme_id)` (if exists)

### calendar_events
- `id` referenced by:
  - `calendar_event_categories(event_id)`
  - `calendar_schedule(event_id)` (if exists)

## Current Issues

### 1. Schema Inconsistency
- Multiple migrations with conflicting structures
- Unknown which columns actually exist in production
- `cleanup_calendar_schedule_table.sql` drops the table, so if it ran, many columns are gone

### 2. Missing Constraints
- **NO unique constraint on `calendar_schedule(year, week_number)`** - allows duplicates
- **NO unique constraint on `calendar_schedule(year, week_number, post_id)`** - same post can be scheduled multiple times
- **NO constraint enforcing theme selection** - no way to ensure one selected theme per week
- **NO check constraint validating `calendar_events.week_number` matches `start_date`**

### 3. Column Ambiguity
- `calendar_schedule` may or may not have:
  - `theme_id` (added in migration 2)
  - `idea_id` (removed in migration 3, but code still references it)
  - `event_id` (removed in migration 3)
  - `status` (removed in migration 3)
  - Other fields from original schema

### 4. Data Model Confusion
- `calendar_ideas` has NO `year` but is used in `calendar_schedule` which requires `year`
- `calendar_themes` has NO `year` but is used in `calendar_schedule` which requires `year`
- Perpetual ideas/themes vs year-specific scheduling creates ambiguity

## Required Changes for V2 Architecture

### New Tables Needed

#### calendar_week_selection
```sql
CREATE TABLE calendar_week_selection (
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    selected_theme_id INTEGER NOT NULL REFERENCES calendar_themes(id) ON DELETE RESTRICT,
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (year, week_number),
    UNIQUE(year, week_number)
);
```
**Purpose:** One selected theme per week
**Constraints:**
- Primary key on (year, week_number) ensures one selection per week
- `selected_theme_id` NOT NULL ensures theme is required
- Foreign key to `calendar_themes`

#### calendar_week_posts
```sql
CREATE TABLE calendar_week_posts (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    post_id INTEGER NOT NULL REFERENCES post(id) ON DELETE CASCADE,
    scheduled_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(year, week_number, post_id)
);
```
**Purpose:** Multiple posts per week allowed
**Constraints:**
- Unique on (year, week_number, post_id) prevents duplicate assignments
- Foreign key to `post` with CASCADE delete
**Indexes:**
- `idx_calendar_week_posts_year_week` ON (year, week_number)
- `idx_calendar_week_posts_post_id` ON (post_id)

### Migration Requirements

1. **Determine current schema** - Query information_schema to see actual columns
2. **Migrate theme selections** - Extract theme_id selections from calendar_schedule
3. **Migrate post assignments** - Extract post_id assignments from calendar_schedule
4. **Handle conflicts** - What if multiple themes selected? (Take most recent)
5. **Preserve data** - Backup calendar_schedule before changes
6. **Rollback plan** - Ability to restore from backup if migration fails

### Columns to Deprecate

From `calendar_schedule` (if they exist):
- `idea_id` - No longer used for week persistence
- `event_id` - No longer used (events stay in calendar_events table)
- `status` - Not needed in scheduling table
- `notes` - Not needed in scheduling table
- `is_override` - Not needed
- `original_idea_id` - Not needed

**Keep:**
- `id`, `year`, `week_number`, `post_id`, `scheduled_date`, `created_at`, `updated_at`
- `theme_id` - May be needed during transition, but eventually deprecated

## Foreign Key Dependencies

### Tables That Reference calendar_schedule
- None currently (no foreign keys TO calendar_schedule)

### Tables Referenced BY calendar_schedule
- `post(id)` - Must keep for post assignments during migration
- `calendar_themes(id)` - Must keep for theme_id references during migration
- `calendar_ideas(id)` - May be removed after migration if idea_id column exists

## Index Requirements

### For calendar_week_selection
- Primary key index on (year, week_number) - automatic
- Index on selected_theme_id for reverse lookups

### For calendar_week_posts
- Index on (year, week_number) for week lookups
- Index on post_id for post lookups
- Unique index on (year, week_number, post_id) - automatic

## Migration Script Outline

```sql
-- Step 1: Check current schema
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'calendar_schedule';

-- Step 2: Backup
CREATE TABLE calendar_schedule_backup AS SELECT * FROM calendar_schedule;

-- Step 3: Create new tables
-- (calendar_week_selection and calendar_week_posts)

-- Step 4: Migrate theme selections
-- Take most recent theme_id per (year, week_number) where theme_id IS NOT NULL

-- Step 5: Migrate post assignments
-- Copy all (year, week_number, post_id, scheduled_date) where post_id IS NOT NULL

-- Step 6: Validate
-- Check data integrity, counts match, etc.
```

