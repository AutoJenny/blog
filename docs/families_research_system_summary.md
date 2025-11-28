# Families Research System - Complete Summary

## Overview

The families research system provides comprehensive web-based research for Scottish surnames and clans, populating structured JSON data across 11 research sections.

## System Components

### 1. Web Research Script (`research_family_web.py`)

**Purpose:** Performs targeted web research for each research section separately.

**Key Features:**
- Section-by-section research (11 distinct sections)
- Live web searches (Google Custom Search API or DuckDuckGo)
- Known source integration
- LLM synthesis of multiple sources
- Automatic data merging with existing research
- Post-processing to fix data structure issues
- Auto-update to database (with `--save` flag)

**Usage:**
```bash
# Research all sections
python3 scripts/research_family_web.py 6762 --save

# Research specific sections
python3 scripts/research_family_web.py 6762 --sections etymology,clan_association --save

# Save without updating database
python3 scripts/research_family_web.py 6762 --save --no-update
```

### 2. Manual Research Tool (`research_family.py`)

**Purpose:** Manual research workflow with validation and database updates.

**Key Features:**
- Generate templates
- Validate JSON
- Update database
- Context display

**Usage:**
```bash
# Show family context
python3 scripts/research_family.py 6762 --context

# Generate template
python3 scripts/research_family.py 6762 --template

# Validate JSON
python3 scripts/research_family.py 6762 --validate data/research_Abernethy_6762.json

# Update database
python3 scripts/research_family.py 6762 --update data/research_Abernethy_6762.json
```

### 3. Basic LLM Research (`research_family_llm.py`)

**Purpose:** Simple LLM-based research using training data only (not recommended for production).

**Status:** Superseded by web research system.

## Research Sections

The system researches 11 distinct sections:

1. **etymology** - Language origins, root words, name meaning
2. **early_records** - Earliest documented appearances
3. **distribution_historic** - Pre-1900 geographic distribution
4. **distribution_modern** - Current/modern distribution
5. **clan_association** - Scottish clan/sept connections
6. **heraldry** - Coats of arms, mottoes, tartans
7. **variants** - Spelling variants, language forms
8. **migration** - Movement patterns, diaspora
9. **notables** - Notable individuals
10. **cultural_notes** - Literary references, cultural associations
11. **genealogy_resources** - Family societies, research resources

## Database Structure

### Families Table
- `id` - Primary key
- `name` - Family name
- `is_clan` - Boolean flag
- `is_canonical` - Boolean flag (not a variant)
- `has_history` - Boolean flag (has existing history text)
- `is_virtual` - Boolean flag
- `research_data` - JSONB field containing all research data
- `created_at`, `updated_at` - Timestamps

### Related Tables
- `family_aliases` - Alternative names
- `family_spellings` - Spelling variant relationships
- `family_septs` - Sept relationships
- `family_resources` - Resources (images, texts, etc.)
- `family_designs` - Design associations

## UI Integration

### Family Detail Page (`/families/<id>`)

**Features:**
- Tabbed interface separating:
  - **Database Data (CSV Import)** - Original data from CSV
  - **Research Data (Web Research)** - Research data from web research
- Displays all research sections in readable format
- Shows raw JSON for reference

**Access:** `http://localhost:5000/families/6762`

## Workflow

### Recommended Workflow

1. **Initial Research:**
   ```bash
   python3 scripts/research_family_web.py <family_id> --save
   ```

2. **Review Results:**
   - Check UI at `/families/<id>`
   - Review JSON file in `data/`
   - Validate data quality

3. **Refine Specific Sections:**
   ```bash
   python3 scripts/research_family_web.py <family_id> --sections <section1,section2> --save
   ```

4. **Manual Corrections (if needed):**
   - Edit JSON file manually
   - Validate: `python3 scripts/research_family.py <id> --validate <file>`
   - Update: `python3 scripts/research_family.py <id> --update <file>`

## Data Quality

### Automatic Fixes

The system automatically fixes:
- Invalid year values (< 1000) → set to null
- Malformed array structures → converted to proper objects
- Incorrect data types → corrected (null vs 0, arrays vs null)
- Schema mismatches → mapped to correct fields

### Validation

All data is validated against:
- JSON schema structure
- Business rules (e.g., has_documented_arms matches arms array)
- Data type requirements
- Required fields

## Configuration

### Google Custom Search API (Recommended)

```bash
export GOOGLE_SEARCH_API_KEY="your-api-key"
export GOOGLE_SEARCH_ENGINE_ID="your-engine-id"
```

**Free tier:** 100 queries/day

### DuckDuckGo Fallback

Automatically used if Google API not configured (no setup required, but less reliable).

## Test Results

Successfully tested with **Abernethy (ID: 6762)**:

- ✅ All 11 sections populated
- ✅ Data structure validated
- ✅ Database updated successfully
- ✅ UI displays correctly
- ✅ Data merging works
- ✅ Post-processing fixes issues

## Documentation Files

- **`families_research_web_system.md`** - Complete web research system guide
- **`families_research_quickstart.md`** - Quick start guide
- **`families_research_data_schema.md`** - JSON schema documentation
- **`families_database.md`** - Database structure documentation
- **`families_research_implementation_plan.md`** - Implementation plan
- **`families_research_llm_guide.md`** - Basic LLM approach (deprecated)
- **`families_import.md`** - CSV import documentation

## Next Steps

1. ✅ **System Development** - Complete
2. ✅ **Testing** - Complete (Abernethy)
3. **Batch Processing** - Scale to multiple families
4. **Quality Improvement** - Refine based on results
5. **Source Expansion** - Add more authoritative sources
6. **Error Handling** - Improve LLM parsing reliability

## Files Reference

- **Web Research Script:** `scripts/research_family_web.py`
- **Manual Research Tool:** `scripts/research_family.py`
- **Research Guide:** `docs/surname_research_guide.md`
- **JSON Template:** `data/research_data_template.json`
- **Family Detail Template:** `templates/families/detail.html`
- **Families Blueprint:** `blueprints/families.py`

