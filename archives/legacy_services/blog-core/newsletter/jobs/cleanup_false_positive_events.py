"""Cleanup script to remove false positive events (page headings) from existing database."""

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
from newsletter.services.event_filtering_service import is_likely_false_positive
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)


def cleanup_false_positives(dry_run: bool = True) -> Dict[str, Any]:
    """Clean up false positive events from the database.
    
    Args:
        dry_run: If True, only report what would be deleted, don't actually delete
    
    Returns:
        Dict with cleanup summary
    """
    with db_manager.get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            # Get all events
            cur.execute("""
                SELECT id, title, url, source_name, event_date, location, raw_data
                FROM newsletter_source_item
                WHERE category = 'event'
                ORDER BY cached_at DESC
            """)
            
            events = cur.fetchall()
    
    false_positives = []
    valid_events = []
    
    for event in events:
        is_false, reason = is_likely_false_positive(dict(event))
        if is_false:
            false_positives.append({
                'id': event['id'],
                'title': event['title'],
                'source': event['source_name'],
                'url': event.get('url'),
                'reason': reason
            })
        else:
            valid_events.append(event)
    
    logger.info(f"Found {len(false_positives)} false positive events out of {len(events)} total")
    
    deleted = 0
    
    if false_positives and not dry_run:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                for fp in false_positives:
                    logger.info(f"Deleting false positive: {fp['title'][:60]} ({fp['reason']})")
                    cur.execute("""
                        DELETE FROM newsletter_source_item
                        WHERE id = %s
                    """, (fp['id'],))
                    deleted += 1
                
                conn.commit()
                logger.info(f"Deleted {deleted} false positive events")
    
    return {
        'total_events': len(events),
        'false_positives': len(false_positives),
        'deleted': deleted if not dry_run else 0,
        'would_delete': len(false_positives) if dry_run else 0,
        'valid_events': len(valid_events),
        'dry_run': dry_run,
        'examples': false_positives[:20] if false_positives else [],
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up false positive events')
    parser.add_argument('--execute', action='store_true', help='Actually delete false positives (default is dry-run)')
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    result = cleanup_false_positives(dry_run=not args.execute)
    
    print(f"\n{'='*80}")
    print(f"False Positive Cleanup Summary:")
    print(f"  Total events: {result['total_events']}")
    print(f"  False positives found: {result['false_positives']}")
    print(f"  Valid events: {result['valid_events']}")
    if args.execute:
        print(f"  Deleted: {result['deleted']}")
    else:
        print(f"  Would delete: {result['would_delete']}")
    
    if result['examples']:
        print(f"\n  Examples of false positives:")
        for fp in result['examples'][:10]:
            print(f"    - {fp['title'][:60]} ({fp['reason']})")
    print(f"{'='*80}")

