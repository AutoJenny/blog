# blueprints/launchpad_queue.py
from flask import Blueprint, render_template, jsonify, request, send_file, redirect, url_for
import logging
import json
import os
import requests
from datetime import datetime, date, time, timedelta
import pytz
from humanize import naturaltime
from config.database import db_manager
import psycopg

bp = Blueprint('launchpad_queue', __name__)
logger = logging.getLogger(__name__)

@bp.route('/api/queue')
def get_queue():
    """Get posting queue."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT pq.id, pq.product_id, pq.content_type, pq.generated_content, pq.status,
                       pq.created_at, pq.updated_at, pq.scheduled_date, pq.scheduled_time,
                       pq.scheduled_timestamp, pq.schedule_name, pq.timezone,
                       cp.name as product_name, cp.sku as product_sku, cp.image_url as product_image
                FROM posting_queue pq
                LEFT JOIN clan_products cp ON pq.product_id = cp.id
                ORDER BY pq.created_at DESC
            """)
            queue_items = cursor.fetchall()
            
            # Convert to list of dicts for JSON serialization
            queue_list = []
            for item in queue_items:
                item_dict = dict(item)
                # Convert datetime objects to ISO format strings
                if item_dict.get('created_at'):
                    item_dict['created_at'] = item_dict['created_at'].isoformat()
                if item_dict.get('updated_at'):
                    item_dict['updated_at'] = item_dict['updated_at'].isoformat()
                if item_dict.get('scheduled_date'):
                    item_dict['scheduled_date'] = item_dict['scheduled_date'].isoformat()
                if item_dict.get('scheduled_time'):
                    item_dict['scheduled_time'] = str(item_dict['scheduled_time'])
                if item_dict.get('scheduled_timestamp'):
                    item_dict['scheduled_timestamp'] = item_dict['scheduled_timestamp'].isoformat()
                queue_list.append(item_dict)
            
            return jsonify({
                'success': True,
                'queue': queue_list
            })
    except Exception as e:
        logger.error(f"Error getting queue: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/queue/<int:item_id>', methods=['DELETE'])
def delete_queue_item(item_id):
    """Delete a queue item."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM posting_queue WHERE id = %s", (item_id,))
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Queue item deleted successfully'
                })
    except Exception as e:
        logger.error(f"Error deleting queue item: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/queue/clear', methods=['POST'])
def clear_queue():
    """Clear all items from the queue."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM posting_queue")
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Queue cleared successfully'
                })
    except Exception as e:
        logger.error(f"Error clearing queue: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
