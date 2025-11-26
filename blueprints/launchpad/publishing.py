# blueprints/launchpad/publishing.py
"""Publishing-related routes and functionality."""

from flask import Blueprint, render_template, jsonify, request
import logging
from config.database import db_manager
import os
import json
from blueprints.launchpad.publishing_helpers import (
    get_post_with_development,
    find_header_image
)

bp = Blueprint("publishing", __name__)
logger = logging.getLogger(__name__)


@bp.route('/publishing')
def publishing():
    """Publishing management page."""
    return render_template('launchpad/publishing.html')

@bp.route('/api/publish/<int:post_id>', methods=['POST'])
def publish_post_to_clan(post_id):
    """Publish a post to clan.com"""
    try:
        # Sync product-match selections to cross-promotion before loading post data
        # This ensures published posts use the matched IDs
        import sys
        import os
        blog_launchpad_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'blog-launchpad')
        sys.path.insert(0, blog_launchpad_path)
        from publish.post_data_loader import sync_product_match_to_cross_promotion
        sync_product_match_to_cross_promotion(post_id)
        
        # Get post data
        post = get_post_with_development(post_id)
        if not post:
            return jsonify({'success': False, 'error': 'Post not found'}), 404
        
        # Use SAME function as preview for sections
        import sys
        import os
        blog_launchpad_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'blog-launchpad')
        sys.path.insert(0, blog_launchpad_path)
        from publish.post_data_loader import get_post_sections_with_images
        sections = get_post_sections_with_images(post_id)
        
        # Fix field mapping - ensure post has the fields our function expects
        if post.get('post_id') and not post.get('id'):
            post['id'] = post['post_id']
        
        # Ensure summary field exists and has content
        if not post.get('summary'):
            post['summary'] = post.get('intro_blurb')
            if not post['summary']:
                raise ValueError("Post must have either summary or intro_blurb")
        
        # Ensure created_at is handled properly - convert to datetime object for template
        if post.get('created_at'):
            logger.info(f"Original created_at: {post['created_at']} (type: {type(post['created_at'])})")
            if isinstance(post['created_at'], str):
                from datetime import datetime
                try:
                    post['created_at'] = datetime.fromisoformat(post['created_at'].replace('Z', '+00:00'))
                    logger.info(f"Converted to datetime: {post['created_at']}")
                except Exception as e:
                    logger.error(f"Failed to parse date: {e}")
                    # If parsing fails, try other formats
                    try:
                        post['created_at'] = datetime.strptime(post['created_at'], '%a, %d %b %Y %H:%M:%S %Z')
                        logger.info(f"Converted with strptime: {post['created_at']}")
                    except Exception as e2:
                        logger.error(f"Failed to parse with strptime: {e2}")
                        post['created_at'] = None
            elif hasattr(post['created_at'], 'isoformat'):
                # Already a datetime object, keep as is
                logger.info(f"Already datetime object: {post['created_at']}")
                pass
            else:
                logger.error(f"Unknown date type: {type(post['created_at'])}")
                post['created_at'] = None
        
        # Always fetch cross-promotion data (decoupled from header image presence)
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT header_image_caption, header_image_title, header_image_width, header_image_height,
                           cross_promotion_category_id, cross_promotion_category_title,
                           cross_promotion_product_id, cross_promotion_product_title,
                           cross_promotion_category_position, cross_promotion_product_position,
                           cross_promotion_category_widget_html, cross_promotion_product_widget_html
                    FROM post WHERE id = %s
                """, (post_id,))
                header_data = cursor.fetchone()
                
            # Add header image if exists (optional) - use SAME function as preview
            import sys
            import os
            blog_launchpad_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'blog-launchpad')
            sys.path.insert(0, blog_launchpad_path)
            from publish.header_image_finder import get_header_image
            header_image = get_header_image(post_id)
            if header_image:
                post['header_image'] = header_image
                # Add metadata from post table if not already set
                if not post['header_image'].get('caption') and header_data and header_data.get('header_image_caption'):
                    post['header_image']['caption'] = header_data['header_image_caption']
                if not post['header_image'].get('title') and header_data and header_data.get('header_image_title'):
                    post['header_image']['title'] = header_data['header_image_title']
                if not post['header_image'].get('width') and header_data and header_data.get('header_image_width'):
                    post['header_image']['width'] = header_data['header_image_width']
                if not post['header_image'].get('height') and header_data and header_data.get('header_image_height'):
                    post['header_image']['height'] = header_data['header_image_height']
                
            # Map cross-promotion regardless of header image
            # Use header_data which was reloaded AFTER sync, so it contains the synced IDs
                post['cross_promotion'] = {
                    'category_id': header_data['cross_promotion_category_id'] if header_data else None,
                    'category_title': header_data['cross_promotion_category_title'] if header_data else None,
                    'product_id': header_data['cross_promotion_product_id'] if header_data else None,
                    'product_title': header_data['cross_promotion_product_title'] if header_data else None,
                'category_position': header_data.get('cross_promotion_category_position') if header_data else None,
                'product_position': header_data.get('cross_promotion_product_position') if header_data else None,
                'category_widget_html': header_data.get('cross_promotion_category_widget_html') if header_data else None,
                'product_widget_html': header_data.get('cross_promotion_product_widget_html') if header_data else None
                }
                
                # Log the IDs being used for debugging
                logger.info(f"=== CROSS-PROMOTION DATA FOR PUBLISH ===")
                logger.info(f"Post {post_id} cross-promotion: product_id={post['cross_promotion'].get('product_id')}, category_id={post['cross_promotion'].get('category_id')}")
                logger.info(f"Product widget HTML: {post['cross_promotion'].get('product_widget_html')}")
                logger.info(f"Category widget HTML: {post['cross_promotion'].get('category_widget_html')}")

            # Auto-select random category/product IDs and default positions if missing
            # BUT: Only if product-match sync didn't already set them (don't overwrite matched IDs)
            try:
                cp = post['cross_promotion']
                to_persist = {}
                # Select a random category if none set (but only if not synced from product-match)
                if not cp.get('category_id'):
                    cursor.execute("""
                        SELECT id, name FROM clan_categories 
                        ORDER BY RANDOM() LIMIT 1
                    """)
                    cat = cursor.fetchone()
                    if cat:
                        cp['category_id'] = cat['id']
                        cp['category_title'] = cat['name'] or 'Related Department'
                        to_persist['cross_promotion_category_id'] = cp['category_id']
                        to_persist['cross_promotion_category_title'] = cp['category_title']
                # Select a random product if none set (but only if not synced from product-match)
                if not cp.get('product_id'):
                    cursor.execute("""
                        SELECT id, name FROM clan_products 
                        ORDER BY RANDOM() LIMIT 1
                    """)
                    prod = cursor.fetchone()
                    if prod:
                        cp['product_id'] = prod['id']
                        cp['product_title'] = prod['name'] or 'Related Products'
                        to_persist['cross_promotion_product_id'] = cp['product_id']
                        to_persist['cross_promotion_product_title'] = cp['product_title']
                # Set default positions if missing (but only if IDs weren't synced from product-match)
                # If IDs exist but positions are NULL, that means they were synced - use section count for positions
                if not cp.get('category_position') and cp.get('category_id'):
                    # Get section count to determine position
                    cursor.execute("SELECT COUNT(*) as section_count FROM post_section WHERE post_id = %s", (post_id,))
                    section_count_result = cursor.fetchone()
                    section_count = section_count_result.get('section_count', 0) if section_count_result else 0
                    default_category_position = min(2, section_count) + 1 if section_count > 0 else 1
                    cp['category_position'] = default_category_position
                    to_persist['cross_promotion_category_position'] = cp['category_position']
                elif not cp.get('category_position'):
                    cp['category_position'] = 2
                    to_persist['cross_promotion_category_position'] = cp['category_position']
                if not cp.get('product_position') and cp.get('product_id'):
                    # Get section count to determine position
                    cursor.execute("SELECT COUNT(*) as section_count FROM post_section WHERE post_id = %s", (post_id,))
                    section_count_result = cursor.fetchone()
                    section_count = section_count_result.get('section_count', 0) if section_count_result else 0
                    default_product_position = min(4, section_count) + 1 if section_count > 0 else 1
                    cp['product_position'] = default_product_position
                    to_persist['cross_promotion_product_position'] = cp['product_position']
                elif not cp.get('product_position'):
                    cp['product_position'] = 4
                    to_persist['cross_promotion_product_position'] = cp['product_position']
                # Persist any newly selected IDs/titles/positions
                if to_persist:
                    placeholders = []
                    values = []
                    for k, v in to_persist.items():
                        placeholders.append(f"{k} = %s")
                        values.append(v)
                    values.append(post_id)
                    cursor.execute(f"""
                        UPDATE post SET 
                            {', '.join(placeholders)},
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, tuple(values))
                    cursor.connection.commit()
                    # Update post dict with persisted values
                    if 'cross_promotion_category_id' in to_persist:
                        cp['category_id'] = to_persist['cross_promotion_category_id']
                    if 'cross_promotion_product_id' in to_persist:
                        cp['product_id'] = to_persist['cross_promotion_product_id']
            except Exception as e:
                logger.warning(f"Could not auto-select random cross-promotion IDs: {e}")

            # Auto-generate missing widget HTML from IDs/positions to ensure widgets are inserted
            try:
                cp = post['cross_promotion']
                needs_update = False
                if cp.get('category_id') and cp.get('category_position') and not cp.get('category_widget_html'):
                    cp['category_widget_html'] = f"{{{{widget type=\"swcatalog/widget_crossSell_category\" category_id=\"{cp.get('category_id')}\" title=\"{cp.get('category_title') or 'Related Department'}\"}}}}"
                    needs_update = True
                if cp.get('product_id') and cp.get('product_position') and not cp.get('product_widget_html'):
                    cp['product_widget_html'] = f"{{{{widget type=\"swcatalog/widget_crossSell_product\" product_id=\"{cp.get('product_id')}\" title=\"{cp.get('product_title') or 'Related Products'}\"}}}}"
                    needs_update = True
                if needs_update:
                    with db_manager.get_cursor() as cursor2:
                        cursor2.execute("""
                            UPDATE post SET 
                                cross_promotion_category_widget_html = %s,
                                cross_promotion_product_widget_html = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (
                            cp.get('category_widget_html'),
                            cp.get('product_widget_html'),
                            post_id
                        ))
                        cursor2.connection.commit()
            except Exception as e:
                logger.warning(f"Could not auto-generate/persist widget HTML: {e}")
        
        # Import publishing class
        import sys
        sys.path.append('/Users/autojenny/Documents/projects/blog/blog-launchpad')
        from clan_publisher import ClanPublisher
        
        # Debug: Log what we're about to send
        logger.info(f"=== FLASK ENDPOINT DEBUG ===")
        logger.info(f"Post data keys: {list(post.keys()) if post else 'NO POST'}")
        logger.info(f"Post title: {post.get('title', 'NO TITLE') if post else 'NO POST'}")
        logger.info(f"Number of sections: {len(sections) if sections else 0}")
        if sections:
            logger.info(f"Section IDs: {[s.get('id') for s in sections]}")
        
        # Create publisher instance and attempt to publish
        publisher = ClanPublisher()
        result = publisher.publish_to_clan(post, sections)
        
        # Debug: Log the result
        logger.info(f"Publishing result: {result}")
        
        if result['success']:
            # Update database with clan post details
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE post SET 
                        clan_post_id = %s,
                        status = 'published',
                        clan_last_attempt = CURRENT_TIMESTAMP,
                        clan_error = NULL,
                        clan_uploaded_url = %s,
                        first_published_at = COALESCE(first_published_at, CURRENT_TIMESTAMP)
                    WHERE id = %s
                """, (result.get('clan_post_id'), result.get('url'), post_id))
            
            return jsonify({
                'success': True, 
                'message': 'Post published successfully to clan.com',
                'clan_post_id': result.get('clan_post_id'),
                'url': result.get('url')
            })
        else:
            # Update database with error
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE post SET 
                        status = 'in_process',
                        clan_last_attempt = CURRENT_TIMESTAMP,
                        clan_error = %s
                    WHERE id = %s
                """, (result.get('error'), post_id))
            
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
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE post SET 
                    status = 'in_process',
                    clan_last_attempt = CURRENT_TIMESTAMP,
                    clan_error = %s
                WHERE id = %s
            """, (str(e), post_id))
        
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/clan-api-data/<int:post_id>')
def clan_api_data(post_id):
    """View the actual API request data that was/will be sent to Clan.com."""
    try:
        # Get post data using our existing helper function
        post = get_post_with_development(post_id)
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        # Use SAME function as preview for sections
        import sys
        import os
        blog_launchpad_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'blog-launchpad')
        sys.path.insert(0, blog_launchpad_path)
        from publish.post_data_loader import get_post_sections_with_images
        sections = get_post_sections_with_images(post_id)
        
        # Fix field mapping - ensure post has the fields our function expects
        if post.get('post_id') and not post.get('id'):
            post['id'] = post['post_id']
        
        # Ensure summary field exists and has content
        if not post.get('summary'):
            post['summary'] = post.get('intro_blurb')
            if not post['summary']:
                raise ValueError("Post must have either summary or intro_blurb")
        
        # Ensure created_at is handled properly - convert to datetime object for template
        if post.get('created_at'):
            if isinstance(post['created_at'], str):
                from datetime import datetime
                try:
                    post['created_at'] = datetime.fromisoformat(post['created_at'].replace('Z', '+00:00'))
                except Exception as e:
                    try:
                        post['created_at'] = datetime.strptime(post['created_at'], '%a, %d %b %Y %H:%M:%S %Z')
                    except Exception as e2:
                        post['created_at'] = None
            elif hasattr(post['created_at'], 'isoformat'):
                # Already a datetime object, keep as is
                pass
            else:
                post['created_at'] = None
        
        # Add header image if exists
        header_image_path = find_header_image(post_id)
        if header_image_path:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT header_image_caption, header_image_title, header_image_width, header_image_height
                    FROM post WHERE id = %s
                """, (post_id,))
                header_data = cursor.fetchone()
                
                if header_data:
                    post['header_image'] = {
                        'path': header_image_path,
                        'alt_text': f"Header image for {post.get('title', 'this post')}",
                        'caption': header_data['header_image_caption'],
                        'title': header_data['header_image_title'],
                        'width': header_data['header_image_width'],
                        'height': header_data['header_image_height']
                    }
        
        # Fetch cross-promotion data for all posts (not just those with header images)
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT cross_promotion_category_id, cross_promotion_category_title,
                       cross_promotion_product_id, cross_promotion_product_title,
                       cross_promotion_category_position, cross_promotion_product_position,
                       cross_promotion_category_widget_html, cross_promotion_product_widget_html
                FROM post WHERE id = %s
            """, (post_id,))
            cross_promo_data = cursor.fetchone()
            
            if cross_promo_data:
                post['cross_promotion'] = {
                    'category_id': cross_promo_data['cross_promotion_category_id'],
                    'category_title': cross_promo_data['cross_promotion_category_title'],
                    'product_id': cross_promo_data['cross_promotion_product_id'],
                    'product_title': cross_promo_data['cross_promotion_product_title'],
                    'category_position': cross_promo_data.get('cross_promotion_category_position'),
                    'product_position': cross_promo_data.get('cross_promotion_product_position'),
                    'category_widget_html': cross_promo_data.get('cross_promotion_category_widget_html'),
                    'product_widget_html': cross_promo_data.get('cross_promotion_product_widget_html')
                }
        
        # Import publishing class to get the actual API data
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'blog-launchpad'))
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
            
    except Exception as e:
        logger.error(f"Error in clan_api_data for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/clan-post-html/<int:post_id>')
def clan_post_html(post_id):
    """View the clan_post HTML that will be uploaded to Clan.com."""
    try:
        # Get view type parameter (default to 'local')
        view_type = request.args.get('view', 'local')
        
        # Get post data using our existing helper function
        post = get_post_with_development(post_id)
        if not post:
            return "Post not found", 404
        
        # Use SAME function as preview for sections
        import sys
        import os
        blog_launchpad_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'blog-launchpad')
        sys.path.insert(0, blog_launchpad_path)
        from publish.post_data_loader import get_post_sections_with_images
        sections = get_post_sections_with_images(post_id)
        
        # Find header image
        header_image_path = find_header_image(post_id)
        if header_image_path:
            # Get header image caption from database
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT header_image_caption, header_image_title, header_image_width, header_image_height
                    FROM post WHERE id = %s
                """, (post_id,))
                header_data = cursor.fetchone()
                header_caption = header_data['header_image_caption'] if header_data and header_data['header_image_caption'] else None
            
            post['header_image'] = {
                'path': header_image_path,
                'alt_text': f"Header image for {post.get('title', 'this post')}",
                'caption': header_caption,
                'title': header_data['header_image_title'] if header_data and header_data['header_image_title'] else None,
                'width': header_data['header_image_width'] if header_data and header_data['header_image_width'] else None,
                'height': header_data['header_image_height'] if header_data and header_data['header_image_height'] else None
            }
        
        if view_type == 'local':
            # Return raw HTML with local paths (for development/debugging)
            raw_html = render_template('launchpad/clan_post_raw.html', post=post, sections=sections)
            return raw_html, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        else:
            # Return processed HTML with CDN URLs (what gets sent to Clan.com)
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'blog-launchpad'))
            from clan_publisher import ClanPublisher
            publisher = ClanPublisher()
            
            # Get uploaded images mapping from database
            uploaded_images = {}
            try:
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT local_image_path, clan_uploaded_url 
                        FROM section_image_mappings 
                        WHERE post_id = %s
                    """, (post_id,))
                    
                    for row in cursor.fetchall():
                        uploaded_images[row['local_image_path']] = row['clan_uploaded_url']
                        
                    # Also get header image mapping if it exists
                    cursor.execute("""
                        SELECT local_image_path, clan_uploaded_url 
                        FROM section_image_mappings 
                        WHERE post_id = %s AND section_id IS NULL
                    """, (post_id,))
                    
                    for row in cursor.fetchall():
                        uploaded_images[row['local_image_path']] = row['clan_uploaded_url']
                        
            except Exception as e:
                logger.warning(f"Could not load image mappings: {e}")
            
            # Get the exact same HTML that gets uploaded
            # Ensure post has 'id' field for compatibility
            if 'post_id' in post and 'id' not in post:
                post['id'] = post['post_id']
            upload_html = publisher.get_preview_html_content(post, sections, uploaded_images)
            
            if upload_html:
                # Return the actual upload HTML as raw text - NO RENDERING
                # Set content type to text/plain so browser shows source code
                return upload_html, 200, {'Content-Type': 'text/plain; charset=utf-8'}
            else:
                return "Error: Failed to generate upload HTML", 500
                
    except Exception as e:
        logger.error(f"Error in clan_post_html for post {post_id}: {e}")
        return f"Error: {str(e)}", 500
