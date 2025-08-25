from datetime import datetime
from flask import Blueprint, render_template, abort, current_app
import psycopg2.extras

bp = Blueprint('preview', __name__)

def get_db_conn():
    """Get database connection."""
    import psycopg2
    return psycopg2.connect('postgresql://nickfiddes@localhost/blog', connect_timeout=5)

def analyze_content_priority(section):
    """
    Analyze which content version is best available based on priority:
    1. polished (highest quality) - Final publication-ready content
    2. draft (basic content) - Initial raw content
    3. placeholder (missing content) - When none available
    """
    if section.get('polished') and section['polished'].strip():
        return {'stage': 'polished', 'quality': 'highest', 'content': section['polished']}
    elif section.get('draft') and section['draft'].strip():
        return {'stage': 'draft', 'quality': 'basic', 'content': section['draft']}
    else:
        return {'stage': 'placeholder', 'quality': 'missing', 'content': None}

def get_missing_stages(section):
    """Return list of missing content stages"""
    stages = ['polished', 'draft']
    return [stage for stage in stages if not section.get(stage) or not section[stage].strip()]

def get_content_class(section):
    """Get CSS class based on content priority"""
    priority = analyze_content_priority(section)
    return f"content-{priority['stage']}"

def get_best_content(section):
    """Get the best available content for a section"""
    priority = analyze_content_priority(section)
    return priority['content']

def is_placeholder(section):
    """Check if section needs a placeholder"""
    priority = analyze_content_priority(section)
    return priority['stage'] == 'placeholder'

def get_missing_stage(section):
    """Get the next missing stage for placeholder display"""
    missing = get_missing_stages(section)
    return missing[0] if missing else 'content'

def get_post_with_development(post_id):
    """Fetch post with development data"""
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get post data
        cur.execute("""
            SELECT p.*, pd.*
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
        
        return dict(post)

def get_post_sections_with_images(post_id):
    """Fetch sections with complete image metadata"""
    print(f"DEBUG: Getting sections for post {post_id}")  # Debug print
    
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # First, let's check if any sections exist
        cur.execute("SELECT COUNT(*) as count FROM post_section WHERE post_id = %s", (post_id,))
        count_result = cur.fetchone()
        print(f"DEBUG: Found {count_result['count']} sections in database")  # Debug print
        
        # Get all sections for the post - using the actual database schema
        cur.execute("""
            SELECT 
                id, post_id, section_order, 
                section_heading,
                section_description, ideas_to_include, facts_to_include,
                draft, polished, highlighting, image_concepts,
                image_prompts,
                image_meta_descriptions, image_captions,
                image_filename, image_generated_at, image_title, image_width, image_height, status
            FROM post_section 
            WHERE post_id = %s 
            ORDER BY section_order
        """, (post_id,))
        
        raw_sections = cur.fetchall()
        print(f"DEBUG: Raw query returned {len(raw_sections)} sections")  # Debug print
        
        sections = []
        for section in raw_sections:
            section_dict = dict(section)
            print(f"DEBUG: Processing section {section_dict.get('id')} with heading: {section_dict.get('section_heading', 'No heading')}")  # Debug print
            
            # Get section image if exists - handle image_filename field
            if section.get('image_filename'):
                # Construct the image path from the filename
                image_path = f"/static/uploads/images/{section['image_filename']}"
                section_dict['image'] = {
                    'path': image_path,
                    'alt_text': section.get('image_captions') or 'Section image',
                    'title': section.get('image_title'),
                    'width': section.get('image_width'),
                    'height': section.get('image_height')
                }
            
            # Add content priority analysis
            section_dict['content_priority'] = analyze_content_priority(section_dict)
            section_dict['missing_stages'] = get_missing_stages(section_dict)
            
            sections.append(section_dict)
        
        print(f"DEBUG: Returning {len(sections)} processed sections")  # Debug print
        return sections

@bp.route('/')
def listing():
    # Try to get real posts from database first
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.id, p.title, p.created_at, p.updated_at,
                       pd.idea_seed, pd.provisional_title, pd.intro_blurb
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.status != 'deleted'
                ORDER BY p.created_at DESC
                LIMIT 20
            """)
            posts_data = cur.fetchall()
            
            if posts_data:
                posts = []
                for post_data in posts_data:
                    posts.append({
                        'id': post_data['id'],
                        'title': post_data['title'] or post_data['provisional_title'] or 'Untitled Post',
                        'date': post_data['created_at'].strftime('%Y-%m-%d') if post_data['created_at'] else 'Unknown',
                        'author': 'nick-fiddes',  # Default author
                        'summary': post_data['intro_blurb'] or post_data['idea_seed'] or 'No summary available.',
                        'created_at': post_data['created_at'] or datetime.now()
                    })
                return render_template('preview/listing.html', posts=posts)
    
    # Fallback to empty list if no posts found in database
    return render_template('preview/listing.html', posts=[])

@bp.route('/<int:post_id>/')
def post_detail(post_id):
    print(f"DEBUG: Preview route called for post {post_id}")  # Debug print
    
    # Fetch real post data with development and sections
    post = get_post_with_development(post_id)
    if not post:
        current_app.logger.error(f"Post {post_id} not found")
        return "Post not found", 404
    
    sections = get_post_sections_with_images(post_id)
    print(f"DEBUG: Found {len(sections)} sections")  # Debug print
    
    # Debug logging
    current_app.logger.info(f"Preview for post {post_id}: found {len(sections)} sections")
    for i, section in enumerate(sections):
        current_app.logger.info(f"Section {i+1}: {section.get('section_heading', 'No heading')} - Priority: {section.get('content_priority', {}).get('stage', 'unknown')}")
    
    # Add helper functions to template context
    template_context = {
        'post': post,
        'sections': sections,
        'get_content_class': get_content_class,
        'get_best_content': get_best_content,
        'is_placeholder': is_placeholder,
        'get_missing_stage': get_missing_stage
    }
    
    print(f"DEBUG: Template context - post: {post.get('title', 'No title')}, sections count: {len(sections)}")  # Debug print
    
    try:
        return render_template('preview_post.html', **template_context)
    except Exception as e:
        print(f"DEBUG: Template error: {e}")  # Debug print
        current_app.logger.error(f"Template error: {e}")
        return f"Template error: {e}", 500 