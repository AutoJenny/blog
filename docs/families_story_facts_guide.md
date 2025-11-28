# Story Facts Research Guide - Second Pass

## Overview

The story facts research is a **second pass** that builds on core factual data to create extended, immersive narratives. It uses a two-prompt system:

1. **Prompt 1 - Fact Extraction**: Extracts structured story facts from web text chunks
2. **Prompt 2 - Story Writing**: Generates immersive narrative from complete JSON

## Workflow

### Step 1: Core Data Research (First Pass)

First, ensure you have core factual data:

```bash
python3 scripts/research_family_web.py <family_id> --save
```

This populates the 11 core research sections (etymology, early_records, distribution, etc.).

### Step 2: Story Facts Research (Second Pass)

Extract story facts and generate narrative:

```bash
python3 scripts/research_family_story_facts.py <family_id> --save
```

This will:
1. Search for story-focused content (clan history, key figures, legends)
2. Fetch and process web pages
3. Extract facts from each text chunk (Prompt 1)
4. Merge extracted facts into `story_facts` object
5. Generate immersive narrative (Prompt 2)
6. Save to database and files

### Step 3: Narrative-Only Generation

If you already have story_facts and just want to regenerate the narrative:

```bash
python3 scripts/research_family_story_facts.py <family_id> --narrative-only --save --word-target 1500
```

## Command Options

- `--save` - Save JSON to file and update database
- `--no-update` - Save to file but don't update database
- `--dry-run` - Validate but don't update database
- `--word-target <number>` - Target word count for narrative (default: 1200)
- `--narrative-only` - Generate narrative from existing story_facts (skip fact extraction)
- `--model <model_name>` - LLM model to use (default: llama3.2:latest)

## Output Files

The script generates:

1. **JSON file**: `data/research_{name}_{id}_story_facts.json`
   - Contains complete research_data with story_facts
   - Narrative stored in `metadata.narrative`

2. **Narrative file**: `data/narrative_{name}_{id}.md`
   - Markdown file with the generated narrative
   - Easy to read and use for content creation

## Story Facts Structure

The `story_facts` object contains:

- **time_span** - Historical timeframe
- **key_figures** - Important individuals with roles and alignment
- **turning_points** - Significant events that changed the family
- **places** - Important locations
- **legends_and_dark_episodes** - Stories and legends (with fact/legend distinction)
- **themes** - Recurring themes
- **sources_summary** - Source evaluation
- **quotations** - Verbatim historical quotations with attribution and context

See `docs/families_story_facts_schema.md` for complete schema documentation.

## Narrative Structure

The generated narrative follows this structure:

1. **Introduction** - Places family in time and space
2. **2-4 Titled Sections** - Key episodes and turning points
3. **Conclusion** - How the name survives today

The narrative:
- **Grounded in facts** from the JSON (all specific names, dates, events, places must be in JSON)
- **Interpretive freedom** for narrative flow, thematic connections, and general historical context
- Clearly signals uncertainty and legend
- Maintains vivid, readable tone
- **Prevents hallucination** by forbidding invented specific facts
- **Allows interpretation** through general context, thematic synthesis, and evocative language
- Incorporates quotations verbatim (1-3 meaningful quotes)
- Uses blockquote or poem formatting for quotations
- Presents quotations with appropriate context (e.g., "a chronicler recorded...", "the king himself wrote...")

**Key Distinction:**
- ✅ **Allowed:** "The 13th century was a time of political upheaval in Scotland..." (general context)
- ✅ **Allowed:** "This pattern suggests the family maintained close ties to the crown..." (interpretive connection)
- ❌ **Forbidden:** "Malcolm Abernethy led the charge at the Battle of Stirling Bridge..." (specific invented fact)

## Integration with Core Data

Story facts build on core data:

- **References core data**: Key figures may appear in `notables`
- **Builds on core data**: `time_span` relates to `early_records`
- **Provides narrative context**: Turns facts into stories
- **Supports content creation**: Ready-to-use narrative text

## Quotations System

The system includes a robust quotations mechanism:

- **Verbatim extraction**: Only extracts quotations that appear explicitly as quoted or poetic lines
- **No reconstruction**: Does not include partial quotations or guess missing lines
- **Attribution**: Only includes speaker if clearly stated in source
- **Deduplication**: Merges duplicate quotations, preserving attribution conflicts in uncertainty_flags
- **Safe integration**: Narrative generator can only use quotations from the JSON array
- **Context-aware**: Quotations are presented with appropriate historical context

**Example narrative usage:**
> As James I sought to bring order to the Highlands, he summoned the fractious chiefs to a parliament in Inverness—only to have each arrested upon arrival. The king, who harboured a taste for verse, marked the occasion in a set of grim lines that capture both his exasperation and his severity:
> 
> To the dungeons strong
> Haul the wretches along,
> As in Christ's my hope,
> They deserve the rope.

## Best Practices

1. **Run first pass first**: Ensure core data exists before story facts
2. **Review extracted facts**: Check `story_facts` in JSON before generating narrative
3. **Verify quotations**: Ensure quotations are verbatim and properly attributed
4. **Adjust word target**: Use `--word-target` to control narrative length
5. **Regenerate narratives**: Use `--narrative-only` to try different narrative styles
6. **Use narrative as starting point**: The narrative provides a solid foundation for writing extended histories, but:
   - Verify all specific factual claims against the JSON
   - Distinguish between factual content and interpretive connections
   - Use the narrative's structure and themes as a guide for further research
7. **Check quotation usage**: Ensure quotations enhance rather than clutter the narrative
8. **Understand the balance**: The narrative balances factual grounding with narrative flow - use it as a creative foundation while maintaining accuracy for specific claims

## Troubleshooting

### No Story Facts Extracted

- Check if web pages were successfully fetched
- Verify LLM is responding correctly
- Review search queries for better results

### Narrative Too Short/Long

- Adjust `--word-target` parameter
- Check if story_facts has enough content
- Narrative length depends on available facts

### Narrative Contains Invented Facts

- Review Prompt 2 to ensure it's using only JSON facts
- Check that story_facts doesn't contain invented data
- Regenerate with lower temperature if needed

## Files Reference

- **Story Facts Script**: `scripts/research_family_story_facts.py`
- **Schema Documentation**: `docs/families_story_facts_schema.md`
- **Prompt Documentation**: `docs/families_story_facts_prompts.md`
- **JSON Template**: `data/research_data_template.json`

