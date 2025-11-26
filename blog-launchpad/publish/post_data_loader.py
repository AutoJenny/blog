"""
Post Data Loader
Loads and prepares post data for publication.
"""

import logging
import os
import re
import psycopg
import psycopg.rows

logger = logging.getLogger(__name__)


def get_db_connection():
    """Get database connection."""
    return psycopg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        dbname=os.getenv('DB_NAME', 'blog'),
        user=os.getenv('DB_USER', 'autojenny'),
        password=os.getenv('DB_PASSWORD', '')
    )


def sync_product_match_to_cross_promotion(post_id):
    """
    Sync product and category IDs from embedding_overrides to post table.
    
    Reads selected_product_id and selected_category_id from post_development.embedding_overrides
    and updates post.cross_promotion_product_id and post.cross_promotion_category_id if they are NULL.
    
    Does not overwrite existing manual cross-promotion selections.
    
    Args:
        post_id: Post ID to sync
        
    Returns:
        bool: True if sync occurred, False otherwise
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # Get embedding_overrides from post_development
            cur.execute("""
                SELECT embedding_overrides
                FROM post_development
                WHERE post_id = %s
            """, (post_id,))
            
            dev_result = cur.fetchone()
            if not dev_result or not dev_result.get('embedding_overrides'):
                logger.debug(f"No embedding_overrides found for post {post_id}")
                return False
            
            # Parse JSON
            import json
            overrides = dev_result['embedding_overrides']
            if isinstance(overrides, str):
                try:
                    overrides = json.loads(overrides)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in embedding_overrides for post {post_id}")
                    return False
            
            if not isinstance(overrides, dict):
                logger.warning(f"embedding_overrides is not a dict for post {post_id}")
                return False
            
            # Extract selected IDs (support both new format and legacy)
            selected_product_id = overrides.get('selected_product_id') or (
                overrides.get('selected_type') == 'product' and overrides.get('selected_id')
            )
            selected_category_id = overrides.get('selected_category_id') or (
                overrides.get('selected_type') == 'category' and overrides.get('selected_id')
            )
            
            if not selected_product_id and not selected_category_id:
                logger.debug(f"No product or category IDs in embedding_overrides for post {post_id}")
                return False
            
            # Check current values in post table (including positions)
            cur.execute("""
                SELECT cross_promotion_product_id, cross_promotion_category_id,
                       cross_promotion_product_position, cross_promotion_category_position
                FROM post
                WHERE id = %s
            """, (post_id,))
            
            post_result = cur.fetchone()
            if not post_result:
                logger.warning(f"Post {post_id} not found")
                return False
            
            # Only update if current values are NULL (don't overwrite manual selections)
            updates = []
            params = []
            
            if selected_product_id and post_result.get('cross_promotion_product_id') is None:
                updates.append("cross_promotion_product_id = %s")
                params.append(selected_product_id)
                logger.info(f"Syncing product_id {selected_product_id} to post {post_id}")
            
            if selected_category_id and post_result.get('cross_promotion_category_id') is None:
                updates.append("cross_promotion_category_id = %s")
                params.append(selected_category_id)
                logger.info(f"Syncing category_id {selected_category_id} to post {post_id}")
            
            # Get section count once to determine default positions
            cur.execute("SELECT COUNT(*) as section_count FROM post_section WHERE post_id = %s", (post_id,))
            section_count_result = cur.fetchone()
            section_count = section_count_result.get('section_count', 0) if section_count_result else 0
            # Default positions: category after section 2, product after section 4, or after last section if fewer sections
            default_category_position = min(2, section_count) + 1 if section_count > 0 else 1
            default_product_position = min(4, section_count) + 1 if section_count > 0 else 1
            
            # Set default positions if:
            # 1. IDs are being synced and positions are NULL, OR
            # 2. IDs already exist but positions are NULL (fix existing records)
            if (selected_category_id and post_result.get('cross_promotion_category_id') is None and post_result.get('cross_promotion_category_position') is None) or \
               (post_result.get('cross_promotion_category_id') is not None and post_result.get('cross_promotion_category_position') is None):
                updates.append("cross_promotion_category_position = %s")
                params.append(default_category_position)
                logger.info(f"Setting default category_position {default_category_position} for post {post_id}")
            
            if (selected_product_id and post_result.get('cross_promotion_product_id') is None and post_result.get('cross_promotion_product_position') is None) or \
               (post_result.get('cross_promotion_product_id') is not None and post_result.get('cross_promotion_product_position') is None):
                updates.append("cross_promotion_product_position = %s")
                params.append(default_product_position)
                logger.info(f"Setting default product_position {default_product_position} for post {post_id}")
            
            if not updates:
                logger.debug(f"Post {post_id} already has cross-promotion IDs, skipping sync")
                return False
            
            # Update post table
            params.append(post_id)
            update_sql = f"""
                UPDATE post
                SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            
            cur.execute(update_sql, params)
            conn.commit()
            
            logger.info(f"Successfully synced product-match IDs to cross-promotion for post {post_id}")
            return True
            
    except Exception as e:
        logger.error(f"Error syncing product-match to cross-promotion for post {post_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def get_post_with_development(post_id):
    """Fetch post with development data."""
    with get_db_connection() as conn:
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        # Get post data, alias post.id as post_id
        # Include year and week_number for recipe posts to enable proper edit links
        # Note: year comes from calendar_schedule, week_number comes from calendar_recipes (perpetual)
        cur.execute("""
            SELECT p.id AS post_id, p.title, p.subtitle, p.created_at, p.updated_at, p.status, p.slug, p.summary, p.title_choices,
                   p.clan_post_id, p.clan_uploaded_url, p.author_id,
                   a.name as author_name,
                   pd.idea_seed, pd.intro_blurb, pd.main_title,
                   p.cross_promotion_category_id, p.cross_promotion_category_title,
                   p.cross_promotion_product_id, p.cross_promotion_product_title,
                   p.cross_promotion_category_position, p.cross_promotion_product_position,
                   p.cross_promotion_category_widget_html, p.cross_promotion_product_widget_html,
                   p.profile_product_id, p.profile_category_id,
                   cs.year, cr.week_number
            FROM post p
            LEFT JOIN author a ON p.author_id = a.id
            LEFT JOIN post_development pd ON pd.post_id = p.id
            LEFT JOIN calendar_recipes cr ON cr.id = p.recipe_id
            LEFT JOIN calendar_schedule cs ON cs.post_id = p.id
            WHERE p.id = %s
        """, (post_id,))
        
        post = cur.fetchone()
        if not post:
            return None
            
        # Get header image - use post_images -> image_archive table (foreign key points here)
        cur.execute("""
            SELECT ia.path as path, ia.filename, ia.alt_text, ia.caption, pi.image_type
            FROM post_images pi
            JOIN image_archive ia ON pi.image_id = ia.id
            WHERE pi.post_id = %s AND pi.image_type LIKE 'header%%'
            ORDER BY CASE WHEN pi.image_type = 'header_optimized' THEN 1 
                          WHEN pi.image_type = 'header_watermarked' THEN 2
                          ELSE 3 END
            LIMIT 1
        """, (post_id,))
        img_row = cur.fetchone()
        if img_row and img_row.get('path'):
            header_path = img_row['path']
            # CRITICAL: Normalize path to ALWAYS be /static/content/posts/... format
            # Remove any leading slashes, then ensure it starts with /static/
            header_path = header_path.lstrip('/')
            if not header_path.startswith('static/'):
                header_path = 'static/' + header_path.lstrip('/')
            header_path = '/' + header_path  # Add leading slash
            post['header_image'] = {
                'path': header_path,
                'alt_text': img_row.get('alt_text'),
                'title': img_row.get('filename'),
                'caption': img_row.get('caption'),
                'width': None,
                'height': None
            }
        
        post_dict = dict(post)
        # Always use post_id for the edit link
        post_dict['id'] = post_dict['post_id']
        
        # Sync product-match selections to cross-promotion fields before building cross_promotion dict
        # This ensures preview shows the matched IDs
        sync_product_match_to_cross_promotion(post_id)
        
        # Reload post data to get synced values
        cur.execute("""
            SELECT cross_promotion_category_id, cross_promotion_category_title,
                   cross_promotion_product_id, cross_promotion_product_title,
                   cross_promotion_category_position, cross_promotion_product_position,
                   cross_promotion_category_widget_html, cross_promotion_product_widget_html
            FROM post WHERE id = %s
        """, (post_id,))
        updated_post = cur.fetchone()
        if updated_post:
            # Update post_dict with synced values
            post_dict['cross_promotion_category_id'] = updated_post.get('cross_promotion_category_id')
            post_dict['cross_promotion_product_id'] = updated_post.get('cross_promotion_product_id')
        
        # Add cross-promotion data structure
        post_dict['cross_promotion'] = {
            'category_id': post_dict.get('cross_promotion_category_id'),
            'category_title': post_dict.get('cross_promotion_category_title'),
            'product_id': post_dict.get('cross_promotion_product_id'),
            'product_title': post_dict.get('cross_promotion_product_title'),
            'category_position': post_dict.get('cross_promotion_category_position'),
            'product_position': post_dict.get('cross_promotion_product_position'),
            'category_widget_html': post_dict.get('cross_promotion_category_widget_html'),
            'product_widget_html': post_dict.get('cross_promotion_product_widget_html')
        }
        
        return post_dict


def get_post_sections_with_images(post_id):
    """Fetch sections with complete image metadata."""
    with get_db_connection() as conn:
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        # Get all sections for the post, including recipe section data
        # Exclude recipe_image_style section (internal use only, not for publishing)
        cur.execute("""
            SELECT 
                id, post_id, section_order, 
                section_heading,
                section_description, ideas_to_include, facts_to_include,
                draft, polished, highlighting, image_concepts,
                image_prompts,
                image_captions, status,
                image_title, image_width, image_height,
                section_type, post_section_elements
            FROM post_section 
            WHERE post_id = %s 
            AND (section_type IS NULL OR section_type != 'recipe_image_style')
            ORDER BY section_order
        """, (post_id,))
        
        raw_sections = cur.fetchall()
        sections = []
        
        for section in raw_sections:
            section_dict = dict(section)
            
            # IMPORTANT: Use polished field directly - no transformations here!
            # Recipe sections should have HTML already rendered and saved to polished during content generation
            # Only safety check: filter out raw JSON if somehow it got into polished/draft
            polished = section.get('polished') or section.get('draft') or ''
            if polished:
                polished_stripped = polished.strip()
                if polished_stripped.startswith('{') or polished_stripped.startswith('[') or '```json' in polished_stripped.lower():
                    logger.warning(f"Section {section['id']} contains raw JSON in polished/draft - this should not happen!")
                    section_dict['polished'] = '<p><em>No content available for this section.</em></p>'
                else:
                    # ALWAYS strip H2 headings from content to prevent duplicates
                    # The template adds H2 from section_heading, so content should not have its own H2
                    original_polished = polished
                    polished = re.sub(r'<h2[^>]*>.*?</h2>', '', polished, flags=re.IGNORECASE | re.DOTALL)
                    
                    # Also strip paragraphs that exactly match the section heading (common duplicate issue)
                    section_heading = section.get('section_heading', '').strip()
                    if section_heading:
                        # Remove quotes from heading for comparison
                        heading_clean = section_heading.replace('"', '').replace("'", '').strip()
                        # Escape special regex characters in heading
                        heading_escaped = re.escape(heading_clean)
                        # Match paragraph containing just the heading (with optional whitespace)
                        paragraph_pattern = rf'<p[^>]*>\s*{heading_escaped}\s*</p>'
                        polished = re.sub(paragraph_pattern, '', polished, flags=re.IGNORECASE | re.DOTALL)
                    
                    if original_polished != polished:
                        logger.info(f"✅ Stripped H2/duplicate heading from section {section['id']} ({section.get('section_heading', 'no heading')}) - removed {len(original_polished) - len(polished)} chars")
                    section_dict['polished'] = polished
            else:
                section_dict['polished'] = '<p><em>No content available for this section.</em></p>'
            
            # Clear draft to ensure we only use polished
            section_dict['draft'] = None
            
            # Ensure section_type is in the dict for template filtering
            if 'section_type' not in section_dict:
                section_dict['section_type'] = section.get('section_type')
            
            # ONLY use optimized images - no fallbacks to raw
            image_path = None
            caption_text = section.get('image_captions') or ''
            alt_text = f"Image for {section.get('section_heading', 'section')}"
            
            import os
            # Priority 1: Check post_images table (optimized images)
            # Foreign key points to image_archive table
            cur.execute("""
                SELECT ia.path, ia.filename, ia.alt_text, ia.caption
                FROM post_images pi
                JOIN image_archive ia ON pi.image_id = ia.id
                WHERE pi.section_id = %s AND pi.image_type = 'section_optimized'
                LIMIT 1
            """, (section['id'],))
            db_image = cur.fetchone()
            if db_image and db_image.get('path'):
                image_path = db_image['path']
                if db_image.get('caption'):
                    caption_text = db_image['caption']
                if db_image.get('alt_text'):
                    alt_text = db_image['alt_text']
                logger.info(f"Using optimized image from database for section {section['id']}: {image_path}")
            
            
            if image_path:
                # Found image in post_images table
                section_dict['image'] = {
                    'path': image_path,
                    'alt_text': alt_text,
                    'title': section.get('image_title'),
                    'width': section.get('image_width'),
                    'height': section.get('image_height')
                }
                # Also set the caption directly on the section for template compatibility
                section_dict['image_captions'] = caption_text
            else:
                # No image in post_images table - NO FALLBACKS
                section_dict['image'] = {
                    'path': None,
                    'alt_text': f"No image available for {section.get('section_heading', 'this section')}",
                    'placeholder': True
                }
            
            sections.append(section_dict)
        
        # Special handling for Profile posts: Auto-assign product image to Section 1
        # This treats the product image as if it were generated for Section 1 (like Theme posts)
        if sections:
            try:
                # Get post type
                import sys
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                sys.path.insert(0, project_root)
                from utils.taxonomy_helpers import get_post_type
                
                # Get post data to determine post_type and profile_product_id
                # Use a simple query to get just the fields needed for post_type determination
                cur.execute("""
                    SELECT profile_product_id, profile_category_id, recipe_id, generated_source_type
                    FROM post
                    WHERE id = %s
                """, (post_id,))
                post_type_data = cur.fetchone()
                
                if post_type_data:
                    # Determine post_type from the simple data
                    if post_type_data.get('recipe_id'):
                        post_type = 'recipe'
                    elif post_type_data.get('profile_category_id'):
                        post_type = 'profile'
                    elif post_type_data.get('generated_source_type'):
                        post_type = 'generated'
                    else:
                        post_type = 'themed'
                    
                    # Get full post data for profile_product_id
                    post_data = get_post_with_development(post_id)
                    logger.info(f"[PROFILE_IMAGE] Post {post_id} type: {post_type}")
                    
                    if post_type == 'profile':
                        # Find Section 1 (section_order = 1)
                        section_1 = None
                        for section in sections:
                            if section.get('section_order') == 1:
                                section_1 = section
                                break
                        
                        if section_1:
                            logger.info(f"[PROFILE_IMAGE] Found Section 1: id={section_1.get('id')}, heading={section_1.get('section_heading')}")
                            section_1_image = section_1.get('image')
                            logger.info(f"[PROFILE_IMAGE] Section 1 image: {section_1_image}")
                            
                            # Check if image exists and has a valid path (not placeholder)
                            has_valid_image = (section_1_image and 
                                             section_1_image.get('path') and 
                                             section_1_image.get('path') != None and
                                             not section_1_image.get('placeholder', False))
                            
                            logger.info(f"[PROFILE_IMAGE] Section 1 has_valid_image: {has_valid_image}")
                            
                            if not has_valid_image:
                                profile_product_id = post_data.get('profile_product_id')
                            if profile_product_id:
                                # Fetch product image URL from clan_products
                                cur.execute("""
                                    SELECT image_url, name
                                    FROM clan_products
                                    WHERE id = %s
                                """, (profile_product_id,))
                                product = cur.fetchone()
                                
                                if product and product.get('image_url'):
                                    product_image_url = product['image_url']
                                    product_name = product.get('name', 'Product')
                                    
                                    # Check which table to use (image_archive or images)
                                    # Check if image_archive table exists
                                    cur.execute("""
                                        SELECT column_name FROM information_schema.columns 
                                        WHERE table_name = 'image_archive' AND column_name = 'path'
                                    """)
                                    use_image_archive = cur.fetchone() is not None
                                    
                                    # Create image record
                                    if use_image_archive:
                                        cur.execute("""
                                            INSERT INTO image_archive (filename, path, alt_text, caption)
                                            VALUES (%s, %s, %s, %s)
                                            RETURNING id
                                        """, (
                                            'product_main.jpg',
                                            product_image_url,
                                            f"Main image of {product_name}",
                                            f"Main product image for {product_name}"
                                        ))
                                    else:
                                        cur.execute("""
                                            INSERT INTO images (filename, file_path, alt_text, caption)
                                            VALUES (%s, %s, %s, %s)
                                            RETURNING id
                                        """, (
                                            'product_main.jpg',
                                            product_image_url,
                                            f"Main image of {product_name}",
                                            f"Main product image for {product_name}"
                                        ))
                                    
                                    image_record = cur.fetchone()
                                    if image_record:
                                        image_id = image_record['id']
                                        
                                        # Create post_images link for Section 1
                                        # Use ON CONFLICT to avoid duplicates if already exists
                                        cur.execute("""
                                            INSERT INTO post_images (post_id, section_id, image_id, image_type)
                                            VALUES (%s, %s, %s, 'section_optimized')
                                            ON CONFLICT (post_id, image_type, section_id) DO UPDATE
                                            SET image_id = EXCLUDED.image_id
                                        """, (post_id, section_1['id'], image_id))
                                        
                                        # Add image to section_1 dict
                                        section_1['image'] = {
                                            'path': product_image_url,
                                            'alt_text': f"Main image of {product_name}",
                                            'title': 'product_main.jpg',
                                            'width': None,
                                            'height': None,
                                            'caption': f"Main product image for {product_name}"
                                        }
                                        section_1['image_captions'] = f"Main product image for {product_name}"
                                        
                                    logger.info(f"[PROFILE_IMAGE] Auto-assigned product image to Section 1 for profile post {post_id}: {product_image_url}")
                                    
                                    # Commit the transaction
                                    conn.commit()
                                else:
                                    logger.warning(f"[PROFILE_IMAGE] Failed to create image record for post {post_id}")
                            else:
                                logger.info(f"[PROFILE_IMAGE] Section 1 already has a valid image, skipping")
                        else:
                            logger.warning(f"[PROFILE_IMAGE] Section 1 not found for post {post_id}")
                    else:
                        logger.info(f"[PROFILE_IMAGE] Post {post_id} is not a profile post (type: {post_type})")
                else:
                    logger.warning(f"[PROFILE_IMAGE] Could not load post data for post {post_id}")
            except Exception as e:
                logger.error(f"[PROFILE_IMAGE] Error auto-assigning product image for post {post_id}: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        return sections


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


def prepare_post_data(post_id):
    """
    Unified data preparation function.
    Loads all post data, sections, header image, and cross-promotion data.
    
    This is the single source of truth for data preparation used by both
    preview and publishing routes.
    
    Args:
        post_id: Post ID to load
    
    Returns:
        Tuple of (post, sections) where:
        - post: Post dict with all fields including header_image and cross_promotion
        - sections: List of section dicts with images
    """
    # Load post data
    post = get_post_with_development(post_id)
    if not post:
        logger.error(f"Post {post_id} not found")
        return None, None
    
    # Load sections
    sections = get_post_sections_with_images(post_id)
    
    # Load header image using shared function
    from .header_image_finder import get_header_image
    header_image = get_header_image(post_id)
    if header_image:
        post['header_image'] = header_image
        # Get additional metadata from database if needed
        import psycopg
        import psycopg.rows
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            cur.execute("""
                SELECT header_image_caption, header_image_title, header_image_width, header_image_height,
                       profile_category_id, recipe_id, generated_source_type
                FROM post WHERE id = %s
            """, (post_id,))
            header_data = cur.fetchone()
            if header_data:
                # Determine post type
                if header_data.get('recipe_id'):
                    post_type = 'recipe'
                elif header_data.get('profile_category_id'):
                    post_type = 'profile'
                elif header_data.get('generated_source_type'):
                    post_type = 'generated'
                else:
                    post_type = 'themed'
                
                # For Profile posts, always set the special caption
                if post_type == 'profile':
                    post['header_image']['caption'] = 'Generated artistic impression - not guaranteed accurate'
                # For other post types, use database caption if available
                elif not post['header_image'].get('caption') and header_data.get('header_image_caption'):
                    post['header_image']['caption'] = header_data['header_image_caption']
                
                # Update other metadata
                if not post['header_image'].get('title') and header_data.get('header_image_title'):
                    post['header_image']['title'] = header_data['header_image_title']
                if not post['header_image'].get('width') and header_data.get('header_image_width'):
                    post['header_image']['width'] = header_data['header_image_width']
                if not post['header_image'].get('height') and header_data.get('header_image_height'):
                    post['header_image']['height'] = header_data['header_image_height']
    
    # Load cross-promotion data using shared function
    from .cross_promotion_loader import load_cross_promotion_data
    cross_promotion = load_cross_promotion_data(post_id)
    # Always set cross_promotion, even if None, so template can check it
    post['cross_promotion'] = cross_promotion
    
    logger.info(f"✅ Prepared post data for post {post_id}")
    return post, sections


def prepare_post_for_publication(post, header_image):
    """
    Validate and enrich post data for publication.
    Ensures header_image is correctly set in post dict.
    DEPRECATED: Use prepare_post_data() instead.
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

