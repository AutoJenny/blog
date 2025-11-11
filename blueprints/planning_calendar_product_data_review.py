"""
Planning Calendar - Product Data Review

Displays CLAN product data for review before content generation.
"""

from flask import render_template, request
from config.database import db_manager
import logging
from utils.content_generation.clan_data_extractor import ClanDataExtractor
from utils.taxonomy_helpers import get_post_type

logger = logging.getLogger(__name__)

def planning_calendar_product_data_review(post_id):
    """
    Product Data Review sub-stage for generated posts.
    
    Displays extracted CLAN product data for human review before content generation.
    """
    try:
        # Verify this is a generated post
        post_type = get_post_type(post_id)
        if post_type != 'generated':
            from flask import redirect, url_for
            return redirect(url_for('planning.planning_calendar_taxonomy', post_id=post_id))
        
        # Get product ID from post's generated_source_type and idea_seed
        product_id = None
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.generated_source_type, pd.idea_seed
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            if result:
                source_type = result.get('generated_source_type')
                idea_seed = result.get('idea_seed', '')
                
                # Extract product ID from idea_seed
                # Format 1: "Generated from product: Product Name (ID: 123)"
                # Format 2: "Generated from product: product 185" (legacy format - extract number)
                if source_type == 'product' and idea_seed:
                    import re
                    # Try Format 1: Extract ID from "(ID: 123)"
                    match = re.search(r'\(ID:\s*(\d+)\)', idea_seed)
                    if match:
                        product_id = int(match.group(1))
                    else:
                        # Try Format 2: Extract number from "product 185" or "product: product 185"
                        # Look for "product" followed by whitespace and a number
                        number_match = re.search(r'product[:\s]+(?:product\s+)?(\d+)', idea_seed, re.IGNORECASE)
                        if number_match:
                            product_id = int(number_match.group(1))
                        else:
                            # Fallback: try to find product by name
                            # Extract product name from idea_seed
                            name_match = re.search(r'product:\s*([^(]+)', idea_seed, re.IGNORECASE)
                            if name_match:
                                product_name = name_match.group(1).strip()
                                cursor.execute("""
                                    SELECT id FROM clan_products
                                    WHERE name = %s
                                    LIMIT 1
                                """, (product_name,))
                                product_result = cursor.fetchone()
                                if product_result:
                                    product_id = product_result['id']
        
        if not product_id:
            # No product ID found - show error
            return render_template('planning/calendar/product_data_review.html',
                                 post_id=post_id,
                                 post_type=post_type,  # Required for header template conditional logic
                                 error="Product ID not found. Please ensure this post was generated from a product.",
                                 blueprint_name='planning')
        
        # Extract product data
        extractor = ClanDataExtractor()
        try:
            product_data = extractor.extract_product_data(product_id)
            validation = extractor.validate_data_completeness(product_data)
        except Exception as e:
            logger.error(f"Error extracting product data for post {post_id}: {e}")
            return render_template('planning/calendar/product_data_review.html',
                                 post_id=post_id,
                                 post_type=post_type,  # Required for header template conditional logic
                                 error=f"Error loading product data: {str(e)}",
                                 blueprint_name='planning')
        
        # Get content type name for category banner
        content_type_name = None
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT ti.display_name as content_type_name
                FROM post p
                LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                WHERE p.id = %s
            """, (post_id,))
            result = cursor.fetchone()
            if result:
                content_type_name = result.get('content_type_name')
        
        return render_template('planning/calendar/product_data_review.html',
                             post_id=post_id,
                             product_id=product_id,
                             product_data=product_data,
                             validation=validation,
                             content_type_name=content_type_name,
                             post_type=post_type,  # Required for header template conditional logic
                             blueprint_name='planning')
    except Exception as e:
        logger.error(f"Error in planning_calendar_product_data_review: {e}")
        import traceback
        traceback.print_exc()
        # Get post_type for error template
        post_type = get_post_type(post_id)
        return render_template('planning/calendar/product_data_review.html',
                             post_id=post_id,
                             post_type=post_type,  # Required for header template conditional logic
                             error=f"Error loading page: {str(e)}",
                             blueprint_name='planning')

