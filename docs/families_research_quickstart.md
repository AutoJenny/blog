# Families Research Quick Start Guide

## Overview

This guide provides a step-by-step process for researching and populating `research_data` for the 158 clans without history texts.

## Prerequisites

- Research guide: `docs/surname_research_guide.md`
- Implementation plan: `docs/families_research_implementation_plan.md`
- Research tool: `scripts/research_family.py`
- JSON template: `data/research_data_template.json`

## Test Case Workflow

### Step 1: Select Test Clan

**Recommended:** Abernethy (ID: 6762) - Well-known, canonical, has some existing resources

**View candidates:**
```bash
python3 scripts/research_family.py 6762 --context
```

### Step 2: Generate Template

```bash
python3 scripts/research_family.py 6762 --template
```

This creates: `data/research_Abernethy_6762.json`

### Step 3: Research

1. **Review family context** (shown when generating template):
   - Existing relationships (aliases, variants, septs)
   - Existing resources
   - Database flags (is_clan, is_canonical, has_history)

2. **Follow research guide** (`docs/surname_research_guide.md`):
   - Start with etymology
   - Then early records
   - Then distribution
   - Then clan association (cross-reference with database)
   - Continue with other sections

3. **Populate JSON**:
   - Edit `data/research_Abernethy_6762.json`
   - Fill sections as research progresses
   - Mark uncertainty explicitly
   - Cite sources

### Step 4: Validate

```bash
python3 scripts/research_family.py 6762 --validate data/research_Abernethy_6762.json
```

**Check for:**
- ✓ No validation errors
- ✓ No invented data
- ✓ Uncertainty properly marked
- ✓ Sources cited
- ✓ Cross-referenced with database

### Step 5: Review

**Use quality checklist from research guide:**
- [ ] No invented dates, people, or records
- [ ] All years use `null` for unknown (not `0`)
- [ ] `has_documented_arms` matches whether `arms` array has entries
- [ ] `is_scottish_name` reflects any Scottish association
- [ ] `variant_spellings` vs `related_surnames` distinction is clear
- [ ] `canonical_form` matches database `name`
- [ ] Uncertainty flags used where evidence is weak
- [ ] Sources are cited
- [ ] Cross-checked with database existing relationships
- [ ] Confidence levels are honest assessments

### Step 6: Update Database

**Dry run first:**
```bash
python3 scripts/research_family.py 6762 --update data/research_Abernethy_6762.json --dry-run
```

**Actual update:**
```bash
python3 scripts/research_family.py 6762 --update data/research_Abernethy_6762.json
```

### Step 7: Verify

```sql
SELECT name, research_data->>'surname' as surname, 
       research_data->'metadata'->>'research_confidence' as confidence
FROM families
WHERE id = 6762;
```

## Refinement Process

After completing the test case:

1. **Review the process:**
   - What worked well?
   - What was difficult?
   - What needs clarification?

2. **Update documentation:**
   - Refine research guide if needed
   - Update implementation plan
   - Add any new validation rules

3. **Refine tool:**
   - Add any missing features
   - Improve error messages
   - Add helpful prompts

## Recommended Approach: Web Research System

**The web research system (`research_family_web.py`) is now the recommended approach:**

1. **Automated web research** for each section
2. **Multiple source synthesis** 
3. **Automatic data merging** with existing research
4. **Post-processing** to fix common issues
5. **Auto-update** to database

```bash
# Research all sections
python3 scripts/research_family_web.py 6762 --save

# Research specific sections
python3 scripts/research_family_web.py 6762 --sections etymology,clan_association --save
```

See `docs/families_research_web_system.md` for complete documentation.

## Batch Processing (After Test)

Once the process is refined:

### Option A: Web Research (Recommended)

1. Use `research_family_web.py` for automated research
2. Review results in UI or JSON file
3. Refine specific sections if needed
4. System automatically updates database

### Option B: Manual with Tooling

1. Generate template for each clan
2. Research manually following guide
3. Validate and update

### Option C: Hybrid

1. Web research does initial research
2. Human fact-checks and enhances
3. Validate and update

## Progress Tracking

**Check progress:**
```sql
-- Count families with research_data
SELECT 
    COUNT(*) FILTER (WHERE research_data IS NOT NULL) as with_research,
    COUNT(*) FILTER (WHERE research_data IS NULL) as without_research
FROM families
WHERE is_clan = TRUE AND has_history = FALSE;
```

**Get next to research:**
```sql
SELECT id, name
FROM families
WHERE is_clan = TRUE 
  AND has_history = FALSE
  AND research_data IS NULL
ORDER BY name
LIMIT 10;
```

## Common Issues

### Validation Errors

**"year should be null for unknown, not 0"**
- Fix: Change `"year": 0` to `"year": null`

**"should be an array [], not null"**
- Fix: Change `null` to `[]` for array fields

**"has_documented_arms is true but arms array is empty"**
- Fix: Either add arms entries or set `has_documented_arms` to `false`

### Research Challenges

**No early records found:**
- Set `year: null`, `approximate: true`
- Explain gap in `record_notes`
- Set `record_confidence: "low"`

**Conflicting sources:**
- Record disagreement in `uncertainty_flags`
- Explain in summary fields
- Set appropriate confidence level

**Very rare surname:**
- Short entry is fine
- High uncertainty is acceptable
- Don't speculate

## Next Steps

1. Complete test case (Abernethy)
2. Review and refine process
3. Begin batch processing
4. Track progress
5. Expand to other families

## Files Reference

- **Research Guide:** `docs/surname_research_guide.md`
- **Implementation Plan:** `docs/families_research_implementation_plan.md`
- **Database Schema:** `docs/families_database.md`
- **Research Tool:** `scripts/research_family.py`
- **JSON Template:** `data/research_data_template.json`

