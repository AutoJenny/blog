#!/usr/bin/env python3
"""
Blog Images - Image Generation and Management Application
"""

import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import requests

app = Flask(__name__)

# Configure port
port = int(os.environ.get('PORT', 5005))

# Configure upload settings
UPLOAD_FOLDER = 'static/content/posts'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_section_images_path(post_id, section_id):
    """Get the path for section images"""
    return os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'sections', str(section_id), 'raw')

@app.route('/')
def index():
    post_id = request.args.get('post_id', '1')
    return render_template('index.html', post_id=post_id)

@app.route('/api/upload', methods=['POST'])
def upload_image():
    """Handle image upload for a specific section"""
    try:
        post_id = request.form.get('post_id')
        section_id = request.form.get('section_id')
        
        if not post_id or not section_id:
            return jsonify({'error': 'Missing post_id or section_id'}), 400
        
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'}), 400
        
        # Create directory if it doesn't exist
        upload_path = get_section_images_path(post_id, section_id)
        os.makedirs(upload_path, exist_ok=True)
        
        # Save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'path': file_path
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=port) 