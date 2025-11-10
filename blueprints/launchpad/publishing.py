# blueprints/launchpad/publishing.py
"""Publishing-related routes and functionality."""

from flask import Blueprint, render_template, jsonify, request
import logging
from config.database import db_manager
import os
import json

bp = Blueprint("publishing", __name__)
logger = logging.getLogger(__name__)


def get_post_with_development(post_id):
    """Fetch post with development data and include image paths."""
    with db_manager.get_cursor() as cursor:
        # Get post data, alias post.id as post_id
        cursor.execute("""
            SELECT p.id AS post_id, p.title, p.subtitle, p.created_at, p.updated_at, p.status, p.slug, p.summary, p.title_choices,
                   p.clan_post_id, p.clan_uploaded_url,
                   p.header_image_id, p.header_image_caption, p.header_image_title, p.header_image_width, p.header_image_height,
                   pd.idea_seed, pd.intro_blurb, pd.main_title,
                   p.cross_promotion_category_id, p.cross_promotion_category_title,
                   p.cross_promotion_product_id, p.cross_promotion_product_title,
                   p.cross_promotion_category_position, p.cross_promotion_product_position,
                   p.cross_promotion_category_widget_html, p.cross_promotion_product_widget_html,
                   p.meta_title, p.meta_description, p.meta_tags, p.meta_image, p.meta_type, p.meta_site_name
            FROM post p
            LEFT JOIN post_development pd ON pd.post_id = p.id
            WHERE p.id = %s
        """, (post_id,))
        
        post = cursor.fetchone()
        if not post:
            return None
        
        post_dict = dict(post)
        
        # Try to get optimized header via post_images link first
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT i.path, i.alt_text, i.caption, i.filename
                FROM post_images pi
                JOIN image i ON pi.image_id = i.id
                WHERE pi.section_id IS NULL 
                  AND pi.image_type = 'header_optimized'
                  AND pi.post_id = %s
                LIMIT 1
            """, (post_id,))
            header_img = cursor.fetchone()
            
            if header_img and header_img['path']:
                # Use optimized header from post_images
                post_dict['header_image'] = {
                    'path': header_img['path'],
                    'id': post_dict.get('header_image_id'),
                    'caption': header_img['caption'] or post_dict.get('header_image_caption'),
                    'title': header_img['filename'] or post_dict.get('header_image_title'),
                    'alt_text': header_img['alt_text'],
                    'width': post_dict.get('header_image_width'),
                    'height': post_dict.get('header_image_height')
                }
            else:
                # Fallback to find_header_image() for legacy posts
                header_image_path = find_header_image(post_id)
                if header_image_path:
                    post_dict['header_image'] = {
                        'path': header_image_path,
                        'id': post_dict.get('header_image_id'),
                        'caption': post_dict.get('header_image_caption'),
                        'title': post_dict.get('header_image_title'),
                        'width': post_dict.get('header_image_width'),
                        'height': post_dict.get('header_image_height')
                    }
        
        return post_dict

def get_post_sections_with_images(post_id):
    """Fetch sections with complete image metadata from post_images linking table (matches preview data)."""
    with db_manager.get_cursor() as cursor:
        # Get all sections with images via post_images linking table (same as preview route)
        cursor.execute("""
            SELECT 
                ps.id, ps.post_id, ps.section_order, 
                ps.section_heading,
                ps.section_description, ps.ideas_to_include, ps.facts_to_include,
                ps.draft, ps.polished, ps.highlighting, ps.image_concepts,
                ps.image_prompts,
                ps.image_alt_text, ps.image_captions, ps.status,
                i.id AS image_id,
                i.filename,
                i.path AS image_path,
                i.alt_text AS image_alt_text,
                i.caption AS image_caption
            FROM post_section ps
            LEFT JOIN post_images pi ON ps.id = pi.section_id AND pi.image_type = 'section_optimized'
            LEFT JOIN image i ON pi.image_id = i.id
            WHERE ps.post_id = %s
            ORDER BY ps.section_order
        """, (post_id,))
        
        raw_sections = cursor.fetchall()
        sections = []
        
        for section in raw_sections:
            section_dict = dict(section)
            
            # Priority 1: Check Photo-harvesting route (selected_landscape.json)
            image_path = None
            caption_text = section_dict.get('image_captions') or ''
            alt_text = section_dict.get('image_alt_text') or ''
            
            try:
                import os
                import json
                photo_json_path = f"static/content/posts/{post_id}/sections/{section_dict['id']}/optimized/selected_landscape.json"
                if os.path.exists(photo_json_path):
                    with open(photo_json_path, 'r') as f:
                        photo_data = json.load(f)
                        photo = photo_data.get('photo', {})
                        if photo.get('url'):
                            # Use hotlinked provider URL (Pexels/Unsplash)
                            image_path = photo['url']
                            # Extract caption/alt from photo metadata if not already set
                            if not caption_text and photo.get('credits'):
                                caption_text = photo['credits']
                            if not alt_text and photo.get('photographer'):
                                alt_text = f"Photo by {photo['photographer']}"
            except Exception as e:
                logger.debug(f"Could not load Photo-harvesting JSON for section {section_dict['id']}: {e}")
            
            # Priority 2: Database link (post_images)
            if not image_path:
                image_path = section_dict.get('image_path')
            
            if image_path:
                # Image exists (Photo-harvesting or post_images linking table)
                section_dict['image'] = {
                    'path': image_path,
                    'caption': caption_text,
                    'alt_text': alt_text,
                    'placeholder': False
                }
            else:
                # Priority 3: Fallback: check filesystem for conventional optimized path
                try:
                    import os
                    candidate = f"/static/content/posts/{post_id}/sections/{section_dict['id']}/optimized/{section_dict['id']}.jpg"
                    filesystem_path = candidate.lstrip('/')
                    if os.path.exists(filesystem_path):
                        section_dict['image'] = {
                            'path': candidate,
                            'caption': caption_text,
                            'alt_text': alt_text,
                            'placeholder': False
                        }
                    else:
                        section_dict['image'] = None
                except Exception:
                    section_dict['image'] = None
            
            sections.append(section_dict)
        
        return sections

def find_header_image(post_id):
    """Find header image for a post."""
    import urllib.parse
    from config.paths import path_resolver
    
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')

    # Priority order: watermarked -> optimized -> raw
    image_types = ['watermarked', 'optimized', 'raw']
    
    for image_type in image_types:
        header_path = path_resolver.get_header_image_path(post_id, image_type)
        if os.path.exists(header_path):
            image_files = [f for f in os.listdir(header_path)
                          if f.lower().endswith(image_extensions) and not f.startswith('.')]
            if image_files:
                image_filename = image_files[0]
                # URL-encode the filename to handle spaces and special characters
                encoded_filename = urllib.parse.quote(image_filename)
                return f"/static/content/posts/{post_id}/header/{image_type}/{encoded_filename}"
    
    # Fallback to legacy structure
    legacy_path = f"/Users/autojenny/Documents/projects/blog/blog-images/static/images/posts/{post_id}/header.jpg"
    if os.path.exists(legacy_path):
        return legacy_path
    
    return None

@bp.route('/publishing')
def publishing():
    """Publishing management page."""
    return render_template('launchpad/publishing.html')

def publish_post_to_clan(post_id):
    """Publish a post to clan.com"""
    try:
        # Get post data
        post = get_post_with_development(post_id)
        if not post:
            return jsonify({'success': False, 'error': 'Post not found'}), 404
        
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
                
            # Add header image if exists (optional)
            header_image_path = find_header_image(post_id)
            if header_image_path:
                post['header_image'] = {
                    'path': header_image_path,
                    'alt_text': f"Header image for {post.get('title', 'this post')}",
                    'caption': header_data['header_image_caption'] if header_data else None,
                    'title': header_data['header_image_title'] if header_data else None,
                    'width': header_data['header_image_width'] if header_data else None,
                    'height': header_data['header_image_height'] if header_data else None
                }
                
            # Map cross-promotion regardless of header image
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

            # Auto-select random category/product IDs and default positions if missing
            try:
                cp = post['cross_promotion']
                to_persist = {}
                # Select a random category if none set
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
                # Select a random product if none set
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
                # Set default positions if missing
                if not cp.get('category_position'):
                    cp['category_position'] = 2
                    to_persist['cross_promotion_category_position'] = cp['category_position']
                if not cp.get('product_position'):
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

def clan_api_data(post_id):
    """View the actual API request data that was/will be sent to Clan.com."""
    try:
        # Get post data using our existing helper function
        post = get_post_with_development(post_id)
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
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

def clan_post_html(post_id):
    """View the clan_post HTML that will be uploaded to Clan.com."""
    try:
        # Get view type parameter (default to 'local')
        view_type = request.args.get('view', 'local')
        
        # Get post data using our existing helper function
        post = get_post_with_development(post_id)
        if not post:
            return "Post not found", 404
        
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
                # Fallback to raw template if preview HTML fails
                raw_html = render_template('launchpad/clan_post_raw.html', post=post, sections=sections)
                return raw_html, 200, {'Content-Type': 'text/plain; charset=utf-8'}
                
    except Exception as e:
        logger.error(f"Error in clan_post_html for post {post_id}: {e}")
        return f"Error: {str(e)}", 500

def validate_publish_data(post_id):
    """Validate publish data consistency and completeness."""
    try:
        # Get post and sections
        post = get_post_with_development(post_id)
        if not post:
            return jsonify({'error': 'Post not found', 'valid': False}), 404
        
        sections = get_post_sections_with_images(post_id)
        
        # Check for required data
        issues = []
        
        # Check required fields
        required_fields = ['title', 'meta_title', 'meta_description', 'meta_tags']
        for field in required_fields:
            if not post.get(field):
                issues.append({
                    'type': 'missing_field',
                    'field': field
                })
        
        # Check taxonomy fields (required for publishing)
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT theme_id, content_type_id, format_id
                FROM post
                WHERE id = %s
            """, (post_id,))
            taxonomy_check = cursor.fetchone()
            
            if not taxonomy_check or not taxonomy_check.get('theme_id'):
                issues.append({
                    'type': 'missing_taxonomy',
                    'field': 'theme_id',
                    'message': 'Post must have a theme assigned. Please assign taxonomy in Planning stage.'
                })
            if not taxonomy_check or not taxonomy_check.get('content_type_id'):
                issues.append({
                    'type': 'missing_taxonomy',
                    'field': 'content_type_id',
                    'message': 'Post must have a content type assigned. Please assign taxonomy in Planning stage.'
                })
            if not taxonomy_check or not taxonomy_check.get('format_id'):
                issues.append({
                    'type': 'missing_taxonomy',
                    'field': 'format_id',
                    'message': 'Post must have a format assigned. Please assign taxonomy in Planning stage.'
                })
        
        # Check meta_image points to optimized path
        meta_image = post.get('meta_image', '')
        if meta_image and '/raw/' in meta_image:
            issues.append({
                'type': 'raw_image_path',
                'field': 'meta_image',
                'path': meta_image
            })
        elif meta_image and '.png' in meta_image and '/optimized/' in meta_image:
            issues.append({
                'type': 'png_in_optimized',
                'field': 'meta_image',
                'path': meta_image
            })
        
        # Check for sections with content
        if not sections or len(sections) == 0:
            issues.append({
                'type': 'no_sections',
                'message': 'Post has no sections'
            })
        
        # Check images use optimized paths
        for section in sections:
            img = section.get('image')
            if img and img.get('path'):
                path = img['path']
                if '/raw/' in path or path.endswith('.png'):
                    issues.append({
                        'type': 'raw_section_image',
                        'section_id': section['id'],
                        'section_heading': section.get('section_heading'),
                        'path': path
                    })
        
        # Ensure cross-promotion data is attached (and auto-select if desired fields are missing)
        try:
            # Load existing cross-promo fields from DB
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT cross_promotion_category_id, cross_promotion_category_title,
                           cross_promotion_product_id, cross_promotion_product_title,
                           cross_promotion_category_position, cross_promotion_product_position,
                           cross_promotion_category_widget_html, cross_promotion_product_widget_html
                    FROM post WHERE id = %s
                """, (post_id,))
                cp = cursor.fetchone() or {}

                # Attach to post for validation context
                post['cross_promotion'] = {
                    'category_id': cp.get('cross_promotion_category_id'),
                    'category_title': cp.get('cross_promotion_category_title'),
                    'product_id': cp.get('cross_promotion_product_id'),
                    'product_title': cp.get('cross_promotion_product_title'),
                    'category_position': cp.get('cross_promotion_category_position'),
                    'product_position': cp.get('cross_promotion_product_position'),
                    'category_widget_html': cp.get('cross_promotion_category_widget_html'),
                    'product_widget_html': cp.get('cross_promotion_product_widget_html')
                }

                # If nothing configured, opportunistically auto-select to avoid blocking publish
                need_persist = False
                if not post['cross_promotion'].get('category_id'):
                    cursor.execute("SELECT id, name FROM clan_categories ORDER BY RANDOM() LIMIT 1")
                    cat = cursor.fetchone()
                    if cat:
                        post['cross_promotion']['category_id'] = cat['id']
                        post['cross_promotion']['category_title'] = cat.get('name') or 'Related Department'
                        post['cross_promotion']['category_position'] = post['cross_promotion']['category_position'] or 2
                        need_persist = True
                if not post['cross_promotion'].get('product_id'):
                    cursor.execute("SELECT id, name FROM clan_products ORDER BY RANDOM() LIMIT 1")
                    prod = cursor.fetchone()
                    if prod:
                        post['cross_promotion']['product_id'] = prod['id']
                        post['cross_promotion']['product_title'] = prod.get('name') or 'Related Products'
                        post['cross_promotion']['product_position'] = post['cross_promotion']['product_position'] or 4
                        need_persist = True
                if need_persist:
                    cursor.execute("""
                        UPDATE post SET
                            cross_promotion_category_id = %s,
                            cross_promotion_category_title = %s,
                            cross_promotion_product_id = %s,
                            cross_promotion_product_title = %s,
                            cross_promotion_category_position = COALESCE(cross_promotion_category_position, %s),
                            cross_promotion_product_position = COALESCE(cross_promotion_product_position, %s),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (
                        post['cross_promotion'].get('category_id'),
                        post['cross_promotion'].get('category_title'),
                        post['cross_promotion'].get('product_id'),
                        post['cross_promotion'].get('product_title'),
                        post['cross_promotion'].get('category_position') or 2,
                        post['cross_promotion'].get('product_position') or 4,
                        post_id
                    ))
                    cursor.connection.commit()

                # Ensure widget HTML exists for preview/publish consistency
                widget_changed = False
                if post['cross_promotion'].get('category_id') and post['cross_promotion'].get('category_position') and not post['cross_promotion'].get('category_widget_html'):
                    post['cross_promotion']['category_widget_html'] = f"{{{{widget type=\"swcatalog/widget_crossSell_category\" category_id=\"{post['cross_promotion'].get('category_id')}\" title=\"{post['cross_promotion'].get('category_title') or 'Related Department'}\"}}}}"
                    widget_changed = True
                if post['cross_promotion'].get('product_id') and post['cross_promotion'].get('product_position') and not post['cross_promotion'].get('product_widget_html'):
                    post['cross_promotion']['product_widget_html'] = f"{{{{widget type=\"swcatalog/widget_crossSell_product\" product_id=\"{post['cross_promotion'].get('product_id')}\" title=\"{post['cross_promotion'].get('product_title') or 'Related Products'}\"}}}}"
                    widget_changed = True
                if widget_changed:
                    with db_manager.get_cursor() as c2:
                        c2.execute("""
                            UPDATE post SET
                                cross_promotion_category_widget_html = %s,
                                cross_promotion_product_widget_html = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (
                            post['cross_promotion'].get('category_widget_html'),
                            post['cross_promotion'].get('product_widget_html'),
                            post_id
                        ))
                        c2.connection.commit()
        except Exception as e:
            logger.warning(f"Validation cross-promotion attach/auto-select error: {e}")

        # After attachment/generation, only warn if DB claims configured but we truly have no usable data
        cp = post.get('cross_promotion') or {}
        if (
            (post.get('cross_promotion_category_id') or post.get('cross_promotion_product_id'))
            and not (cp.get('category_widget_html') or cp.get('product_widget_html'))
        ):
            issues.append({
                'type': 'cross_promotion_missing',
                'message': 'Cross-promotion configured but no widget HTML available'
            })
        
        valid = len(issues) == 0
        
        return jsonify({
            'valid': valid,
            'issues': issues,
            'section_count': len(sections),
            'has_all_meta_fields': all(post.get(f) for f in required_fields),
            'meta_image_is_optimized': meta_image and '/optimized/' in meta_image and meta_image.endswith('.jpg'),
            'message': 'Ready to publish' if valid else f'Found {len(issues)} issues that need attention'
        })
        
    except Exception as e:
        logger.error(f"Error validating publish data for post {post_id}: {e}")
        return jsonify({'error': str(e), 'valid': False}), 500
