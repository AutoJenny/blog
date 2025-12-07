#!/usr/bin/env python3
"""
Import missing histories from the new CSV file into the database.

This script reads the new CSV file and imports only the histories that
are missing from the database, based on the comparison report.
"""

import csv
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# History types to import
HISTORY_TYPES = [
    'history_legacy',
    'history_scottish',
    'history_english',
    'history_welsh',
    'history_irish',
]


def check_history_exists(cursor, family_id: int, history_type: str) -> bool:
    """Check if a history already exists for a family."""
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM family_resources
        WHERE family_id = %s
          AND resource_type = 'text'
          AND resource_category = %s
          AND LENGTH(resource_value) > 10
    """, (family_id, history_type))
    result = cursor.fetchone()
    return result['count'] > 0 if result else False


def import_history(cursor, family_id: int, history_type: str, content: str, dry_run: bool = False) -> bool:
    """Import a single history into the database."""
    if not content or len(content.strip()) <= 10:
        return False
    
    if dry_run:
        logger.info(f"  [DRY RUN] Would import {history_type} for family_id {family_id} ({len(content)} chars)")
        return True
    
    try:
        # Check for existing record first to avoid duplicates
        cursor.execute("""
            SELECT id FROM family_resources
            WHERE family_id = %s
              AND resource_type = 'text'
              AND resource_category = %s
        """, (family_id, history_type))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing record
            cursor.execute("""
                UPDATE family_resources
                SET resource_value = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (content.strip(), existing['id']))
            return True
        else:
            # Insert new record
            cursor.execute("""
                INSERT INTO family_resources (family_id, resource_type, resource_category, resource_value)
                VALUES (%s, 'text', %s, %s)
            """, (family_id, history_type, content.strip()))
            return True
    except Exception as e:
        logger.error(f"  Error importing {history_type} for family_id {family_id}: {e}")
        return False


def get_family_id_by_name(cursor, family_name: str) -> int:
    """Get family ID by name."""
    cursor.execute("SELECT id FROM families WHERE name = %s", (family_name,))
    result = cursor.fetchone()
    return result['id'] if result else None


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Import missing histories from CSV file"
    )
    parser.add_argument(
        '--csv-file',
        default='data/families (1).csv',
        help='Path to CSV file (default: data/families (1).csv)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be imported without actually importing'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of families to process (for testing)'
    )
    
    args = parser.parse_args()
    
    csv_file = args.csv_file
    if not os.path.exists(csv_file):
        logger.error(f"CSV file not found: {csv_file}")
        return 1
    
    logger.info(f"Reading CSV file: {csv_file}")
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made to database")
    
    # Statistics
    stats = {
        'total_checked': 0,
        'imported': 0,
        'skipped_existing': 0,
        'skipped_no_family': 0,
        'errors': 0,
    }
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Read CSV and import histories
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, start=2):
                    if args.limit and row_num > args.limit + 1:
                        break
                    
                    family_name = row['name'].strip()
                    if not family_name:
                        continue
                    
                    # Get family ID
                    family_id = get_family_id_by_name(cur, family_name)
                    if not family_id:
                        logger.warning(f"  Family not found in database: {family_name}")
                        stats['skipped_no_family'] += 1
                        continue
                    
                    # Process each history type
                    for history_type in HISTORY_TYPES:
                        content = row.get(history_type, '').strip()
                        if not content or len(content) <= 10:
                            continue
                        
                        stats['total_checked'] += 1
                        
                        # Check if already exists
                        if check_history_exists(cur, family_id, history_type):
                            logger.debug(f"  Skipping {history_type} for {family_name} (already exists)")
                            stats['skipped_existing'] += 1
                            continue
                        
                        # Import the history
                        logger.info(f"  Importing {history_type} for {family_name} (ID: {family_id}) - {len(content)} chars")
                        if import_history(cur, family_id, history_type, content, args.dry_run):
                            stats['imported'] += 1
                        else:
                            stats['errors'] += 1
                    
                    # Commit after each family
                    if not args.dry_run:
                        conn.commit()
    
    # Print summary
    print("\n" + "="*60)
    print("IMPORT SUMMARY")
    print("="*60)
    print(f"Total histories checked: {stats['total_checked']}")
    print(f"Imported: {stats['imported']}")
    print(f"Skipped (already exist): {stats['skipped_existing']}")
    print(f"Skipped (family not found): {stats['skipped_no_family']}")
    print(f"Errors: {stats['errors']}")
    print("="*60)
    
    if args.dry_run:
        print("\nThis was a DRY RUN - no changes were made to the database.")
        print("Run without --dry-run to perform the actual import.")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

