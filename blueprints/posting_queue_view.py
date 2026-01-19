"""
Posting Queue View Blueprint
Provides a dedicated UI to view and manage all posts in the posting_queue
"""

from flask import Blueprint, render_template, jsonify, request
from config.database import db_manager
import logging

bp = Blueprint('posting_queue_view', __name__)
logger = logging.getLogger(__name__)

@bp.route('/posting-queue')
def queue_view():
    """Main queue view page showing all posts"""
    return render_template('posting_queue/view.html')

@bp.route('/api/posting-queue/all')
def get_all_queue_items():
    """Get all posts in posting_queue with full details"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    pq.id,
                    pq.idea_id,
                    pq.product_id,
                    pq.content_type,
                    pq.platform,
                    pq.channel_type,
                    pq.generated_content,
                    pq.generated_caption,
                    pq.image_path,
                    pq.status,
                    pq.scheduled_date,
                    pq.scheduled_time,
                    pq.scheduled_timestamp,
                    pq.schedule_name,
                    pq.timezone,
                    pq.platform_post_id,
                    pq.created_at,
                    pq.updated_at,
                    -- Product details
                    cp.name as product_name,
                    cp.sku as product_sku,
                    cp.image_url as product_image,
                    -- Idea details (for language posts)
                    ci.idea_title,
                    ci.idea_description
                FROM posting_queue pq
                LEFT JOIN clan_products cp ON pq.product_id = cp.id
                LEFT JOIN calendar_ideas ci ON pq.idea_id = ci.id
                ORDER BY 
                    CASE pq.status
                        WHEN 'draft' THEN 1
                        WHEN 'ready' THEN 2
                        WHEN 'pending' THEN 3
                        WHEN 'published' THEN 4
                        WHEN 'failed' THEN 5
                        ELSE 6
                    END,
                    COALESCE(pq.scheduled_timestamp, (pq.scheduled_date::date + pq.scheduled_time::time)::timestamp) ASC NULLS LAST,
                    pq.created_at DESC
            """)
            
            items = cursor.fetchall()
            
            # Convert to list of dicts
            queue_list = []
            for item in items:
                item_dict = dict(item)
                # Convert datetime objects to ISO format strings
                for key in ['created_at', 'updated_at', 'scheduled_date', 'scheduled_timestamp']:
                    if item_dict.get(key):
                        if hasattr(item_dict[key], 'isoformat'):
                            item_dict[key] = item_dict[key].isoformat()
                if item_dict.get('scheduled_time'):
                    item_dict['scheduled_time'] = str(item_dict['scheduled_time'])
                queue_list.append(item_dict)
            
            return jsonify({
                'success': True,
                'items': queue_list,
                'total': len(queue_list)
            })
    except Exception as e:
        logger.error(f"Error getting queue items: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'items': []
        }), 500

@bp.route('/api/posting-queue/stats')
def get_queue_stats():
    """Get statistics about the posting queue"""
    try:
        with db_manager.get_cursor() as cursor:
            # Overall stats
            cursor.execute("""
                SELECT 
                    status,
                    content_type,
                    COUNT(*) as count
                FROM posting_queue
                GROUP BY status, content_type
                ORDER BY status, content_type
            """)
            status_breakdown = cursor.fetchall()
            
            # Total counts
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'draft') as draft,
                    COUNT(*) FILTER (WHERE status = 'ready') as ready,
                    COUNT(*) FILTER (WHERE status = 'pending') as pending,
                    COUNT(*) FILTER (WHERE status = 'published') as published,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed
                FROM posting_queue
            """)
            totals = cursor.fetchone()
            
            # Language posts stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_language,
                    COUNT(*) FILTER (WHERE status = 'draft') as draft_language,
                    COUNT(*) FILTER (WHERE status = 'ready') as ready_language
                FROM posting_queue
                WHERE content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
            """)
            language_stats = cursor.fetchone()
            
            # Product posts stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_product,
                    COUNT(*) FILTER (WHERE status = 'draft') as draft_product,
                    COUNT(*) FILTER (WHERE status = 'ready') as ready_product
                FROM posting_queue
                WHERE content_type = 'product'
            """)
            product_stats = cursor.fetchone()
            
            return jsonify({
                'success': True,
                'totals': dict(totals),
                'status_breakdown': [dict(r) for r in status_breakdown],
                'language_posts': dict(language_stats),
                'product_posts': dict(product_stats)
            })
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
