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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=port) 