"""
Knowledge Base Browser Blueprint
Standalone KB browsing and review interface
"""

from flask import Blueprint, render_template, request, jsonify
from config.database import db_manager
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

bp = Blueprint('kb_browser', __name__, url_prefix='/kb')

@bp.route('/browser')
def browser():
    """KB Browser main page"""
    article_id = request.args.get('article_id', type=int)
    category_id = request.args.get('category_id', type=int)
    
    article_data = None
    category_data = None
    
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
        except Exception as e:
            logger.error(f"Error loading category {category_id}: {e}")
            return render_template('kb/browser.html',
                                 error=f"Error loading category: {str(e)}")
    
    return render_template('kb/browser.html',
                         article_data=article_data,
                         category_data=category_data,
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
        
        return jsonify({
            'success': True,
            'article': article_data
        })
    except Exception as e:
        logger.error(f"Error fetching article {article_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/category/<int:category_id>')
def api_category(category_id):
    """Get full category data with articles"""
    try:
        category_data = get_category_data(category_id)
        
        if not category_data:
            return jsonify({
                'success': False,
                'error': 'Category not found'
            }), 404
        
        # Get articles in this category
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, url_key, position
                FROM clan_kb_articles
                WHERE category_id = %s AND is_active = TRUE
                ORDER BY position, name
            """, (category_id,))
            articles = cursor.fetchall()
            category_data['articles'] = [dict(a) for a in articles]
        
        return jsonify({
            'success': True,
            'category': category_data
        })
    except Exception as e:
        logger.error(f"Error fetching category {category_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def get_article_data(article_id):
    """Get full article data from database"""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                id, category_id, name, url_key, feature_image, feature_image_local,
                short_text, text, meta_title, meta_keywords, meta_description,
                is_active, user_id, user_name, votes_sum, votes_num, rating,
                position, clan_created_at, clan_updated_at,
                first_seen_at, last_updated, last_content_change_at
            FROM clan_kb_articles
            WHERE id = %s
        """, (article_id,))
        
        article = cursor.fetchone()
        if not article:
            return None
        
        article_dict = dict(article)
        
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
        
        return dict(category)

