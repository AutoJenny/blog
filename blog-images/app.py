#!/usr/bin/env python3
"""
Blog Images - Image Generation and Management Application
"""

import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import requests
import psycopg2
import psycopg2.extras
from datetime import datetime

app = Flask(__name__)

# Configure port
port = int(os.environ.get('PORT', 5005))

# Configure upload settings
UPLOAD_FOLDER = 'static/content/posts'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Database connection function
def get_db_conn():
    """Get database connection."""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'blog'),
        user=os.getenv('DB_USER', 'nickfiddes'),
        password=os.getenv('DB_PASSWORD', '')
    )

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_section_images_path(post_id, section_id):
    """Get the path for section images"""
    return os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'sections', str(section_id), 'raw')

def get_upload_path(post_id, image_type, section_id=None):
    """Get upload path based on image type"""
    if image_type == 'header':
        return os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'raw')
    elif image_type == 'section':
        if not section_id:
            raise ValueError("section_id required for section image uploads")
        return os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'sections', str(section_id), 'raw')
    elif image_type == 'featured':
        return os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'featured', 'raw')
    else:
        # Default to section upload for backward compatibility
        if not section_id:
            raise ValueError("section_id required for section image uploads")
        return os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'sections', str(section_id), 'raw')

@app.route('/')
def index():
    post_id = request.args.get('post_id', '1')
    return render_template('index.html', post_id=post_id)

@app.route('/upload')
def upload():
    """Dedicated upload interface for workflow integration"""
    post_id = request.args.get('post_id', '1')
    return render_template('upload.html', post_id=post_id)

@app.route('/mockup')
def mockup():
    """Mockup of unified image processing interface"""
    return render_template('mockup.html')

@app.route('/api/sections/<int:post_id>')
def get_sections(post_id):
    """Get all sections for a post from database"""
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT id, section_heading, section_description, section_order, status
                    FROM post_section 
                    WHERE post_id = %s 
                    ORDER BY section_order
                """, (post_id,))
                sections = cur.fetchall()
                
                # Convert to list of dictionaries
                sections_list = []
                for section in sections:
                    sections_list.append({
                        'id': section['id'],
                        'section_heading': section['section_heading'],
                        'section_description': section['section_description'],
                        'section_order': section['section_order'],
                        'status': section['status']
                    })
                
                return jsonify({'sections': sections_list})
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
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
        return jsonify({'error': str(e)}), 500

@app.route('/api/images/<int:post_id>/<int:section_id>')
def get_section_images(post_id, section_id):
    """Get list of images for a specific section"""
    try:
        images_path = get_section_images_path(post_id, section_id)
        
        if not os.path.exists(images_path):
            return jsonify({'images': []})
        
        images = []
        for filename in os.listdir(images_path):
            if allowed_file(filename):
                images.append({
                    'filename': filename,
                    'url': f'/static/content/posts/{post_id}/sections/{section_id}/raw/{filename}'
                })
        
        return jsonify({'images': images})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/static/content/posts/<int:post_id>/sections/<int:section_id>/raw/<filename>')
def serve_section_image(post_id, section_id, filename):
    """Serve section images"""
    try:
        images_path = get_section_images_path(post_id, section_id)
        return send_from_directory(images_path, filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/images/<int:post_id>')
def get_all_images(post_id):
    """Get all images for a post across all types"""
    try:
        images = []
        
        # Check for header images
        header_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'raw')
        if os.path.exists(header_path):
            for filename in os.listdir(header_path):
                if allowed_file(filename):
                    images.append({
                        'filename': filename,
                        'url': f'/static/content/posts/{post_id}/header/raw/{filename}',
                        'type': 'header',
                        'path': os.path.join(header_path, filename)
                    })
        
        # Check for featured images
        featured_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'featured', 'raw')
        if os.path.exists(featured_path):
            for filename in os.listdir(featured_path):
                if allowed_file(filename):
                    images.append({
                        'filename': filename,
                        'url': f'/static/content/posts/{post_id}/featured/raw/{filename}',
                        'type': 'featured',
                        'path': os.path.join(featured_path, filename)
                    })
        
        # Check for section images
        sections_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'sections')
        if os.path.exists(sections_path):
            for section_dir in os.listdir(sections_path):
                section_path = os.path.join(sections_path, section_dir, 'raw')
                if os.path.exists(section_path):
                    for filename in os.listdir(section_path):
                        if allowed_file(filename):
                            images.append({
                                'filename': filename,
                                'url': f'/static/content/posts/{post_id}/sections/{section_dir}/raw/{filename}',
                                'type': 'section',
                                'section_id': section_dir,
                                'path': os.path.join(section_path, filename)
                            })
        
        return jsonify({'images': images})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/images/<int:post_id>/<image_type>')
def get_images_by_type(post_id, image_type):
    """Get images for specific type (header, section, featured) or processing stage (raw, optimized, captioned)"""
    try:
        images = []
        
        # Handle processing stages (raw, optimized, captioned)
        if image_type in ['raw', 'optimized', 'captioned']:
            processing_stage = image_type
            
            # Get header images for this processing stage
            header_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', processing_stage)
            if os.path.exists(header_path):
                for filename in os.listdir(header_path):
                    if allowed_file(filename):
                        images.append({
                            'filename': filename,
                            'url': f'/static/content/posts/{post_id}/header/{processing_stage}/{filename}',
                            'type': 'header',
                            'section_id': None,
                            'processing_stage': processing_stage,
                            'path': os.path.join(header_path, filename)
                        })
            
            # Get section images for this processing stage
            sections_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'sections')
            if os.path.exists(sections_path):
                for section_dir in os.listdir(sections_path):
                    section_path = os.path.join(sections_path, section_dir, processing_stage)
                    if os.path.exists(section_path):
                        for filename in os.listdir(section_path):
                            if allowed_file(filename):
                                images.append({
                                    'filename': filename,
                                    'url': f'/static/content/posts/{post_id}/sections/{section_dir}/{processing_stage}/{filename}',
                                    'type': 'section',
                                    'section_id': section_dir,
                                    'processing_stage': processing_stage,
                                    'path': os.path.join(section_path, filename)
                                })
            
            # Return unified response format
            header_count = len([img for img in images if img['type'] == 'header'])
            section_count = len([img for img in images if img['type'] == 'section'])
            
            return jsonify({
                'images': images,
                'total': len(images),
                'header_count': header_count,
                'section_count': section_count
            })
        
        # Handle legacy image types (header, section, featured)
        elif image_type == 'header':
            header_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'raw')
            if os.path.exists(header_path):
                for filename in os.listdir(header_path):
                    if allowed_file(filename):
                        images.append({
                            'filename': filename,
                            'url': f'/static/content/posts/{post_id}/header/raw/{filename}',
                            'type': 'header',
                            'path': os.path.join(header_path, filename)
                        })
        
        elif image_type == 'featured':
            featured_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'featured', 'raw')
            if os.path.exists(featured_path):
                for filename in os.listdir(featured_path):
                    if allowed_file(filename):
                        images.append({
                            'filename': filename,
                            'url': f'/static/content/posts/{post_id}/featured/raw/{filename}',
                            'type': 'featured',
                            'path': os.path.join(featured_path, filename)
                        })
        
        elif image_type == 'section':
            sections_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'sections')
            if os.path.exists(sections_path):
                for section_dir in os.listdir(sections_path):
                    section_path = os.path.join(sections_path, section_dir, 'raw')
                    if os.path.exists(section_path):
                        for filename in os.listdir(section_path):
                            if allowed_file(filename):
                                images.append({
                                    'filename': filename,
                                    'url': f'/static/content/posts/{post_id}/sections/{section_dir}/raw/{filename}',
                                    'type': 'section',
                                    'section_id': section_dir,
                                    'path': os.path.join(section_path, filename)
                                })
        
        return jsonify({'images': images})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/images/stats/<int:post_id>')
def get_image_stats(post_id):
    """Get image count, sizes, processing status"""
    try:
        stats = {
            'total_images': 0,
            'header_images': 0,
            'section_images': 0,
            'featured_images': 0,
            'optimized_images': 0,
            'optimized_header_images': 0,
            'optimized_section_images': 0,
            'total_size': 0
        }
        
        # Count header images
        header_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'raw')
        if os.path.exists(header_path):
            for filename in os.listdir(header_path):
                if allowed_file(filename):
                    stats['header_images'] += 1
                    stats['total_images'] += 1
                    file_path = os.path.join(header_path, filename)
                    if os.path.exists(file_path):
                        stats['total_size'] += os.path.getsize(file_path)
        
        # Count featured images
        featured_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'featured', 'raw')
        if os.path.exists(featured_path):
            for filename in os.listdir(featured_path):
                if allowed_file(filename):
                    stats['featured_images'] += 1
                    stats['total_images'] += 1
                    file_path = os.path.join(featured_path, filename)
                    if os.path.exists(file_path):
                        stats['total_size'] += os.path.getsize(file_path)
        
        # Count section images
        sections_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'sections')
        if os.path.exists(sections_path):
            for section_dir in os.listdir(sections_path):
                section_path = os.path.join(sections_path, section_dir, 'raw')
                if os.path.exists(section_path):
                    for filename in os.listdir(section_path):
                        if allowed_file(filename):
                            stats['section_images'] += 1
                            stats['total_images'] += 1
                            file_path = os.path.join(section_path, filename)
                            if os.path.exists(file_path):
                                stats['total_size'] += os.path.getsize(file_path)
        
        # Count optimized images
        # Optimized header images
        header_optimized_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'optimized')
        if os.path.exists(header_optimized_path):
            for filename in os.listdir(header_optimized_path):
                if allowed_file(filename):
                    stats['optimized_header_images'] += 1
                    stats['optimized_images'] += 1
                    file_path = os.path.join(header_optimized_path, filename)
                    if os.path.exists(file_path):
                        stats['total_size'] += os.path.getsize(file_path)
        
        # Optimized section images
        if os.path.exists(sections_path):
            for section_dir in os.listdir(sections_path):
                section_optimized_path = os.path.join(sections_path, section_dir, 'optimized')
                if os.path.exists(section_optimized_path):
                    for filename in os.listdir(section_optimized_path):
                        if allowed_file(filename):
                            stats['optimized_section_images'] += 1
                            stats['optimized_images'] += 1
                            file_path = os.path.join(section_optimized_path, filename)
                            if os.path.exists(file_path):
                                stats['total_size'] += os.path.getsize(file_path)
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/images/optimized/stats/<int:post_id>')
def get_optimized_stats(post_id):
    """Get optimized image count and sizes"""
    try:
        stats = {
            'optimized_images': 0,
            'optimized_header_images': 0,
            'optimized_section_images': 0,
            'optimized_size': 0
        }
        
        # Count optimized header images
        header_optimized_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'optimized')
        if os.path.exists(header_optimized_path):
            for filename in os.listdir(header_optimized_path):
                if allowed_file(filename):
                    stats['optimized_header_images'] += 1
                    stats['optimized_images'] += 1
                    file_path = os.path.join(header_optimized_path, filename)
                    if os.path.exists(file_path):
                        stats['optimized_size'] += os.path.getsize(file_path)
        
        # Count optimized section images
        sections_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'sections')
        if os.path.exists(sections_path):
            for section_dir in os.listdir(sections_path):
                section_optimized_path = os.path.join(sections_path, section_dir, 'optimized')
                if os.path.exists(section_optimized_path):
                    for filename in os.listdir(section_optimized_path):
                        if allowed_file(filename):
                            stats['optimized_section_images'] += 1
                            stats['optimized_images'] += 1
                            file_path = os.path.join(section_optimized_path, filename)
                            if os.path.exists(file_path):
                                stats['optimized_size'] += os.path.getsize(file_path)
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Image Processing Pipeline Endpoints
@app.route('/api/process/optimize', methods=['POST'])
def optimize_images():
    """Optimize images with specified quality settings"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        image_paths = data.get('image_paths', [])
        quality = data.get('quality', 85)
        
        if not post_id:
            return jsonify({'error': 'Missing post_id'}), 400
        
        # For now, return a mock response indicating processing would happen
        # In a real implementation, this would use PIL/Pillow to optimize images
        job_id = f"optimize_{post_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': f'Optimization job created for {len(image_paths)} images',
            'status': 'queued'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process/watermark', methods=['POST'])
def watermark_images():
    """Add watermarks to images"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        image_paths = data.get('image_paths', [])
        watermark_text = data.get('watermark_text', 'BlogForge')
        
        if not post_id:
            return jsonify({'error': 'Missing post_id'}), 400
        
        # For now, return a mock response
        job_id = f"watermark_{post_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': f'Watermark job created for {len(image_paths)} images',
            'status': 'queued'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process/caption', methods=['POST'])
def generate_captions():
    """Generate captions for images using AI"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        image_paths = data.get('image_paths', [])
        
        if not post_id:
            return jsonify({'error': 'Missing post_id'}), 400
        
        # For now, return a mock response
        job_id = f"caption_{post_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': f'Caption generation job created for {len(image_paths)} images',
            'status': 'queued'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process/status/<job_id>')
def get_processing_status(job_id):
    """Check processing status for a job"""
    try:
        # For now, return a mock status
        # In a real implementation, this would check a job queue or database
        return jsonify({
            'job_id': job_id,
            'status': 'completed',
            'progress': 100,
            'message': 'Processing completed successfully',
            'results': {
                'processed_images': 5,
                'errors': 0,
                'output_paths': []
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Image Management Features
@app.route('/api/manage/images/<image_id>/preview')
def get_image_preview(image_id):
    """Get image preview with metadata"""
    try:
        # For now, return a mock response
        # In a real implementation, this would look up the image by ID
        return jsonify({
            'image_id': image_id,
            'filename': f'image_{image_id}.png',
            'url': f'/static/content/posts/53/sections/710/raw/image_{image_id}.png',
            'type': 'section',
            'section_id': 710,
            'post_id': 53,
            'status': 'raw',
            'size': 1024000,
            'dimensions': {'width': 800, 'height': 600},
            'uploaded_at': '2025-08-05T12:26:05Z'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/manage/images/<image_id>/metadata', methods=['PUT'])
def update_image_metadata(image_id):
    """Update image metadata"""
    try:
        data = request.get_json()
        caption = data.get('caption')
        alt_text = data.get('alt_text')
        tags = data.get('tags', [])
        
        # For now, return a mock response
        # In a real implementation, this would update database metadata
        return jsonify({
            'success': True,
            'image_id': image_id,
            'message': 'Metadata updated successfully',
            'metadata': {
                'caption': caption,
                'alt_text': alt_text,
                'tags': tags,
                'updated_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/manage/images/<image_id>/duplicate', methods=['POST'])
def duplicate_image(image_id):
    """Duplicate an image"""
    try:
        # For now, return a mock response
        # In a real implementation, this would copy the file and create new metadata
        new_image_id = f"{image_id}_copy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return jsonify({
            'success': True,
            'original_image_id': image_id,
            'new_image_id': new_image_id,
            'message': 'Image duplicated successfully',
            'new_url': f'/static/content/posts/53/sections/710/raw/{new_image_id}.png'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/manage/images/<image_id>/versions')
def get_image_versions(image_id):
    """Get all versions of an image"""
    try:
        # For now, return a mock response
        # In a real implementation, this would look up version history
        return jsonify({
            'image_id': image_id,
            'versions': [
                {
                    'version': 'raw',
                    'url': f'/static/content/posts/53/sections/710/raw/{image_id}.png',
                    'created_at': '2025-08-05T12:26:05Z',
                    'size': 1024000
                },
                {
                    'version': 'optimized',
                    'url': f'/static/content/posts/53/sections/710/optimized/{image_id}.png',
                    'created_at': '2025-08-05T12:30:00Z',
                    'size': 512000
                }
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Statistics and Monitoring Endpoints
@app.route('/api/stats/overview')
def get_overview_stats():
    """Get overall statistics across all posts"""
    try:
        # For now, return a mock response
        # In a real implementation, this would aggregate data from all posts
        return jsonify({
            'total_posts': 5,
            'total_images': 42,
            'total_storage_mb': 156.8,
            'average_images_per_post': 8.4,
            'recent_uploads': [
                {
                    'post_id': 53,
                    'filename': 'header.png',
                    'type': 'header',
                    'uploaded_at': '2025-08-05T12:26:05Z'
                },
                {
                    'post_id': 53,
                    'filename': '713.png',
                    'type': 'section',
                    'uploaded_at': '2025-08-05T12:25:30Z'
                }
            ],
            'processing_queue': {
                'pending': 3,
                'processing': 1,
                'completed_today': 12
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats/processing')
def get_processing_stats():
    """Get processing statistics and queue status"""
    try:
        # For now, return a mock response
        return jsonify({
            'queue_status': {
                'pending': 3,
                'processing': 1,
                'completed': 25,
                'failed': 2
            },
            'processing_times': {
                'average_optimization': 2.5,
                'average_watermarking': 1.8,
                'average_captioning': 5.2
            },
            'error_rates': {
                'optimization': 0.05,
                'watermarking': 0.02,
                'captioning': 0.08
            },
            'recent_jobs': [
                {
                    'job_id': 'optimize_53_20250805_122605',
                    'type': 'optimization',
                    'status': 'completed',
                    'created_at': '2025-08-05T12:26:05Z',
                    'completed_at': '2025-08-05T12:26:08Z'
                }
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats/storage')
def get_storage_stats():
    """Get storage usage statistics"""
    try:
        # For now, return a mock response
        return jsonify({
            'total_storage_mb': 156.8,
            'storage_by_type': {
                'header_images': 12.5,
                'section_images': 134.2,
                'featured_images': 10.1
            },
            'storage_by_post': {
                '53': 27.5,
                '1': 15.2,
                '2': 22.1
            },
            'largest_files': [
                {
                    'filename': 'header.png',
                    'post_id': 53,
                    'size_mb': 2.8,
                    'type': 'header'
                },
                {
                    'filename': '713.png',
                    'post_id': 53,
                    'size_mb': 2.1,
                    'type': 'section'
                }
            ],
            'storage_trends': {
                'daily_uploads_mb': [5.2, 3.8, 7.1, 4.5, 6.2],
                'total_growth_mb': 45.8
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PROCESSING PIPELINE ENDPOINTS
# ============================================================================

@app.route('/api/pipeline/start', methods=['POST'])
def start_processing_pipeline():
    """Start processing pipeline for images"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        image_ids = data.get('image_ids', [])
        settings = data.get('settings', {})
        job_type = data.get('job_type', 'pipeline')
        
        if not post_id or not image_ids:
            return jsonify({'error': 'post_id and image_ids required'}), 400
        
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Create processing job
                cur.execute("""
                    INSERT INTO image_processing_jobs 
                    (post_id, job_type, status, total_images, settings)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (post_id, job_type, 'pending', len(image_ids), json.dumps(settings)))
                
                job_id = cur.fetchone()['id']
                
                # Create processing steps
                steps = ['generation', 'optimization', 'watermarking', 'captioning', 'metadata']
                for step in steps:
                    cur.execute("""
                        INSERT INTO image_processing_steps 
                        (job_id, step_name, status)
                        VALUES (%s, %s, %s)
                    """, (job_id, step, 'pending'))
                
                # Create image processing status records
                for image_id in image_ids:
                    cur.execute("""
                        INSERT INTO image_processing_status 
                        (image_id, post_id, image_type, section_id, current_step, pipeline_status, processing_job_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (image_id, post_id, settings.get('image_type', 'section'), 
                         settings.get('section_id'), 'generation', 'raw', job_id))
                
                conn.commit()
                
                # Start processing (mock implementation)
                # In real implementation, this would queue the job for background processing
                
                return jsonify({
                    'success': True,
                    'job_id': job_id,
                    'message': f'Processing pipeline started for {len(image_ids)} images'
                })
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pipeline/status/<int:job_id>')
def get_pipeline_status(job_id):
    """Get real-time processing status for a job"""
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get job details
                cur.execute("""
                    SELECT * FROM image_processing_jobs WHERE id = %s
                """, (job_id,))
                job = cur.fetchone()
                
                if not job:
                    return jsonify({'error': 'Job not found'}), 404
                
                # Get processing steps
                cur.execute("""
                    SELECT * FROM image_processing_steps 
                    WHERE job_id = %s 
                    ORDER BY id
                """, (job_id,))
                steps = cur.fetchall()
                
                # Get image status
                cur.execute("""
                    SELECT * FROM image_processing_status 
                    WHERE processing_job_id = %s
                """, (job_id,))
                images = cur.fetchall()
                
                # Calculate overall progress
                total_steps = len(steps)
                completed_steps = sum(1 for step in steps if step['status'] == 'completed')
                overall_progress = int((completed_steps / total_steps) * 100) if total_steps > 0 else 0
                
                return jsonify({
                    'job_id': job_id,
                    'status': job['status'],
                    'overall_progress': overall_progress,
                    'total_images': job['total_images'],
                    'processed_images': job['processed_images'],
                    'steps': [dict(step) for step in steps],
                    'images': [dict(image) for image in images],
                    'created_at': job['created_at'].isoformat() if job['created_at'] else None,
                    'started_at': job['started_at'].isoformat() if job['started_at'] else None,
                    'completed_at': job['completed_at'].isoformat() if job['completed_at'] else None
                })
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pipeline/cancel/<int:job_id>', methods=['POST'])
def cancel_processing_job(job_id):
    """Cancel a processing job"""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Update job status
                cur.execute("""
                    UPDATE image_processing_jobs 
                    SET status = 'cancelled', completed_at = NOW()
                    WHERE id = %s
                """, (job_id,))
                
                # Update step status
                cur.execute("""
                    UPDATE image_processing_steps 
                    SET status = 'cancelled'
                    WHERE job_id = %s AND status IN ('pending', 'processing')
                """, (job_id,))
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Job {job_id} cancelled successfully'
                })
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pipeline/jobs/<int:post_id>')
def get_pipeline_jobs(post_id):
    """Get all processing jobs for a post"""
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT j.*, 
                           COUNT(s.id) as total_steps,
                           COUNT(CASE WHEN s.status = 'completed' THEN 1 END) as completed_steps
                    FROM image_processing_jobs j
                    LEFT JOIN image_processing_steps s ON j.id = s.job_id
                    WHERE j.post_id = %s
                    GROUP BY j.id
                    ORDER BY j.created_at DESC
                """, (post_id,))
                
                jobs = cur.fetchall()
                
                jobs_list = []
                for job in jobs:
                    progress = int((job['completed_steps'] / job['total_steps']) * 100) if job['total_steps'] > 0 else 0
                    jobs_list.append({
                        'id': job['id'],
                        'job_type': job['job_type'],
                        'status': job['status'],
                        'progress': progress,
                        'total_images': job['total_images'],
                        'processed_images': job['processed_images'],
                        'created_at': job['created_at'].isoformat() if job['created_at'] else None,
                        'started_at': job['started_at'].isoformat() if job['started_at'] else None,
                        'completed_at': job['completed_at'].isoformat() if job['completed_at'] else None
                    })
                
                return jsonify({'jobs': jobs_list})
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# BATCH PROCESSING ENDPOINTS
# ============================================================================

@app.route('/api/batch/start', methods=['POST'])
def start_batch_processing():
    """Start batch processing for multiple images"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        image_ids = data.get('image_ids', [])
        settings = data.get('settings', {})
        
        if not post_id or not image_ids:
            return jsonify({'error': 'post_id and image_ids required'}), 400
        
        # Use the pipeline system for batch processing
        return start_processing_pipeline()
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/batch/status/<int:batch_id>')
def get_batch_status(batch_id):
    """Get batch processing status"""
    # Batch processing uses the same system as pipeline
    return get_pipeline_status(batch_id)

@app.route('/api/batch/cancel/<int:batch_id>', methods=['POST'])
def cancel_batch(batch_id):
    """Cancel batch processing"""
    # Batch processing uses the same system as pipeline
    return cancel_processing_job(batch_id)

@app.route('/api/batch/history/<int:post_id>')
def get_batch_history(post_id):
    """Get batch processing history for a post"""
    # Use the same endpoint as pipeline jobs
    return get_pipeline_jobs(post_id)

# ============================================================================
# ADVANCED PROCESSING FEATURES
# ============================================================================

@app.route('/api/advanced/process-step', methods=['POST'])
def process_single_step():
    """Process a single step for specific images"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        image_ids = data.get('image_ids', [])
        step_name = data.get('step_name')
        settings = data.get('settings', {})
        
        if not post_id or not image_ids or not step_name:
            return jsonify({'error': 'post_id, image_ids, and step_name required'}), 400
        
        # Validate step name
        valid_steps = ['generation', 'optimization', 'watermarking', 'captioning', 'metadata']
        if step_name not in valid_steps:
            return jsonify({'error': f'Invalid step name. Must be one of: {valid_steps}'}), 400
        
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Create processing job for single step
                cur.execute("""
                    INSERT INTO image_processing_jobs 
                    (post_id, job_type, status, total_images, settings)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (post_id, f'single_{step_name}', 'pending', len(image_ids), json.dumps(settings)))
                
                job_id = cur.fetchone()['id']
                
                # Create only the specified step
                cur.execute("""
                    INSERT INTO image_processing_steps 
                    (job_id, step_name, status)
                    VALUES (%s, %s, %s)
                """, (job_id, step_name, 'pending'))
                
                # Create image processing status records
                for image_id in image_ids:
                    cur.execute("""
                        INSERT INTO image_processing_status 
                        (image_id, post_id, image_type, section_id, current_step, pipeline_status, processing_job_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (image_id, post_id, settings.get('image_type', 'section'), 
                         settings.get('section_id'), step_name, 'processing', job_id))
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'job_id': job_id,
                    'message': f'Single step processing started: {step_name}'
                })
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced/retry-failed', methods=['POST'])
def retry_failed_images():
    """Retry processing for failed images"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        image_ids = data.get('image_ids', [])
        settings = data.get('settings', {})
        
        if not post_id or not image_ids:
            return jsonify({'error': 'post_id and image_ids required'}), 400
        
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get failed images and their last failed step
                cur.execute("""
                    SELECT image_id, current_step, error_message
                    FROM image_processing_status 
                    WHERE post_id = %s AND image_id = ANY(%s) AND pipeline_status = 'failed'
                """, (post_id, image_ids))
                
                failed_images = cur.fetchall()
                
                if not failed_images:
                    return jsonify({'error': 'No failed images found'}), 404
                
                # Create retry job
                cur.execute("""
                    INSERT INTO image_processing_jobs 
                    (post_id, job_type, status, total_images, settings)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (post_id, 'retry_failed', 'pending', len(failed_images), json.dumps(settings)))
                
                job_id = cur.fetchone()['id']
                
                # Create processing steps starting from the failed step
                for failed_image in failed_images:
                    step_name = failed_image['current_step']
                    steps = ['generation', 'optimization', 'watermarking', 'captioning', 'metadata']
                    
                    # Find the index of the failed step and create steps from there
                    try:
                        failed_index = steps.index(step_name)
                        remaining_steps = steps[failed_index:]
                        
                        for step in remaining_steps:
                            cur.execute("""
                                INSERT INTO image_processing_steps 
                                (job_id, step_name, status)
                                VALUES (%s, %s, %s)
                            """, (job_id, step, 'pending'))
                        
                        # Update image status
                        cur.execute("""
                            UPDATE image_processing_status 
                            SET processing_job_id = %s, pipeline_status = 'retrying'
                            WHERE post_id = %s AND image_id = %s
                        """, (job_id, post_id, failed_image['image_id']))
                        
                    except ValueError:
                        # Step not found, start from beginning
                        for step in steps:
                            cur.execute("""
                                INSERT INTO image_processing_steps 
                                (job_id, step_name, status)
                                VALUES (%s, %s, %s)
                            """, (job_id, step, 'pending'))
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'job_id': job_id,
                    'message': f'Retry processing started for {len(failed_images)} failed images'
                })
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced/optimize-settings', methods=['POST'])
def optimize_processing_settings():
    """Optimize processing settings based on image analysis"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        image_ids = data.get('image_ids', [])
        
        if not post_id or not image_ids:
            return jsonify({'error': 'post_id and image_ids required'}), 400
        
        # Mock implementation - in real system, this would analyze images
        # and suggest optimal settings based on image characteristics
        optimized_settings = {
            'quality_level': 'high',
            'watermark_style': 'clan',
            'generate_captions': True,
            'create_variations': False,
            'compression_level': 85,
            'max_width': 1920,
            'max_height': 1080,
            'format': 'webp',
            'metadata_preservation': True
        }
        
        return jsonify({
            'success': True,
            'optimized_settings': optimized_settings,
            'message': 'Settings optimized based on image analysis'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced/smart-organization', methods=['POST'])
def smart_organization():
    """Automatically organize images based on content analysis"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        organization_type = data.get('type', 'auto')
        
        if not post_id:
            return jsonify({'error': 'post_id required'}), 400
        
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get all images for the post
                cur.execute("""
                    SELECT * FROM image_processing_status 
                    WHERE post_id = %s
                    ORDER BY created_at DESC
                """, (post_id,))
                
                images = cur.fetchall()
                
                if not images:
                    return jsonify({'error': 'No images found for this post'}), 404
                
                # Mock organization logic
                organized_groups = {
                    'headers': [],
                    'sections': [],
                    'featured': [],
                    'social': [],
                    'thumbnails': []
                }
                
                for image in images:
                    # Mock classification based on image type and metadata
                    if image['image_type'] == 'header':
                        organized_groups['headers'].append(dict(image))
                    elif image['image_type'] == 'section':
                        organized_groups['sections'].append(dict(image))
                    else:
                        organized_groups['featured'].append(dict(image))
                
                return jsonify({
                    'success': True,
                    'organized_groups': organized_groups,
                    'total_images': len(images),
                    'message': f'Organized {len(images)} images into {len(organized_groups)} groups'
                })
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced/processing-presets', methods=['GET'])
def get_processing_presets():
    """Get available processing presets"""
    try:
        presets = {
            'web_optimized': {
                'name': 'Web Optimized',
                'description': 'Optimized for web display with good quality and size',
                'settings': {
                    'quality_level': 'high',
                    'watermark_style': 'clan',
                    'generate_captions': True,
                    'create_variations': False,
                    'compression_level': 85,
                    'max_width': 1920,
                    'max_height': 1080,
                    'format': 'webp'
                }
            },
            'social_media': {
                'name': 'Social Media',
                'description': 'Optimized for social media platforms',
                'settings': {
                    'quality_level': 'medium',
                    'watermark_style': 'text',
                    'generate_captions': True,
                    'create_variations': True,
                    'compression_level': 75,
                    'max_width': 1200,
                    'max_height': 630,
                    'format': 'jpg'
                }
            },
            'print_ready': {
                'name': 'Print Ready',
                'description': 'High quality for print publications',
                'settings': {
                    'quality_level': 'maximum',
                    'watermark_style': 'none',
                    'generate_captions': False,
                    'create_variations': False,
                    'compression_level': 95,
                    'max_width': 3000,
                    'max_height': 2000,
                    'format': 'png'
                }
            },
            'thumbnail': {
                'name': 'Thumbnail',
                'description': 'Small thumbnails for previews',
                'settings': {
                    'quality_level': 'low',
                    'watermark_style': 'none',
                    'generate_captions': False,
                    'create_variations': False,
                    'compression_level': 60,
                    'max_width': 300,
                    'max_height': 200,
                    'format': 'jpg'
                }
            }
        }
        
        return jsonify({
            'success': True,
            'presets': presets
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced/apply-preset', methods=['POST'])
def apply_processing_preset():
    """Apply a processing preset to images"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        image_ids = data.get('image_ids', [])
        preset_name = data.get('preset_name')
        
        if not post_id or not image_ids or not preset_name:
            return jsonify({'error': 'post_id, image_ids, and preset_name required'}), 400
        
        # Get preset settings
        presets_response = get_processing_presets()
        presets_data = presets_response.get_json()
        
        if not presets_data.get('success'):
            return jsonify({'error': 'Failed to load presets'}), 500
        
        preset = presets_data['presets'].get(preset_name)
        if not preset:
            return jsonify({'error': f'Preset "{preset_name}" not found'}), 404
        
        # Start processing with preset settings
        return start_processing_pipeline()
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced/processing-analytics', methods=['GET'])
def get_processing_analytics():
    """Get processing analytics and insights"""
    try:
        post_id = request.args.get('post_id')
        
        if not post_id:
            return jsonify({'error': 'post_id required'}), 400
        
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get processing statistics
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_jobs,
                        COUNT(CASE WHEN j.status = 'completed' THEN 1 END) as completed_jobs,
                        COUNT(CASE WHEN j.status = 'failed' THEN 1 END) as failed_jobs,
                        COUNT(CASE WHEN j.status = 'cancelled' THEN 1 END) as cancelled_jobs,
                        AVG(EXTRACT(EPOCH FROM (j.completed_at - j.started_at))) as avg_processing_time
                    FROM image_processing_jobs j
                    WHERE j.post_id = %s
                """, (post_id,))
                
                stats = cur.fetchone()
                
                # Get step performance
                cur.execute("""
                    SELECT 
                        s.step_name,
                        COUNT(*) as total_steps,
                        COUNT(CASE WHEN s.status = 'completed' THEN 1 END) as completed_steps,
                        AVG(EXTRACT(EPOCH FROM (s.completed_at - s.started_at))) as avg_step_time
                    FROM image_processing_steps s
                    JOIN image_processing_jobs j ON s.job_id = j.id
                    WHERE j.post_id = %s
                    GROUP BY s.step_name
                """, (post_id,))
                
                step_stats = cur.fetchall()
                
                analytics = {
                    'overview': {
                        'total_jobs': stats['total_jobs'] or 0,
                        'completed_jobs': stats['completed_jobs'] or 0,
                        'failed_jobs': stats['failed_jobs'] or 0,
                        'cancelled_jobs': stats['cancelled_jobs'] or 0,
                        'success_rate': round((stats['completed_jobs'] or 0) / (stats['total_jobs'] or 1) * 100, 2),
                        'avg_processing_time': round(stats['avg_processing_time'] or 0, 2)
                    },
                    'step_performance': [dict(step) for step in step_stats],
                    'recommendations': [
                        'Consider batch processing for similar images',
                        'Optimize watermark settings for faster processing',
                        'Use presets for consistent results'
                    ]
                }
                
                return jsonify({
                    'success': True,
                    'analytics': analytics
                })
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sections/<int:post_id>/selected', methods=['GET'])
def get_selected_images(post_id):
    """Get selected images for all sections of a post."""
    try:
        conn = get_db_conn()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT id as section_id, image_filename as selected_image 
            FROM post_section 
            WHERE post_id = %s AND image_filename IS NOT NULL
        """, (post_id,))
        
        selected_images = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'selected_images': [dict(row) for row in selected_images]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sections/<int:post_id>/<int:section_id>/select', methods=['POST'])
def select_section_image(post_id, section_id):
    """Select an image for a specific section."""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
        
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Update the image_filename for this section
        cursor.execute("""
            UPDATE post_section 
            SET image_filename = %s 
            WHERE post_id = %s AND id = %s
        """, (filename, post_id, section_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'selected_image': filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/header/<int:post_id>/select', methods=['POST'])
def select_header_image(post_id):
    """Select a header image for a post."""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
        
        # For now, we'll use a simple approach: store the selection in a session or cache
        # Since the image table doesn't seem to be used for header images in this system,
        # we'll implement a simpler solution that doesn't require database changes
        
        header_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'raw')
        if os.path.exists(os.path.join(header_path, filename)):
            # Store the selection in a simple file or use a different approach
            # For now, we'll just return success without persisting to database
            # TODO: Implement proper header image selection persistence
            
            return jsonify({'success': True, 'selected_image': filename})
        else:
            return jsonify({'error': 'Header image file not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sections/<int:post_id>/selected/count', methods=['GET'])
def get_selected_count(post_id):
    """Get count of selected images for a post."""
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM post_section 
            WHERE post_id = %s AND image_filename IS NOT NULL
        """, (post_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return jsonify({'selected_count': result[0] if result else 0})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sections/<int:post_id>/selected/stats', methods=['GET'])
def get_selected_stats(post_id):
    """Get count and total size of selected images for a post."""
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Get selected images from post_section table
        cursor.execute("""
            SELECT id, image_filename 
            FROM post_section 
            WHERE post_id = %s AND image_filename IS NOT NULL
            ORDER BY id
        """, (post_id,))
        
        selected_sections = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Calculate total size of selected images
        total_size = 0
        valid_count = 0
        sections_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'sections')
        
        for section in selected_sections:
            section_id = section[0]  # id is first column
            selected_filename = section[1]  # image_filename is second column
            
            # Check if the selected file exists in raw directory
            raw_path = os.path.join(sections_path, str(section_id), 'raw', selected_filename)
            if os.path.exists(raw_path):
                total_size += os.path.getsize(raw_path)
                valid_count += 1
            else:
                # Check optimized directory
                optimized_path = os.path.join(sections_path, str(section_id), 'optimized', selected_filename)
                if os.path.exists(optimized_path):
                    total_size += os.path.getsize(optimized_path)
                    valid_count += 1
                else:
                    # If selected file doesn't exist, try to find any image in the section
                    raw_dir = os.path.join(sections_path, str(section_id), 'raw')
                    if os.path.exists(raw_dir):
                        for filename in os.listdir(raw_dir):
                            if allowed_file(filename):
                                file_path = os.path.join(raw_dir, filename)
                                total_size += os.path.getsize(file_path)
                                valid_count += 1
                                break  # Use the first available image
        
        return jsonify({
            'selected_count': valid_count,
            'selected_size': total_size
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/images/<int:post_id>/selected', methods=['GET'])
def get_selected_images_unified(post_id):
    """Get all selected images (header + sections) for a post with unified response format"""
    try:
        images = []
        
        # Get header image selection from post table
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # For now, we'll assume no header image is selected since the database structure
        # doesn't seem to support header image selection in the current system
        # TODO: Implement proper header image selection persistence
        
        # Get section image selections from post_section table
        cursor.execute("""
            SELECT id, image_filename 
            FROM post_section 
            WHERE post_id = %s AND image_filename IS NOT NULL
            ORDER BY id
        """, (post_id,))
        
        selected_sections = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # For now, no header images are selected since the database structure
        # doesn't support header image selection in the current implementation
        
        # Add section images
        sections_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'sections')
        for section in selected_sections:
            section_id = section[0]
            selected_filename = section[1]
            
            # Check raw directory first
            raw_path = os.path.join(sections_path, str(section_id), 'raw', selected_filename)
            if os.path.exists(raw_path):
                images.append({
                    'filename': selected_filename,
                    'url': f'/static/content/posts/{post_id}/sections/{section_id}/raw/{selected_filename}',
                    'type': 'section',
                    'section_id': str(section_id),
                    'processing_stage': 'raw',
                    'is_selected': True
                })
            else:
                # Check optimized directory
                optimized_path = os.path.join(sections_path, str(section_id), 'optimized', selected_filename)
                if os.path.exists(optimized_path):
                    images.append({
                        'filename': selected_filename,
                        'url': f'/static/content/posts/{post_id}/sections/{section_id}/optimized/{selected_filename}',
                        'type': 'section',
                        'section_id': str(section_id),
                        'processing_stage': 'optimized',
                        'is_selected': True
                    })
                else:
                    # Fallback to first available image in raw directory
                    raw_dir = os.path.join(sections_path, str(section_id), 'raw')
                    if os.path.exists(raw_dir):
                        for filename in os.listdir(raw_dir):
                            if allowed_file(filename):
                                images.append({
                                    'filename': filename,
                                    'url': f'/static/content/posts/{post_id}/sections/{section_id}/raw/{filename}',
                                    'type': 'section',
                                    'section_id': str(section_id),
                                    'processing_stage': 'raw',
                                    'is_selected': True,
                                    'note': f'Selected file "{selected_filename}" not found, using "{filename}"'
                                })
                                break
        
        # Return unified response format
        header_count = len([img for img in images if img['type'] == 'header'])
        section_count = len([img for img in images if img['type'] == 'section'])
        
        return jsonify({
            'images': images,
            'total': len(images),
            'header_count': header_count,
            'section_count': section_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/images/<int:post_id>/raw')
def get_raw_images(post_id):
    """Get all raw images (header + sections) for a post"""
    return get_images_by_type(post_id, 'raw')

@app.route('/api/images/<int:post_id>/optimized')
def get_optimized_images(post_id):
    """Get all optimized images (header + sections) for a post"""
    return get_images_by_type(post_id, 'optimized')

@app.route('/api/images/<int:post_id>/captioned')
def get_captioned_images(post_id):
    """Get all captioned images (header + sections) for a post"""
    return get_images_by_type(post_id, 'captioned')

@app.route('/api/sections/<int:post_id>/initialize-selections', methods=['POST'])
def initialize_selections(post_id):
    """Initialize default selections (first image) for sections that don't have selected images."""
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Get sections that don't have selected images
        cursor.execute("""
            SELECT id 
            FROM post_section 
            WHERE post_id = %s AND image_filename IS NULL
        """, (post_id,))
        
        sections_without_selection = cursor.fetchall()
        
        # For each section, find the first image and set it as selected
        for (section_id,) in sections_without_selection:
            # Get the first image for this section
            cursor.execute("""
                SELECT filename 
                FROM images 
                WHERE post_id = %s AND section_id = %s 
                ORDER BY filename 
                LIMIT 1
            """, (post_id, section_id))
            
            result = cursor.fetchone()
            if result:
                filename = result[0]
                # Set this as the selected image
                cursor.execute("""
                    UPDATE post_section 
                    SET image_filename = %s 
                    WHERE id = %s
                """, (filename, section_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'initialized': len(sections_without_selection)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=port) 