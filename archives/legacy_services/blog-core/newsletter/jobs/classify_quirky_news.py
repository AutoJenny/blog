"""Batch job to classify quirky news articles using LLM.

Processes articles that have passed heuristic filtering but haven't been
classified yet.
"""

from __future__ import annotations

import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

# Add project root to path if config module not found
try:
    import config
except ImportError:
    # Running as script - add path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    sys.path.insert(0, project_root)
    blog_core = os.path.join(project_root, 'blog-core')
    sys.path.insert(0, blog_core)

from config.database import db_manager
from newsletter.services.quirky_classification_service import classify_quirky_article

logger = logging.getLogger(__name__)


def run(threshold: float = 3.0, days_back: int = 14, batch_size: int = 10) -> Dict[str, Any]:
    """Run batch classification job.
    
    Args:
        threshold: Minimum heuristic_score to process
        days_back: How many days back to look for articles
        batch_size: Number of articles to process per batch
    
    Returns:
        Result dict with counts and errors
    """
    logger.info(f"Starting quirky news classification (threshold={threshold}, days_back={days_back})")
    
    start_time = datetime.now()
    processed = 0
    classified = 0
    errors = []
    
    try:
        # Get candidates
        candidates = _get_classification_candidates(threshold, days_back, limit=batch_size * 5)
        logger.info(f"Found {len(candidates)} candidate articles")
        
        if not candidates:
            return {
                'success': True,
                'processed': 0,
                'classified': 0,
                'errors': [],
                'message': 'No candidates found'
            }
        
        # Process in batches
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1} ({len(batch)} articles)")
            
            for article in batch:
                try:
                    processed += 1
                    classification = classify_quirky_article(article, use_cache=True)
                    
                    # Update database
                    _update_article_classification(article['id'], classification)
                    classified += 1
                    
                except Exception as e:
                    error_msg = f"Error classifying article {article.get('id')}: {e}"
                    logger.error(error_msg, exc_info=True)
                    errors.append(error_msg)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        result = {
            'success': True,
            'processed': processed,
            'classified': classified,
            'errors': errors,
            'duration_seconds': elapsed,
            'completed_at': datetime.now().isoformat()
        }
        
        logger.info(f"Classification complete: {classified}/{processed} classified in {elapsed:.2f}s")
        return result
        
    except Exception as e:
        logger.error(f"Classification job failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'processed': processed,
            'classified': classified,
            'errors': errors
        }


def _get_classification_candidates(threshold: float, days_back: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Get articles that need classification.
    
    Only processes articles from LOCAL WEEKLY NEWSPAPERS (sources with region set).
    National newspapers (BBC Scotland, The Herald, The Scotsman) are excluded.
    """
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT nsi.id, nsi.source_name, nsi.title, nsi.url, nsi.published_at, 
                       nsi.location, nsi.category, nsi.raw_data, nsi.heuristic_score, nsi.heuristic_flags
                FROM newsletter_source_item nsi
                INNER JOIN newsletter_snapshot_source ns ON nsi.source_name = ns.name
                WHERE nsi.heuristic_score >= %s
                AND nsi.llm_class IS NULL
                AND (nsi.published_at >= %s OR nsi.cached_at >= %s)
                AND nsi.category = 'news'
                AND ns.region IS NOT NULL  -- Only local weekly newspapers
                ORDER BY nsi.heuristic_score DESC, nsi.published_at DESC
                LIMIT %s
            """, (threshold, cutoff_date, cutoff_date, limit))
            
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]


def _update_article_classification(article_id: int, classification: Dict[str, Any]) -> None:
    """Update article with classification results."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE newsletter_source_item
                SET llm_class = %s,
                    llm_quirky_score = %s,
                    llm_summary_raw = %s,
                    safety_flag = %s
                WHERE id = %s
            """, (
                classification.get('llm_class'),
                classification.get('llm_quirky_score'),
                classification.get('llm_summary_raw'),
                classification.get('safety_flag'),
                article_id
            ))
            conn.commit()


if __name__ == '__main__':
    import sys
    import os
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    result = run()
    
    if result.get('success'):
        print(f"✓ Classification complete: {result.get('classified')}/{result.get('processed')} classified")
        sys.exit(0)
    else:
        print(f"✗ Classification failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

