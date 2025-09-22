# blueprints/post_info.py
from flask import Blueprint, render_template, request, jsonify
import logging
import json
from datetime import datetime
from config.database import db_manager

bp = Blueprint('post_info', __name__)
logger = logging.getLogger(__name__)

# Custom Jinja filter to parse JSON
@bp.app_template_filter('from_json')
def from_json_filter(value):
    """Parse JSON string to Python object."""
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []

@bp.route('/')
def index():
    """Main page for post info microservice."""
    try:
        with db_manager.get_cursor() as cursor:
            # Get all posts
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post
                WHERE status != 'deleted'
                ORDER BY created_at DESC
            """)
            posts = cursor.fetchall()
            
            # Get post_development data for the first post (default post_id=1)
            default_post_id = 1
            if posts:
                default_post_id = posts[0]['id']
            
            cursor.execute("""
                SELECT *
                FROM post_development
                WHERE post_id = %s
            """, (default_post_id,))
            post_development = cursor.fetchone()
            
            return render_template('post_info/index.html', 
                                 posts=posts, 
                                 selected_post_id=default_post_id,
                                 post_development=post_development)
            
    except Exception as e:
        logger.error(f"Error loading index page: {str(e)}")
        return render_template('post_info/index.html', 
                             posts=[], 
                             selected_post_id=1,
                             post_development=None,
                             error=str(e))

@bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'post-info',
        'timestamp': datetime.now().isoformat()
    })

@bp.route('/api/post-info/<int:post_id>', methods=['GET'])
def get_post_info(post_id):
    """Get post metadata for a specific post."""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post basic info
            cursor.execute("""
                SELECT p.id, p.title, p.summary, p.created_at, p.updated_at, p.status
                FROM post p
                WHERE p.id = %s
            """, (post_id,))
            
            post = cursor.fetchone()
            if not post:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get post development metadata
            cursor.execute("""
                SELECT main_title, subtitle, intro_blurb, basic_metadata, tags, categories, seo_optimization
                FROM post_development
                WHERE post_id = %s
            """, (post_id,))
            
            development = cursor.fetchone()
            
            # Combine the data
            post_info = dict(post)
            if development:
                post_info.update(dict(development))
            
            return jsonify(post_info)
            
    except Exception as e:
        logger.error(f"Error getting post info: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/api/post-info/<int:post_id>', methods=['PUT'])
def update_post_info(post_id):
    """Update post metadata for a specific post."""
    try:
        data = request.get_json()
        
        # Separate fields by table
        post_fields = {}
        development_fields = {}
        
        # Map fields to appropriate tables
        field_mapping = {
            'title': 'post',
            'summary': 'post',
            'status': 'post',
            'main_title': 'development',
            'subtitle': 'development',
            'intro_blurb': 'development',
            'basic_metadata': 'development',
            'tags': 'development',
            'categories': 'development',
            'seo_optimization': 'development'
        }
        
        for field, value in data.items():
            if field in field_mapping:
                if field_mapping[field] == 'post':
                    post_fields[field] = value
                else:
                    development_fields[field] = value
        
        with db_manager.get_cursor() as cursor:
            # Update post table if there are post fields
            if post_fields:
                update_fields = []
                update_values = []
                
                for field, value in post_fields.items():
                    update_fields.append(f"{field} = %s")
                    update_values.append(value)
                
                update_values.append(post_id)
                cursor.execute(f"""
                    UPDATE post
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                """, update_values)
            
            # Update post_development table if there are development fields
            if development_fields:
                # Check if post_development record exists
                cursor.execute("""
                    SELECT id FROM post_development WHERE post_id = %s
                """, (post_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing record
                    update_fields = []
                    update_values = []
                    
                    for field, value in development_fields.items():
                        update_fields.append(f"{field} = %s")
                        update_values.append(value)
                    
                    update_values.append(post_id)
                    cursor.execute(f"""
                        UPDATE post_development
                        SET {', '.join(update_fields)}
                        WHERE post_id = %s
                    """, update_values)
                else:
                    # Create new record
                    fields = list(development_fields.keys())
                    values = list(development_fields.values())
                    fields.append('post_id')
                    values.append(post_id)
                    
                    placeholders = ', '.join(['%s'] * len(fields))
                    field_names = ', '.join(fields)
                    
                    cursor.execute(f"""
                        INSERT INTO post_development ({field_names})
                        VALUES ({placeholders})
                    """, values)
            
            return jsonify({
                'success': True,
                'message': 'Post info updated successfully'
            })
            
    except Exception as e:
        logger.error(f"Error updating post info: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/api/post-info/<int:post_id>/seo', methods=['GET'])
def get_post_seo(post_id):
    """Get SEO-specific metadata for a post."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT seo_optimization, basic_metadata
                FROM post_development
                WHERE post_id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'Post not found'}), 404
            
            seo_data = {}
            if result['seo_optimization']:
                try:
                    seo_data = json.loads(result['seo_optimization']) if isinstance(result['seo_optimization'], str) else result['seo_optimization']
                except json.JSONDecodeError:
                    seo_data = {}
            
            if result['basic_metadata']:
                try:
                    basic_metadata = json.loads(result['basic_metadata']) if isinstance(result['basic_metadata'], str) else result['basic_metadata']
                    seo_data.update(basic_metadata)
                except json.JSONDecodeError:
                    pass
            
            return jsonify(seo_data)
            
    except Exception as e:
        logger.error(f"Error getting post SEO: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/api/post-info/<int:post_id>/seo', methods=['PUT'])
def update_post_seo(post_id):
    """Update SEO metadata for a post."""
    try:
        data = request.get_json()
        
        with db_manager.get_cursor() as cursor:
            # Check if post_development record exists
            cursor.execute("""
                SELECT id FROM post_development WHERE post_id = %s
            """, (post_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE post_development
                    SET seo_optimization = %s
                    WHERE post_id = %s
                """, (json.dumps(data), post_id))
            else:
                # Create new record
                cursor.execute("""
                    INSERT INTO post_development (post_id, seo_optimization)
                    VALUES (%s, %s)
                """, (post_id, json.dumps(data)))
            
            return jsonify({
                'success': True,
                'message': 'SEO metadata updated successfully'
            })
            
    except Exception as e:
        logger.error(f"Error updating post SEO: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/api/post-info', methods=['GET'])
def list_posts_info():
    """Get basic info for all posts."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.summary, p.created_at, p.updated_at, p.status,
                       pd.main_title, pd.subtitle, pd.intro_blurb, pd.tags, pd.categories
                FROM post p
                LEFT JOIN post_development pd ON pd.post_id = p.id
                WHERE p.status != 'deleted'
                ORDER BY p.created_at DESC
            """)
            
            posts = [dict(row) for row in cursor.fetchall()]
            return jsonify(posts)
            
    except Exception as e:
        logger.error(f"Error listing posts info: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/test')
def test():
    """Test endpoint"""
    return jsonify({'status': 'ok', 'message': 'Post info service is working'})