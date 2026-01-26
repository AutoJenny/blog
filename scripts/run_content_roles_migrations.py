#!/usr/bin/env python3
"""
Run Content Roles Framework migrations (Phase 2).

This script runs the two migrations needed for the Content Roles Framework:
1. 20260123_add_content_roles_framework.sql
2. 20260123_add_content_roles_approval_fields.sql
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration(migration_file: str) -> bool:
    """Run a single migration file."""
    migration_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'migrations',
        migration_file
    )
    
    if not os.path.exists(migration_path):
        logger.error(f"Migration file not found: {migration_path}")
        return False
    
    logger.info(f"Running migration: {migration_file}")
    
    try:
        with open(migration_path, 'r') as f:
            sql = f.read()
        
        # Use get_connection() to ensure proper transaction handling
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Execute the SQL (migrations use BEGIN/COMMIT)
                cursor.execute(sql)
                # Commit is handled by the transaction block in the migration
                conn.commit()
        
        logger.info(f"✅ Successfully ran {migration_file}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to run {migration_file}: {e}", exc_info=True)
        return False


def main():
    """Run all Content Roles Framework migrations."""
    logger.info("=" * 80)
    logger.info("CONTENT ROLES FRAMEWORK MIGRATIONS (Phase 2)")
    logger.info("=" * 80)
    logger.info("")
    
    migrations = [
        '20260123_add_content_roles_framework.sql',
        '20260123_add_content_roles_approval_fields.sql'
    ]
    
    success_count = 0
    for migration in migrations:
        logger.info(f"\n{'=' * 80}")
        logger.info(f"Migration: {migration}")
        logger.info(f"{'=' * 80}\n")
        
        if run_migration(migration):
            success_count += 1
        else:
            logger.error(f"\n❌ Migration {migration} failed. Stopping.")
            return False
    
    logger.info("\n" + "=" * 80)
    logger.info(f"✅ All migrations completed successfully ({success_count}/{len(migrations)})")
    logger.info("=" * 80)
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
