# Web-Research-Based Family Research System

## Overview

The `research_family_web.py` script performs **targeted web research for each of the 11 research sections separately**. Unlike the basic LLM approach, this system:

1. **Separately researches each section** with section-specific search queries
2. **Performs live web searches** using Google Custom Search API or DuckDuckGo
3. **Searches known sources** relevant to each research topic
4. **Compares and synthesizes** information from multiple sources
5. **Produces definitive records** for each research section

## Architecture

### Research Sections

The system researches **11 distinct sections**, each with its own search strategy:

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

### Research Process for Each Section

For each section, the system:

1. **Builds section-specific search queries** (3-5 queries per section)
2. **Searches known sources** (2-3 authoritative sources per section)
3. **Performs web searches** using Google Custom Search API or DuckDuckGo
4. **Aggregates results** from multiple sources
5. **Sends to LLM for synthesis** with:
   - All search results
   - Section-specific research guide
   - Family context from database
   - JSON template for that section
6. **LLM synthesizes** multiple sources into definitive JSON
7. **Combines all sections** into final research data

## Usage

### Basic Usage

Research all sections for a family (automatically saves to file AND updates database):

```bash
python3 scripts/research_family_web.py <family_id_or_name> --save
```

**Note:** `--save` now automatically updates the database. Use `--no-update` if you want to save to file only.

### Research Specific Sections

```bash
python3 scripts/research_family_web.py 6762 --sections etymology,early_records,clan_association --save
```

This will:
- Research only the specified sections
- Merge with existing research data (doesn't overwrite other sections)
- Save to file and update database

### Save Without Updating Database

```bash
python3 scripts/research_family_web.py 6762 --save --no-update
```

### Dry Run (Validate Only)

```bash
python3 scripts/research_family_web.py 6762 --save --dry-run
```

## Configuration

### Google Custom Search API (Recommended)

For best results, configure Google Custom Search API:

1. Get API key from [Google Cloud Console](https://console.cloud.google.com/)
2. Create a Custom Search Engine at [Google Custom Search](https://programmablesearchengine.google.com/)
3. Set environment variables:
   ```bash
   export GOOGLE_SEARCH_API_KEY="your-api-key"
   export GOOGLE_SEARCH_ENGINE_ID="your-engine-id"
   ```

**Note:** Free tier allows 100 queries/day.

### DuckDuckGo Fallback

If Google Custom Search is not configured, the system automatically falls back to DuckDuckGo HTML scraping (no API key required, but less reliable).

## Search Strategy by Section

### Etymology
- **Queries:** "{surname} surname etymology", "{surname} name origin meaning", etc.
- **Known Sources:** ancestry.com, houseofnames.com, surnamedb.com, behindthename.com
- **Focus:** Language origins, root words, name meaning, name type

### Early Records
- **Queries:** "{surname} earliest records Scotland", "{surname} first mention Scotland", etc.
- **Known Sources:** scotlandspeople.gov.uk, nationalarchives.gov.uk, familysearch.org
- **Focus:** Earliest documented appearances, dates, locations, record types

### Distribution (Historic & Modern)
- **Queries:** "{surname} distribution Scotland", "{surname} surname map", etc.
- **Known Sources:** forebears.io, surnamedb.com, ancestry.com surname distribution
- **Focus:** Geographic distribution, regional concentrations, frequency

### Clan Association
- **Queries:** "{surname} Scottish clan", "{surname} clan sept Scotland", etc.
- **Known Sources:** clan.com, scotclans.com, electricscotland.com, lyon-court.com
- **Focus:** Scottish clan/sept connections, official status, territorial associations

### Heraldry
- **Queries:** "{surname} coat of arms Scotland", "{surname} heraldry Scotland", etc.
- **Known Sources:** lyon-court.com, tartanregister.gov.uk, clan.com tartan
- **Focus:** Coats of arms, mottoes, tartans, heraldic records

### Variants
- **Queries:** "{surname} spelling variants", "{surname} surname variations", etc.
- **Known Sources:** ancestry.com surname variations, familysearch.org
- **Focus:** Spelling variants, language forms, related surnames

### Migration
- **Queries:** "{surname} migration Scotland", "{surname} emigration Scotland", etc.
- **Known Sources:** scotlandspeople.gov.uk emigration, nationalarchives.gov.uk migration
- **Focus:** Movement patterns, diaspora, emigration waves

### Notables
- **Queries:** "{surname} famous people Scotland", "{surname} notable Scots", etc.
- **Known Sources:** wikipedia.org, biography.com, electricscotland.com
- **Focus:** Notable individuals, verifiable biographical information

### Cultural Notes
- **Queries:** "{surname} Scottish culture", "{surname} literature references", etc.
- **Known Sources:** wikipedia.org, electricscotland.com, scotland.org
- **Focus:** Literary references, cultural associations, folklore

### Genealogy Resources
- **Queries:** "{surname} family society Scotland", "{surname} genealogy resources", etc.
- **Known Sources:** familysearch.org, scotlandspeople.gov.uk, scottishgenealogy.org
- **Focus:** Family societies, published histories, record-rich areas

## LLM Synthesis Process

For each section, the LLM receives:

1. **Web Search Results** - Multiple sources with titles, URLs, snippets
2. **Research Guide** - Section-specific instructions from `surname_research_guide.md`
3. **Family Context** - Database information (is_clan, aliases, variants, etc.)
4. **JSON Template** - Structure to populate

The LLM then:
- Analyzes all search results
- Compares information from multiple sources
- Identifies conflicts or uncertainties
- Synthesizes a definitive record
- Populates JSON structure with factual information only
- Marks uncertainty explicitly
- Cites sources

## Output

The script produces:
- **JSON file** with complete research data (`data/research_{name}_{id}_web.json`)
- **Validation** against schema and business rules
- **Optional database update** if `--update` flag is used

## Key Features

1. **Live Research** - Uses current web sources, not just training data
2. **Section-Specific** - Each section researched independently with targeted queries
3. **Multiple Sources** - Compares and synthesizes from multiple sources
4. **Source Citations** - Tracks where information came from
5. **Conflict Detection** - Identifies when sources disagree
6. **Comprehensive** - Covers all 11 research sections systematically
7. **Data Merging** - Automatically merges with existing research data (doesn't overwrite)
8. **Post-Processing** - Automatically fixes common data structure issues
9. **Auto-Update** - `--save` flag automatically updates database (can be disabled with `--no-update`)
10. **Validation** - Validates all data against schema before saving

## Data Merging

The script automatically merges new research with existing data:

- **Preserves existing sections** - Only researched sections are updated
- **Merges data** - New data is merged with existing, not overwritten
- **Maintains structure** - Existing data structure is preserved

Example: If you research only `etymology` and `early_records`, all other sections remain unchanged.

## Post-Processing

The system automatically post-processes research data to fix common issues:

- **Year validation** - Rejects invalid years (< 1000), sets to null
- **Array structure** - Converts malformed arrays to proper objects
- **Data type fixes** - Ensures correct data types (null vs 0, arrays vs null)
- **Schema compliance** - Fixes structure to match JSON schema
- **Field mapping** - Maps alternative field names to correct schema fields

## Limitations

1. **API Rate Limits** - Google Custom Search free tier: 100 queries/day
2. **Search Quality** - Depends on search engine and query formulation
3. **LLM Synthesis** - Still requires review for accuracy
4. **Time** - Researching all 11 sections takes time (several minutes per family)
5. **LLM Response Parsing** - Occasionally fails to parse JSON from LLM (falls back to template)

## Best Practices

1. **Start with test case** - Test with one family first (e.g., Abernethy)
2. **Review output** - Always review LLM synthesis before updating database
3. **Research selectively** - Use `--sections` to research specific sections
4. **Validate** - Always validate before updating database
5. **Fact-check** - LLM synthesis should be fact-checked, especially for critical information
6. **Iterate** - Refine search queries and known sources based on results

## Troubleshooting

### No Search Results

**Problem:** Web searches return no results

**Solutions:**
- Check Google Custom Search API configuration
- Verify internet connection
- Try different search queries
- Check if DuckDuckGo fallback is working

### LLM Synthesis Errors

**Problem:** LLM fails to synthesize or produces invalid JSON

**Solutions:**
- Check LLM service is running (Ollama)
- Increase `max_tokens` if response is truncated
- Lower `temperature` for more structured output
- Review search results quality

### Rate Limiting

**Problem:** Google Custom Search API rate limit exceeded

**Solutions:**
- Use `--sections` to research fewer sections at a time
- Wait for daily limit reset
- Consider upgrading API quota
- Use DuckDuckGo fallback (no rate limits, but less reliable)

## Comparison with Other Approaches

### vs. Manual Research (`research_family.py`)
- **Faster** - Automated research vs. manual
- **Less control** - Requires review vs. full control
- **Good for** - Initial research, batch processing

### vs. Basic LLM (`research_family_llm.py`)
- **Live sources** - Web research vs. training data only
- **More comprehensive** - Section-by-section vs. single prompt
- **Better quality** - Multiple sources vs. single LLM response

## Test Results

Successfully tested with **Abernethy (ID: 6762)**:

- ✅ All 11 sections researched and populated
- ✅ Data structure validated and fixed automatically
- ✅ Successfully merged with existing data
- ✅ Database updated automatically
- ✅ UI displays both database data and research data in separate tabs

### Example Output Quality

- **Etymology**: Complete with origin languages, root words, and summary
- **Distribution**: Both historic and modern distribution data
- **Clan Association**: Scottish name identified, clan associations found
- **Heraldry**: Arms, mottoes, and tartans documented
- **Variants**: Multiple spelling variants identified
- **Migration**: Migration phases with regions and drivers
- **Genealogy Resources**: Family societies and record-rich areas identified

## Next Steps

1. ✅ **Test with Abernethy** - Completed successfully
2. **Refine search queries** - Improve based on results
3. **Add more known sources** - Expand authoritative source list
4. **Optimize synthesis prompts** - Improve LLM output quality
5. **Scale to batch processing** - Research multiple families
6. **Improve error handling** - Better handling of LLM parsing failures

## Files Reference

- **Web Research Script:** `scripts/research_family_web.py`
- **Research Guide:** `docs/surname_research_guide.md`
- **Database Schema:** `docs/families_database.md`
- **JSON Template:** `data/research_data_template.json`

