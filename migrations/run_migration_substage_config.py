#!/usr/bin/env python3
"""
Data Migration Script: Post Type Substages Config
Migrates data from config/post_type_substages.py to database tables.

Usage:
    python migrations/run_migration_substage_config.py
"""

import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg
from config.database import db_manager
from config.post_type_substages import SUBSTAGE_METADATA, POST_TYPE_SUBSTAGES
from config.output_channel_stages import OUTPUT_CHANNEL_STAGES

# Mapping of substage keys to their stage (extracted from context)
SUBSTAGE_STAGE_MAP = {
    # Calendar substages
    'view': 'calendar',
    'week-view': 'calendar',
    'ideas-week': 'calendar',
    
    # Planning substages
    'ideas': 'planning',
    'taxonomy': 'planning',
    'topic_brainstorming': 'planning',
    'section_structure': 'planning',
    'topic_allocation': 'planning',
    'section_titling': 'planning',
    'product_data_review': 'planning',
    'section_content_mapping': 'planning',
    
    # Research substages
    'research': 'research',
    'sources': 'research',
    'visuals': 'research',
    'prompts': 'research',
    'verification': 'research',
    
    # Authoring substages
    'drafting': 'authoring',
    'image_concepts': 'authoring',
    'image_prompts': 'authoring',
    'image_captions': 'authoring',
    'recipe_image_style_prompt': 'authoring',
    
    # Content substages
    'format_content': 'content',
    
    # Imaging substages
    'image_generation': 'imaging',
    'optimise': 'imaging',
    
    # Header substages
    'title_summary': 'header',
    'header_image': 'header',
    'seo_meta': 'header',
    'product_match': 'header',
    'final_review': 'header',
    
    # Channel-specific substages (from output_channel_stages)
    'format_for_facebook': 'content',
    'add_hashtags': 'content',
    'add_translation': 'content',
    'optimize_for_facebook': 'imaging',
    'publish_to_facebook': 'publish',
    'format_for_instagram': 'content',
    'create_caption': 'content',
    'optimize_for_instagram': 'imaging',
    'create_carousel': 'imaging',
    'publish_to_instagram': 'publish',
    'format_for_twitter': 'content',
    'publish_to_twitter': 'publish',
    'format_for_newsletter': 'content',
    'add_to_newsletter': 'publish',
    'extract_summary': 'syndication',
    'publish_to_facebook': 'syndication',
    'publish_to_instagram': 'syndication',
    'publish_to_twitter': 'syndication',
}


def migrate_substage_metadata(cursor):
    """Migrate SUBSTAGE_METADATA to substage_metadata table"""
    print("Migrating substage metadata...")
    
    inserted = 0
    for substage_key, metadata in SUBSTAGE_METADATA.items():
        stage = SUBSTAGE_STAGE_MAP.get(substage_key, 'unknown')
        
        try:
            cursor.execute("""
                INSERT INTO substage_metadata 
                (substage_key, label, route_function, display_order, stage, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (substage_key) DO UPDATE SET
                    label = EXCLUDED.label,
                    route_function = EXCLUDED.route_function,
                    display_order = EXCLUDED.display_order,
                    stage = EXCLUDED.stage,
                    updated_at = NOW()
            """, (
                substage_key,
                metadata.get('label', substage_key.replace('_', ' ').title()),
                metadata.get('route_function'),
                metadata.get('order', 999),
                stage,
                True
            ))
            inserted += 1
        except Exception as e:
            print(f"Error inserting {substage_key}: {e}")
            raise
    
    print(f"  ✓ Inserted/updated {inserted} substage metadata records")
    return inserted


def migrate_post_type_substages(cursor):
    """Migrate POST_TYPE_SUBSTAGES to post_type_substages table"""
    print("Migrating post type substages...")
    
    inserted = 0
    for post_type, stages_dict in POST_TYPE_SUBSTAGES.items():
        for stage, substage_keys in stages_dict.items():
            for order, substage_key in enumerate(substage_keys, start=1):
                try:
                    cursor.execute("""
                        INSERT INTO post_type_substages 
                        (post_type, stage, substage_key, display_order, is_active)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (post_type, stage, substage_key) DO UPDATE SET
                            display_order = EXCLUDED.display_order,
                            is_active = EXCLUDED.is_active,
                            updated_at = NOW()
                    """, (post_type, stage, substage_key, order, True))
                    inserted += 1
                except Exception as e:
                    print(f"Error inserting {post_type}/{stage}/{substage_key}: {e}")
                    raise
    
    print(f"  ✓ Inserted/updated {inserted} post type substage records")
    return inserted


def ensure_channel_substage_metadata(cursor, substage_key, stage):
    """Ensure a substage exists in substage_metadata (for channel-specific substages)"""
    cursor.execute("""
        SELECT id FROM substage_metadata WHERE substage_key = %s
    """, (substage_key,))
    
    if not cursor.fetchone():
        # Create metadata entry for channel-specific substage
        label = substage_key.replace('_', ' ').title()
        cursor.execute("""
            INSERT INTO substage_metadata 
            (substage_key, label, route_function, display_order, stage, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (substage_key) DO NOTHING
        """, (substage_key, label, None, 999, stage, True))


def migrate_output_channel_substages(cursor):
    """Migrate OUTPUT_CHANNEL_STAGES to output_channel_substages table"""
    print("Migrating output channel substages...")
    
    inserted = 0
    skipped = 0
    
    for (post_type, output_channel), config in OUTPUT_CHANNEL_STAGES.items():
        # Skip entries that use post_type config (they'll fall back automatically)
        if config.get('use_post_type_config'):
            skipped += 1
            continue
        
        stages = config.get('stages', [])
        substages_dict = config.get('substages', {})
        
        for stage in stages:
            substage_keys = substages_dict.get(stage, [])
            for order, substage_key in enumerate(substage_keys, start=1):
                # Ensure substage metadata exists
                stage_for_metadata = SUBSTAGE_STAGE_MAP.get(substage_key, stage)
                ensure_channel_substage_metadata(cursor, substage_key, stage_for_metadata)
                
                try:
                    cursor.execute("""
                        INSERT INTO output_channel_substages 
                        (post_type, output_channel, stage, substage_key, display_order, use_post_type_config, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (post_type, output_channel, stage, substage_key) DO UPDATE SET
                            display_order = EXCLUDED.display_order,
                            is_active = EXCLUDED.is_active,
                            updated_at = NOW()
                    """, (post_type, output_channel, stage, substage_key, order, False, True))
                    inserted += 1
                except Exception as e:
                    print(f"Error inserting {post_type}/{output_channel}/{stage}/{substage_key}: {e}")
                    raise
    
    print(f"  ✓ Inserted/updated {inserted} output channel substage records")
    print(f"  ✓ Skipped {skipped} entries using post_type config")
    return inserted


def verify_migration(cursor):
    """Verify migration was successful"""
    print("\nVerifying migration...")
    
    # Check substage_metadata
    cursor.execute("SELECT COUNT(*) as count FROM substage_metadata")
    metadata_row = cursor.fetchone()
    metadata_count = metadata_row['count'] if isinstance(metadata_row, dict) else metadata_row[0]
    print(f"  substage_metadata: {metadata_count} records")
    
    # Check post_type_substages
    cursor.execute("SELECT COUNT(*) as count FROM post_type_substages")
    post_type_row = cursor.fetchone()
    post_type_count = post_type_row['count'] if isinstance(post_type_row, dict) else post_type_row[0]
    print(f"  post_type_substages: {post_type_count} records")
    
    # Check output_channel_substages
    cursor.execute("SELECT COUNT(*) as count FROM output_channel_substages")
    channel_row = cursor.fetchone()
    channel_count = channel_row['count'] if isinstance(channel_row, dict) else channel_row[0]
    print(f"  output_channel_substages: {channel_count} records")
    
    # Verify expected counts
    expected_metadata = len(SUBSTAGE_METADATA)
    expected_post_type = sum(len(stages_dict) * len(substages) 
                            for stages_dict in POST_TYPE_SUBSTAGES.values() 
                            for substages in stages_dict.values())
    
    print(f"\nExpected vs Actual:")
    print(f"  Metadata: {expected_metadata} expected, {metadata_count} actual")
    print(f"  Post Type: ~{expected_post_type} expected, {post_type_count} actual")
    
    if metadata_count < expected_metadata:
        print(f"  ⚠ Warning: Fewer metadata records than expected")
    
    return metadata_count > 0 and post_type_count > 0


def main():
    """Run the migration"""
    print("=" * 60)
    print("Post Type Substages Configuration Migration")
    print("=" * 60)
    print(f"Started at: {datetime.now()}\n")
    
    try:
        with db_manager.get_cursor() as cursor:
            try:
                # Migrate data (autocommit is enabled, so each statement commits immediately)
                migrate_substage_metadata(cursor)
                migrate_post_type_substages(cursor)
                migrate_output_channel_substages(cursor)
                
                # Verify
                if verify_migration(cursor):
                    print("\n" + "=" * 60)
                    print("✓ Migration completed successfully!")
                    print("=" * 60)
                    return 0
                else:
                    print("\n" + "=" * 60)
                    print("✗ Migration verification failed")
                    print("=" * 60)
                    return 1
                    
            except Exception as e:
                print(f"\n✗ Error during migration: {e}")
                import traceback
                traceback.print_exc()
                return 1
                
    except Exception as e:
        print(f"\n✗ Error connecting to database: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

