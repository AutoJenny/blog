"""Round Scotland editorial UI routes.

Provides interface for reviewing, editing, and managing weekly quirky news highlights.
"""

from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from typing import List, Dict, Any
import os, sys

# Ensure the newsletter package (under blog-core/newsletter) is importable
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-core'))

from newsletter.db.queries_issue import get_issue
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('newsletter_round_scotland', __name__)


@bp.route('/newsletter/issue/<int:issue_id>/round-scotland')
def overview(issue_id: int):
    """Overview page showing all selected highlights for an issue."""
    try:
        issue = get_issue(issue_id=issue_id)
        if not issue:
            return redirect(url_for('newsletter.newsletter_issues.dashboard'))
        
        # Get weekly highlights for this issue
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT wh.id, wh.week_start, wh.week_end, wh.created_at
                    FROM weekly_highlights wh
                    WHERE wh.issue_id = %s
                """, (issue_id,))
                row = cur.fetchone()
                
                if not row:
                    return render_template('newsletter/round_scotland/overview.html',
                                         issue_id=issue_id,
                                         issue=issue,
                                         highlights=None,
                                         items=[])
                
                highlights = dict(row)
                highlights_id = highlights['id']
                
                # Get items
                cur.execute("""
                    SELECT whi.id, whi.position, whi.title_internal, whi.summary_newsletter,
                           whi.summary_social, whi.location_label, whi.source_label,
                           whi.permalink, whi.selected_image_url, whi.selected_image_caption,
                           whi.selected_image_credit, whi.remote_image_url,
                           nsi.title, nsi.url, nsi.source_name, nsi.llm_quirky_score,
                           nsi.available_images
                    FROM weekly_highlights_items whi
                    JOIN newsletter_source_item nsi ON whi.article_id = nsi.id
                    WHERE whi.weekly_highlights_id = %s
                    ORDER BY whi.position
                """, (highlights_id,))
                rows = cur.fetchall() or []
                items = [dict(r) for r in rows]
        
        return render_template('newsletter/round_scotland/overview.html',
                             issue_id=issue_id,
                             issue=issue,
                             highlights=highlights,
                             items=items)
    except Exception as e:
        logger.error(f"Error in round-scotland overview: {e}", exc_info=True)
        return redirect(url_for('newsletter.newsletter_issues.view_issue', issue_id=issue_id))


@bp.route('/newsletter/issue/<int:issue_id>/round-scotland/item/<int:item_id>/edit')
def edit_item(issue_id: int, item_id: int):
    """Edit page for a single highlight item."""
    try:
        issue = get_issue(issue_id=issue_id)
        if not issue:
            return redirect(url_for('newsletter.newsletter_issues.dashboard'))
        
        # Get item data
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT whi.id, whi.position, whi.title_internal, whi.summary_newsletter,
                           whi.summary_social, whi.location_label, whi.source_label,
                           whi.permalink, whi.selected_image_url, whi.selected_image_caption,
                           whi.selected_image_credit, whi.remote_image_url,
                           nsi.id as article_id, nsi.title, nsi.url, nsi.source_name,
                           nsi.llm_quirky_score, nsi.available_images, nsi.llm_summary_raw
                    FROM weekly_highlights_items whi
                    JOIN newsletter_source_item nsi ON whi.article_id = nsi.id
                    WHERE whi.id = %s
                """, (item_id,))
                row = cur.fetchone()
                
                if not row:
                    return redirect(url_for('newsletter.newsletter_round_scotland.overview', issue_id=issue_id))
                
                item = dict(row)
                # Parse available_images JSONB
                import json
                if item.get('available_images'):
                    if isinstance(item['available_images'], str):
                        item['available_images'] = json.loads(item['available_images'])
                    elif not isinstance(item['available_images'], list):
                        item['available_images'] = []
                else:
                    item['available_images'] = []
        
        return render_template('newsletter/round_scotland/item_editor.html',
                             issue_id=issue_id,
                             issue=issue,
                             item=item)
    except Exception as e:
        logger.error(f"Error in edit_item: {e}", exc_info=True)
        return redirect(url_for('newsletter.newsletter_round_scotland.overview', issue_id=issue_id))


@bp.route('/newsletter/issue/<int:issue_id>/round-scotland/item/<int:item_id>/update', methods=['POST'])
def update_item(issue_id: int, item_id: int):
    """Update a highlight item."""
    try:
        data = request.get_json() or request.form
        
        title_internal = data.get('title_internal', '').strip()
        summary_newsletter = data.get('summary_newsletter', '').strip()
        summary_social = data.get('summary_social', '').strip()
        location_label = data.get('location_label', '').strip()
        source_label = data.get('source_label', '').strip()
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE weekly_highlights_items
                    SET title_internal = %s,
                        summary_newsletter = %s,
                        summary_social = %s,
                        location_label = %s,
                        source_label = %s
                    WHERE id = %s
                """, (title_internal, summary_newsletter, summary_social, location_label, source_label, item_id))
                conn.commit()
        
        if request.is_json:
            return jsonify({'success': True})
        return redirect(url_for('newsletter.newsletter_round_scotland.edit_item', issue_id=issue_id, item_id=item_id))
    except Exception as e:
        logger.error(f"Error updating item: {e}", exc_info=True)
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        return redirect(url_for('newsletter.newsletter_round_scotland.overview', issue_id=issue_id))


@bp.route('/newsletter/issue/<int:issue_id>/round-scotland/item/<int:item_id>/remove', methods=['POST'])
def remove_item(issue_id: int, item_id: int):
    """Remove an item from weekly highlights."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Get article_id before deleting
                cur.execute("SELECT article_id FROM weekly_highlights_items WHERE id = %s", (item_id,))
                row = cur.fetchone()
                if row:
                    article_id = row[0]
                    # Unmark article as selected
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET selected_for_highlights = FALSE
                        WHERE id = %s
                    """, (article_id,))
                
                # Delete item
                cur.execute("DELETE FROM weekly_highlights_items WHERE id = %s", (item_id,))
                conn.commit()
        
        if request.is_json:
            return jsonify({'success': True})
        return redirect(url_for('newsletter.newsletter_round_scotland.overview', issue_id=issue_id))
    except Exception as e:
        logger.error(f"Error removing item: {e}", exc_info=True)
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        return redirect(url_for('newsletter.newsletter_round_scotland.overview', issue_id=issue_id))


@bp.route('/newsletter/issue/<int:issue_id>/round-scotland/item/<int:item_id>/images', methods=['GET'])
def get_item_images(issue_id: int, item_id: int):
    """Get available images for an item."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT whi.selected_image_url, whi.selected_image_caption, whi.selected_image_credit,
                           nsi.available_images
                    FROM weekly_highlights_items whi
                    JOIN newsletter_source_item nsi ON whi.article_id = nsi.id
                    WHERE whi.id = %s
                """, (item_id,))
                row = cur.fetchone()
                
                if not row:
                    return jsonify({'success': False, 'error': 'Item not found'}), 404
                
                import json
                available_images = row[3] or []
                if isinstance(available_images, str):
                    available_images = json.loads(available_images)
                elif not isinstance(available_images, list):
                    available_images = []
                
                selected = None
                if row[0]:  # selected_image_url
                    selected = {
                        'url': row[0],
                        'caption': row[1] or '',
                        'credit': row[2] or ''
                    }
                
                return jsonify({
                    'success': True,
                    'images': available_images,
                    'selected': selected
                })
    except Exception as e:
        logger.error(f"Error getting images: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/newsletter/issue/<int:issue_id>/round-scotland/item/<int:item_id>/select-image', methods=['POST'])
def select_image(issue_id: int, item_id: int):
    """Save image selection for an item."""
    try:
        data = request.get_json() or request.form
        image_url = data.get('image_url', '').strip() or None
        
        # If image_url provided, get caption and credit from available_images
        caption = None
        credit = None
        
        if image_url:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT nsi.available_images
                        FROM weekly_highlights_items whi
                        JOIN newsletter_source_item nsi ON whi.article_id = nsi.id
                        WHERE whi.id = %s
                    """, (item_id,))
                    row = cur.fetchone()
                    if row and row[0]:
                        import json
                        available_images = row[0]
                        if isinstance(available_images, str):
                            available_images = json.loads(available_images)
                        
                        # Find matching image
                        for img in available_images:
                            if img.get('url') == image_url:
                                caption = img.get('caption', '')
                                credit = img.get('credit', '')
                                break
        
        # Update item
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE weekly_highlights_items
                    SET selected_image_url = %s,
                        selected_image_caption = %s,
                        selected_image_credit = %s
                    WHERE id = %s
                """, (image_url, caption, credit, item_id))
                conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error selecting image: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/newsletter/issue/<int:issue_id>/round-scotland/candidates')
def candidates(issue_id: int):
    """Browse candidate pool of quirky articles not yet selected."""
    logger.info(f"Candidates route called for issue {issue_id}")
    try:
        issue = get_issue(issue_id=issue_id)
        if not issue:
            logger.warning(f"Issue {issue_id} not found")
            return redirect(url_for('newsletter.newsletter_issues.dashboard'))
        
        # Get filter parameters
        region_filter = request.args.get('region', '')
        min_score = int(request.args.get('min_score', 60))
        days_back = int(request.args.get('days_back', 14))
        
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Get candidates
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT nsi.id, nsi.source_name, nsi.title, nsi.url, nsi.published_at,
                           nsi.location, nsi.llm_quirky_score, nsi.llm_summary_raw,
                           nsi.safety_flag, nsi.heuristic_score, ns.region
                    FROM newsletter_source_item nsi
                    INNER JOIN newsletter_snapshot_source ns ON nsi.source_name = ns.name
                    WHERE nsi.llm_class = 'quirky'
                    AND nsi.llm_quirky_score >= %s
                    AND (nsi.safety_flag IS NULL OR nsi.safety_flag NOT IN ('death', 'serious_illness', 'crime'))
                    AND nsi.published_at >= %s
                    AND (nsi.selected_for_highlights = FALSE OR nsi.selected_for_highlights IS NULL)
                    AND ns.region IS NOT NULL  -- Only local weekly newspapers
                """
                params = [min_score, cutoff_date]
                
                if region_filter:
                    query += " AND ns.region = %s"
                    params.append(region_filter)
                
                query += " ORDER BY nsi.llm_quirky_score DESC, nsi.published_at DESC LIMIT 50"
                
                cur.execute(query, tuple(params))
                rows = cur.fetchall() or []
                candidates = [dict(r) for r in rows]
                logger.info(f"Found {len(candidates)} candidates for issue {issue_id}")
        
        # Get available regions for filter
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT region FROM newsletter_snapshot_source
                    WHERE region IS NOT NULL
                    ORDER BY region
                """)
                rows = cur.fetchall() or []
                regions = [r['region'] for r in rows if r.get('region')]
        
        logger.info(f"Rendering candidates page for issue {issue_id} with {len(candidates)} candidates")
        try:
            return render_template('newsletter/round_scotland/candidates.html',
                                 issue_id=issue_id,
                                 issue=issue,
                                 candidates=candidates,
                                 regions=regions,
                                 current_region=region_filter,
                                 min_score=min_score,
                                 days_back=days_back)
        except Exception as template_error:
            logger.error(f"Template rendering error: {template_error}", exc_info=True)
            raise
    except Exception as e:
        logger.error(f"Error in candidates for issue {issue_id}: {e}", exc_info=True)
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Full traceback: {error_details}")
        # Flash error message
        flash(f"Error loading candidates: {str(e)}", "error")
        # Temporarily return error page for debugging
        if request.args.get('debug') == '1':
            return f"<h1>Error</h1><pre>{error_details}</pre>", 500
        return redirect(url_for('newsletter.newsletter_round_scotland.overview', issue_id=issue_id))

