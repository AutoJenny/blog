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

@app.route('/test')
def test():
    return jsonify({'status': 'ok', 'message': 'Flask app is working'})

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
        post_title = None
        section_titles = {}
        
        # Get post title and section titles from database
        try:
            with get_db_conn() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    # Get post title
                    cur.execute("SELECT title FROM post WHERE id = %s", (post_id,))
                    post_result = cur.fetchone()
                    if post_result:
                        post_title = post_result['title']
                    
                    # Get section titles
                    cur.execute("""
                        SELECT id, section_heading 
                        FROM post_section 
                        WHERE post_id = %s 
                        ORDER BY section_order
                    """, (post_id,))
                    sections = cur.fetchall()
                    for section in sections:
                        section_titles[str(section['id'])] = section['section_heading']
        except Exception as e:
            print(f"Database error getting titles: {e}")
            # Continue without titles if database fails
        
        # Handle processing stages (raw, optimized, watermarked, captioned)
        if image_type in ['raw', 'optimized', 'watermarked', 'captioned']:
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
                            'section_title': post_title,  # Header images get post title
                            'processing_stage': processing_stage,
                            'path': os.path.join(header_path, filename)
                        })
            
            # Get section images for this processing stage
            sections_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'sections')
            if os.path.exists(sections_path):
                for section_dir in os.listdir(sections_path):
                    section_path = os.path.join(sections_path, section_dir, processing_stage)
                    if os.path.exists(section_path):
                        section_title = section_titles.get(section_dir, f"Section {section_dir}")
                        for filename in os.listdir(section_path):
                            if allowed_file(filename):
                                images.append({
                                    'filename': filename,
                                    'url': f'/static/content/posts/{post_id}/sections/{section_dir}/{processing_stage}/{filename}',
                                    'type': 'section',
                                    'section_id': section_dir,
                                    'section_title': section_title,
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
                'section_count': section_count,
                'post_title': post_title
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
    """Generate captions for images using LLM"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        caption_style = data.get('caption_style', 'Descriptive')
        caption_language = data.get('caption_language', 'English')
        
        if not post_id:
            return jsonify({'error': 'Missing post_id'}), 400
        
        # Get post and section data for context
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get post data
                cur.execute("""
                    SELECT p.title, p.subtitle, pd.basic_idea, pd.idea_scope
                    FROM post p
                    LEFT JOIN post_development pd ON p.id = pd.post_id
                    WHERE p.id = %s
                """, (post_id,))
                post_data = cur.fetchone()
                
                if not post_data:
                    return jsonify({'error': 'Post not found'}), 404
                
                # Get section data
                cur.execute("""
                    SELECT id, section_heading, section_description, image_filename
                    FROM post_section
                    WHERE post_id = %s
                    ORDER BY section_order
                """, (post_id,))
                sections = cur.fetchall()
        
                # Get watermarked images
                watermarked_images = []
                
                # Check header watermarked images
                header_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'watermarked')
                print(f"Checking header path: {header_path}")
                if os.path.exists(header_path):
                    for filename in os.listdir(header_path):
                        if allowed_file(filename):
                            watermarked_images.append({
                                'type': 'header',
                                'path': os.path.join(header_path, filename),
                                'filename': filename,
                                'section_id': None
                            })
                            print(f"Found header image: {filename}")
                
                # Check section watermarked images
                sections_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'sections')
                for section in sections:
                    section_watermarked_path = os.path.join(sections_path, str(section['id']), 'watermarked')
                    print(f"Checking section path: {section_watermarked_path}")
                    if os.path.exists(section_watermarked_path):
                        for filename in os.listdir(section_watermarked_path):
                            if allowed_file(filename):
                                watermarked_images.append({
                                    'type': 'section',
                                    'path': os.path.join(section_watermarked_path, filename),
                                    'filename': filename,
                                    'section_id': section['id'],
                                    'section_heading': section['section_heading']
                                })
                                print(f"Found section image: {filename}")
                
                print(f"Total watermarked images found: {len(watermarked_images)}")
                if not watermarked_images:
                    return jsonify({'error': 'No watermarked images found'}), 404
        
                # Generate captions using LLM
        captions_generated = 0
        captions_data = []
        
        for image_info in watermarked_images:
            try:
                # Prepare context for LLM
                context = {
                    'post_title': post_data['title'],
                    'post_subtitle': post_data['subtitle'],
                    'basic_idea': post_data['basic_idea'],
                    'idea_scope': post_data['idea_scope'],
                    'image_type': image_info['type'],
                    'caption_style': caption_style,
                    'caption_language': caption_language
                }
                
                if image_info['type'] == 'section':
                    context['section_heading'] = image_info['section_heading']
                
                # Generate caption using LLM
                caption = generate_caption_via_llm(context, image_info)
                
                # Save caption to database
                save_caption_to_database(image_info, caption, post_id)
                
                captions_data.append({
                    'image_path': image_info['path'],
                    'caption': caption,
                    'type': image_info['type'],
                    'section_id': image_info.get('section_id')
                })
                
                captions_generated += 1
                
            except Exception as e:
                print(f"Error generating caption for {image_info['filename']}: {e}")
                # If it's an Ollama connection error, stop processing and return error
                if 'Ollama LLM service is not running' in str(e):
                    return jsonify({'error': str(e)}), 503
                continue
        
        return jsonify({
            'success': True,
            'captions_generated': captions_generated,
            'total_images': len(watermarked_images),
            'captions': captions_data,
            'message': f'Successfully generated captions for {captions_generated} images'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_caption_via_llm(context, image_info):
    """Generate caption using LLM via blog-core API"""
    try:
        # Fetch prompts from workflow system
        system_prompt_response = requests.get('http://localhost:5000/api/workflow/prompts/all')
        if system_prompt_response.status_code == 200:
            prompts = system_prompt_response.json()
            
            # Find the image captions system prompt (ID 110)
            system_prompt = next((p for p in prompts if p['id'] == 110), None)
            # Find the image captions task prompt (ID 109)
            task_prompt = next((p for p in prompts if p['id'] == 109), None)
            
            if system_prompt and task_prompt:
                # Construct the full prompt using system and task prompts
                system_content = system_prompt.get('prompt_text', '')
                task_content = task_prompt.get('prompt_text', '')
                
                # Build context information
                context_info = f"""Post Context:
- Title: {context['post_title']}
- Subtitle: {context['post_subtitle']}
- Basic Idea: {context['basic_idea']}
- Idea Scope: {context['idea_scope']}"""
                
                if context['image_type'] != 'header':
                    context_info += f"\n- Section: {context['section_heading']}"
                
                context_info += f"""
Caption Style: {context['caption_style']}
Caption Language: {context['caption_language']}
Image Type: {'Header' if context['image_type'] == 'header' else 'Section'}"""
                
                # Combine system prompt, task prompt, and context
                prompt = f"""{system_content}

{task_content}

{context_info}

Please generate a caption for this image:"""
                
                print(f"Using workflow prompts for captioning: System={system_prompt['name']}, Task={task_prompt['name']}")
            else:
                # Fallback to hardcoded prompts if workflow prompts not found
                print("Workflow prompts not found, using fallback prompts")
                if context['image_type'] == 'header':
                    prompt = f"""You are an expert image caption writer for blog posts.

Given the post context:
- Title: {context['post_title']}
- Subtitle: {context['post_subtitle']}
- Basic Idea: {context['basic_idea']}
- Idea Scope: {context['idea_scope']}

Generate a compelling, descriptive caption for this header image that:
1. Accurately describes what's shown
2. Connects to the blog post content
3. Is engaging and informative
4. Uses {context['caption_style'].lower()} style
5. Is written in {context['caption_language']}

Keep the caption concise (1-2 sentences) and avoid redundancy.
Return only the caption text, with no additional commentary or formatting."""
                else:
                    prompt = f"""You are an expert image caption writer for blog posts.

Given the post context:
- Title: {context['post_title']}
- Subtitle: {context['post_subtitle']}
- Basic Idea: {context['basic_idea']}
- Idea Scope: {context['idea_scope']}
- Section: {context['section_heading']}

Generate a compelling, descriptive caption for this section image that:
1. Accurately describes what's shown
2. Connects to the section content
3. Is engaging and informative
4. Uses {context['caption_style'].lower()} style
5. Is written in {context['caption_language']}

Keep the caption concise (1-2 sentences) and avoid redundancy.
Return only the caption text, with no additional commentary or formatting."""
        else:
            # Fallback to hardcoded prompts if API call fails
            print(f"Failed to fetch workflow prompts: {system_prompt_response.status_code}")
            if context['image_type'] == 'header':
                prompt = f"""You are an expert image caption writer for blog posts.

Given the post context:
- Title: {context['post_title']}
- Subtitle: {context['post_subtitle']}
- Basic Idea: {context['basic_idea']}
- Idea Scope: {context['idea_scope']}

Generate a compelling, descriptive caption for this header image that:
1. Accurately describes what's shown
2. Connects to the blog post content
3. Is engaging and informative
4. Uses {context['caption_style'].lower()} style
5. Is written in {context['caption_language']}

Keep the caption concise (1-2 sentences) and avoid redundancy.
Return only the caption text, with no additional commentary or formatting."""
            else:
                prompt = f"""You are an expert image caption writer for blog posts.

Given the post context:
- Title: {context['post_title']}
- Subtitle: {context['post_subtitle']}
- Basic Idea: {context['basic_idea']}
- Idea Scope: {context['idea_scope']}
- Section: {context['section_heading']}

Generate a compelling, descriptive caption for this section image that:
1. Accurately describes what's shown
2. Connects to the section content
3. Is engaging and informative
4. Uses {context['caption_style'].lower()} style
5. Is written in {context['caption_language']}

Keep the caption concise (1-2 sentences) and avoid redundancy.
Return only the caption text, with no additional commentary or formatting."""
        
        # Call LLM service directly via the test endpoint
        llm_response = requests.post(
            'http://localhost:5002/api/llm/test',
            json={
                'prompt': prompt,
                'model': 'mistral'
            },
            timeout=30
        )
        
        if llm_response.status_code == 200:
            result = llm_response.json()
            if result.get('status') == 'success':
                return result.get('response', '').strip()
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"LLM API error: {error_msg}")
                # Check if it's an Ollama connection error
                if 'Connection refused' in error_msg or '11434' in error_msg:
                    raise Exception("Ollama LLM service is not running. Please start Ollama to generate captions.")
                else:
                    raise Exception(f"LLM API error: {error_msg}")
        else:
            raise Exception(f"LLM API request failed: {llm_response.status_code}")
            
    except Exception as e:
        print(f"Error in generate_caption_via_llm: {e}")
        # Re-raise the exception instead of returning fallback captions
        raise e

def save_caption_to_database(image_info, caption, post_id):
    """Save caption to appropriate database field"""
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                if image_info['type'] == 'header':
                    # Save to post.header_image_caption
                    cur.execute("""
                        UPDATE post 
                        SET header_image_caption = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (caption, post_id))
                else:
                    # Save to post_section.image_captions
                    cur.execute("""
                        UPDATE post_section 
                        SET image_captions = %s
                        WHERE post_id = %s AND id = %s
                    """, (caption, post_id, image_info['section_id']))
                
                conn.commit()
                print(f"Saved caption for {image_info['filename']}: {caption[:50]}...")
                
    except Exception as e:
        print(f"Error saving caption to database: {e}")
        raise

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
        
        # Store header image selection in a simple file
        header_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'raw')
        if os.path.exists(os.path.join(header_path, filename)):
            # Create a selection file to track the selected header image
            selection_file = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'selected_image.txt')
            with open(selection_file, 'w') as f:
                f.write(filename)
            
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
        
        # Get header image selection from file
        header_selection_file = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'selected_image.txt')
        selected_header_filename = None
        if os.path.exists(header_selection_file):
            with open(header_selection_file, 'r') as f:
                selected_header_filename = f.read().strip()
        
        # Get section image selections from post_section table
        conn = get_db_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, image_filename 
            FROM post_section 
            WHERE post_id = %s AND image_filename IS NOT NULL
            ORDER BY id
        """, (post_id,))
        
        selected_sections = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Add header image if selected
        if selected_header_filename:
            header_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'raw')
            if os.path.exists(header_path):
                for filename in os.listdir(header_path):
                    if allowed_file(filename) and filename == selected_header_filename:
                        images.append({
                            'filename': filename,
                            'url': f'/static/content/posts/{post_id}/header/raw/{filename}',
                            'type': 'header',
                            'section_id': None,
                            'processing_stage': 'raw',
                            'is_selected': True
                        })
                        break  # Use the selected header image
        
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

@app.route('/api/images/<int:post_id>/watermarked')
def get_watermarked_images(post_id):
    """Get all watermarked images (header + sections) for a post"""
    return get_images_by_type(post_id, 'watermarked')

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

def generate_filename_from_title(title, max_length=50):
    """Generate a clean filename from a title."""
    import re
    
    # Convert to lowercase and replace spaces/special chars with underscores
    filename = re.sub(r'[^a-zA-Z0-9\s\-]', '', title.lower())
    filename = re.sub(r'[\s\-]+', '_', filename)
    filename = filename.strip('_')
    
    # Truncate if too long
    if len(filename) > max_length:
        filename = filename[:max_length].rstrip('_')
    
    return filename

def optimize_image(input_path, output_path, settings):
    """Optimize an image with the specified settings."""
    from PIL import Image
    
    # Parse settings (format: format_width_quality)
    parts = settings.split('_')
    format_type = parts[0]  # webp, jpeg, png
    max_width = int(parts[1])  # 800, 1200, 1600
    quality = int(parts[2]) if len(parts) > 2 else 85  # 85, 100
    
    # Open image
    with Image.open(input_path) as img:
        # Convert to RGB if necessary (for JPEG/WebP)
        if format_type in ['jpeg', 'webp'] and img.mode in ['RGBA', 'LA', 'P']:
            # Create white background for transparent images
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Calculate new dimensions
        width, height = img.size
        if width > max_width:
            ratio = max_width / width
            new_width = max_width
            new_height = int(height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save with appropriate settings
        if format_type == 'webp':
            img.save(output_path, 'WEBP', quality=quality, method=6)
        elif format_type == 'jpeg':
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
        elif format_type == 'png':
            if quality == 100:  # Lossless
                img.save(output_path, 'PNG', optimize=True)
            else:
                img.save(output_path, 'PNG', optimize=True, compress_level=9)
        
        return True

@app.route('/api/optimize/preview/<int:post_id>')
def preview_optimization(post_id):
    """Preview what files will be optimized during optimization."""
    try:
        preview = []
        settings = request.args.get('settings', 'webp_1200_85')  # Default to recommended settings
        
        # Get post title and section titles
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("SELECT title FROM post WHERE id = %s", (post_id,))
                post_result = cur.fetchone()
                post_title = post_result['title'] if post_result else f"post_{post_id}"
                
                # Get section titles and selections
                cur.execute("""
                    SELECT id, section_heading, image_filename 
                    FROM post_section 
                    WHERE post_id = %s 
                    ORDER BY section_order
                """, (post_id,))
                sections = cur.fetchall()
                section_titles = {str(section['id']): section['section_heading'] for section in sections}
                section_selections = {str(section['id']): section['image_filename'] for section in sections if section['image_filename']}
        
        # Determine file extension based on settings
        format_type = settings.split('_')[0]
        file_ext = format_type if format_type != 'jpeg' else 'jpg'
        
        # Preview header image selection
        header_selection_file = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'selected_image.txt')
        selected_header_filename = None
        if os.path.exists(header_selection_file):
            with open(header_selection_file, 'r') as f:
                selected_header_filename = f.read().strip()
        
        if selected_header_filename:
            header_new_name = f"{generate_filename_from_title(post_title)}.{file_ext}"
            preview.append({
                'type': 'header',
                'original': selected_header_filename,
                'new_name': header_new_name,
                'settings': settings
            })
        
        # Preview section image selections
        sections_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'sections')
        for section_id, selected_filename in section_selections.items():
            section_title = section_titles.get(section_id, f"Section {section_id}")
            section_new_name = f"{generate_filename_from_title(section_title)}.{file_ext}"
            preview.append({
                'type': 'section',
                'section_id': section_id,
                'original': selected_filename,
                'new_name': section_new_name,
                'settings': settings
            })
        
        # Add fallback images for sections without explicit selections
        for section_id in section_titles.keys():
            if section_id not in section_selections:
                # Use first available image in raw directory
                raw_dir = os.path.join(sections_path, section_id, 'raw')
                if os.path.exists(raw_dir):
                    for filename in os.listdir(raw_dir):
                        if allowed_file(filename):
                            section_title = section_titles.get(section_id, f"Section {section_id}")
                            section_new_name = f"{generate_filename_from_title(section_title)}.{file_ext}"
                            preview.append({
                                'type': 'section',
                                'section_id': section_id,
                                'original': filename,
                                'new_name': section_new_name,
                                'settings': settings
                            })
                            break
        
        return jsonify({
            'success': True,
            'preview': preview
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimize/rename/<int:post_id>', methods=['POST'])
def optimize_rename_images(post_id):
    """Optimize selected images and move them to optimized stage."""
    try:
        optimized_count = 0
        settings = request.json.get('settings', 'webp_1200_85') if request.json else 'webp_1200_85'
        
        # Get post title and section titles
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("SELECT title FROM post WHERE id = %s", (post_id,))
                post_result = cur.fetchone()
                post_title = post_result['title'] if post_result else f"post_{post_id}"
                
                # Get section titles and selections
                cur.execute("""
                    SELECT id, section_heading, image_filename 
                    FROM post_section 
                    WHERE post_id = %s 
                    ORDER BY section_order
                """, (post_id,))
                sections = cur.fetchall()
                section_titles = {str(section['id']): section['section_heading'] for section in sections}
                section_selections = {str(section['id']): section['image_filename'] for section in sections if section['image_filename']}
        
        # Determine file extension based on settings
        format_type = settings.split('_')[0]
        file_ext = format_type if format_type != 'jpeg' else 'jpg'
        
        # Process header image selection
        header_selection_file = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'selected_image.txt')
        selected_header_filename = None
        if os.path.exists(header_selection_file):
            with open(header_selection_file, 'r') as f:
                selected_header_filename = f.read().strip()
        
        if selected_header_filename:
            header_old_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'raw', selected_header_filename)
            header_new_name = f"{generate_filename_from_title(post_title)}.{file_ext}"
            header_new_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'optimized', header_new_name)
            
            # Create optimized directory
            os.makedirs(os.path.dirname(header_new_path), exist_ok=True)
            
            # Optimize and save image
            if os.path.exists(header_old_path):
                if optimize_image(header_old_path, header_new_path, settings):
                    optimized_count += 1
        
        # Process section images using the same logic as the selected endpoint
        sections_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'sections')
        for section_id in section_titles.keys():
            selected_filename = section_selections.get(section_id)
            section_processed = False
            
            if selected_filename:
                # Try to use the selected filename from database
                raw_path = os.path.join(sections_path, section_id, 'raw', selected_filename)
                if os.path.exists(raw_path):
                    section_old_path = raw_path
                    section_title = section_titles.get(section_id, f"Section {section_id}")
                    section_new_name = f"{generate_filename_from_title(section_title)}.{file_ext}"
                    section_new_path = os.path.join(sections_path, section_id, 'optimized', section_new_name)
                    
                    # Create optimized directory
                    os.makedirs(os.path.dirname(section_new_path), exist_ok=True)
                    
                    # Optimize and save image
                    if optimize_image(section_old_path, section_new_path, settings):
                        optimized_count += 1
                        section_processed = True
                else:
                    # Check optimized directory
                    optimized_path = os.path.join(sections_path, section_id, 'optimized', selected_filename)
                    if os.path.exists(optimized_path):
                        section_old_path = optimized_path
                        section_title = section_titles.get(section_id, f"Section {section_id}")
                        section_new_name = f"{generate_filename_from_title(section_title)}.{file_ext}"
                        section_new_path = os.path.join(sections_path, section_id, 'optimized', section_new_name)
                        
                        # Create optimized directory
                        os.makedirs(os.path.dirname(section_new_path), exist_ok=True)
                        
                        # Optimize and save image
                        if optimize_image(section_old_path, section_new_path, settings):
                            optimized_count += 1
                            section_processed = True
            
            # If not processed yet, use fallback to first available image
            if not section_processed:
                raw_dir = os.path.join(sections_path, section_id, 'raw')
                if os.path.exists(raw_dir):
                    for filename in os.listdir(raw_dir):
                        if allowed_file(filename):
                            section_old_path = os.path.join(raw_dir, filename)
                            section_title = section_titles.get(section_id, f"Section {section_id}")
                            section_new_name = f"{generate_filename_from_title(section_title)}.{file_ext}"
                            section_new_path = os.path.join(sections_path, section_id, 'optimized', section_new_name)
                            
                            # Create optimized directory
                            os.makedirs(os.path.dirname(section_new_path), exist_ok=True)
                            
                            # Optimize and save image
                            if optimize_image(section_old_path, section_new_path, settings):
                                optimized_count += 1
                                break
        
        return jsonify({
            'success': True,
            'optimized_count': optimized_count,
            'message': f'Successfully optimized and moved {optimized_count} images to optimized stage'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def load_watermark(watermark_path):
    """Load the watermark image."""
    try:
        from PIL import Image
        watermark = Image.open(watermark_path)
        return watermark
    except Exception as e:
        print(f"❌ Error loading watermark: {e}")
        return None

def get_font(size=20):
    """Get a font for text rendering."""
    try:
        from PIL import ImageFont
        # Try to use a system font
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", size)
    except:
        try:
            # Fallback to default font
            font = ImageFont.load_default()
        except:
            # Last resort - no font
            font = None
    
    return font

def add_watermark(image, watermark, position='bottom-right'):
    """Add watermark to image with 0% transparency against 80% transparent background."""
    if watermark is None:
        return image
    
    # Resize watermark to reasonable size (max 200px width)
    watermark_width = min(200, image.width // 4)
    watermark_height = int(watermark.height * (watermark_width / watermark.width))
    watermark_resized = watermark.resize((watermark_width, watermark_height), Image.Resampling.LANCZOS)
    
    # Create watermark with 0% transparency (fully visible)
    watermark_with_alpha = Image.new('RGBA', watermark_resized.size, (0, 0, 0, 0))
    watermark_with_alpha.paste(watermark_resized, (0, 0))
    
    # Calculate position with 10px margins
    margin = 10
    if position == 'bottom-right':
        x = image.width - watermark_width - margin
        y = image.height - watermark_height - margin
    else:
        x = margin
        y = image.height - watermark_height - margin
    
    # Create new image with alpha channel if needed
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Create grey background with 80% transparency (20% opacity)
    grey_bg = Image.new('RGBA', (watermark_width + 20, watermark_height + 20), (128, 128, 128, 51))  # Grey with 20% alpha (80% transparent)
    
    # Paste grey background first
    bg_x = x - 10
    bg_y = y - 10
    image.paste(grey_bg, (bg_x, bg_y), grey_bg)
    
    # Paste fully visible watermark
    image.paste(watermark_with_alpha, (x, y), watermark_with_alpha)
    
    return image

def add_ai_generated_text(image):
    """Add 'AI-generated image' text to bottom left."""
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    font = get_font(16)
    
    text = "AI-generated image"
    text_color = (128, 128, 128, 180)  # Grey with transparency
    
    # Calculate text position (bottom left with padding)
    if font:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    else:
        text_width = len(text) * 8  # Approximate width
        text_height = 16
    
    x = 20
    y = image.height - text_height - 20
    
    # Draw text
    if font:
        draw.text((x, y), text, fill=text_color, font=font)
    else:
        # Fallback without font
        draw.text((x, y), text, fill=text_color)
    
    return image

def watermark_single_image(image_path, watermark, output_path):
    """Process a single image with watermark and AI text."""
    try:
        from PIL import Image
        print(f"🖼️  Processing: {os.path.basename(image_path)}")
        print(f"DEBUG: Image path: {image_path}")
        print(f"DEBUG: Image path exists: {os.path.exists(image_path)}")
        print(f"DEBUG: Output path: {output_path}")
        
        # Load image
        image = Image.open(image_path)
        print(f"DEBUG: Image loaded successfully, size: {image.size}")
        
        # Add watermark
        image = add_watermark(image, watermark, 'bottom-right')
        print(f"DEBUG: Watermark added")
        
        # Add AI-generated text
        image = add_ai_generated_text(image)
        print(f"DEBUG: AI text added")
        
        # Save as WebP
        if output_path.endswith('.webp'):
            image.save(output_path, 'WEBP', quality=85, method=6)
        else:
            image.save(output_path, optimize=True)
        
        print(f"✅ Saved: {os.path.basename(output_path)}")
        return True
        
    except Exception as e:
        print(f"❌ Error processing {os.path.basename(image_path)}: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/api/watermark/preview/<int:post_id>')
def preview_watermarking(post_id):
    """Preview what images will be watermarked."""
    try:
        # Get selected images using the same logic as optimization
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get post title
                cur.execute("SELECT title FROM post WHERE id = %s", (post_id,))
                post_result = cur.fetchone()
                post_title = post_result['title'] if post_result else f"Post {post_id}"
                
                # Get section titles and selections
                cur.execute("""
                    SELECT id, section_heading, image_filename
                    FROM post_section 
                    WHERE post_id = %s 
                    ORDER BY section_order
                """, (post_id,))
                sections = cur.fetchall()
                section_titles = {str(section['id']): section['section_heading'] for section in sections}
                section_selections = {str(section['id']): section['image_filename'] for section in sections if section['image_filename']}
        
        preview_list = []
        
        # Process header image selection
        header_selection_file = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'selected_image.txt')
        selected_header_filename = None
        if os.path.exists(header_selection_file):
            with open(header_selection_file, 'r') as f:
                selected_header_filename = f.read().strip()
        
        if selected_header_filename:
            header_old_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'optimized', selected_header_filename)
            if os.path.exists(header_old_path):
                header_new_name = f"{generate_filename_from_title(post_title)}.webp"
                preview_list.append({
                    'type': 'header',
                    'original': selected_header_filename,
                    'new_name': header_new_name,
                    'title': post_title
                })
        
        # Process section images
        sections_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'sections')
        for section_id in section_titles.keys():
            selected_filename = section_selections.get(section_id)
            section_processed = False
            
            if selected_filename:
                # Try optimized directory first
                optimized_path = os.path.join(sections_path, section_id, 'optimized', selected_filename)
                if os.path.exists(optimized_path):
                    section_title = section_titles.get(section_id, f"Section {section_id}")
                    section_new_name = f"{generate_filename_from_title(section_title)}.webp"
                    preview_list.append({
                        'type': 'section',
                        'section_id': section_id,
                        'original': selected_filename,
                        'new_name': section_new_name,
                        'title': section_title
                    })
                    section_processed = True
                else:
                    # Try raw directory
                    raw_path = os.path.join(sections_path, section_id, 'raw', selected_filename)
                    if os.path.exists(raw_path):
                        section_title = section_titles.get(section_id, f"Section {section_id}")
                        section_new_name = f"{generate_filename_from_title(section_title)}.webp"
                        preview_list.append({
                            'type': 'section',
                            'section_id': section_id,
                            'original': selected_filename,
                            'new_name': section_new_name,
                            'title': section_title
                        })
                        section_processed = True
            
            # If not processed yet, use fallback to first available optimized image
            if not section_processed:
                optimized_dir = os.path.join(sections_path, section_id, 'optimized')
                if os.path.exists(optimized_dir):
                    for filename in os.listdir(optimized_dir):
                        if allowed_file(filename):
                            section_title = section_titles.get(section_id, f"Section {section_id}")
                            section_new_name = f"{generate_filename_from_title(section_title)}.webp"
                            preview_list.append({
                                'type': 'section',
                                'section_id': section_id,
                                'original': filename,
                                'new_name': section_new_name,
                                'title': section_title
                            })
                            break
        
        return jsonify({
            'success': True,
            'preview': preview_list,
            'count': len(preview_list)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watermark/process/<int:post_id>', methods=['POST'])
def process_watermarking(post_id):
    """Process watermarking for a post."""
    try:
        from PIL import Image
        
        # Load watermark
        watermark_path = os.path.join('static', 'images', 'site', 'clan-watermark.png')
        watermark = load_watermark(watermark_path)
        if watermark is None:
            return jsonify({'error': 'Could not load watermark image'}), 500
        
        watermarked_count = 0
        
        # Get post and section data
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get post title
                cur.execute("SELECT title FROM post WHERE id = %s", (post_id,))
                post_result = cur.fetchone()
                post_title = post_result['title'] if post_result else f"Post {post_id}"
                
                # Get section titles and selections
                cur.execute("""
                    SELECT id, section_heading, image_filename
                    FROM post_section 
                    WHERE post_id = %s 
                    ORDER BY section_order
                """, (post_id,))
                sections = cur.fetchall()
                section_titles = {str(section['id']): section['section_heading'] for section in sections}
                section_selections = {str(section['id']): section['image_filename'] for section in sections if section['image_filename']}
        
        # Process header image - process all optimized images
        header_optimized_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'optimized')
        print(f"DEBUG: Processing header optimized dir: {header_optimized_dir}")
        if os.path.exists(header_optimized_dir):
            for filename in os.listdir(header_optimized_dir):
                if allowed_file(filename):
                    header_old_path = os.path.join(header_optimized_dir, filename)
                    header_new_name = f"{generate_filename_from_title(post_title)}.webp"
                    header_new_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'watermarked', header_new_name)
                    
                    print(f"DEBUG: Processing header image: {header_old_path} -> {header_new_path}")
                    
                    # Create watermarked directory
                    os.makedirs(os.path.dirname(header_new_path), exist_ok=True)
                    
                    # Process image
                    if watermark_single_image(header_old_path, watermark, header_new_path):
                        watermarked_count += 1
                        print(f"DEBUG: Successfully watermarked header image")
                    else:
                        print(f"DEBUG: Failed to watermark header image")
        
        # Process section images - process all optimized images
        sections_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'sections')
        print(f"DEBUG: Processing sections path: {sections_path}")
        for section_id in section_titles.keys():
            optimized_dir = os.path.join(sections_path, section_id, 'optimized')
            print(f"DEBUG: Processing section {section_id} optimized dir: {optimized_dir}")
            if os.path.exists(optimized_dir):
                for filename in os.listdir(optimized_dir):
                    if allowed_file(filename):
                        section_old_path = os.path.join(optimized_dir, filename)
                        section_title = section_titles.get(section_id, f"Section {section_id}")
                        section_new_name = f"{generate_filename_from_title(section_title)}.webp"
                        section_new_path = os.path.join(sections_path, section_id, 'watermarked', section_new_name)
                        
                        print(f"DEBUG: Processing section image: {section_old_path} -> {section_new_path}")
                        
                        # Create watermarked directory
                        os.makedirs(os.path.dirname(section_new_path), exist_ok=True)
                        
                        # Process image
                        if watermark_single_image(section_old_path, watermark, section_new_path):
                            watermarked_count += 1
                            print(f"DEBUG: Successfully watermarked section {section_id} image")
                        else:
                            print(f"DEBUG: Failed to watermark section {section_id} image")
        
        return jsonify({
            'success': True,
            'watermarked_count': watermarked_count,
            'message': f'Successfully watermarked {watermarked_count} images'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watermark/test/<int:post_id>')
def test_watermark_loading(post_id):
    """Test watermark loading and image processing."""
    try:
        from PIL import Image
        
        # Test watermark loading
        watermark_path = os.path.join('static', 'images', 'site', 'clan-watermark.png')
        print(f"DEBUG: Testing watermark path: {watermark_path}")
        print(f"DEBUG: Watermark path exists: {os.path.exists(watermark_path)}")
        
        watermark = load_watermark(watermark_path)
        if watermark is None:
            return jsonify({'error': 'Could not load watermark image'}), 500
        
        # Test finding optimized images
        header_optimized_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'optimized')
        print(f"DEBUG: Header optimized dir: {header_optimized_dir}")
        print(f"DEBUG: Header optimized dir exists: {os.path.exists(header_optimized_dir)}")
        
        if os.path.exists(header_optimized_dir):
            files = os.listdir(header_optimized_dir)
            print(f"DEBUG: Files in header optimized dir: {files}")
        
        # Test section images
        sections_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'sections')
        print(f"DEBUG: Sections path: {sections_path}")
        print(f"DEBUG: Sections path exists: {os.path.exists(sections_path)}")
        
        if os.path.exists(sections_path):
            for section_dir in os.listdir(sections_path):
                optimized_dir = os.path.join(sections_path, section_dir, 'optimized')
                if os.path.exists(optimized_dir):
                    files = os.listdir(optimized_dir)
                    print(f"DEBUG: Files in {section_dir}/optimized: {files}")
        
        return jsonify({
            'success': True,
            'watermark_loaded': watermark is not None,
            'header_optimized_dir': header_optimized_dir,
            'header_optimized_exists': os.path.exists(header_optimized_dir),
            'sections_path': sections_path,
            'sections_exists': os.path.exists(sections_path)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watermark/stats/<int:post_id>')
def get_watermarked_stats(post_id):
    """Get statistics for watermarked images."""
    try:
        total_count = 0
        total_size = 0
        
        # Count header watermarked images
        header_watermarked_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'header', 'watermarked')
        if os.path.exists(header_watermarked_dir):
            for filename in os.listdir(header_watermarked_dir):
                if allowed_file(filename):
                    file_path = os.path.join(header_watermarked_dir, filename)
                    total_count += 1
                    total_size += os.path.getsize(file_path)
        
        # Count section watermarked images
        sections_path = os.path.join(app.config['UPLOAD_FOLDER'], str(post_id), 'sections')
        if os.path.exists(sections_path):
            for section_dir in os.listdir(sections_path):
                section_watermarked_dir = os.path.join(sections_path, section_dir, 'watermarked')
                if os.path.exists(section_watermarked_dir):
                    for filename in os.listdir(section_watermarked_dir):
                        if allowed_file(filename):
                            file_path = os.path.join(section_watermarked_dir, filename)
                            total_count += 1
                            total_size += os.path.getsize(file_path)
        
        return jsonify({
            'watermarked_count': total_count,
            'watermarked_size': total_size
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/captions/<int:post_id>')
def get_captions(post_id):
    """Get all captions for a post"""
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get post data with header caption
                cur.execute("""
                    SELECT p.title, p.header_image_caption
                    FROM post p
                    WHERE p.id = %s
                """, (post_id,))
                post_data = cur.fetchone()
                
                # Get section data with captions
                cur.execute("""
                    SELECT id, section_heading, image_captions
                    FROM post_section
                    WHERE post_id = %s
                    ORDER BY section_order
                """, (post_id,))
                sections = cur.fetchall()
        
        captions = {
            'header': {
                'caption': post_data['header_image_caption'] if post_data else None,
                'title': post_data['title'] if post_data else None
            },
            'sections': [
                {
                    'id': section['id'],
                    'section_heading': section['section_heading'],
                    'caption': section['image_captions']
                }
                for section in sections
            ]
        }
        
        return jsonify({
            'success': True,
            'captions': captions
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/caption/prompt', methods=['POST'])
def get_caption_prompt():
    """Get the current caption prompt that would be sent to the LLM"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        caption_style = data.get('caption_style', 'Descriptive')
        caption_language = data.get('caption_language', 'English')
        
        # Get post context
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT p.title, p.subtitle, pd.basic_idea, pd.idea_scope
                    FROM post p
                    LEFT JOIN post_development pd ON p.id = pd.post_id
                    WHERE p.id = %s
                """, (post_id,))
                post_data = cur.fetchone()
                
                if not post_data:
                    return jsonify({'success': False, 'error': 'Post not found'}), 404
                
                # Get a sample section for context
                cur.execute("""
                    SELECT section_heading
                    FROM post_section 
                    WHERE post_id = %s
                    LIMIT 1
                """, (post_id,))
                section_data = cur.fetchone()
                section_heading = section_data['section_heading'] if section_data else "Sample Section"
        
        # Fetch prompts from workflow system
        system_prompt_response = requests.get('http://localhost:5000/api/workflow/prompts/all')
        if system_prompt_response.status_code == 200:
            prompts = system_prompt_response.json()
            
            # Find the image captions system prompt (ID 110)
            system_prompt = next((p for p in prompts if p['id'] == 110), None)
            # Find the image captions task prompt (ID 111)
            task_prompt = next((p for p in prompts if p['id'] == 111), None)
            
            if system_prompt and task_prompt:
                # Construct the full prompt using system and task prompts
                system_content = system_prompt.get('prompt_text', '')
                task_content = task_prompt.get('prompt_text', '')
                
                # Build context information
                context_info = f"""Post Context:
- Title: {post_data['title']}
- Subtitle: {post_data['subtitle']}
- Basic Idea: {post_data['basic_idea']}
- Idea Scope: {post_data['idea_scope']}
- Section: {section_heading}
Caption Style: {caption_style}
Caption Language: {caption_language}
Image Type: Section"""
                
                # Combine system prompt, task prompt, and context
                full_prompt = f"""{system_content}

{task_content}

{context_info}

Please generate a caption for this image:"""
                
                return jsonify({
                    'success': True,
                    'prompt': full_prompt
                })
            else:
                # Fallback to hardcoded prompts
                fallback_prompt = f"""You are an expert image caption writer for blog posts.

Given the post context:
- Title: {post_data['title']}
- Subtitle: {post_data['subtitle']}
- Basic Idea: {post_data['basic_idea']}
- Idea Scope: {post_data['idea_scope']}
- Section: {section_heading}

Generate a compelling, descriptive caption for this section image that:
1. Accurately describes what's shown
2. Connects to the section content
3. Is engaging and informative
4. Uses {caption_style.lower()} style
5. Is written in {caption_language}

Keep the caption concise (1-2 sentences) and avoid redundancy.
Return only the caption text, with no additional commentary or formatting."""
                
                return jsonify({
                    'success': True,
                    'prompt': fallback_prompt
                })
        else:
            # Fallback to hardcoded prompts if API call fails
            fallback_prompt = f"""You are an expert image caption writer for blog posts.

Given the post context:
- Title: {post_data['title']}
- Subtitle: {post_data['subtitle']}
- Basic Idea: {post_data['basic_idea']}
- Idea Scope: {post_data['idea_scope']}
- Section: {section_heading}

Generate a compelling, descriptive caption for this section image that:
1. Accurately describes what's shown
2. Connects to the section content
3. Is engaging and informative
4. Uses {caption_style.lower()} style
5. Is written in {caption_language}

Keep the caption concise (1-2 sentences) and avoid redundancy.
Return only the caption text, with no additional commentary or formatting."""
            
            return jsonify({
                'success': True,
                'prompt': fallback_prompt
            })
                
    except Exception as e:
        print(f"Error getting caption prompt: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=port) 