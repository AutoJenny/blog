#!/usr/bin/env python3
"""
Apply Product & Category Profiles Phase 1 migrations

This script applies all database migrations for Phase 1:
1. Create producers table
2. Add profile fields to post table
3. Add producer_id to clan_products
4. Add specifications to clan_products
5. Add heritage data to categories
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.database import db_manager

def read_migration_file(filename):
    """Read SQL migration file."""
    migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations')
    filepath = os.path.join(migrations_dir, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Migration file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        return f.read()

def apply_migration(migration_sql, description):
    """Apply a single migration."""
    print(f"\nApplying: {description}...")
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(migration_sql)
                conn.commit()
        print(f"✓ {description} - SUCCESS")
        return True
    except Exception as e:
        print(f"✗ {description} - FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Apply all Phase 1 migrations."""
    print("=" * 60)
    print("Product & Category Profiles - Phase 1 Migrations")
    print("=" * 60)
    
    migrations = [
        ('create_producers_table.sql', 'Create producers table'),
        ('add_profile_fields_to_post.sql', 'Add profile fields to post table'),
        ('add_producer_id_to_clan_products.sql', 'Add producer_id to clan_products'),
        ('add_specifications_to_clan_products.sql', 'Add specifications to clan_products'),
        ('add_heritage_to_categories.sql', 'Add heritage data to categories'),
    ]
    
    success_count = 0
    failed_count = 0
    
    for filename, description in migrations:
        try:
            migration_sql = read_migration_file(filename)
            if apply_migration(migration_sql, description):
                success_count += 1
            else:
                failed_count += 1
        except Exception as e:
            print(f"✗ Error reading {filename}: {e}")
            failed_count += 1
    
    print("\n" + "=" * 60)
    print(f"Migration Summary: {success_count} succeeded, {failed_count} failed")
    print("=" * 60)
    
    if failed_count > 0:
        print("\n⚠ Some migrations failed. Please review the errors above.")
        return 1
    
    print("\n✓ All migrations applied successfully!")
    print("\nNext step: Run 'python scripts/migrate_suppliers_to_producers.py' to populate producers table")
    return 0

if __name__ == '__main__':
    sys.exit(main())







