# blueprints/launchpad/publishing_helpers.py
"""Helper functions for publishing-related functionality."""

import logging
from config.database import db_manager
import os

logger = logging.getLogger(__name__)


def get_post_with_development(post_id):
    """Fetch post with development data and include image paths."""
    with db_manager.get_cursor() as cursor:
        # Get post data, alias post.id as post_id
        cursor.execute("""
            SELECT p.id AS post_id, p.title, p.subtitle, p.created_at, p.updated_at, p.status, p.slug, p.summary, p.title_choices,
                   p.clan_post_id, p.clan_uploaded_url,
                   p.header_image_id, p.header_image_caption, p.header_image_title, p.header_image_width, p.header_image_height,
                   pd.idea_seed, pd.intro_blurb, pd.main_title,
                   p.cross_promotion_category_id, p.cross_promotion_category_title,
                   p.cross_promotion_product_id, p.cross_promotion_product_title,
                   p.cross_promotion_category_position, p.cross_promotion_product_position,
                   p.cross_promotion_category_widget_html, p.cross_promotion_product_widget_html,
                   p.meta_title, p.meta_description, p.meta_tags, p.meta_image, p.meta_type, p.meta_site_name
            FROM post p
            LEFT JOIN post_development pd ON pd.post_id = p.id
            WHERE p.id = %s
        """, (post_id,))
        
        post = cursor.fetchone()
        if not post:
            return None
        
        post_dict = dict(post)
        
        # Get header image using the SAME function as preview
        import sys
        import os
        blog_launchpad_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'blog-launchpad')
        sys.path.insert(0, blog_launchpad_path)
        from publish.header_image_finder import get_header_image
        header_image = get_header_image(post_id)
        if header_image:
            post_dict['header_image'] = header_image
            # Add metadata from post table if not already set
            if not post_dict['header_image'].get('caption') and post_dict.get('header_image_caption'):
                post_dict['header_image']['caption'] = post_dict.get('header_image_caption')
            if not post_dict['header_image'].get('title') and post_dict.get('header_image_title'):
                post_dict['header_image']['title'] = post_dict.get('header_image_title')
            if not post_dict['header_image'].get('width') and post_dict.get('header_image_width'):
                post_dict['header_image']['width'] = post_dict.get('header_image_width')
            if not post_dict['header_image'].get('height') and post_dict.get('header_image_height'):
                post_dict['header_image']['height'] = post_dict.get('header_image_height')
        
        return post_dict

def get_post_sections_with_images(post_id):
    """Fetch sections with complete image metadata from post_images linking table (matches preview data)."""
    with db_manager.get_cursor() as cursor:
        # Get all sections with images via post_images linking table (same as preview route)
        cursor.execute("""
            SELECT 
                ps.id, ps.post_id, ps.section_order, 
                ps.section_heading,
                ps.section_description, ps.ideas_to_include, ps.facts_to_include,
                ps.draft, ps.polished, ps.highlighting, ps.image_concepts,
                ps.image_prompts,
                ps.image_alt_text, ps.image_captions, ps.status,
                i.id AS image_id,
                i.filename,
                i.file_path AS image_path,
                i.alt_text AS image_alt_text,
                i.caption AS image_caption
            FROM post_section ps
            LEFT JOIN post_images pi ON ps.id = pi.section_id AND pi.image_type = 'section_optimized'
            LEFT JOIN images i ON pi.image_id = i.id
            WHERE ps.post_id = %s
            ORDER BY ps.section_order
        """, (post_id,))
        
        raw_sections = cursor.fetchall()
        sections = []
        
        for section in raw_sections:
            section_dict = dict(section)
            
            # Priority 1: Check Photo-harvesting route (selected_landscape.json)
            image_path = None
            caption_text = section_dict.get('image_captions') or ''
            alt_text = section_dict.get('image_alt_text') or ''
            
            try:
                import json
                photo_json_path = f"static/content/posts/{post_id}/sections/{section_dict['id']}/optimized/selected_landscape.json"
                if os.path.exists(photo_json_path):
                    with open(photo_json_path, 'r') as f:
                        photo_data = json.load(f)
                        photo = photo_data.get('photo', {})
                        if photo.get('url'):
                            # Use hotlinked provider URL (Pexels/Unsplash)
                            image_path = photo['url']
                            # Extract caption/alt from photo metadata if not already set
                            if not caption_text and photo.get('credits'):
                                caption_text = photo['credits']
                            if not alt_text and photo.get('photographer'):
                                alt_text = f"Photo by {photo['photographer']}"
            except Exception as e:
                logger.debug(f"Could not load Photo-harvesting JSON for section {section_dict['id']}: {e}")
            
            # Priority 2: Database link (post_images)
            if not image_path:
                image_path = section_dict.get('image_path')
            
            if image_path:
                # Image exists (Photo-harvesting or post_images linking table)
                section_dict['image'] = {
                    'path': image_path,
                    'caption': caption_text,
                    'alt_text': alt_text,
                    'placeholder': False
                }
            else:
                section_dict['image'] = None
            
            sections.append(section_dict)
        
        return sections

def find_header_image(post_id):
    """Find header image for a post."""
    import urllib.parse
    from config.paths import path_resolver
    
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')

    # Priority order: watermarked -> optimized -> raw
    image_types = ['watermarked', 'optimized', 'raw']
    
    for image_type in image_types:
        header_path = path_resolver.get_header_image_path(post_id, image_type)
        if os.path.exists(header_path):
            image_files = [f for f in os.listdir(header_path)
                          if f.lower().endswith(image_extensions) and not f.startswith('.')]
            if image_files:
                image_filename = image_files[0]
                # URL-encode the filename to handle spaces and special characters
                encoded_filename = urllib.parse.quote(image_filename)
                return f"/static/content/posts/{post_id}/header/{image_type}/{encoded_filename}"
    
    return None

