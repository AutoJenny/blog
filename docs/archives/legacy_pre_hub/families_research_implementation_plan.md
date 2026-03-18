# Families Research Implementation Plan

## Overview

This document outlines the practical process for populating `research_data` JSON fields for the 158 clans without history texts, starting with a single test case to refine the process.

## Phase 1: Single Test Case (Refinement)

### Step 1: Select Test Candidate

**Criteria for test clan:**
- Canonical name (not a variant)
- No existing history text
- Not too rare (should have some researchable information)
- Not too common (to avoid overwhelming complexity)

**Recommended test candidates:**
- Abernethy (ID: 6762) - Well-known clan, should have good sources
- Adair (ID: ?) - Moderate complexity
- Ainslie (ID: ?) - Good for testing

**Action:** Select one clan and record the choice.

### Step 2: Research Workflow

**Tools needed:**
1. Research guide (`docs/surname_research_guide.md`)
2. JSON template (`data/research_data_template.json`)
3. Database access to check existing relationships
4. Source access (web search, databases, etc.)

**Process:**
1. **Pre-research database check:**
   ```sql
   SELECT 
     f.id, f.name, f.is_clan, f.is_canonical,
     (SELECT COUNT(*) FROM family_septs WHERE sept_of_id = f.id) as sept_count,
     (SELECT COUNT(*) FROM family_spellings WHERE spelling_of_id = f.id) as variant_count,
     (SELECT COUNT(*) FROM family_aliases WHERE family_id = f.id) as alias_count
   FROM families f
   WHERE f.name = '[TEST_CLAN_NAME]';
   ```

2. **Research each section** following the guide:
   - Start with etymology (foundation)
   - Then early records
   - Then distribution
   - Then clan association (cross-reference with database)
   - Then other sections as evidence allows

3. **Build JSON incrementally:**
   - Start with template
   - Fill sections as research progresses
   - Mark uncertainty explicitly
   - Cite sources

4. **Validate JSON:**
   - Check against schema
   - Verify data types (null vs 0, arrays vs null, etc.)
   - Ensure all required fields present
   - Check boolean logic

### Step 3: Create Research Script/Tool

**Proposed structure:**

```python
# scripts/research_family.py
# - Takes family ID or name
# - Checks database for existing data
# - Guides through research process
# - Validates JSON
# - Optionally uses LLM for research assistance
```

**Features:**
- Database context retrieval
- JSON validation
- Progress tracking
- Review/approval workflow

### Step 4: Test Research Execution

**Manual process for first test:**
1. Research the test clan manually
2. Populate JSON following guide
3. Validate JSON structure
4. Review for quality (use checklist)
5. Store in database
6. Review output

**Review criteria:**
- No invented data
- Uncertainty properly marked
- Sources cited
- Cross-referenced with database
- Follows guide guidelines

### Step 5: Refine Process

**Based on test results, refine:**
- Research workflow
- JSON structure (if needed)
- Validation rules
- Quality checklist
- Documentation

## Phase 2: Batch Processing (After Refinement)

### Step 1: Prioritization

**Priority order for 158 clans:**
1. Canonical clans (98) - Start here
2. Variant clans (60) - Can reference canonical forms

**Within canonical clans, consider:**
- Well-known clans first (easier to research)
- Or alphabetically
- Or by existing sept count (more complex = more important)

### Step 2: Automation Options

**Option A: Manual with Tooling**
- Use research script for each clan
- Human researcher follows guide
- Tool validates and stores

**Option B: LLM-Assisted**
- LLM does initial research
- Human reviews and refines
- Tool validates and stores

**Option C: Hybrid**
- LLM does initial research
- Human fact-checks and enhances
- Tool validates and stores

### Step 3: Progress Tracking

**Database tracking:**
```sql
-- Add research status tracking
ALTER TABLE families ADD COLUMN research_status VARCHAR(50);
-- Values: 'not_started', 'in_progress', 'review', 'complete', 'needs_revision'
```

**Or use metadata in research_data:**
```json
{
  "metadata": {
    "research_status": "complete | in_progress | needs_revision",
    "researcher": "name or identifier",
    "reviewed_by": "name or null",
    "review_date": "YYYY-MM-DD or null"
  }
}
```

### Step 4: Quality Control

**Review process:**
1. Automated validation (JSON schema, data types)
2. Peer review checklist
3. Source verification spot-checks
4. Update process for corrections

## Proposed Implementation Steps

### Immediate (Test Phase)

1. **Create research tool script** (`scripts/research_family.py`)
   - Database context retrieval
   - JSON template loading
   - Validation functions
   - Storage functions

2. **Select test clan** (recommend: Abernethy or similar)

3. **Manual research** following guide

4. **Populate JSON** and validate

5. **Store in database** and review

6. **Refine process** based on results

### Short-term (After Test)

1. **Add progress tracking** (research_status field or metadata)

2. **Create batch processing script** (if using automation)

3. **Set up review workflow**

4. **Begin processing priority clans**

### Long-term (Scaling)

1. **Automate where possible** (LLM assistance, validation)

2. **Build review interface** (if needed)

3. **Process all 158 clans**

4. **Expand to other families** (non-clans, variants)

## Technical Implementation

### Database Updates

**Option 1: Direct JSONB update**
```sql
UPDATE families
SET research_data = '{
  "surname": "Abernethy",
  ...
}'::jsonb
WHERE id = 6762;
```

**Option 2: Python script with validation**
```python
def update_research_data(family_id, research_json):
    # Validate JSON structure
    # Check against schema
    # Update database
    # Log changes
```

### Validation Functions

**JSON Schema validation:**
- Check required fields
- Validate data types
- Check enum values
- Verify relationships

**Business logic validation:**
- `has_documented_arms` matches `arms` array
- `is_scottish_name` logic
- Year handling (null not 0)
- Array handling ([] not null)

### Progress Tracking

**Database approach:**
```sql
-- Add status column
ALTER TABLE families 
ADD COLUMN research_status VARCHAR(50) DEFAULT 'not_started';

-- Or use JSON metadata
-- research_data->'metadata'->>'research_status'
```

**Tracking queries:**
```sql
-- Count by status
SELECT research_status, COUNT(*) 
FROM families 
WHERE is_clan = TRUE AND has_history = FALSE
GROUP BY research_status;

-- Get next to research
SELECT id, name 
FROM families 
WHERE is_clan = TRUE 
  AND has_history = FALSE 
  AND research_status = 'not_started'
ORDER BY name
LIMIT 1;
```

## LLM Integration (If Using)

### Research Assistant Prompt

**Structure:**
1. Provide family context (name, is_clan, existing relationships)
2. Provide research guide
3. Request research for specific sections
4. Validate output
5. Iterate

### Quality Control

**LLM output should:**
- Be fact-checked
- Cite sources
- Mark uncertainty
- Be reviewed by human

**Human review should:**
- Verify sources
- Check for invention
- Validate uncertainty flags
- Approve or request revision

## Success Metrics

**For test case:**
- [ ] JSON validates against schema
- [ ] No invented data
- [ ] Uncertainty properly marked
- [ ] Sources cited
- [ ] Cross-referenced with database
- [ ] Review checklist passed

**For batch:**
- [ ] All 158 clans researched
- [ ] Quality maintained
- [ ] Progress trackable
- [ ] Reviewable/updatable

## Next Steps

1. **Create research tool script** (see below)
2. **Select test clan**
3. **Execute test research**
4. **Review and refine**
5. **Scale to batch processing**

---

## Appendix: Research Tool Script Structure

```python
#!/usr/bin/env python3
"""
Family Research Tool
Helps research and populate research_data JSON for families
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional

# Database connection
from config.database import db_manager

def get_family_context(family_id: int) -> Dict:
    """Get existing family data from database."""
    # Query family and relationships
    pass

def load_template() -> Dict:
    """Load JSON template."""
    pass

def validate_research_json(data: Dict) -> tuple[bool, list[str]]:
    """Validate JSON against schema and business rules."""
    errors = []
    # Check schema
    # Check data types
    # Check business logic
    return len(errors) == 0, errors

def update_family_research(family_id: int, research_data: Dict) -> bool:
    """Update family research_data in database."""
    # Validate
    # Update
    # Log
    pass

def main():
    """Main research workflow."""
    # Get family ID
    # Load context
    # Guide research
    # Validate
    # Store
    pass
```

