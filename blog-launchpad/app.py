from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for
import requests
import os
import logging
import json
from datetime import datetime
import pytz
from humanize import naturaltime
import psycopg.rows

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_ollama_running():
    """Check if Ollama is running and start it if needed."""
    try:
        # Check if Ollama is already running
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            logger.info("Ollama is already running")
            return True
    except requests.exceptions.ConnectionError:
        logger.info("Ollama is not running, attempting to start it...")
    except Exception as e:
        logger.warning(f"Error checking Ollama status: {e}")
    
    try:
        # Try to start Ollama
        import subprocess
        import time
        
        logger.info("Starting Ollama service...")
        # Start Ollama in the background
        subprocess.Popen(['ollama', 'serve'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        
        # Wait for Ollama to start up
        for attempt in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            try:
                response = requests.get('http://localhost:11434/api/tags', timeout=2)
                if response.status_code == 200:
                    logger.info("Ollama started successfully")
                    return True
            except requests.exceptions.ConnectionError:
                continue
        
        logger.error("Failed to start Ollama after 30 seconds")
        return False
        
    except FileNotFoundError:
        logger.error("Ollama not found in PATH. Please install Ollama first.")
        return False
    except Exception as e:
        logger.error(f"Error starting Ollama: {e}")
        return False

app = Flask(__name__, template_folder="templates", static_folder="static")

# Custom Jinja2 filter to strip HTML document structure
@app.template_filter('strip_html_doc')
def strip_html_doc(content):
    """Strip HTML document structure and return only body content."""
    if not content:
        return content
    
    import re
    
    # Remove DOCTYPE declaration
    content = re.sub(r'<!DOCTYPE[^>]*>', '', content, flags=re.IGNORECASE)
    
    # Remove html, head, and body tags, keeping only the content inside body
    content = re.sub(r'<html[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</html[^>]*>', '', content, flags=re.IGNORECASE)  # Handle both </html> and </html
    content = re.sub(r'<head[^>]*>.*?</head>', '', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<body[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</body[^>]*>', '', content, flags=re.IGNORECASE)  # Handle both </body> and </body
    
    # Remove any remaining malformed HTML closing tags
    content = re.sub(r'</html[^>]*', '', content, flags=re.IGNORECASE)  # Remove </html without >
    content = re.sub(r'</body[^>]*', '', content, flags=re.IGNORECASE)  # Remove </body without >
    
    # Clean up any remaining whitespace and newlines
    content = re.sub(r'\s+', ' ', content)
    content = re.sub(r'>\s+<', '><', content)
    
    return content.strip()

# Add route to serve blog-images static files
@app.route('/static/content/posts/<int:post_id>/sections/<int:section_id>/<directory>/<filename>')
def serve_section_image(post_id, section_id, directory, filename):
    """Serve section images from the blog-images directory."""
    import os
    blog_images_static = "/Users/nickfiddes/Code/projects/blog/blog-images/static"
    image_path = os.path.join(blog_images_static, "content", "posts", str(post_id), "sections", str(section_id), directory, filename)
    
    if os.path.exists(image_path):
        return send_file(image_path)
    else:
        return "Image not found", 404

@app.route('/static/content/posts/<int:post_id>/header/<directory>/<filename>')
def serve_header_image(post_id, directory, filename):
    """Serve header images from the blog-images directory."""
    import os
    blog_images_static = "/Users/nickfiddes/Code/projects/blog/blog-images/static"
    image_path = os.path.join(blog_images_static, "content", "posts", str(post_id), "header", directory, filename)
    
    if os.path.exists(image_path):
        return send_file(image_path)
    else:
        return "Image not found", 404

# Database connection function (shared with blog-core)
def get_db_connection():
    """Get database connection."""
    import psycopg
    return psycopg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        dbname=os.getenv('DB_NAME', 'blog'),
        user=os.getenv('DB_USER', 'autojenny'),
        password=os.getenv('DB_PASSWORD', '')
    )

def get_category_hierarchy(category_ids):
    """Convert category IDs to breadcrumb-style hierarchy with product categories first."""
    # Temporarily disabled to fix tuple index error
    return []

@app.route('/')
def index():
    """Main launchpad page."""
    return render_template('index.html')

@app.route('/cross-promotion')
def cross_promotion():
    """Cross-promotion management page."""
    with get_db_connection() as conn:
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        cur.execute("""
            SELECT p.id, p.title, p.subtitle, p.created_at, p.updated_at, p.status, p.slug,
                   pd.idea_seed, pd.intro_blurb, pd.main_title,
                   p.cross_promotion_category_id, p.cross_promotion_category_title,
                   p.cross_promotion_product_id, p.cross_promotion_product_title,
                   p.cross_promotion_category_position, p.cross_promotion_product_position,
                   p.cross_promotion_category_widget_html, p.cross_promotion_product_widget_html
            FROM post p
            LEFT JOIN post_development pd ON pd.post_id = p.id
            WHERE p.status != 'deleted'
            ORDER BY p.updated_at DESC NULLS LAST, p.created_at DESC
        """)
        posts = [dict(row) for row in cur.fetchall()]
        
        for post in posts:
            post['cross_promotion'] = {
                'category_id': post.get('cross_promotion_category_id'),
                'category_title': post.get('cross_promotion_category_title'),
                'product_id': post.get('cross_promotion_product_id'),
                'product_title': post.get('cross_promotion_product_title'),
                'category_position': post.get('cross_promotion_category_position'),
                'product_position': post.get('cross_promotion_product_position'),
                'category_widget_html': post.get('cross_promotion_category_widget_html'),
                'product_widget_html': post.get('cross_promotion_product_widget_html')
            }
            sections = get_post_sections_with_images(post['id'])
            post['sections'] = sections
    
    default_post = posts[0] if posts else None
    return render_template('cross_promotion.html', posts=posts, default_post=default_post)

@app.route('/publishing')
def publishing():
    """Publishing management page."""
    return render_template('publishing.html')

# Daily Product Posts Routes
@app.route('/social-media-command-center')
def social_media_command_center():
    """Main Social Media Command Center dashboard."""
    return render_template('social_media_command_center.html')

@app.route('/api/social-media/timeline')
def get_unified_timeline():
    """Get unified timeline data from all posting queues."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Get all posts from posting_queue with platform/channel info
            cur.execute("""
                SELECT pq.id, pq.platform, pq.channel_type, pq.content_type,
                       pq.scheduled_timestamp, pq.generated_content, pq.status,
                       pq.platform_post_id, pq.error_message,
                       cp.name as product_name, cp.sku, cp.image_url as product_image,
                       cp.price, pq.created_at, pq.updated_at
                FROM posting_queue pq
                LEFT JOIN clan_products cp ON pq.product_id = cp.id
                WHERE pq.status IN ('pending', 'ready', 'published', 'failed')
                ORDER BY pq.scheduled_timestamp ASC, pq.created_at ASC
                LIMIT 50
            """)
            
            items = cur.fetchall()
            
            timeline_items = []
            for item in items:
                # Use scheduled_timestamp if available, otherwise fall back to created_at
                scheduled_time = item[4] if item[4] else item[13]  # scheduled_timestamp or created_at
                
                # Validate required fields - no fallbacks allowed
                if not item[1]:  # platform
                    raise ValueError(f"Post {item[0]} is missing platform information")
                if not item[2]:  # channel_type
                    raise ValueError(f"Post {item[0]} is missing channel_type information")
                if not item[3]:  # content_type
                    raise ValueError(f"Post {item[0]} is missing content_type information")
                if not item[5]:  # content
                    raise ValueError(f"Post {item[0]} is missing generated content")
                if not item[6]:  # status
                    raise ValueError(f"Post {item[0]} is missing status information")
                
                timeline_items.append({
                    'id': item[0],
                    'platform': item[1],
                    'channel_type': item[2],
                    'content_type': item[3],
                    'scheduled_timestamp': scheduled_time.isoformat() if scheduled_time else None,
                    'content': item[5],
                    'status': item[6],
                    'platform_post_id': item[7],
                    'error_message': item[8],
                    'product_name': item[9],
                    'sku': item[10],
                    'product_image': item[11],
                    'price': str(item[12]) if item[12] else None,
                    'created_at': item[13].isoformat() if item[13] else None,
                    'updated_at': item[14].isoformat() if item[14] else None
                })
            
            return jsonify({
                'success': True,
                'timeline': timeline_items,
                'count': len(timeline_items)
            })
        
    except Exception as e:
        logger.error(f"Error getting unified timeline: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get timeline: {str(e)}'
        }), 500

@app.route('/daily-product-posts')
def daily_product_posts():
    """Daily Product Posts management page."""
    return render_template('daily_product_posts.html')

@app.route('/daily-product-posts/select')
def daily_product_posts_select():
    """Redirect to main daily product posts page."""
    return redirect('/daily-product-posts')

# Daily Product Posts API Endpoints
@app.route('/api/daily-product-posts/test-categories', methods=['GET'])
def test_categories():
    """Test category query to debug DictCursor issue."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            cur.execute("""
                SELECT id, name FROM clan_categories 
                WHERE parent_id = 267
                ORDER BY RANDOM()
                LIMIT 1
            """)
            category = cur.fetchone()
            
            if category:
                return jsonify({
                    'success': True,
                    'category': dict(category),
                    'type': str(type(category))
                })
            else:
                return jsonify({'success': False, 'error': 'No categories found'})
                
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/daily-product-posts/test-simple', methods=['GET'])
def test_simple():
    """Test simple product selection without category filtering."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            cur.execute("""
                SELECT id, name, sku, price, description, image_url, url, category_ids
                FROM clan_products 
                WHERE price IS NOT NULL AND price != ''
                ORDER BY RANDOM() 
                LIMIT 1
            """)
            product = cur.fetchone()
            
            if product:
                return jsonify({
                    'success': True,
                    'product': dict(product)
                })
            else:
                return jsonify({'success': False, 'error': 'No products found'})
                
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/daily-product-posts/select-product', methods=['POST'])
def select_random_product():
    """Select a random product from Clan.com catalogue using category-first approach."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # First, get all products and filter by category (simple approach)
            cur.execute("""
                SELECT id, name, sku, price, description, image_url, url, category_ids
                FROM clan_products 
                WHERE price IS NOT NULL AND price != ''
                ORDER BY RANDOM() 
                LIMIT 100
            """)
            all_products = cur.fetchall()
            
            if not all_products:
                return jsonify({'success': False, 'error': 'No products available'})
            
            # Top-level category IDs and names
            category_ids = [20, 328, 18, 37, 19, 21, 100, 16]
            category_names = {
                20: 'Children', 328: 'Clearance', 18: 'Gifts', 37: 'Homeware',
                19: 'Jewellery', 21: 'Kilts & Highlandwear', 100: 'Men', 16: 'Women'
            }
            
            # Randomly select one category
            import random
            selected_category_id = random.choice(category_ids)
            
            # Filter products by selected category
            matching_products = []
            for product in all_products:
                if product['category_ids'] and selected_category_id in product['category_ids']:
                    matching_products.append(product)
            
            # If no products found in this category, try other categories
            if not matching_products:
                for cat_id in category_ids:
                    if cat_id != selected_category_id:
                        for product in all_products:
                            if product['category_ids'] and cat_id in product['category_ids']:
                                matching_products.append(product)
                                selected_category_id = cat_id
                                break
                        if matching_products:
                            break
            
            # If still no matches, just pick any product
            if not matching_products:
                selected_product = random.choice(all_products)
                selected_category_id = None
            else:
                selected_product = random.choice(matching_products)
            
            # Simple product data conversion
            product_dict = dict(selected_product)
            product_dict['category_hierarchy'] = []
            
            # Response with selected category info
            response_data = {
                'success': True, 
                'product': product_dict
            }
            
            if selected_category_id:
                response_data['selected_category'] = {
                    'id': selected_category_id,
                    'name': category_names.get(selected_category_id, 'Unknown')
                }
            
            return jsonify(response_data)
            
    except Exception as e:
        import traceback
        logger.error(f"Error selecting random product: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/daily-product-posts/generate-content', methods=['POST'])
def generate_product_content():
    """Generate AI content for selected product."""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        content_type = data.get('content_type', 'feature')
        
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # Get product details
            cur.execute("SELECT * FROM clan_products WHERE id = %s", (product_id,))
            product = cur.fetchone()
            
            if not product:
                return jsonify({'success': False, 'error': 'Product not found'})
            
            # Get content template
            cur.execute("""
                SELECT template_prompt FROM product_content_templates 
                WHERE content_type = %s AND is_active = true
            """, (content_type,))
            template = cur.fetchone()
            
            if not template:
                return jsonify({'success': False, 'error': 'Content template not found'})
            
            # Prepare prompt with URL for call to action
            if not product['description']:
                raise ValueError(f"Product {product['name']} has no description")
            
            prompt = template['template_prompt'].format(
                product_name=product['name'],
                product_description=product['description'],
                product_url=product['url']
            )
            
            # Call LLM
            llm_request = {
                'provider': 'ollama',
                'model': 'mistral',
                'prompt': prompt,
                'temperature': 0.8,
                'max_tokens': 200
            }
            
            response = requests.post('http://localhost:11434/api/generate', 
                                   json=llm_request, timeout=30)
            
            if response.status_code == 200:
                # Parse streaming response
                response_lines = response.text.strip().split('\n')
                generated_text = ""
                
                for line in response_lines:
                    if line.strip():
                        try:
                            line_data = json.loads(line)
                            if 'response' in line_data:
                                generated_text += line_data['response']
                        except json.JSONDecodeError:
                            continue
                
                # Save to database
                today = datetime.now().date()
                cur.execute("""
                    INSERT INTO daily_posts (product_id, post_date, content_text, content_type, status)
                    VALUES (%s, %s, %s, %s, 'draft')
                """, (product_id, today, generated_text, content_type))
                conn.commit()
                
                return jsonify({
                    'success': True, 
                    'content': generated_text
                })
            else:
                return jsonify({'success': False, 'error': 'LLM service unavailable'})
                
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        return jsonify({'success': False, 'error': str(e)})

def post_to_facebook_page(page_id, access_token, post_content, product_image, page_name=""):
    """Helper function to post to a single Facebook page."""
    import requests
    
    photos_url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
    photos_payload = {
        'url': product_image,
        'caption': post_content,
        'published': True,
        'access_token': access_token
    }
    
    print(f"DEBUG: Posting to {page_name} (Page ID: {page_id})")
    print(f"DEBUG: Facebook API call - URL: {photos_url}")
    print(f"DEBUG: Product image URL: {product_image}")
    print(f"DEBUG: Access token being used: {access_token[:20]}...")
    
    response = requests.post(photos_url, data=photos_payload, timeout=30)
    print(f"DEBUG: Facebook API response - Status: {response.status_code}")
    print(f"DEBUG: Facebook API response - Content: {response.text}")
    
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

@app.route('/api/daily-product-posts/post-now', methods=['POST'])
def post_to_facebook():
    """Post content to Facebook with product image - posts to both pages."""
    try:
        data = request.get_json()
        
        # Handle both old format (from daily-product-posts page) and new format (from timeline)
        item_id = data.get('item_id')
        product_id = data.get('product_id')
        content = data.get('content')
        content_type = data.get('content_type')
        platform = data.get('platform', 'facebook')
        
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            if item_id:
                # New format: posting from timeline
                # Get the queue item details
                cur.execute("""
                    SELECT pq.*, cp.name as product_name, cp.image_url as product_image
                    FROM posting_queue pq
                    LEFT JOIN clan_products cp ON pq.product_id = cp.id
                    WHERE pq.id = %s
                """, (item_id,))
                
                queue_item = cur.fetchone()
                if not queue_item:
                    return jsonify({'success': False, 'error': 'Queue item not found'})
                
                # Get Facebook credentials for both pages
                cur.execute("""
                    SELECT credential_key, credential_value
                    FROM platform_credentials 
                    WHERE platform_id = (SELECT id FROM platforms WHERE name = 'facebook')
                    AND is_active = true
                """)
                credentials = cur.fetchall()
                
                # Convert to dictionary
                creds = {}
                for cred in credentials:
                    creds[cred['credential_key']] = cred['credential_value']
                
                # Prepare post content
                post_content = queue_item['generated_content']
                product_image = queue_item['product_image']
                
                # Define both pages to post to
                pages_to_post = []
                
                # Page 1 (CLAN by Scotweb)
                if creds.get('page_access_token') and creds.get('page_id'):
                    pages_to_post.append({
                        'page_id': creds['page_id'],
                        'access_token': creds['page_access_token'],
                        'name': 'CLAN by Scotweb'
                    })
                
                # Page 2 (Scotweb CLAN)
                if creds.get('page_access_token_2') and creds.get('page_id_2'):
                    pages_to_post.append({
                        'page_id': creds['page_id_2'],
                        'access_token': creds['page_access_token_2'],
                        'name': 'Scotweb CLAN'
                    })
                
                if not pages_to_post:
                    return jsonify({'success': False, 'error': 'No Facebook pages configured'})
                
                # Post to both pages
                results = []
                successful_posts = []
                failed_posts = []
                
                for page in pages_to_post:
                    result = post_to_facebook_page(
                        page['page_id'], 
                        page['access_token'], 
                        post_content, 
                        product_image, 
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
                
                # Update database based on results
                if successful_posts:
                    # Use the first successful post ID for the database
                    primary_post_id = successful_posts[0]
                    
                    # Update the queue item status
                    cur.execute("""
                        UPDATE posting_queue 
                        SET status = 'published', platform_post_id = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (primary_post_id, item_id))
                    
                    # Also update daily_posts if it exists
                    cur.execute("""
                        UPDATE daily_posts 
                        SET status = 'posted', posted_at = NOW()
                        WHERE product_id = %s AND post_date = %s
                    """, (queue_item['product_id'], datetime.now().date()))
                    
                    conn.commit()
                    
                    # Prepare response message
                    success_message = f"Post published successfully to {len(successful_posts)} page(s)"
                    if failed_posts:
                        success_message += f" (Failed: {', '.join(failed_posts)})"
                    
                    return jsonify({
                        'success': True,
                        'message': success_message,
                        'platform_post_id': primary_post_id,
                        'all_results': results,
                        'successful_posts': successful_posts,
                        'failed_posts': failed_posts
                    })
                else:
                    # All posts failed
                    error_message = f"Failed to post to any page: {'; '.join(failed_posts)}"
                    
                    # Update queue item with error
                    cur.execute("""
                        UPDATE posting_queue 
                        SET status = 'error', error_message = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (error_message, item_id))
                    
                    conn.commit()
                    
                    return jsonify({
                        'success': False,
                        'error': error_message,
                        'all_results': results
                    })
            else:
                # Old format: posting from daily-product-posts page
                if not product_id:
                    return jsonify({'success': False, 'error': 'Product ID is required'})
                
                # Get product details including image
                cur.execute("""
                    SELECT name, image_url, sku, price, description
                    FROM clan_products WHERE id = %s
                """, (product_id,))
                product = cur.fetchone()
                
                if not product:
                    return jsonify({'success': False, 'error': 'Product not found'})
                
                # Get Facebook credentials for both pages
                cur.execute("""
                    SELECT credential_key, credential_value
                    FROM platform_credentials 
                    WHERE platform_id = (SELECT id FROM platforms WHERE name = 'facebook')
                    AND is_active = true
                """)
                credentials = cur.fetchall()
                
                # Convert to dictionary
                creds = {}
                for cred in credentials:
                    creds[cred['credential_key']] = cred['credential_value']
                
                # Prepare post content
                post_content = content or f"Check out {product['name']} - £{product['price']}"
                product_image = product['image_url']
                
                # Define both pages to post to
                pages_to_post = []
                
                # Page 1 (CLAN by Scotweb)
                if creds.get('page_access_token') and creds.get('page_id'):
                    pages_to_post.append({
                        'page_id': creds['page_id'],
                        'access_token': creds['page_access_token'],
                        'name': 'CLAN by Scotweb'
                    })
                
                # Page 2 (Scotweb CLAN)
                if creds.get('page_access_token_2') and creds.get('page_id_2'):
                    pages_to_post.append({
                        'page_id': creds['page_id_2'],
                        'access_token': creds['page_access_token_2'],
                        'name': 'Scotweb CLAN'
                    })
                
                if not pages_to_post:
                    return jsonify({'success': False, 'error': 'No Facebook pages configured'})
                
                # Post to both pages
                results = []
                successful_posts = []
                failed_posts = []
                
                for page in pages_to_post:
                    result = post_to_facebook_page(
                        page['page_id'], 
                        page['access_token'], 
                        post_content, 
                        product_image, 
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
                
                # Update database based on results
                if successful_posts:
                    # Use the first successful post ID for the database
                    primary_post_id = successful_posts[0]
                    
                    # Update daily_posts with real Facebook post ID
                    today = datetime.now().date()
                    cur.execute("""
                        UPDATE daily_posts 
                        SET status = 'posted', posted_at = NOW(), facebook_post_id = %s
                        WHERE product_id = %s AND post_date = %s
                    """, (primary_post_id, product_id, today))
                    conn.commit()
                    
                    # Prepare response message
                    success_message = f"Post published successfully to {len(successful_posts)} page(s)"
                    if failed_posts:
                        success_message += f" (Failed: {', '.join(failed_posts)})"
                    
                    return jsonify({
                        'success': True,
                        'message': success_message,
                        'platform_post_id': primary_post_id,
                        'all_results': results,
                        'successful_posts': successful_posts,
                        'failed_posts': failed_posts
                    })
                else:
                    # All posts failed
                    error_message = f"Failed to post to any page: {'; '.join(failed_posts)}"
                    
                    return jsonify({
                        'success': False,
                        'error': error_message,
                        'all_results': results
                    })
            
    except Exception as e:
        logger.error(f"Error posting to Facebook: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/daily-product-posts/categories')
def get_categories():
    """Get available product categories."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # Get categories with hierarchy (all 258 categories)
            cur.execute("""
                SELECT id, name, level, parent_id, description
                FROM clan_categories 
                ORDER BY level, name
            """)
            categories = cur.fetchall()
            
            return jsonify({
                'success': True,
                'categories': [dict(cat) for cat in categories]
            })
            
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/daily-product-posts/today-status')
def get_today_status():
    """Get today's post status."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            today = datetime.now().date()
            cur.execute("""
                SELECT dp.*, p.* FROM daily_posts dp
                JOIN clan_products p ON dp.product_id = p.id
                WHERE dp.post_date = %s
            """, (today,))
            post = cur.fetchone()
            
            if post:
                return jsonify({
                    'success': True,
                    'post': dict(post)
                })
            else:
                return jsonify({
                    'success': True,
                    'post': None
                })
                
    except Exception as e:
        logger.error(f"Error getting today's status: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/syndication')
def syndication():
    """Social Media Syndication homepage."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # Get total platforms count
            cur.execute("SELECT COUNT(*) as total_platforms FROM platforms")
            total_platforms = cur.fetchone()['total_platforms']
            
            # Get active channels count (developed and active)
            cur.execute("""
                SELECT COUNT(*) as active_channels
                FROM content_processes 
                WHERE development_status = 'developed' AND is_active = true
            """)
            active_channels = cur.fetchone()['active_channels']
            
            # Get total configurations count
            cur.execute("SELECT COUNT(*) as total_configs FROM process_configurations")
            total_configs = cur.fetchone()['total_configs']
            
            return render_template('syndication.html',
                                total_platforms=total_platforms,
                                active_channels=active_channels,
                                total_configs=total_configs)
                                
    except Exception as e:
        logger.error(f"Error in syndication: {e}")
        return render_template('syndication.html',
                            total_platforms=0,
                            active_channels=0,
                            total_configs=0)

@app.route('/syndication/dashboard')
def syndication_dashboard():
    """New social media syndication dashboard with platform management."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # Get Facebook platform data
            cur.execute("""
                SELECT 
                    p.id, p.name, p.display_name, p.description, p.status, p.development_status,
                    p.total_posts_count, p.success_rate_percentage, p.average_response_time_ms,
                    p.last_activity_at, p.last_post_at, p.last_api_call_at,
                    p.estimated_completion_date, p.actual_completion_date,
                    p.development_notes, p.created_at, p.updated_at
                FROM platforms p 
                WHERE p.name = 'facebook'
            """)
            platform = cur.fetchone()
            
            if not platform:
                return "Facebook platform not found", 404
            
            # Get platform capabilities count
            cur.execute("""
                SELECT COUNT(*) as capabilities_count
                FROM platform_capabilities 
                WHERE platform_id = %s
            """, (platform['id'],))
            capabilities_count = cur.fetchone()['capabilities_count']
            
            # Get content processes for Facebook with configuration counts
            cur.execute("""
                SELECT 
                    cp.id, cp.process_name, cp.display_name, cp.description, 
                    cp.development_status, cp.priority, cp.is_active,
                    ct.name as channel_type_name, ct.display_name as channel_display_name,
                    (SELECT COUNT(*) FROM process_configurations WHERE process_id = cp.id) as configurations_count
                FROM content_processes cp
                JOIN channel_types ct ON cp.channel_type_id = ct.id
                WHERE cp.platform_id = %s
                ORDER BY cp.priority
            """, (platform['id'],))
            processes = cur.fetchall()
            
            # Get process configurations count
            cur.execute("""
                SELECT COUNT(*) as configs_count
                FROM process_configurations 
                WHERE process_id IN (SELECT id FROM content_processes WHERE platform_id = %s)
            """, (platform['id'],))
            configs_count = cur.fetchone()['configs_count']
            
            # Get content priority score
            cur.execute("""
                SELECT priority_score, priority_factors, last_calculated_at
                FROM content_priorities 
                WHERE content_type = 'platform' AND content_id = %s
            """, (platform['id'],))
            priority_data = cur.fetchone()
            
            # Calculate active channels count (only fully developed ones)
            active_channels = sum(1 for p in processes if p['development_status'] == 'developed' and p['is_active'])
            
            # Get platform capabilities for display
            cur.execute("""
                SELECT capability_name, capability_value, description, unit
                FROM platform_capabilities 
                WHERE platform_id = %s AND is_active = true
                ORDER BY display_order
            """, (platform['id'],))
            capabilities = cur.fetchall()
            
            return render_template('syndication_dashboard.html', 
                                platform=platform,
                                processes=processes,
                                capabilities=capabilities,
                                capabilities_count=capabilities_count,
                                configs_count=configs_count,
                                active_channels=active_channels,
                                priority_data=priority_data)
                                
    except Exception as e:
        logger.error(f"Error in syndication_dashboard: {e}")
        return f"Error loading dashboard: {str(e)}", 500

@app.route('/syndication/<platform_name>/<channel_type>')
def channel_config(platform_name, channel_type):
    """Generic channel configuration for any platform and channel type."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # Get platform data
            cur.execute("""
                SELECT 
                    p.id, p.name, p.display_name, p.description, p.status, p.development_status,
                    p.total_posts_count, p.success_rate_percentage, p.average_response_time_ms,
                    p.last_activity_at, p.last_post_at, p.last_api_call_at
                FROM platforms p 
                WHERE p.name = %s
            """, (platform_name,))
            platform = cur.fetchone()
            
            if not platform:
                return f"Platform '{platform_name}' not found", 404
            
            # Get channel type data
            cur.execute("""
                SELECT 
                    ct.id, ct.name, ct.display_name, ct.description
                FROM channel_types ct
                WHERE ct.name = %s
            """, (channel_type,))
            channel_type_data = cur.fetchone()
            
            if not channel_type_data:
                return f"Channel type '{channel_type}' not found", 404
            
            # Get process data for this platform/channel combination
            cur.execute("""
                SELECT 
                    cp.id, cp.process_name, cp.display_name, cp.description, 
                    cp.development_status, cp.priority, cp.is_active,
                    ct.name as channel_type_name, ct.display_name as channel_display_name
                FROM content_processes cp
                JOIN channel_types ct ON cp.channel_type_id = ct.id
                WHERE cp.platform_id = %s AND ct.name = %s
            """, (platform['id'], channel_type))
            process = cur.fetchone()
            
            if not process:
                return f"Process for {platform_name} {channel_type} not found", 404
            
            # Get process configurations count
            cur.execute("""
                SELECT COUNT(*) as configs_count
                FROM process_configurations 
                WHERE process_id = %s
            """, (process['id'],))
            configs_count = cur.fetchone()['configs_count']
            
            # Get process execution data (if any exists)
            cur.execute("""
                SELECT 
                    COALESCE(total_executions, 0) as total_executions,
                    COALESCE(success_rate_percentage, 0) as avg_success_rate
                FROM content_processes 
                WHERE id = %s
            """, (process['id'],))
            execution_data = cur.fetchone()
            
            # Get channel requirements for MVP interface
            cur.execute("""
                SELECT 
                    cr.requirement_category,
                    cr.requirement_key,
                    cr.requirement_value,
                    cr.description
                FROM channel_requirements cr
                JOIN platforms p ON cr.platform_id = p.id
                JOIN channel_types ct ON cr.channel_type_id = ct.id
                WHERE p.name = %s 
                AND ct.name = %s
                ORDER BY cr.requirement_category, cr.requirement_key
            """, (platform_name, channel_type))
            requirements = cur.fetchall()
            
            return render_template(f'syndication/{platform_name}/{channel_type}.html',
                                platform=platform,
                                channel_type=channel_type_data,
                                process=process,
                                configs_count=configs_count,
                                execution_data=execution_data,
                                requirements=requirements)
                                
    except Exception as e:
        logger.error(f"Error in channel_config: {e}")
        return f"Error loading configuration: {str(e)}", 500

@app.route('/syndication/facebook')
def facebook_posting_hub():
    """Consolidated Facebook posting hub with credentials and content management."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # Get Facebook platform data
            cur.execute("""
                SELECT 
                    p.id, p.name, p.display_name, p.description, p.status, p.development_status,
                    p.total_posts_count, p.success_rate_percentage, p.average_response_time_ms,
                    p.last_activity_at, p.last_post_at, p.last_api_call_at
                FROM platforms p 
                WHERE p.name = 'facebook'
            """)
            platform = cur.fetchone()
            
            if not platform:
                return "Facebook platform not found", 404
            
            # Get platform capabilities
            cur.execute("""
                SELECT capability_name, capability_value, description, unit
                FROM platform_capabilities 
                WHERE platform_id = %s AND is_active = true
                ORDER BY display_order
            """, (platform['id'],))
            capabilities = cur.fetchall()
            
            # Get platform credentials (if any)
            cur.execute("""
                SELECT credential_type, credential_key, credential_value, is_encrypted
                FROM platform_credentials 
                WHERE platform_id = %s AND is_active = true
            """, (platform['id'],))
            credentials = cur.fetchall()
            
            # Get recent posts from posting queue
            cur.execute("""
                SELECT pq.id, pq.platform, pq.channel_type, pq.content_type,
                       pq.scheduled_timestamp, pq.generated_content, pq.status,
                       pq.platform_post_id, pq.error_message, pq.created_at, pq.updated_at
                FROM posting_queue pq
                WHERE pq.platform = 'facebook'
                ORDER BY pq.scheduled_timestamp ASC, pq.created_at ASC
                LIMIT 20
            """)
            recent_posts = cur.fetchall()
            
            return render_template('syndication/facebook_posting_hub.html', 
                                platform=platform,
                                capabilities=capabilities,
                                credentials=credentials,
                                recent_posts=recent_posts)
                                
    except Exception as e:
        logger.error(f"Error in facebook_posting_hub: {e}")
        return f"Error loading Facebook hub: {str(e)}", 500

@app.route('/api/syndication/facebook/credentials', methods=['GET', 'POST'])
def facebook_credentials():
    """Get or save Facebook API credentials."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            if request.method == 'GET':
                # Get existing credentials
                cur.execute("""
                    SELECT credential_type, credential_key, credential_value
                    FROM platform_credentials 
                    WHERE platform_id = (SELECT id FROM platforms WHERE name = 'facebook')
                    AND is_active = true
                """)
                credentials = cur.fetchall()
                
                # Convert to dictionary format
                creds_dict = {}
                for cred in credentials:
                    creds_dict[cred['credential_key']] = cred['credential_value']
                
                return jsonify({
                    'success': True,
                    'credentials': creds_dict
                })
            
            elif request.method == 'POST':
                # Save new credentials
                data = request.get_json()
                
                # Get Facebook platform ID
                cur.execute("SELECT id FROM platforms WHERE name = 'facebook'")
                platform = cur.fetchone()
                if not platform:
                    return jsonify({'success': False, 'error': 'Facebook platform not found'})
                
                platform_id = platform['id']
                
                # Save each credential
                for key, value in data.items():
                    if value:  # Only save non-empty values
                        cur.execute("""
                            INSERT INTO platform_credentials (platform_id, credential_type, credential_key, credential_value, is_active)
                            VALUES (%s, 'api_key', %s, %s, true)
                            ON CONFLICT (platform_id, credential_type, credential_key)
                            DO UPDATE SET credential_value = EXCLUDED.credential_value, updated_at = NOW()
                        """, (platform_id, key, value))
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Credentials saved successfully'
                })
                
    except Exception as e:
        logger.error(f"Error in facebook_credentials: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/test-facebook-post', methods=['POST'])
def test_facebook_post():
    """Test endpoint to replicate the exact curl command that worked."""
    try:
        # Get Facebook credentials
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            cur.execute("""
                SELECT credential_key, credential_value
                FROM platform_credentials 
                WHERE platform_id = (SELECT id FROM platforms WHERE name = 'facebook')
                AND is_active = true
            """)
            credentials = cur.fetchall()
            
            # Convert to dictionary
            creds = {}
            for cred in credentials:
                creds[cred['credential_key']] = cred['credential_value']
            
            page_id = creds['page_id']
            access_token = creds['page_access_token']
            
            # Use the exact same curl command that worked
            import subprocess
            curl_cmd = f'curl -s -X POST "https://graph.facebook.com/v18.0/{page_id}/feed" -d "message=Test post from Flask app&access_token={access_token}"'
            print(f"DEBUG: Running curl command: {curl_cmd}")
            result = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True)
            print(f"DEBUG: Curl result: {result.stdout}")
            
            return jsonify({
                'success': True,
                'curl_command': curl_cmd,
                'result': result.stdout
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/syndication/facebook/feed-post')
def facebook_feed_post_redirect():
    """Redirect for backward compatibility to the generic route."""
    return redirect(url_for('channel_config', platform_name='facebook', channel_type='feed_post'))

@app.route('/syndication/facebook/daily-product-posts')
def daily_product_posts_redirect():
    """Redirect to the daily product posts page."""
    return redirect('/daily-product-posts')

@app.route('/syndication/posting')
def syndication_posting():
    """Platform-agnostic posting hub."""
    return render_template('syndication/posting/posting_hub.html')

@app.route('/syndication/posting/<platform_name>/<channel_type>')
def platform_posting(platform_name, channel_type):
    """Platform-specific posting interface."""
    return render_template('syndication/posting/platform_posting.html', 
                         platform_name=platform_name, 
                         channel_type=channel_type)

@app.route('/syndication/select-posts')
def syndication_select_posts():
    """Select Posts for syndication."""
    return render_template('syndication_select_posts.html')

# Platform settings route removed - will be reimplemented properly

# Individual platform settings route removed - will be reimplemented properly

@app.route('/syndication/create-piece')
def syndication_create_piece():
    """Create Piece page for social media syndication."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # Get Facebook platform data (default)
            cur.execute("""
                SELECT 
                    p.id, p.name, p.display_name, p.description, p.status, p.development_status,
                    p.total_posts_count, p.success_rate_percentage, p.average_response_time_ms,
                    p.last_activity_at, p.last_post_at, p.last_api_call_at
                FROM platforms p 
                WHERE p.name = 'facebook'
            """)
            platform = cur.fetchone()
            
            if not platform:
                return "Facebook platform not found", 404
            
            # Get Facebook Feed Post channel type data (default)
            cur.execute("""
                SELECT 
                    ct.id, ct.name, ct.display_name, ct.description
                FROM channel_types ct
                WHERE ct.name = 'feed_post'
            """)
            channel_type = cur.fetchone()
            
            if not channel_type:
                return "Feed Post channel type not found", 404
            
            # Get Facebook Feed Post requirements for the component
            cur.execute("""
                SELECT 
                    cr.requirement_category,
                    cr.requirement_key,
                    cr.requirement_value,
                    cr.description
                FROM channel_requirements cr
                JOIN platforms p ON cr.platform_id = p.id
                JOIN channel_types ct ON cr.channel_type_id = ct.id
                WHERE p.name = 'facebook' 
                AND ct.name = 'feed_post'
                ORDER BY cr.requirement_category, cr.requirement_key
            """)
            requirements = cur.fetchall()
            
            return render_template('syndication_create_piece.html',
                                platform=platform,
                                channel_type=channel_type,
                                requirements=requirements)
                                
    except Exception as e:
        logger.error(f"Error in syndication_create_piece: {e}")
        return f"Error loading create piece page: {str(e)}", 500

@app.route('/syndication/create-piece-includes')
def syndication_create_piece_includes():
    """Create Piece page for social media syndication (modular includes version)."""
    return render_template('syndication_create_piece_includes.html')

# Old social media specifications API endpoints removed - will be reimplemented properly

@app.route('/api/syndication/published-posts')
def get_published_posts():
    """Get all posts with status=published for syndication."""
    try:
        import psycopg
        from psycopg.rows import dict_row
        
        # Database connection
        conn = psycopg.connect(
            host="localhost",
            dbname="blog",
            user="postgres",
            password="postgres"
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get published posts ordered by most recently updated
        query = """
            SELECT 
                p.id,
                p.title,
                p.status,
                p.created_at,
                p.updated_at,
                p.slug,
                p.clan_uploaded_url,
                COUNT(ps.id) as section_count
            FROM post p
            LEFT JOIN post_section ps ON p.id = ps.post_id
            WHERE p.status = 'published'
            GROUP BY p.id, p.title, p.status, p.created_at, p.updated_at, p.slug, p.clan_uploaded_url
            ORDER BY p.updated_at DESC
        """
        
        cursor.execute(query)
        posts = cursor.fetchall()
        
        # Convert to list of dicts for JSON serialization
        posts_list = []
        for post in posts:
            posts_list.append({
                'id': post['id'],
                'title': post['title'],
                'status': post['status'],
                'created_at': post['created_at'].isoformat() if post['created_at'] else None,
                'updated_at': post['updated_at'].isoformat() if post['updated_at'] else None,
                'slug': post['slug'],
                'clan_uploaded_url': post['clan_uploaded_url'],
                'section_count': post['section_count']
            })
        
        cursor.close()
        conn.close()
        
        return {'posts': posts_list}
        
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/api/syndication/post-sections/<int:post_id>')
def get_post_sections(post_id):
    """Get all sections for a specific post."""
    try:
        import psycopg
        from psycopg.rows import dict_row
        
        # Database connection
        conn = psycopg.connect(
            host="localhost",
            dbname="blog",
            user="postgres",
            password="postgres"
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get sections for the specified post
        query = """
            SELECT 
                ps.id,
                ps.section_heading as title,
                ps.section_description as content,
                ps.polished,
                ps.section_order as "order"
            FROM post_section ps
            WHERE ps.post_id = %s
            ORDER BY ps.section_order ASC, ps.id ASC
        """
        
        cursor.execute(query, (post_id,))
        sections = cursor.fetchall()
        
        # Convert to list of dicts for JSON serialization
        sections_list = []
        for section in sections:
            # Find the actual image path using the same logic as the preview page
            image_path = find_section_image(post_id, section['id'])
            
            sections_list.append({
                'id': section['id'],
                'title': section['title'],
                'content': section['content'],
                'polished': section['polished'],
                'order': section['order'],
                'image_path': image_path
            })
        
        cursor.close()
        conn.close()
        
        return {'sections': sections_list}
        
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/test-api')
def test_api():
    """Test API endpoint."""
    return render_template('test_api.html')

@app.route('/docs/publishing')
def publishing_docs():
    """Serve publishing documentation."""
    import os
    docs_path = "/Users/nickfiddes/Code/projects/blog/blog-core/docs/reference/publishing/clan_com_publishing_system.md"
    
    if os.path.exists(docs_path):
        with open(docs_path, 'r') as f:
            content = f.read()
        return render_template('markdown_viewer.html', content=content, title="Clan.com Publishing System")
    else:
        return "Documentation not found", 404

@app.route('/api/syndication/posts')
def get_syndication_posts():
    """Get all published blog posts for manual selection."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute("""
                    SELECT id, title, created_at, updated_at, status, slug
                    FROM post
                    WHERE status = 'published'
                    ORDER BY created_at DESC
                """)
                posts = cur.fetchall()

                return jsonify({
                    'status': 'success',
                    'posts': [dict(post) for post in posts]
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/syndication/posts/<int:post_id>')
def get_syndication_post_details(post_id):
    """Get details for a specific blog post."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute("""
                    SELECT id, title, created_at, updated_at, status, slug
                    FROM post
                    WHERE id = %s AND status = 'published'
                """, (post_id,))
                post = cur.fetchone()

                if post:
                    # Get section count
                    cur.execute("""
                        SELECT COUNT(*) as section_count
                        FROM post_section
                        WHERE post_id = %s
                    """, (post_id,))
                    section_count = cur.fetchone()['section_count']

                    post_dict = dict(post)
                    post_dict['section_count'] = section_count

                    return jsonify({
                        'status': 'success',
                        'post': post_dict
                    })
                else:
                    return jsonify({'error': 'Post not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/syndication/facebook/schedules', methods=['GET'])
def get_blog_post_schedules():
    """Get all schedules for blog post syndication."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute("""
                    SELECT id, name, days, time, timezone, is_active as active, created_at
                    FROM daily_posts_schedule 
                    WHERE is_active = true 
                    AND platform = 'facebook' 
                    AND channel_type = 'feed_post' 
                    AND content_type = 'blog_post'
                    ORDER BY created_at DESC
                """)
                
                schedules = cur.fetchall()
                
                transformed_schedules = []
                for schedule in schedules:
                    transformed_schedules.append({
                        'id': schedule['id'],
                        'name': schedule['name'],
                        'days': schedule['days'],
                        'time': str(schedule['time']),
                        'timezone': schedule['timezone'],
                        'active': schedule['active'],
                        'created_at': schedule['created_at'].isoformat() if schedule['created_at'] else None
                    })
                
                return jsonify({
                    'success': True,
                    'schedules': transformed_schedules
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/syndication/facebook/schedules', methods=['POST'])
def create_blog_post_schedule():
    """Create a new schedule for blog post syndication."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'days', 'time', 'timezone']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO daily_posts_schedule (name, days, time, timezone, platform, channel_type, content_type, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    data['name'],
                    json.dumps(data['days']),  # Convert array to JSON string
                    data['time'],
                    data['timezone'],
                    'facebook',
                    'feed_post',
                    'blog_post',
                    data.get('active', True)
                ))
                
                schedule_id = cur.fetchone()[0]
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Schedule created successfully',
                    'schedule_id': schedule_id
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/syndication/facebook/schedules/<int:schedule_id>', methods=['PUT'])
def update_blog_post_schedule(schedule_id):
    """Update a blog post schedule."""
    try:
        data = request.get_json()
        
        # Build update query dynamically
        update_fields = []
        update_values = []
        
        allowed_fields = ['name', 'days', 'time', 'timezone', 'active']
        for field in allowed_fields:
            if field in data:
                if field == 'active':
                    update_fields.append('is_active = %s')
                elif field == 'days':
                    update_fields.append('days = %s')
                    update_values.append(json.dumps(data[field]))  # Convert array to JSON string
                    continue
                else:
                    update_fields.append(f'{field} = %s')
                update_values.append(data[field])
        
        if not update_fields:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        update_values.append(schedule_id)
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE daily_posts_schedule 
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s 
                    AND platform = 'facebook' 
                    AND channel_type = 'feed_post' 
                    AND content_type = 'blog_post'
                    RETURNING id
                """, update_values)
                
                updated_schedule = cur.fetchone()
                if not updated_schedule:
                    return jsonify({'error': 'Schedule not found'}), 404
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Schedule updated successfully'
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/syndication/facebook/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_blog_post_schedule(schedule_id):
    """Delete a blog post schedule."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM daily_posts_schedule 
                    WHERE id = %s 
                    AND platform = 'facebook' 
                    AND channel_type = 'feed_post' 
                    AND content_type = 'blog_post'
                    RETURNING id
                """, (schedule_id,))
                
                deleted_schedule = cur.fetchone()
                if not deleted_schedule:
                    return jsonify({'error': 'Schedule not found'}), 404
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Schedule deleted successfully'
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/syndication/facebook/queue', methods=['GET'])
def get_blog_post_queue():
    """Get all blog post items in the Facebook posting queue."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute("""
                    SELECT 
                        pq.id,
                        pq.product_id as post_id,
                        p.title as post_title,
                        p.slug as post_slug,
                        p.created_at as post_created_at,
                        ps.section_heading as section_title,
                        ps.section_order as section_order,
                        pq.generated_content,
                        pq.scheduled_date,
                        pq.scheduled_time,
                        pq.schedule_name,
                        pq.timezone,
                        pq.status,
                        pq.queue_order,
                        pq.created_at,
                        pq.updated_at
                    FROM posting_queue pq
                    LEFT JOIN post p ON pq.product_id = p.id
                    LEFT JOIN post_section ps ON pq.section_id = ps.id
                    WHERE pq.platform = 'facebook' 
                    AND pq.channel_type = 'feed_post' 
                    AND pq.content_type = 'blog_post'
                    ORDER BY pq.queue_order ASC, pq.created_at ASC
                """)
                
                queue_items = cur.fetchall()
                
                transformed_items = []
                for item in queue_items:
                    transformed_items.append({
                        'id': item['id'],
                        'post_id': item['post_id'],
                        'post_title': item['post_title'],
                        'post_slug': item['post_slug'],
                        'post_created_at': item['post_created_at'].isoformat() if item['post_created_at'] else None,
                        'section_title': item['section_title'],
                        'section_order': item['section_order'],
                        'generated_content': item['generated_content'],
                        'scheduled_date': item['scheduled_date'].isoformat() if item['scheduled_date'] else None,
                        'scheduled_time': str(item['scheduled_time']) if item['scheduled_time'] else None,
                        'schedule_name': item['schedule_name'],
                        'timezone': item['timezone'],
                        'status': item['status'],
                        'queue_order': item['queue_order'],
                        'created_at': item['created_at'].isoformat() if item['created_at'] else None,
                        'updated_at': item['updated_at'].isoformat() if item['updated_at'] else None
                    })
                
                return jsonify({
                    'success': True,
                    'queue_items': transformed_items
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/syndication/facebook/queue', methods=['POST'])
def add_to_blog_post_queue():
    """Add a blog post item to the Facebook posting queue."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['post_id', 'section_id', 'generated_content', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get next queue order
                cur.execute("""
                    SELECT COALESCE(MAX(queue_order), 0) + 1 as next_order
                    FROM posting_queue 
                    WHERE platform = 'facebook' AND channel_type = 'feed_post' AND content_type = 'blog_post'
                """)
                next_order = cur.fetchone()[0]
                
                # Get post and section details
                cur.execute("""
                    SELECT p.title, ps.section_heading as section_title, ps.section_order as section_order
                    FROM post p
                    JOIN post_section ps ON p.id = ps.post_id
                    WHERE p.id = %s AND ps.id = %s
                """, (data['post_id'], data['section_id']))
                
                post_section = cur.fetchone()
                if not post_section:
                    return jsonify({'error': 'Post or section not found'}), 404
                
                # Insert into queue
                cur.execute("""
                    INSERT INTO posting_queue (
                        product_id, section_id, generated_content, scheduled_date, scheduled_time, 
                        schedule_name, timezone, status, queue_order, platform, channel_type, content_type
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    data['post_id'],
                    data['section_id'],
                    data['generated_content'],
                    data['scheduled_date'],
                    data['scheduled_time'],
                    data['schedule_name'],
                    data['timezone'],
                    data.get('status', 'ready'),
                    next_order,
                    'facebook',
                    'feed_post',
                    'blog_post'
                ))
                
                queue_item_id = cur.fetchone()[0]
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Item added to queue successfully',
                    'queue_item_id': queue_item_id
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/syndication/facebook/queue/<int:item_id>', methods=['DELETE'])
def remove_from_blog_post_queue(item_id):
    """Remove a blog post item from the Facebook posting queue."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM posting_queue 
                    WHERE id = %s AND platform = 'facebook' AND channel_type = 'feed_post' AND content_type = 'blog_post'
                    RETURNING id
                """, (item_id,))
                
                deleted_item = cur.fetchone()
                if not deleted_item:
                    return jsonify({'error': 'Queue item not found'}), 404
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Item removed from queue successfully'
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/syndication/facebook/queue/<int:item_id>', methods=['PUT'])
def update_blog_post_queue_item(item_id):
    """Update a blog post item in the Facebook posting queue."""
    try:
        data = request.get_json()
        
        # Build update query dynamically
        update_fields = []
        update_values = []
        
        allowed_fields = ['generated_content', 'scheduled_date', 'scheduled_time', 'schedule_name', 'timezone', 'status', 'queue_order']
        for field in allowed_fields:
            if field in data:
                update_fields.append(f'{field} = %s')
                update_values.append(data[field])
        
        if not update_fields:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        update_values.append(item_id)
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE posting_queue 
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND platform = 'facebook' AND channel_type = 'feed_post' AND content_type = 'blog_post'
                    RETURNING id
                """, update_values)
                
                updated_item = cur.fetchone()
                if not updated_item:
                    return jsonify({'error': 'Queue item not found'}), 404
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Queue item updated successfully'
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/syndication/facebook/queue/clear', methods=['DELETE'])
def clear_blog_post_queue():
    """Clear all blog post items from the Facebook posting queue."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM posting_queue 
                    WHERE platform = 'facebook' AND channel_type = 'feed_post' AND content_type = 'blog_post'
                """)
                
                deleted_count = cur.rowcount
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Cleared {deleted_count} items from queue'
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/syndication/social-media-platforms')
def get_social_media_platforms():
    """Get only developed social media platforms for the dropdown selector."""
    try:
        from models.social_media import SocialMediaPlatform
        db_config = {'host': 'localhost', 'dbname': 'blog', 'user': 'autojenny', 'password': ''}
        platform_model = SocialMediaPlatform(db_config)
        platforms = platform_model.get_platforms_by_status('developed')
        platforms_list = [{'id': p['id'], 'platform_name': p['platform_name'], 'display_name': p['display_name'], 'status': p['status'], 'priority': p['priority'], 'icon_url': p['icon_url']} for p in platforms]
        return jsonify({'platforms': platforms_list})
    except Exception as e:
        print(f"Error fetching social media platforms: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/syndication/content-processes')
def get_content_processes():
    """Get only developed content processes for syndication."""
    try:
        from models.content_process import ContentProcess
        db_config = {'host': 'localhost', 'dbname': 'blog', 'user': 'autojenny', 'password': ''}
        process_model = ContentProcess(db_config)
        processes = process_model.get_processes_by_development_status('developed')
        processes_list = [{'id': p['id'], 'process_name': p['process_name'], 'display_name': p['display_name'], 'platform_id': p['platform_id'], 'platform_name': p['platform_name'], 'platform_display_name': p['platform_display_name'], 'content_type': p['content_type'], 'description': p['description'], 'is_active': p['is_active'], 'priority': p['priority'], 'development_status': p.get('development_status', 'draft')} for p in processes]
        return jsonify({'processes': processes_list})
    except Exception as e:
        print(f"Error fetching content processes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/syndication/content-processes/all')
def get_all_content_processes():
    """Get all content processes (including draft/undeveloped) for admin purposes."""
    try:
        from models.content_process import ContentProcess
        db_config = {'host': 'localhost', 'dbname': 'blog', 'user': 'autojenny', 'password': ''}
        process_model = ContentProcess(db_config)
        processes = process_model.get_all_processes()
        processes_list = [{'id': p['id'], 'process_name': p['process_name'], 'display_name': p['display_name'], 'platform_id': p['platform_id'], 'platform_name': p['platform_name'], 'platform_display_name': p['platform_display_name'], 'content_type': p['content_type'], 'description': p['description'], 'is_active': p['is_active'], 'priority': p['priority'], 'development_status': p.get('development_status', 'draft')} for p in processes]
        return jsonify({'processes': processes_list})
    except Exception as e:
        print(f"Error fetching all content processes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/syndication/content-processes/<int:process_id>/configs')
def get_process_configs(process_id):
    """Get configurations for a specific content process."""
    try:
        from models.content_process import ContentProcess
        db_config = {'host': 'localhost', 'dbname': 'blog', 'user': 'autojenny', 'password': ''}
        process_model = ContentProcess(db_config)
        configs = process_model.get_process_configs(process_id)
        configs_list = [{'id': c['id'], 'config_category': c['config_category'], 'config_key': c['config_key'], 'config_value': c['config_value'], 'config_type': c['config_type'], 'is_required': c['is_required'], 'display_order': c['display_order']} for c in configs]
        return jsonify({'configs': configs_list})
    except Exception as e:
        print(f"Error fetching process configs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/syndication/content-processes/<int:process_id>/configs', methods=['PUT'])
def update_process_config(process_id):
    """Update a specific process configuration."""
    try:
        from models.content_process import ContentProcess
        db_config = {'host': 'localhost', 'dbname': 'blog', 'user': 'autojenny', 'password': ''}
        process_model = ContentProcess(db_config)
        
        data = request.get_json()
        config_id = data.get('config_id')
        new_value = data.get('value')
        
        if not config_id or new_value is None:
            return jsonify({'error': 'Missing config_id or value'}), 400
        
        # Update the configuration
        success = process_model.update_config_value(config_id, new_value)
        
        if success:
            return jsonify({'message': 'Configuration updated successfully'})
        else:
            return jsonify({'error': 'Failed to update configuration'}), 500
            
    except Exception as e:
        print(f"Error updating process config: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/syndication/content-processes/<int:process_id>/status', methods=['PUT'])
def update_process_development_status(process_id):
    """Update the development status of a content process."""
    try:
        from models.content_process import ContentProcess
        db_config = {'host': 'localhost', 'dbname': 'blog', 'user': 'autojenny', 'password': ''}
        process_model = ContentProcess(db_config)
        
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status or new_status not in ['draft', 'developed', 'testing', 'production']:
            return jsonify({'error': 'Invalid status value'}), 400
        
        # Update the development status
        success = process_model.update_development_status(process_id, new_status)
        
        if success:
            return jsonify({'message': 'Development status updated successfully'})
        else:
            return jsonify({'error': 'Failed to update development status'}), 500
            
    except Exception as e:
        print(f"Error updating process status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/docs/social_media_syndication_plan.md')
def syndication_docs():
    """Serve social media syndication plan documentation."""
    import os
    docs_path = "/Users/nickfiddes/Code/projects/blog/blog-launchpad/docs/social_media_syndication_plan.md"
    
    if os.path.exists(docs_path):
        with open(docs_path, 'r') as f:
            content = f.read()
        return render_template('markdown_viewer.html', content=content, title="Social Media Syndication Plan")
    else:
        return "Documentation not found", 404

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'blog-launchpad'})

@app.route('/preview/<int:post_id>')
@app.route('/preview/<int:post_id>/')
def preview_post(post_id):
    """Preview a specific post."""
    # Get post data from database
    post = get_post_with_development(post_id)
    if not post:
        return "Post not found", 404
    
    sections = get_post_sections_with_images(post_id)
    
    # Find header image
    header_image_path = find_header_image(post_id)
    if header_image_path:
        # Get header image caption from database
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            cur.execute("""
                SELECT header_image_caption, header_image_title, header_image_width, header_image_height,
                       cross_promotion_category_id, cross_promotion_category_title,
                       cross_promotion_product_id, cross_promotion_product_title
                FROM post WHERE id = %s
            """, (post_id,))
            header_data = cur.fetchone()
            header_caption = header_data['header_image_caption'] if header_data and header_data['header_image_caption'] else None
        
        post['header_image'] = {
            'path': header_image_path,
            'alt_text': f"Header image for {post.get('title', 'this post')}",
            'caption': header_caption,
            'title': header_data['header_image_title'] if header_data and header_data['header_image_title'] else None,
            'width': header_data['header_image_width'] if header_data and header_data['header_image_width'] else None,
            'height': header_data['header_image_height'] if header_data and header_data['header_image_height'] else None
        }
        
        # Add cross-promotion data
        post['cross_promotion'] = {
            'category_id': header_data['cross_promotion_category_id'] if header_data and header_data['cross_promotion_category_id'] else None,
            'category_title': header_data['cross_promotion_category_title'] if header_data and header_data['cross_promotion_category_title'] else None,
            'product_id': header_data['cross_promotion_product_id'] if header_data and header_data['cross_promotion_product_id'] else None,
            'product_title': header_data['cross_promotion_product_title'] if header_data and header_data['cross_promotion_product_title'] else None,
            'category_position': header_data.get('cross_promotion_category_position'),
            'product_position': header_data.get('cross_promotion_product_position')
        }
    
    return render_template('post_preview.html', post=post, sections=sections)

@app.route('/clan-post-html/<int:post_id>')
def clan_post_html(post_id):
    """View the clan_post HTML that will be uploaded to Clan.com."""
    # Get view type parameter (default to 'local')
    view_type = request.args.get('view', 'local')
    
    # Get post data from database
    post = get_post_with_development(post_id)
    if not post:
        return "Post not found", 404
    
    sections = get_post_sections_with_images(post_id)
    
    # Find header image
    header_image_path = find_header_image(post_id)
    if header_image_path:
        # Get header image caption from database
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            cur.execute("""
                SELECT header_image_caption, header_image_title, header_image_width, header_image_height
                FROM post WHERE id = %s
            """, (post_id,))
            header_data = cur.fetchone()
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
        raw_html = render_template('clan_post_raw.html', post=post, sections=sections)
        return raw_html, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    else:
        # Return processed HTML with CDN URLs (what gets sent to Clan.com)
        from clan_publisher import ClanPublisher
        publisher = ClanPublisher()
        
        # Get uploaded images mapping from database
        uploaded_images = {}
        try:
            with get_db_connection() as conn:
                cur = conn.cursor(row_factory=psycopg.rows.dict_row)
                cur.execute("""
                    SELECT local_image_path, clan_uploaded_url 
                    FROM section_image_mappings 
                    WHERE post_id = %s
                """, (post_id,))
                
                for row in cur.fetchall():
                    uploaded_images[row['local_image_path']] = row['clan_uploaded_url']
                    
                # Also get header image mapping if it exists
                cur.execute("""
                    SELECT local_image_path, clan_uploaded_url 
                    FROM section_image_mappings 
                    WHERE post_id = %s AND section_id IS NULL
                """, (post_id,))
                
                for row in cur.fetchall():
                    uploaded_images[row['local_image_path']] = row['clan_uploaded_url']
                    
        except Exception as e:
            print(f"Warning: Could not load image mappings: {e}")
        
        # Get the exact same HTML that gets uploaded
        upload_html = publisher.get_preview_html_content(post, sections, uploaded_images)
        
        if upload_html:
            # Return the actual upload HTML as raw text - NO RENDERING
            # Set content type to text/plain so browser shows source code
            return upload_html, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        else:
            # Fallback to raw template if preview HTML fails
            raw_html = render_template('clan_post_raw.html', post=post, sections=sections)
            return raw_html, 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/clan-api-data/<int:post_id>')
def clan_api_data(post_id):
    """View the actual API request data that was/will be sent to Clan.com."""
    # Get post data from database
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
    
    # Ensure created_at is handled properly
    if post.get('created_at') and not isinstance(post['created_at'], str):
        post['created_at'] = post['created_at'].isoformat() if hasattr(post['created_at'], 'isoformat') else str(post['created_at'])
    
    # Add header image if exists
    header_image_path = find_header_image(post_id)
    if header_image_path:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            cur.execute("""
                SELECT header_image_caption, header_image_title, header_image_width, header_image_height,
                       cross_promotion_category_id, cross_promotion_category_title,
                       cross_promotion_product_id, cross_promotion_product_title,
                       cross_promotion_category_position, cross_promotion_product_position,
                       cross_promotion_category_widget_html, cross_promotion_product_widget_html
                FROM post WHERE id = %s
            """, (post_id,))
            header_data = cur.fetchone()
            
            post['header_image'] = {
                'path': header_image_path,
                'alt_text': f"Header image for {post.get('title', 'this post')}",
                'caption': header_data['header_image_caption'] if header_data else None,
                'title': header_data['header_image_title'] if header_data else None,
                'width': header_data['header_image_width'] if header_data else None,
                'height': header_data['header_image_height'] if header_data else None
            }
            
            post['cross_promotion'] = {
                'category_id': header_data['cross_promotion_category_id'] if header_data else None,
                'category_title': header_data['cross_promotion_category_title'] if header_data else None,
                'product_id': header_data['cross_promotion_product_id'] if header_data else None,
                'product_title': header_data['cross_promotion_product_title'] if header_data else None,
                'category_position': header_data.get('cross_promotion_category_position'),
                'product_position': header_data.get('cross_promotion_product_position'),
                'category_widget_html': header_data.get('cross_promotion_category_widget_html'),
                'product_widget_html': header_data.get('cross_promotion_product_widget_html')
            }
    
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

@app.route('/api/syndication/resize-image', methods=['POST'])
def resize_image_for_facebook():
    """Resize an image to Facebook's recommended dimensions (1200x630)."""
    try:
        data = request.get_json()
        image_url = data.get('image_url')
        
        if not image_url:
            return jsonify({'error': 'Missing image_url'}), 400
        
        # For now, return a mock response with the resized image URL
        # In a real implementation, this would call the blog-images service
        # and return the actual resized image URL
        
        # Extract filename from URL for demo purposes
        import urllib.parse
        parsed_url = urllib.parse.urlparse(image_url)
        filename = os.path.basename(parsed_url.path)
        
        # Mock resized image URL (in reality, this would be the processed image)
        resized_url = f"{image_url}?resized=1200x630"
        
        return jsonify({
            'success': True,
            'original_url': image_url,
            'resized_url': resized_url,
            'dimensions': {
                'width': 1200,
                'height': 630,
                'aspect_ratio': '1.91:1'
            },
            'message': 'Image resized for Facebook (mock response)'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/syndication/image-mappings/<int:post_id>', methods=['GET'])
def get_section_image_mappings(post_id):
    """Get the stored image mappings for a post's sections."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            cur.execute("""
                SELECT 
                    sim.section_id,
                    sim.local_image_path,
                    sim.clan_uploaded_url,
                    sim.image_filename,
                    sim.image_size_bytes,
                    sim.image_dimensions,
                    sim.uploaded_at
                FROM section_image_mappings sim
                WHERE sim.post_id = %s
                ORDER BY sim.section_id
            """, (post_id,))
            
            mappings = cur.fetchall()
            
            # Convert to dictionary format for easier lookup
            result = {}
            for mapping in mappings:
                section_id = mapping['section_id']
                result[section_id] = {
                    'local_image_path': mapping['local_image_path'],
                    'clan_uploaded_url': mapping['clan_uploaded_url'],
                    'image_filename': mapping['image_filename'],
                    'image_size_bytes': mapping['image_size_bytes'],
                    'image_dimensions': mapping['image_dimensions'],
                    'uploaded_at': mapping['uploaded_at'].isoformat() if mapping['uploaded_at'] else None
                }
            
            return jsonify({
                'status': 'success',
                'post_id': post_id,
                'mappings': result,
                'count': len(result)
            })
            
    except Exception as e:
        logger.error(f"Error getting image mappings: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def get_post_with_development(post_id):
    """Fetch post with development data."""
    with get_db_connection() as conn:
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        # Get post data, alias post.id as post_id
        cur.execute("""
            SELECT p.id AS post_id, p.title, p.subtitle, p.created_at, p.updated_at, p.status, p.slug, p.summary, p.title_choices,
                   p.clan_post_id, p.clan_uploaded_url,
                   pd.idea_seed, pd.intro_blurb, pd.main_title,
                   p.cross_promotion_category_id, p.cross_promotion_category_title,
                   p.cross_promotion_product_id, p.cross_promotion_product_title,
                   p.cross_promotion_category_position, p.cross_promotion_product_position,
                   p.cross_promotion_category_widget_html, p.cross_promotion_product_widget_html
            FROM post p
            LEFT JOIN post_development pd ON pd.post_id = p.id
            WHERE p.id = %s
        """, (post_id,))
        
        post = cur.fetchone()
        if not post:
            return None
            
        # Get header image if exists
        if post.get('header_image_id'):
            cur.execute("""
                SELECT * FROM image WHERE id = %s
            """, (post['header_image_id'],))
            header_image = cur.fetchone()
            if header_image:
                post['header_image'] = dict(header_image)
        
        post_dict = dict(post)
        # Always use post_id for the edit link
        post_dict['id'] = post_dict['post_id']
        
        # Add cross-promotion data structure
        post_dict['cross_promotion'] = {
            'category_id': post_dict.get('cross_promotion_category_id'),
            'category_title': post_dict.get('cross_promotion_category_title'),
            'product_id': post_dict.get('cross_promotion_product_id'),
            'product_title': post_dict.get('cross_promotion_product_title'),
            'category_position': post_dict.get('cross_promotion_category_position'),
            'product_position': post_dict.get('cross_promotion_product_position'),
            'category_widget_html': post_dict.get('cross_promotion_category_widget_html'),
            'product_widget_html': post_dict.get('cross_promotion_product_widget_html')
        }
        
        return post_dict

def find_header_image(post_id):
    """
    Find the first available header image for a post in the new directory structure.
    Returns the image path or None if no image found.
    """
    import urllib.parse
    
    # Path to the blog-images static directory
    blog_images_static = "/Users/nickfiddes/Code/projects/blog/blog-images/static"
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')

    # 1. Look for images in the header's optimized directory first
    header_optimized_path = os.path.join(blog_images_static, "content", "posts", str(post_id), "header", "optimized")
    if os.path.exists(header_optimized_path):
        image_files = [f for f in os.listdir(header_optimized_path)
                      if f.lower().endswith(image_extensions) and not f.startswith('.')]
        if image_files:
            image_filename = image_files[0]
            # URL-encode the filename to handle spaces and special characters
            encoded_filename = urllib.parse.quote(image_filename)
            return f"/static/content/posts/{post_id}/header/optimized/{encoded_filename}"

    # 2. Fall back to raw directory if optimized is empty
    header_raw_path = os.path.join(blog_images_static, "content", "posts", str(post_id), "header", "raw")
    if os.path.exists(header_raw_path):
        image_files = [f for f in os.listdir(header_raw_path)
                      if f.lower().endswith(image_extensions) and not f.startswith('.')]
        if image_files:
            image_filename = image_files[0]
            # URL-encode the filename to handle spaces and special characters
            encoded_filename = urllib.parse.quote(image_filename)
            return f"/static/content/posts/{post_id}/header/raw/{encoded_filename}"

    return None

def find_section_image(post_id, section_id):
    """
    Find the first available image for a section in the new directory structure.
    Returns the image path or None if no image found.
    """
    import urllib.parse
    
    # Path to the blog-images static directory
    blog_images_static = "/Users/nickfiddes/Code/projects/blog/blog-images/static"
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')

    # 1. Look for images in the section's optimized directory first
    section_optimized_path = os.path.join(blog_images_static, "content", "posts", str(post_id), "sections", str(section_id), "optimized")
    if os.path.exists(section_optimized_path):
        image_files = [f for f in os.listdir(section_optimized_path)
                      if f.lower().endswith(image_extensions) and not f.startswith('.')]
        if image_files:
            image_filename = image_files[0]
            # URL-encode the filename to handle spaces and special characters
            encoded_filename = urllib.parse.quote(image_filename)
            # Return URL pointing to blog-images service on port 5005
            return f"http://localhost:5005/static/content/posts/{post_id}/sections/{section_id}/optimized/{encoded_filename}"

    # 2. Fall back to raw directory if optimized is empty
    section_raw_path = os.path.join(blog_images_static, "content", "posts", str(post_id), "sections", str(section_id), "raw")
    if os.path.exists(section_raw_path):
        image_files = [f for f in os.listdir(section_raw_path)
                      if f.lower().endswith(image_extensions) and not f.startswith('.')]
        if image_files:
            image_filename = image_files[0]
            # URL-encode the filename to handle spaces and special characters
            encoded_filename = urllib.parse.quote(image_filename)
            # Return URL pointing to blog-images service on port 5005
            return f"http://localhost:5005/static/content/posts/{post_id}/sections/{section_id}/raw/{encoded_filename}"

    return None

def get_post_sections_with_images(post_id):
    """Fetch sections with complete image metadata."""
    with get_db_connection() as conn:
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        # Get all sections for the post
        cur.execute("""
            SELECT 
                id, post_id, section_order, 
                section_heading,
                section_description, ideas_to_include, facts_to_include,
                draft, polished, highlighting, image_concepts,
                image_prompts,
                image_meta_descriptions, image_captions, status,
                image_title, image_width, image_height
            FROM post_section 
            WHERE post_id = %s 
            ORDER BY section_order
        """, (post_id,))
        
        raw_sections = cur.fetchall()
        sections = []
        
        for section in raw_sections:
            section_dict = dict(section)
            
            # Try to find image in the new directory structure first
            image_path = find_section_image(post_id, section['id'])
            
            if image_path:
                # Found image in new structure
                section_dict['image'] = {
                    'path': image_path,
                    'alt_text': section.get('image_captions') or f"Image for {section.get('section_heading', 'section')}",
                    'title': section.get('image_title'),
                    'width': section.get('image_width'),
                    'height': section.get('image_height')
                }
                # Also set the caption directly on the section for template compatibility
                section_dict['image_captions'] = section.get('image_captions')
            elif section.get('image_id'):
                # Fallback to legacy image_id system
                cur.execute("""
                    SELECT * FROM image WHERE id = %s
                """, (section['image_id'],))
                image = cur.fetchone()
                if image:
                    section_dict['image'] = dict(image)
                    # Also set the caption directly on the section for template compatibility
                    section_dict['image_captions'] = section.get('image_captions')
            elif section.get('generated_image_url'):
                # Fallback to generated_image_url
                section_dict['image'] = {
                    'path': section['generated_image_url'],
                    'alt_text': section.get('image_captions') or 'Section image',
                    'title': section.get('image_title'),
                    'width': section.get('image_width'),
                    'height': section.get('image_height')
                }
                # Also set the caption directly on the section for template compatibility
                section_dict['image_captions'] = section.get('image_captions')
            else:
                # No image found - provide placeholder info
                section_dict['image'] = {
                    'path': None,
                    'alt_text': f"No image available for {section.get('section_heading', 'this section')}",
                    'placeholder': True
                }
            
            sections.append(section_dict)
        
        return sections

@app.route('/api/posts')
def get_posts():
    """Get all posts for the launchpad."""
    with get_db_connection() as conn:
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        cur.execute("""
            SELECT p.id, p.title, p.created_at, p.updated_at, p.status,
                   p.clan_post_id, p.clan_last_attempt, p.clan_error, p.clan_uploaded_url,
                   pd.idea_seed, pd.provisional_title, pd.intro_blurb
            FROM post p
            LEFT JOIN post_development pd ON p.id = pd.post_id
            WHERE p.status != 'deleted'
            ORDER BY p.created_at DESC
        """)
        posts = cur.fetchall()
        return jsonify([dict(post) for post in posts])

@app.route('/api/cross-promotion/<int:post_id>', methods=['GET'])
def get_cross_promotion(post_id):
    """Get cross-promotion data for a post."""
    with get_db_connection() as conn:
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        cur.execute("""
            SELECT cross_promotion_category_id, cross_promotion_category_title,
                   cross_promotion_product_id, cross_promotion_product_title
            FROM post WHERE id = %s
        """, (post_id,))
        data = cur.fetchone()
        
        if data:
            return jsonify({
                'category_id': data['cross_promotion_category_id'],
                'category_title': data['cross_promotion_category_title'],
                'product_id': data['cross_promotion_product_id'],
                'product_title': data['cross_promotion_product_title']
            })
        else:
            return jsonify({'error': 'Post not found'}), 404

@app.route('/api/cross-promotion/<int:post_id>', methods=['POST'])
def update_cross_promotion(post_id):
    """Update cross-promotion data for a post."""
    data = request.get_json()
    
    # Generate the actual widget HTML
    category_widget_html = None
    product_widget_html = None
    
    if data.get('category_id') and data.get('category_position'):
        category_widget_html = f'{{{{widget type="swcatalog/widget_crossSell_category" category_id="{data.get("category_id")}" title="{data.get("category_title") or "Related Department"}"}}}}'
    
    if data.get('product_id') and data.get('product_position'):
        product_widget_html = f'{{{{widget type="swcatalog/widget_crossSell_product" product_id="{data.get("product_id")}" title="{data.get("product_title") or "Related Products"}"}}}}'
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE post SET 
                cross_promotion_category_id = %s,
                cross_promotion_category_title = %s,
                cross_promotion_product_id = %s,
                cross_promotion_product_title = %s,
                cross_promotion_category_position = %s,
                cross_promotion_product_position = %s,
                cross_promotion_category_widget_html = %s,
                cross_promotion_product_widget_html = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            data.get('category_id'),
            data.get('category_title'),
            data.get('product_id'),
            data.get('product_title'),
            data.get('category_position'),
            data.get('product_position'),
            category_widget_html,
            product_widget_html,
            post_id
        ))
        conn.commit()
        
        if cur.rowcount > 0:
            return jsonify({'success': True, 'message': 'Cross-promotion data updated'})
        else:
            return jsonify({'error': 'Post not found'}), 404

# Clan API functionality moved to separate module
from clan_api import get_categories, get_products, get_category_products, get_related_products, refresh_cache, get_cache_stats

@app.route('/api/clan/categories')
def clan_categories():
    """Get available categories from clan.com API."""
    categories = get_categories()
    return jsonify(categories)

@app.route('/api/clan/products')
def clan_products():
    """Search products from clan.com API."""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 50)
    products = get_products(limit=int(limit), query=query)
    return jsonify(products)

@app.route('/api/clan/category/<int:category_id>/products')
def clan_category_products(category_id):
    """Get products from a specific category."""
    products = get_category_products(category_id)
    return jsonify(products)

@app.route('/api/clan/product/<int:product_id>/related')
def clan_related_products(product_id):
    """Get related products for a specific product."""
    products = get_related_products(product_id)
    return jsonify(products)

@app.route('/api/clan/widget/products')
def clan_widget_products():
    """Local preselection endpoint for widget - uses cached catalog for super-fast loading"""
    try:
        from clan_cache import clan_cache
        
        # Get limit from query parameter, default to 3
        limit = request.args.get('limit', 3, type=int)
        
        # Get offset for randomization (0 = start, 1 = skip first 3, 2 = skip first 6, etc.)
        offset = request.args.get('offset', 0, type=int)
        
        # Check if we have products in cache
        cache_stats = clan_cache.get_cache_stats()
        product_count = cache_stats.get('products_count', 0)
        
        if product_count == 0:
            # No products in cache - trigger initial download
            logger.info("No products in cache, triggering initial catalog download...")
            download_result = clan_cache.download_full_catalog()
            
            if not download_result.get('success'):
                return jsonify({'error': 'Failed to download catalog', 'details': download_result.get('error')}), 500
            
            logger.info(f"Initial catalog download complete: {download_result.get('stored_count')} products")
        
        # Get random products from local cache (super fast!)
        cached_products = clan_cache.get_random_products(limit, offset)
        
        if not cached_products:
            return jsonify({'error': 'No products available in cache'}), 500
        
        # Extract SKUs for detailed data fetching
        skus = [product['sku'] for product in cached_products]
        
        # Fetch detailed data for selected products only
        detailed_products = clan_cache.get_products_with_detailed_data(skus)
        
        # Map to widget format
        widget_products = []
        for detailed_product in detailed_products:
            widget_product = {
                "id": detailed_product.get('id'),
                "name": detailed_product.get('name', 'Product Name'),
                "sku": detailed_product.get('sku', ''),
                "url": detailed_product.get('url', ''),
                "description": detailed_product.get('description'),
                "image_url": detailed_product.get('image_url', 'https://static.clan.com/media/catalog/product/cache/5/image/9df78eab33525d08d6e5fb8d27136e95/e/s/essential.jpg'),
                "price": detailed_product.get('price', '29.99')
            }
            widget_products.append(widget_product)
        
        logger.info(f"Widget loaded {len(widget_products)} products from local cache in ~0.001s")
        return jsonify(widget_products)
        
    except Exception as e:
        logger.error(f"Error in local widget products: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/clan/cache/refresh', methods=['POST'])
def refresh_clan_cache():
    """Manually refresh the clan.com cache."""
    try:
        stats = refresh_cache()
        return jsonify({
            'success': True,
            'message': 'Cache refreshed successfully',
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to refresh cache: {str(e)}'
        }), 500

@app.route('/api/clan/cache/stats')
def get_clan_cache_stats():
    """Get cache statistics."""
    try:
        stats = get_cache_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            'error': f'Failed to get cache stats: {str(e)}'
        }), 500

@app.route('/api/clan/cache/save-product', methods=['POST'])
def save_individual_product():
    """Save a single product to the cache database"""
    try:
        product_data = request.json
        if not product_data:
            return jsonify({'success': False, 'error': 'No product data provided'}), 400
        
        # Import clan_cache and save the product
        from clan_cache import ClanCache
        cache = ClanCache()
        
        # Save single product
        cache.store_single_product(product_data)
        
        return jsonify({'success': True, 'message': 'Product saved successfully'})
        
    except Exception as e:
        logger.error(f"Error saving individual product: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/publish/<int:post_id>', methods=['POST'])
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
        
        # Ensure created_at is handled properly
        if post.get('created_at') and not isinstance(post['created_at'], str):
            post['created_at'] = post['created_at'].isoformat() if hasattr(post['created_at'], 'isoformat') else str(post['created_at'])
        
        # Add header image if exists
        header_image_path = find_header_image(post_id)
        if header_image_path:
            with get_db_connection() as conn:
                cur = conn.cursor(row_factory=psycopg.rows.dict_row)
                cur.execute("""
                    SELECT header_image_caption, header_image_title, header_image_width, header_image_height,
                           cross_promotion_category_id, cross_promotion_category_title,
                           cross_promotion_product_id, cross_promotion_product_title,
                           cross_promotion_category_position, cross_promotion_product_position,
                           cross_promotion_category_widget_html, cross_promotion_product_widget_html
                    FROM post WHERE id = %s
                """, (post_id,))
                header_data = cur.fetchone()
                
                post['header_image'] = {
                    'path': header_image_path,
                    'alt_text': f"Header image for {post.get('title', 'this post')}",
                    'caption': header_data['header_image_caption'] if header_data else None,
                    'title': header_data['header_image_title'] if header_data else None,
                    'width': header_data['header_image_width'] if header_data else None,
                    'height': header_data['header_image_height'] if header_data else None
                }
                
                post['cross_promotion'] = {
                    'category_id': header_data['cross_promotion_category_id'] if header_data else None,
                    'category_title': header_data['cross_promotion_category_title'] if header_data else None,
                    'product_id': header_data['cross_promotion_product_id'] if header_data else None,
                    'product_title': header_data['cross_promotion_product_title'] if header_data else None,
                    'category_position': header_data.get('cross_promotion_category_position'),
                    'product_position': header_data.get('cross_promotion_product_position'),
                    'category_widget_html': header_data.get('cross_promotion_category_widget_html'),
                    'product_widget_html': header_data.get('cross_promotion_product_widget_html')
                }
        
        # Import publishing class
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

@app.route('/api/clan/catalog/download', methods=['POST'])
def download_catalog():
    """Manually trigger full catalog download from clan.com"""
    try:
        from clan_cache import clan_cache
        
        logger.info("Manual catalog download triggered")
        result = clan_cache.download_full_catalog()
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': result.get('message'),
                'total_downloaded': result.get('total_downloaded'),
                'stored_count': result.get('stored_count')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error')
            }), 500
            
    except Exception as e:
        logger.error(f"Error in manual catalog download: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clan/catalog/status')
def catalog_status():
    """Get catalog cache status and statistics"""
    try:
        from clan_cache import clan_cache
        
        stats = clan_cache.get_cache_stats()
        return jsonify({
            'success': True,
            'cache_stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting catalog status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clan/catalog/refresh-urls', methods=['POST'])
def refresh_product_urls():
    """Refresh product URLs from clan.com API to fix 404 links"""
    try:
        from clan_cache import clan_cache
        
        logger.info("Manual product URL refresh triggered")
        result = clan_cache.refresh_product_urls()
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': result.get('message'),
                'updated_count': result.get('updated_count')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error')
            }), 500
            
    except Exception as e:
        logger.error(f"Error in product URL refresh: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# =====================================================
# SOCIAL MEDIA API ENDPOINTS - NEW DATABASE SCHEMA
# =====================================================

@app.route('/api/social-media/platforms/<platform_name>', methods=['GET'])
def get_platform(platform_name):
    """Get platform information by name"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        cur.execute("""
            SELECT id, name, display_name, description, status, priority, 
                   website_url, api_documentation_url, logo_url, development_status,
                   is_featured, menu_priority, is_visible_in_ui, last_activity_at,
                   last_post_at, last_api_call_at, total_posts_count, 
                   success_rate_percentage, average_response_time_ms,
                   estimated_completion_date, actual_completion_date, development_notes,
                   created_at, updated_at
            FROM platforms 
            WHERE name = %s
        """, (platform_name,))
        
        platform = cur.fetchone()
        
        if not platform:
            return jsonify({'error': 'Platform not found'}), 404
        
        # Convert datetime objects to strings for JSON serialization
        platform_dict = dict(platform)
        for key, value in platform_dict.items():
            if hasattr(value, 'isoformat'):
                platform_dict[key] = value.isoformat()
        
        cur.close()
        conn.close()
        
        return jsonify(platform_dict)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/social-media/platforms/<int:platform_id>/capabilities', methods=['GET'])
def get_platform_capabilities(platform_id):
    """Get platform capabilities by platform ID"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        cur.execute("""
            SELECT id, capability_type, capability_name, capability_value, description,
                   unit, min_value, max_value, validation_rules, is_active, display_order,
                   created_at, updated_at
            FROM platform_capabilities 
            WHERE platform_id = %s AND is_active = true
            ORDER BY display_order, capability_type, capability_name
        """, (platform_id,))
        
        capabilities = cur.fetchall()
        
        # Convert datetime objects to strings for JSON serialization
        capabilities_list = []
        for cap in capabilities:
            cap_dict = dict(cap)
            for key, value in cap_dict.items():
                if hasattr(value, 'isoformat'):
                    cap_dict[key] = value.isoformat()
            capabilities_list.append(cap_dict)
        
        cur.close()
        conn.close()
        
        return jsonify(capabilities_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/social-media/channels', methods=['GET'])
def get_channels():
    """Get all channels with platform support information"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        cur.execute("""
            SELECT ct.id, ct.name, ct.display_name, ct.description, ct.content_type,
                   ct.media_support, ct.default_priority, ct.is_active, ct.display_order,
                   pcs.platform_id, pcs.is_supported, pcs.status, pcs.development_status,
                   pcs.priority, pcs.notes, pcs.estimated_completion_date, 
                   pcs.actual_completion_date, pcs.development_notes, pcs.last_activity_at,
                   cp.process_name, cp.display_name as process_display_name, 
                   cp.description as process_description, cp.development_status as process_development_status
            FROM channel_types ct
            LEFT JOIN platform_channel_support pcs ON ct.id = pcs.channel_type_id
            LEFT JOIN content_processes cp ON pcs.platform_id = cp.platform_id AND pcs.channel_type_id = cp.channel_type_id
            WHERE ct.is_active = true
            ORDER BY ct.display_order, ct.name
        """)
        
        channels = cur.fetchall()
        
        # Convert datetime objects to strings for JSON serialization
        channels_list = []
        for channel in channels:
            channel_dict = dict(channel)
            for key, value in channel_dict.items():
                if hasattr(value, 'isoformat'):
                    channel_dict[key] = value.isoformat()
            channels_list.append(channel_dict)
        
        cur.close()
        conn.close()
        
        return jsonify(channels_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/social-media/processes/<process_name>/config', methods=['GET'])
def get_process_config(process_name):
    """Get process configuration by process name"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        # First get the process details
        cur.execute("""
            SELECT cp.id, cp.process_name, cp.display_name, cp.description, 
                   cp.development_status, cp.priority, cp.is_active,
                   cp.platform_id, cp.channel_type_id,
                   p.name as platform_name, p.display_name as platform_display_name,
                   ct.name as channel_name, ct.display_name as channel_display_name
            FROM content_processes cp
            JOIN platforms p ON cp.platform_id = p.id
            JOIN channel_types ct ON cp.channel_type_id = ct.id
            WHERE cp.process_name = %s
        """, (process_name,))
        
        process = cur.fetchone()
        
        if not process:
            return jsonify({'error': 'Process not found'}), 404
        
        # Get process configurations
        cur.execute("""
            SELECT pc.id, pc.config_category, pc.config_key, pc.config_value, 
                   pc.description, pc.display_order, pc.is_active, pc.validation_rules,
                   cc.display_name as category_display_name, cc.color_theme, cc.icon_class
            FROM process_configurations pc
            JOIN config_categories cc ON pc.config_category = cc.name
            WHERE pc.process_id = %s AND pc.is_active = true
            ORDER BY pc.display_order, pc.config_category, pc.config_key
        """, (process['id'],))
        
        configs = cur.fetchall()
        
        # Get channel requirements
        cur.execute("""
            SELECT cr.id, cr.requirement_category, cr.requirement_key, cr.requirement_value,
                   cr.description, cr.is_required, cr.validation_rules, cr.unit,
                   cr.min_value, cr.max_value, cr.display_order, cr.is_active,
                   rc.display_name as category_display_name, rc.color_theme, rc.icon_class
            FROM channel_requirements cr
            JOIN requirement_categories rc ON cr.requirement_category = rc.name
            WHERE cr.platform_id = %s AND cr.channel_type_id = %s AND cr.is_active = true
            ORDER BY cr.display_order, cr.requirement_category, cr.requirement_key
        """, (process['platform_id'], process['channel_type_id']))
        
        requirements = cur.fetchall()
        
        # Convert datetime objects to strings for JSON serialization
        process_dict = dict(process)
        for key, value in process_dict.items():
            if hasattr(value, 'isoformat'):
                process_dict[key] = value.isoformat()
        
        configs_list = []
        for config in configs:
            config_dict = dict(config)
            for key, value in config_dict.items():
                if hasattr(value, 'isoformat'):
                    config_dict[key] = value.isoformat()
            configs_list.append(config_dict)
        
        requirements_list = []
        for req in requirements:
            req_dict = dict(req)
            for key, value in req_dict.items():
                if hasattr(value, 'isoformat'):
                    req_dict[key] = value.isoformat()
            requirements_list.append(req_dict)
        
        # Create a comprehensive response
        response = {
            'process': process_dict,
            'configurations': configs_list,
            'requirements': requirements_list
        }
        
        cur.close()
        conn.close()
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/social-media/platforms/<int:platform_id>/channels', methods=['GET'])
def get_platform_channels(platform_id):
    """Get all channels for a specific platform"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        cur.execute("""
            SELECT ct.id, ct.name, ct.display_name, ct.description, ct.content_type,
                   ct.media_support, ct.default_priority, ct.is_active, ct.display_order,
                   pcs.is_supported, pcs.status, pcs.development_status, pcs.priority,
                   pcs.notes, pcs.estimated_completion_date, pcs.actual_completion_date,
                   pcs.development_notes, pcs.last_activity_at,
                   cp.process_name, cp.display_name as process_display_name,
                   cp.description as process_description, cp.development_status as process_development_status
            FROM channel_types ct
            JOIN platform_channel_support pcs ON ct.id = pcs.channel_type_id
            LEFT JOIN content_processes cp ON pcs.platform_id = cp.platform_id AND pcs.channel_type_id = cp.channel_type_id
            WHERE pcs.platform_id = %s AND ct.is_active = true
            ORDER BY pcs.priority, ct.display_order
        """, (platform_id,))
        
        channels = cur.fetchall()
        
        # Convert datetime objects to strings for JSON serialization
        channels_list = []
        for channel in channels:
            channel_dict = dict(channel)
            for key, value in channel_dict.items():
                if hasattr(value, 'isoformat'):
                    channel_dict[key] = value.isoformat()
            channels_list.append(channel_dict)
        
        cur.close()
        conn.close()
        
        return jsonify(channels_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/social-media/platforms/<int:platform_id>/channels/<int:channel_id>/requirements', methods=['GET'])
def get_channel_requirements(platform_id, channel_id):
    """Get requirements for a specific channel on a specific platform"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        cur.execute("""
            SELECT cr.id, cr.requirement_category, cr.requirement_key, cr.requirement_value,
                   cr.description, cr.is_required, cr.validation_rules, cr.unit,
                   cr.min_value, cr.max_value, cr.display_order, cr.is_active,
                   cr.content_length, cr.final_instruction,
                   rc.display_name as category_display_name, rc.color_theme, rc.icon_class
            FROM channel_requirements cr
            JOIN requirement_categories rc ON cr.requirement_category = rc.name
            WHERE cr.platform_id = %s AND cr.channel_type_id = %s AND cr.is_active = true
            ORDER BY cr.display_order, cr.requirement_category, cr.requirement_key
        """, (platform_id, channel_id))
        
        requirements = cur.fetchall()
        
        # Convert datetime objects to strings for JSON serialization
        requirements_list = []
        for req in requirements:
            req_dict = dict(req)
            for key, value in req_dict.items():
                if hasattr(value, 'isoformat'):
                    req_dict[key] = value.isoformat()
            requirements_list.append(req_dict)
        
        cur.close()
        conn.close()
        
        return jsonify(requirements_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/social-media/platforms', methods=['GET'])
def get_all_platforms():
    """Get all platforms with basic information"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        cur.execute("""
            SELECT id, name, display_name, description, status, priority, 
                   development_status, is_featured, menu_priority, is_visible_in_ui,
                   last_activity_at, total_posts_count, success_rate_percentage,
                   created_at, updated_at
            FROM platforms 
            WHERE is_visible_in_ui = true
            ORDER BY priority, display_name
        """)
        
        platforms = cur.fetchall()
        
        # Convert datetime objects to strings for JSON serialization
        platforms_list = []
        for platform in platforms:
            platform_dict = dict(platform)
            for key, value in platform_dict.items():
                if hasattr(value, 'isoformat'):
                    platform_dict[key] = value.isoformat()
            platforms_list.append(platform_dict)
        
        cur.close()
        conn.close()
        
        return jsonify(platforms_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =====================================================
# ADVANCED UI & OPERATIONAL API ENDPOINTS - PHASE 4
# =====================================================

@app.route('/api/social-media/ui/sections', methods=['GET'])
def get_ui_sections():
    """Get UI sections with their display properties"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        cur.execute("""
            SELECT id, name, display_name, description, section_type, parent_section_id,
                   display_order, is_visible, is_collapsible, default_collapsed,
                   color_theme, icon_class, css_classes, created_at, updated_at
            FROM ui_sections 
            WHERE is_visible = true
            ORDER BY display_order, name
        """)
        
        sections = cur.fetchall()
        
        # Convert datetime objects to strings for JSON serialization
        sections_list = []
        for section in sections:
            section_dict = dict(section)
            for key, value in section_dict.items():
                if hasattr(value, 'isoformat'):
                    section_dict[key] = value.isoformat()
            sections_list.append(section_dict)
        
        cur.close()
        conn.close()
        
        return jsonify(sections_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/social-media/ui/menu-items', methods=['GET'])
def get_ui_menu_items():
    """Get UI menu items with navigation structure"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        cur.execute("""
            SELECT id, name, display_name, description, menu_type, parent_menu_id,
                   section_id, url_pattern, icon_class, display_order, is_visible,
                   is_active, requires_permission, badge_text, badge_color,
                   created_at, updated_at
            FROM ui_menu_items 
            WHERE is_visible = true AND is_active = true
            ORDER BY display_order, name
        """)
        
        menu_items = cur.fetchall()
        
        # Convert datetime objects to strings for JSON serialization
        menu_items_list = []
        for item in menu_items:
            item_dict = dict(item)
            for key, value in item_dict.items():
                if hasattr(value, 'isoformat'):
                    item_dict[key] = value.isoformat()
            menu_items_list.append(item_dict)
        
        cur.close()
        conn.close()
        
        return jsonify(menu_items_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/social-media/ui/display-rules', methods=['GET'])
def get_ui_display_rules():
    """Get UI display rules for conditional rendering"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        cur.execute("""
            SELECT id, rule_name, description, rule_type, target_type, target_id,
                   condition_expression, is_active, priority, created_at, updated_at
            FROM ui_display_rules 
            WHERE is_active = true
            ORDER BY priority DESC, rule_name
        """)
        
        rules = cur.fetchall()
        
        # Convert datetime objects to strings for JSON serialization
        rules_list = []
        for rule in rules:
            rule_dict = dict(rule)
            for key, value in rule_dict.items():
                if hasattr(value, 'isoformat'):
                    rule_dict[key] = value.isoformat()
            rules_list.append(rule_dict)
        
        cur.close()
        conn.close()
        
        return jsonify(rules_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/social-media/priorities', methods=['GET'])
def get_content_priorities():
    """Get content priority scores and factors"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        cur.execute("""
            SELECT id, content_type, content_id, priority_score, priority_factors,
                   last_calculated_at, next_calculation_at, calculation_version,
                   created_at, updated_at
            FROM content_priorities 
            ORDER BY priority_score DESC, last_calculated_at DESC
        """)
        
        priorities = cur.fetchall()
        
        # Convert datetime objects to strings for JSON serialization
        priorities_list = []
        for priority in priorities:
            priority_dict = dict(priority)
            for key, value in priority_dict.items():
                if hasattr(value, 'isoformat'):
                    priority_dict[key] = value.isoformat()
            priorities_list.append(priority_dict)
        
        cur.close()
        conn.close()
        
        return jsonify(priorities_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/social-media/priorities/factors', methods=['GET'])
def get_priority_factors():
    """Get priority calculation factors and weights"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        cur.execute("""
            SELECT id, factor_name, display_name, description, factor_type, weight,
                   calculation_formula, is_active, is_configurable, min_value,
                   max_value, default_value, unit, created_at, updated_at
            FROM priority_factors 
            WHERE is_active = true
            ORDER BY weight DESC, factor_name
        """)
        
        factors = cur.fetchall()
        
        # Convert datetime objects to strings for JSON serialization
        factors_list = []
        for factor in factors:
            factor_dict = dict(factor)
            for key, value in factor_dict.items():
                if hasattr(value, 'isoformat'):
                    factor_dict[key] = value.isoformat()
            factors_list.append(factor_dict)
        
        cur.close()
        conn.close()
        
        return jsonify(factors_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/social-media/ui/user-preferences/<int:user_id>', methods=['GET'])
def get_user_preferences(user_id):
    """Get user-specific UI preferences"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        cur.execute("""
            SELECT id, user_id, preference_key, preference_value, preference_type,
                   category, is_global, created_at, updated_at
            FROM ui_user_preferences 
            WHERE user_id = %s OR is_global = true
            ORDER BY category, preference_key
        """, (user_id,))
        
        preferences = cur.fetchall()
        
        # Convert datetime objects to strings for JSON serialization
        preferences_list = []
        for pref in preferences:
            pref_dict = dict(pref)
            for key, value in pref_dict.items():
                if hasattr(value, 'isoformat'):
                    pref_dict[key] = value.isoformat()
            preferences_list.append(pref_dict)
        
        cur.close()
        conn.close()
        
        return jsonify(preferences_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/social-media/ui/session-state/<session_id>', methods=['GET'])
def get_session_state(session_id):
    """Get session-specific UI state"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        cur.execute("""
            SELECT id, session_id, user_id, state_key, state_value, state_type,
                   expires_at, created_at, updated_at
            FROM ui_session_state 
            WHERE session_id = %s AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            ORDER BY state_key
        """, (session_id,))
        
        states = cur.fetchall()
        
        # Convert datetime objects to strings for JSON serialization
        states_list = []
        for state in states:
            state_dict = dict(state)
            for key, value in state_dict.items():
                if hasattr(value, 'isoformat'):
                    state_dict[key] = value.isoformat()
            states_list.append(state_dict)
        
        cur.close()
        conn.close()
        
        return jsonify(states_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/social-media/priorities/calculate', methods=['POST'])
def calculate_content_priorities():
    """Calculate and update content priority scores"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        # Get all priority factors
        cur.execute("""
            SELECT factor_name, weight, calculation_formula, is_active
            FROM priority_factors 
            WHERE is_active = true
            ORDER BY weight DESC
        """)
        
        factors = cur.fetchall()
        
        if not factors:
            return jsonify({'error': 'No priority factors found'}), 400
        
        # Get platforms to calculate priorities for
        cur.execute("""
            SELECT id, name, last_activity_at, total_posts_count, success_rate_percentage
            FROM platforms 
            WHERE is_visible_in_ui = true
        """)
        
        platforms = cur.fetchall()
        
        updated_count = 0
        
        for platform in platforms:
            # Calculate priority score based on factors
            priority_score = 0.0
            priority_factors = {}
            
            for factor in factors:
                factor_name = factor['factor_name']
                weight = float(factor['weight'])  # Convert decimal to float
                
                # Simple calculation based on factor type
                if factor_name == 'post_recency':
                    days_since = (datetime.now() - platform['last_activity_at']).days if platform['last_activity_at'] else 30
                    factor_score = max(0, 1.0 - (days_since / 30.0))
                elif factor_name == 'posting_frequency':
                    factor_score = min(1.0, platform['total_posts_count'] / 100.0)
                elif factor_name == 'success_rate':
                    factor_score = platform['success_rate_percentage'] / 100.0 if platform['success_rate_percentage'] else 0.5
                else:
                    factor_score = 0.5  # Default score
                
                priority_score += factor_score * weight
                priority_factors[factor_name] = factor_score
            
            # Normalize score to 0-1 range
            priority_score = min(1.0, max(0.0, priority_score))
            
            # Update or insert priority record
            cur.execute("""
                INSERT INTO content_priorities (content_type, content_id, priority_score, priority_factors, calculation_version)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (content_type, content_id) 
                DO UPDATE SET 
                    priority_score = EXCLUDED.priority_score,
                    priority_factors = EXCLUDED.priority_factors,
                    last_calculated_at = CURRENT_TIMESTAMP,
                    calculation_version = EXCLUDED.calculation_version
            """, ('platform', platform['id'], priority_score, json.dumps(priority_factors), '1.0'))
            
            updated_count += 1
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Updated priorities for {updated_count} platforms',
            'updated_count': updated_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =====================================================
# SOCIAL MEDIA SYNDICATION ROUTES
# =====================================================
# Facebook platform settings routes removed - will be reimplemented properly




# LLM Integration API Endpoints for Syndication

@app.route('/api/syndication/llm/providers')
def get_llm_providers():
    """Get available LLM providers for dropdown population."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            cur.execute("""
                SELECT id, name, type, description 
                FROM llm_provider 
                ORDER BY name
            """)
            providers = cur.fetchall()
            
            provider_list = []
            for provider in providers:
                provider_list.append({
                    'id': provider['id'],
                    'name': provider['name'],
                    'type': provider['type'],
                    'description': provider['description']
                })
            
            return jsonify({'providers': provider_list})
    except Exception as e:
        logger.error(f"Error fetching LLM providers: {e}")
        return jsonify({'error': 'Failed to fetch providers'}), 500

@app.route('/api/syndication/llm/models/<int:provider_id>')
def get_llm_models(provider_id):
    """Get available models for a specific provider."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            cur.execute("""
                SELECT id, name, description, strengths, weaknesses
                FROM llm_model 
                WHERE provider_id = %s 
                ORDER BY name
            """, (provider_id,))
            models = cur.fetchall()
            
            model_list = []
            for model in models:
                model_list.append({
                    'id': model['id'],
                    'name': model['name'],
                    'description': model['description'],
                    'strengths': model['strengths'],
                    'weaknesses': model['weaknesses']
                })
            
            return jsonify({'models': model_list})
    except Exception as e:
        logger.error(f"Error fetching LLM models: {e}")
        return jsonify({'error': 'Failed to fetch models'}), 500

@app.route('/api/syndication/llm/settings', methods=['GET'])
def get_llm_settings():
    """Get saved LLM settings for the current process."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            cur.execute("""
                SELECT config_key, config_value, config_category
                FROM process_configurations 
                WHERE process_id = 1 AND config_category = 'llm_settings'
            """)
            configs = cur.fetchall()
            
            settings = {}
            for config in configs:
                settings[config['config_key']] = {
                    'value': config['config_value'],
                    'category': config['config_category']
                }
            
            return jsonify({'settings': settings})
    except Exception as e:
        logger.error(f"Error fetching LLM settings: {e}")
        return jsonify({'error': 'Failed to fetch settings'}), 500

@app.route('/api/syndication/llm/settings', methods=['POST'])
def save_llm_settings():
    """Save LLM settings for the current process."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            for key, value in data.items():
                # Insert or update each setting
                cur.execute("""
                    INSERT INTO process_configurations (process_id, config_category, config_key, config_value)
                    VALUES (1, 'llm_settings', %s, %s)
                    ON CONFLICT (process_id, config_category, config_key) 
                    DO UPDATE SET config_value = EXCLUDED.config_value
                """, (key, value))
            
            conn.commit()
            return jsonify({'success': True, 'message': 'Settings saved successfully'})
    except Exception as e:
        logger.error(f"Error saving LLM settings: {e}")
        return jsonify({'error': 'Failed to save settings'}), 500

@app.route('/api/syndication/llm/execute', methods=['POST'])
def execute_llm_request():
    """Direct LLM execution for syndication using Ollama."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract LLM parameters
        provider = data.get('provider', 'ollama')
        model = data.get('model', 'llama3.1:70b')  # Default to user's preferred model
        prompt = data.get('prompt', '')
        temperature = float(data.get('temperature', 0.7))
        max_tokens = int(data.get('max_tokens', 1000))
        
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400
        
        # Ensure Ollama is running before starting
        if not ensure_ollama_running():
            return jsonify({
                'error': 'Failed to start Ollama service. Please ensure Ollama is installed and try again.'
            }), 500
        
        # Call Ollama directly
        import requests
        ollama_response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': model,
                'prompt': prompt,
                'options': {
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            },
            timeout=60
        )
        
        if ollama_response.status_code == 200:
            # Ollama returns streaming JSON lines, we need to parse them
            response_lines = ollama_response.text.strip().split('\n')
            generated_text = ""
            
            for line in response_lines:
                if line.strip():
                    try:
                        line_data = json.loads(line)
                        if 'response' in line_data:
                            generated_text += line_data['response']
                    except json.JSONDecodeError:
                        continue  # Skip malformed lines
            
            return jsonify({
                'output': generated_text,
                'result': generated_text,
                'status': 'success',
                'model_used': model,
                'tokens_generated': len(generated_text.split())
            })
        else:
            return jsonify({'error': f'Ollama error: {ollama_response.status_code}'}), ollama_response.status_code
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Ollama: {e}")
        return jsonify({'error': 'Failed to connect to Ollama'}), 500
    except Exception as e:
        logger.error(f"Error executing LLM request: {e}")
        return jsonify({'error': 'Failed to execute LLM request'}), 500

@app.route('/api/syndication/ollama/direct', methods=['POST'])
def direct_ollama_request():
    """NEW DIRECT OLLAMA ENDPOINT - bypasses old code completely."""
    import requests  # Import at top of function to avoid UnboundLocalError
    import time  # Import for sleep function in retry mechanism
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract LLM parameters
        provider = data.get('provider', 'ollama')
        model = data.get('model', 'mistral:latest')  # Changed from llama3.1:70b to mistral:latest for stability
        prompt = data.get('prompt', '')
        temperature = float(data.get('temperature', 0.7))
        max_tokens = int(data.get('max_tokens', 1000))
        
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400
        
        # Call Ollama directly
        # Note: requests import moved to top of function to avoid UnboundLocalError
        
        # Add better error handling and model validation
        logger.info(f"Making Ollama request to model: {model}")
        logger.info(f"Prompt length: {len(prompt)} characters")
        
        # Limit prompt length to prevent crashes (most models handle 4K tokens well)
        max_prompt_length = 4000  # Conservative limit
        if len(prompt) > max_prompt_length:
            logger.warning(f"Prompt too long ({len(prompt)} chars), truncating to {max_prompt_length}")
            prompt = prompt[:max_prompt_length] + "\n\n[Content truncated due to length]"
            logger.info(f"Truncated prompt length: {len(prompt)} characters")
        
        # First check if the model is available (with better error handling)
        available_models = []
        try:
            model_check = requests.get('http://localhost:11434/api/tags', timeout=5)  # Reduced timeout
            if model_check.status_code == 200:
                try:
                    available_models = [m['name'] for m in model_check.json().get('models', [])]
                    logger.info(f"Available models: {available_models}")
                except Exception as parse_error:
                    logger.warning(f"Failed to parse models response: {parse_error}")
                    available_models = []
            else:
                logger.warning(f"Model check returned status {model_check.status_code}")
                available_models = []
        except requests.exceptions.ConnectionError:
            logger.warning("Cannot connect to Ollama for model check - proceeding with default model")
            available_models = []
        except requests.exceptions.Timeout:
            logger.warning("Model check timed out - proceeding with default model")
            available_models = []
        except Exception as e:
            logger.warning(f"Error checking models: {e} - proceeding with default model")
            available_models = []
        
        # Always prefer smaller, more stable models to prevent crashes
        if available_models:
            # Prioritize smaller, more stable models
            stable_models = ['mistral:latest', 'llama3.1:8b', 'llama3:latest', 'llama3.2:latest']
            for stable_model in stable_models:
                if stable_model in available_models:
                    if model != stable_model:
                        logger.info(f"Switching from {model} to more stable model: {stable_model}")
                        model = stable_model
                    break
            else:
                # If no stable models available, use the requested one
                logger.warning(f"No stable models available, using requested: {model}")
        else:
            # If we can't check models, default to mistral:latest
            if model != 'mistral:latest':
                logger.info(f"Defaulting to stable model: mistral:latest")
                model = 'mistral:latest'
        
        # Make the actual request with retry mechanism
        max_retries = 2
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                logger.info(f"Attempting Ollama request (attempt {retry_count + 1}/{max_retries + 1})")
                ollama_response = requests.post(
                    'http://localhost:11434/api/generate',
                    json={
                        'model': model,
                        'prompt': prompt,
                        'options': {
                            'temperature': temperature,
                            'num_predict': max_tokens
                        }
                    },
                    timeout=120  # Increased timeout for large models
                )
                break  # Success, exit retry loop
                
            except requests.exceptions.Timeout:
                logger.error(f"Ollama request timed out after 120 seconds (attempt {retry_count + 1})")
                if retry_count == max_retries:
                    return jsonify({'error': 'Ollama request timed out after multiple attempts. The model might be too large or the prompt too long.'}), 504
                retry_count += 1
                logger.info(f"Retrying in 2 seconds...")
                time.sleep(2)
                
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Ollama connection error (attempt {retry_count + 1}): {e}")
                if retry_count == max_retries:
                    # Try to restart Ollama automatically
                    logger.info("Attempting to restart Ollama automatically...")
                    try:
                        import subprocess
                        import os
                        import signal
                        
                        # Start Ollama in background
                        process = subprocess.Popen(
                            ['ollama', 'serve'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
                        )
                        
                        # Wait for Ollama to start
                        time.sleep(5)
                        
                        # Test if it's working
                        test_response = requests.get('http://localhost:11434/api/tags', timeout=10)
                        if test_response.status_code == 200:
                            logger.info("Ollama restarted successfully, retrying request...")
                            # Reset retry count and try again
                            retry_count = 0
                            max_retries = 1  # Give it one more try
                            time.sleep(2)
                            continue
                        else:
                            logger.error("Failed to restart Ollama automatically")
                            return jsonify({'error': f'Ollama connection error after multiple attempts: {str(e)}. Ollama may have crashed and could not be restarted automatically.'}), 500
                            
                    except Exception as restart_error:
                        logger.error(f"Failed to restart Ollama: {restart_error}")
                        return jsonify({'error': f'Ollama connection error after multiple attempts: {str(e)}. Ollama may have crashed and could not be restarted automatically.'}), 500
                
                retry_count += 1
                logger.info(f"Retrying in 2 seconds...")
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Unexpected error during Ollama request (attempt {retry_count + 1}): {e}")
                if retry_count == max_retries:
                    return jsonify({'error': f'Unexpected error after multiple attempts: {str(e)}'}), 500
                retry_count += 1
                logger.info(f"Retrying in 2 seconds...")
                time.sleep(2)
        
        logger.info(f"Ollama request successful after {retry_count + 1} attempts")
        
        if ollama_response.status_code == 200:
            # Ollama returns streaming JSON lines, we need to parse them
            response_lines = ollama_response.text.strip().split('\n')
            generated_text = ""
            
            for line in response_lines:
                if line.strip():
                    try:
                        line_data = json.loads(line)
                        if 'response' in line_data:
                            generated_text += line_data['response']
                    except json.JSONDecodeError:
                        continue  # Skip malformed lines
            
            return jsonify({
                'output': generated_text,
                'result': generated_text,
                'status': 'success',
                'model_used': model,
                'tokens_generated': len(generated_text.split())
            })
        else:
            return jsonify({'error': f'Ollama error: {ollama_response.status_code}'}), ollama_response.status_code
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Ollama: {e}")
        return jsonify({'error': f'Failed to connect to Ollama: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error executing LLM request: {e}")
        return jsonify({'error': f'Failed to execute LLM request: {str(e)}'}), 500

@app.route('/api/syndication/ollama/test', methods=['GET'])
def test_ollama_connection():
    """Simple test endpoint to check Ollama connectivity."""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=10)
        if response.status_code == 200:
            return jsonify({
                'status': 'success',
                'message': 'Ollama is accessible',
                'models': response.json().get('models', [])
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Ollama returned status {response.status_code}'
            }), 500
    except Exception as e:
        logger.error(f"Error testing Ollama connection: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to connect to Ollama: {str(e)}'
        }), 500

@app.route('/api/syndication/ollama/start', methods=['POST'])
def start_ollama():
    """Start Ollama as a background process."""
    try:
        import subprocess
        import os
        import signal
        import time
        
        # Check if Ollama is already running
        try:
            import requests
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            if response.status_code == 200:
                return jsonify({
                    'status': 'success',
                    'message': 'Ollama is already running',
                    'already_running': True
                })
        except:
            pass  # Ollama is not running, continue to start it
        
        # Start Ollama in the background
        try:
            # Use subprocess.Popen to start Ollama in background
            process = subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None
            )
            
            # Wait a moment for Ollama to start
            time.sleep(3)
            
            # Test if Ollama is now accessible
            try:
                response = requests.get('http://localhost:11434/api/tags', timeout=10)
                if response.status_code == 200:
                    return jsonify({
                        'status': 'success',
                        'message': 'Ollama started successfully',
                        'process_id': process.pid,
                        'already_running': False
                    })
                else:
                    # Kill the process if it didn't start properly
                    if hasattr(os, 'killpg'):
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    else:
                        process.terminate()
                    raise Exception(f'Ollama started but returned status {response.status_code}')
            except Exception as e:
                # Kill the process if connection test failed
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()
                raise Exception(f'Failed to connect to Ollama after starting: {str(e)}')
                
        except FileNotFoundError:
            return jsonify({
                'status': 'error',
                'message': 'Ollama command not found. Please ensure Ollama is installed and in your PATH.'
            }), 500
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Failed to start Ollama: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error starting Ollama: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error starting Ollama: {str(e)}'
        }), 500

@app.route('/api/syndication/pieces', methods=['GET', 'POST'])
def syndication_pieces():
    """Handle syndication pieces using existing llm_interaction table."""
    try:
        if request.method == 'POST':
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['post_id', 'section_id', 'platform_id', 'channel_type_id', 
                             'process_id', 'original_content', 'generated_content']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            with get_db_connection() as conn:
                cur = conn.cursor(row_factory=psycopg.rows.dict_row)
                
                # Use the existing llm_interaction table
                # Store metadata in interaction_metadata JSON field
                metadata = {
                    'post_id': str(data['post_id']),
                    'section_id': str(data['section_id']),
                    'platform_id': str(data['platform_id']),
                    'channel_type_id': str(data['channel_type_id']),
                    'process_id': str(data['process_id']),
                    'llm_model': str(data.get('llm_model', '')),
                    'llm_temperature': str(data.get('llm_temperature', '')),
                    'llm_max_tokens': str(data.get('llm_max_tokens', '')),
                    'llm_provider': str(data.get('llm_provider', '')),
                    'processing_time_ms': str(data.get('processing_time_ms', ''))
                }
                
                # Store parameters in parameters_used JSON field
                parameters = {
                    'platform': str(data.get('platform_name', 'Unknown')),
                    'channel_type': str(data.get('channel_type_name', 'Unknown')),
                    'requirements': str(data.get('requirements', '')),
                    'prompt_used': str(data.get('prompt_used', ''))
                }
                
                # Insert into llm_interaction table
                cur.execute("""
                    INSERT INTO llm_interaction (
                        prompt_id, input_text, output_text, parameters_used, interaction_metadata
                    ) VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    116,  # Social Media Syndication prompt ID
                    data['original_content'],
                    data['generated_content'],
                    json.dumps(parameters),
                    json.dumps(metadata)
                ))
                
                piece_id = cur.fetchone()['id']
                conn.commit()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Syndication piece saved successfully',
                    'piece_id': piece_id,
                    'action': 'created'
                })
        
        else:
            # GET request - retrieve pieces for a specific post
            post_id = request.args.get('post_id')
            if not post_id:
                return jsonify({'error': 'post_id parameter required'}), 400
            
            with get_db_connection() as conn:
                cur = conn.cursor(row_factory=psycopg.rows.dict_row)
                
                cur.execute("""
                    SELECT 
                        li.id,
                        li.input_text as original_content,
                        li.output_text as generated_content,
                        li.parameters_used,
                        li.interaction_metadata,
                        li.created_at,
                        lp.name as prompt_name,
                        lp.description as prompt_description
                    FROM llm_interaction li
                    JOIN llm_prompt lp ON li.prompt_id = lp.id
                    WHERE li.interaction_metadata->>'post_id' = %s
                    AND lp.name = 'Social Media Syndication'
                    ORDER BY li.created_at DESC
                """, (post_id,))
                
                pieces = []
                for row in cur.fetchall():
                    piece = dict(row)
                    # Parse JSON fields - check if they're strings first
                    if piece['parameters_used'] and isinstance(piece['parameters_used'], str):
                        try:
                            piece['parameters_used'] = json.loads(piece['parameters_used'])
                        except json.JSONDecodeError:
                            piece['parameters_used'] = {}
                    if piece['interaction_metadata'] and isinstance(piece['interaction_metadata'], str):
                        try:
                            piece['interaction_metadata'] = json.loads(piece['interaction_metadata'])
                        except json.JSONDecodeError:
                            piece['interaction_metadata'] = {}
                    pieces.append(piece)
                
                return jsonify({
                    'status': 'success',
                    'pieces': pieces
                })
                
    except Exception as e:
        logger.error(f"Error handling syndication pieces: {e}")
        return jsonify({'error': f'Failed to handle syndication pieces: {str(e)}'}), 500

@app.route('/api/syndication/pieces/<int:piece_id>', methods=['GET', 'PUT', 'DELETE'])
def syndication_piece(piece_id):
    """Handle individual syndication piece operations using existing llm_interaction table."""
    try:
        if request.method == 'GET':
            with get_db_connection() as conn:
                cur = conn.cursor(row_factory=psycopg.rows.dict_row)
                
                cur.execute("""
                    SELECT 
                        li.id,
                        li.input_text as original_content,
                        li.output_text as generated_content,
                        li.parameters_used,
                        li.interaction_metadata,
                        li.created_at,
                        lp.name as prompt_name,
                        lp.description as prompt_description
                    FROM llm_interaction li
                    JOIN llm_prompt lp ON li.prompt_id = lp.id
                    WHERE li.id = %s AND lp.name = 'Social Media Syndication'
                """, (piece_id,))
                
                piece = cur.fetchone()
                if not piece:
                    return jsonify({'error': 'Syndication piece not found'}), 404
                
                # Parse JSON fields
                if piece['parameters_used']:
                    piece['parameters_used'] = json.loads(piece['parameters_used'])
                if piece['interaction_metadata']:
                    piece['interaction_metadata'] = json.loads(piece['interaction_metadata'])
                
                return jsonify({
                    'status': 'success',
                    'piece': dict(piece)
                })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            with get_db_connection() as conn:
                cur = conn.cursor(row_factory=psycopg.rows.dict_row)
                
                # Update the piece - only output_text can be updated
                if 'generated_content' not in data:
                    return jsonify({'error': 'Only generated_content can be updated'}), 400
                
                cur.execute("""
                    UPDATE llm_interaction SET
                        output_text = %s
                    WHERE id = %s AND prompt_id = %s
                    RETURNING id
                """, (data['generated_content'], piece_id, 116))
                
                updated_piece = cur.fetchone()
                if not updated_piece:
                    return jsonify({'error': 'Syndication piece not found'}), 404
                
                conn.commit()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Syndication piece updated successfully',
                    'piece_id': piece_id
                })
        
        elif request.method == 'DELETE':
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                cur.execute("DELETE FROM llm_interaction WHERE id = %s AND prompt_id = %s RETURNING id", (piece_id, 116))
                
                deleted_piece = cur.fetchone()
                if not deleted_piece:
                    return jsonify({'error': 'Syndication piece not found'}), 404
                
                conn.commit()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Syndication piece deleted successfully'
                })
                
    except Exception as e:
        logger.error(f"Error handling syndication piece {piece_id}: {e}")
        return jsonify({'error': f'Failed to handle syndication piece: {str(e)}'}), 500

@app.route('/api/daily-product-posts/update-products', methods=['POST'])
def update_products():
    """Check for and update products with changes from Clan.com API"""
    try:
        logger.info("Starting incremental product update...")
        
        # Import the update classes
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
        
        from update_product_images import ProductImageUpdater
        from update_product_categories import ProductCategoryUpdater
        from update_product_prices import ProductPriceUpdater
        
        stats = {
            'images_updated': 0,
            'categories_updated': 0,
            'prices_updated': 0,
            'total_products_checked': 0,
            'errors': []
        }
        
        # Check for products that need updates (older than 1 day or missing data)
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # Find products that need updates
            cur.execute("""
                SELECT sku, name, last_updated,
                       CASE WHEN image_url IS NULL OR image_url = '' THEN 1 ELSE 0 END as needs_image,
                       CASE WHEN category_ids IS NULL OR category_ids = '[]'::jsonb THEN 1 ELSE 0 END as needs_categories,
                       CASE WHEN price IS NULL OR price = '' OR price = '0.00' THEN 1 ELSE 0 END as needs_price
                FROM clan_products 
                WHERE last_updated < NOW() - INTERVAL '1 day' 
                   OR image_url IS NULL OR image_url = ''
                   OR category_ids IS NULL OR category_ids = '[]'::jsonb
                   OR price IS NULL OR price = '' OR price = '0.00'
                ORDER BY last_updated ASC
                LIMIT 50
            """)
            
            products_to_update = cur.fetchall()
            stats['total_products_checked'] = len(products_to_update)
            
            if not products_to_update:
                return jsonify({
                    'success': True,
                    'message': 'All products are up to date! No updates needed.',
                    'stats': stats
                })
            
            logger.info(f"Found {len(products_to_update)} products that need updates")
            
            # Update images if needed
            products_needing_images = [p for p in products_to_update if p['needs_image']]
            if products_needing_images:
                logger.info(f"Updating images for {len(products_needing_images)} products...")
                try:
                    image_updater = ProductImageUpdater()
                    # Get fresh data from API for these products
                    products_with_images = image_updater.fetch_products_by_sku([p['sku'] for p in products_needing_images])
                    if products_with_images:
                        image_stats = image_updater.update_product_images(products_with_images)
                        stats['images_updated'] = image_stats.get('successful_updates', 0)
                        stats['errors'].extend(image_stats.get('errors', []))
                except Exception as e:
                    logger.error(f"Error updating images: {e}")
                    stats['errors'].append(f"Image update error: {str(e)}")
            
            # Update categories if needed
            products_needing_categories = [p for p in products_to_update if p['needs_categories']]
            if products_needing_categories:
                logger.info(f"Updating categories for {len(products_needing_categories)} products...")
                try:
                    category_updater = ProductCategoryUpdater()
                    # Get fresh data from API for these products
                    products_with_categories = category_updater.fetch_products_by_sku([p['sku'] for p in products_needing_categories])
                    if products_with_categories:
                        category_stats = category_updater.update_product_categories(products_with_categories)
                        stats['categories_updated'] = category_stats.get('successful_updates', 0)
                        stats['errors'].extend(category_stats.get('errors', []))
                except Exception as e:
                    logger.error(f"Error updating categories: {e}")
                    stats['errors'].append(f"Category update error: {str(e)}")
            
            # Update prices if needed
            products_needing_prices = [p for p in products_to_update if p['needs_price']]
            if products_needing_prices:
                logger.info(f"Updating prices for {len(products_needing_prices)} products...")
                try:
                    price_updater = ProductPriceUpdater()
                    # Get fresh data from API for these products
                    products_with_prices = price_updater.fetch_products_by_sku([p['sku'] for p in products_needing_prices])
                    if products_with_prices:
                        price_stats = price_updater.update_product_prices(products_with_prices)
                        stats['prices_updated'] = price_stats.get('successful_updates', 0)
                        stats['errors'].extend(price_stats.get('errors', []))
                except Exception as e:
                    logger.error(f"Error updating prices: {e}")
                    stats['errors'].append(f"Price update error: {str(e)}")
        
        total_updates = stats['images_updated'] + stats['categories_updated'] + stats['prices_updated']
        
        if total_updates > 0:
            message = f"Successfully updated {total_updates} products: {stats['images_updated']} images, {stats['categories_updated']} categories, {stats['prices_updated']} prices"
        else:
            message = "No products needed updates, but checked for changes"
        
        if stats['errors']:
            message += f" (with {len(stats['errors'])} errors)"
        
        return jsonify({
            'success': True,
            'message': message,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error in update_products: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to update products: {str(e)}'
        }), 500

@app.route('/api/daily-product-posts/start-ollama', methods=['POST'])
def start_ollama_daily_posts():
    """Start the Ollama service for AI content generation."""
    try:
        import subprocess
        import os
        
        # Check if Ollama is already running
        try:
            result = subprocess.run(['pgrep', '-f', 'ollama'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return jsonify({
                    'success': True,
                    'message': 'Ollama is already running'
                })
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass
        
        # Start Ollama in the background
        try:
            # Try to start Ollama serve
            subprocess.Popen(['ollama', 'serve'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL,
                           preexec_fn=os.setsid if hasattr(os, 'setsid') else None)
            
            # Give it a moment to start
            import time
            time.sleep(2)
            
            # Verify it's running
            result = subprocess.run(['pgrep', '-f', 'ollama'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                return jsonify({
                    'success': True,
                    'message': 'Ollama service started successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to start Ollama service'
                })
                
        except FileNotFoundError:
            return jsonify({
                'success': False,
                'error': 'Ollama not found. Please install Ollama first.'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to start Ollama: {str(e)}'
            })
            
    except Exception as e:
        logger.error(f"Error starting Ollama: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to start Ollama: {str(e)}'
        }), 500

@app.route('/api/daily-product-posts/add-schedule', methods=['POST'])
def add_schedule():
    """Add a new posting schedule for daily product posts."""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        time = data.get('time', '17:00')
        timezone = data.get('timezone', 'GMT')
        days = data.get('days', [1,2,3,4,5])  # Default to weekdays
        
        # Validate input
        if not name:
            return jsonify({
                'success': False,
                'error': 'Schedule name is required'
            }), 400
            
        if not days or len(days) == 0:
            return jsonify({
                'success': False,
                'error': 'At least one day must be selected'
            }), 400
        
        # Store schedule in database
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Check if name already exists
            cur.execute("SELECT id FROM daily_posts_schedule WHERE name = %s AND is_active = true", (name,))
            if cur.fetchone():
                return jsonify({
                    'success': False,
                    'error': 'A schedule with this name already exists'
                }), 400
            
            # Create new schedule record
            cur.execute("""
                INSERT INTO daily_posts_schedule (name, time, timezone, days, is_active, display_order, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (name, time, timezone, json.dumps(days), True, 0))
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'Schedule "{name}" added successfully'
        })
        
    except Exception as e:
        logger.error(f"Error adding schedule: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to add schedule: {str(e)}'
        }), 500

@app.route('/api/daily-product-posts/set-schedule', methods=['POST'])
def set_schedule():
    """Set the posting schedule for daily product posts (legacy endpoint)."""
    try:
        data = request.get_json()
        time = data.get('time', '17:00')
        timezone = data.get('timezone', 'GMT')
        days = data.get('days', [1,2,3,4,5])  # Default to weekdays
        
        # Validate input
        if not days or len(days) == 0:
            return jsonify({
                'success': False,
                'error': 'At least one day must be selected'
            }), 400
        
        # Store schedule in database (using a simple approach for now)
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Create or update schedule record
            cur.execute("""
                INSERT INTO daily_posts_schedule (name, time, timezone, days, is_active, display_order, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (id) DO UPDATE SET
                    time = EXCLUDED.time,
                    timezone = EXCLUDED.timezone,
                    days = EXCLUDED.days,
                    is_active = EXCLUDED.is_active,
                    updated_at = NOW()
            """, ('Default Schedule', time, timezone, json.dumps(days), True, 0))
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'Schedule set for {len(days)} days at {time} {timezone}'
        })
        
    except Exception as e:
        logger.error(f"Error setting schedule: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to set schedule: {str(e)}'
        }), 500

@app.route('/api/daily-product-posts/clear-schedule', methods=['POST'])
def clear_schedule():
    """Clear the posting schedule for daily product posts."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Deactivate all schedules
            cur.execute("""
                UPDATE daily_posts_schedule 
                SET is_active = false, updated_at = NOW()
                WHERE is_active = true
            """)
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Schedule cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Error clearing schedule: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to clear schedule: {str(e)}'
        }), 500

@app.route('/api/daily-product-posts/schedule-status')
def get_schedule_status():
    """Get the current posting schedule status."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # Get active schedule
            cur.execute("""
                SELECT time, timezone, days, is_active, created_at, updated_at
                FROM daily_posts_schedule
                WHERE is_active = true
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            schedule = cur.fetchone()
            
            if schedule:
                return jsonify({
                    'success': True,
                    'schedule': {
                        'time': str(schedule['time']),
                        'timezone': schedule['timezone'],
                        'days': schedule['days'] if isinstance(schedule['days'], list) else json.loads(schedule['days']) if schedule['days'] else [],
                        'is_active': schedule['is_active'],
                        'created_at': schedule['created_at'].isoformat() if schedule['created_at'] else None,
                        'updated_at': schedule['updated_at'].isoformat() if schedule['updated_at'] else None
                    }
                })
            else:
                return jsonify({
                    'success': True,
                    'schedule': None
                })
        
    except Exception as e:
        logger.error(f"Error getting schedule status: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get schedule status: {str(e)}'
        }), 500

@app.route('/api/daily-product-posts/schedules')
def get_all_schedules():
    """Get all active posting schedules."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # Get all active schedules
            cur.execute("""
                SELECT id, name, time, timezone, days, is_active, created_at, updated_at
                FROM daily_posts_schedule
                WHERE is_active = true 
                AND platform = 'facebook' 
                AND channel_type = 'feed_post' 
                AND content_type = 'product'
                ORDER BY display_order ASC, created_at ASC
            """)
            
            schedules = cur.fetchall()
            
            # Convert to list of dictionaries
            schedule_list = []
            for schedule in schedules:
                schedule_list.append({
                    'id': schedule['id'],
                    'name': schedule['name'],
                    'time': str(schedule['time']),
                    'timezone': schedule['timezone'],
                    'days': schedule['days'] if isinstance(schedule['days'], list) else json.loads(schedule['days']) if schedule['days'] else [],
                    'is_active': schedule['is_active'],
                    'created_at': schedule['created_at'].isoformat() if schedule['created_at'] else None,
                    'updated_at': schedule['updated_at'].isoformat() if schedule['updated_at'] else None
                })
            
            return jsonify({
                'success': True,
                'schedules': schedule_list
            })
        
    except Exception as e:
        logger.error(f"Error getting schedules: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get schedules: {str(e)}'
        }), 500

@app.route('/api/daily-product-posts/delete-schedule/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Delete a specific posting schedule."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Check if schedule exists
            cur.execute("SELECT name FROM daily_posts_schedule WHERE id = %s", (schedule_id,))
            schedule = cur.fetchone()
            
            if not schedule:
                return jsonify({
                    'success': False,
                    'error': 'Schedule not found'
                }), 404
            
            # Delete the schedule
            cur.execute("DELETE FROM daily_posts_schedule WHERE id = %s", (schedule_id,))
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': f'Schedule "{schedule[0]}" deleted successfully'
            })
        
    except Exception as e:
        logger.error(f"Error deleting schedule: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to delete schedule: {str(e)}'
        }), 500

@app.route('/api/daily-product-posts/test-schedules')
def test_schedules():
    """Test all schedules and return a preview of next 7 days."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # Get all active schedules
            cur.execute("""
                SELECT name, time, timezone, days
                FROM daily_posts_schedule
                WHERE is_active = true
                ORDER BY display_order ASC, created_at ASC
            """)
            
            schedules = cur.fetchall()
            
            if not schedules:
                return jsonify({
                    'success': True,
                    'preview': 'No schedules active'
                })
            
            # Generate preview for next 7 days
            from datetime import datetime, timedelta
            now = datetime.now()
            preview_lines = []
            
            for i in range(7):
                date = now + timedelta(days=i)
                dayOfWeek = date.weekday() + 1  # Convert Monday=0 to Monday=1, Sunday=6 to Sunday=7
                dateStr = date.strftime('%m/%d/%Y')
                
                day_schedules = []
                for schedule in schedules:
                    days = schedule['days'] if isinstance(schedule['days'], list) else json.loads(schedule['days']) if schedule['days'] else []
                    if dayOfWeek in days:
                        time_formatted = str(schedule['time'])[:5]  # HH:MM format
                        day_schedules.append(f"{schedule['name']} at {time_formatted} {schedule['timezone']}")
                
                if day_schedules:
                    day_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][date.weekday()]
                    preview_lines.append(f"{day_name} {dateStr}: {', '.join(day_schedules)}")
            
            preview = '\n'.join(preview_lines) if preview_lines else 'No posts scheduled in the next 7 days'
            
            return jsonify({
                'success': True,
                'preview': preview
            })
        
    except Exception as e:
        logger.error(f"Error testing schedules: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to test schedules: {str(e)}'
        }), 500

# Queue Management API Endpoints
@app.route('/api/daily-product-posts/queue', methods=['GET'])
def get_queue():
    """Get all items in the posting queue."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("""
                SELECT pq.*, cp.name as product_name, cp.image_url as product_image, 
                       cp.sku, cp.price, cp.category_ids as categories
                FROM posting_queue pq
                LEFT JOIN clan_products cp ON pq.product_id = cp.id
                WHERE pq.platform = 'facebook' 
                AND pq.channel_type = 'feed_post' 
                AND pq.content_type = 'product'
                ORDER BY pq.scheduled_timestamp ASC, pq.created_at ASC
            """)
            
            items = cur.fetchall()
            
            queue_items = []
            for item in items:
                # Validate required fields - no fallbacks allowed
                if not item[8]:  # status
                    raise ValueError(f"Queue item {item[0]} is missing status information")
                if not item[11]:  # platform
                    raise ValueError(f"Queue item {item[0]} is missing platform information")
                if not item[12]:  # channel_type
                    raise ValueError(f"Queue item {item[0]} is missing channel_type information")
                if not item[13]:  # content_type
                    raise ValueError(f"Queue item {item[0]} is missing content_type information")
                
                queue_items.append({
                    'id': item[0],
                    'product_id': item[1],
                    'scheduled_date': item[2].isoformat() if item[2] else None,
                    'scheduled_time': str(item[3]) if item[3] else None,
                    'schedule_name': item[4],
                    'timezone': item[5],
                    'generated_content': item[6],
                    'queue_order': item[7],
                    'status': item[8],
                    'created_at': item[9].isoformat() if item[9] else None,
                    'updated_at': item[10].isoformat() if item[10] else None,
                    'platform': item[11],
                    'channel_type': item[12],
                    'content_type': item[13],
                    'scheduled_timestamp': item[14].isoformat() if item[14] else None,
                    'platform_post_id': item[15],
                    'error_message': item[16],
                    'product_name': item[17],
                    'product_image': item[18],
                    'sku': item[19],
                    'price': str(item[20]) if item[20] else None,
                    'categories': item[21] if item[21] else []
                })
            
            return jsonify({
                'success': True,
                'queue_items': queue_items
            })
        
    except Exception as e:
        logger.error(f"Error getting queue: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get queue: {str(e)}'
        }), 500

@app.route('/api/daily-product-posts/queue', methods=['POST'])
def add_to_queue():
    """Add an item to the posting queue."""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        generated_content = data.get('generated_content')
        scheduled_date = data.get('scheduled_date')
        scheduled_time = data.get('scheduled_time')
        schedule_name = data.get('schedule_name')
        timezone = data.get('timezone')
        
        if not product_id or not generated_content:
            return jsonify({
                'success': False,
                'error': 'Product ID and generated content are required'
            }), 400
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Get next queue order
            cur.execute("SELECT COALESCE(MAX(queue_order), 0) + 1 FROM posting_queue")
            next_order = cur.fetchone()[0]
            
            # Calculate scheduled_timestamp if both date and time are provided
            scheduled_timestamp = None
            if scheduled_date and scheduled_time:
                from datetime import datetime
                try:
                    scheduled_timestamp = datetime.combine(scheduled_date, scheduled_time)
                except:
                    scheduled_timestamp = None
            
            # Insert new queue item - platform/channel/type come from daily-product-posts module context
            cur.execute("""
                INSERT INTO posting_queue 
                (product_id, scheduled_date, scheduled_time, schedule_name, timezone, 
                 generated_content, queue_order, status, platform, channel_type, content_type, scheduled_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'ready', 'facebook', 'feed_post', 'product', %s)
                RETURNING id, created_at
            """, (product_id, scheduled_date, scheduled_time, schedule_name, timezone, 
                  generated_content, next_order, scheduled_timestamp))
            
            result = cur.fetchone()
            queue_id = result[0]
            created_at = result[1]
            
            # Get product details
            cur.execute("""
                SELECT name, image_url, sku, price, category_ids
                FROM clan_products WHERE id = %s
            """, (product_id,))
            
            product = cur.fetchone()
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Item added to queue successfully',
                'queue_item': {
                    'id': queue_id,
                    'product_id': product_id,
                    'scheduled_date': scheduled_date,
                    'scheduled_time': scheduled_time,
                    'schedule_name': schedule_name,
                    'timezone': timezone,
                    'generated_content': generated_content,
                    'queue_order': next_order,
                    'status': 'ready',  # This will be the database default
                    'created_at': created_at.isoformat(),
                    'updated_at': created_at.isoformat(),
                    'product_name': product[0] if product else None,
                    'product_image': product[1] if product else None,
                    'sku': product[2] if product else None,
                    'price': str(product[3]) if product and product[3] else None,
                    'categories': product[4] if product and product[4] else []
                }
            })
        
    except Exception as e:
        logger.error(f"Error adding to queue: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to add to queue: {str(e)}'
        }), 500

@app.route('/api/daily-product-posts/queue/<int:item_id>', methods=['PUT'])
def update_queue_item(item_id):
    """Update a queue item's schedule information."""
    try:
        data = request.get_json()
        scheduled_date = data.get('scheduled_date')
        scheduled_time = data.get('scheduled_time')
        schedule_name = data.get('schedule_name')
        timezone = data.get('timezone')
        queue_order = data.get('queue_order')
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Check if item exists
            cur.execute("SELECT id FROM posting_queue WHERE id = %s", (item_id,))
            if not cur.fetchone():
                return jsonify({
                    'success': False,
                    'error': 'Queue item not found'
                }), 404
            
            # Update the item
            if queue_order is not None:
                cur.execute("""
                    UPDATE posting_queue 
                    SET scheduled_date = %s, scheduled_time = %s, schedule_name = %s, 
                        timezone = %s, queue_order = %s, updated_at = NOW()
                    WHERE id = %s
                """, (scheduled_date, scheduled_time, schedule_name, timezone, queue_order, item_id))
            else:
                cur.execute("""
                    UPDATE posting_queue 
                    SET scheduled_date = %s, scheduled_time = %s, schedule_name = %s, 
                        timezone = %s, updated_at = NOW()
                    WHERE id = %s
                """, (scheduled_date, scheduled_time, schedule_name, timezone, item_id))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Queue item updated successfully'
            })
        
    except Exception as e:
        logger.error(f"Error updating queue item: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to update queue item: {str(e)}'
        }), 500

@app.route('/api/daily-product-posts/queue/<int:item_id>', methods=['DELETE'])
def remove_from_queue(item_id):
    """Remove an item from the posting queue."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Check if item exists
            cur.execute("SELECT id FROM posting_queue WHERE id = %s", (item_id,))
            if not cur.fetchone():
                return jsonify({
                    'success': False,
                    'error': 'Queue item not found'
                }), 404
            
            # Delete the item
            cur.execute("DELETE FROM posting_queue WHERE id = %s", (item_id,))
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Item removed from queue successfully'
            })
        
    except Exception as e:
        logger.error(f"Error removing from queue: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to remove from queue: {str(e)}'
        }), 500

@app.route('/api/daily-product-posts/queue/clear', methods=['DELETE'])
def clear_queue():
    """Clear all items from the posting queue."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Delete all items
            cur.execute("DELETE FROM posting_queue")
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Queue cleared successfully'
            })
        
    except Exception as e:
        logger.error(f"Error clearing queue: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to clear queue: {str(e)}'
        }), 500

@app.route('/api/daily-product-posts/generate-batch', methods=['POST'])
def generate_batch_items():
    """Generate multiple items for the posting queue automatically."""
    import time
    start_time = time.time()
    max_processing_time = 120  # 2 minutes max
    
    try:
        data = request.get_json()
        count = data.get('count', 10)
        
        if count < 1 or count > 50:
            return jsonify({
                'success': False,
                'error': 'Count must be between 1 and 50'
            }), 400
        
        # Ensure Ollama is running before starting
        if not ensure_ollama_running():
            return jsonify({
                'success': False,
                'error': 'Failed to start Ollama service. Please ensure Ollama is installed and try again.'
            }), 500
        
        generated_items = []
        errors = []
        
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # Get current queue count for scheduling
            cur.execute("SELECT COUNT(*) as count FROM posting_queue WHERE status = 'pending'")
            current_count = cur.fetchone()['count']
            
            # Get available content types
            cur.execute("SELECT id, template_name, content_type, template_prompt FROM product_content_templates WHERE is_active = true")
            content_types = cur.fetchall()
            
            if not content_types:
                return jsonify({
                    'success': False,
                    'error': 'No content templates available'
                }), 400
            
            # Generate items
            for i in range(count):
                # Check if we're running out of time
                if time.time() - start_time > max_processing_time:
                    logger.warning(f"Processing timeout reached after {i} items")
                    errors.append(f"Processing timeout reached after {i} items")
                    break
                    
                try:
                    # Select random product using existing logic
                    cur.execute("""
                        SELECT id, name, sku, price, description, image_url, url, category_ids
                        FROM clan_products
                        WHERE price IS NOT NULL AND price != ''
                        ORDER BY RANDOM()
                        LIMIT 100
                    """)
                    all_products = cur.fetchall()
                    
                    if not all_products:
                        errors.append(f"Item {i+1}: No products available")
                        continue
                    
                    # Category-first selection
                    category_ids = [20, 328, 18, 37, 19, 21, 100, 16]
                    import random
                    selected_category_id = random.choice(category_ids)
                    
                    # Filter products by selected category
                    matching_products = []
                    for product in all_products:
                        if product['category_ids'] and selected_category_id in product['category_ids']:
                            matching_products.append(product)
                    
                    # If no products found in this category, try other categories
                    if not matching_products:
                        for cat_id in category_ids:
                            if cat_id != selected_category_id:
                                for product in all_products:
                                    if product['category_ids'] and cat_id in product['category_ids']:
                                        matching_products.append(product)
                                        selected_category_id = cat_id
                                        break
                                if matching_products:
                                    break
                    
                    # If still no matches, just pick any product
                    if not matching_products:
                        selected_product = random.choice(all_products)
                    else:
                        selected_product = random.choice(matching_products)
                    
                    # Select random content type
                    content_type = random.choice(content_types)
                    logger.debug(f"Selected content type: {content_type}")
                    
                    # Generate content using Ollama - MUST succeed or skip this item
                    
                    # Prepare prompt with URL for call to action
                    try:
                        if not selected_product['description']:
                            raise ValueError(f"Product {selected_product['name']} has no description")
                        
                        prompt = content_type['template_prompt'].format(
                            product_name=selected_product['name'],
                            product_description=selected_product['description'],
                            product_url=selected_product['url']
                        )
                    except KeyError as e:
                        logger.error(f"Missing field in content_type for item {i+1}: {e}")
                        errors.append(f"Item {i+1}: Missing field in content_type - {str(e)}")
                        continue
                    except Exception as e:
                        logger.error(f"Error formatting prompt for item {i+1}: {e}")
                        errors.append(f"Item {i+1}: Error formatting prompt - {str(e)}")
                        continue
                    
                    # Call Ollama API - this MUST work or we skip this item
                    try:
                        ollama_response = requests.post('http://localhost:11434/api/generate', 
                            json={
                                'model': 'mistral',
                                'prompt': prompt,
                                'stream': False
                            },
                            timeout=10  # Reduced timeout to prevent browser timeout
                        )
                        
                        if ollama_response.status_code != 200:
                            logger.error(f"Ollama API returned status {ollama_response.status_code} for item {i+1}")
                            errors.append(f"Item {i+1}: Ollama API failed with status {ollama_response.status_code}")
                            continue
                            
                        generated_content = ollama_response.json().get('response', '').strip()
                        
                        if not generated_content or len(generated_content) < 10:
                            logger.error(f"Ollama returned empty or too short content for item {i+1}")
                            errors.append(f"Item {i+1}: Ollama returned empty content")
                            continue
                            
                    except requests.exceptions.ConnectionError:
                        logger.error(f"Cannot connect to Ollama for item {i+1} - is Ollama running?")
                        errors.append(f"Item {i+1}: Cannot connect to Ollama - please start Ollama first")
                        continue
                    except Exception as e:
                        logger.error(f"Ollama generation failed for item {i+1}: {e}")
                        errors.append(f"Item {i+1}: Ollama generation failed - {str(e)}")
                        continue
                    
                    # Calculate next available posting time
                    # Simple approach: spread items across next few days
                    from datetime import datetime, timedelta
                    base_date = datetime.now() + timedelta(days=1)  # Start tomorrow
                    item_date = base_date + timedelta(days=i // 3)  # 3 items per day
                    scheduled_date = item_date.strftime('%Y-%m-%d')
                    
                    # Distribute times throughout the day
                    time_slots = ['09:00:00', '13:00:00', '17:00:00']
                    scheduled_time = time_slots[i % 3]
                    
                    # Calculate scheduled_timestamp
                    from datetime import datetime
                    scheduled_timestamp = None
                    if scheduled_date and scheduled_time:
                        try:
                            scheduled_timestamp = datetime.combine(scheduled_date, datetime.strptime(scheduled_time, '%H:%M:%S').time())
                        except:
                            scheduled_timestamp = None
                    
                    # Add to queue - all items in queue are ready by definition
                    # Platform/channel/type come from daily-product-posts module context
                    cur.execute("""
                        INSERT INTO posting_queue 
                        (product_id, scheduled_date, scheduled_time, schedule_name, timezone, 
                         generated_content, queue_order, status, platform, channel_type, content_type, scheduled_timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'ready', 'facebook', 'feed_post', 'product', %s)
                        RETURNING id, created_at
                    """, (
                        selected_product['id'],
                        scheduled_date,
                        scheduled_time,
                        f"Auto-generated {content_type['template_name']}",
                        'GMT',  # Default timezone
                        generated_content,
                        current_count + i + 1,
                        scheduled_timestamp
                    ))
                    
                    result = cur.fetchone()
                    queue_id = result[0]
                    created_at = result[1]
                    
                    generated_items.append({
                        'product_name': selected_product['name'],
                        'content_type': content_type['template_name'],
                        'scheduled_date': scheduled_date,
                        'scheduled_time': scheduled_time
                    })
                    
                except Exception as e:
                    logger.error(f"Error generating item {i+1}: {e}")
                    errors.append(f"Item {i+1}: {str(e)}")
                    continue
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'generated_count': len(generated_items),
                'total_requested': count,
                'errors': errors,
                'items': generated_items
            })
        
    except Exception as e:
        logger.error(f"Error generating batch items: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to generate batch items: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port) 