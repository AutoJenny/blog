# Families Database Documentation

## Overview

The families database stores Scottish family and clan names with their relationships, resources, and research data. The database has evolved from a simple import structure to include comprehensive research capabilities.

## Table Structure

### Main Table: `families`

The core table storing family/clan names and metadata.

#### Original Fields (from CSV import)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key - unique family identifier from source system |
| `name` | VARCHAR(255) | Family/clan name (unique) |
| `is_clan` | BOOLEAN | TRUE if this is an official Scottish clan |
| `is_virtual` | BOOLEAN | TRUE if this is a virtual/placeholder entry (usually FALSE) |
| `created_at` | TIMESTAMP | When the record was created |
| `updated_at` | TIMESTAMP | When the record was last updated |

#### New Fields (added for research framework)

| Column | Type | Description |
|--------|------|-------------|
| `is_canonical` | BOOLEAN | TRUE if this name is not a spelling variant of another name. FALSE if it is a variant. |
| `has_history` | BOOLEAN | TRUE if this family has at least one history text resource (history_scottish, history_legacy, history_english, history_irish, or history_welsh) |
| `research_data` | JSONB | Comprehensive research framework JSON (see schema below) |

#### Indexes

- Primary key on `id`
- Unique index on `name`
- Index on `is_clan`
- Index on `is_virtual`
- Index on `is_canonical`
- Index on `has_history`
- GIN index on `research_data` (for efficient JSON queries)

## Relationship Tables

### `family_aliases`

Alternative names for families (child relationships).

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `family_id` | INTEGER | Foreign key to `families.id` |
| `alias_name` | VARCHAR(255) | Alternative name for the family |
| `created_at` | TIMESTAMP | When the record was created |

**Example:** "Toomey" is an alias of "Towmey"

### `family_spellings`

Spelling variations linking families to their canonical form (parent relationships).

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `family_id` | INTEGER | Foreign key to `families.id` (the variant) |
| `spelling_of_id` | INTEGER | Foreign key to `families.id` (the canonical form) |
| `created_at` | TIMESTAMP | When the record was created |

**Example:** "Abarcrumbie" is a spelling variant of "Abercrombie"

**Note:** Some families have bidirectional relationships (both have variants AND are variants themselves).

### `family_septs`

Sept relationships - sub-families that belong to clans.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `family_id` | INTEGER | Foreign key to `families.id` (the sept) |
| `sept_of_id` | INTEGER | Foreign key to `families.id` (the clan) |
| `created_at` | TIMESTAMP | When the record was created |

**Example:** "Abbot" is a sept of "MacNab"

### `family_resources`

Resources associated with families: images, text content, JSON data, location coordinates.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `family_id` | INTEGER | Foreign key to `families.id` |
| `resource_type` | VARCHAR(50) | Type: 'image', 'text', 'json', 'location' |
| `resource_category` | VARCHAR(255) | Category (e.g., 'british_fleet', 'scottish_gentry', 'history_legacy') |
| `resource_value` | TEXT | Filename, text content, or JSON string |
| `resource_metadata` | JSONB | Additional structured data |
| `created_at` | TIMESTAMP | When the record was created |
| `updated_at` | TIMESTAMP | When the record was last updated |

**Resource Categories:**
- **Images:** `british_fleet`, `scottish_gentry`, `bookplate_scottish`, `crest_scottish_svg`, etc.
- **Text:** `history_scottish`, `history_legacy`, `history_english`, `history_irish`, `history_welsh`, `location_text`
- **JSON:** `location_coords` (latitude/longitude data)

### `family_designs`

Fabric designs associated with families.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `family_id` | INTEGER | Foreign key to `families.id` |
| `design_id` | INTEGER | Design ID from external system |
| `design_year` | INTEGER | Year of design if available |
| `design_url` | TEXT | URL to design if available |
| `is_default` | BOOLEAN | TRUE if this is the default design |
| `created_at` | TIMESTAMP | When the record was created |

## Data Statistics

### Current State (as of import)

- **Total families:** 10,000
- **Clans:** 280 (2.8%)
- **Canonical names:** 4,309 (43.1%)
- **Variant names:** 5,691 (56.9%)
- **Families with history:** 246 (2.5%)
- **Clans with history:** 122 (43.6% of clans)
- **Clans without history:** 158 (56.4% of clans) - **High priority for research**

### Relationship Statistics

- **Aliases:** 1,326 relationships
- **Spellings:** 10,571 relationships
- **Septs:** 1,232 relationships
- **Resources:** 35,155 resources
- **Designs:** 2,751 designs

## Research Data Schema

The `research_data` JSONB column stores comprehensive research information following this structure:

### Top-Level Fields

```json
{
  "surname": "string",
  "primary_language_region": "string (e.g. 'Scottish', 'English', 'Irish', 'Mixed', 'Unknown')"
}
```

### Metadata

```json
{
  "metadata": {
    "sources": ["string (short identifiers or URLs)"],
    "last_updated": "YYYY-MM-DD",
    "research_confidence": "high | medium | low",
    "notes": "string (free-text notes about research quality, gaps, or controversies)"
  }
}
```

### Etymology

```json
{
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
        "approx_date": "string (e.g. 'c. 1400', '15th century')",
        "region": "string or null",
        "source_hint": "string"
      }
    ],
    "etymology_summary": "string",
    "uncertainty_flags": ["string"]
  }
}
```

### Early Records

```json
{
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
  }
}
```

### Distribution (Historic)

```json
{
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
  }
}
```

### Distribution (Modern)

```json
{
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
  }
}
```

### Clan Association

```json
{
  "clan_association": {
    "is_scottish_name": true,
    "clan_sept_of": ["string"],
    "territorial_family": "string or null",
    "kindred_or_confederation": "string or null",
    "official_status": "recognized_by_Lyon | traditional_association | marketing_only | none | unknown",
    "sources_hint": ["string"],
    "association_notes": "string"
  }
}
```

### Heraldry

```json
{
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
  }
}
```

### Variants

```json
{
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
  }
}
```

### Migration

```json
{
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
  }
}
```

### Notables

```json
{
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
  }
}
```

### Cultural Notes

```json
{
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
  }
}
```

### Genealogy Resources

```json
{
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

## Common Queries

### Find canonical clans without history (high priority)

```sql
SELECT name, id
FROM families
WHERE is_clan = TRUE
  AND is_canonical = TRUE
  AND has_history = FALSE
ORDER BY name;
```

### Find families with research data

```sql
SELECT name, research_data->>'primary_language_region' as region
FROM families
WHERE research_data IS NOT NULL;
```

### Find families by research confidence

```sql
SELECT name, research_data->'metadata'->>'research_confidence' as confidence
FROM families
WHERE research_data->'metadata'->>'research_confidence' = 'high';
```

### Get all spelling variants of a family

```sql
SELECT f2.name as variant
FROM family_spellings fs
JOIN families f1 ON fs.spelling_of_id = f1.id
JOIN families f2 ON fs.family_id = f2.id
WHERE f1.name = 'Abercrombie';
```

### Get all septs of a clan

```sql
SELECT f2.name as sept
FROM family_septs fs
JOIN families f1 ON fs.sept_of_id = f1.id
JOIN families f2 ON fs.family_id = f2.id
WHERE f1.name = 'MacNab';
```

## Migration History

1. **create_families_tables.sql** - Initial schema creation
2. **add_families_canonical_flag.sql** - Added `is_canonical` flag
3. **add_families_has_history_flag.sql** - Added `has_history` flag
4. **add_families_research_data.sql** - Added `research_data` JSONB column

## Data Import

The families data was imported from `data/family.csv` using `scripts/import_families_csv.py`. The CSV contained HTML-embedded data that was parsed and normalized into the relationship tables.

## Priority Families for Research

**158 clans without history texts** are high priority for research data population. These families need comprehensive research to fill gaps in the database.

See the list of these clans in the database query results or in the import documentation.

## Notes

- All JSON fields in `research_data` are optional - populate only what is known
- Use `null` for unknown values, not empty strings
- Dates should follow YYYY-MM-DD format where applicable
- Confidence levels should be honest assessments of research quality
- Include uncertainty flags where evidence is weak or disputed
- The GIN index on `research_data` enables efficient queries on any JSON path

