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
            
            if not header_data:
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

            # Start with DB values
            category_id = header_data.get('cross_promotion_category_id')
            category_title = header_data.get('cross_promotion_category_title')
            product_id = header_data.get('cross_promotion_product_id')
            product_title = header_data.get('cross_promotion_product_title')
            category_position = header_data.get('cross_promotion_category_position')
            product_position = header_data.get('cross_promotion_product_position')
            category_widget_html = header_data.get('cross_promotion_category_widget_html')
            product_widget_html = header_data.get('cross_promotion_product_widget_html')

            # If nothing configured at all, opportunistically auto-select a random category/product
            # so preview always shows some x-marketing widget by default.
            try:
                need_persist_ids = False
                # Auto-select category if missing
                if not category_id:
                    cur.execute("SELECT id, name FROM clan_categories ORDER BY RANDOM() LIMIT 1")
                    cat = cur.fetchone()
                    if cat:
                        category_id = cat['id']
                        category_title = cat.get('name') or 'Related Department'
                        # Default after section 2 (position 3). This will be mapped appropriately in template.
                        category_position = category_position or 3
                        need_persist_ids = True

                # Auto-select product if missing
                if not product_id:
                    cur.execute("SELECT id, name FROM clan_products ORDER BY RANDOM() LIMIT 1")
                    prod = cur.fetchone()
                    if prod:
                        product_id = prod['id']
                        product_title = prod.get('name') or 'Related Products'
                        # Default after section 4 (position 5)
                        product_position = product_position or 5
                        need_persist_ids = True

                if need_persist_ids:
                    cur.execute("""
                        UPDATE post SET
                            cross_promotion_category_id = %s,
                            cross_promotion_category_title = %s,
                            cross_promotion_product_id = %s,
                            cross_promotion_product_title = %s,
                            cross_promotion_category_position = COALESCE(cross_promotion_category_position, %s),
                            cross_promotion_product_position = COALESCE(cross_promotion_product_position, %s),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (
                        category_id,
                        category_title,
                        product_id,
                        product_title,
                        category_position or 3,
                        product_position or 5,
                        post_id
                    ))
                    conn.commit()
            except Exception as e:
                logger.warning(f"Auto-selecting cross-promotion IDs for post {post_id} failed: {e}")

            # Ensure widget HTML exists for preview (and persist it)
            try:
                widget_changed = False
                if category_id and category_position and not category_widget_html:
                    # Do NOT include title attribute; we strip titles in widgets for a cleaner look.
                    category_widget_html = f'{{{{widget type="swcatalog/widget_crossSell_category" category_id="{category_id}"}}}}'
                    widget_changed = True
                if product_id and product_position and not product_widget_html:
                    product_widget_html = f'{{{{widget type="swcatalog/widget_crossSell_product" product_id="{product_id}"}}}}'
                    widget_changed = True

                if widget_changed:
                    cur.execute("""
                        UPDATE post SET
                            cross_promotion_category_widget_html = %s,
                            cross_promotion_product_widget_html = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (
                        category_widget_html,
                        product_widget_html,
                        post_id
                    ))
                    conn.commit()
            except Exception as e:
                logger.warning(f"Auto-generating cross-promotion widget HTML for post {post_id} failed: {e}")

            # Strip title parameter from widget HTML - we don't want headings on widgets
            if category_widget_html and 'title=' in category_widget_html:
                import re
                category_widget_html = re.sub(r'\s+title="[^"]*"', '', category_widget_html)

            if product_widget_html and 'title=' in product_widget_html:
                import re
                product_widget_html = re.sub(r'\s+title="[^"]*"', '', product_widget_html)

            # Return dict even if some values are None - template needs to check this
            return {
                'category_id': category_id,
                'category_title': category_title,
                'product_id': product_id,
                'product_title': product_title,
                'category_position': category_position,
                'product_position': product_position,
                'category_widget_html': category_widget_html,
                'product_widget_html': product_widget_html
            }
    except Exception as e:
        logger.error(f"Error loading cross-promotion data for post {post_id}: {e}")
        return None

