#!/usr/bin/env python3
"""Run migration to add photo_search_results column to post_section table"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Execute the photo_search_results migration"""
    try:
        with db_manager.get_cursor() as cursor:
            # Check if column already exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'post_section' 
                AND column_name = 'photo_search_results'
            """)
            
            if cursor.fetchone():
                logger.info("Column photo_search_results already exists. Skipping migration.")
                return
            
            # Add column
            cursor.execute("""
                ALTER TABLE post_section 
                ADD COLUMN photo_search_results JSONB DEFAULT '[]'::jsonb
            """)
            logger.info("Added photo_search_results column to post_section")
            
            # Add comment
            cursor.execute("""
                COMMENT ON COLUMN post_section.photo_search_results IS 
                'JSONB array of photo search results from Pexels/Unsplash including URLs, credits, and selection status'
            """)
            logger.info("Migration completed successfully")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()

