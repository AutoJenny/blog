#!/usr/bin/env python3
"""
Import families data from clan.com CSV file.

This script:
- Imports new families or updates existing ones (upsert)
- Handles spelling_of relationships
- Imports related data (spellings, septs, histories, designs)
- Avoids creating duplicate records

Usage:
    python3 scripts/import_families_clan_csv.py [--dry-run] [--skip-related]
"""

import csv
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.database import db_manager
import psycopg
from psycopg.rows import dict_row


def parse_comma_separated(value: str) -> List[str]:
    """Parse comma-separated values, handling spaces and empty values."""
    if not value or not value.strip():
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


def parse_design_ids(value: str) -> List[int]:
    """Parse comma-separated design IDs."""
    if not value or not value.strip():
        return []
    try:
        return [int(id.strip()) for id in value.split(',') if id.strip().isdigit()]
    except ValueError:
        return []


def get_existing_family_ids(conn) -> Set[int]:
    """Get set of existing family IDs from database."""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM families")
        return set(row['id'] for row in cur.fetchall())


def upsert_family(conn, family_data: Dict, dry_run: bool = False) -> bool:
    """Insert or update a family record."""
    family_id = int(family_data['id'])
    name = family_data['name'].strip()
    is_clan = family_data.get('is_clan', '0') == '1'
    is_virtual = family_data.get('is_virtual', '0') == '1'
    
    # spelling_of contains the NAME of the canonical form, not the ID
    # We need to look up the ID by name
    spelling_of_id = None
    if family_data.get('spelling_of') and family_data['spelling_of'].strip():
        spelling_of_name = family_data['spelling_of'].strip()
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM families WHERE name = %s LIMIT 1", (spelling_of_name,))
            result = cur.fetchone()
            if result:
                spelling_of_id = result['id']
            elif not dry_run:
                # If the canonical form doesn't exist yet, we'll set it later in a second pass
                # For now, we'll leave it NULL and update it after all families are imported
                pass
    
    if dry_run:
        existing_ids = get_existing_family_ids(conn)
        is_new = family_id not in existing_ids
        spelling_info = f" (spelling_of: {family_data.get('spelling_of', '')})" if family_data.get('spelling_of') else ""
        print(f"  [DRY RUN] Would {'UPDATE' if not is_new else 'INSERT'} family ID {family_id}: {name}{spelling_info}")
        return True
    
    with conn.cursor() as cur:
        # Use ON CONFLICT to handle upsert
        cur.execute("""
            INSERT INTO families (id, name, is_clan, is_virtual, spelling_of, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                is_clan = EXCLUDED.is_clan,
                is_virtual = EXCLUDED.is_virtual,
                spelling_of = COALESCE(EXCLUDED.spelling_of, families.spelling_of),
                updated_at = NOW()
        """, (family_id, name, is_clan, is_virtual, spelling_of_id))
    
    return True


def import_spellings(conn, family_id: int, spellings_str: str, dry_run: bool = False) -> int:
    """Import spelling variants by updating their spelling_of field."""
    if not spellings_str or not spellings_str.strip():
        return 0
    
    spellings = parse_comma_separated(spellings_str)
    if not spellings:
        return 0
    
    if dry_run:
        print(f"    [DRY RUN] Would set spelling_of for {len(spellings)} spelling variants")
        return len(spellings)
    
    imported = 0
    with conn.cursor() as cur:
        for spelling_name in spellings:
            # Find the family_id for this spelling variant (if it exists)
            cur.execute("SELECT id FROM families WHERE name = %s LIMIT 1", (spelling_name,))
            spelling_family = cur.fetchone()
            
            if spelling_family:
                variant_id = spelling_family['id']
                # Update the variant's spelling_of to point to this family (the canonical form)
                cur.execute("""
                    UPDATE families 
                    SET spelling_of = %s, updated_at = NOW()
                    WHERE id = %s AND (spelling_of IS NULL OR spelling_of != %s)
                """, (family_id, variant_id, family_id))
                if cur.rowcount > 0:
                    imported += 1
    
    return imported


def import_septs(conn, family_id: int, septs_str: str, dry_run: bool = False) -> int:
    """Import septs into family_septs table."""
    if not septs_str or not septs_str.strip():
        return 0
    
    septs = parse_comma_separated(septs_str)
    if not septs:
        return 0
    
    if dry_run:
        print(f"    [DRY RUN] Would import {len(septs)} septs for family {family_id}")
        return len(septs)
    
    imported = 0
    with conn.cursor() as cur:
        for sept_name in septs:
            # Find the family_id for this sept (if it exists)
            cur.execute("SELECT id FROM families WHERE name = %s LIMIT 1", (sept_name,))
            sept_family = cur.fetchone()
            
            if sept_family:
                sept_of_id = sept_family['id']
                # Check if relationship already exists
                cur.execute("""
                    SELECT id FROM family_septs 
                    WHERE family_id = %s AND sept_of_id = %s
                """, (family_id, sept_of_id))
                existing = cur.fetchone()
                
                if not existing:
                    cur.execute("""
                        INSERT INTO family_septs (family_id, sept_of_id, created_at)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT DO NOTHING
                    """, (family_id, sept_of_id))
                    imported += 1
    
    return imported


def import_histories(conn, family_id: int, histories_str: str, dry_run: bool = False) -> int:
    """Import national histories into family_resources table."""
    if not histories_str or not histories_str.strip():
        return 0
    
    histories = parse_comma_separated(histories_str)
    if not histories:
        return 0
    
    if dry_run:
        print(f"    [DRY RUN] Would import {len(histories)} history types for family {family_id}")
        return len(histories)
    
    imported = 0
    with conn.cursor() as cur:
        for history_type in histories:
            # Check if this resource already exists
            cur.execute("""
                SELECT id FROM family_resources 
                WHERE family_id = %s 
                AND resource_type = 'history' 
                AND resource_category = %s
            """, (family_id, history_type))
            existing = cur.fetchone()
            
            if not existing:
                cur.execute("""
                    INSERT INTO family_resources 
                    (family_id, resource_type, resource_category, resource_value, created_at, updated_at)
                    VALUES (%s, 'history', %s, %s, NOW(), NOW())
                """, (family_id, history_type, f"{history_type.title()} history"))
                imported += 1
    
    return imported


def import_designs(conn, family_id: int, design_names_str: str, design_ids_str: str, dry_run: bool = False) -> int:
    """Import designs into family_designs table."""
    if not design_names_str or not design_names_str.strip():
        return 0
    
    design_names = parse_comma_separated(design_names_str)
    design_ids = parse_design_ids(design_ids_str) if design_ids_str else []
    
    if not design_names:
        return 0
    
    if dry_run:
        print(f"    [DRY RUN] Would import {len(design_names)} designs for family {family_id}")
        return len(design_names)
    
    imported = 0
    with conn.cursor() as cur:
        # Match design names with IDs (if provided)
        for idx, design_name in enumerate(design_names):
            design_id = design_ids[idx] if idx < len(design_ids) else None
            
            # Check if this design already exists for this family
            if design_id:
                cur.execute("""
                    SELECT id FROM family_designs 
                    WHERE family_id = %s AND design_id = %s
                """, (family_id, design_id))
            else:
                cur.execute("""
                    SELECT id FROM family_designs 
                    WHERE family_id = %s AND design_id IS NULL
                """, (family_id,))
            
            existing = cur.fetchone()
            
            if not existing:
                cur.execute("""
                    INSERT INTO family_designs 
                    (family_id, design_id, is_default, created_at)
                    VALUES (%s, %s, %s, NOW())
                """, (family_id, design_id, idx == 0))  # First design is default
                imported += 1
    
    return imported


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Import families data from clan.com CSV')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be imported without making changes')
    parser.add_argument('--skip-related', action='store_true', help='Skip importing related data (spellings, septs, etc.)')
    parser.add_argument('--csv-file', type=str, default='data/families.csv', help='Path to CSV file')
    
    args = parser.parse_args()
    
    csv_file = Path(args.csv_file)
    if not csv_file.exists():
        print(f"Error: CSV file not found: {csv_file}")
        sys.exit(1)
    
    print("=" * 60)
    print("Importing Families from clan.com CSV")
    print("=" * 60)
    print(f"CSV file: {csv_file}")
    print(f"Dry run: {args.dry_run}")
    print(f"Skip related data: {args.skip_related}")
    print()
    
    # Read CSV
    print("Reading CSV file...")
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"Found {len(rows)} rows in CSV")
    
    # Get existing IDs
    with db_manager.get_connection() as conn:
        existing_ids = get_existing_family_ids(conn)
        print(f"Existing families in database: {len(existing_ids)}")
        
        # Process rows
        new_count = 0
        update_count = 0
        skipped_duplicates = 0
        stats = {
            'spellings': 0,
            'septs': 0,
            'histories': 0,
            'designs': 0
        }
        
        # Track processed IDs to handle CSV duplicates
        processed_ids = set()
        
        print("\nProcessing families...")
        for idx, row in enumerate(rows, 1):
            try:
                family_id = int(row['id'])
                
                # Skip if we've already processed this ID (handle CSV duplicates)
                if family_id in processed_ids:
                    skipped_duplicates += 1
                    if idx % 1000 == 0:
                        print(f"  Processed {idx}/{len(rows)} rows... (skipped {skipped_duplicates} duplicates)")
                    continue
                
                processed_ids.add(family_id)
                
                # Upsert family
                is_new = family_id not in existing_ids
                if upsert_family(conn, row, args.dry_run):
                    if is_new:
                        new_count += 1
                    else:
                        update_count += 1
                
                # Import related data
                if not args.skip_related:
                    if not args.dry_run:
                        conn.commit()  # Commit family first
                    
                    # Import spellings
                    if row.get('spellings'):
                        count = import_spellings(conn, family_id, row['spellings'], args.dry_run)
                        stats['spellings'] += count
                    
                    # Import septs
                    if row.get('septs'):
                        count = import_septs(conn, family_id, row['septs'], args.dry_run)
                        stats['septs'] += count
                    
                    # Import histories
                    if row.get('present_national_histories'):
                        count = import_histories(conn, family_id, row['present_national_histories'], args.dry_run)
                        stats['histories'] += count
                    
                    # Import designs
                    if row.get('design_names'):
                        count = import_designs(
                            conn, 
                            family_id, 
                            row.get('design_names', ''),
                            row.get('design_ids', ''),
                            args.dry_run
                        )
                        stats['designs'] += count
                    
                    if not args.dry_run:
                        conn.commit()
                
                if idx % 1000 == 0:
                    print(f"  Processed {idx}/{len(rows)} rows... (new: {new_count}, updated: {update_count}, skipped: {skipped_duplicates})")
            
            except Exception as e:
                print(f"  Error processing row {idx} (ID: {row.get('id', 'unknown')}): {e}")
                if not args.dry_run:
                    conn.rollback()
                continue
        
        # Second pass: Update spelling_of for families where the canonical form wasn't found in first pass
        if not args.dry_run:
            print("\nUpdating spelling_of relationships (second pass)...")
            updated_spelling_of = 0
            for row in rows:
                try:
                    family_id = int(row['id'])
                    if row.get('spelling_of') and row['spelling_of'].strip():
                        spelling_of_name = row['spelling_of'].strip()
                        with conn.cursor() as cur:
                            # Look up the canonical form's ID
                            cur.execute("SELECT id FROM families WHERE name = %s LIMIT 1", (spelling_of_name,))
                            result = cur.fetchone()
                            if result:
                                canonical_id = result['id']
                                # Update this family's spelling_of
                                cur.execute("""
                                    UPDATE families 
                                    SET spelling_of = %s, updated_at = NOW()
                                    WHERE id = %s AND (spelling_of IS NULL OR spelling_of != %s)
                                """, (canonical_id, family_id, canonical_id))
                                if cur.rowcount > 0:
                                    updated_spelling_of += 1
                except Exception as e:
                    continue
            
            if updated_spelling_of > 0:
                conn.commit()
                print(f"  Updated {updated_spelling_of} spelling_of relationships")
        
        # Final commit
        if not args.dry_run:
            conn.commit()
        
        print("\n" + "=" * 60)
        print("Import Summary")
        print("=" * 60)
        print(f"New families added: {new_count}")
        print(f"Existing families updated: {update_count}")
        print(f"Duplicate rows skipped: {skipped_duplicates}")
        if not args.skip_related:
            print(f"\nRelated data imported:")
            print(f"  Spellings: {stats['spellings']}")
            print(f"  Septs: {stats['septs']}")
            print(f"  Histories: {stats['histories']}")
            print(f"  Designs: {stats['designs']}")
        print()
        
        if args.dry_run:
            print("DRY RUN - No changes were made to the database")
        else:
            print("Import complete!")


if __name__ == '__main__':
    main()

