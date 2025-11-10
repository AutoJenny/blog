#!/usr/bin/env python3
"""
Run the image style migrations.
This script runs the SQL migrations to add default_image_style support.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration(sql_file):
    """Run a SQL migration file"""
    migration_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations', sql_file)
    
    if not os.path.exists(migration_path):
        logger.error(f"Migration file not found: {migration_path}")
        return False
    
    logger.info(f"Running migration: {sql_file}")
    
    try:
        with open(migration_path, 'r') as f:
            sql = f.read()
        
        with db_manager.get_cursor() as cursor:
            # Execute the SQL
            cursor.execute(sql)
            cursor.connection.commit()
            logger.info(f"✅ Migration {sql_file} completed successfully")
            return True
    except Exception as e:
        logger.error(f"❌ Error running migration {sql_file}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    logger.info("Running image style migrations...\n")
    
    # Run migrations in order
    migrations = [
        'add_default_image_style_to_taxonomy.sql',
        'populate_landscape_image_style.sql'
    ]
    
    for migration in migrations:
        if not run_migration(migration):
            logger.error(f"Failed to run {migration}. Stopping.")
            return
        logger.info("")
    
    logger.info("✅ All migrations completed successfully!")

if __name__ == '__main__':
    main()

