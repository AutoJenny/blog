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
    """Get images for specific type (header, section, featured)"""
    try:
        images = []
        
        if image_type == 'header':
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=port) 