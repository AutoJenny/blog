"""
Post Data Loader
Loads and prepares post data for publication.
"""

import logging
import sys
import os

# Add parent directory to path to import from app.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import get_post_with_development, get_post_sections_with_images
from .header_image_finder import get_header_image

logger = logging.getLogger(__name__)


def load_post_data(post_id):
    """
    Load post data from database with development data.
    Returns post dict with all necessary fields.
    """
    try:
        post = get_post_with_development(post_id)
        if not post:
            logger.error(f"Post {post_id} not found")
            return None
        
        logger.info(f"Loaded post {post_id}: {post.get('title', 'No title')}")
        return post
    
    except Exception as e:
        logger.error(f"Error loading post {post_id}: {e}")
        return None


def load_sections(post_id):
    """
    Load sections with images for a post.
    Returns list of section dicts.
    """
    try:
        sections = get_post_sections_with_images(post_id)
        if not sections:
            logger.warning(f"No sections found for post {post_id}")
            return []
        
        logger.info(f"Loaded {len(sections)} sections for post {post_id}")
        return sections
    
    except Exception as e:
        logger.error(f"Error loading sections for post {post_id}: {e}")
        return []


def prepare_post_for_publication(post, header_image):
    """
    Validate and enrich post data for publication.
    Ensures header_image is correctly set in post dict.
    """
    if not post:
        logger.error("Cannot prepare None post for publication")
        return None
    
    # Validate required fields
    required_fields = ['title', 'summary']
    for field in required_fields:
        if not post.get(field):
            logger.error(f"Post {post.get('id')} missing required field: {field}")
            return None
    
    # Set header_image in post dict if provided
    if header_image:
        post['header_image'] = header_image
        logger.info(f"Set header_image for post {post.get('id')}: {header_image.get('path')}")
    else:
        logger.warning(f"No header image found for post {post.get('id')}")
        # Don't fail - some posts might not have header images
    
    return post

