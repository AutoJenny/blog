"""
Publish Orchestrator
Orchestrates the publication flow using ClanPublisher methods.
"""

import logging
import sys
import os

# Add parent directory to path to import from clan_publisher.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from clan_publisher import ClanPublisher
from config.database import db_manager
from .post_data_loader import load_post_data, load_sections, prepare_post_for_publication
from .header_image_finder import get_header_image

logger = logging.getLogger(__name__)


def publish_post_to_clan(post_id):
    """
    Main orchestration function for publishing a post to clan.com.
    Returns dict with success status and result/error message.
    """
    try:
        logger.info(f"=== Starting publication for post {post_id} ===")
        
        # Step 1: Load post data and sections
        logger.info("Step 1: Loading post data...")
        post = load_post_data(post_id)
        if not post:
            return {
                'success': False,
                'error': f'Post {post_id} not found or could not be loaded'
            }
        
        logger.info("Step 2: Loading sections...")
        sections = load_sections(post_id)
        
        # Step 2: Find header image (single source of truth)
        logger.info("Step 3: Finding header image...")
        header_image = get_header_image(post_id)
        if header_image:
            logger.info(f"✅ Found header image: {header_image.get('path')}")
        else:
            logger.warning(f"⚠️ No header image found for post {post_id}")
        
        # Step 3: Prepare post data (validate, enrich with header_image)
        logger.info("Step 4: Preparing post for publication...")
        post = prepare_post_for_publication(post, header_image)
        if not post:
            return {
                'success': False,
                'error': f'Post {post_id} failed validation'
            }
        
        logger.info(f"✅ Post prepared. header_image: {post.get('header_image')}")
        if post.get('header_image'):
            logger.info(f"   header_image path: {post['header_image'].get('path')}")
        
        # Step 4: Initialize ClanPublisher and process images
        logger.info("Step 5: Processing images...")
        publisher = ClanPublisher()
        
        # CRITICAL: Pass header_image in post dict - do NOT let ClanPublisher re-find it
        # The header_image is already set in post dict by prepare_post_for_publication
        logger.info(f"Before process_images: post['header_image'] = {post.get('header_image')}")
        uploaded_images = publisher.process_images(post, sections)
        logger.info(f"After process_images: post['header_image'] = {post.get('header_image')}")
        logger.info(f"uploaded_images keys: {list(uploaded_images.keys())}")
        logger.info(f"✅ Processed {len(uploaded_images)} images")
        
        # Step 5: Generate HTML content
        logger.info("Step 6: Generating HTML content...")
        html_content = publisher.get_preview_html_content(post, sections, uploaded_images)
        logger.info(f"✅ Generated HTML content ({len(html_content)} chars)")
        
        # Step 6: Determine if this is an update or new post
        is_update = bool(post.get('clan_post_id'))
        logger.info(f"Step 7: Publishing to clan.com (is_update: {is_update})...")
        
        # Step 7: Create or update post on clan.com
        logger.info(f"Before create_or_update_post: post['header_image'] = {post.get('header_image')}")
        result = publisher.create_or_update_post(post, html_content, is_update, uploaded_images)
        
        if result.get('success'):
            # Step 8: Update database with results
            logger.info("Step 8: Updating database...")
            with db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE post 
                        SET clan_post_id = %s, 
                            clan_uploaded_url = %s,
                            status = 'published'
                        WHERE id = %s
                    """, (
                        result.get('clan_post_id'),
                        result.get('clan_url'),
                        post_id
                    ))
                    conn.commit()
            
            logger.info(f"✅ Successfully published post {post_id} to clan.com")
            return {
                'success': True,
                'clan_post_id': result.get('clan_post_id'),
                'clan_url': result.get('clan_url'),
                'message': f'Post {post_id} published successfully'
            }
        else:
            logger.error(f"❌ Failed to publish post {post_id}: {result.get('error')}")
            return {
                'success': False,
                'error': result.get('error', 'Unknown error during publication')
            }
    
    except Exception as e:
        logger.error(f"❌ Exception during publication of post {post_id}: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Exception: {str(e)}'
        }

