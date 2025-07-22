from flask import Flask, render_template, jsonify, request, redirect
import requests
import os
from datetime import datetime
import pytz
from humanize import naturaltime
import psycopg2.extras

app = Flask(__name__, template_folder="templates", static_folder="static")

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

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'blog-launchpad'})

@app.route('/preview/<int:post_id>')
def preview_post(post_id):
    """Preview a specific post."""
    # Get post data from database
    post = get_post_with_development(post_id)
    if not post:
        return "Post not found", 404
    
    sections = get_post_sections_with_images(post_id)
    
    return render_template('post_preview.html', post=post, sections=sections)

def get_post_with_development(post_id):
    """Fetch post with development data."""
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get post data, alias post.id as post_id
        cur.execute("""
            SELECT p.id AS post_id, p.*, pd.*
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
                image_prompts, watermarking,
                image_meta_descriptions, image_captions, image_prompt_example_id,
                generated_image_url, image_generation_metadata, image_id, status
            FROM post_section 
            WHERE post_id = %s 
            ORDER BY section_order
        """, (post_id,))
        
        raw_sections = cur.fetchall()
        sections = []
        
        for section in raw_sections:
            section_dict = dict(section)
            
            # Get section image if exists
            if section.get('image_id'):
                cur.execute("""
                    SELECT * FROM image WHERE id = %s
                """, (section['image_id'],))
                image = cur.fetchone()
                if image:
                    section_dict['image'] = dict(image)
            elif section.get('generated_image_url'):
                # Handle direct image URLs from generated_image_url
                section_dict['image'] = {
                    'path': section['generated_image_url'],
                    'alt_text': section.get('image_captions') or 'Section image'
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
                   pd.idea_seed, pd.provisional_title, pd.intro_blurb
            FROM post p
            LEFT JOIN post_development pd ON p.id = pd.post_id
            WHERE p.status != 'deleted'
            ORDER BY p.created_at DESC
        """)
        posts = cur.fetchall()
        return jsonify([dict(post) for post in posts])

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port) 