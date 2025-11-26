"""
Image Page Routes
Flask routes for rendering imaging workflow pages
"""

from flask import Blueprint, render_template, request, redirect, url_for
from config.database import db_manager
from utils.taxonomy_helpers import get_post_type, get_illustration_method_with_post
# CRITICAL: resolve_post_for_week() should NOT be used when post_id is in URL
# post_id in URL is the definitive identifier - week params are context only
from config.authoring_panel_configs import get_panel_config, get_panel_config_by_post_type
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
            
            # CRITICAL: Always use post_id from URL - it's the definitive identifier
            # Week parameters are context only, not for changing post_id
            # This applies to ALL post types (themed, recipe, profile, generated)
            target_post_id = post_id  # Always use URL post_id
            
            # Get post_type for panel configuration (illustration_method is deprecated)
            post_type = get_post_type(target_post_id)
            
            # Get panel configuration for this post type
            panel_config = get_panel_config_by_post_type(post_type)
            
            # Deprecated: illustration_method always 'LLM-creation' for backward compatibility
            illustration_method = 'LLM-creation'
            
            # Photo-harvesting is deprecated - no redirect needed
            
            with db_manager.get_cursor() as cursor:
                # Get post data (including profile_product_id for profile posts)
                cursor.execute("""
                    SELECT p.id, p.title, p.status, p.created_at, p.updated_at, p.profile_product_id
                    FROM post p
                    WHERE p.id = %s
                """, (target_post_id,))
                
                post = cursor.fetchone()
                if not post:
                    return f"Post {target_post_id} not found", 404
                
                # Photo-harvesting is deprecated - always use LLM-creation (image generation)
                
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
                
                # For profile posts, fetch product data with all images
                product_data = None
                product_images = []
                if post_type == 'profile' and post.get('profile_product_id'):
                    product_id = post['profile_product_id']
                    # Get product SKU
                    cursor.execute("""
                        SELECT sku, name, image_url
                        FROM clan_products
                        WHERE id = %s
                    """, (product_id,))
                    product = cursor.fetchone()
                    if product:
                        product_data = {
                            'id': product_id,
                            'sku': product['sku'],
                            'name': product['name'],
                            'image_url': product['image_url']
                        }
                        # Fetch all images via API (will be done in template via JavaScript)
            
            # Use centralized template mapping
            from config.template_mappings import get_template_path
            template_name = get_template_path('imaging', 'image-generation', post_type)
            if not template_name:
                # Fallback to default if mapping not found
                template_name = 'imaging/sections/image_generation.html'
            
            return render_template(template_name, 
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
                                 illustration_method=illustration_method,
                                 product_data=product_data)
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
            
            # CRITICAL: Always use post_id from URL - it's the definitive identifier
            # Week parameters are context only, not for changing post_id
            target_post_id = post_id  # Always use URL post_id
            
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

