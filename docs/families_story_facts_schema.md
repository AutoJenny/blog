# Story Facts Schema - Second Pass Research

## Overview

The `story_facts` section is a **second pass** research layer focused on extended narratives and immersive storytelling. This is distinct from the core factual data in other sections and is designed to support richer, more engaging content.

**Purpose:** Provide narrative elements, key figures, turning points, and thematic context to create more extensive and immersive family histories.

## Schema Structure

```json
{
  "story_facts": {
    "time_span": {
      "earliest_century": "string (e.g. '12th' or 'unknown')",
      "latest_century": "string (e.g. '18th' or 'modern')",
      "notes": "string (brief summary of how long the family is visible in history)"
    },
    "key_figures": [
      {
        "name": "string",
        "titles_or_roles": [
          "string (e.g. 'High Steward of Scotland', 'King of Scots')"
        ],
        "life_dates": "string or null (e.g. 'c. 1320–1390', 'fl. 14th c.')",
        "alignment": "royal_line | cadet_branch | rebel | church | rival_family | other | unknown",
        "one_line": "string (short hook for this person in the story)",
        "sources_hint": [
          "string (short id or URL slug)"
        ],
        "uncertainty_flags": [
          "string (e.g. 'exact dates disputed')"
        ]
      }
    ],
    "turning_points": [
      {
        "id": "string (unique within this surname, e.g. 'marriage_to_bruce_heir')",
        "title": "string (e.g. 'A dynasty is born')",
        "approx_date": "string (e.g. 'late 13th century', '1437')",
        "place": "string or null (castle, town, region)",
        "involved_figures": [
          "string (names as in key_figures.name)"
        ],
        "summary": "string (dry factual summary, not purple prose)",
        "consequences": "string (how this changed the family or kingdom)",
        "is_legendary": false,
        "sources_hint": [
          "string"
        ],
        "uncertainty_flags": [
          "string"
        ]
      }
    ],
    "places": [
      {
        "name": "string (e.g. 'Castle Stalker')",
        "type": "castle | island | town | region | estate | other",
        "location_description": "string (e.g. 'on an islet in the Firth of Lorne in Appin')",
        "period_relevance": "string (e.g. '14th–16th centuries')",
        "link_to_family": "string (why this place matters to the surname story)",
        "sources_hint": [
          "string"
        ]
      }
    ],
    "legends_and_dark_episodes": [
      {
        "label": "string (e.g. 'The Wolf of Badenoch')",
        "approx_date": "string or null",
        "place": "string or null",
        "summary": "string (what the story/episode claims, in neutral tone)",
        "is_mostly_legend": true,
        "known_facts": "string (what can be historically verified)",
        "caution": "string (what is doubtful, exaggerated or pure legend)",
        "involved_figures": [
          "string (names of people if known)"
        ],
        "sources_hint": [
          "string"
        ]
      }
    ],
    "themes": [
      "string (e.g. 'service to the crown', 'rebellion', 'religious conflict', 'Highland lawlessness')"
    ],
    "sources_summary": [
      {
        "source_id": "string (your own short handle, e.g. 'wp_stewart_clan')",
        "type": "scholarly | popular_history | clan_site | tourism | commercial_genealogy | other",
        "reliability": "high | medium | low | unknown",
        "coverage": "string (which periods/topics it mainly covers)",
        "notes": "string (e.g. 'romanticised Jacobite focus', 'good on medieval records')"
      }
    ],
    "quotations": [
      {
        "id": "string (unique handle, e.g. 'james_i_inverness_poem')",
        "quoted_text": "string (verbatim quotation exactly as found)",
        "speaker": "string (e.g. 'King James I')",
        "approx_date": "string (e.g. '1430s', 'c. 1437', 'medieval')",
        "context_summary": "string (brief factual explanation of what the quotation refers to)",
        "source_hint": [
          "string (origin or URL slug)"
        ],
        "reliability": "high | medium | low | uncertain",
        "uncertainty_flags": [
          "string (if authenticity or attribution has been disputed)"
        ]
      }
    ]
  }
}
```

## Field Definitions

### time_span

**Purpose:** Establish the historical timeframe for the family's story.

- **earliest_century**: Century when family first appears (e.g., "12th", "13th", "unknown")
- **latest_century**: Most recent century of significance (e.g., "18th", "modern", "unknown")
- **notes**: Brief summary of the family's historical visibility

### key_figures

**Purpose:** Identify important individuals who shaped the family's story.

- **name**: Full name or known name
- **titles_or_roles**: Array of titles/roles (e.g., "High Steward of Scotland", "King of Scots")
- **life_dates**: Approximate dates (e.g., "c. 1320–1390", "fl. 14th c.") or null
- **alignment**: Relationship to power structure
  - `royal_line` - Direct royal lineage
  - `cadet_branch` - Junior branch of noble family
  - `rebel` - Opposed to established authority
  - `church` - Religious figure
  - `rival_family` - From competing family
  - `other` - Other significant relationship
  - `unknown` - Relationship unclear
- **one_line**: Short hook/summary for narrative use
- **sources_hint**: Array of source identifiers
- **uncertainty_flags**: Array of uncertainty notes

### turning_points

**Purpose:** Significant events that changed the family's trajectory.

- **id**: Unique identifier within this surname (e.g., "marriage_to_bruce_heir")
- **title**: Descriptive title (e.g., "A dynasty is born")
- **approx_date**: Approximate date (e.g., "late 13th century", "1437")
- **place**: Location where event occurred (castle, town, region) or null
- **involved_figures**: Array of names matching `key_figures.name`
- **summary**: Dry factual summary (not purple prose)
- **consequences**: How this changed the family or kingdom
- **is_legendary**: Boolean - true if primarily legendary
- **sources_hint**: Array of source identifiers
- **uncertainty_flags**: Array of uncertainty notes

### places

**Purpose:** Important locations associated with the family.

- **name**: Place name (e.g., "Castle Stalker")
- **type**: Type of place
  - `castle` - Fortified structure
  - `island` - Island
  - `town` - Town or city
  - `region` - Geographic region
  - `estate` - Landed estate
  - `other` - Other type
- **location_description**: Physical description (e.g., "on an islet in the Firth of Lorne in Appin")
- **period_relevance**: Time period when place was significant (e.g., "14th–16th centuries")
- **link_to_family**: Why this place matters to the surname story
- **sources_hint**: Array of source identifiers

### legends_and_dark_episodes

**Purpose:** Document legendary stories and controversial episodes.

- **label**: Descriptive label (e.g., "The Wolf of Badenoch")
- **approx_date**: Approximate date or null
- **place**: Location or null
- **summary**: What the story/episode claims (neutral tone)
- **is_mostly_legend**: Boolean - true if primarily legendary
- **known_facts**: What can be historically verified
- **caution**: What is doubtful, exaggerated, or pure legend
- **involved_figures**: Array of names if known
- **sources_hint**: Array of source identifiers

### themes

**Purpose:** Recurring themes in the family's history.

Array of strings identifying themes (e.g., "service to the crown", "rebellion", "religious conflict", "Highland lawlessness").

### sources_summary

**Purpose:** Evaluate and summarize sources used for story research.

- **source_id**: Short identifier (e.g., "wp_stewart_clan")
- **type**: Type of source
  - `scholarly` - Academic/scholarly work
  - `popular_history` - Popular history book
  - `clan_site` - Clan association website
  - `tourism` - Tourism/heritage site
  - `commercial_genealogy` - Commercial genealogy site
  - `other` - Other type
- **reliability**: Reliability assessment
  - `high` - Highly reliable
  - `medium` - Moderately reliable
  - `low` - Low reliability
  - `unknown` - Reliability unknown
- **coverage**: Which periods/topics it mainly covers
- **notes**: Additional notes (e.g., "romanticised Jacobite focus", "good on medieval records")

### quotations

**Purpose:** Store verbatim historical quotations safely and accurately.

- **id**: Unique identifier within this surname (e.g., "james_i_inverness_poem")
- **quoted_text**: Verbatim quotation exactly as found (must be exact, no reconstruction)
- **speaker**: Attributed speaker (e.g., "King James I") - only if clearly stated
- **approx_date**: Approximate date or period (e.g., "1430s", "c. 1437", "medieval")
- **context_summary**: Brief factual explanation of what the quotation refers to
- **source_hint**: Array of source identifiers or URL slugs
- **reliability**: Reliability of the quotation
  - `high` - Well-documented and verified
  - `medium` - Reasonably reliable
  - `low` - Questionable attribution or source
  - `uncertain` - Attribution or authenticity disputed
- **uncertainty_flags**: Array of uncertainty notes (e.g., "Also attributed to...", "Tradition says...")

**Critical Rules:**
- Extract ONLY quotations that appear explicitly as quoted or poetic lines
- Do NOT include partial quotations or reconstruct missing lines
- Do NOT guess speakers - only include if clearly stated
- Preserve exact wording verbatim
- Mark uncertainty explicitly in uncertainty_flags

## Distinction from Core Data

**Core Data (First Pass):**
- Factual, structured data
- Etymology, records, distribution, etc.
- Focus on verifiable facts
- Used for reference and data queries

**Story Facts (Second Pass):**
- Narrative elements and storytelling
- Key figures, turning points, legends
- Focus on immersive narratives
- Used for extended content creation

## Research Approach

This is a **second pass** research process:

1. **First Pass:** Core factual data (etymology, records, distribution, etc.)
2. **Second Pass:** Story facts (narrative elements, key figures, turning points)

The second pass builds on the first pass, using core data as foundation for narrative research.

## Usage Notes

- **Keep factual:** Even in narrative sections, maintain factual accuracy
- **Distinguish legend from fact:** Use `is_mostly_legend` and `caution` fields
- **Cite sources:** Always include `sources_hint` for traceability
- **Mark uncertainty:** Use `uncertainty_flags` for disputed information
- **Avoid purple prose:** Keep summaries dry and factual, even in narrative context

## Integration with Core Data

Story facts should:
- Reference core data where relevant (e.g., key figures may appear in `notables`)
- Build on core data (e.g., `time_span` relates to `early_records`)
- Provide narrative context for core facts
- Support extended content creation

## Next Steps

1. **Wait for prompting info** - User will provide fact extraction guidelines
2. **Create research script** - Second pass research tool
3. **Test with Abernethy** - Validate approach
4. **Integrate with UI** - Display story facts separately from core data

