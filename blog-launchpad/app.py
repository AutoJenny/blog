from flask import Flask, render_template, jsonify, request, send_file, redirect
import requests
import os
import logging
import json
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
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
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
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
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

@app.route('/syndication/facebook/feed-post')
def facebook_feed_post_config():
    """Facebook Feed Post channel configuration."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
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
            
            # Get Facebook Feed Post process data
            cur.execute("""
                SELECT 
                    cp.id, cp.process_name, cp.display_name, cp.description, 
                    cp.development_status, cp.priority, cp.is_active,
                    ct.name as channel_type_name, ct.display_name as channel_display_name
                FROM content_processes cp
                JOIN channel_types ct ON cp.channel_type_id = ct.id
                WHERE cp.platform_id = %s AND cp.process_name = 'facebook_feed_post'
            """, (platform['id'],))
            process = cur.fetchone()
            
            if not process:
                return "Facebook Feed Post process not found", 404
            
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
            
            # Get Facebook Feed Post requirements for MVP interface
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
            
            return render_template('facebook_feed_post_config.html',
                                platform=platform,
                                process=process,
                                configs_count=configs_count,
                                execution_data=execution_data,
                                requirements=requirements)
                                
    except Exception as e:
        logger.error(f"Error in facebook_feed_post_config: {e}")
        return f"Error loading configuration: {str(e)}", 500

@app.route('/syndication/select-posts')
def syndication_select_posts():
    """Select Posts for syndication."""
    return render_template('syndication_select_posts.html')

# Platform settings route removed - will be reimplemented properly

# Individual platform settings route removed - will be reimplemented properly

@app.route('/syndication/create-piece')
def syndication_create_piece():
    """Create Piece page for social media syndication."""
    return render_template('syndication_create_piece.html')

@app.route('/syndication/create-piece-includes')
def syndication_create_piece_includes():
    """Create Piece page for social media syndication (modular includes version)."""
    return render_template('syndication_create_piece_includes.html')

# Old social media specifications API endpoints removed - will be reimplemented properly

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

@app.route('/api/syndication/post-sections/<int:post_id>')
def get_post_sections(post_id):
    """Get all sections for a specific post."""
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

@app.route('/api/syndication/social-media-platforms')
def get_social_media_platforms():
    """Get only developed social media platforms for the dropdown selector."""
    try:
        from models.social_media import SocialMediaPlatform
        db_config = {'host': 'localhost', 'database': 'blog', 'user': 'postgres', 'password': 'postgres'}
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
        db_config = {'host': 'localhost', 'database': 'blog', 'user': 'postgres', 'password': 'postgres'}
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
        db_config = {'host': 'localhost', 'database': 'blog', 'user': 'postgres', 'password': 'postgres'}
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
        db_config = {'host': 'localhost', 'database': 'blog', 'user': 'postgres', 'password': 'postgres'}
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
        db_config = {'host': 'localhost', 'database': 'blog', 'user': 'postgres', 'password': 'postgres'}
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
        db_config = {'host': 'localhost', 'database': 'blog', 'user': 'postgres', 'password': 'postgres'}
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
            'product_title': header_data['cross_promotion_product_title'] if header_data and header_data['cross_promotion_product_title'] else None,
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

# =====================================================
# SOCIAL MEDIA API ENDPOINTS - NEW DATABASE SCHEMA
# =====================================================

@app.route('/api/social-media/platforms/<platform_name>', methods=['GET'])
def get_platform(platform_name):
    """Get platform information by name"""
    try:
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
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
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
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
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
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
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
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
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
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
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("""
            SELECT cr.id, cr.requirement_category, cr.requirement_key, cr.requirement_value,
                   cr.description, cr.is_required, cr.validation_rules, cr.unit,
                   cr.min_value, cr.max_value, cr.display_order, cr.is_active,
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
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
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
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
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
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
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
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
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
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
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
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
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
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
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
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
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
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
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

@app.route('/syndication/mvp-test')
def mvp_llm_test():
    """MVP LLM test interface for testing post rewriting using stored channel requirements."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get only the active Facebook Feed Post channel requirements
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
            
            return render_template('mvp_llm_test.html', requirements=requirements)
            
    except Exception as e:
        logger.error(f"Error in mvp_llm_test: {e}")
        return f"Error loading MVP test: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port) 