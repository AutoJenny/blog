# blueprints/launchpad/blog_post_syndication.py
"""Blog post Facebook syndication functionality - extracted from launchpad_old.py"""

from flask import Blueprint, jsonify, request
import logging
import requests
from config.database import db_manager

bp = Blueprint('blog_post_syndication', __name__)
logger = logging.getLogger(__name__)


def refresh_facebook_cache(url):
    """Refresh Facebook's cache for a given URL using the Sharing Debugger API."""
    try:
        # Use Facebook's Sharing Debugger API to refresh cache
        debug_url = "https://graph.facebook.com/v18.0/"
        params = {
            'id': url,
            'scrape': 'true',
            'access_token': 'YOUR_APP_ACCESS_TOKEN'  # This would need to be configured
        }
        
        logger.info(f"Refreshing Facebook cache for: {url}")
        # Note: This requires an app access token, which we don't currently have configured
        # For now, we'll just log the attempt
        logger.info("Facebook cache refresh attempted (requires app access token)")
        return True
        
    except Exception as e:
        logger.error(f"Error refreshing Facebook cache: {e}")
        return False


def post_to_facebook_unified(page_id, access_token, message, link_url, page_name=""):
    """
    Unified Facebook posting function - always uses /feed endpoint with link.
    
    ⚠️ DISABLED - Facebook posting has been disabled to prevent unwanted posts.
    """
    logger.error(f"BLOCKED: post_to_facebook_unified called for page={page_name} (ID: {page_id}) - Facebook posting is DISABLED")
    return {'success': False, 'error': 'Facebook posting has been disabled'}
    logger.info(f"Posting to {page_name} (Page ID: {page_id})")
    logger.info(f"Post content: {message[:100]}...")
    logger.info(f"Link URL: {link_url}")
    logger.info(f"Access token being used: {access_token[:20]}...")
    
    # Try to refresh Facebook's cache for the link URL
    refresh_facebook_cache(link_url)
    
    # Always use /feed endpoint for link sharing
    feed_url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
    
    feed_payload = {
        'message': message,
        'link': link_url,
        'access_token': access_token
    }
    
    logger.info(f"Facebook API call - URL: {feed_url}")
    response = requests.post(feed_url, data=feed_payload, timeout=30)
    logger.info(f"Facebook API response - Status: {response.status_code}")
    logger.info(f"Facebook API response - Content: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        return {
            'success': True,
            'post_id': result.get('id'),
            'response': result
        }
    else:
        error_data = response.json() if response.content else {}
        error_msg = error_data.get('error', {}).get('message', 'Unknown Facebook API error')
        return {
            'success': False,
            'error': f'Facebook API error: {response.status_code}',
            'details': error_msg
        }


def prepare_blog_post_data(queue_item):
    """Prepare blog post data for Facebook posting using new publication system."""
    generated_content = queue_item['generated_content']
    image_url = queue_item.get('product_image')  # Can be used for header image if available
    
    # Get the blog post URL from the new publication system
    link_url = None
    
    # Try to get working URL from database first (if post_id is available)
    if queue_item.get('post_id'):
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT clan_uploaded_url, title 
                FROM post 
                WHERE id = %s
            """, (queue_item['post_id'],))
            result = cursor.fetchone()
            if result and result['clan_uploaded_url']:
                link_url = result['clan_uploaded_url']
            elif result and result['title']:
                # Fallback: construct URL from title/slug if no uploaded URL
                logger.warning(f"Post {queue_item['post_id']} has no clan_uploaded_url, may need to construct URL")
    
    # If no post_id or no URL found, extract URL from generated content as fallback
    if not link_url:
        import re
        # Look for clan.com/blog URLs in the generated content
        url_pattern = r'https://clan\.com/blog/[^\s]+'
        urls = re.findall(url_pattern, generated_content)
        
        if urls:
            link_url = urls[0]  # Take the first URL found
            logger.info(f"Extracted URL from content: {link_url}")
    
    if not link_url:
        logger.error(f"No link URL found for queue item {queue_item.get('id')}")
        # Return a fallback URL - this should not happen in production
        link_url = f"https://clan.com/blog"
    
    return {
        'message': generated_content,
        'image_url': image_url,
        'link_url': link_url,
        'content_type': 'blog_post'
    }


def execute_facebook_post(queue_item_id):
    """
    Shared function to post a queue item to Facebook (both pages).
    Used by both manual posting and automated posting systems.
    Returns: {'success': bool, 'message': str, 'platform_post_ids': list}
    
    ⚠️ DISABLED - Facebook posting has been disabled to prevent unwanted posts.
    """
    logger.error(f"BLOCKED: execute_facebook_post called for queue_item_id={queue_item_id} - Facebook posting is DISABLED")
    return {'success': False, 'message': 'Facebook posting has been disabled', 'platform_post_ids': []}
    try:
        with db_manager.get_cursor() as cursor:
            # Get the queue item details - handle both product and blog post
            cursor.execute("""
                SELECT pq.*, 
                       cp.name as product_name,
                       p.title as post_title,
                       p.clan_uploaded_url
                FROM posting_queue pq
                LEFT JOIN clan_products cp ON pq.product_id = cp.id
                LEFT JOIN post p ON pq.post_id = p.id
                WHERE pq.id = %s
            """, (queue_item_id,))
            
            queue_item = cursor.fetchone()
            if not queue_item:
                return {'success': False, 'message': 'Queue item not found'}
            
            # Prepare data based on content type
            content_type = queue_item['content_type']
            if content_type == 'blog_post':
                post_data = prepare_blog_post_data(queue_item)
            elif content_type == 'product':
                # Import product function from launchpad_old or create it here
                from blueprints.launchpad_old import prepare_product_post_data
                post_data = prepare_product_post_data(queue_item)
            else:
                return {'success': False, 'message': f'Unsupported content type: {content_type}'}
            
            # Get Facebook credentials for both pages
            cursor.execute("""
                SELECT credential_key, credential_value
                FROM platform_credentials 
                WHERE platform_id = (SELECT id FROM platforms WHERE name = 'facebook')
                AND is_active = true
            """)
            credentials = cursor.fetchall()
            
            # Convert to dictionary
            creds = {}
            for cred in credentials:
                creds[cred['credential_key']] = cred['credential_value']
            
            # Define both pages to post to
            pages_to_post = []
            
            # Page 1 (Scotweb CLAN)
            if creds.get('page_access_token') and creds.get('page_id'):
                pages_to_post.append({
                    'page_id': creds['page_id'],
                    'access_token': creds['page_access_token'],
                    'name': 'Scotweb CLAN'
                })
            
            # Page 2 (CLAN by Scotweb) - only add if different from Page 1
            if (creds.get('page_access_token_2') and creds.get('page_id_2') and 
                creds.get('page_id_2') != creds.get('page_id')):
                pages_to_post.append({
                    'page_id': creds['page_id_2'],
                    'access_token': creds['page_access_token_2'],
                    'name': 'CLAN by Scotweb'
                })
            elif creds.get('page_id_2') == creds.get('page_id'):
                logger.warning("Both Facebook pages have the same page_id - skipping duplicate posting to prevent double posts")
            
            if not pages_to_post:
                return {'success': False, 'message': 'No Facebook pages configured'}
            
            # Post to both pages using unified function
            results = []
            successful_posts = []
            failed_posts = []
            
            for page in pages_to_post:
                result = post_to_facebook_unified(
                    page['page_id'], 
                    page['access_token'], 
                    post_data['message'],
                    post_data['link_url'],
                    page['name']
                )
                results.append({
                    'page_name': page['name'],
                    'page_id': page['page_id'],
                    'result': result
                })
                
                if result['success']:
                    successful_posts.append(result['post_id'])
                else:
                    failed_posts.append(f"{page['name']}: {result['error']}")
            
            # Update queue item status
            if successful_posts:
                cursor.execute("""
                    UPDATE posting_queue 
                    SET status = 'published', 
                        platform_post_id = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (successful_posts[0], queue_item_id))  # Store first post ID as primary
                
                conn = cursor.connection
                conn.commit()
                
                if len(failed_posts) == 0:
                    return {
                        'success': True, 
                        'message': f'Successfully posted to {len(successful_posts)} page(s)',
                        'platform_post_ids': successful_posts
                    }
                else:
                    return {
                        'success': True, 
                        'message': f'Posted to {len(successful_posts)} page(s), failed on {len(failed_posts)}: {", ".join(failed_posts)}',
                        'platform_post_ids': successful_posts
                    }
            else:
                # All posts failed
                cursor.execute("""
                    UPDATE posting_queue 
                    SET status = 'failed', 
                        error_message = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (", ".join(failed_posts), queue_item_id))
                
                conn = cursor.connection
                conn.commit()
                
                return {
                    'success': False, 
                    'message': f'Failed to post to all pages: {", ".join(failed_posts)}'
                }
                
    except Exception as e:
        logger.error(f"Error in execute_facebook_post: {e}", exc_info=True)
        return {'success': False, 'message': str(e)}


# API Routes for Blog Post Syndication

@bp.route('/api/syndication/posts')
def get_published_posts():
    """Get list of published posts for syndication."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, title, subtitle, summary, slug, 
                       clan_post_id, clan_uploaded_url,
                       created_at, updated_at, status
                FROM post
                WHERE status = 'published' 
                  AND clan_uploaded_url IS NOT NULL
                ORDER BY updated_at DESC, created_at DESC
            """)
            posts = cursor.fetchall()
            
            posts_list = []
            for post in posts:
                posts_list.append({
                    'id': post['id'],
                    'title': post['title'],
                    'subtitle': post.get('subtitle'),
                    'summary': post.get('summary'),
                    'slug': post.get('slug'),
                    'clan_post_id': post.get('clan_post_id'),
                    'clan_uploaded_url': post['clan_uploaded_url'],
                    'created_at': post['created_at'].isoformat() if post['created_at'] else None,
                    'updated_at': post['updated_at'].isoformat() if post['updated_at'] else None,
                    'status': post['status']
                })
            
            return jsonify({
                'success': True,
                'posts': posts_list
            })
    except Exception as e:
        logger.error(f"Error getting published posts: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/syndication/posts/<int:post_id>')
def get_post_details(post_id):
    """Get details for a specific post."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, title, subtitle, summary, slug,
                       clan_post_id, clan_uploaded_url,
                       created_at, updated_at, status,
                       header_image_id
                FROM post
                WHERE id = %s AND status = 'published'
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return jsonify({
                    'success': False,
                    'error': 'Post not found or not published'
                }), 404
            
            # Get header image if available
            header_image = None
            if post['header_image_id']:
                cursor.execute("""
                    SELECT file_path as path, alt_text, caption
                    FROM images
                    WHERE id = %s
                """, (post['header_image_id'],))
                img_result = cursor.fetchone()
                if img_result and img_result['path']:
                    header_image = {
                        'path': img_result['path'],
                        'alt_text': img_result.get('alt_text'),
                        'caption': img_result.get('caption')
                    }
            
            return jsonify({
                'success': True,
                'post': {
                    'id': post['id'],
                    'title': post['title'],
                    'subtitle': post.get('subtitle'),
                    'summary': post.get('summary'),
                    'slug': post.get('slug'),
                    'clan_post_id': post.get('clan_post_id'),
                    'clan_uploaded_url': post['clan_uploaded_url'],
                    'created_at': post['created_at'].isoformat() if post['created_at'] else None,
                    'updated_at': post['updated_at'].isoformat() if post['updated_at'] else None,
                    'status': post['status'],
                    'header_image': header_image
                }
            })
    except Exception as e:
        logger.error(f"Error getting post details: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/syndication/generate-blog-content', methods=['POST'])
def generate_blog_content():
    """Generate social media content for a blog post using LLM."""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        content_type = data.get('content_type', 'blog_post')
        
        if not post_id:
            return jsonify({
                'success': False,
                'error': 'Post ID is required'
            }), 400
        
        # Get post details
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, title, subtitle, summary, clan_uploaded_url
                FROM post
                WHERE id = %s AND status = 'published'
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return jsonify({
                    'success': False,
                    'error': 'Post not found or not published'
                }), 404
            
            # Get LLM prompt template for social media syndication
            cursor.execute("""
                SELECT prompt_text
                FROM llm_prompt
                WHERE name = 'Social Media Syndication'
                LIMIT 1
            """)
            prompt_config = cursor.fetchone()
            
            if not prompt_config:
                return jsonify({
                    'success': False,
                    'error': 'No LLM prompt configuration found'
                }), 404
            
            # Format the prompt with platform info and blog post details
            prompt_template = prompt_config['prompt_text']
            
            blog_url = post['clan_uploaded_url'] or f"https://clan.com/blog/{post.get('slug', '')}"
            
            formatted_prompt = prompt_template.format(
                platform='Facebook',
                channel_type='blog_post',
                requirements=f"""Create an engaging blog post promotion for Facebook:
Blog Post Title: {post['title']}
Subtitle: {post.get('subtitle', '')}
Summary: {post.get('summary', '')}
Blog Post URL: {blog_url}

Write a compelling social media post that highlights the key points of this blog article. Use an engaging tone with appropriate emojis. Include a clear call-to-action directing people to read the full article. Keep it concise but informative, capturing the essence of the blog post."""
            )
            
            # Call LLM service
            from blueprints.llm_actions import LLMService
            llm_service = LLMService()
            
            # Prepare messages for the LLM
            messages = [
                {"role": "system", "content": "You are a social media marketing expert specializing in blog content promotion."},
                {"role": "user", "content": formatted_prompt}
            ]
            
            response = llm_service.execute_llm_request(
                provider='ollama',
                model='mistral',
                messages=messages
            )
            
            if response and 'content' in response:
                generated_content = response['content']
                
                # Check if content already exists for this post and content_type
                cursor.execute("""
                    SELECT id FROM posting_queue
                    WHERE post_id = %s AND content_type = %s
                    LIMIT 1
                """, (post_id, content_type))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing content
                    cursor.execute("""
                        UPDATE posting_queue
                        SET generated_content = %s, post_title = %s, updated_at = NOW()
                        WHERE post_id = %s AND content_type = %s
                        RETURNING id
                    """, (generated_content, post['title'], post_id, content_type))
                    result = cursor.fetchone()
                    queue_item_id = result['id'] if result else None
                else:
                    # Insert new content
                    cursor.execute("""
                        INSERT INTO posting_queue (
                            post_id, content_type, generated_content, 
                            post_title, status, platform, channel_type,
                            created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, 'draft', 'facebook', 'feed_post', NOW(), NOW())
                        RETURNING id
                    """, (post_id, content_type, generated_content, post['title']))
                    result = cursor.fetchone()
                    queue_item_id = result['id'] if result else None
                
                conn = cursor.connection
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'content': generated_content,
                    'post': {
                        'id': post['id'],
                        'title': post['title'],
                        'clan_uploaded_url': post['clan_uploaded_url']
                    },
                    'queue_item_id': queue_item_id
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to generate content'
                }), 500
                
    except Exception as e:
        logger.error(f"Error generating blog content: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/syndication/save-blog-content', methods=['POST'])
def save_blog_content():
    """Save generated content for a blog post to the posting queue."""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        content_type = data.get('content_type', 'blog_post')
        generated_content = data.get('content') or data.get('generated_content')
        
        if not post_id or not generated_content:
            return jsonify({
                'success': False,
                'error': 'Post ID and generated content are required'
            }), 400
        
        with db_manager.get_connection() as conn:
            cur = conn.cursor()
            
            # Get post title
            cur.execute("SELECT title FROM post WHERE id = %s", (post_id,))
            post_result = cur.fetchone()
            post_title = post_result['title'] if post_result else None
            
            # Check if content already exists for this post and content_type
            cur.execute("""
                SELECT id FROM posting_queue
                WHERE post_id = %s AND content_type = %s
            """, (post_id, content_type))
            existing = cur.fetchone()
            
            if existing:
                # Update existing content
                cur.execute("""
                    UPDATE posting_queue
                    SET generated_content = %s, post_title = %s, updated_at = NOW()
                    WHERE post_id = %s AND content_type = %s
                """, (generated_content, post_title, post_id, content_type))
            else:
                # Insert new content
                cur.execute("""
                    INSERT INTO posting_queue (
                        post_id, content_type, generated_content, post_title,
                        status, platform, channel_type, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, 'draft', 'facebook', 'feed_post', NOW(), NOW())
                """, (post_id, content_type, generated_content, post_title))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Generated content saved successfully'
            })
    except Exception as e:
        logger.error(f"Error saving blog content: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/syndication/get-blog-content/<int:post_id>')
def get_blog_content(post_id):
    """Get generated content for a blog post."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT generated_content, created_at, updated_at, status, id
                FROM posting_queue 
                WHERE post_id = %s AND content_type = 'blog_post'
                ORDER BY updated_at DESC
                LIMIT 1
            """, (post_id,))
            
            result = cursor.fetchone()
            
            if result:
                return jsonify({
                    'success': True,
                    'content': result['generated_content'],
                    'queue_item_id': result['id'],
                    'status': result['status'],
                    'created_at': result['created_at'].isoformat() if result['created_at'] else None,
                    'updated_at': result['updated_at'].isoformat() if result['updated_at'] else None
                })
            else:
                return jsonify({
                    'success': True,
                    'content': None
                })
                
    except Exception as e:
        logger.error(f"Error getting blog content: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/syndication/post-now', methods=['POST'])
def post_now():
    """Post blog post content to Facebook immediately."""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        
        if not item_id:
            return jsonify({
                'success': False,
                'error': 'Item ID is required'
            }), 400
        
        # Use the shared execute_facebook_post function
        result = execute_facebook_post(item_id)
        
        if result['success']:
            return jsonify({
                'success': True, 
                'message': result['message'],
                'platform_post_ids': result.get('platform_post_ids', [])
            })
        else:
            return jsonify({'success': False, 'error': result['message']})
            
    except Exception as e:
        logger.error(f"Error in post_now: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# Export execute_facebook_post for use by other modules (like automated posting)
__all__ = ['execute_facebook_post', 'prepare_blog_post_data', 'post_to_facebook_unified']

