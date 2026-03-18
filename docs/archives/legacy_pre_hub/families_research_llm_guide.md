# LLM-Assisted Family Research Guide

## Overview

The `research_family_llm.py` script uses an LLM (Large Language Model) to assist with researching and populating `research_data` JSON fields for families. This is Option 2 from the implementation plan - LLM-assisted research.

## Prerequisites

- LLM service running (Ollama recommended, default model: `llama3.2:latest`)
- Database connection configured
- Research guide: `docs/surname_research_guide.md`
- JSON template: `data/research_data_template.json`

## Usage

### Basic Usage

Research a family by ID or name:

```bash
python3 scripts/research_family_llm.py <family_id_or_name>
```

### Options

- `--model <model_name>`: Specify LLM model (default: `llama3.2:latest`)
- `--save`: Save JSON output to file
- `--update`: Update database with research data
- `--dry-run`: Validate but do not update database
- `--temperature <float>`: LLM temperature (default: 0.3 for more factual output)
- `--max-tokens <int>`: Max tokens for LLM response (default: 4000)

### Examples

**1. Research and save to file (no database update):**
```bash
python3 scripts/research_family_llm.py 6762 --save
```

**2. Research and update database:**
```bash
python3 scripts/research_family_llm.py 6762 --save --update
```

**3. Dry run (validate only):**
```bash
python3 scripts/research_family_llm.py 6762 --save --update --dry-run
```

**4. Use different model:**
```bash
python3 scripts/research_family_llm.py 6762 --model llama3.1:70b --save
```

**5. Research by name:**
```bash
python3 scripts/research_family_llm.py "Abernethy" --save
```

## Workflow

### Step 1: Research with LLM

```bash
python3 scripts/research_family_llm.py 6762 --save
```

This will:
1. Fetch family context from database
2. Load research guide and template
3. Create research prompt
4. Call LLM for research
5. Extract and validate JSON
6. Save to file: `data/research_Abernethy_6762_llm.json`

### Step 2: Review LLM Output

**Always review LLM output before updating database!**

Check the generated JSON file:
- Verify facts are accurate
- Check for invented data
- Ensure uncertainty is properly marked
- Verify sources are cited
- Cross-reference with database relationships

### Step 3: Manual Refinement (if needed)

Edit the JSON file manually to:
- Fix any errors
- Add missing information
- Correct uncertainty flags
- Enhance source citations

### Step 4: Validate

```bash
python3 scripts/research_family.py 6762 --validate data/research_Abernethy_6762_llm.json
```

### Step 5: Update Database

**Dry run first:**
```bash
python3 scripts/research_family.py 6762 --update data/research_Abernethy_6762_llm.json --dry-run
```

**Actual update:**
```bash
python3 scripts/research_family.py 6762 --update data/research_Abernethy_6762_llm.json
```

## LLM Service Configuration

The script automatically detects and uses the available LLM service:

1. **blog-core/app/llm/services.py** (preferred) - Has `generate()` method
2. **blueprints/planning_llm.py** (fallback) - Uses `execute_llm_request()` method

### Ollama Setup

If using Ollama (recommended):

1. Install Ollama: https://ollama.ai
2. Pull model: `ollama pull llama3.2:latest`
3. Ensure Ollama is running: `ollama serve`
4. Default URL: `http://localhost:11434`

### Model Selection

Recommended models for research:
- `llama3.2:latest` - Good balance of speed and quality
- `llama3.1:70b` - Higher quality, slower
- `mistral` - Fast, good for quick research

## Quality Control

### LLM Output Review Checklist

- [ ] No invented dates, people, or records
- [ ] All years use `null` for unknown (not `0`)
- [ ] `has_documented_arms` matches whether `arms` array has entries
- [ ] `is_scottish_name` reflects any Scottish association
- [ ] `variant_spellings` vs `related_surnames` distinction is clear
- [ ] `canonical_form` matches database `name` (unless reason to differ)
- [ ] Uncertainty flags used where evidence is weak
- [ ] Sources are cited (short identifiers or URLs if allowed)
- [ ] Cross-checked with database existing relationships
- [ ] Confidence levels are honest assessments
- [ ] No generic "family arms" claims
- [ ] Distinction between surname-specific and generic patterns is clear

### Common LLM Issues

**1. Invented Data**
- LLMs may invent specific dates or records
- **Fix:** Remove or mark as uncertain

**2. Overconfident Claims**
- LLMs may state facts without uncertainty
- **Fix:** Add uncertainty flags and lower confidence

**3. Missing Sources**
- LLMs may not cite sources
- **Fix:** Add source citations manually

**4. Generic Patterns**
- LLMs may apply generic patterns to specific surnames
- **Fix:** Verify surname-specific evidence

**5. JSON Format Errors**
- LLMs may produce invalid JSON
- **Fix:** Script attempts to extract JSON, but manual fixes may be needed

## Comparison: Manual vs LLM-Assisted

### Manual Research (`research_family.py`)
- **Pros:** Full control, no invented data, thorough fact-checking
- **Cons:** Time-consuming, requires research skills
- **Best for:** High-priority families, complex cases, final review

### LLM-Assisted (`research_family_llm.py`)
- **Pros:** Faster initial research, good starting point, handles structure
- **Cons:** Requires review, may invent data, needs fact-checking
- **Best for:** Batch processing, initial research, less critical families

### Recommended Hybrid Approach

1. **Use LLM for initial research** on multiple families
2. **Review and fact-check** each LLM output
3. **Manually refine** high-priority families
4. **Use manual research** for complex or disputed cases

## Troubleshooting

### LLM Service Not Found

**Error:** `ImportError` or `LLMService not found`

**Solution:** Ensure the LLM service is available in one of:
- `blog-core/app/llm/services.py`
- `blueprints/planning_llm.py`

### LLM Connection Error

**Error:** `Connection refused` or `timeout`

**Solution:**
1. Check Ollama is running: `ollama serve`
2. Verify URL: `http://localhost:11434`
3. Test connection: `curl http://localhost:11434/api/tags`

### Invalid JSON Output

**Error:** `Could not extract valid JSON from LLM response`

**Solution:**
1. Check LLM response in output
2. Try different model (some models are better at JSON)
3. Increase `--max-tokens` if response is truncated
4. Lower `--temperature` for more structured output

### Validation Errors

**Error:** Validation fails after LLM research

**Solution:**
1. Review validation errors
2. Fix common issues (null vs 0, arrays vs null)
3. Manually edit JSON file
4. Re-validate before updating database

## Best Practices

1. **Always review LLM output** before updating database
2. **Start with test case** (e.g., Abernethy ID: 6762)
3. **Use lower temperature** (0.3) for more factual output
4. **Validate before updating** database
5. **Keep LLM output files** for review and comparison
6. **Fact-check critical information** manually
7. **Mark uncertainty explicitly** in LLM output
8. **Cross-reference with database** relationships
9. **Use manual research** for high-priority families
10. **Iterate and refine** the process based on results

## Integration with Manual Research

The LLM-assisted script works alongside the manual research tool:

1. **Generate with LLM:** `research_family_llm.py --save`
2. **Review and refine:** Edit JSON file manually
3. **Validate:** `research_family.py --validate`
4. **Update:** `research_family.py --update`

Both tools use the same JSON schema and validation, ensuring compatibility.

## Next Steps

1. **Test with one family** (recommended: Abernethy ID: 6762)
2. **Review output quality**
3. **Refine prompt or process** if needed
4. **Scale to batch processing** for remaining clans
5. **Track progress** using database queries

## Files Reference

- **LLM Research Script:** `scripts/research_family_llm.py`
- **Manual Research Script:** `scripts/research_family.py`
- **Research Guide:** `docs/surname_research_guide.md`
- **Implementation Plan:** `docs/families_research_implementation_plan.md`
- **Database Schema:** `docs/families_database.md`
- **JSON Template:** `data/research_data_template.json`

