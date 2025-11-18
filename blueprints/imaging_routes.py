"""
Image Page Routes
Flask routes for rendering imaging workflow pages
"""

from flask import Blueprint, render_template, request, redirect, url_for
from config.database import db_manager
from utils.taxonomy_helpers import get_post_type, get_illustration_method_with_post
from utils.week_post_resolver import resolve_post_for_week
from config.authoring_panel_configs import get_panel_config
import logging

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Register page routes with the blueprint"""
    
    @bp.route('/posts/<int:post_id>/sections/image-generation')
    def imaging_sections_image_generation(post_id):
        """Image Generation page - standalone imaging workflow"""
        try:
            # CRITICAL: Check for week context in URL params to determine correct post
            url_year = request.args.get('year', type=int)
            url_week = request.args.get('week', type=int)
            
            # Check if this is a recipe post first - recipe posts should use URL post_id directly
            url_post_type = get_post_type(post_id)
            
            # SINGLE SOURCE OF TRUTH: Use approved utility for week/post resolution
            # BUT: For recipe posts, always use the URL post_id (recipes have their own scheduling)
            target_post_id = post_id
            if url_post_type != 'recipe' and url_year and url_week:
                resolved_post_id = resolve_post_for_week(url_year, url_week)
                if resolved_post_id:
                    target_post_id = resolved_post_id
                    logger.info(f"Week {url_year}/{url_week} resolved to post_id {target_post_id} (instead of URL post_id {post_id})")
                else:
                    logger.warning(f"Week {url_year}/{url_week} has no scheduled post - using URL post_id {post_id}")
            elif url_post_type == 'recipe':
                logger.info(f"Recipe post {post_id} - using URL post_id directly (not resolving via week)")
            
            # Recipe posts should ALWAYS use LLM-creation (image generation), not Photo-harvesting
            if url_post_type == 'recipe':
                illustration_method = 'LLM-creation'
            else:
                # Use utility function to get illustration_method for non-recipe posts
                resolved_for_method, illustration_method = get_illustration_method_with_post(
                    post_id, url_year, url_week
                )
                # Use the resolved post_id from illustration method resolution if it's different (but not for recipes)
                if resolved_for_method != target_post_id:
                    target_post_id = resolved_for_method
            
            # Check if route is active (Photo-harvesting is inactive but kept in reserve)
            panel_config = get_panel_config(illustration_method)
            if not panel_config.get('active', True):
                # Route is inactive, redirect to LLM-creation route
                illustration_method = 'LLM-creation'
                panel_config = get_panel_config('LLM-creation')
            
            with db_manager.get_cursor() as cursor:
                # Get post data
                cursor.execute("""
                    SELECT p.id, p.title, p.status, p.created_at, p.updated_at
                    FROM post p
                    WHERE p.id = %s
                """, (target_post_id,))
                
                post = cursor.fetchone()
                if not post:
                    return f"Post {target_post_id} not found", 404
                
                # Recipe posts should NEVER use Photo-harvesting - skip this check for recipes
                if url_post_type != 'recipe':
                    # Check if Photo-harvesting route is active before redirecting (only for non-recipe posts)
                    photo_harvesting_config = get_panel_config('Photo-harvesting')
                    if illustration_method == 'Photo-harvesting' and photo_harvesting_config.get('active', True):
                        redirect_url = url_for('imaging.imaging_sections_photo_selection', post_id=post_id)
                        if url_year and url_week:
                            redirect_url += f'?year={url_year}&week={url_week}'
                        return redirect(redirect_url)
                # If Photo-harvesting is inactive or this is a recipe post, continue with LLM-creation route
                
                # Format dates for display
                post_created = post['created_at'].strftime('%Y-%m-%d %H:%M') if post['created_at'] else 'Unknown'
                post_updated = post['updated_at'].strftime('%Y-%m-%d %H:%M') if post['updated_at'] else 'Unknown'
                
                # Get post type for recipe-specific handling
                post_type = get_post_type(target_post_id)
                
                # Get content_type_name for header
                cursor.execute("""
                    SELECT ti.display_name as content_type_name
                    FROM post p
                    LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                    WHERE p.id = %s
                """, (target_post_id,))
                result = cursor.fetchone()
                content_type_name = result.get('content_type_name') if result else None
            
            return render_template('imaging/sections/image_generation.html', 
                                 post_id=post_id,
                                 post=post,
                                 page_title='Image Generation',
                                 post_type=post_type,
                                 post_title=post.get('title'),
                                 post_status=post.get('status'),
                                 post_created=post_created,
                                 post_updated=post_updated,
                                 content_type_name=content_type_name,
                                 currentStage='imaging',
                                 currentSubstage='image-generation',
                                 illustration_method=illustration_method)
        except Exception as e:
            logger.error(f"Error rendering image generation page: {str(e)}")
            return f"Error: {str(e)}", 500

    @bp.route('/posts/<int:post_id>/sections/optimise')
    def imaging_sections_optimise(post_id):
        """Optimise page - imaging workflow substage"""
        try:
            # CRITICAL: Check for week context in URL params to determine correct post
            url_year = request.args.get('year', type=int)
            url_week = request.args.get('week', type=int)
            
            # SINGLE SOURCE OF TRUTH: Use approved utility for week/post resolution
            target_post_id = post_id
            if url_year and url_week:
                resolved_post_id = resolve_post_for_week(url_year, url_week)
                if resolved_post_id:
                    target_post_id = resolved_post_id
                    logger.info(f"Week {url_year}/{url_week} resolved to post_id {target_post_id} (instead of URL post_id {post_id})")
                else:
                    logger.warning(f"Week {url_year}/{url_week} has no scheduled post - using URL post_id {post_id}")
            
            # Use utility function to get illustration_method
            target_post_id, illustration_method = get_illustration_method_with_post(
                post_id, url_year, url_week
            )
            
            # Check if route is active
            panel_config = get_panel_config(illustration_method)
            if not panel_config.get('active', True):
                illustration_method = 'LLM-creation'
            
            with db_manager.get_cursor() as cursor:
                # Get post data and post type
                post_type = get_post_type(target_post_id)
                
                cursor.execute("""
                    SELECT p.id, p.title, p.status, p.created_at, p.updated_at
                    FROM post p
                    WHERE p.id = %s
                """, (target_post_id,))
                post = cursor.fetchone()
                if not post:
                    return f"Post {target_post_id} not found", 404

                post_created = post['created_at'].strftime('%Y-%m-%d %H:%M') if post['created_at'] else 'Unknown'
                post_updated = post['updated_at'].strftime('%Y-%m-%d %H:%M') if post['updated_at'] else 'Unknown'
                
                # Get content_type_name for header
                cursor.execute("""
                    SELECT ti.display_name as content_type_name
                    FROM post p
                    LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                    WHERE p.id = %s
                """, (target_post_id,))
                result = cursor.fetchone()
                content_type_name = result.get('content_type_name') if result else None

            return render_template('imaging/sections/optimise.html',
                                   post_id=post_id,
                                   post=post,
                                   page_title='Optimise',
                                   post_type=post_type,
                                   post_title=post.get('title'),
                                   post_status=post.get('status'),
                                   post_created=post_created,
                                   post_updated=post_updated,
                                   content_type_name=content_type_name,
                                   currentStage='imaging',
                                   currentSubstage='optimise',
                                   illustration_method=illustration_method)
        except Exception as e:
            logger.error(f"Error rendering optimise page: {str(e)}")
            return f"Error: {str(e)}", 500

    @bp.route('/posts/<int:post_id>/sections/photo-selection')
    def imaging_sections_photo_selection(post_id):
        """Photo Selection page - for Photo-harvesting illustration method (DEPRECATED)"""
        # Photo-harvesting is deprecated - redirect to image generation
        logger.warning(f"Photo-harvesting route accessed for post {post_id} - redirecting to image generation")
        url_year = request.args.get('year', type=int)
        url_week = request.args.get('week', type=int)
        redirect_url = url_for('imaging.imaging_sections_image_generation', post_id=post_id)
        if url_year and url_week:
            redirect_url += f'?year={url_year}&week={url_week}'
        return redirect(redirect_url)

