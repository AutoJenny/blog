"""
Planning API - Profiles

CRUD endpoints for Product & Category Profiles
"""

from flask import request, jsonify
from config.database import db_manager
import logging
import json
from datetime import date

logger = logging.getLogger(__name__)

def api_create_profile():
    """Create a new profile (Product or Category)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        profile_type = data.get('profile_type')
        if profile_type not in ['product', 'category']:
            return jsonify({'success': False, 'error': 'Invalid profile_type. Must be "product" or "category"'}), 400
        
        title = data.get('title')
        if not title:
            return jsonify({'success': False, 'error': 'Title is required'}), 400
        
        # Validate product or category selection
        if profile_type == 'product':
            product_id = data.get('profile_product_id')
            if not product_id:
                return jsonify({'success': False, 'error': 'Product selection is required'}), 400
        else:
            category_id = data.get('profile_category_id')
            if not category_id:
                return jsonify({'success': False, 'error': 'Category selection is required'}), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Create post record
                cur.execute("""
                    INSERT INTO post (
                        title, profile_type, profile_product_id, profile_category_id,
                        profile_producer_name, profile_standfirst, status, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id
                """, (
                    title,
                    profile_type,
                    data.get('profile_product_id') if profile_type == 'product' else None,
                    data.get('profile_category_id') if profile_type == 'category' else None,
                    data.get('profile_producer_name'),
                    data.get('profile_standfirst'),
                    'draft'  # New profiles start as drafts
                ))
                
                post_id = cur.fetchone()[0]
                
                # Schedule in calendar if week/year provided
                year = data.get('year')
                week_number = data.get('week_number')
                weekday = data.get('weekday')
                
                # If weekday not provided, get default from post_type_config for profiles
                if year and week_number:
                    if weekday is None:
                        from blueprints.post_type_config import get_publication_day_for_post_type
                        profile_config = get_publication_day_for_post_type('profile', cur)
                        weekday = profile_config['day'] if profile_config else 4  # Fallback to Thursday
                    
                    cur.execute("""
                        INSERT INTO calendar_week_posts (
                            year, week_number, post_id, weekday, created_at
                        )
                        VALUES (%s, %s, %s, %s, NOW())
                        ON CONFLICT (year, week_number, post_id) DO UPDATE SET
                            weekday = EXCLUDED.weekday,
                            updated_at = NOW()
                    """, (year, week_number, post_id, weekday))
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'post_id': post_id,
                    'profile_id': post_id
                })
                
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

def api_get_profile(profile_id):
    """Get a profile by ID"""
    try:
        with db_manager.get_cursor() as cur:
            # Removed deprecated calendar_week_posts join - using new cyclic system
            cur.execute("""
                SELECT 
                    p.id, p.title, p.profile_type, p.profile_product_id, p.profile_category_id,
                    p.profile_producer_id, p.profile_producer_name, p.profile_standfirst,
                    p.profile_explore_links, p.profile_quick_facts, p.slug,
                    p.status, p.created_at, p.updated_at
                FROM post p
                WHERE p.id = %s AND p.profile_type IS NOT NULL
            """, (profile_id,))
            
            row = cur.fetchone()
            
            if not row:
                return jsonify({'success': False, 'error': 'Profile not found'}), 404
            
            if isinstance(row, dict):
                profile = {
                    'id': row['id'],
                    'title': row['title'],
                    'profile_type': row['profile_type'],
                    'profile_product_id': row.get('profile_product_id'),
                    'profile_category_id': row.get('profile_category_id'),
                    'profile_producer_id': row.get('profile_producer_id'),
                    'profile_producer_name': row.get('profile_producer_name'),
                    'profile_standfirst': row.get('profile_standfirst'),
                    'profile_explore_links': row.get('profile_explore_links'),
                    'profile_quick_facts': row.get('profile_quick_facts'),
                    'slug': row.get('slug'),
                    'status': row.get('status'),
                    'created_at': row['created_at'].isoformat() if row.get('created_at') else None,
                    'updated_at': row['updated_at'].isoformat() if row.get('updated_at') else None
                }
            else:
                profile = {
                    'id': row[0],
                    'title': row[1],
                    'profile_type': row[2],
                    'profile_product_id': row[3] if len(row) > 3 else None,
                    'profile_category_id': row[4] if len(row) > 4 else None,
                    'profile_producer_id': row[5] if len(row) > 5 else None,
                    'profile_producer_name': row[6] if len(row) > 6 else None,
                    'profile_standfirst': row[7] if len(row) > 7 else None,
                    'profile_explore_links': row[8] if len(row) > 8 else None,
                    'profile_quick_facts': row[9] if len(row) > 9 else None,
                    'slug': row[10] if len(row) > 10 else None,
                    'status': row[11] if len(row) > 11 else None,
                    'created_at': row[12].isoformat() if len(row) > 12 and row[12] else None,
                    'updated_at': row[13].isoformat() if len(row) > 13 and row[13] else None
                }
            
            return jsonify({
                'success': True,
                'profile': profile
            })
            
    except Exception as e:
        logger.error(f"Error fetching profile {profile_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

def api_update_profile(profile_id):
    """Update an existing profile"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Update post record
                update_fields = []
                update_values = []
                
                if 'title' in data:
                    update_fields.append('title = %s')
                    update_values.append(data['title'])
                
                if 'profile_standfirst' in data:
                    update_fields.append('profile_standfirst = %s')
                    update_values.append(data['profile_standfirst'])
                
                if 'profile_producer_name' in data:
                    update_fields.append('profile_producer_name = %s')
                    update_values.append(data['profile_producer_name'])
                
                if 'profile_product_id' in data:
                    update_fields.append('profile_product_id = %s')
                    update_values.append(data['profile_product_id'])
                
                if 'profile_category_id' in data:
                    update_fields.append('profile_category_id = %s')
                    update_values.append(data['profile_category_id'])
                
                update_fields.append('updated_at = NOW()')
                update_values.append(profile_id)
                
                if len(update_fields) > 1:  # More than just updated_at
                    cur.execute(f"""
                        UPDATE post
                        SET {', '.join(update_fields)}
                        WHERE id = %s AND profile_type IS NOT NULL
                    """, update_values)
                
                # Update calendar scheduling
                year = data.get('year')
                week_number = data.get('week_number')
                weekday = data.get('weekday')
                
                # If weekday not provided, get default from post_type_config for profiles
                if year and week_number:
                    if weekday is None:
                        from blueprints.post_type_config import get_publication_day_for_post_type
                        profile_config = get_publication_day_for_post_type('profile', cur)
                        weekday = profile_config['day'] if profile_config else 4  # Fallback to Thursday
                    
                    cur.execute("""
                        INSERT INTO calendar_week_posts (
                            year, week_number, post_id, weekday, created_at
                        )
                        VALUES (%s, %s, %s, %s, NOW())
                        ON CONFLICT (year, week_number, post_id) DO UPDATE SET
                            weekday = EXCLUDED.weekday,
                            updated_at = NOW()
                    """, (year, week_number, profile_id, weekday))
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'profile_id': profile_id
                })
                
    except Exception as e:
        logger.error(f"Error updating profile {profile_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

def api_delete_profile(profile_id):
    """Delete a profile"""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Delete from calendar_week_posts first (cascade should handle this, but explicit is safer)
                cur.execute("""
                    DELETE FROM calendar_week_posts WHERE post_id = %s
                """, (profile_id,))
                
                # Delete post (cascade will handle related records)
                cur.execute("""
                    DELETE FROM post WHERE id = %s AND profile_type IS NOT NULL
                """, (profile_id,))
                
                if cur.rowcount == 0:
                    return jsonify({'success': False, 'error': 'Profile not found'}), 404
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Profile deleted'
                })
                
    except Exception as e:
        logger.error(f"Error deleting profile {profile_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

