"""
Publish Endpoint
Flask route handler for publishing posts to clan.com
"""

from flask import Blueprint, jsonify, request
import logging
import psycopg
import psycopg.rows
from .post_data_loader import get_post_with_development, get_post_sections_with_images
from .header_image_finder import get_header_image
from .cross_promotion_loader import load_cross_promotion_data

logger = logging.getLogger(__name__)

bp = Blueprint('publish', __name__, url_prefix='/api/publish')


def get_db_connection():
    """Get database connection."""
    import os
    return psycopg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        dbname=os.getenv('DB_NAME', 'blog'),
        user=os.getenv('DB_USER', 'autojenny'),
        password=os.getenv('DB_PASSWORD', '')
    )


def publish_post_to_clan_handler(post_id):
    """Publish a post to clan.com"""
    try:
        # Use unified data preparation - SAME as preview route
        from .post_data_loader import prepare_post_data
        post, sections = prepare_post_data(post_id)
        if not post:
            return jsonify({'success': False, 'error': 'Post not found'}), 404
        
        # Fix field mapping - ensure post has the fields our function expects
        if post.get('post_id') and not post.get('id'):
            post['id'] = post['post_id']
        
        # Ensure summary field exists and has content
        if not post.get('summary'):
            post['summary'] = post.get('intro_blurb')
            if not post['summary']:
                raise ValueError("Post must have either summary or intro_blurb")
        
        # Ensure created_at is handled properly
        if post.get('created_at') and not isinstance(post['created_at'], str):
            post['created_at'] = post['created_at'].isoformat() if hasattr(post['created_at'], 'isoformat') else str(post['created_at'])
        
        logger.info(f"=== HEADER IMAGE CHECK FOR POST {post_id} ===")
        logger.info(f"Post has header_image: {post.get('header_image')}")
        logger.info(f"Post header_image path: {post.get('header_image', {}).get('path') if post.get('header_image') else 'N/A'}")
        
        # Import publishing class
        from clan_publisher import ClanPublisher
        
        # Debug: Log what we're about to send
        logger.info(f"=== FLASK ENDPOINT DEBUG ===")
        logger.info(f"Post data keys: {list(post.keys()) if post else 'NO POST'}")
        logger.info(f"Post title: {post.get('title', 'NO TITLE') if post else 'NO POST'}")
        logger.info(f"Number of sections: {len(sections) if sections else 0}")
        if sections:
            logger.info(f"Section IDs: {[s.get('id') for s in sections]}")
        
        # CRITICAL: Verify header_image is set before publishing
        logger.info(f"=== PRE-PUBLISH HEADER IMAGE VERIFICATION ===")
        logger.info(f"post.get('header_image'): {post.get('header_image')}")
        if post.get('header_image'):
            logger.info(f"post['header_image'].get('path'): {post['header_image'].get('path')}")
        else:
            logger.warning(f"⚠️ WARNING: post['header_image'] is None/empty before calling publish_to_clan!")
        
        # Create publisher instance and attempt to publish
        publisher = ClanPublisher()
        result = publisher.publish_to_clan(post, sections)
        
        # Debug: Log the result
        logger.info(f"Publishing result: {result}")
        
        if result['success']:
            # Update database with clan post details
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE post SET 
                        clan_post_id = %s,
                        status = 'published',
                        clan_last_attempt = CURRENT_TIMESTAMP,
                        clan_error = NULL,
                        clan_uploaded_url = %s
                    WHERE id = %s
                """, (result.get('clan_post_id'), result.get('url'), post_id))
                conn.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Post published successfully to clan.com',
                'clan_post_id': result.get('clan_post_id'),
                'url': result.get('url')
            })
        else:
            # Update database with error
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE post SET 
                        status = 'error',
                        clan_last_attempt = CURRENT_TIMESTAMP,
                        clan_error = %s
                    WHERE id = %s
                """, (result.get('error'), post_id))
                conn.commit()
            
            # Check if it's a network connectivity issue
            error_msg = result.get('error', 'Unknown error occurred')
            if 'timeout' in error_msg.lower() or 'connection' in error_msg.lower():
                error_msg = f"Network Error: Cannot connect to clan.com. Please check your internet connection and try again. (Details: {error_msg})"
            
            return jsonify({
                'success': False, 
                'error': error_msg
            }), 500
            
    except Exception as e:
        # Update database with error
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE post SET 
                    status = 'error',
                    clan_last_attempt = CURRENT_TIMESTAMP,
                    clan_error = %s
                WHERE id = %s
            """, (str(e), post_id))
            conn.commit()
        
        return jsonify({'success': False, 'error': str(e)}), 500


def clan_api_data_handler(post_id):
    """View the actual API request data that was/will be sent to Clan.com."""
    # Use unified data preparation - SAME as preview and publishing routes
    from .post_data_loader import prepare_post_data
    post, sections = prepare_post_data(post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    # Fix field mapping - ensure post has the fields our function expects
    if post.get('post_id') and not post.get('id'):
        post['id'] = post['post_id']
    
    # Ensure summary field exists and has content
    if not post.get('summary'):
        post['summary'] = post.get('intro_blurb')
        if not post['summary']:
            raise ValueError("Post must have either summary or intro_blurb")
    
    # Ensure created_at is handled properly
    if post.get('created_at') and not isinstance(post['created_at'], str):
        post['created_at'] = post['created_at'].isoformat() if hasattr(post['created_at'], 'isoformat') else str(post['created_at'])
    
    # Import publishing class to get the actual API data
    from clan_publisher import ClanPublisher
    publisher = ClanPublisher()
    
    # Get the actual API request data that would be sent to Clan.com
    try:
        # This will generate the same data structure that gets sent to Clan.com
        logger.info(f"Calling _prepare_api_data for post {post_id}")
        logger.info(f"Post data keys: {list(post.keys()) if post else 'NO POST'}")
        logger.info(f"Post summary: {post.get('summary')}")
        logger.info(f"Post subtitle: {post.get('subtitle')}")
        api_data = publisher._prepare_api_data(post, sections)
        logger.info(f"API data returned: {api_data}")
        return jsonify(api_data)
    except Exception as e:
        logger.error(f"Error preparing API data for post {post_id}: {e}")
        return jsonify({'error': f'Failed to prepare API data: {str(e)}'}), 500




