# Families/Clans Data Import

## Overview

This document describes the import process for Scottish family and clan data from the `family.csv` file into normalized PostgreSQL tables.

## Database Schema

The import creates the following tables:

- **families**: Main table storing family/clan names and flags
- **family_aliases**: Alternative names for families (child relationships)
- **family_spellings**: Spelling variations linking families to canonical forms (parent relationships)
- **family_septs**: Sept relationships - sub-families that belong to clans
- **family_resources**: Resources associated with families (images, text, JSON data, location coordinates)
- **family_designs**: Fabric designs associated with families

See `migrations/create_families_tables.sql` for the complete schema.

## Import Process

### Step 1: Run Migration

First, create the database tables:

```bash
cd /Users/autojenny/Documents/projects/blog
psql $DATABASE_URL -f migrations/create_families_tables.sql
```

Or using Python:

```python
import sys
sys.path.insert(0, '.')
from config.database import db_manager

with open('migrations/create_families_tables.sql', 'r') as f:
    sql = f.read()

with db_manager.get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()
```

### Step 2: Import Data

Run the import script:

```bash
python3 scripts/import_families_csv.py
```

The script will:
1. Parse the CSV file (`data/family.csv`)
2. Extract clean data from embedded HTML
3. Parse relationships (aliases, spellings, septs)
4. Extract resources (images, text, JSON)
5. Import all data into PostgreSQL

### Step 3: Verify Import

Check the import statistics printed at the end, or query the database:

```sql
-- Count families
SELECT COUNT(*) FROM families;

-- Count clans
SELECT COUNT(*) FROM families WHERE is_clan = true;

-- Check relationships
SELECT 
    (SELECT COUNT(*) FROM family_aliases) as aliases,
    (SELECT COUNT(*) FROM family_spellings) as spellings,
    (SELECT COUNT(*) FROM family_septs) as septs,
    (SELECT COUNT(*) FROM family_resources) as resources,
    (SELECT COUNT(*) FROM family_designs) as designs;
```

## Data Structure

### CSV Columns

The CSV file contains:
- **ID**: Numeric family identifier
- **Name**: Family/clan name
- **Is Clan**: "Yes" or "No"
- **Is Virtual**: "Yes" or "No" (usually "No")
- **Designs**: HTML links to fabric designs
- **Aliases**: HTML forms with child relationships
- **Spellings**: HTML forms with parent relationships (spelling variations)
- **Septs**: HTML forms with sept relationships
- **Resources**: HTML divs with structured data (images, text, JSON)
- **Action**: HTML delete links (not imported)

### Parsed Data

The import script extracts:
- **Aliases**: Alternative names (e.g., "Toomey" is an alias of "Towmey")
- **Spellings**: Spelling variations (e.g., "Abarcrumbie" is a spelling of "Abercrombie")
- **Septs**: Sept relationships (e.g., "Abbot" is a sept of "MacNab")
- **Resources**: 
  - Images: PNG/SVG files with categories (e.g., "british_fleet", "scottish_gentry")
  - Text: Historical information
  - JSON: Location coordinates and other structured data
- **Designs**: Design IDs, years, and URLs

## Notes

- The import uses `ON CONFLICT` clauses to handle duplicates gracefully
- Relationships are only created if both families exist in the database
- Resources are stored with their original HTML structure parsed into structured fields
- The script commits every 100 records for performance

## Troubleshooting

If the import fails:
1. Check that the migration has been run
2. Verify the CSV file exists at `data/family.csv`
3. Check database connection settings
4. Review error messages in the output

Common issues:
- **Missing families in relationships**: Some relationships reference families that don't exist yet. The import handles this by checking for family existence before creating relationships.
- **HTML parsing errors**: The script includes error handling for malformed HTML, but some edge cases may need manual review.

