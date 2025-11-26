"""
Preview Route Handlers
Handles preview routes for blog posts.
"""

import logging
from flask import render_template
from .post_data_loader import prepare_post_data
from .post_renderer import render_post_html

logger = logging.getLogger(__name__)


def preview_post(post_id):
    """
    Preview a specific post.
    Renders HTML fresh each time (no caching).
    Shows EXACT HTML that will be published (verbatim, except image paths).
    The preview template wrapper provides UI (title, header image, etc.) but does NOT modify the content.
    """
    # Use unified data preparation
    post, sections = prepare_post_data(post_id)
    if not post:
        return "Post not found", 404
    
    # Render HTML using unified rendering function (no image replacements for preview)
    # This is the EXACT HTML that will be published
    html_content = render_post_html(post, sections, image_replacements=None)
    
    # NO CACHING - always generate fresh HTML
    
    # Wrap in preview template (for UI elements: title, header image, red divider, etc.)
    # The rendered_content is the EXACT HTML that will be published - template just wraps it
    # Try launchpad template first, then fallback to main templates
    from flask import current_app
    try:
        # Try launchpad template path
        return render_template('launchpad/post_preview.html', post=post, sections=sections, rendered_content=html_content)
    except Exception:
        # Fallback to direct path if launchpad subfolder doesn't work
        # This handles both unified_app (templates/launchpad/) and blog-launchpad/app.py (templates/)
        try:
            return render_template('post_preview.html', post=post, sections=sections, rendered_content=html_content)
        except Exception as e:
            logger.error(f"Template not found: {e}")
            # Last resort: check if we're in unified_app and template is in launchpad subfolder
            import os
            template_paths = [
                os.path.join(current_app.template_folder, 'launchpad', 'post_preview.html'),
                os.path.join(current_app.template_folder, 'post_preview.html'),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'post_preview.html'),
            ]
            for path in template_paths:
                if os.path.exists(path):
                    logger.info(f"Found template at: {path}")
                    # Use direct file rendering as last resort
                    with open(path, 'r', encoding='utf-8') as f:
                        from jinja2 import Template
                        template = Template(f.read())
                        return template.render(post=post, sections=sections, rendered_content=html_content)
            raise


def clan_post_html(post_id):
    """View the clan_post HTML that will be uploaded to Clan.com."""
    from flask import request
    import psycopg
    import psycopg.rows
    
    # Get view type parameter (default to 'local')
    view_type_param = request.args.get('view', 'local')
    
    # Use unified data preparation
    post, sections = prepare_post_data(post_id)
    if not post:
        return "Post not found", 404
    
    if view_type_param == 'local':
        # Return raw HTML with local paths (for development/debugging)
        # Use unified rendering function (no image replacements)
        raw_html = render_post_html(post, sections, image_replacements=None)
        return raw_html, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    else:
        # Return processed HTML with CDN URLs (what gets sent to Clan.com)
        # Get uploaded images mapping from database
        from .post_data_loader import get_db_connection
        uploaded_images = {}
        try:
            with get_db_connection() as conn:
                cur = conn.cursor(row_factory=psycopg.rows.dict_row)
                cur.execute("""
                    SELECT local_image_path, clan_uploaded_url 
                    FROM section_image_mappings 
                    WHERE post_id = %s
                """, (post_id,))
                
                for row in cur.fetchall():
                    uploaded_images[row['local_image_path']] = row['clan_uploaded_url']
                    
                # Also get header image mapping if it exists
                cur.execute("""
                    SELECT local_image_path, clan_uploaded_url 
                    FROM section_image_mappings 
                    WHERE post_id = %s AND section_id IS NULL
                """, (post_id,))
                
                for row in cur.fetchall():
                    uploaded_images[row['local_image_path']] = row['clan_uploaded_url']
                    
        except Exception as e:
            logger.warning(f"Could not load image mappings: {e}")
        
        # Use unified rendering function WITH image replacements (published version)
        upload_html = render_post_html(post, sections, image_replacements=uploaded_images)
        
        if not upload_html:
            return "Failed to render HTML with image replacements", 500
        
        # Return the actual upload HTML as raw text - NO RENDERING
        # Set content type to text/plain so browser shows source code
        return upload_html, 200, {'Content-Type': 'text/plain; charset=utf-8'}

