"""Page routes for header blueprint"""
from flask import Blueprint, render_template, request, redirect, url_for
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Register all page routes for the header blueprint"""
    
    @bp.route('/posts/<int:post_id>/title-summary')
    def header_title_summary(post_id):
        """Title & Summary substage - Generate post title, subtitle, slug, and summary
        Week-persistence compliance: resolve target_post_id from ?year&?week and pass post_type.
        Note: illustration_method is deprecated, always uses LLM-creation.
        """
        try:
            # Resolve week context
            year = request.args.get('year', type=int)
            week = request.args.get('week', type=int)

            # Get post type for the original post_id first
            from utils.taxonomy_helpers import get_post_type
            original_post_type = get_post_type(post_id)

            # Resolve post_id from week context (required for generation, but allow page to render)
            # BUT: For recipe/profile posts, preserve the original post_id to maintain recipe/profile association
            from utils.week_post_resolver import resolve_post_for_week
            target_post_id = None
            week_has_post = False
            
            if year and week:
                if original_post_type in ('recipe', 'profile'):
                    # For recipe/profile posts, preserve original post_id - don't resolve to different post
                    target_post_id = post_id
                    week_has_post = True  # Assume has post if we're preserving it
                else:
                    # Only resolve for themed posts
                    resolved = resolve_post_for_week(year, week)
                    if resolved:
                        target_post_id = resolved
                        week_has_post = True
                    else:
                        logger.warning(f"No post scheduled for year={year}, week={week}")
                        target_post_id = post_id
            else:
                # No week context provided - use provided post_id but flag as invalid for generation
                target_post_id = post_id
                logger.warning(f"Title-summary route called without week context: year={year}, week={week}")

            # Get post_type (illustration_method is deprecated, always use LLM-creation)
            from utils.taxonomy_helpers import get_post_type
            post_type = get_post_type(target_post_id)
            illustration_method = 'LLM-creation'  # Deprecated, kept for backward compatibility
            # Use original post_type for recipe/profile, otherwise get from resolved post
            post_type = original_post_type if original_post_type in ('recipe', 'profile') else get_post_type(target_post_id)

            # Get post data with all required fields for header
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                           p.content_type_id
                    FROM post p
                    WHERE p.id = %s
                """, (target_post_id,))
                post = cursor.fetchone()
                
                if not post:
                    return render_template('header/title_summary.html',
                                          post_id=target_post_id,
                                          original_post_id=post_id,
                                          year=year,
                                          week=week,
                                          post_type=post_type,
                                          blueprint_name='header',
                                          error='Post not found')
                
                # Get content_type_name for header
                cursor.execute("""
                    SELECT ti.display_name as content_type_name
                    FROM post p
                    LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                    WHERE p.id = %s
                """, (target_post_id,))
                result = cursor.fetchone()
                content_type_name = result.get('content_type_name') if result else None
            
            return render_template(
                'header/title_summary.html',
                post_id=target_post_id,
                original_post_id=post_id,
                post=post,
                post_type=post_type,
                post_title=post.get('title'),
                post_status=post.get('status'),
                post_created=post.get('created_at'),
                post_updated=post.get('updated_at'),
                content_type_name=content_type_name,
                year=year,
                week=week,
                illustration_method=illustration_method,
                week_has_post=week_has_post,
                blueprint_name='header'
            )
        except Exception as e:
            logger.error(f"Error loading header title-summary: {e}")
            from utils.taxonomy_helpers import get_post_type
            post_type = get_post_type(post_id)
            
            # Try to get post data even in error case
            post = None
            content_type_name = None
            try:
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                               p.content_type_id
                        FROM post p
                        WHERE p.id = %s
                    """, (post_id,))
                    post = cursor.fetchone()
                    
                    if post:
                        cursor.execute("""
                            SELECT ti.display_name as content_type_name
                            FROM post p
                            LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                            WHERE p.id = %s
                        """, (post_id,))
                        result = cursor.fetchone()
                        content_type_name = result.get('content_type_name') if result else None
            except:
                pass
            
            return render_template('header/title_summary.html',
                                  post_id=post_id,
                                  post=post,
                                  post_type=post_type,
                                  post_title=post.get('title') if post else None,
                                  post_status=post.get('status') if post else None,
                                  post_created=post.get('created_at') if post else None,
                                  post_updated=post.get('updated_at') if post else None,
                                  content_type_name=content_type_name,
                                  blueprint_name='header',
                                  error=str(e))

    @bp.route('/posts/<int:post_id>/header-image')
    def header_header_image(post_id):
        """Header Image substage - Create header image with caption and alt text"""
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)

        from utils.week_post_resolver import resolve_post_for_week
        # Get post type for the original post_id first
        from utils.taxonomy_helpers import get_post_type
        original_post_type = get_post_type(post_id)
        
        # NO FALLBACKS: Only use resolved post_id from week context
        # BUT: For recipe/profile posts, preserve the original post_id
        if not year or not week:
            logger.error(f"Header image route called without week context: year={year}, week={week}")
            return "Week context (year and week) is required.", 400
        
        if original_post_type in ('recipe', 'profile'):
            # For recipe/profile posts, preserve original post_id
            target_post_id = post_id
        else:
            # Only resolve for themed posts
            target_post_id = resolve_post_for_week(year, week)
            if not target_post_id:
                logger.error(f"No post scheduled for year={year}, week={week}")
                return f"No post scheduled for week {week}, {year}. Please schedule a post for this week first.", 404
        
        # Get post_type (illustration_method is deprecated, always use LLM-creation)
        from utils.taxonomy_helpers import get_post_type
        post_type = get_post_type(target_post_id)
        illustration_method = 'LLM-creation'  # Deprecated, kept for backward compatibility
        # Use original post_type for recipe/profile, otherwise get from resolved post
        post_type = original_post_type if original_post_type in ('recipe', 'profile') else get_post_type(target_post_id)

        # Get post data with all required fields for header
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                       p.content_type_id
                FROM post p
                WHERE p.id = %s
            """, (target_post_id,))
            post = cursor.fetchone()
            
            if not post:
                return render_template('header/header_image.html',
                                      post_id=target_post_id,
                                      year=year,
                                      week=week,
                                      post_type=post_type,
                                      blueprint_name='header',
                                      error='Post not found')
            
            # Get content_type_name for header
            cursor.execute("""
                SELECT ti.display_name as content_type_name
                FROM post p
                LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                WHERE p.id = %s
            """, (target_post_id,))
            result = cursor.fetchone()
            content_type_name = result.get('content_type_name') if result else None
        
        return render_template(
            'header/header_image.html', 
            post_id=target_post_id,
            post=post,
            post_type=post_type,
            post_title=post.get('title'),
            post_status=post.get('status'),
            post_created=post.get('created_at'),
            post_updated=post.get('updated_at'),
            content_type_name=content_type_name,
            year=year,
            week=week,
            illustration_method=illustration_method,
            blueprint_name='header'
        )

    @bp.route('/posts/<int:post_id>/seo-meta')
    def header_seo_meta(post_id):
        """SEO & Meta substage - Generate SEO metadata including meta title, description, and tags"""
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)

        from utils.week_post_resolver import resolve_post_for_week
        
        # Get post type for the original post_id first
        from utils.taxonomy_helpers import get_post_type
        original_post_type = get_post_type(post_id)
        
        # Resolve post_id from week context (required for generation, but allow page to render)
        # BUT: For recipe/profile posts, preserve the original post_id
        target_post_id = None
        week_has_post = False
        
        if year and week:
            if original_post_type in ('recipe', 'profile'):
                # For recipe/profile posts, preserve original post_id
                target_post_id = post_id
                week_has_post = True
            else:
                # Only resolve for themed posts
                resolved = resolve_post_for_week(year, week)
                if resolved:
                    target_post_id = resolved
                    week_has_post = True
                else:
                    logger.warning(f"No post scheduled for year={year}, week={week}")
                    target_post_id = post_id
        else:
            # No week context provided - use provided post_id but flag as invalid for generation
            target_post_id = post_id
            logger.warning(f"SEO meta route called without week context: year={year}, week={week}")
        
        # Use original post_type for recipe/profile, otherwise get from resolved post
        post_type = original_post_type if original_post_type in ('recipe', 'profile') else get_post_type(target_post_id)
        
        # Get post data with all required fields for header
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                       p.content_type_id
                FROM post p
                WHERE p.id = %s
            """, (target_post_id,))
            post = cursor.fetchone()
            
            if not post:
                return render_template('header/seo_meta.html',
                                      post_id=target_post_id,
                                      year=year,
                                      week=week,
                                      post_type=post_type,
                                      blueprint_name='header',
                                      error='Post not found')
            
            # Get content_type_name for header
            cursor.execute("""
                SELECT ti.display_name as content_type_name
                FROM post p
                LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                WHERE p.id = %s
            """, (target_post_id,))
            result = cursor.fetchone()
            content_type_name = result.get('content_type_name') if result else None
        
        return render_template(
            'header/seo_meta.html', 
            post_id=target_post_id,
            post=post,
            post_type=post_type,
            post_title=post.get('title'),
            post_status=post.get('status'),
            post_created=post.get('created_at'),
            post_updated=post.get('updated_at'),
            content_type_name=content_type_name,
            year=year,
            week=week,
            week_has_post=week_has_post,
            blueprint_name='header'
        )

    @bp.route('/posts/<int:post_id>/publishing-details')
    def header_publishing_details(post_id):
        """Deprecated route: Publishing Details substage removed. Redirect to SEO & Meta."""
        return redirect(url_for('header.header_seo_meta', post_id=post_id))

    @bp.route('/posts/<int:post_id>/final-review')
    def header_final_review(post_id):
        """Final review - redirects to unified preview route"""
        # Redirect to unified preview route in launchpad app
        return redirect(f'/preview/{post_id}')

    @bp.route('/posts/<int:post_id>/preview')
    def header_preview(post_id):
        """DEPRECATED: Redirects to unified preview route. This route has been removed."""
        # Redirect to unified preview route in launchpad app
        logger.info(f"Redirecting deprecated header preview route to unified /preview/{post_id}")
        return redirect(f'/preview/{post_id}')

