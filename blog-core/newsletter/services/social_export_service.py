"""Social media export service for Round Scotland highlights.

Exports quirky news summaries in formats suitable for Facebook, Instagram, Twitter.
"""

from __future__ import annotations

import json
import csv
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List
from config.database import db_manager

logger = logging.getLogger(__name__)


def export_weekly_highlights_social(
    issue_id: int,
    format: str = 'json',
    include_utms: bool = True,
    suggested_days_ahead: int = 1
) -> str | Dict[str, Any]:
    """Export weekly highlights for social media posting.
    
    Args:
        issue_id: Newsletter issue ID
        format: Export format ('json', 'csv', 'facebook', 'instagram', 'twitter')
        include_utms: Whether to include UTM parameters in links
        suggested_days_ahead: Days ahead to suggest posting dates (default: 1)
    
    Returns:
        Exported content as string (for CSV/text formats) or dict (for JSON)
    """
    logger.info(f"Exporting social media content for issue {issue_id}, format: {format}")
    
    # Get weekly highlights for issue
    highlights = _get_weekly_highlights(issue_id)
    if not highlights:
        return {'error': 'No weekly highlights found for this issue'}
    
    # Get highlight items
    items = _get_highlight_items(highlights['id'])
    if not items:
        return {'error': 'No highlight items found'}
    
    # Format based on requested format
    if format == 'json':
        return _export_json(items, include_utms, suggested_days_ahead)
    elif format == 'csv':
        return _export_csv(items, include_utms, suggested_days_ahead)
    elif format == 'facebook':
        return _export_facebook(items, include_utms, suggested_days_ahead)
    elif format == 'instagram':
        return _export_instagram(items, include_utms, suggested_days_ahead)
    elif format == 'twitter':
        return _export_twitter(items, include_utms, suggested_days_ahead)
    else:
        return {'error': f'Unknown format: {format}'}


def _get_weekly_highlights(issue_id: int) -> Dict[str, Any] | None:
    """Get weekly highlights record for issue."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, issue_id, week_start, week_end, created_at
                FROM weekly_highlights
                WHERE issue_id = %s
            """, (issue_id,))
            row = cur.fetchone()
            if row:
                return dict(row)
            return None


def _get_highlight_items(highlights_id: int) -> List[Dict[str, Any]]:
    """Get all items for a weekly highlights set."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    whi.id,
                    whi.position,
                    whi.title_internal,
                    whi.summary_newsletter,
                    whi.summary_social,
                    whi.location_label,
                    whi.source_label,
                    whi.permalink,
                    whi.selected_image_url,
                    whi.remote_image_url,
                    nsi.title,
                    nsi.url
                FROM weekly_highlights_items whi
                JOIN newsletter_source_item nsi ON whi.article_id = nsi.id
                WHERE whi.weekly_highlights_id = %s
                ORDER BY whi.position
            """, (highlights_id,))
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]


def _export_json(items: List[Dict[str, Any]], include_utms: bool, days_ahead: int) -> Dict[str, Any]:
    """Export as JSON structure."""
    base_date = datetime.now() + timedelta(days=days_ahead)
    
    posts = []
    for idx, item in enumerate(items):
        post_date = base_date + timedelta(days=idx)
        permalink = item.get('permalink') or item.get('url', '')
        if include_utms and permalink:
            permalink = _add_utm_params(permalink, 'social', item.get('source_label', ''))
        
        posts.append({
            'suggested_date': post_date.strftime('%Y-%m-%d'),
            'platform': 'all',
            'title': item.get('title_internal') or item.get('title', ''),
            'text': item.get('summary_social') or item.get('summary_newsletter', ''),
            'location': item.get('location_label', ''),
            'source': item.get('source_label', ''),
            'link': permalink,
            'image_url': item.get('remote_image_url') or item.get('selected_image_url'),
        })
    
    return {
        'export_date': datetime.now().isoformat(),
        'issue_id': items[0].get('issue_id') if items else None,
        'posts': posts
    }


def _export_csv(items: List[Dict[str, Any]], include_utms: bool, days_ahead: int) -> str:
    """Export as CSV format."""
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Date', 'Platform', 'Title', 'Text', 'Location', 'Source', 'Link', 'Image URL'
    ])
    
    base_date = datetime.now() + timedelta(days=days_ahead)
    for idx, item in enumerate(items):
        post_date = base_date + timedelta(days=idx)
        permalink = item.get('permalink') or item.get('url', '')
        if include_utms and permalink:
            permalink = _add_utm_params(permalink, 'social', item.get('source_label', ''))
        
        writer.writerow([
            post_date.strftime('%Y-%m-%d'),
            'all',
            item.get('title_internal') or item.get('title', ''),
            item.get('summary_social') or item.get('summary_newsletter', ''),
            item.get('location_label', ''),
            item.get('source_label', ''),
            permalink,
            item.get('remote_image_url') or item.get('selected_image_url', ''),
        ])
    
    return output.getvalue()


def _export_facebook(items: List[Dict[str, Any]], include_utms: bool, days_ahead: int) -> str:
    """Export as Facebook-ready text posts."""
    base_date = datetime.now() + timedelta(days=days_ahead)
    posts = []
    
    for idx, item in enumerate(items):
        post_date = base_date + timedelta(days=idx)
        text = item.get('summary_social') or item.get('summary_newsletter', '')
        location = item.get('location_label', '')
        source = item.get('source_label', '')
        permalink = item.get('permalink') or item.get('url', '')
        
        if include_utms and permalink:
            permalink = _add_utm_params(permalink, 'facebook', source)
        
        post = f"📅 {post_date.strftime('%Y-%m-%d')}\n\n"
        post += f"{text}\n\n"
        if location:
            post += f"📍 {location}\n"
        if source:
            post += f"📰 {source}\n"
        if permalink:
            post += f"\n🔗 {permalink}"
        
        posts.append(post)
    
    return "\n\n---\n\n".join(posts)


def _export_instagram(items: List[Dict[str, Any]], include_utms: bool, days_ahead: int) -> str:
    """Export as Instagram-ready captions."""
    base_date = datetime.now() + timedelta(days=days_ahead)
    posts = []
    
    for idx, item in enumerate(items):
        post_date = base_date + timedelta(days=idx)
        text = item.get('summary_social') or item.get('summary_newsletter', '')
        location = item.get('location_label', '')
        source = item.get('source_label', '')
        permalink = item.get('permalink') or item.get('url', '')
        
        if include_utms and permalink:
            permalink = _add_utm_params(permalink, 'instagram', source)
        
        # Instagram captions (shorter, with hashtags)
        post = f"{text}\n\n"
        if location:
            post += f"📍 {location}\n"
        if source:
            post += f"📰 {source}\n"
        post += "\n#Scotland #ScottishNews #LocalNews #RoundScotland"
        if location:
            # Add location hashtag (simplified)
            location_tag = location.split(',')[0].replace(' ', '')
            post += f" #{location_tag}"
        if permalink:
            post += f"\n\n🔗 Link in bio"
        
        posts.append(f"Date: {post_date.strftime('%Y-%m-%d')}\n\n{post}")
    
    return "\n\n---\n\n".join(posts)


def _export_twitter(items: List[Dict[str, Any]], include_utms: bool, days_ahead: int) -> str:
    """Export as Twitter-ready tweets (280 char limit)."""
    base_date = datetime.now() + timedelta(days=days_ahead)
    posts = []
    
    for idx, item in enumerate(items):
        post_date = base_date + timedelta(days=idx)
        text = item.get('summary_social') or item.get('summary_newsletter', '')
        location = item.get('location_label', '')
        source = item.get('source_label', '')
        permalink = item.get('permalink') or item.get('url', '')
        
        if include_utms and permalink:
            permalink = _add_utm_params(permalink, 'twitter', source)
        
        # Truncate to fit Twitter limit (280 chars)
        # Format: text + location + source + link
        tweet = text[:200]  # Reserve space for location, source, link
        if location:
            tweet += f" 📍{location}"
        if source:
            tweet += f" 📰{source}"
        if permalink:
            # Use short link if available, otherwise truncate
            tweet += f" {permalink[:50]}"
        
        if len(tweet) > 280:
            # Truncate more aggressively
            available = 280 - len(f" 📍{location} 📰{source} {permalink[:30]}")
            tweet = text[:available-3] + "..." + f" 📍{location} 📰{source} {permalink[:30]}"
        
        posts.append(f"Date: {post_date.strftime('%Y-%m-%d')}\n{tweet}")
    
    return "\n\n---\n\n".join(posts)


def _add_utm_params(url: str, medium: str, source: str) -> str:
    """Add UTM parameters to URL."""
    from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
    
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    params['utm_source'] = [source.replace(' ', '_').lower()[:50]]
    params['utm_medium'] = [medium]
    params['utm_campaign'] = ['round_scotland']
    
    new_query = urlencode(params, doseq=True)
    new_parsed = parsed._replace(query=new_query)
    return urlunparse(new_parsed)

