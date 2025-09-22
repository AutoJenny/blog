# blueprints/images.py
from flask import Blueprint, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import logging
from config.database import db_manager

bp = Blueprint('images', __name__)
logger = logging.getLogger(__name__)

# Configure upload settings
UPLOAD_FOLDER = 'static/content/posts'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_upload_path(post_id, image_type, section_id=None):
    """Get the upload path for different image types"""
    base_path = os.path.join(UPLOAD_FOLDER, str(post_id))
    
    if image_type == 'header':
        return os.path.join(base_path, 'header', 'raw')
    elif image_type == 'featured':
        return os.path.join(base_path, 'featured', 'raw')
    elif image_type == 'section' and section_id:
        return os.path.join(base_path, 'sections', str(section_id), 'raw')
    else:
        return os.path.join(base_path, 'misc', 'raw')

@bp.route('/')
def index():
    """Main images interface with context support"""
    # Get context parameters from request
    post_id = request.args.get('post_id', '1')
    stage = request.args.get('stage', 'planning')
    substage = request.args.get('substage', 'idea')
    step = request.args.get('step', 'basic_idea')
    
    return render_template('images/index.html', 
                         post_id=post_id,
                         stage=stage,
                         substage=substage,
                         step=step)

@bp.route('/test')
def test():
    """Test endpoint"""
    return jsonify({'status': 'ok', 'message': 'Images service is working'})

@bp.route('/upload')
def upload():
    """Dedicated upload interface for workflow integration"""
    post_id = request.args.get('post_id', '1')
    section_id = request.args.get('section_id')
    image_type = request.args.get('image_type', 'section')
    
    return render_template('images/upload.html',
                         post_id=post_id,
                         section_id=section_id,
                         image_type=image_type)

@bp.route('/api/sections/<int:post_id>')
def get_sections(post_id):
    """Get sections for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, title, content, section_order
                FROM post_section
                WHERE post_id = %s
                ORDER BY section_order
            """, (post_id,))
            sections = cursor.fetchall()
            
            return jsonify([dict(section) for section in sections])
    
    except Exception as e:
        logger.error(f"Error getting sections for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/upload', methods=['POST'])
def upload_image():
    """Handle image upload for different image types"""
    try:
        post_id = request.form.get('post_id')
        section_id = request.form.get('section_id')
        image_type = request.form.get('image_type', 'section')  # Default to section for backward compatibility
        
        if not post_id:
            return jsonify({'error': 'Missing post_id'}), 400
        
        # Validate section_id for section uploads
        if image_type == 'section' and not section_id:
            return jsonify({'error': 'Missing section_id for section image uploads'}), 400
        
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'}), 400
        
        # Create directory if it doesn't exist
        upload_path = get_upload_path(post_id, image_type, section_id)
        os.makedirs(upload_path, exist_ok=True)
        
        # Save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'path': file_path,
            'image_type': image_type
        })
        
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/images/<int:post_id>/<int:section_id>')
def get_section_images(post_id, section_id):
    """Get list of images for a specific section"""
    try:
        images = []
        section_path = os.path.join(UPLOAD_FOLDER, str(post_id), 'sections', str(section_id), 'raw')
        
        if os.path.exists(section_path):
            for filename in os.listdir(section_path):
                if allowed_file(filename):
                    images.append({
                        'filename': filename,
                        'url': f'/images/static/content/posts/{post_id}/sections/{section_id}/raw/{filename}',
                        'path': os.path.join(section_path, filename)
                    })
        
        return jsonify(images)
    
    except Exception as e:
        logger.error(f"Error getting section images: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/static/content/posts/<int:post_id>/sections/<int:section_id>/raw/<filename>')
def serve_section_image(post_id, section_id, filename):
    """Serve section images"""
    try:
        section_path = os.path.join(UPLOAD_FOLDER, str(post_id), 'sections', str(section_id), 'raw')
        return send_from_directory(section_path, filename)
    except Exception as e:
        logger.error(f"Error serving section image: {e}")
        return jsonify({'error': str(e)}), 404

@bp.route('/api/images/<int:post_id>')
def get_all_images(post_id):
    """Get all images for a post across all types"""
    try:
        images = []
        
        # Check for header images
        header_path = os.path.join(UPLOAD_FOLDER, str(post_id), 'header', 'raw')
        if os.path.exists(header_path):
            for filename in os.listdir(header_path):
                if allowed_file(filename):
                    images.append({
                        'filename': filename,
                        'url': f'/images/static/content/posts/{post_id}/header/raw/{filename}',
                        'type': 'header',
                        'path': os.path.join(header_path, filename)
                    })
        
        # Check for featured images
        featured_path = os.path.join(UPLOAD_FOLDER, str(post_id), 'featured', 'raw')
        if os.path.exists(featured_path):
            for filename in os.listdir(featured_path):
                if allowed_file(filename):
                    images.append({
                        'filename': filename,
                        'url': f'/images/static/content/posts/{post_id}/featured/raw/{filename}',
                        'type': 'featured',
                        'path': os.path.join(featured_path, filename)
                    })
        
        # Check for section images
        sections_path = os.path.join(UPLOAD_FOLDER, str(post_id), 'sections')
        if os.path.exists(sections_path):
            for section_dir in os.listdir(sections_path):
                section_path = os.path.join(sections_path, section_dir, 'raw')
                if os.path.exists(section_path):
                    for filename in os.listdir(section_path):
                        if allowed_file(filename):
                            images.append({
                                'filename': filename,
                                'url': f'/images/static/content/posts/{post_id}/sections/{section_dir}/raw/{filename}',
                                'type': 'section',
                                'section_id': section_dir,
                                'path': os.path.join(section_path, filename)
                            })
        
        return jsonify(images)
    
    except Exception as e:
        logger.error(f"Error getting all images for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'images'})