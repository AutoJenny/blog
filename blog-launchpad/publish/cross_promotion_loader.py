"""
Cross-Promotion Data Loader
Loads cross-promotion data for posts.
"""

import logging
import psycopg
import psycopg.rows

logger = logging.getLogger(__name__)


def get_db_connection():
    """Get database connection."""
    import os
    return psycopg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        dbname=os.getenv('DB_NAME', 'blog'),
        user=os.getenv('DB_USER', 'autojenny'),
        password=os.getenv('DB_PASSWORD', '')
    )


def load_cross_promotion_data(post_id):
    """
    Load cross-promotion data for a post from database.
    Returns dict with cross-promotion fields or None if post not found.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            cur.execute("""
                SELECT cross_promotion_category_id, cross_promotion_category_title,
                       cross_promotion_product_id, cross_promotion_product_title,
                       cross_promotion_category_position, cross_promotion_product_position,
                       cross_promotion_category_widget_html, cross_promotion_product_widget_html
                FROM post WHERE id = %s
            """, (post_id,))
            header_data = cur.fetchone()
            
            if header_data:
                # Strip title parameter from widget HTML - we don't want headings on widgets
                category_widget_html = header_data.get('cross_promotion_category_widget_html')
                product_widget_html = header_data.get('cross_promotion_product_widget_html')
                
                # Remove title parameter if present
                if category_widget_html and 'title=' in category_widget_html:
                    import re
                    # Remove title="..." parameter
                    category_widget_html = re.sub(r'\s+title="[^"]*"', '', category_widget_html)
                
                if product_widget_html and 'title=' in product_widget_html:
                    import re
                    # Remove title="..." parameter
                    product_widget_html = re.sub(r'\s+title="[^"]*"', '', product_widget_html)
                
                # Return dict even if all values are None - template needs to check this
                return {
                    'category_id': header_data.get('cross_promotion_category_id'),
                    'category_title': header_data.get('cross_promotion_category_title'),
                    'product_id': header_data.get('cross_promotion_product_id'),
                    'product_title': header_data.get('cross_promotion_product_title'),
                    'category_position': header_data.get('cross_promotion_category_position'),
                    'product_position': header_data.get('cross_promotion_product_position'),
                    'category_widget_html': category_widget_html,
                    'product_widget_html': product_widget_html
                }
            else:
                logger.warning(f"Post {post_id} not found for cross-promotion data")
                # Return empty dict so template can check if widgets are configured
                return {
                    'category_id': None,
                    'category_title': None,
                    'product_id': None,
                    'product_title': None,
                    'category_position': None,
                    'product_position': None,
                    'category_widget_html': None,
                    'product_widget_html': None
                }
    except Exception as e:
        logger.error(f"Error loading cross-promotion data for post {post_id}: {e}")
        return None

