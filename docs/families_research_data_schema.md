# Families Research Data Schema

## Overview

The `research_data` column in the `families` table stores a comprehensive JSON framework for surname research. This document describes the complete schema structure.

## Column Details

- **Column Name:** `research_data`
- **Type:** JSONB (PostgreSQL JSON Binary)
- **Indexed:** Yes (GIN index for efficient JSON queries)
- **Nullable:** Yes (initially NULL for all families)

## JSON Schema

```json
{
  "surname": "string",
  "primary_language_region": "string (e.g. 'Scottish', 'English', 'Irish', 'Mixed', 'Unknown')",
  
  "metadata": {
    "sources": ["string (short identifiers or URLs)"],
    "last_updated": "YYYY-MM-DD",
    "research_confidence": "high | medium | low",
    "notes": "string (free-text notes about research quality, gaps, or controversies)"
  },
  
  "etymology": {
    "origin_languages": ["Gaelic", "Norse", "Norman French", "Scots", "Irish", "Old English", "Pictish", "Other", "Unknown"],
    "name_type": "patronymic | locational | occupational | descriptive | clan_territorial | habitational | religious | other | unknown",
    "literal_meaning": "string or null",
    "root_words": [
      {
        "language": "string",
        "form": "string",
        "meaning": "string"
      }
    ],
    "earliest_known_forms": [
      {
        "spelling": "string",
        "approx_date": "string",
        "region": "string or null",
        "source_hint": "string"
      }
    ],
    "etymology_summary": "string",
    "uncertainty_flags": ["string"]
  },
  
  "early_records": {
    "earliest_attestation": {
      "year": 0,
      "approximate": true,
      "location": "string",
      "jurisdiction": "string",
      "spelling": "string",
      "record_type": "string",
      "source_hint": "string or null",
      "notes": "string"
    },
    "other_attestations": [
      {
        "year": 0,
        "approximate": true,
        "location": "string",
        "jurisdiction": "string",
        "spelling": "string",
        "record_type": "string",
        "source_hint": "string or null",
        "notes": "string"
      }
    ],
    "record_confidence": "high | medium | low",
    "record_notes": "string"
  },
  
  "distribution_historic": {
    "snapshot_period": "string",
    "regions": [
      {
        "country": "string",
        "subregion_type": "county | parish | island | town | other",
        "subregion_name": "string",
        "relative_frequency": "very_high | high | medium | low | very_low | unknown",
        "evidence_hint": "string"
      }
    ],
    "summary": "string",
    "uncertainty_flags": ["string"]
  },
  
  "distribution_modern": {
    "reference_period": "string",
    "by_country": [
      {
        "country": "string",
        "relative_frequency": "very_high | high | medium | low | very_low",
        "approx_rank": "integer or null",
        "trend": "growing | stable | declining | unknown"
      }
    ],
    "notes": "string"
  },
  
  "clan_association": {
    "is_scottish_name": true,
    "clan_sept_of": ["string"],
    "territorial_family": "string or null",
    "kindred_or_confederation": "string or null",
    "official_status": "recognized_by_Lyon | traditional_association | marketing_only | none | unknown",
    "sources_hint": ["string"],
    "association_notes": "string"
  },
  
  "heraldry": {
    "has_documented_arms": true,
    "arms": [
      {
        "armiger_name": "string",
        "jurisdiction": "string",
        "approx_date": "string or null",
        "blazon": "string",
        "notes": "string"
      }
    ],
    "mottoes": [
      {
        "text": "string",
        "language": "string",
        "translation": "string or null",
        "attribution": "string"
      }
    ],
    "tartans": [
      {
        "name": "string",
        "status": "clan | family | fashion | corporate | other | unknown",
        "register_reference": "string or null",
        "notes": "string"
      }
    ],
    "disclaimer": "string"
  },
  
  "variants": {
    "canonical_form": "string",
    "variant_spellings": ["string"],
    "language_forms": [
      {
        "language": "string",
        "form": "string",
        "script": "string",
        "notes": "string"
      }
    ],
    "related_surnames": [
      {
        "surname": "string",
        "relationship_type": "cognate | anglicised_form | branch | doubtful | unknown",
        "notes": "string"
      }
    ],
    "variant_notes": "string"
  },
  
  "migration": {
    "summary": "string",
    "phases": [
      {
        "period": "string",
        "from_regions": ["string"],
        "to_regions": ["string"],
        "drivers": ["string"],
        "evidence_hint": "string"
      }
    ],
    "uncertainty_flags": ["string"]
  },
  
  "notables": {
    "people": [
      {
        "full_name": "string",
        "birth_year": 0,
        "death_year": 0,
        "approximate_dates": true,
        "occupation": "string",
        "main_region": "string",
        "short_bio": "string",
        "notability_type": "politics | military | arts | scholarship | business | religion | sport | other",
        "source_hint": "string"
      }
    ],
    "notables_notes": "string"
  },
  
  "cultural_notes": {
    "stereotypes_legends": "string",
    "literary_or_media_references": [
      {
        "work_title": "string",
        "author_or_creator": "string",
        "approx_date": "string or null",
        "context": "string",
        "fictional_or_real": "fictional | real"
      }
    ],
    "associated_occupations": ["string"],
    "social_status_history": "string",
    "cultural_summary": "string"
  },
  
  "genealogy_resources": {
    "family_societies": [
      {
        "name": "string",
        "region": "string",
        "url": "string or null",
        "notes": "string"
      }
    ],
    "published_histories": [
      {
        "title": "string",
        "author": "string",
        "year": 0,
        "publisher_or_place": "string or null",
        "notes": "string"
      }
    ],
    "record_rich_areas": [
      {
        "region": "string",
        "jurisdiction": "string",
        "record_types": ["parish_registers", "kirk_session", "sasines", "tax_lists", "census", "other"],
        "notes": "string"
      }
    ],
    "research_tips": "string"
  }
}
```

## Usage Examples

### Query families with research data

```sql
SELECT name, research_data
FROM families
WHERE research_data IS NOT NULL;
```

### Query by research confidence

```sql
SELECT name, research_data->'metadata'->>'research_confidence' as confidence
FROM families
WHERE research_data->'metadata'->>'research_confidence' = 'high';
```

### Query by primary language region

```sql
SELECT name, research_data->>'primary_language_region' as region
FROM families
WHERE research_data->>'primary_language_region' = 'Scottish';
```

### Update research data

```sql
UPDATE families
SET research_data = '{
  "surname": "Abercrombie",
  "primary_language_region": "Scottish",
  "metadata": {
    "last_updated": "2025-01-15",
    "research_confidence": "medium"
  }
}'::jsonb
WHERE name = 'Abercrombie';
```

## Priority Families

The 158 clans without history texts are high priority for research data population:
- See the list in the database query results
- These families need comprehensive research to fill gaps

## Story Facts (Second Pass)

The `story_facts` section is a **second pass** research layer for extended narratives and immersive storytelling. See `docs/families_story_facts_schema.md` for complete documentation.

**Note:** Story facts are distinct from core factual data and are designed to support richer, more engaging content creation.

## Notes

- All fields are optional - populate only what is known
- Use `null` for unknown values, not empty strings
- Dates should follow YYYY-MM-DD format where applicable
- Confidence levels should be honest assessments of research quality
- Include uncertainty flags where evidence is weak or disputed
- **Core data (first pass)** and **story facts (second pass)** are separate research phases

