#!/usr/bin/env python3
"""Apply newsletter enhancement fields migration."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.database import db_manager

def apply_migration():
    """Apply the newsletter enhancement fields migration."""
    migration_sql = """
    -- Add fields to newsletter_source_item for suitability scoring and deduplication
    ALTER TABLE newsletter_source_item
    ADD COLUMN IF NOT EXISTS suitability_score NUMERIC(3,1),
    ADD COLUMN IF NOT EXISTS suitability_notes TEXT,
    ADD COLUMN IF NOT EXISTS source_url_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS is_event BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS calendar_event_id INTEGER;

    -- Add index for URL hash lookups (deduplication)
    CREATE INDEX IF NOT EXISTS idx_newsletter_source_item_url_hash 
        ON newsletter_source_item(source_url_hash);

    -- Add index for suitability scoring queries
    CREATE INDEX IF NOT EXISTS idx_newsletter_source_item_suitability 
        ON newsletter_source_item(suitability_score) 
        WHERE suitability_score IS NOT NULL;

    -- Add index for calendar_event_id lookups
    CREATE INDEX IF NOT EXISTS idx_newsletter_source_item_calendar_event 
        ON newsletter_source_item(calendar_event_id) 
        WHERE calendar_event_id IS NOT NULL;

    -- Phase 8.2: Calendar Events Extension
    ALTER TABLE calendar_events
    ADD COLUMN IF NOT EXISTS source_url TEXT,
    ADD COLUMN IF NOT EXISTS source_name VARCHAR(128),
    ADD COLUMN IF NOT EXISTS imported_from VARCHAR(128);

    -- Add index for source_url lookups (deduplication)
    CREATE INDEX IF NOT EXISTS idx_calendar_events_source_url 
        ON calendar_events(source_url) 
        WHERE source_url IS NOT NULL;

    -- Add index for source_name lookups
    CREATE INDEX IF NOT EXISTS idx_calendar_events_source_name 
        ON calendar_events(source_name) 
        WHERE source_name IS NOT NULL;
    """
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(migration_sql)
                conn.commit()
        print("✓ Migration applied successfully")
        return 0
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(apply_migration())

