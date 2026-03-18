# Research System - Database Table Analysis

**Date:** 2026-01-19  
**Purpose:** Analyze existing database tables to determine if they can support the new research system, or if new tables are needed

---

## Executive Summary

**Good News:** We have suitable existing tables that can be used for the research system. However, the current `recipe_research` column in `post_development` is focused on ingredients/method research, not the expanded background research we need. **Recommendation:** Extend existing tables rather than creating new ones.

---

## Existing Tables Analysis

### 1. `post_development` Table

#### Current Structure
- **Primary Key:** `id`
- **Foreign Key:** `post_id` (references `post.id`)
- **Unique Constraint:** `post_id` (one-to-one with posts)

#### Relevant Columns for Research

| Column | Type | Current Use | Potential Use for Research |
|--------|------|-------------|---------------------------|
| `recipe_research` | JSONB | Stores ingredients/method research | **Can be extended** to include background research topics |
| `section_structure` | JSON | Section planning structure | Not directly relevant |
| `topic_allocation` | JSON | Topic allocation data | Not directly relevant |
| `refined_topics` | JSON | Refined topic data | Not directly relevant |

#### Current `recipe_research` Usage

From `blueprints/recipes_research.py`, the current structure appears to be:
```json
{
  "authentic_ingredients": [...],
  "authentic_method": {...},
  "regional_variations": [...],
  "sources": [...]
}
```

**Limitation:** This is focused on recipe ingredients/method, not the expanded background research (origins, geographic spread, evolution, cultural significance, modern incarnations).

**Recommendation:** Extend `recipe_research` JSONB structure to include background research topics.

---

### 2. `post_section` Table

#### Current Structure
- **Primary Key:** `id`
- **Foreign Key:** `post_id` (references `post.id`)
- **Indexes:** 
  - `idx_post_section_section_type` (on `section_type`)
  - `idx_post_section_elements` (GIN index on JSONB)

#### Relevant Columns for Research

| Column | Type | Current Use | Potential Use for Research |
|--------|------|-------------|---------------------------|
| `section_type` | VARCHAR(100) | Identifies section type (e.g., `recipe_background`) | **Perfect** - can identify background section |
| `post_section_elements` | JSONB | Stores structured section data | **Can store** research sources, facts, metadata per section |
| `draft` | TEXT | Draft content | **Can store** synthesized research paragraphs |
| `polished` | TEXT | Final polished content | **Can store** final integrated background content |
| `section_heading` | TEXT | Section title | Can display research topic label |
| `section_description` | TEXT | Section description | Can store research topic description |

#### Current Usage Pattern

From `docs/recipes/section-types.md`:
- `recipe_background` section type exists
- `post_section_elements` is used for structured data (ingredients, method steps)
- Sections are linked to posts via `post_id`

**Advantage:** This table already supports recipe sections and can store research data per section.

---

## Recommended Approach

### Option A: Extend `post_development.recipe_research` (Recommended)

**Structure:**
```json
{
  "ingredients_method_research": {
    "authentic_ingredients": [...],
    "authentic_method": {...},
    "regional_variations": [...]
  },
  "background_research": {
    "topics": [
      {
        "key": "origins",
        "label": "Origins & Early History",
        "status": "completed",
        "research_query": "earliest mentions and recorded origins of Forfar Bridie in Scotland",
        "sources": [
          {
            "title": "...",
            "url": "...",
            "domain_tier": 1,
            "reliability": "high",
            "facts_extracted": [...]
          }
        ],
        "extracted_facts": {
          "dates": [...],
          "locations": [...],
          "events": [...],
          "cultural_notes": [...]
        },
        "synthesized_content": "The Forfar Bridie first appears...",
        "completed_at": "2026-01-19T10:30:00Z"
      },
      {
        "key": "geographic_spread",
        "status": "pending",
        ...
      }
    ],
    "synthesized_background": "Combined background content from all topics..."
  }
}
```

**Pros:**
- Uses existing column
- All research data in one place
- Easy to query/update
- Maintains backward compatibility

**Cons:**
- Large JSONB structure (but PostgreSQL handles this well)
- Less normalized (but acceptable for this use case)

---

### Option B: Use `post_section` for Research Storage

**Approach:**
- Create one `post_section` record per research topic
- Use `section_type` = `recipe_background_research_origins`, `recipe_background_research_geographic_spread`, etc.
- Store research data in `post_section_elements` JSONB
- Store synthesized content in `draft` field

**Structure per section:**
```json
// post_section_elements
{
  "research_topic": "origins",
  "research_query": "...",
  "sources": [...],
  "extracted_facts": {...},
  "status": "completed"
}

// draft field
"The Forfar Bridie first appears in historical records..."
```

**Pros:**
- More normalized structure
- Can leverage existing section management UI
- Each topic is a separate record (easier to query individually)
- Can use section workflow status tracking

**Cons:**
- Creates multiple section records (one per research topic)
- Mixes research sections with content sections
- May be confusing in UI (research vs. content sections)

---

### Option C: Hybrid Approach (Best of Both Worlds)

**Use `post_development.recipe_research` for:**
- Research topic definitions and status tracking
- Source lists and extracted facts
- Research metadata

**Use `post_section` (recipe_background section) for:**
- Final synthesized background content (in `draft` field)
- Integration with drafting workflow

**Structure:**
```json
// post_development.recipe_research.background_research
{
  "topics": [
    {
      "key": "origins",
      "status": "completed",
      "sources": [...],
      "extracted_facts": {...},
      "synthesized_content": "..."
    }
  ],
  "synthesized_background": "Combined content..."
}

// post_section (where section_type = 'recipe_background')
{
  "draft": "Final background content from research",
  "post_section_elements": {
    "research_sources": [...],
    "research_topics_used": ["origins", "geographic_spread", ...]
  }
}
```

**Pros:**
- Research data separate from content
- Final content in proper section table
- Can track research separately from drafting
- Clear separation of concerns

**Cons:**
- Data split across two tables
- Need to sync research content to section

---

## Final Recommendation: **Option A (Extended JSONB)**

### Rationale

1. **Simplicity:** Single source of truth for all research data
2. **Performance:** PostgreSQL JSONB is efficient for this use case
3. **Flexibility:** Easy to add new research topics without schema changes
4. **Backward Compatibility:** Existing `recipe_research` data remains accessible
5. **Query Efficiency:** Can query research status, topics, sources all from one column

### Implementation Structure

```json
{
  "ingredients_method_research": {
    // Existing structure - keep for backward compatibility
    "authentic_ingredients": [...],
    "authentic_method": {...},
    "regional_variations": [...],
    "sources": [...]
  },
  "background_research": {
    "topics": [
      {
        "key": "origins",
        "label": "Origins & Early History",
        "status": "pending" | "researching" | "completed" | "failed",
        "research_query": "earliest mentions and recorded origins of {recipe_name} in Scotland",
        "sources": [
          {
            "title": "Source Title",
            "url": "https://...",
            "domain": "example.edu",
            "domain_tier": 1,
            "reliability": "high",
            "facts_extracted": ["fact1", "fact2"],
            "rank": 1
          }
        ],
        "extracted_facts": {
          "dates": [
            {"value": "1851", "context": "First documented", "source": "..."}
          ],
          "locations": [
            {"value": "Forfar, Angus", "context": "Origin location", "source": "..."}
          ],
          "events": [...],
          "cultural_notes": [...],
          "uncertainties": ["Some sources claim..."]
        },
        "synthesized_content": "The Forfar Bridie first appears in historical records in 1851...",
        "error_message": null,
        "created_at": "2026-01-19T10:00:00Z",
        "updated_at": "2026-01-19T10:30:00Z",
        "completed_at": "2026-01-19T10:30:00Z"
      }
    ],
    "synthesized_background": "Combined background content from all completed topics...",
    "last_updated": "2026-01-19T10:30:00Z"
  }
}
```

### Database Operations

**Query Research Status:**
```sql
SELECT 
  recipe_research->'background_research'->'topics' as topics
FROM post_development
WHERE post_id = %s;
```

**Update Research Topic:**
```sql
UPDATE post_development
SET recipe_research = jsonb_set(
  recipe_research,
  '{background_research,topics}',
  (SELECT jsonb_agg(
    CASE 
      WHEN topic->>'key' = 'origins' 
      THEN topic || '{"status": "completed"}'::jsonb
      ELSE topic
    END
  ) FROM jsonb_array_elements(recipe_research->'background_research'->'topics') topic)
)
WHERE post_id = %s;
```

**Add New Research Topic:**
```sql
UPDATE post_development
SET recipe_research = jsonb_set(
  recipe_research,
  '{background_research,topics}',
  (recipe_research->'background_research'->'topics') || '[{"key": "new_topic", ...}]'::jsonb
)
WHERE post_id = %s;
```

---

## Migration Strategy

### Step 1: Extend Existing Structure

No schema changes needed! We can extend the JSONB structure immediately.

### Step 2: Backward Compatibility

Ensure code handles both old and new structures:
```python
research_data = dev_data.get('recipe_research', {})
if isinstance(research_data, str):
    research_data = json.loads(research_data)

# Check if old structure (no background_research key)
if 'background_research' not in research_data:
    # Initialize new structure
    research_data['background_research'] = {
        'topics': [],
        'synthesized_background': None
    }
    # Preserve existing data
    research_data['ingredients_method_research'] = research_data
```

### Step 3: Index Optimization (Optional)

If we need to query research topics frequently, we can add a GIN index:
```sql
CREATE INDEX IF NOT EXISTS idx_post_development_recipe_research_background 
ON post_development USING GIN ((recipe_research->'background_research'));
```

---

## Comparison with Original Design

### Original Design (New Table)
- **Table:** `post_research`
- **Structure:** One row per research topic
- **Pros:** Normalized, easy to query individual topics
- **Cons:** New table, more complex joins

### Recommended Design (Extended JSONB)
- **Table:** `post_development.recipe_research` (existing)
- **Structure:** JSONB array of topics
- **Pros:** No schema changes, simpler queries, all data in one place
- **Cons:** Slightly more complex JSONB queries

**Verdict:** Extended JSONB is better for this use case because:
1. No migration needed
2. Research is inherently hierarchical (topics → sources → facts)
3. PostgreSQL JSONB is optimized for this pattern
4. Easier to maintain and extend

---

## Conclusion

**We can use existing tables!** The `post_development.recipe_research` JSONB column is perfect for storing the expanded background research. We just need to:

1. Extend the JSONB structure to include `background_research` section
2. Maintain backward compatibility with existing `ingredients_method_research`
3. Use the existing `post_section` table for the final `recipe_background` section content

**No new tables needed!** ✅
