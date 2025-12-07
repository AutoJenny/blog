#!/usr/bin/env python3
"""
Migration Script: calendar_week_items -> calendar_week_overrides

Migrates active week-level overrides from the old calendar_week_items table
to the new calendar_week_overrides table.

Only migrates:
- Active items (is_active = TRUE)
- Week-level items (weekday IS NULL, for themes/recipes/words/phrases)
- Selected themes (is_selected = TRUE for themes)
- Profile items (need to check metadata for profile_type)
"""

import sys
import os
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.database import db_manager
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def map_item_type_to_category(item_type: str, metadata: dict = None) -> str:
    """
    Map old item_type to new category.
    
    Returns None if mapping not possible.
    """
    mapping = {
        'theme': 'theme',
        'recipe': 'recipe',
        'weekly_word': 'weekly_word',
        'weekly_phrase': 'weekly_phrase',
    }
    
    if item_type in mapping:
        return mapping[item_type]
    
    # Handle profiles - need to check metadata
    if item_type == 'profile':
        if metadata:
            profile_type = metadata.get('profile_type')
            if profile_type == 'product':
                return 'profile_product'
            elif profile_type == 'surname':
                return 'profile_surname'
            elif profile_type == 'category':
                # Old system had 'category', new system doesn't - skip or map to product?
                logger.warning("Found profile with type 'category', skipping (not in new system)")
                return None
        # If no metadata, try to infer from other sources or skip
        logger.warning("Found profile without profile_type in metadata, skipping")
        return None
    
    return None


def migrate_week_items():
    """Migrate data from calendar_week_items to calendar_week_overrides."""
    
    logger.info("Starting migration from calendar_week_items to calendar_week_overrides...")
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check if old table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'calendar_week_items'
                    )
                """)
                result = cursor.fetchone()
                table_exists = result['exists'] if isinstance(result, dict) else result[0]
                
                if not table_exists:
                    logger.info("calendar_week_items table does not exist - nothing to migrate")
                    return 0
                
                # Get all active week-level items
                cursor.execute("""
                    SELECT 
                        item_type,
                        item_id,
                        year,
                        week_number,
                        metadata,
                        is_selected
                    FROM calendar_week_items
                    WHERE is_active = TRUE
                        AND weekday IS NULL
                        AND (
                            item_type IN ('theme', 'recipe', 'weekly_word', 'weekly_phrase')
                            OR (item_type = 'profile' AND metadata IS NOT NULL)
                        )
                    ORDER BY year, week_number, item_type
                """)
                
                rows = cursor.fetchall()
                logger.info(f"Found {len(rows)} active week-level items to migrate")
                
                if len(rows) == 0:
                    logger.info("No items to migrate")
                    return 0
                
                migrated = 0
                skipped = 0
                errors = 0
                
                for row in rows:
                    item_type = row['item_type']
                    item_id = row['item_id']
                    year = row['year']
                    week_number = row['week_number']
                    metadata = row['metadata'] or {}
                    is_selected = row['is_selected']
                    
                    # Skip non-selected themes (only selected themes are overrides)
                    if item_type == 'theme' and not is_selected:
                        skipped += 1
                        logger.debug(f"Skipping non-selected theme: year={year} week={week_number} item_id={item_id}")
                        continue
                    
                    # Map item_type to category
                    category = map_item_type_to_category(item_type, metadata)
                    
                    if not category:
                        skipped += 1
                        logger.debug(f"Skipping unmappable item: item_type={item_type} year={year} week={week_number}")
                        continue
                    
                    # Check if override already exists
                    cursor.execute("""
                        SELECT id FROM calendar_week_overrides
                        WHERE year = %s AND week_number = %s AND category = %s
                    """, (year, week_number, category))
                    
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Update existing override
                        cursor.execute("""
                            UPDATE calendar_week_overrides
                            SET item_id = %s, updated_at = NOW()
                            WHERE year = %s AND week_number = %s AND category = %s
                        """, (item_id, year, week_number, category))
                        logger.debug(f"Updated override: {category} year={year} week={week_number} item_id={item_id}")
                    else:
                        # Insert new override
                        cursor.execute("""
                            INSERT INTO calendar_week_overrides
                                (year, week_number, category, item_id, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, NOW(), NOW())
                        """, (year, week_number, category, item_id))
                        logger.debug(f"Inserted override: {category} year={year} week={week_number} item_id={item_id}")
                    
                    migrated += 1
                
                conn.commit()
                
                logger.info(f"Migration complete:")
                logger.info(f"  - Migrated: {migrated} items")
                logger.info(f"  - Skipped: {skipped} items")
                logger.info(f"  - Errors: {errors} items")
                
                return migrated
                
    except Exception as e:
        logger.exception("Error during migration")
        raise


if __name__ == "__main__":
    try:
        count = migrate_week_items()
        print(f"\n✓ Migration complete: {count} items migrated")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)

