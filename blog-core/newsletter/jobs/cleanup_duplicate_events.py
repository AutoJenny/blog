"""Cleanup script to remove duplicate events from newsletter_source_item."""

from __future__ import annotations

import logging
import sys
from typing import List, Dict, Any

# Add blog-core to path
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
blog_core_dir = os.path.join(script_dir, '../..')
sys.path.insert(0, os.path.abspath(blog_core_dir))

from config.database import db_manager
from newsletter.services.event_deduplication_service import find_all_duplicates, normalize_title, calculate_title_similarity

logger = logging.getLogger(__name__)


def cleanup_duplicates(dry_run: bool = True) -> Dict[str, Any]:
    """Clean up duplicate events, keeping the best one from each group.
    
    Args:
        dry_run: If True, only report what would be deleted, don't actually delete
    
    Returns:
        Dict with cleanup summary
    """
    duplicate_groups = find_all_duplicates()
    
    total_duplicates = sum(len(group['ids']) - 1 for group in duplicate_groups)  # Minus 1 to keep best
    total_groups = len(duplicate_groups)
    
    logger.info(f"Found {total_groups} duplicate groups ({total_duplicates} duplicates to remove)")
    
    deleted = 0
    kept = 0
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            for group in duplicate_groups:
                ids = group['ids']
                if len(ids) <= 1:
                    continue
                
                # Get all events in this group to determine which to keep
                cur.execute("""
                    SELECT id, title, url, event_date, location, cached_at, 
                           combined_score, suitability_score
                    FROM newsletter_source_item
                    WHERE id = ANY(%s)
                    ORDER BY 
                        CASE WHEN event_date IS NOT NULL THEN 0 ELSE 1 END,  -- Prefer ones with dates
                        CASE WHEN url IS NOT NULL THEN 0 ELSE 1 END,  -- Prefer ones with URLs
                        CASE WHEN location IS NOT NULL THEN 0 ELSE 1 END,  -- Prefer ones with locations
                        combined_score DESC NULLS LAST,  -- Prefer higher scores
                        cached_at DESC  -- Prefer most recently cached
                """, (ids,))
                
                events = cur.fetchall()
                if not events:
                    continue
                
                # Keep the first (best) one
                keep_id = events[0]['id']
                delete_ids = [e['id'] for e in events[1:]]
                
                logger.info(f"\nGroup: {group['title'][:60]}")
                logger.info(f"  Source: {group['source']}")
                logger.info(f"  Keeping ID {keep_id}: {events[0]['title'][:60]}")
                logger.info(f"  Deleting {len(delete_ids)} duplicates: {delete_ids}")
                
                if not dry_run:
                    # Delete duplicates
                    cur.execute("""
                        DELETE FROM newsletter_source_item
                        WHERE id = ANY(%s)
                    """, (delete_ids,))
                    
                    deleted += len(delete_ids)
                    kept += 1
                else:
                    deleted += len(delete_ids)
                    kept += 1
            
            if not dry_run:
                conn.commit()
                logger.info(f"\nCleanup complete: Deleted {deleted} duplicates, kept {kept} originals")
            else:
                logger.info(f"\nDry run complete: Would delete {deleted} duplicates, keep {kept} originals")
    
    return {
        'groups_found': total_groups,
        'duplicates_found': total_duplicates,
        'deleted': deleted if not dry_run else 0,
        'would_delete': deleted if dry_run else 0,
        'kept': kept,
        'dry_run': dry_run,
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up duplicate events')
    parser.add_argument('--execute', action='store_true', help='Actually delete duplicates (default is dry-run)')
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    result = cleanup_duplicates(dry_run=not args.execute)
    
    print(f"\n{'='*80}")
    print(f"Cleanup Summary:")
    print(f"  Groups found: {result['groups_found']}")
    print(f"  Duplicates found: {result['duplicates_found']}")
    if args.execute:
        print(f"  Deleted: {result['deleted']}")
    else:
        print(f"  Would delete: {result['would_delete']}")
    print(f"  Kept: {result['kept']}")
    print(f"{'='*80}")

