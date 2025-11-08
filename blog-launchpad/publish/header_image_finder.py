"""
Header Image Finder
Single source of truth for finding header images for posts.
"""

import os
import urllib.parse
import logging
from config.database import db_manager

logger = logging.getLogger(__name__)


def find_header_image_filesystem(post_id):
    """
    Find header image on filesystem.
    ALL images are in project_root/static/ - no fallbacks.
    Returns web path or None.
    """
    # Get project root (this file is in blog-launchpad/publish/, go up two levels to project root)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    # ALL images are in project_root/static/ - no fallbacks
    project_static = os.path.join(project_root, 'static')
    
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')
    image_types = ['optimized', 'watermarked', 'raw']  # Check optimized first
    
    # Check project_root/static/ only
    for image_type in image_types:
        header_path = os.path.join(project_static, "content", "posts", str(post_id), "header", image_type)
        if os.path.exists(header_path):
            image_files = [f for f in os.listdir(header_path)
                          if f.lower().endswith(image_extensions) and not f.startswith('.')]
            if image_files:
                # Sort to prefer 'header.*' filenames, then any image
                image_files.sort(key=lambda x: (not x.lower().startswith('header'), x.lower()))
                image_filename = image_files[0]
                # DO NOT URL-encode - use filename as-is for consistency with database paths
                web_path = f"/static/content/posts/{post_id}/header/{image_type}/{image_filename}"
                logger.info(f"Found header image on filesystem: {web_path} (from {len(image_files)} files)")
                return web_path
    
    logger.warning(f"No header image found on filesystem for post {post_id}")
    return None


def load_header_image_from_db(post_id):
    """
    Load header image from post_images table.
    Tries images table first, then falls back to image table (for FK constraint compatibility).
    Returns dict with path, alt_text, caption, width, height or None.
    """
    try:
        with db_manager.get_cursor() as cursor:
            # First try images table (new schema)
            cursor.execute("""
                SELECT i.file_path, i.filename, i.alt_text, i.caption, i.width, i.height, pi.image_type
                FROM post_images pi
                JOIN images i ON pi.image_id = i.id
                WHERE pi.post_id = %s AND pi.image_type LIKE 'header%%'
                ORDER BY CASE WHEN pi.image_type = 'header_optimized' THEN 1 
                              WHEN pi.image_type = 'header_watermarked' THEN 2
                              ELSE 3 END
                LIMIT 1
            """, (post_id,))
            
            img_row = cursor.fetchone()
            if img_row and img_row.get('file_path'):
                header_path = img_row['file_path']
                # CRITICAL: Normalize path to ALWAYS be /static/content/posts/... format
                # Remove any leading slashes, then ensure it starts with /static/
                header_path = header_path.lstrip('/')
                if not header_path.startswith('static/'):
                    header_path = 'static/' + header_path.lstrip('/')
                header_path = '/' + header_path  # Add leading slash
                logger.info(f"Normalized header path: {repr(img_row['file_path'])} -> {repr(header_path)}")
                
                header_image = {
                    'path': header_path,
                    'alt_text': img_row.get('alt_text'),
                    'title': img_row.get('filename'),
                    'caption': img_row.get('caption'),
                    'width': img_row.get('width'),
                    'height': img_row.get('height')
                }
                logger.info(f"Found header image in database (images table): {header_path}")
                return header_image
            
            # Fallback to image table (old schema) - for FK constraint compatibility
            cursor.execute("""
                SELECT i.path as file_path, i.filename, i.alt_text, i.caption, NULL as width, NULL as height, pi.image_type
                FROM post_images pi
                JOIN image i ON pi.image_id = i.id
                WHERE pi.post_id = %s AND pi.image_type LIKE 'header%%'
                ORDER BY CASE WHEN pi.image_type = 'header_optimized' THEN 1 
                              WHEN pi.image_type = 'header_watermarked' THEN 2
                              ELSE 3 END
                LIMIT 1
            """, (post_id,))
            
            img_row = cursor.fetchone()
            if img_row and img_row.get('file_path'):
                header_path = img_row['file_path']
                # CRITICAL: Normalize path to ALWAYS be /static/content/posts/... format
                # Remove any leading slashes, then ensure it starts with /static/
                header_path = header_path.lstrip('/')
                if not header_path.startswith('static/'):
                    header_path = 'static/' + header_path.lstrip('/')
                header_path = '/' + header_path  # Add leading slash
                logger.info(f"Normalized header path (image table): {repr(img_row['file_path'])} -> {repr(header_path)}")
                
                header_image = {
                    'path': header_path,
                    'alt_text': img_row.get('alt_text'),
                    'title': img_row.get('filename'),
                    'caption': img_row.get('caption'),
                    'width': img_row.get('width'),
                    'height': img_row.get('height')
                }
                logger.info(f"Found header image in database (image table): {header_path}")
                return header_image
    
    except Exception as e:
        logger.error(f"Error loading header image from database: {e}")
    
    return None


def get_header_image(post_id):
    """
    Main function to get header image for a post.
    Tries database first, then filesystem.
    Returns dict with path, alt_text, caption, width, height or None.
    """
    # Try database first
    header_image = load_header_image_from_db(post_id)
    if header_image:
        return header_image
    
    # Fallback to filesystem
    header_path = find_header_image_filesystem(post_id)
    if header_path:
        return {
            'path': header_path,
            'alt_text': None,
            'title': None,
            'caption': None,
            'width': None,
            'height': None
        }
    
    logger.warning(f"No header image found for post {post_id}")
    return None

