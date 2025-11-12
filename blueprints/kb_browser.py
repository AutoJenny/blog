"""
Knowledge Base Browser Blueprint
Standalone KB browsing and review interface
"""

from flask import Blueprint, render_template, request, jsonify
from config.database import db_manager
import logging
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

bp = Blueprint('kb_browser', __name__, url_prefix='/kb')

@bp.route('/browser')
def browser():
    """KB Browser main page"""
    article_id = request.args.get('article_id', type=int)
    category_id = request.args.get('category_id', type=int)
    
    article_data = None
    category_data = None
    subcategories = []
    category_articles = []
    
    if article_id:
        try:
            article_data = get_article_data(article_id)
            if article_data and article_data.get('category_id'):
                category_data = get_category_data(article_data['category_id'])
        except Exception as e:
            logger.error(f"Error loading article {article_id}: {e}")
            return render_template('kb/browser.html',
                                 error=f"Error loading article: {str(e)}")
    
    if category_id and not article_data:
        try:
            category_data = get_category_data(category_id)
            if category_data:
                # Get subcategories
                subcategories = get_subcategories(category_id)
                # Get articles in this category
                category_articles = get_category_articles(category_id)
        except Exception as e:
            logger.error(f"Error loading category {category_id}: {e}")
            return render_template('kb/browser.html',
                                 error=f"Error loading category: {str(e)}")
    
    return render_template('kb/browser.html',
                         article_data=article_data,
                         category_data=category_data,
                         subcategories=subcategories,
                         category_articles=category_articles,
                         current_article_id=article_id,
                         current_category_id=category_id)

@bp.route('/api/categories')
def api_categories():
    """Get list of all categories for navigation"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, level, parent_id, path, children_count
                FROM clan_kb_categories
                WHERE is_active = TRUE
                ORDER BY level, position, name
            """)
            categories = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'categories': [dict(c) for c in categories]
            })
    except Exception as e:
        logger.error(f"Error fetching category list: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/articles')
def api_articles():
    """Get list of all articles for navigation"""
    try:
        category_id = request.args.get('category_id', type=int)
        query = request.args.get('q', '').strip()
        
        with db_manager.get_cursor() as cursor:
            if query:
                # Search by name
                cursor.execute("""
                    SELECT id, name, category_id, url_key, position
                    FROM clan_kb_articles
                    WHERE is_active = TRUE 
                      AND (LOWER(name) LIKE %s OR LOWER(url_key) LIKE %s)
                    ORDER BY name
                    LIMIT 20
                """, (f'%{query.lower()}%', f'%{query.lower()}%'))
            elif category_id:
                cursor.execute("""
                    SELECT id, name, category_id, url_key, position
                    FROM clan_kb_articles
                    WHERE is_active = TRUE AND category_id = %s
                    ORDER BY position, name
                """, (category_id,))
            else:
                cursor.execute("""
                    SELECT id, name, category_id, url_key, position
                    FROM clan_kb_articles
                    WHERE is_active = TRUE
                    ORDER BY category_id, position, name
                """)
            articles = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'articles': [dict(a) for a in articles]
            })
    except Exception as e:
        logger.error(f"Error fetching article list: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/article/<int:article_id>')
def api_article(article_id):
    """Get full article data"""
    try:
        article_data = get_article_data(article_id)
        
        if not article_data:
            return jsonify({
                'success': False,
                'error': 'Article not found'
            }), 404
        
        # Convert datetime objects to strings for JSON serialization
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        # Serialize article data
        serialized_article = {}
        for key, value in article_data.items():
            if isinstance(value, datetime):
                serialized_article[key] = value.isoformat()
            elif isinstance(value, list):
                serialized_article[key] = [serialize_datetime(item) if isinstance(item, datetime) else item for item in value]
            else:
                serialized_article[key] = value
        
        return jsonify({
            'success': True,
            'article': serialized_article
        })
    except Exception as e:
        logger.error(f"Error fetching article {article_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/category/<int:category_id>')
def api_category(category_id):
    """Get full category data with subcategories and articles"""
    try:
        category_data = get_category_data(category_id)
        
        if not category_data:
            return jsonify({
                'success': False,
                'error': 'Category not found'
            }), 404
        
        # Get subcategories
        subcategories = get_subcategories(category_id)
        category_data['subcategories'] = subcategories
        
        # Get articles in this category
        articles = get_category_articles(category_id)
        category_data['articles'] = articles
        
        # Serialize datetime objects
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        serialized_category = {}
        for key, value in category_data.items():
            if isinstance(value, datetime):
                serialized_category[key] = value.isoformat()
            elif isinstance(value, list):
                serialized_category[key] = [serialize_datetime(item) if isinstance(item, datetime) else item for item in value]
            else:
                serialized_category[key] = value
        
        return jsonify({
            'success': True,
            'category': serialized_category
        })
    except Exception as e:
        logger.error(f"Error fetching category {category_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def get_category_breadcrumbs(category_id):
    """Build breadcrumb trail from category path"""
    if not category_id:
        return []
    
    with db_manager.get_cursor() as cursor:
        # Get the category's path
        cursor.execute("""
            SELECT path FROM clan_kb_categories WHERE id = %s
        """, (category_id,))
        
        result = cursor.fetchone()
        path_value = result['path'] if result and result.get('path') else None
        
        if not path_value:
            # Fallback: build from parent_id chain
            breadcrumbs = []
            current_id = category_id
            while current_id:
                cursor.execute("""
                    SELECT id, name, parent_id FROM clan_kb_categories WHERE id = %s
                """, (current_id,))
                cat = cursor.fetchone()
                if cat:
                    breadcrumbs.insert(0, {'id': cat['id'], 'name': cat['name']})
                    current_id = cat['parent_id']
                else:
                    break
            return breadcrumbs
        
        # Parse path (e.g., "1/58/188/72")
        path_ids = [int(id_str) for id_str in path_value.split('/') if id_str.strip()]
        
        # Also include the current category
        if category_id not in path_ids:
            path_ids.append(category_id)
        
        # Fetch all categories in the path
        if path_ids:
            # Use psycopg array syntax for proper ordering
            cursor.execute("""
                SELECT id, name, level, parent_id
                FROM clan_kb_categories
                WHERE id = ANY(%s)
                ORDER BY array_position(%s::int[], id)
            """, (path_ids, path_ids))
            
            categories = cursor.fetchall()
            breadcrumbs = [{'id': c['id'], 'name': c['name'], 'level': c['level']} for c in categories]
            
            # Filter out root categories
            # ID 1 is system root, ID 58 is "Help Centre" (we show that as root link)
            breadcrumbs = [b for b in breadcrumbs if b['id'] not in [1, 58]]
            
            return breadcrumbs
        
        return []

def get_article_data(article_id):
    """Get full article data from database"""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                id, category_id, name, url_key, feature_image, feature_image_local,
                short_text, text, meta_title, meta_keywords, meta_description,
                is_active, user_id, user_name, votes_sum, votes_num, rating,
                position, clan_created_at, clan_updated_at,
                first_seen_at, last_updated, last_content_change_at, embedded_images
            FROM clan_kb_articles
            WHERE id = %s
        """, (article_id,))
        
        article = cursor.fetchone()
        if not article:
            return None
        
        article_dict = dict(article)
        
        # Build breadcrumbs from category path
        if article_dict.get('category_id'):
            article_dict['breadcrumbs'] = get_category_breadcrumbs(article_dict['category_id'])
        
        # Clean HTML content for display
        if article_dict.get('text'):
            soup = BeautifulSoup(article_dict['text'], 'html.parser')
            article_dict['text_cleaned'] = str(soup)
        
        if article_dict.get('short_text'):
            soup = BeautifulSoup(article_dict['short_text'], 'html.parser')
            article_dict['short_text_cleaned'] = str(soup)
        
        return article_dict

def get_category_data(category_id):
    """Get category data from database"""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                id, name, url_key, meta_title, meta_keywords, meta_description,
                is_active, sort_order, parent_id, path, level, position, children_count,
                clan_created_at, clan_updated_at, first_seen_at, last_updated
            FROM clan_kb_categories
            WHERE id = %s
        """, (category_id,))
        
        category = cursor.fetchone()
        if not category:
            return None
        
        category_dict = dict(category)
        
        # Add breadcrumbs
        category_dict['breadcrumbs'] = get_category_breadcrumbs(category_id)
        
        return category_dict

def get_subcategories(category_id):
    """Get direct child categories"""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                id, name, url_key, level, children_count, position
            FROM clan_kb_categories
            WHERE parent_id = %s AND is_active = TRUE
            ORDER BY position, name
        """, (category_id,))
        
        categories = cursor.fetchall()
        return [dict(c) for c in categories]

def get_category_articles(category_id):
    """Get articles in a category"""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                id, name, url_key, position
            FROM clan_kb_articles
            WHERE category_id = %s AND is_active = TRUE
            ORDER BY position, name
        """, (category_id,))
        
        articles = cursor.fetchall()
        return [dict(a) for a in articles]

