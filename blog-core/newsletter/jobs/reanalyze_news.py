"""Re-analyze existing news items with synopsis service."""

from __future__ import annotations

import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta, date
from config.database import db_manager
from newsletter.services.news_synopsis_service import process_news_with_synopsis
from newsletter.services.scoring import score_items
from newsletter.db.queries_sources import store_source_items

logger = logging.getLogger(__name__)


def reanalyze_news_items(days_back: int = 30, limit: int = 50) -> Dict[str, Any]:
    """Re-analyze existing news items that haven't been processed with synopsis service.
    
    Args:
        days_back: Number of days to look back
        limit: Maximum number of items to process
        
    Returns:
        Dict with results
    """
    today = date.today()
    start_date = today - timedelta(days=days_back)
    
    # Get news items to re-analyze: those without scores, OR those with existing scores (to force re-analysis)
    sql = """
        SELECT id, source_name, title, url, published_at, category,
               raw_data, suitability_score
        FROM newsletter_source_item
        WHERE category = 'news'
          AND published_at IS NOT NULL
          AND published_at::date >= %s
        ORDER BY 
          CASE WHEN suitability_score IS NULL THEN 0 ELSE 1 END,
          published_at DESC
        LIMIT %s
    """
    
    items_to_process = []
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (start_date, limit))
            rows = cur.fetchall() or []
            for row in rows:
                items_to_process.append({
                    'id': row['id'],
                    'source_name': row['source_name'],
                    'title': row['title'],
                    'url': row['url'],
                    'published_at': row['published_at'],
                    'category': row['category'],
                    'raw_data': row['raw_data'] or {},
                })
    
    logger.info(f"Found {len(items_to_process)} news items to re-analyze")
    
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    for item in items_to_process:
        try:
            # Process with synopsis service (force re-analysis, ignore cache)
            processed = process_news_with_synopsis(item, cache_results=False)
            
            if processed:
                # Always update the score, even if below threshold
                # Score the item
                scored = score_items([processed])
                
                # Update in database (store_source_items handles deduplication)
                stored = store_source_items(scored)
                
                final_score = processed.get('suitability_score', 0)
                if final_score >= 6.0:
                    processed_count += 1
                    logger.info(f"✓ Re-analyzed: {item['title'][:50]} (score: {final_score})")
                else:
                    skipped_count += 1
                    logger.debug(f"Re-scored below threshold: {item['title'][:50]} (score: {final_score})")
            else:
                skipped_count += 1
                logger.debug(f"Failed to process: {item['title'][:50]}")
                
        except Exception as e:
            error_count += 1
            logger.error(f"Error re-analyzing {item['title'][:50]}: {e}", exc_info=True)
            continue
    
    return {
        'total_found': len(items_to_process),
        'processed': processed_count,
        'skipped': skipped_count,
        'errors': error_count,
    }


if __name__ == '__main__':
    import sys
    sys.path.insert(0, '../../..')
    
    result = reanalyze_news_items(days_back=30, limit=50)
    print(f"Re-analyzed {result['processed']} items, skipped {result['skipped']}, errors {result['errors']}")

