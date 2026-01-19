"""
Posting Queue View Blueprint
Provides a dedicated UI to view and manage all posts in the posting_queue
"""

from flask import Blueprint, render_template, jsonify, request
from config.database import db_manager
from datetime import datetime, date, time
import logging
import json

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
                    ci.idea_description,
                    -- Additional fields for better display
                    pq.generated_caption,
                    pq.image_path,
                    -- Image URLs (for display)
                    CASE 
                        WHEN pq.content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult') 
                             AND pq.image_path IS NOT NULL 
                             AND pq.image_path LIKE '/Users/%%/static/%%' 
                        THEN REPLACE(pq.image_path, '/Users/autojenny/Documents/projects/blog', '')
                        WHEN pq.content_type = 'product' AND cp.image_url IS NOT NULL
                        THEN cp.image_url
                        WHEN pq.content_type = 'product' AND pq.image_path IS NOT NULL
                        THEN pq.image_path
                        ELSE NULL
                    END as display_image_url
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

@bp.route('/api/posting-queue/<int:item_id>', methods=['PUT'])
def update_queue_item(item_id):
    """Update a posting queue item"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Get current item to check status and content_type
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT status, content_type, product_id, scheduled_date, scheduled_time
                FROM posting_queue
                WHERE id = %s
            """, (item_id,))
            current_item = cursor.fetchone()
            
            if not current_item:
                return jsonify({'success': False, 'error': 'Queue item not found'}), 404
            
            # Can't edit published posts
            if current_item['status'] == 'published':
                return jsonify({'success': False, 'error': 'Cannot edit published posts'}), 400
            
            # Build update query dynamically
            update_fields = []
            update_values = []
            
            # Handle product_id change (for product posts)
            if 'product_id' in data and data['product_id']:
                new_product_id = data['product_id']
                if current_item['content_type'] != 'product':
                    return jsonify({'success': False, 'error': 'Can only change product_id for product posts'}), 400
                
                # Verify product exists
                cursor.execute("SELECT id, name, sku, image_url, url, description, short_description FROM clan_products WHERE id = %s", (new_product_id,))
                product = cursor.fetchone()
                if not product:
                    return jsonify({'success': False, 'error': f'Product {new_product_id} not found'}), 404
                
                update_fields.append("product_id = %s")
                update_values.append(new_product_id)
                
                # If regenerate_caption is requested, generate new caption
                if data.get('regenerate_caption', False):
                    try:
                        from utils.product_post_caption_generator import generate_product_post_caption
                        from utils.content_generation.clan_data_extractor import ClanDataExtractor
                        
                        # Get product data
                        extractor = ClanDataExtractor()
                        product_data = extractor.extract_product_data(new_product_id)
                        
                        # Generate caption
                        caption_result = generate_product_post_caption(
                            product_name=product_data.get('name', ''),
                            product_description=product_data.get('description') or product_data.get('short_description', ''),
                            product_url=product_data.get('url', ''),
                            model='mistral'
                        )
                        
                        new_caption = caption_result.get('caption', '')
                        if new_caption:
                            update_fields.append("generated_caption = %s")
                            update_values.append(new_caption)
                            logger.info(f"Generated new caption for product {new_product_id}")
                    except Exception as e:
                        logger.error(f"Error generating caption for product {new_product_id}: {e}")
                        # Continue without regenerating caption
            
            # Handle caption editing
            if 'generated_caption' in data:
                update_fields.append("generated_caption = %s")
                update_values.append(data['generated_caption'])
            
            # Handle rescheduling
            if 'scheduled_date' in data:
                update_fields.append("scheduled_date = %s")
                update_values.append(data['scheduled_date'])
            
            if 'scheduled_time' in data:
                update_fields.append("scheduled_time = %s")
                update_values.append(data['scheduled_time'])
            
            # Recalculate scheduled_timestamp if date or time changed
            if 'scheduled_date' in data or 'scheduled_time' in data:
                # Get the final scheduled_date and scheduled_time
                final_date = data.get('scheduled_date') or current_item['scheduled_date']
                final_time = data.get('scheduled_time') or current_item['scheduled_time']
                
                if final_date and final_time:
                    # Parse time if it's a string
                    if isinstance(final_time, str):
                        # Remove seconds if present (HH:MM:SS -> HH:MM)
                        time_parts = final_time.split(':')
                        hour = int(time_parts[0])
                        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                        final_time_obj = time(hour, minute)
                    else:
                        final_time_obj = final_time
                    
                    # Parse date if it's a string
                    if isinstance(final_date, str):
                        final_date_obj = date.fromisoformat(final_date)
                    else:
                        final_date_obj = final_date
                    
                    # Create timestamp
                    scheduled_timestamp = datetime.combine(final_date_obj, final_time_obj)
                    update_fields.append("scheduled_timestamp = %s")
                    update_values.append(scheduled_timestamp)
            
            if not update_fields:
                return jsonify({'success': False, 'error': 'No valid fields to update'}), 400
            
            # Add updated_at (no placeholder needed - it's a function call)
            update_fields.append("updated_at = NOW()")
            
            # Build the SET clause - join field assignments
            set_clause = ', '.join(update_fields)
            
            # Execute update - item_id goes at the end for WHERE clause
            update_query = f"UPDATE posting_queue SET {set_clause} WHERE id = %s"
            # Add item_id to values for WHERE clause
            update_values.append(item_id)
            cursor.execute(update_query, tuple(update_values))
            
            # Fetch updated item
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
                    cp.name as product_name,
                    cp.sku as product_sku,
                    cp.image_url as product_image,
                    ci.idea_title,
                    ci.idea_description,
                    CASE 
                        WHEN pq.content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult') 
                             AND pq.image_path IS NOT NULL 
                             AND pq.image_path LIKE '/Users/%%/static/%%' 
                        THEN REPLACE(pq.image_path, '/Users/autojenny/Documents/projects/blog', '')
                        WHEN pq.content_type = 'product' AND cp.image_url IS NOT NULL
                        THEN cp.image_url
                        WHEN pq.content_type = 'product' AND pq.image_path IS NOT NULL
                        THEN pq.image_path
                        ELSE NULL
                    END as display_image_url
                FROM posting_queue pq
                LEFT JOIN clan_products cp ON pq.product_id = cp.id
                LEFT JOIN calendar_ideas ci ON pq.idea_id = ci.id
                WHERE pq.id = %s
            """, (item_id,))
            
            updated_item = cursor.fetchone()
            if not updated_item:
                return jsonify({'success': False, 'error': 'Failed to fetch updated item'}), 500
            
            # Convert to dict and format dates
            item_dict = dict(updated_item)
            for key in ['created_at', 'updated_at', 'scheduled_date', 'scheduled_timestamp']:
                if item_dict.get(key) and hasattr(item_dict[key], 'isoformat'):
                    item_dict[key] = item_dict[key].isoformat()
            if item_dict.get('scheduled_time'):
                item_dict['scheduled_time'] = str(item_dict['scheduled_time'])
            
            return jsonify({
                'success': True,
                'message': 'Queue item updated successfully',
                'item': item_dict
            })
            
    except Exception as e:
        logger.error(f"Error updating queue item {item_id}: {e}")
        logger.exception("Full exception details:")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/posting-queue/<int:item_id>', methods=['DELETE'])
def delete_queue_item(item_id):
    """Delete a posting queue item"""
    try:
        with db_manager.get_cursor() as cursor:
            # Check if item exists and get status
            cursor.execute("""
                SELECT status, content_type
                FROM posting_queue
                WHERE id = %s
            """, (item_id,))
            
            item = cursor.fetchone()
            if not item:
                return jsonify({'success': False, 'error': 'Queue item not found'}), 404
            
            # Can't delete published posts (preserve historical record)
            if item['status'] == 'published':
                return jsonify({
                    'success': False,
                    'error': 'Cannot delete published posts (preserve historical record)'
                }), 400
            
            # Delete the item
            cursor.execute("DELETE FROM posting_queue WHERE id = %s", (item_id,))
            
            return jsonify({
                'success': True,
                'message': 'Queue item deleted successfully'
            })
            
    except Exception as e:
        logger.error(f"Error deleting queue item {item_id}: {e}")
        logger.exception("Full exception details:")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
