# blueprints/post_sections.py
from flask import Blueprint, render_template, request, jsonify, send_file
import logging
import os
from config.database import db_manager

bp = Blueprint('post_sections', __name__)
logger = logging.getLogger(__name__)

def find_section_image(post_id, section_id):
    """Find the first image for a section"""
    try:
        # Check for images in the blog-images directory
        image_path = f"static/content/posts/{post_id}/sections/{section_id}/raw"
        if os.path.exists(image_path):
            for filename in os.listdir(image_path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    return f"/post-sections/static/content/posts/{post_id}/sections/{section_id}/raw/{filename}"
        return None
    except Exception as e:
        logger.error(f"Error finding section image: {e}")
        return None

def get_sections(post_id):
    """Get all sections for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT ps.id, ps.title, ps.content, ps.section_order, ps.created_at, ps.updated_at
                FROM post_section ps
                WHERE ps.post_id = %s
                ORDER BY ps.section_order
            """, (post_id,))
            sections = cursor.fetchall()
            
            # Add image URLs to each section
            for section in sections:
                section['image_url'] = find_section_image(post_id, section['id'])
            
            return [dict(section) for section in sections]
    
    except Exception as e:
        logger.error(f"Error getting sections for post {post_id}: {e}")
        return []

@bp.route('/')
def index():
    """Main post sections interface with context support"""
    # Get query parameters for post context
    post_id = request.args.get('post_id')
    stage = request.args.get('stage')
    substage = request.args.get('substage')
    step = request.args.get('step')
    
    # If we have post context, render sections panel directly
    if post_id:
        return render_template('post_sections/sections_panel.html', 
                             post_id=post_id, 
                             stage=stage, 
                             substage=substage, 
                             step=step)
    
    # Otherwise redirect to sections
    return redirect(url_for('post_sections.sections_panel'))

@bp.route('/sections')
def sections_panel():
    """Sections panel interface"""
    post_id = request.args.get('post_id')
    stage = request.args.get('stage')
    substage = request.args.get('substage')
    step = request.args.get('step')
    
    # Check if this is for the section_illustrations step
    if step == 'section_illustrations':
        return render_template('post_sections/sections_panel_images.html',
                             post_id=post_id,
                             stage=stage,
                             substage=substage,
                             step=step)
    else:
        return render_template('post_sections/sections_panel.html',
                             post_id=post_id,
                             stage=stage,
                             substage=substage,
                             step=step)

@bp.route('/sections-summary')
def sections_summary():
    """Sections summary panel"""
    post_id = request.args.get('post_id')
    if not post_id:
        return '<div style="color:red;padding:1em;">Post ID required</div>', 400
    
    try:
        sections = get_sections(post_id)
        return render_template('post_sections/sections_summary.html', 
                             sections=sections, 
                             post_id=post_id)
    except Exception as e:
        return f'<div style="color:red;padding:1em;">Error loading sections: {e}</div>', 500

@bp.route('/sections-images')
def sections_panel_images():
    """Sections panel specifically for Image substage with image placeholders"""
    post_id = request.args.get('post_id')
    stage = request.args.get('stage')
    substage = request.args.get('substage')
    step = request.args.get('step')
    
    return render_template('post_sections/sections_panel_images.html',
                         post_id=post_id,
                         stage=stage,
                         substage=substage,
                         step=step)

@bp.route('/api/sections/<int:post_id>')
def get_sections_api(post_id):
    """Get sections for a post via API"""
    try:
        sections = get_sections(post_id)
        return jsonify(sections)
    except Exception as e:
        logger.error(f"Error getting sections for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/sections/<int:post_id>/<int:section_id>')
def get_section_api(post_id, section_id):
    """Get a specific section"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT ps.id, ps.title, ps.content, ps.section_order, ps.created_at, ps.updated_at
                FROM post_section ps
                WHERE ps.post_id = %s AND ps.id = %s
            """, (post_id, section_id))
            section = cursor.fetchone()
            
            if section:
                section_dict = dict(section)
                section_dict['image_url'] = find_section_image(post_id, section_id)
                return jsonify(section_dict)
            else:
                return jsonify({'error': 'Section not found'}), 404
    
    except Exception as e:
        logger.error(f"Error getting section {section_id} for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/sections', methods=['POST'])
def create_section():
    """Create a new section"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        title = data.get('title', '')
        content = data.get('content', '')
        
        if not post_id:
            return jsonify({'error': 'Post ID is required'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Get the next section order
            cursor.execute("""
                SELECT COALESCE(MAX(section_order), 0) + 1 as next_order
                FROM post_section
                WHERE post_id = %s
            """, (post_id,))
            next_order = cursor.fetchone()['next_order']
            
            # Create the section
            cursor.execute("""
                INSERT INTO post_section (post_id, title, content, section_order)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (post_id, title, content, next_order))
            
            section_id = cursor.fetchone()['id']
            
            return jsonify({
                'success': True,
                'section_id': section_id,
                'message': 'Section created successfully'
            })
    
    except Exception as e:
        logger.error(f"Error creating section: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/sections/<int:section_id>', methods=['PUT'])
def update_section(section_id):
    """Update a section"""
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        section_order = data.get('section_order')
        
        with db_manager.get_cursor() as cursor:
            # Build update query dynamically
            update_fields = []
            update_values = []
            
            if title is not None:
                update_fields.append("title = %s")
                update_values.append(title)
            
            if content is not None:
                update_fields.append("content = %s")
                update_values.append(content)
            
            if section_order is not None:
                update_fields.append("section_order = %s")
                update_values.append(section_order)
            
            if update_fields:
                update_values.append(section_id)
                cursor.execute(f"""
                    UPDATE post_section
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                """, update_values)
                
                return jsonify({
                    'success': True,
                    'message': 'Section updated successfully'
                })
            else:
                return jsonify({'error': 'No fields to update'}), 400
    
    except Exception as e:
        logger.error(f"Error updating section {section_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/sections/<int:section_id>', methods=['DELETE'])
def delete_section(section_id):
    """Delete a section"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("DELETE FROM post_section WHERE id = %s", (section_id,))
            
            return jsonify({
                'success': True,
                'message': 'Section deleted successfully'
            })
    
    except Exception as e:
        logger.error(f"Error deleting section {section_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/sections/<int:post_id>/sync', methods=['POST'])
def sync_sections(post_id):
    """Sync sections for a post"""
    try:
        # This would implement section synchronization logic
        # For now, just return success
        return jsonify({
            'success': True,
            'message': 'Sections synced successfully'
        })
    
    except Exception as e:
        logger.error(f"Error syncing sections for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/sections/<int:post_id>/reorder', methods=['POST'])
def reorder_sections(post_id):
    """Reorder sections for a post"""
    try:
        data = request.get_json()
        section_orders = data.get('section_orders', [])
        
        with db_manager.get_cursor() as cursor:
            for section_id, new_order in section_orders:
                cursor.execute("""
                    UPDATE post_section
                    SET section_order = %s
                    WHERE id = %s AND post_id = %s
                """, (new_order, section_id, post_id))
            
            return jsonify({
                'success': True,
                'message': 'Sections reordered successfully'
            })
    
    except Exception as e:
        logger.error(f"Error reordering sections for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/static/content/posts/<int:post_id>/sections/<int:section_id>/raw/<filename>')
def serve_section_image(post_id, section_id, filename):
    """Serve section images"""
    try:
        image_path = f"static/content/posts/{post_id}/sections/{section_id}/raw"
        return send_from_directory(image_path, filename)
    except Exception as e:
        logger.error(f"Error serving section image: {e}")
        return jsonify({'error': str(e)}), 404

@bp.route('/test')
def test():
    """Test endpoint"""
    return jsonify({'status': 'ok', 'message': 'Post sections service is working'})

@bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'post-sections'})