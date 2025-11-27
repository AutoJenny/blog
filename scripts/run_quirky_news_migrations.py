"""Run database migrations for quirky news feature.

This script runs all three migrations needed for the Round Scotland component.
"""

from __future__ import annotations

import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.database import db_manager

logger = logging.getLogger(__name__)


def run_migration(migration_file: str) -> bool:
    """Run a single migration file."""
    migration_path = os.path.join(os.path.dirname(__file__), '..', migration_file)
    
    if not os.path.exists(migration_path):
        logger.error(f"Migration file not found: {migration_path}")
        return False
    
    logger.info(f"Running migration: {migration_file}")
    
    with open(migration_path, 'r') as f:
        sql = f.read()
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Execute the SQL (migrations use BEGIN/COMMIT)
                cur.execute(sql)
                conn.commit()
        logger.info(f"✓ Successfully ran {migration_file}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to run {migration_file}: {e}", exc_info=True)
        return False


def main():
    """Run all quirky news migrations."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    migrations = [
        'migrations/add_quirky_news_source_fields.sql',
        'migrations/add_quirky_news_fields.sql',
        'migrations/create_weekly_highlights_tables.sql',
    ]
    
    logger.info("Starting quirky news migrations...")
    logger.info("="*60)
    
    success_count = 0
    for migration in migrations:
        if run_migration(migration):
            success_count += 1
        else:
            logger.error(f"Migration failed: {migration}")
            return 1
    
    logger.info("="*60)
    logger.info(f"Completed: {success_count}/{len(migrations)} migrations successful")
    
    if success_count == len(migrations):
        logger.info("✓ All migrations completed successfully!")
        return 0
    else:
        logger.error("✗ Some migrations failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())

