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

            # CRITICAL: Always use post_id from URL - it's the definitive identifier
            # Week parameters are context only, not for changing post_id
            target_post_id = post_id  # Always use URL post_id
            
            # Week context is for display/validation only
            week_has_post = bool(year and week)  # True if week context provided

            # Get post_type (illustration_method is deprecated, always use LLM-creation)
            from utils.taxonomy_helpers import get_post_type
            post_type = get_post_type(target_post_id)
            illustration_method = 'LLM-creation'  # Deprecated, kept for backward compatibility
            # Use original post_type for non-themed posts, otherwise get from resolved post
            non_themed_types = ('recipe', 'profile', 'generated')
            post_type = original_post_type if original_post_type in non_themed_types else get_post_type(target_post_id)

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

        # CRITICAL: Always use post_id from URL - it's the definitive identifier
        # Week parameters are context only, not for changing post_id
        from utils.taxonomy_helpers import get_post_type
        original_post_type = get_post_type(post_id)
        
        target_post_id = post_id  # Always use URL post_id
        
        # Week context validation (for themed posts, but don't change post_id)
        non_themed_types = ('recipe', 'profile', 'generated')
        if original_post_type not in non_themed_types:
            if not year or not week:
                logger.warning(f"Themed post header image route called without week context: year={year}, week={week}")
                # Don't return error - allow page to render, just warn
        
        # Get post_type (illustration_method is deprecated, always use LLM-creation)
        from utils.taxonomy_helpers import get_post_type
        post_type = get_post_type(target_post_id)
        illustration_method = 'LLM-creation'  # Deprecated, kept for backward compatibility
        # Use original post_type for non-themed posts, otherwise get from resolved post
        non_themed_types = ('recipe', 'profile', 'generated')
        post_type = original_post_type if original_post_type in non_themed_types else get_post_type(target_post_id)

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
        
        # Use centralized template mapping
        from utils.template_helpers import resolve_template_for_route
        template_name = resolve_template_for_route('header', 'header-image', target_post_id)
        if not template_name:
            # Fallback to default if mapping not found
            template_name = 'header/header_image.html'
        
        return render_template(
            template_name, 
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

        # CRITICAL: Always use post_id from URL - it's the definitive identifier
        # Week parameters are context only, not for changing post_id
        from utils.taxonomy_helpers import get_post_type
        original_post_type = get_post_type(post_id)
        
        target_post_id = post_id  # Always use URL post_id
        week_has_post = bool(year and week)  # True if week context provided
        
        # Use original post_type for non-themed posts, otherwise get from resolved post
        post_type = original_post_type if original_post_type in non_themed_types else get_post_type(target_post_id)
        
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

    @bp.route('/posts/<int:post_id>/product-match')
    def header_product_match(post_id):
        """Product Match substage - Display and select matching products/categories"""
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)

        # CRITICAL: Always use post_id from URL - it's the definitive identifier
        # Week parameters are context only, not for changing post_id
        from utils.taxonomy_helpers import get_post_type
        original_post_type = get_post_type(post_id)
        
        target_post_id = post_id  # Always use URL post_id
        week_has_post = bool(year and week)  # True if week context provided
        
        # Use original post_type for non-themed posts, otherwise get from resolved post
        post_type = original_post_type if original_post_type in non_themed_types else get_post_type(target_post_id)
        
        # Check if post has embeddings
        has_embeddings = False
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, last_embedded_at
                FROM content_chunks
                WHERE chunk_type = 'post' AND source_id = %s
            """, (target_post_id,))
            embedding_data = cursor.fetchone()
            has_embeddings = embedding_data is not None
        
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
                return render_template('header/product_match.html',
                                      post_id=target_post_id,
                                      year=year,
                                      week=week,
                                      post_type=post_type,
                                      blueprint_name='header',
                                      error='Post not found',
                                      has_embeddings=False)
            
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
            'header/product_match.html', 
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
            has_embeddings=has_embeddings,
            blueprint_name='header'
        )

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

