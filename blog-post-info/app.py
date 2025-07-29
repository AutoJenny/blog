from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import psycopg2
import psycopg2.extras
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Enable CORS for all routes
CORS(app, origins=["http://localhost:5000", "http://localhost:5001", "http://localhost:5002", "http://localhost:5003"])

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql://nickfiddes@localhost/blog')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom Jinja filter to parse JSON
@app.template_filter('from_json')
def from_json_filter(value):
    """Parse JSON string to Python object."""
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []

def get_db_conn():
    """Get database connection."""
    try:
        return psycopg2.connect(app.config['DATABASE_URL'])
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise



@app.route('/')
def index():
    """Main page for blog-post-info microservice."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get all posts
            cur.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post
                WHERE status != 'deleted'
                ORDER BY created_at DESC
            """)
            posts = cur.fetchall()
            
            # Get post_development data for the first post (default post_id=1)
            default_post_id = 1
            if posts:
                default_post_id = posts[0]['id']
            
            cur.execute("""
                SELECT *
                FROM post_development
                WHERE post_id = %s
            """, (default_post_id,))
            post_development = cur.fetchone()
            
            return render_template('index.html', 
                                 posts=posts, 
                                 selected_post_id=default_post_id,
                                 post_development=post_development)
            
    except Exception as e:
        logger.error(f"Error loading index page: {str(e)}")
        return render_template('index.html', 
                             posts=[], 
                             selected_post_id=1,
                             post_development=None,
                             error=str(e))

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'blog-post-info',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/post-info/<int:post_id>', methods=['GET'])
def get_post_info(post_id):
    """Get post metadata for a specific post."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get post basic info
            cur.execute("""
                SELECT p.id, p.title, p.summary, p.created_at, p.updated_at, p.status
                FROM post p
                WHERE p.id = %s
            """, (post_id,))
            
            post = cur.fetchone()
            if not post:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get post development metadata
            cur.execute("""
                SELECT main_title, subtitle, intro_blurb, basic_metadata, tags, categories, seo_optimization
                FROM post_development
                WHERE post_id = %s
            """, (post_id,))
            
            development = cur.fetchone()
            
            # Combine the data
            post_info = dict(post)
            if development:
                post_info.update(dict(development))
            
            return jsonify(post_info)
            
    except Exception as e:
        logger.error(f"Error getting post info: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/post-info/<int:post_id>', methods=['PUT'])
def update_post_info(post_id):
    """Update post metadata for a specific post."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Update post table fields
            post_fields = ['title', 'summary']
            post_updates = []
            post_values = []
            
            for field in post_fields:
                if field in data:
                    post_updates.append(f"{field} = %s")
                    post_values.append(data[field])
            
            if post_updates:
                post_values.append(post_id)
                cur.execute(f"""
                    UPDATE post 
                    SET {', '.join(post_updates)}, updated_at = NOW()
                    WHERE id = %s
                """, tuple(post_values))
            
            # Update post_development table fields
            dev_fields = ['main_title', 'subtitle', 'intro_blurb', 'basic_metadata', 'tags', 'categories', 'seo_optimization']
            dev_updates = []
            dev_values = []
            
            for field in dev_fields:
                if field in data:
                    dev_updates.append(f"{field} = %s")
                    dev_values.append(data[field])
            
            if dev_updates:
                # Check if post_development record exists
                cur.execute("SELECT id FROM post_development WHERE post_id = %s", (post_id,))
                exists = cur.fetchone()
                
                if exists:
                    dev_values.append(post_id)
                    cur.execute(f"""
                        UPDATE post_development 
                        SET {', '.join(dev_updates)}
                        WHERE post_id = %s
                    """, tuple(dev_values))
                else:
                    # Create new post_development record
                    dev_values.append(post_id)
                    cur.execute(f"""
                        INSERT INTO post_development (post_id, {', '.join(dev_fields)})
                        VALUES (%s, {', '.join(['%s'] * len(dev_fields))})
                    """, tuple(dev_values))
            
            conn.commit()
            
            return jsonify({'message': 'Post info updated successfully'})
            
    except Exception as e:
        logger.error(f"Error updating post info: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/post-info/<int:post_id>/seo', methods=['GET'])
def get_post_seo(post_id):
    """Get SEO-specific metadata for a post."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            cur.execute("""
                SELECT seo_optimization, tags, categories
                FROM post_development
                WHERE post_id = %s
            """, (post_id,))
            
            result = cur.fetchone()
            if not result:
                return jsonify({'error': 'Post not found'}), 404
            
            return jsonify(dict(result))
            
    except Exception as e:
        logger.error(f"Error getting post SEO: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/post-info/<int:post_id>/seo', methods=['PUT'])
def update_post_seo(post_id):
    """Update SEO-specific metadata for a post."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Check if post_development record exists
            cur.execute("SELECT id FROM post_development WHERE post_id = %s", (post_id,))
            exists = cur.fetchone()
            
            seo_fields = ['seo_optimization', 'tags', 'categories']
            updates = []
            values = []
            
            for field in seo_fields:
                if field in data:
                    updates.append(f"{field} = %s")
                    values.append(data[field])
            
            if not updates:
                return jsonify({'error': 'No SEO fields provided'}), 400
            
            if exists:
                values.append(post_id)
                cur.execute(f"""
                    UPDATE post_development 
                    SET {', '.join(updates)}
                    WHERE post_id = %s
                """, tuple(values))
            else:
                values.append(post_id)
                cur.execute(f"""
                    INSERT INTO post_development (post_id, {', '.join(seo_fields)})
                    VALUES (%s, {', '.join(['%s'] * len(seo_fields))})
                """, tuple(values))
            
            conn.commit()
            
            return jsonify({'message': 'SEO metadata updated successfully'})
            
    except Exception as e:
        logger.error(f"Error updating post SEO: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/post-info', methods=['GET'])
def list_posts_info():
    """Get basic info for all posts."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            cur.execute("""
                SELECT p.id, p.title, p.summary, p.created_at, p.updated_at, p.status,
                       pd.main_title, pd.subtitle, pd.intro_blurb, pd.tags, pd.categories
                FROM post p
                LEFT JOIN post_development pd ON pd.post_id = p.id
                WHERE p.status != 'deleted'
                ORDER BY p.created_at DESC
            """)
            
            posts = [dict(row) for row in cur.fetchall()]
            return jsonify(posts)
            
    except Exception as e:
        logger.error(f"Error listing posts info: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/test-headers')
def test_headers():
    """Test route for headers."""
    return jsonify({'message': 'Headers test route working', 'post_id': request.args.get('post_id')})

@app.route('/headers')
def headers_panel():
    """Headers panel for Post Info substage."""
    post_id = request.args.get('post_id', type=int)
    if not post_id:
        return jsonify({'error': 'Post ID required'}), 400
    
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get post header information including title_choices
            cur.execute("""
                SELECT p.title, p.summary, p.title_choices, p.subtitle,
                       pd.main_title, pd.subtitle as dev_subtitle, pd.intro_blurb
                FROM post p
                LEFT JOIN post_development pd ON pd.post_id = p.id
                WHERE p.id = %s
            """, (post_id,))
            
            post_data = cur.fetchone()
            if not post_data:
                return jsonify({'error': 'Post not found'}), 404
            
            return render_template('headers_panel.html', post=dict(post_data), post_id=post_id)
            
    except Exception as e:
        logger.error(f"Error getting headers: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/sections-summary')
def sections_summary_panel():
    post_id = request.args.get('post_id', type=int)
    if not post_id:
        return '<div style="color:red;padding:1em;">Post ID required</div>', 400
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT section_order, section_heading, section_description
                FROM post_section
                WHERE post_id = %s
                ORDER BY section_order
            """, (post_id,))
            sections = cur.fetchall()
        return render_template('sections_summary_panel.html', sections=sections, post_id=post_id)
    except Exception as e:
        return f'<div style="color:red;padding:1em;">Error loading sections: {e}</div>', 500



@app.route('/api/posts')
def get_posts_for_preview():
    """Get posts for preview dashboard."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            cur.execute("""
                SELECT p.id, p.title, p.summary, p.created_at, p.updated_at, p.status,
                       pd.main_title, pd.subtitle, pd.intro_blurb, pd.tags, pd.categories,
                       pd.idea_seed
                FROM post p
                LEFT JOIN post_development pd ON pd.post_id = p.id
                WHERE p.status != 'deleted'
                ORDER BY p.created_at DESC
            """)
            
            posts = [dict(row) for row in cur.fetchall()]
            return jsonify(posts)
            
    except Exception as e:
        logger.error(f"Error getting posts for preview: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/post/<int:post_id>', methods=['GET'])
def get_post_data(post_id):
    """Get post data for a specific post."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            cur.execute("""
                SELECT *
                FROM post
                WHERE id = %s
            """, (post_id,))
            
            post = cur.fetchone()
            if not post:
                return jsonify({'error': 'Post not found'}), 404
            
            return jsonify(dict(post))
            
    except Exception as e:
        logger.error(f"Error getting post data: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/post_development/<int:post_id>', methods=['GET'])
def get_post_development_data(post_id):
    """Get post_development data for a specific post."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            cur.execute("""
                SELECT *
                FROM post_development
                WHERE post_id = %s
            """, (post_id,))
            
            post_development = cur.fetchone()
            if not post_development:
                return jsonify({'error': 'Post development data not found'}), 404
            
            return jsonify(dict(post_development))
            
    except Exception as e:
        logger.error(f"Error getting post development data: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/titles-editor')
def titles_editor():
    """Titles editor page for managing post titles and subtitles."""
    post_id = request.args.get('post_id', type=int)
    if not post_id:
        return jsonify({'error': 'post_id parameter required'}), 400
    
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get PROVISIONAL_TITLE data from post_development
            cur.execute("""
                SELECT provisional_title
                FROM post_development
                WHERE post_id = %s
            """, (post_id,))
            
            result = cur.fetchone()
            if not result:
                return jsonify({'error': 'Post development data not found'}), 404
            
            provisional_title = result['provisional_title']
            
            # Parse the JSON data
            if provisional_title:
                try:
                    title_data = json.loads(provisional_title)
                    # Handle array of objects with title/subtitle properties
                    if isinstance(title_data, list):
                        titles = [item.get('title', '') for item in title_data if item.get('title')]
                        subtitles = [item.get('subtitle', '') for item in title_data if item.get('subtitle')]
                    else:
                        # Fallback for object format
                        titles = title_data.get('title', [])
                        subtitles = title_data.get('subtitle', [])
                except (json.JSONDecodeError, TypeError):
                    titles = []
                    subtitles = []
            else:
                titles = []
                subtitles = []
            
            return render_template('titles-editor.html', 
                                 post_id=post_id,
                                 titles=titles,
                                 subtitles=subtitles)
            
    except Exception as e:
        logger.error(f"Error loading titles editor: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/save-titles', methods=['POST'])
def save_titles():
    """Save selected title and subtitle to the post table."""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        title_index = data.get('title_index')
        subtitle_index = data.get('subtitle_index')
        
        if not post_id:
            return jsonify({'error': 'post_id required'}), 400
        
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get the provisional_title data to extract the selected values
            cur.execute("""
                SELECT provisional_title
                FROM post_development
                WHERE post_id = %s
            """, (post_id,))
            
            result = cur.fetchone()
            if not result:
                return jsonify({'error': 'Post development data not found'}), 404
            
            provisional_title = result['provisional_title']
            
            if provisional_title:
                try:
                    title_data = json.loads(provisional_title)
                    if isinstance(title_data, list):
                        selected_title = title_data[title_index].get('title', '') if title_index is not None and 0 <= title_index < len(title_data) else ''
                        selected_subtitle = title_data[subtitle_index].get('subtitle', '') if subtitle_index is not None and 0 <= subtitle_index < len(title_data) else ''
                    else:
                        selected_title = title_data.get('title', [''])[title_index] if title_index is not None else ''
                        selected_subtitle = title_data.get('subtitle', [''])[subtitle_index] if subtitle_index is not None else ''
                except (json.JSONDecodeError, TypeError, IndexError):
                    selected_title = ''
                    selected_subtitle = ''
            else:
                selected_title = ''
                selected_subtitle = ''
            
            # Update the post table with the selected title and subtitle
            cur.execute("""
                UPDATE post
                SET title = %s, subtitle = %s
                WHERE id = %s
            """, (selected_title, selected_subtitle, post_id))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Titles saved successfully',
                'title': selected_title,
                'subtitle': selected_subtitle
            })
            
    except Exception as e:
        logger.error(f"Error saving titles: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/get-current-titles/<int:post_id>', methods=['GET'])
def get_current_titles(post_id):
    """Get current title and subtitle from the post table."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get current title and subtitle from post table
            cur.execute("""
                SELECT title, subtitle
                FROM post
                WHERE id = %s
            """, (post_id,))
            
            post = cur.fetchone()
            if not post:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get provisional_title data to find the indices
            cur.execute("""
                SELECT provisional_title
                FROM post_development
                WHERE post_id = %s
            """, (post_id,))
            
            result = cur.fetchone()
            provisional_title = result['provisional_title'] if result else None
            
            title_index = None
            subtitle_index = None
            
            if provisional_title:
                try:
                    title_data = json.loads(provisional_title)
                    if isinstance(title_data, list):
                        # Find the index of the current title and subtitle
                        for i, item in enumerate(title_data):
                            if item.get('title') == post['title']:
                                title_index = i
                            if item.get('subtitle') == post['subtitle']:
                                subtitle_index = i
                except (json.JSONDecodeError, TypeError):
                    pass
            
            return jsonify({
                'title': post['title'],
                'subtitle': post['subtitle'],
                'title_index': title_index,
                'subtitle_index': subtitle_index
            })
            
    except Exception as e:
        logger.error(f"Error getting current titles: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5004))
    app.run(debug=True, host='0.0.0.0', port=port) 