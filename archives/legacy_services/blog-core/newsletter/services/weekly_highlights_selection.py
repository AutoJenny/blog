"""Weekly selection service for quirky news highlights.

Selects the best quirky stories for a newsletter issue with regional diversity.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List
from config.database import db_manager

logger = logging.getLogger(__name__)


def select_weekly_highlights(issue_id: int, target_week: str, 
                             quirky_score_threshold: int = 60,
                             max_per_region: int = 2,
                             max_total: int = 8) -> Dict[str, Any]:
    """Select weekly highlights for an issue.
    
    Args:
        issue_id: Newsletter issue ID
        target_week: Target week string (e.g., "2025W44")
        quirky_score_threshold: Minimum llm_quirky_score (default: 60)
        max_per_region: Maximum items per region (default: 2)
        max_total: Maximum total items (default: 8)
    
    Returns:
        Dict with selection results
    """
    logger.info(f"Selecting weekly highlights for issue {issue_id}, week {target_week}")
    
    # Calculate week dates
    week_start, week_end = _parse_week(target_week)
    if not week_start:
        return {'success': False, 'error': f'Invalid week format: {target_week}'}
    
    # Get candidates
    candidates = _get_candidates(week_start, week_end, quirky_score_threshold)
    logger.info(f"Found {len(candidates)} candidate articles")
    
    if not candidates:
        return {
            'success': True,
            'selected_count': 0,
            'message': 'No candidates found'
        }
    
    # Apply diversity rules and select
    selected = _apply_diversity_selection(candidates, max_per_region, max_total)
    logger.info(f"Selected {len(selected)} articles with diversity rules")
    
    # Create weekly_highlights record
    highlights_id = _create_weekly_highlights(issue_id, week_start, week_end)
    
    # Create highlight items
    items_created = _create_highlight_items(highlights_id, selected)
    
    # Mark articles as selected
    _mark_articles_selected([item['article_id'] for item in selected])
    
    return {
        'success': True,
        'highlights_id': highlights_id,
        'selected_count': items_created,
        'articles': selected
    }


def _parse_week(week_str: str) -> tuple[datetime, datetime]:
    """Parse week string (e.g., "2025W44") into start and end dates."""
    try:
        # Format: YYYYWww
        year = int(week_str[:4])
        week_num = int(week_str[5:])
        
        # Calculate start date (Monday of that week)
        jan1 = datetime(year, 1, 1)
        # Find first Monday
        days_offset = (7 - jan1.weekday()) % 7
        first_monday = jan1 + timedelta(days=days_offset)
        
        # Week 1 starts on first Monday, so week N starts N-1 weeks later
        week_start = first_monday + timedelta(weeks=week_num - 1)
        week_end = week_start + timedelta(days=6)
        
        return (week_start, week_end)
    except Exception as e:
        logger.error(f"Failed to parse week {week_str}: {e}")
        return (None, None)


def _get_candidates(week_start: datetime, week_end: datetime, 
                    quirky_score_threshold: int) -> List[Dict[str, Any]]:
    """Get candidate articles for selection."""
    # Look for articles published in the last 7 days before week_end
    date_cutoff = week_end - timedelta(days=7)
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT nsi.id, nsi.source_name, nsi.title, nsi.url, nsi.published_at,
                       nsi.location, nsi.llm_quirky_score, nsi.llm_summary_raw,
                       nsi.safety_flag, nsi.available_images,
                       ns.region
                FROM newsletter_source_item nsi
                INNER JOIN newsletter_snapshot_source ns ON nsi.source_name = ns.name
                WHERE nsi.llm_class = 'quirky'
                AND nsi.llm_quirky_score >= %s
                AND (nsi.safety_flag IS NULL OR nsi.safety_flag NOT IN ('death', 'serious_illness', 'crime'))
                AND nsi.published_at >= %s
                AND nsi.published_at <= %s
                AND (nsi.selected_for_highlights = FALSE OR nsi.selected_for_highlights IS NULL)
                AND ns.region IS NOT NULL  -- Only local weekly newspapers
                ORDER BY nsi.llm_quirky_score DESC, nsi.published_at DESC
                LIMIT 100
            """, (quirky_score_threshold, date_cutoff, week_end))
            
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]


def _apply_diversity_selection(candidates: List[Dict[str, Any]], 
                                max_per_region: int, max_total: int) -> List[Dict[str, Any]]:
    """Apply diversity rules and select articles.
    
    Groups by region and limits per region, then selects top scoring.
    """
    # Group by region
    by_region: Dict[str, List[Dict[str, Any]]] = {}
    no_region = []
    
    for candidate in candidates:
        region = candidate.get('region') or 'Unknown'
        if region == 'Unknown':
            no_region.append(candidate)
        else:
            if region not in by_region:
                by_region[region] = []
            by_region[region].append(candidate)
    
    # Select from each region
    selected = []
    for region, articles in by_region.items():
        # Sort by quirky score
        articles.sort(key=lambda x: x.get('llm_quirky_score', 0), reverse=True)
        selected.extend(articles[:max_per_region])
    
    # Add from no-region group if space
    remaining = max_total - len(selected)
    if remaining > 0 and no_region:
        no_region.sort(key=lambda x: x.get('llm_quirky_score', 0), reverse=True)
        selected.extend(no_region[:remaining])
    
    # Sort all selected by score and limit to max_total
    selected.sort(key=lambda x: x.get('llm_quirky_score', 0), reverse=True)
    selected = selected[:max_total]
    
    return selected


def _create_weekly_highlights(issue_id: int, week_start: datetime, week_end: datetime) -> int:
    """Create weekly_highlights record."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Check if exists
            cur.execute("""
                SELECT id FROM weekly_highlights WHERE issue_id = %s
            """, (issue_id,))
            existing = cur.fetchone()
            
            if existing:
                return existing[0]
            
            # Create new
            cur.execute("""
                INSERT INTO weekly_highlights (issue_id, week_start, week_end)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (issue_id, week_start.date(), week_end.date()))
            
            highlights_id = cur.fetchone()[0]
            conn.commit()
            return highlights_id


def _create_highlight_items(highlights_id: int, articles: List[Dict[str, Any]]) -> int:
    """Create weekly_highlights_items records."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Delete existing items for this highlights set
            cur.execute("""
                DELETE FROM weekly_highlights_items WHERE weekly_highlights_id = %s
            """, (highlights_id,))
            
            # Insert new items
            for position, article in enumerate(articles, 1):
                cur.execute("""
                    INSERT INTO weekly_highlights_items
                    (weekly_highlights_id, article_id, position, permalink)
                    VALUES (%s, %s, %s, %s)
                """, (highlights_id, article['id'], position, article.get('url')))
            
            conn.commit()
            return len(articles)


def _mark_articles_selected(article_ids: List[int]) -> None:
    """Mark articles as selected for highlights."""
    if not article_ids:
        return
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE newsletter_source_item
                SET selected_for_highlights = TRUE
                WHERE id = ANY(%s)
            """, (article_ids,))
            conn.commit()

