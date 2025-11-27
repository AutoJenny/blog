"""Newsletter Preview Routes."""

from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from typing import List, Dict, Any
import os, sys

# Ensure the newsletter package (under blog-core/newsletter) is importable
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-core'))

# Import common dependencies
from newsletter.db.queries_issue import get_issue, list_blocks_by_issue
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('newsletter_preview', __name__)


@bp.route('/newsletter/issue/<int:issue_id>/preview')
def preview_issue(issue_id: int):
    blocks = []
    issue = None
    try:
        blocks = list_blocks_by_issue(issue_id=issue_id)
        issue = get_issue(issue_id=issue_id)
    except Exception:
        blocks = []
    
    # Load base64 tile data for background
    tile_base64_data = None
    try:
        # Get project root (blueprints/ -> project root)
        project_root = os.path.dirname(os.path.dirname(__file__))
        tile_path = os.path.join(project_root, 'static', 'images', 'newsletter', 'tile_base64.txt')
        if os.path.exists(tile_path):
            with open(tile_path, 'r') as f:
                tile_base64_data = f.read().strip()
        else:
            # Try absolute path as fallback
            abs_path = '/Users/autojenny/Documents/projects/blog/static/images/newsletter/tile_base64.txt'
            if os.path.exists(abs_path):
                with open(abs_path, 'r') as f:
                    tile_base64_data = f.read().strip()
        if tile_base64_data:
            import logging
            logging.getLogger(__name__).info(f"Loaded tile background ({len(tile_base64_data)} chars)")
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Could not load tile background: {e}")
        pass  # Tile is optional
    
    # Convert local image paths to clan.com URLs for feature blocks
    # Also convert markdown links to HTML for snapshot blocks
    import re
    processed_blocks = []
    for b in blocks:
        block_data = {"type": b["type"], "payload_json": b["payload_json"].copy() if b["payload_json"] else {}}
        
        # If this is a snapshot block, convert markdown links to HTML
        if b["type"] == "snapshot":
            payload = block_data["payload_json"]
            # Convert [title](url) to HTML links
            def markdown_to_html(text):
                if not text:
                    return ""
                # Convert [title](url) to <a href="url">title</a>
                return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" style="color:#6b4e3d; text-decoration:underline;">\1</a>', text)
            
            if payload.get("news_paragraph"):
                payload["news_paragraph"] = markdown_to_html(payload["news_paragraph"])
            if payload.get("events_paragraph"):
                payload["events_paragraph"] = markdown_to_html(payload["events_paragraph"])
        
        # If this is a last_chance block, ensure product images are valid URLs
        if b["type"] == "last_chance":
            items = block_data["payload_json"].get("items", [])
            for item in items:
                # Images should already be URLs from scraping, but ensure they're valid
                if item.get("image_url"):
                    if not item["image_url"].startswith("http"):
                        # If relative URL, make absolute
                        from urllib.parse import urljoin
                        item["image_url"] = urljoin("https://clan.com", item["image_url"])
        
        # If this is a feature or spotlight block, ensure hero_image is populated from post's header image
        if b["type"] == "feature" or b["type"] == "spotlight":
            post_id = block_data["payload_json"].get("id")
            hero_image = block_data["payload_json"].get("hero_image")
            
            # If hero_image is missing, look it up from the post's header_image_id
            if not hero_image and post_id:
                try:
                    from config.database import db_manager
                    with db_manager.get_cursor() as cursor:
                        # First try images table
                        cursor.execute("""
                            SELECT i.file_path
                            FROM post p
                            JOIN images i ON p.header_image_id = i.id
                            WHERE p.id = %s
                        """, (post_id,))
                        result = cursor.fetchone()
                        if result and result.get('file_path'):
                            hero_image = result['file_path']
                        else:
                            # Fallback to image_archive table via post_images
                            cursor.execute("""
                                SELECT ia.path
                                FROM post p
                                JOIN post_images pi ON pi.post_id = p.id AND pi.image_type LIKE 'header%%'
                                JOIN image_archive ia ON pi.image_id = ia.id
                                WHERE p.id = %s
                                ORDER BY CASE WHEN pi.image_type = 'header_optimized' THEN 1 
                                             WHEN pi.image_type = 'header_watermarked' THEN 2
                                             ELSE 3 END
                                LIMIT 1
                            """, (post_id,))
                            result = cursor.fetchone()
                            if result and result.get('path'):
                                hero_image = result['path']
                        
                        if hero_image:
                            block_data["payload_json"]["hero_image"] = hero_image
                            logger.info(f"Populated feature block hero_image for post {post_id}: {hero_image}")
                except Exception as e:
                    logger.warning(f"Could not lookup hero_image for post {post_id}: {e}")
                    pass
            
            # If hero_image exists and is a local path, try to convert to clan.com URL
            if hero_image and hero_image.startswith("/static/") and post_id:
                try:
                    from config.database import db_manager
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT clan_uploaded_url 
                            FROM section_image_mappings 
                            WHERE post_id = %s 
                              AND section_id IS NULL
                              AND local_image_path = %s
                            LIMIT 1
                        """, (post_id, hero_image))
                        result = cursor.fetchone()
                        if result and result.get('clan_uploaded_url'):
                            block_data["payload_json"]["hero_image"] = result['clan_uploaded_url']
                            logger.info(f"Converted feature block hero_image from {hero_image} to {result['clan_uploaded_url']}")
                except Exception as e:
                    logger.warning(f"Could not convert hero_image path: {e}")
                    pass  # Keep original path if conversion fails
        
        processed_blocks.append(block_data)
    
    # Get words of the week for the issue's target week
    words_of_the_week = {}
    if issue and issue.get('target_week'):
        try:
            from datetime import date
            from newsletter.selectors.words_of_the_week import get_words_of_the_week
            
            # Parse year and week from target_week
            target_week = issue['target_week']
            if 'W' in target_week:
                year_str, week_str = target_week.split('W')
                week_number = int(week_str)
            else:
                week_number = int(target_week)
            
            words_of_the_week = get_words_of_the_week(week_number=week_number)
        except Exception as e:
            logger.warning(f"Error getting words of the week for preview: {e}")
            pass
    
    # Get seasonal recipe post for preview
    seasonal_recipe_post = None
    try:
        from newsletter.selectors.seasonal_recipe import select_seasonal_recipe_post
        seasonal_recipe_post = select_seasonal_recipe_post()
    except Exception as e:
        logger.warning(f"Error getting seasonal recipe post for preview: {e}")
        pass
    
    # Map blocks to pass each payload as "block" expected by partials
    return render_template(
        'newsletter/render.html',
        words_of_the_week=words_of_the_week,
        seasonal_recipe_post=seasonal_recipe_post,
        subject=f"Issue {issue_id}",
        issue=issue,
        blocks=processed_blocks,
        tile_base64_data=tile_base64_data
    )


@bp.route('/newsletter/issue/<int:issue_id>/preview/export')
def export_preview(issue_id: int):
    """Export newsletter preview as standalone HTML file for sharing."""
    from flask import Response, request
    import base64
    
    # Get the same data as preview route
    blocks = []
    issue = None
    try:
        blocks = list_blocks_by_issue(issue_id=issue_id)
        issue = get_issue(issue_id=issue_id)
    except Exception:
        blocks = []
    
    # Load base64 tile data for background
    tile_base64_data = None
    try:
        project_root = os.path.dirname(os.path.dirname(__file__))
        tile_path = os.path.join(project_root, 'static', 'images', 'newsletter', 'tile_base64.txt')
        if os.path.exists(tile_path):
            with open(tile_path, 'r') as f:
                tile_base64_data = f.read().strip()
        else:
            abs_path = '/Users/autojenny/Documents/projects/blog/static/images/newsletter/tile_base64.txt'
            if os.path.exists(abs_path):
                with open(abs_path, 'r') as f:
                    tile_base64_data = f.read().strip()
    except Exception:
        pass
    
    # Process blocks (same as preview route)
    import re
    processed_blocks = []
    for b in blocks:
        block_data = {"type": b["type"], "payload_json": b["payload_json"].copy() if b["payload_json"] else {}}
        
        if b["type"] == "snapshot":
            payload = block_data["payload_json"]
