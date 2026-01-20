"""
Research Blueprint
Handles research stage routes and views.
"""

from flask import Blueprint, render_template, jsonify
import logging
from config.database import db_manager
from utils.taxonomy_helpers import get_post_type
from config.research_topics import get_research_topics_for_post_type, has_research_topics
import json

bp = Blueprint('research', __name__)
logger = logging.getLogger(__name__)


@bp.route('/research/posts/<int:post_id>/background-research')
def background_research(post_id):
    """Background research page for recipe and other post types."""
    try:
        post_type = get_post_type(post_id)
        
        # Check if this post type has research topics
        if not has_research_topics(post_type):
            return f"Background research is not available for post type '{post_type}'", 400
        
        with db_manager.get_cursor() as cursor:
            # Get post data
            if post_type == 'recipe':
                cursor.execute("""
                    SELECT p.id, p.title, p.subtitle, cr.recipe_title, cr.recipe_description, cr.seasonal_context
                    FROM post p
                    LEFT JOIN calendar_recipes cr ON cr.id = p.recipe_id
                    WHERE p.id = %s
                """, (post_id,))
            else:
                cursor.execute("""
                    SELECT id, title, subtitle FROM post WHERE id = %s
                """, (post_id,))
            
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            # Get research data
            cursor.execute("""
                SELECT recipe_research FROM post_development WHERE post_id = %s
            """, (post_id,))
            dev_data = cursor.fetchone()
            
            research_data = None
            if dev_data and dev_data.get('recipe_research'):
                try:
                    research_data = dev_data['recipe_research']
                    if isinstance(research_data, str):
                        research_data = json.loads(research_data)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse recipe_research for post {post_id}")
            
            # Get research topics for this post type
            topics = get_research_topics_for_post_type(post_type)
            
            # Get item name for display
            if post_type == 'recipe':
                item_name = post.get('recipe_title') or post.get('title', '')
                item_description = post.get('recipe_description') or post.get('subtitle', '')
            else:
                item_name = post.get('title', '')
                item_description = post.get('subtitle', '')
            
            return render_template(
                'research/background_research.html',
                post_id=post_id,
                post_type=post_type,
                post=post,
                item_name=item_name,
                item_description=item_description,
                research_data=research_data,
                research_topics=topics
            )
            
    except Exception as e:
        logger.error(f"Error in background_research: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500
