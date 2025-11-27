"""Newsletter Events Routes."""

from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from typing import List, Dict, Any
import os, sys

# Ensure the newsletter package (under blog-core/newsletter) is importable
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-core'))

# Import common dependencies
from newsletter.db.queries_issue import get_issue
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('newsletter_events', __name__)


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


