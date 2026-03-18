# Families CSV Comparison Report

## Summary

Comparison between the new `families.csv` from clan.com and the existing `families` table in the database.

**Date:** 2025-11-28

---

## Row Count Comparison

| Source | Total Rows | Unique IDs | ID Range |
|--------|-----------|------------|----------|
| CSV File | 14,643 | 14,569 | 1 to 16,429 |
| Database | 10,000 | 10,000 | 1 to 16,435 |

### Differences

- **New IDs in CSV (not in database):** 4,573 families
- **IDs in both:** 9,996 families
- **IDs in database but not in CSV:** 4 families

**Action Required:** Import 4,573 new family records from CSV.

---

## Column Comparison

### CSV Columns (10 total)

1. `id` - ✅ Exists in database
2. `name` - ✅ Exists in database
3. `is_clan` - ✅ Exists in database
4. `is_virtual` - ✅ Exists in database
5. `spelling_of` - ❌ **NEW COLUMN** (48.3% of rows have values)
6. `spellings` - Maps to `family_spellings` table (4.2% of rows have values)
7. `septs` - Maps to `family_septs` table (0.8% of rows have values)
8. `present_national_histories` - Maps to `family_resources` table (1.1% of rows have values)
9. `design_names` - Maps to `family_designs` table (6.0% of rows have values)
10. `design_ids` - Maps to `family_designs` table (6.0% of rows have values)

### Database Columns (not in CSV)

- `created_at` - Metadata (auto-generated)
- `updated_at` - Metadata (auto-generated)
- `is_canonical` - Flag we added (derived from `spelling_of` relationship)
- `has_history` - Flag we added (derived from `family_resources`)
- `research_data` - JSONB field we added (our research data)

---

## New Column: `spelling_of`

**Status:** ❌ **NEW - Needs to be added to database**

**Description:** Indicates that this family name is a spelling variant of another family.

**Statistics:**
- 7,067 rows (48.3%) have a `spelling_of` value
- Format: Contains the ID of the canonical family name
- Example: ID 2 (Adams) has `spelling_of = "Adam"` (likely ID of the canonical form)

**Action Required:**
1. Add `spelling_of` column to `families` table (INTEGER, nullable, foreign key to `families.id`)
2. Import the `spelling_of` relationships from CSV
3. This will help identify canonical vs variant names more accurately than our current `is_canonical` flag

---

## Data Mapping to Related Tables

### 1. Spellings (`spellings` column)
- **Maps to:** `family_spellings` table
- **Coverage:** 617 rows (4.2%) have spelling variants
- **Format:** Comma-separated list of spelling variants
- **Action:** Parse and import into `family_spellings` table

### 2. Septs (`septs` column)
- **Maps to:** `family_septs` table
- **Coverage:** 116 rows (0.8%) have septs
- **Format:** Comma-separated list of sept names
- **Action:** Parse and import into `family_septs` table

### 3. National Histories (`present_national_histories` column)
- **Maps to:** `family_resources` table
- **Coverage:** 157 rows (1.1%) have history flags
- **Format:** Comma-separated list (e.g., "scottish,english,welsh,irish")
- **Action:** Parse and import as `resource_type='history'` in `family_resources` table

### 4. Designs (`design_names` and `design_ids` columns)
- **Maps to:** `family_designs` table
- **Coverage:** 876 rows (6.0%) have design information
- **Format:** 
  - `design_names`: Comma-separated list of design names
  - `design_ids`: Comma-separated list of design IDs
- **Action:** Parse and import into `family_designs` table

---

## Import Plan

### Phase 1: Schema Updates
1. ✅ Add `spelling_of` column to `families` table
   ```sql
   ALTER TABLE families 
   ADD COLUMN spelling_of INTEGER REFERENCES families(id);
   ```

### Phase 2: Import New Families
1. Import 4,573 new family records (IDs not in database)
2. Update existing 9,996 records with any new data from CSV

### Phase 3: Import Related Data
1. Parse and import `spellings` → `family_spellings`
2. Parse and import `septs` → `family_septs`
3. Parse and import `present_national_histories` → `family_resources`
4. Parse and import `design_names` + `design_ids` → `family_designs`
5. Import `spelling_of` relationships

### Phase 4: Update Derived Flags
1. Recalculate `is_canonical` based on `spelling_of` relationships
2. Recalculate `has_history` based on `family_resources` with history types

---

## Notes

- The CSV has some duplicate IDs (14,643 rows but only 14,569 unique IDs)
- Need to handle duplicate IDs during import (likely updates vs new records)
- The `spelling_of` column is the most significant new data point (48.3% coverage)
- Most related data (spellings, septs, designs) is sparse but valuable when present

