# Family Profile Post Type - Integration Guide

**Date:** 2026-01-19  
**Status:** Planning & Design  
**Purpose:** Complete guide for integrating family profile posts into the blog creation system

---

## Executive Summary

Family profile posts are a new post type that will use family/clan data from the `families` table to create comprehensive blog posts about Scottish families and clans. This document outlines the complete integration requirements.

---

## Current State

### ✅ What Exists

1. **Family Data**
   - `families` table with 158+ clans
   - `families.research_data` JSONB field with comprehensive research framework
   - Family relationships (aliases, spellings, septs)
   - Family resources (images, text, JSON data)

2. **Research Framework**
   - `utils/family_research/` module
   - Fact extraction from web sources
   - Narrative generation from research data
   - Story facts processing

3. **Database Schema**
   - `families` table with all necessary fields
   - `family_aliases`, `family_spellings`, `family_septs` relationship tables
   - `family_resources` for images and text
   - `family_designs` for fabric designs

### ❌ What's Missing

1. **Post Type Integration**
   - Not in `config/post_type_substages.py`
   - Not in `post_type_config` table
   - No post creation logic

2. **Calendar Integration**
   - Not in calendar resolver
   - No schedule for family profiles
   - No calendar JSON files

3. **Automation**
   - No creation script
   - No workflow script
   - Not in background monitor

4. **Database Schema**
   - No `profile_family_id` field in `post` table
   - No link between posts and families

---

## Integration Requirements

### 1. Database Schema

#### Add Profile Family ID to Post Table

**Migration**: `migrations/add_profile_family_id_to_post.sql`

```sql
-- Add profile_family_id to post table
ALTER TABLE post 
ADD COLUMN IF NOT EXISTS profile_family_id INTEGER REFERENCES families(id) ON DELETE SET NULL;

-- Create index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_post_profile_family ON post(profile_family_id) WHERE profile_family_id IS NOT NULL;

-- Update profile_type check constraint to include 'family'
-- (May need to drop and recreate constraint if it exists)
ALTER TABLE post 
DROP CONSTRAINT IF EXISTS post_profile_type_check;

ALTER TABLE post 
ADD CONSTRAINT post_profile_type_check 
CHECK (profile_type IN ('product', 'category', 'family', NULL));
```

**Alternative**: Extend existing `profile_type` field
- Current: `profile_type IN ('product', 'category', NULL)`
- New: `profile_type IN ('product', 'category', 'family', NULL)`
- Use `profile_family_id` to link to families table

---

### 2. Post Type Configuration

#### Add to `config/post_type_substages.py`

```python
'family_profile': {
    'planning': ['taxonomy', 'family_data_review', 'topic_brainstorming', 
                 'section_structure', 'topic_allocation', 'section_titling'],
    'authoring': ['drafting', 'image_concepts', 'image_prompts', 'image_captions'],
    'imaging': ['image_generation', 'optimise'],
    'header': ['title_summary', 'header_image', 'seo_meta', 'publishing_details', 'final_review']
}
```

**Key Differences from Other Profiles:**
- Has `family_data_review` substage (similar to `product_data_review`)
- Uses family research data instead of product/category data
- May include research stage (like themed posts) if needed

---

#### Add to `post_type_config` Table

```sql
INSERT INTO post_type_config (
    post_type, 
    default_publication_day, 
    default_publication_time, 
    timezone, 
    is_active, 
    description
) VALUES (
    'family_profile',
    4,  -- Thursday (to match other profiles)
    '14:00:00',
    'Europe/London',
    TRUE,
    'Family/Clan Profile Posts - Thursday afternoon'
) ON CONFLICT (post_type) DO UPDATE SET
    default_publication_day = EXCLUDED.default_publication_day,
    default_publication_time = EXCLUDED.default_publication_time,
    updated_at = NOW();
```

---

### 3. Calendar Integration

#### Add to Calendar Resolver

**File**: `utils/calendar_resolver.py`

Add to `get_category_config()`:

```python
if category == "family_profile":
    return {
        "table": "families",  # Or use calendar_family_sequence if created
        "id_column": "id",
        "position_column": "position",  # If using sequence table
        "extra_filter": ("is_clan = TRUE", []),  # Only clans, or all families?
    }
```

**Decision Needed**: 
- Use `families` table directly?
- Or create `calendar_family_sequence` table (like `calendar_profile_sequence`)?

**Recommended**: Create `calendar_family_sequence` table for consistency

---

#### Create Calendar Schedule

**Option A: JSON Schedule Files** (Like themes/recipes)

Create `data/calendar/schedule/family_profile/2026.json`:
```json
[
  {"week": 1, "item_id": 123, "position": 1, "title": "Abernethy"},
  {"week": 2, "item_id": 456, "position": 1, "title": "Adair"},
  ...
]
```

**Option B: Database Table** (Like profile sequence)

Create `calendar_family_sequence` table:
```sql
CREATE TABLE calendar_family_sequence (
    id SERIAL PRIMARY KEY,
    family_id INTEGER REFERENCES families(id),
    position INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Recommended**: Option B (Database Table) - more flexible, easier to manage

---

#### Integrate with `resolve_item_for_week()`

**File**: `utils/calendar_resolver.py`

Update `resolve_item_for_week()` to support `family_profile` category:

```python
def resolve_item_for_week(category: str, year: int, week_number: int, ...):
    # Add family_profile handling
    if category == 'family_profile':
        # Resolve from calendar_family_sequence or families table
        # Use cyclic position logic
        # Return family data
```

---

### 4. Post Creation Logic

#### Create Family Profile Post Function

**Location**: `blueprints/planning_api_posts.py` or new module

```python
def create_family_profile_post(family_id: int, year: int, week_number: int) -> Optional[int]:
    """
    Create a family profile post from family data
    """
    # 1. Get family data from families table
    # 2. Check if post already exists
    # 3. Create post with profile_family_id
    # 4. Set profile_type='family'
    # 5. Set idea_seed from family name
    # 6. Schedule in calendar_week_items
    # 7. Return post_id
```

**Key Steps:**
1. Query `families` table for family data
2. Extract family name for title
3. Create post with `profile_family_id` and `profile_type='family'`
4. Set `idea_seed` to family name
5. Schedule in `calendar_week_items` with correct weekday

---

### 5. Planning Stage Integration

#### Family Data Review Substage

**Location**: `blueprints/planning_calendar_clean.py` or new module

**Route**: `/planning/posts/<post_id>/calendar/family-data-review?year=<year>&week=<week>`

**Purpose**: Review family research data before drafting

**What it does:**
1. Loads family data from `families` table
2. Displays `research_data` JSONB field
3. Shows family relationships (septs, aliases, spellings)
4. Allows user to review and confirm data
5. Prepares data for drafting stage

**Data Display:**
- Family name and basic info
- Research data (etymology, early records, distribution, etc.)
- Story facts (key figures, turning points, places, legends)
- Family relationships
- Resources (images, text)

---

#### Use Family Research Data in Drafting

**Integration**: When drafting family profile posts, use:
- `utils/family_research/narrative.py::generate_narrative()` - Generate narrative from research data
- `utils/family_research/db_utils.py::get_family_context()` - Get family context
- `families.research_data` JSONB - Comprehensive research framework

**Drafting Process:**
1. Load family research data
2. Use narrative generator to create draft content
3. Structure content into sections
4. Add family-specific details (heraldry, septs, etc.)

---

### 6. Automation Scripts

#### Automated Family Profile Creator

**File**: `scripts/automated_family_profile_creator.py` (Future)

**Structure**: Similar to `automated_blog_post_creator.py`

**Key Functions:**
- `create_family_profile_post(family_item, year, week_number)`
- Resolve families from calendar schedule
- Create posts with `profile_family_id`
- Schedule in calendar

---

#### Automated Family Profile Workflow

**File**: `scripts/automated_family_profile_workflow.py` (Future)

**Structure**: Similar to `automated_blog_post_workflow.py`

**Key Differences:**
- Uses family research data instead of product/category data
- May include research stage (if family research needed)
- Uses family-specific narrative generation

---

### 7. UI Integration

#### Planning Stage UI

**Family Data Review Page**:
- Display family information
- Show research data
- Allow data confirmation
- Link to family research tools

**Similar to**: Product data review page (`/planning/posts/<post_id>/calendar/product-data-review`)

---

#### One-Click Publication Support

**Update**: `config/post_type_substages.py` to include `family_profile`

**Update**: One-click UI to support family profiles

**Update**: Pipeline display to show family profile stages

---

## Process Flow

### Manual Creation (Initial)

```
1. Calendar View
   ↓ Select family from calendar
2. Family Data Review
   ↓ Review and confirm family data
3. Taxonomy Assignment
   ↓ Assign content category/type/format
4. Topic Brainstorming
   ↓ Generate topics from family data
5. Section Structure Design
   ↓ Design content structure
6. Topic Allocation
   ↓ Allocate topics to sections
7. Section Titling
   ↓ Create section titles
8. Drafting
   ↓ Generate draft using family research data
9. Image Concepts/Prompts/Captions
   ↓ Develop images
10. Image Generation
   ↓ Generate AI images
11. Image Optimization
   ↓ Optimize images
12. Title & Summary
   ↓ Generate title and summary
13. Header Image
   ↓ Create header image
14. SEO Meta
   ↓ Generate SEO metadata
15. Publishing Details
   ↓ Set publication details
16. Final Review
   ↓ Review and publish
```

### Automated Creation (Future)

```
Calendar Schedule
  ↓ (1 week ahead)
automated_family_profile_creator.py
  ↓ Creates post with profile_family_id
automated_family_profile_workflow.py
  ↓ Executes workflow stages
Status: 'ready'
  ↓ (manual review/publication)
Publication
```

---

## Data Flow

### Family Data → Post Creation

```
families table
  ↓ (family_id)
Post creation
  ↓ (profile_family_id set)
Post record created
  ↓ (status='draft')
Calendar scheduling
  ↓ (calendar_week_items)
Scheduled for week
```

### Family Research Data → Drafting

```
families.research_data (JSONB)
  ↓ (loaded)
Family research framework
  ↓ (utils/family_research/)
Narrative generation
  ↓ (generate_narrative())
Draft content
  ↓ (stored in post_section)
Ready for review
```

---

## Key Differences from Other Profile Types

| Aspect | Product Profile | Surname Profile | Family Profile |
|--------|----------------|-----------------|----------------|
| **Data Source** | `clan_products` | `clan_categories` | `families` |
| **ID Field** | `profile_product_id` | `profile_category_id` | `profile_family_id` |
| **Review Substage** | `product_data_review` | Category data review | `family_data_review` |
| **Research Data** | Product specs | Category heritage | `research_data` JSONB |
| **Narrative Source** | Product description | Category data | Family research framework |
| **Special Features** | Product images, SKU | Category hierarchy | Family relationships, septs |

---

## Implementation Checklist

### Phase 1: Database & Schema
- [ ] Create migration: `add_profile_family_id_to_post.sql`
- [ ] Run migration
- [ ] Verify schema changes

### Phase 2: Post Type Configuration
- [ ] Add `family_profile` to `config/post_type_substages.py`
- [ ] Add to `post_type_config` table
- [ ] Test post type detection

### Phase 3: Calendar Integration
- [ ] Create `calendar_family_sequence` table (or use JSON)
- [ ] Add `family_profile` to calendar resolver
- [ ] Test calendar resolution

### Phase 4: Post Creation
- [ ] Create `create_family_profile_post()` function
- [ ] Test post creation
- [ ] Verify calendar scheduling

### Phase 5: Planning Stage
- [ ] Create family data review substage
- [ ] Create route and template
- [ ] Test data review flow

### Phase 6: Drafting Integration
- [ ] Integrate family research framework
- [ ] Test narrative generation
- [ ] Verify draft content

### Phase 7: Automation (Future)
- [ ] Create `automated_family_profile_creator.py`
- [ ] Create `automated_family_profile_workflow.py`
- [ ] Add to background monitor
- [ ] Test automation

---

## Research Data Structure

### `families.research_data` JSONB Field

The research data follows a comprehensive schema:

```json
{
  "surname": "Abernethy",
  "etymology": {...},
  "early_records": {...},
  "distribution_historic": {...},
  "distribution_modern": {...},
  "clan_association": {...},
  "heraldry": {...},
  "variants": {...},
  "migration": {...},
  "notables": {...},
  "story_facts": {
    "key_figures": [...],
    "turning_points": [...],
    "places": [...],
    "legends_and_dark_episodes": [...],
    "themes": [...]
  },
  "genealogy_resources": [...]
}
```

**Usage in Post Creation:**
- Extract data for drafting
- Use narrative generator to create content
- Include specific details (names, dates, places)
- Reference family relationships

---

## Family Research Framework Integration

### Available Functions

**From `utils/family_research/`:**

1. **`get_family_context(family_id)`**
   - Gets family data from database
   - Returns family information and relationships

2. **`generate_narrative(surname, surname_json, llm_service, word_target)`**
   - Generates narrative from research data
   - Uses LLM to create comprehensive article
   - Returns HTML-formatted content

3. **`extract_facts_from_chunk(surname, chunk_text, existing_story_facts, llm_service)`**
   - Extracts story facts from text chunks
   - Used for research data population

4. **`perform_web_search(query, max_results)`**
   - Performs web search for family research
   - Returns search results

### Usage in Drafting

```python
from utils.family_research import get_family_context, generate_narrative
from utils.family_research.db_utils import get_family_context

# Get family data
family_context = get_family_context(family_id)
family_name = family_context['name']
research_data = family_context['research_data']

# Generate narrative
narrative = generate_narrative(
    surname=family_name,
    surname_json=research_data,
    llm_service=llm_service,
    word_target=2500
)

# Use narrative as draft content
```

---

## Calendar Schedule Options

### Option A: Database Table (Recommended)

**Table**: `calendar_family_sequence`

```sql
CREATE TABLE calendar_family_sequence (
    id SERIAL PRIMARY KEY,
    family_id INTEGER NOT NULL REFERENCES families(id),
    position INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(family_id, position)
);

CREATE INDEX idx_calendar_family_sequence_position ON calendar_family_sequence(position);
CREATE INDEX idx_calendar_family_sequence_family ON calendar_family_sequence(family_id);
```

**Usage:**
- Similar to `calendar_profile_sequence`
- Position-based cyclic scheduling
- Easy to reorder and manage

---

### Option B: JSON Schedule Files

**Location**: `data/calendar/schedule/family_profile/2026.json`

**Format**: Same as theme/recipe JSON files

**Usage:**
- Pre-computed schedule
- Cyclic position logic
- Consistent with other calendar items

---

## Post Type Detection

### Detection Logic

**In `utils/taxonomy_helpers.py::get_post_type()`:**

```python
def get_post_type(post_id: int) -> str:
    # Check for family profile
    if post.profile_family_id is not None:
        return 'family_profile'
    
    # Existing logic for other types...
```

---

## Publication Schedule

### Default Configuration

- **Publication Day**: Thursday (4)
- **Publication Time**: 14:00
- **Timezone**: Europe/London

**Rationale**: Matches other profile posts (product and surname profiles)

---

## Automation Script Design

### `automated_family_profile_creator.py`

**Structure**: Similar to `automated_blog_post_creator.py`

**Key Functions:**
```python
def create_family_profile_posts(self, days_ahead: int = 7):
    # Get upcoming weeks
    # For each week:
    #   - Resolve family from calendar
    #   - Check if post exists
    #   - Create post with profile_family_id
    #   - Schedule in calendar_week_items
```

---

### `automated_family_profile_workflow.py`

**Structure**: Similar to `automated_blog_post_workflow.py`

**Key Differences:**
- Uses family research data
- May include research stage
- Uses family-specific narrative generation

---

## Testing Strategy

### Unit Tests
- Test post creation with family_id
- Test family data loading
- Test narrative generation
- Test calendar scheduling

### Integration Tests
- Test full workflow from creation to ready
- Test with real family data
- Test calendar resolution
- Test automation scripts

### Manual Testing
- Create family profile post manually
- Review family data
- Generate draft content
- Verify publication

---

## Related Documentation

- `docs/families_research_implementation_plan.md` - Family research process
- `docs/families_database.md` - Families database schema
- `docs/families_research_data_schema.md` - Research data structure
- `docs/BLOG_POST_AUTOMATION_GOALS.md` - Automation goals
- `docs/BLOG_POST_CREATION_PROCESS.md` - Creation process

---

## Next Steps

1. **Database Schema** - Create migration for `profile_family_id`
2. **Post Type Config** - Add to `post_type_substages.py` and `post_type_config`
3. **Calendar Integration** - Add to resolver and create schedule
4. **Post Creation** - Implement creation function
5. **Planning Stage** - Create family data review substage
6. **Drafting Integration** - Integrate family research framework
7. **Automation** - Create automation scripts (future)

---

**Last Updated:** 2026-01-19
