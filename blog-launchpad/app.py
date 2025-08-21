

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
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
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

@app.route('/syndication')
def syndication():
    """Social Media Syndication homepage."""
    return render_template('syndication.html')

@app.route('/syndication/select-posts')
def syndication_select_posts():
    """Select Posts for syndication."""
    return render_template('syndication_select_posts.html')

@app.route('/syndication/platform-settings')
def syndication_platform_settings():
    """Platform Settings for syndication."""
    return render_template('syndication_platform_settings.html')

@app.route('/syndication/platform-settings/<platform>')
def syndication_platform_detail(platform):
    """Individual platform settings page."""
    try:
        from models.social_media import SocialMediaPlatform
        
        # Database configuration
        db_config = {
            'host': 'localhost',
            'database': 'blog',
            'user': 'nickfiddes',
            'password': 'password',
            'port': '5432'
        }
        
        # Get platform data with specifications
        platform_model = SocialMediaPlatform(db_config)
        platform_data = platform_model.get_platform_with_specs(platform)
        
        if not platform_data:
            # Fallback to basic data if platform not found
            platform_data = {
                'platform_name': platform,
                'display_name': platform.title(),
                'status': 'undeveloped',
                'specifications': {}
            }
        
        return render_template(f'syndication_platform_{platform}.html', platform=platform_data)
        
    except Exception as e:
        # Fallback to basic data if there's any error
        print(f"Error loading platform data: {e}")
        platform_data = {
            'platform_name': platform,
            'display_name': platform.title(),
            'status': 'undeveloped',
            'specifications': {}
        }
        return render_template(f'syndication_platform_{platform}.html', platform=platform_data)

@app.route('/syndication/create-piece')
def syndication_create_piece():
    """Create Piece page for social media syndication."""
    return render_template('syndication_create_piece.html')

# API endpoints for CRUD operations on social media specifications
@app.route('/api/social-media/specifications/update', methods=['POST'])
def update_specification():
    """Update a social media platform specification."""
    try:
        from models.social_media import SocialMediaSpecification
        
        data = request.get_json()
        spec_id = data.get('spec_id')
        category = data.get('category')
        key = data.get('key')
        value = data.get('value')
        
        if not all([spec_id, category, key, value]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Database configuration
        db_config = {
            'host': 'localhost',
            'database': 'blog',
            'user': 'nickfiddes',
            'password': 'password',
            'port': '5432'
        }
        
        spec_model = SocialMediaSpecification(db_config)
        success = spec_model.update_specification_by_id(spec_id, value)
        
        if success:
            return jsonify({'message': 'Specification updated successfully'})
        else:
            return jsonify({'error': 'Failed to update specification'}), 500
            
    except Exception as e:
        print(f"Error updating specification: {e}")
        return jsonify({'error': str(e)}), 500



@app.route('/api/social-media/specifications/delete', methods=['DELETE'])
def delete_specification():
    """Delete a social media platform specification."""
    try:
        from models.social_media import SocialMediaSpecification
        
        data = request.get_json()
        spec_id = data.get('spec_id')
        
        if not spec_id:
            return jsonify({'error': 'Missing specification ID'}), 400
        
        # Database configuration
        db_config = {
            'host': 'localhost',
            'database': 'blog',
            'user': 'nickfiddes',
            'password': 'password',
            'port': '5432'
        }
        
        spec_model = SocialMediaSpecification(db_config)
        success = spec_model.delete_specification(spec_id)
        
        if success:
            return jsonify({'message': 'Specification deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete specification'}), 500
            
    except Exception as e:
        print(f"Error deleting specification: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/syndication/published-posts')
def get_published_posts():
    """Get all posts with status=published for syndication."""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        # Database connection
        conn = psycopg2.connect(
            host="localhost",
            database="blog",
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
                COUNT(ps.id) as section_count
            FROM post p
            LEFT JOIN post_section ps ON p.id = ps.post_id
            WHERE p.status = 'published'
            GROUP BY p.id, p.title, p.status, p.created_at, p.updated_at, p.slug
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
                'section_count': post['section_count']
            })
        
        cursor.close()
        conn.close()
        
        return {'posts': posts_list}
        
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
            'product_title': header_data['cross_promotion_product_title'] if header_data and header_data['cross_promotion_product_title'] else None,
            'category_position': header_data.get('cross_promotion_category_position'),
            'product_position': header_data.get('cross_promotion_product_position')
        }
    
    return render_template('post_preview.html', post=post, sections=sections)

@app.route('/clan-post-html/<int:post_id>')
def clan_post_html(post_id):
    """View the clan_post HTML that will be uploaded to Clan.com."""
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
                       cross_promotion_product_id, cross_promotion_product_title,
                       cross_promotion_category_position, cross_promotion_product_position,
                       cross_promotion_category_widget_html, cross_promotion_product_widget_html
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
            'product_title': header_data['cross_promotion_product_title'] if header_data and header_data['cross_promotion_product_id'] else None,
            'category_position': header_data.get('cross_promotion_category_position'),
            'product_position': header_data.get('cross_promotion_product_position'),
            'category_widget_html': header_data.get('cross_promotion_category_widget_html'),
            'product_widget_html': header_data.get('cross_promotion_product_widget_html')
        }
    
    # Generate the actual HTML that will be uploaded to clan.com
    # This should match exactly what the upload script uses
    from clan_publisher import ClanPublisher
    publisher = ClanPublisher()
    
    # Get the exact same HTML that gets uploaded
    upload_html = publisher.get_preview_html_content(post, sections)
    
    if upload_html:
        # Return the actual upload HTML as raw text - NO RENDERING
        # Set content type to text/plain so browser shows source code
        return upload_html, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    else:
        # Fallback to raw template if preview HTML fails
        raw_html = render_template('clan_post_raw.html', post=post, sections=sections)
        return raw_html, 200, {'Content-Type': 'text/plain; charset=utf-8'}

def get_post_with_development(post_id):
    """Fetch post with development data."""
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get post data, alias post.id as post_id
        cur.execute("""
            SELECT p.id AS post_id, p.title, p.subtitle, p.created_at, p.updated_at, p.status, p.slug, p.summary, p.title_choices,
                   p.clan_post_id, p.clan_uploaded_url,
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
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
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
    
    # Generate the actual widget HTML
    category_widget_html = None
    product_widget_html = None
    
    if data.get('category_id') and data.get('category_position'):
        category_widget_html = f'{{{{widget type="swcatalog/widget_crossSell_category" category_id="{data.get("category_id")}" title="{data.get("category_title") or "Related Department"}"}}}}'
    
    if data.get('product_id') and data.get('product_position'):
        product_widget_html = f'{{{{widget type="swcatalog/widget_crossSell_product" product_id="{data.get("product_id")}" title="{data.get("product_title") or "Related Products"}"}}}}'
    
    with get_db_conn() as conn:
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
                "name": detailed_product.get('name', 'Product Name'),
                "sku": detailed_product.get('sku', ''),
                "url": detailed_product.get('url', ''),
                "description": detailed_product.get('description', 'No description available'),
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
            with get_db_conn() as conn:
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
            with get_db_conn() as conn:
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
        with get_db_conn() as conn:
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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port) 