"""Monitoring service for quirky news pipeline.

Tracks ingestion rates, classification success, selection counts, and alerts on issues.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List
from config.database import db_manager

logger = logging.getLogger(__name__)


def get_pipeline_stats(days_back: int = 7) -> Dict[str, Any]:
    """Get statistics for the quirky news pipeline.
    
    Args:
        days_back: Number of days to look back
    
    Returns:
        Dict with statistics
    """
    cutoff = datetime.now() - timedelta(days=days_back)
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Articles ingested per source
            cur.execute("""
                SELECT 
                    source_name,
                    COUNT(*) as total,
                    COUNT(CASE WHEN heuristic_score > 0 THEN 1 END) as passed_heuristic,
                    COUNT(CASE WHEN llm_class IS NOT NULL THEN 1 END) as classified,
                    COUNT(CASE WHEN llm_class = 'quirky' THEN 1 END) as quirky,
                    COUNT(CASE WHEN selected_for_highlights = TRUE THEN 1 END) as selected
                FROM newsletter_source_item
                WHERE cached_at >= %s
                    AND category = 'news'
                GROUP BY source_name
                ORDER BY total DESC
            """, (cutoff,))
            source_stats = [dict(r) for r in cur.fetchall() or []]
            
            # Overall stats
            cur.execute("""
                SELECT 
                    COUNT(*) as total_articles,
                    COUNT(CASE WHEN heuristic_score >= 3.0 THEN 1 END) as passed_heuristic,
                    COUNT(CASE WHEN llm_class IS NOT NULL THEN 1 END) as classified,
                    COUNT(CASE WHEN llm_class = 'quirky' THEN 1 END) as quirky,
                    COUNT(CASE WHEN llm_quirky_score >= 60 THEN 1 END) as high_quirky_score,
                    COUNT(CASE WHEN selected_for_highlights = TRUE THEN 1 END) as selected,
                    AVG(heuristic_score) as avg_heuristic_score,
                    AVG(llm_quirky_score) as avg_quirky_score
                FROM newsletter_source_item
                WHERE cached_at >= %s
                    AND category = 'news'
            """, (cutoff,))
            overall = dict(cur.fetchone() or {})
            
            # Weekly highlights stats
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT wh.id) as highlights_sets,
                    COUNT(whi.id) as total_items,
                    AVG(item_count.count) as avg_items_per_set
                FROM weekly_highlights wh
                LEFT JOIN weekly_highlights_items whi ON wh.id = whi.weekly_highlights_id
                LEFT JOIN (
                    SELECT weekly_highlights_id, COUNT(*) as count
                    FROM weekly_highlights_items
                    GROUP BY weekly_highlights_id
                ) item_count ON wh.id = item_count.weekly_highlights_id
                WHERE wh.created_at >= %s
            """, (cutoff,))
            highlights_stats = dict(cur.fetchone() or {})
            
            # LLM error rates (from classification attempts)
            cur.execute("""
                SELECT 
                    COUNT(*) as total_attempts,
                    COUNT(CASE WHEN llm_class IS NULL AND heuristic_score >= 3.0 THEN 1 END) as failed_classifications
                FROM newsletter_source_item
                WHERE cached_at >= %s
                    AND category = 'news'
                    AND heuristic_score >= 3.0
            """, (cutoff,))
            llm_stats = dict(cur.fetchone() or {})
            
            return {
                'period_days': days_back,
                'overall': overall,
                'by_source': source_stats,
                'highlights': highlights_stats,
                'llm': llm_stats,
                'generated_at': datetime.now().isoformat()
            }


def check_alerts() -> List[Dict[str, Any]]:
    """Check for pipeline issues and return alerts.
    
    Returns:
        List of alert dicts with 'level', 'message', 'details'
    """
    alerts = []
    stats = get_pipeline_stats(days_back=7)
    
    # Check for sources with no articles
    major_sources = ['BBC Scotland', 'The Scotsman', 'The Herald']
    for source_stat in stats.get('by_source', []):
        source_name = source_stat.get('source_name', '')
        if source_name in major_sources and source_stat.get('total', 0) == 0:
            alerts.append({
                'level': 'warning',
                'message': f'No articles from {source_name} in last 7 days',
                'details': source_stat
            })
    
    # Check for low classification rate
    overall = stats.get('overall', {})
    total = overall.get('total_articles', 0)
    classified = overall.get('classified', 0)
    if total > 0:
        classification_rate = classified / total
        if classification_rate < 0.5:
            alerts.append({
                'level': 'warning',
                'message': f'Low classification rate: {classification_rate:.1%}',
                'details': {'total': total, 'classified': classified}
            })
    
    # Check for empty weekly highlights
    highlights = stats.get('highlights', {})
    if highlights.get('highlights_sets', 0) == 0:
        alerts.append({
            'level': 'info',
            'message': 'No weekly highlights sets created in last 7 days',
            'details': highlights
        })
    elif highlights.get('total_items', 0) < 3:
        alerts.append({
            'level': 'warning',
            'message': f'Low weekly highlights count: {highlights.get("total_items", 0)} items',
            'details': highlights
        })
    
    # Check for high LLM failure rate
    llm_stats = stats.get('llm', {})
    total_attempts = llm_stats.get('total_attempts', 0)
    failed = llm_stats.get('failed_classifications', 0)
    if total_attempts > 0:
        failure_rate = failed / total_attempts
        if failure_rate > 0.3:
            alerts.append({
                'level': 'error',
                'message': f'High LLM classification failure rate: {failure_rate:.1%}',
                'details': {'total_attempts': total_attempts, 'failed': failed}
            })
    
    return alerts


def log_pipeline_metrics() -> None:
    """Log pipeline metrics for monitoring."""
    stats = get_pipeline_stats()
    alerts = check_alerts()
    
    logger.info(f"Pipeline stats (7 days): {stats.get('overall', {})}")
    logger.info(f"Highlights: {stats.get('highlights', {})}")
    
    if alerts:
        for alert in alerts:
            if alert['level'] == 'error':
                logger.error(f"Alert: {alert['message']} - {alert.get('details', {})}")
            elif alert['level'] == 'warning':
                logger.warning(f"Alert: {alert['message']} - {alert.get('details', {})}")
            else:
                logger.info(f"Alert: {alert['message']} - {alert.get('details', {})}")

