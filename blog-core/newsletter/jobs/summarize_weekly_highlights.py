"""Batch job to summarize all items in a weekly highlights set."""

from __future__ import annotations

import logging
from typing import Any, Dict
from config.database import db_manager
from newsletter.services.quirky_summarization_service import summarize_highlight_item

logger = logging.getLogger(__name__)


def run(highlights_id: int) -> Dict[str, Any]:
    """Summarize all items in a weekly highlights set.
    
    Args:
        highlights_id: weekly_highlights.id
    
    Returns:
        Result dict with counts and errors
    """
    logger.info(f"Summarizing weekly highlights {highlights_id}")
    
    # Get all items
    items = _get_highlight_items(highlights_id)
    logger.info(f"Found {len(items)} items to summarize")
    
    if not items:
        return {
            'success': True,
            'processed': 0,
            'summarized': 0,
            'errors': []
        }
    
    processed = 0
    summarized = 0
    errors = []
    
    for item in items:
        try:
            processed += 1
            result = summarize_highlight_item(item['id'])
            
            if result.get('success'):
                summarized += 1
            else:
                errors.append(f"Item {item['id']}: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            error_msg = f"Item {item['id']}: {e}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
    
    return {
        'success': True,
        'processed': processed,
        'summarized': summarized,
        'errors': errors
    }


def _get_highlight_items(highlights_id: int) -> list[Dict[str, Any]]:
    """Get all items for a highlights set."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, position, article_id
                FROM weekly_highlights_items
                WHERE weekly_highlights_id = %s
                ORDER BY position
            """, (highlights_id,))
            
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]


if __name__ == '__main__':
    import sys
    import os
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python summarize_weekly_highlights.py <highlights_id>")
        sys.exit(1)
    
    highlights_id = int(sys.argv[1])
    result = run(highlights_id)
    
    if result.get('success'):
        print(f"✓ Summarization complete: {result.get('summarized')}/{result.get('processed')} summarized")
        if result.get('errors'):
            print(f"  Errors: {len(result.get('errors'))}")
        sys.exit(0)
    else:
        print(f"✗ Summarization failed")
        sys.exit(1)

