"""Newsletter Blueprint - Top-level UI shell.

Routes here stay thin (<60 LOC each) and delegate to services. Keep this file
small; split views into helpers if it approaches ~400–500 LOC.
"""

from __future__ import annotations

from flask import Blueprint, render_template, redirect, url_for, request, jsonify
import os, sys

# Ensure the newsletter package (under blog-core/newsletter) is importable
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-core'))

from newsletter.db.queries_issue import (
    list_issues,
    count_issues,
    soft_delete_issue,
    get_issue,
    update_issue_theme,
    update_issue_subject_preheader,
    list_blocks_by_issue,
    set_block_enabled,
    update_block_payload,
    delete_block,
    insert_block,
    move_block,
    shift_positions,
)
from newsletter.selectors.theme import get_themes_for_week, parse_target_week, get_theme_by_id
from newsletter.services.draft_service import build_weekly_issue
from newsletter.services.qa_service import run_pre_send_checks
from newsletter.services.approval_service import approve_issue, send_issue
from newsletter.services.block_editor_service import get_suggestions, apply_suggestion, save_override, regenerate_text
from newsletter.jobs.weekly_autodraft import run as run_autodraft
from newsletter.db.queries_source_management import (
    list_all_sources,
    get_source,
    create_source,
    update_source,
    delete_source,
    get_cache_status,
    get_item_stats,
)
from newsletter.db.queries_sources import get_cached_items
from newsletter.jobs.prefetch_sources import run as run_prefetch

bp = Blueprint('newsletter', __name__)


@bp.route('/newsletter')
def dashboard():
    """Top-level Newsletter dashboard."""
    status_filter = request.args.get('status')
    q = request.args.get('q')
    show_deleted = request.args.get('show_deleted', '0') == '1'
    try:
        page = max(1, int(request.args.get('page', '1')))
    except Exception:
        page = 1
    per_page = 12
    offset = (page - 1) * per_page
    issues = []
    try:
        total = count_issues(status=status_filter, q=q, show_deleted=show_deleted)
        issues = list_issues(limit=per_page, offset=offset, status=status_filter, q=q, show_deleted=show_deleted)
    except Exception:
        total = 0
        issues = []
    total_pages = max(1, (total + per_page - 1) // per_page)
    return render_template('newsletter/index.html', page_title='Newsletter', issues=issues, status_filter=status_filter, q=q, page=page, total_pages=total_pages, show_deleted=show_deleted)


@bp.route('/newsletter/issue/<int:issue_id>/delete', methods=['POST'])
def delete_issue_route(issue_id: int):
    """Soft delete an issue."""
    soft_delete_issue(issue_id=issue_id)
    return redirect(url_for('newsletter.dashboard'))


@bp.route('/newsletter/issue', methods=['POST'])
def create_or_regenerate_issue():
    """Create a new draft issue and populate initial blocks."""
    result = build_weekly_issue()
    return redirect(url_for('newsletter.view_issue', issue_id=result["issue_id"]))


@bp.route('/newsletter/issue/<int:issue_id>')
def view_issue(issue_id: int):
    """Simple issue view showing blocks list (preview comes later)."""
    issue = None
    themes = []
    try:
        issue = get_issue(issue_id=issue_id)
        if issue and issue.get('target_week'):
            week_number = parse_target_week(issue['target_week'])
            themes = get_themes_for_week(week_number)
    except Exception:
        pass
    
    blocks = []
    try:
        blocks = list_blocks_by_issue(issue_id=issue_id)
    except Exception:
        blocks = []
    # Auto-generate one of each block type if none exist yet
    if not blocks:
        default_types = [
            "intro",
            "feature",
            "snapshot",
            "new_products",
            "spotlight",
            "category",
            "weekly_words",
            "evergreen",
            "closing",
        ]
        pos = 0
        for t in default_types:
            insert_block(issue_id=issue_id, block_type=t, position=pos, enabled=True, payload={})
            pos += 1
        try:
            blocks = list_blocks_by_issue(issue_id=issue_id)
        except Exception:
            blocks = []
    else:
        # Ensure Intro exists for existing issues; if missing, prepend at position 0
        has_intro = any((b.get("type") == "intro") for b in blocks)
        if not has_intro:
            try:
                shift_positions(issue_id=issue_id, from_position=0)
                insert_block(issue_id=issue_id, block_type="intro", position=0, enabled=True, payload={})
                blocks = list_blocks_by_issue(issue_id=issue_id)
            except Exception:
                pass
    
    current_theme = None
    if issue and issue.get('theme_id'):
        try:
            current_theme = get_theme_by_id(issue['theme_id'])
        except Exception:
            pass
    
    return render_template('newsletter/issue.html', issue_id=issue_id, issue=issue, blocks=blocks, themes=themes, current_theme=current_theme)


@bp.route('/newsletter/issue/<int:issue_id>/preview')
def preview_issue(issue_id: int):
    blocks = []
    try:
        blocks = list_blocks_by_issue(issue_id=issue_id)
    except Exception:
        blocks = []
    # Map blocks to pass each payload as "block" expected by partials
    normalized = []
    for b in blocks:
        normalized.append({
            "type": b.get("type"),
            "payload_json": b.get("payload_json", {}),
        })
    # The partials expect a variable named `block` when included; render will set it via context assignment
    # We pass blocks and reuse includes that reference `block` by setting it before each include in template
    # Simpler: in template we refer to b.payload_json as `block` using Jinja context; here we just pass blocks
    return render_template('newsletter/render.html', subject=f"Issue {issue_id}", blocks=[{"type": b["type"], "payload_json": b["payload_json"]} for b in blocks])


@bp.route('/newsletter/issue/<int:issue_id>/qa')
def qa_issue(issue_id: int):
    checks = []
    try:
        checks = run_pre_send_checks(issue_id)
    except Exception:
        checks = []
    return render_template('newsletter/qa.html', issue_id=issue_id, checks=checks)


@bp.route('/newsletter/issue/<int:issue_id>/approve', methods=['POST'])
def approve_issue_route(issue_id: int):
    approve_issue(issue_id=issue_id)
    return redirect(url_for('newsletter.view_issue', issue_id=issue_id))


@bp.route('/newsletter/issue/<int:issue_id>/send', methods=['POST'])
def send_issue_route(issue_id: int):
    adapter = request.form.get('adapter', 'preview')
    result = send_issue(issue_id=issue_id, adapter=adapter)
    return redirect(url_for('newsletter.view_issue', issue_id=issue_id))


@bp.route('/newsletter/issue/<int:issue_id>/theme', methods=['POST'])
def update_theme_route(issue_id: int):
    """Update theme for an issue."""
    theme_id = request.form.get('theme_id')
    if theme_id and theme_id != '':
        try:
            theme_id_int = int(theme_id)
            theme = get_theme_by_id(theme_id_int)
            if theme:
                update_issue_theme(issue_id=issue_id, theme_id=theme_id_int)
                # Update subject and preheader from theme
                subject = f"{theme.get('idea_title', 'This week in Scotland')} — {get_issue(issue_id).get('target_week', '')}"
                preheader = theme.get('seasonal_context') or theme.get('idea_description') or "A quick wander through culture & craft."
                update_issue_subject_preheader(issue_id=issue_id, subject=subject, preheader=preheader)
        except Exception:
            pass
    else:
        update_issue_theme(issue_id=issue_id, theme_id=None)
    return redirect(url_for('newsletter.view_issue', issue_id=issue_id))


@bp.route('/newsletter/autodraft', methods=['POST'])
def trigger_autodraft():
    try:
        result = run_autodraft()
        issue_id = result.get('issue_id') if result else None
        if not issue_id:
            return redirect(url_for('newsletter.dashboard')), 302
        return redirect(url_for('newsletter.view_issue', issue_id=issue_id))
    except Exception as e:
        # Log error and redirect to dashboard
        import logging
        logging.error(f"Autodraft failed: {e}", exc_info=True)
        return redirect(url_for('newsletter.dashboard'))


# Block management endpoints

@bp.route('/newsletter/block/<int:block_id>/toggle', methods=['POST'])
def toggle_block(block_id: int):
    enabled = request.form.get('enabled', 'true').lower() == 'true'
    set_block_enabled(block_id=block_id, enabled=enabled)
    issue_id = int(request.form.get('issue_id', '0'))
    return redirect(url_for('newsletter.view_issue', issue_id=issue_id))


@bp.route('/newsletter/block/<int:block_id>/update', methods=['POST'])
def update_block(block_id: int):
    import json
    raw = request.form.get('payload_json') or '{}'
    try:
        payload = json.loads(raw)
    except Exception:
        payload = {}
    update_block_payload(block_id=block_id, payload=payload)
    issue_id = int(request.form.get('issue_id', '0'))
    return redirect(url_for('newsletter.view_issue', issue_id=issue_id))


@bp.route('/newsletter/block/<int:block_id>/delete', methods=['POST'])
def remove_block(block_id: int):
    issue_id = int(request.form.get('issue_id', '0'))
    delete_block(block_id=block_id)
    return redirect(url_for('newsletter.view_issue', issue_id=issue_id))


@bp.route('/newsletter/issue/<int:issue_id>/block/add', methods=['POST'])
def add_block(issue_id: int):
    block_type = request.form.get('type', 'evergreen')
    # Calculate position: optional provided, else append to end
    try:
        existing = list_blocks_by_issue(issue_id=issue_id)
        desired = request.form.get('position')
        if desired is not None and desired != '':
            try:
                desired_pos = int(desired)
            except Exception:
                desired_pos = 0
            if desired_pos < 0:
                desired_pos = 0
            if existing:
                max_pos = max(b.get('position', 0) for b in existing)
                if desired_pos > max_pos + 1:
                    desired_pos = max_pos + 1
                # Shift existing blocks at and after desired_pos
                shift_positions(issue_id=issue_id, from_position=desired_pos)
            position = desired_pos
        else:
            if existing:
                max_pos = max(b.get('position', 0) for b in existing)
                position = max_pos + 1
            else:
                position = 0
    except Exception:
        position = 9999
    payload = {}
    insert_block(issue_id=issue_id, block_type=block_type, position=position, enabled=True, payload=payload)
    return redirect(url_for('newsletter.view_issue', issue_id=issue_id))


@bp.route('/newsletter/block/<int:block_id>/move', methods=['POST'])
def move_block_route(block_id: int):
    direction = request.form.get('direction', 'up')
    move_block(block_id=block_id, direction=direction)
    issue_id = int(request.form.get('issue_id', '0'))
    return redirect(url_for('newsletter.view_issue', issue_id=issue_id))


# Block editor API endpoints (JSON)

@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/suggestions', methods=['GET'])
def get_block_suggestions(issue_id: int, block_id: int):
    """Get suggestions for a block."""
    try:
        from newsletter.db.queries_issue import get_block
        import logging
        logger = logging.getLogger(__name__)
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        issue = get_issue(issue_id=issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        target_week = issue.get('target_week', '')
        block_type = block.get('type', '')
        
        logger.debug(f"Getting suggestions for block {block_id} (type: {block_type}, week: {target_week})")
        
        result = get_suggestions(
            block_id=block_id,
            block_type=block_type,
            issue_id=issue_id,
            target_week=target_week
        )
        
        logger.debug(f"Suggestions result: {len(result.get('suggestions', []))} suggestions found")
        
        # If no suggestions and no error, provide helpful message
        if not result.get('suggestions') and not result.get('error'):
            result['error'] = 'No suggestions available. Make sure source prefetch has run and there is content in the database.'
        
        return jsonify(result)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error getting suggestions: {e}", exc_info=True)
        return jsonify({'error': str(e), 'suggestions': [], 'current': None, 'metadata': {}}), 500


@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/select-suggestion', methods=['POST'])
def select_block_suggestion(issue_id: int, block_id: int):
    """Apply a suggestion to a block."""
    try:
        from newsletter.db.queries_issue import get_block
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        issue = get_issue(issue_id=issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        target_week = issue.get('target_week', '')
        block_type = block.get('type', '')
        
        suggestion_id = request.json.get('suggestion_id') if request.is_json else None
        if suggestion_id:
            try:
                suggestion_id = int(suggestion_id)
            except Exception:
                suggestion_id = None
        
        result = apply_suggestion(
            block_id=block_id,
            block_type=block_type,
            issue_id=issue_id,
            target_week=target_week,
            suggestion_id=suggestion_id
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/override', methods=['POST'])
def override_block_text(issue_id: int, block_id: int):
    """Save manual text override for a block."""
    try:
        from newsletter.db.queries_issue import get_block
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        block_type = block.get('type', '')
        override_text = ''
        
        if request.is_json:
            override_text = request.json.get('text', '')
        else:
            override_text = request.form.get('text', '')
        
        result = save_override(
            block_id=block_id,
            block_type=block_type,
            override_text=override_text
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/preview', methods=['GET'])
def preview_block(issue_id: int, block_id: int):
    """Get rendered HTML preview for a block."""
    try:
        from newsletter.db.queries_issue import get_block
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        # For now, return payload; later can render full HTML
        payload = block.get('payload_json', {})
        block_type = block.get('type', '')
        
        return jsonify({
            'block_type': block_type,
            'payload': payload,
            'html': '',  # TODO: render actual HTML template
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Source Management Routes

@bp.route('/newsletter/weather/summary')
def weather_summary():
    """Get weather summary for past week and forecast."""
    try:
        from newsletter.services.weather_summary_service import generate_weather_summary
        
        days_back = request.args.get('days_back', 7, type=int)
        days_ahead = request.args.get('days_ahead', 7, type=int)
        
        summary = generate_weather_summary(days_back=days_back, days_ahead=days_ahead)
        
        # If requested as HTML page
        if request.args.get('view') == 'page':
            return render_template('newsletter/weather_summary.html', summary=summary)
        
        # Otherwise return JSON
        return jsonify({
            'status': 'success',
            'data': summary
        })
    except Exception as e:
        logger.error(f"Error generating weather summary: {e}", exc_info=True)
        if request.args.get('view') == 'page':
            return render_template('newsletter/weather_summary.html', error=str(e))
        return jsonify({'error': str(e)}), 500


@bp.route('/newsletter/weather')
def weather_summary_page():
    """Weather summary page UI."""
    return render_template('newsletter/weather_summary.html')


@bp.route('/newsletter/news/summary')
def news_summary():
    """Get news summary from synopses."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from newsletter.services.news_synopsis_service import generate_news_summary
        
        days_back = request.args.get('days_back', 7, type=int)
        limit = request.args.get('limit', 100, type=int)  # Default to 100, allow override
        sort_by = request.args.get('sort_by', 'combined_score')  # combined_score, suitability_score, published_at
        
        summary = generate_news_summary(days_back=days_back, limit=limit, sort_by=sort_by)
        
        # If requested as HTML page
        if request.args.get('view') == 'page':
            return render_template('newsletter/news_summary.html', summary=summary)
        
        # Otherwise return JSON
        return jsonify({
            'status': 'success',
            'data': summary
        })
    except Exception as e:
        logger.error(f"Error generating news summary: {e}", exc_info=True)
        if request.args.get('view') == 'page':
            return render_template('newsletter/news_summary.html', error=str(e))
        return jsonify({'error': str(e)}), 500


@bp.route('/newsletter/news')
def news_summary_page():
    """News summary page UI."""
    return render_template('newsletter/news_summary.html')


@bp.route('/newsletter/events/summary')
def events_summary():
    """Get events summary."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from newsletter.services.events_summary_service import generate_events_summary
        
        days_back = request.args.get('days_back', 365, type=int)  # Default to 1 year back
        days_ahead = request.args.get('days_ahead', 365, type=int)  # Default to 1 year ahead
        source_name = request.args.get('source', None, type=str)
        location = request.args.get('location', None, type=str)
        
        recurrence_type = request.args.get('recurrence_type', None, type=str)
        
        summary = generate_events_summary(
            days_back=days_back,
            days_ahead=days_ahead,
            source_name=source_name,
            location=location,
            recurrence_type=recurrence_type
        )
        
        # If requested as HTML page
        if request.args.get('view') == 'page':
            return render_template('newsletter/events_summary.html', summary=summary)
        
        # Otherwise return JSON
        return jsonify({
            'status': 'success',
            'data': summary
        })
    except Exception as e:
        logger.error(f"Error generating events summary: {e}", exc_info=True)
        if request.args.get('view') == 'page':
            return render_template('newsletter/events_summary.html', error=str(e))
        return jsonify({'error': str(e)}), 500


@bp.route('/newsletter/events')
def events_summary_page():
    """Events summary page UI."""
    return render_template('newsletter/events_summary.html')


@bp.route('/newsletter/events/<int:event_id>')
def event_detail(event_id: int):
    """Get detailed view of a single event."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from newsletter.services.events_summary_service import get_event_detail
        
        event = get_event_detail(event_id)
        
        if not event:
            return render_template('newsletter/event_detail.html', error='Event not found'), 404
        
        return render_template('newsletter/event_detail.html', event=event)
    except Exception as e:
        logger.error(f"Error fetching event detail: {e}", exc_info=True)
        return render_template('newsletter/event_detail.html', error=str(e)), 500


@bp.route('/newsletter/events/<int:event_id>/recurrence-type', methods=['POST'])
def update_event_recurrence_type(event_id: int):
    """Update event recurrence type (manual override)."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        data = request.get_json()
        recurrence_type = data.get('recurrence_type')
        
        if recurrence_type not in ('annual', 'one_off'):
            return jsonify({'success': False, 'error': 'Invalid recurrence_type. Must be "annual" or "one_off"'}), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Check event exists
                cur.execute("""
                    SELECT id FROM newsletter_source_item
                    WHERE id = %s AND category = 'event'
                """, (event_id,))
                
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Event not found'}), 404
                
                # Update recurrence type
                cur.execute("""
                    UPDATE newsletter_source_item
                    SET event_recurrence_type = %s
                    WHERE id = %s
                """, (recurrence_type, event_id))
                
                conn.commit()
                
                logger.info(f"Updated event {event_id} recurrence type to {recurrence_type}")
                
                return jsonify({
                    'success': True,
                    'message': f'Event classified as {recurrence_type}',
                    'recurrence_type': recurrence_type
                })
    except Exception as e:
        logger.error(f"Error updating event recurrence type: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/newsletter/events/<int:event_id>/update', methods=['POST'])
def update_event_field(event_id: int):
    """Update a specific field of an event."""
    import logging
    from datetime import datetime
    from psycopg.types.json import Json
    
    logger = logging.getLogger(__name__)
    
    try:
        from config.database import db_manager
        
        data = request.get_json()
        field = data.get('field')
        value = data.get('value')
        
        if not field:
            return jsonify({'success': False, 'error': 'Field name required'}), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Check event exists and get current raw_data
                cur.execute("""
                    SELECT id, raw_data FROM newsletter_source_item
                    WHERE id = %s AND category = 'event'
                """, (event_id,))
                
                row = cur.fetchone()
                if not row:
                    return jsonify({'success': False, 'error': 'Event not found'}), 404
                
                event_id_db, raw_data = row
                if not raw_data:
                    raw_data = {}
                
                # Update based on field type
                if field == 'title':
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET title = %s
                        WHERE id = %s
                    """, (value, event_id))
                    raw_data['title'] = value
                
                elif field == 'description':
                    raw_data['description'] = value
                    raw_data['summary'] = value  # Also update summary
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET raw_data = %s
                        WHERE id = %s
                    """, (Json(raw_data), event_id))
                
                elif field == 'date_text':
                    raw_data['date_text'] = value
                    raw_data['date_text_preserved'] = value
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET raw_data = %s
                        WHERE id = %s
                    """, (Json(raw_data), event_id))
                
                elif field == 'event_date':
                    # Parse date string and update both event_date and raw_data
                    event_date = None
                    if value:
                        try:
                            event_date = datetime.strptime(value, '%Y-%m-%d').date()
                        except ValueError:
                            return jsonify({'success': False, 'error': 'Invalid date format'}), 400
                    
                    raw_data['event_date'] = value if value else None
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET event_date = %s, raw_data = %s
                        WHERE id = %s
                    """, (event_date, Json(raw_data), event_id))
                
                elif field == 'location':
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET location = %s
                        WHERE id = %s
                    """, (value if value else None, event_id))
                    raw_data['location'] = value if value else None
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET raw_data = %s
                        WHERE id = %s
                    """, (Json(raw_data), event_id))
                
                else:
                    return jsonify({'success': False, 'error': f'Unknown field: {field}'}), 400
                
                conn.commit()
                
                logger.info(f"Updated event {event_id} field {field}")
                
                return jsonify({
                    'success': True,
                    'message': f'Field {field} updated',
                    'value': value
                })
    except Exception as e:
        logger.error(f"Error updating event field: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/newsletter/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id: int):
    """Delete an event (soft delete by marking as deleted)."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from config.database import db_manager
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Check event exists
                cur.execute("""
                    SELECT id FROM newsletter_source_item
                    WHERE id = %s AND category = 'event'
                """, (event_id,))
                
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Event not found'}), 404
                
                # Soft delete - mark as deleted
                # Assuming we have a deleted column, otherwise we'll need to add it
                # For now, let's check if deleted column exists, if not, actually delete
                cur.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'newsletter_source_item' AND column_name = 'deleted'
                """)
                
                if cur.fetchone():
                    # Soft delete
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET deleted = TRUE
                        WHERE id = %s
                    """, (event_id,))
                else:
                    # Hard delete (if no deleted column)
                    cur.execute("""
                        DELETE FROM newsletter_source_item
                        WHERE id = %s
                    """, (event_id,))
                
                conn.commit()
                
                logger.info(f"Deleted event {event_id}")
                
                return jsonify({
                    'success': True,
                    'message': 'Event deleted successfully'
                })
    except Exception as e:
        logger.error(f"Error deleting event: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/newsletter/news/reanalyze', methods=['POST'])
def reanalyze_news():
    """Re-analyze existing news items with synopsis service."""
    try:
        from newsletter.jobs.reanalyze_news import reanalyze_news_items
        
        result = reanalyze_news_items(days_back=30, limit=50)
        
        return jsonify({
            'success': True,
            'message': f"Re-analyzed {result['processed']} items, skipped {result['skipped']}, errors {result['errors']}",
            'result': result
        })
    except Exception as e:
        logger.error(f"Error re-analyzing news: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/newsletter/news/clean', methods=['POST'])
def clean_synopses():
    """Clean subscription text from existing synopses."""
    try:
        from newsletter.jobs.clean_existing_synopses import clean_all_synopses
        
        result = clean_all_synopses()
        
        return jsonify({
            'success': True,
            'message': f"Cleaned {result['updated']} synopses, {result['unchanged']} unchanged",
            'result': result
        })
    except Exception as e:
        logger.error(f"Error cleaning synopses: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/newsletter/sources')
def sources_management():
    """Source aggregation management page."""
    sources = list_all_sources()
    cache_status = get_cache_status()
    item_stats = get_item_stats()
    
    # Get cached items for preview (recent 20)
    recent_items = get_cached_items(days_back=14, limit=20)
    
    return render_template(
        'newsletter/sources.html',
        sources=sources,
        cache_status=cache_status,
        item_stats=item_stats,
        recent_items=recent_items,
    )


@bp.route('/newsletter/sources/add', methods=['POST'])
def add_source():
    """Add a new source."""
    name = request.form.get('name', '').strip()
    base_url = request.form.get('base_url', '').strip()
    source_type = request.form.get('type', 'rss').strip()
    enabled = request.form.get('enabled', 'off') == 'on'
    api_key_ref = request.form.get('api_key_ref', '').strip() or None
    
    if not name or not base_url:
        return redirect(url_for('newsletter.sources_management')), 302
    
    create_source(name=name, base_url=base_url, type=source_type, enabled=enabled, api_key_ref=api_key_ref)
    return redirect(url_for('newsletter.sources_management'))


@bp.route('/newsletter/sources/<int:source_id>/edit', methods=['POST'])
def edit_source(source_id: int):
    """Update an existing source."""
    name = request.form.get('name', '').strip()
    base_url = request.form.get('base_url', '').strip()
    source_type = request.form.get('type', 'rss').strip()
    enabled = request.form.get('enabled', 'off') == 'on'
    api_key_ref = request.form.get('api_key_ref', '').strip() or None
    
    updates = {}
    if name:
        updates['name'] = name
    if base_url:
        updates['base_url'] = base_url
    if source_type:
        updates['type'] = source_type
    updates['enabled'] = enabled
    if api_key_ref is not None:
        updates['api_key_ref'] = api_key_ref
    
    update_source(source_id, **updates)
    return redirect(url_for('newsletter.sources_management'))


@bp.route('/newsletter/sources/<int:source_id>/delete', methods=['POST'])
def delete_source_route(source_id: int):
    """Delete a source."""
    delete_source(source_id)
    return redirect(url_for('newsletter.sources_management'))


@bp.route('/newsletter/sources/<int:source_id>/toggle', methods=['POST'])
def toggle_source(source_id: int):
    """Toggle source enabled/disabled."""
    source = get_source(source_id)
    if source:
        update_source(source_id, enabled=not source.get('enabled', False))
    return redirect(url_for('newsletter.sources_management'))


@bp.route('/newsletter/sources/fetch', methods=['POST'])
def trigger_fetch():
    """Manually trigger source prefetch job."""
    result = run_prefetch()
    # Could show success/error message, but for now just redirect
    return redirect(url_for('newsletter.sources_management'))


@bp.route('/newsletter/sources/<int:source_id>/test', methods=['GET'])
def test_source(source_id: int):
    """Test a source by fetching and returning sample items with proper error handling."""
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    
    try:
        source = get_source(source_id)
        if not source:
            logger.warning(f"Source test: source {source_id} not found")
            return jsonify({
                'success': False, 
                'error': 'Source not found',
                'error_type': 'not_found'
            }), 404
        
        if not source.get('enabled'):
            logger.info(f"Source test: {source.get('name')} is disabled")
            return jsonify({
                'success': False, 
                'error': 'Source is disabled. Enable it first to test.',
                'error_type': 'disabled'
            }), 400
        
        # Use manager to create adapter and fetch
        from newsletter.sources.manager import create_adapter_from_source
        
        source_name = source.get('name', 'Unknown')
        source_type = source.get('type', 'unknown')
        source_url = source.get('base_url', '')
        
        logger.info(f"Testing source: {source_name} (type: {source_type}, url: {source_url})")
        
        # Create adapter with explicit error handling
        try:
            adapter = create_adapter_from_source(source)
        except Exception as adapter_error:
            error_msg = f"Failed to create adapter: {str(adapter_error)}"
            logger.error(f"Source test adapter creation failed: {error_msg}", exc_info=True)
            return jsonify({
                'success': False,
                'error': error_msg,
                'error_type': 'adapter_creation_error',
                'source_name': source_name,
                'source_type': source_type
            }), 500
        
        if not adapter:
            error_msg = f"Could not create adapter for type: {source_type}. Supported types: rss, reddit, html, weather, event, museum"
            logger.error(f"Source test: {error_msg}")
            return jsonify({
                'success': False, 
                'error': error_msg,
                'error_type': 'unsupported_type',
                'source_type': source_type
            }), 400
        
        # Log adapter category assignment for debugging
        adapter_category = None
        if hasattr(adapter, 'category'):
            adapter_category = adapter.category
            logger.info(f"Adapter created: {type(adapter).__name__} with category: {adapter_category}")
        else:
            logger.warning(f"Adapter {type(adapter).__name__} has no category attribute")
        
        # Fetch items with error handling
        try:
            logger.info(f"Fetching items from {source_name}...")
            items = adapter.fetch_and_normalize()
            logger.info(f"Fetched {len(items)} items from {source_name}")
        except Exception as fetch_error:
            error_msg = f"Failed to fetch from source: {str(fetch_error)}"
            logger.error(f"Source test fetch failed for {source_name}: {error_msg}", exc_info=True)
            return jsonify({
                'success': False,
                'error': error_msg,
                'error_type': 'fetch_error',
                'source_name': source_name,
                'details': str(fetch_error)
            }), 500
        
        if not items:
            return jsonify({
                'success': True,
                'items_count': 0,
                'categories': {},
                'items': [],
                'warning': 'No items found. The source may be empty, require authentication, or the URL may be incorrect.',
                'adapter_category': adapter_category
            })
        
        # Limit to first 10 for preview
        preview_items = items[:10]
        
        # Group by category for debugging and validation
        categories = {}
        category_breakdown = {}
        for item in items:
            cat = item.get('category', 'other')
            categories[cat] = categories.get(cat, 0) + 1
            if cat not in category_breakdown:
                category_breakdown[cat] = []
            category_breakdown[cat].append(item.get('title', 'No title')[:50])
        
        # Validate category assignment
        category_mismatch = False
        expected_category = None
        if adapter_category and categories:
            # Check if adapter category matches items
            if adapter_category not in categories:
                category_mismatch = True
                expected_category = adapter_category
                logger.warning(
                    f"Category mismatch: adapter category '{adapter_category}' but items have categories: {list(categories.keys())}"
                )
        
        return jsonify({
            'success': True,
            'items_count': len(items),
            'categories': categories,
            'category_breakdown': {k: len(v) for k, v in category_breakdown.items()},
            'adapter_category': adapter_category,
            'category_validation': {
                'match': not category_mismatch,
                'expected': expected_category,
                'found': list(categories.keys())
            },
            'items': [
                {
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'category': item.get('category', 'other'),
                    'source_name': item.get('source_name', ''),
                    'published_at': item.get('published_at').isoformat() if item.get('published_at') else None,
                    'event_date': item.get('event_date').isoformat() if item.get('event_date') else None,
                    'raw_data_preview': str(item.get('raw_data', {}))[:100] if item.get('raw_data') else None,
                }
                for item in preview_items
            ],
        })
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Source test failed for source {source_id}: {error_msg}", exc_info=True)
        return jsonify({
            'success': False,
            'error': error_msg,
            'error_type': 'unexpected_error',
            'traceback': error_trace if logger.level <= logging.DEBUG else None
        }), 500


@bp.route('/newsletter/sources/items')
def cached_items():
    """Full cached items page with filters."""
    from newsletter.db.queries_source_management import list_all_sources
    
    # Get filter parameters
    category_filter = request.args.get('category', '')
    source_filter = request.args.get('source', '')
    days_back = int(request.args.get('days', '14'))
    
    # Get items
    items = get_cached_items(
        category=category_filter if category_filter else None,
        days_back=days_back,
        limit=500  # Increased limit to show more items
    )
    
    # Filter by source if provided
    if source_filter:
        items = [item for item in items if item.get('source_name', '').lower() == source_filter.lower()]
    
    # Get all possible categories (including weather)
    all_categories = ['news', 'weather', 'event', 'community', 'other']
    
    # Get all sources from database (not just cached items)
    all_sources = list_all_sources()
    sources = sorted([s.get('name', '') for s in all_sources if s.get('name')])
    
    return render_template(
        'newsletter/cached_items.html',
        items=items,
        categories=all_categories,
        sources=sources,
        category_filter=category_filter,
        source_filter=source_filter,
        days_back=days_back,
    )

