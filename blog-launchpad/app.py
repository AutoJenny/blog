

from flask import Flask, render_template, jsonify, request, send_file, redirect
import requests
import os
import logging
from datetime import datetime
import pytz
from humanize import naturaltime
import psycopg2.extras

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
def get_db_conn():
    """Get database connection."""
    import psycopg2
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'blog'),
        user=os.getenv('DB_USER', 'nickfiddes'),
        password=os.getenv('DB_PASSWORD', '')
    )

@app.route('/')
def index():
    """Main launchpad page."""
    return render_template('index.html')

@app.route('/cross-promotion')
def cross_promotion():
    """Cross-promotion management page."""
    return render_template('cross_promotion.html')

@app.route('/publishing')
def publishing():
    """Publishing management page."""
    return render_template('publishing.html')

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
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
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
            'product_title': header_data['cross_promotion_product_title'] if header_data and header_data['cross_promotion_product_title'] else None
        }
    
    return render_template('post_preview.html', post=post, sections=sections)

def get_post_with_development(post_id):
    """Fetch post with development data."""
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get post data, alias post.id as post_id
        cur.execute("""
            SELECT p.id AS post_id, p.title, p.subtitle, p.created_at, p.updated_at, p.status, p.slug, p.summary, p.title_choices,
                   pd.idea_seed, pd.intro_blurb, pd.main_title
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
            return f"/static/content/posts/{post_id}/sections/{section_id}/optimized/{encoded_filename}"

    # 2. Fall back to raw directory if optimized is empty
    section_raw_path = os.path.join(blog_images_static, "content", "posts", str(post_id), "sections", str(section_id), "raw")
    if os.path.exists(section_raw_path):
        image_files = [f for f in os.listdir(section_raw_path)
                      if f.lower().endswith(image_extensions) and not f.startswith('.')]
        if image_files:
            image_filename = image_files[0]
            # URL-encode the filename to handle spaces and special characters
            encoded_filename = urllib.parse.quote(image_filename)
            return f"/static/content/posts/{post_id}/sections/{section_id}/raw/{encoded_filename}"

    return None

def get_post_sections_with_images(post_id):
    """Fetch sections with complete image metadata."""
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
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
                    'caption': section.get('image_captions'),
                    'title': section.get('image_title'),
                    'width': section.get('image_width'),
                    'height': section.get('image_height')
                }
            elif section.get('image_id'):
                # Fallback to legacy image_id system
                cur.execute("""
                    SELECT * FROM image WHERE id = %s
                """, (section['image_id'],))
                image = cur.fetchone()
                if image:
                    section_dict['image'] = dict(image)
            elif section.get('generated_image_url'):
                # Fallback to generated_image_url
                section_dict['image'] = {
                    'path': section['generated_image_url'],
                    'alt_text': section.get('image_captions') or 'Section image',
                    'caption': section.get('image_captions'),
                    'title': section.get('image_title'),
                    'width': section.get('image_width'),
                    'height': section.get('image_height')
                }
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
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT p.id, p.title, p.created_at, p.updated_at, p.status,
                   p.clan_post_id, p.clan_status, p.clan_last_attempt, p.clan_error, p.clan_uploaded_url,
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
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
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
    
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE post SET 
                cross_promotion_category_id = %s,
                cross_promotion_category_title = %s,
                cross_promotion_product_id = %s,
                cross_promotion_product_title = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            data.get('category_id'),
            data.get('category_title'),
            data.get('product_id'),
            data.get('product_title'),
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
            post['summary'] = post.get('intro_blurb', 'No summary available')
        
        # Ensure created_at is handled properly
        if post.get('created_at') and not isinstance(post['created_at'], str):
            post['created_at'] = post['created_at'].isoformat() if hasattr(post['created_at'], 'isoformat') else str(post['created_at'])
        
        # Add header image if exists
        header_image_path = find_header_image(post_id)
        if header_image_path:
            with get_db_conn() as conn:
                cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cur.execute("""
                    SELECT header_image_caption, header_image_title, header_image_width, header_image_height,
                           cross_promotion_category_id, cross_promotion_category_title,
                           cross_promotion_product_id, cross_promotion_product_title
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
                    'product_title': header_data['cross_promotion_product_title'] if header_data else None
                }
        
        # Import publishing function
        from clan_publisher import publish_to_clan
        
        # Debug: Log what we're about to send
        logger.info(f"=== FLASK ENDPOINT DEBUG ===")
        logger.info(f"Post data keys: {list(post.keys()) if post else 'NO POST'}")
        logger.info(f"Post title: {post.get('title', 'NO TITLE') if post else 'NO POST'}")
        logger.info(f"Number of sections: {len(sections) if sections else 0}")
        if sections:
            logger.info(f"Section IDs: {[s.get('id') for s in sections]}")
        
        # Attempt to publish
        result = publish_to_clan(post, sections)
        
        # Debug: Log the result
        logger.info(f"Publishing result: {result}")
        
        if result['success']:
            # Update database with clan post details
            with get_db_conn() as conn:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE post SET 
                        clan_post_id = %s,
                        clan_status = 'published',
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
            with get_db_conn() as conn:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE post SET 
                        clan_status = 'error',
                        clan_last_attempt = CURRENT_TIMESTAMP,
                        clan_error = %s
                    WHERE id = %s
                """, (result.get('error'), post_id))
                conn.commit()
            
            return jsonify({
                'success': False, 
                'error': result.get('error', 'Unknown error occurred')
            }), 500
        
    except Exception as e:
        # Update database with error
        with get_db_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE post SET 
                    clan_status = 'error',
                    clan_last_attempt = CURRENT_TIMESTAMP,
                    clan_error = %s
                WHERE id = %s
            """, (str(e), post_id))
            conn.commit()
        
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port) 