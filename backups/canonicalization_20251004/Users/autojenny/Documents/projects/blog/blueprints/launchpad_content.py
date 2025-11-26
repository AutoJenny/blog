# blueprints/launchpad_content.py
from flask import Blueprint, render_template, jsonify, request, send_file, redirect, url_for
import logging
import json
import os
import requests
from datetime import datetime, date, time, timedelta
import pytz
from humanize import naturaltime
from config.database import db_manager
import psycopg

bp = Blueprint('launchpad_content', __name__)
logger = logging.getLogger(__name__)

def strip_html_doc(content):
    """Strip HTML tags from content."""
    import re
    # Remove HTML tags
    clean = re.compile('<.*?>')
    return re.sub(clean, '', content)

@bp.route('/api/syndication/save-generated-content', methods=['POST'])
def save_generated_content():
    """Save generated content for a product."""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        content_type = data.get('content_type', 'product')
        generated_content = data.get('content') or data.get('generated_content')
        
        if not product_id or not generated_content:
            return jsonify({
                'success': False,
                'error': 'Product ID and generated content are required'
            }), 400
        
        with db_manager.get_connection() as conn:
            cur = conn.cursor()
            
            # Check if content already exists for this product and content_type
            cur.execute("""
                SELECT id FROM posting_queue
                WHERE product_id = %s AND content_type = %s
            """, (product_id, content_type))
            existing = cur.fetchone()
            
            if existing:
                # Update existing content
                cur.execute("""
                    UPDATE posting_queue
                    SET generated_content = %s, updated_at = NOW()
                    WHERE product_id = %s AND content_type = %s
                """, (generated_content, product_id, content_type))
            else:
                # Insert new content
                cur.execute("""
                    INSERT INTO posting_queue (product_id, content_type, generated_content, status, created_at, updated_at)
                    VALUES (%s, %s, %s, 'draft', NOW(), NOW())
                """, (product_id, content_type, generated_content))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Generated content saved successfully'
            })
    except Exception as e:
        logger.error(f"Error saving generated content: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/get-generated-content/<int:product_id>/<content_type>')
def get_generated_content(product_id, content_type):
    """Get generated content for a product and content type."""
    try:
        with db_manager.get_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # Query for generated content
            cur.execute("""
                SELECT generated_content as content, created_at, updated_at 
                FROM posting_queue 
                WHERE product_id = %s AND content_type = %s AND status IN ('draft', 'ready', 'pending')
            """, (product_id, content_type))
            
            result = cur.fetchone()
            
            if result:
                return jsonify({
                    'success': True,
                    'content': result['content'],
                    'created_at': result['created_at'].isoformat() if result['created_at'] else None,
                    'updated_at': result['updated_at'].isoformat() if result['updated_at'] else None
                })
            else:
                return jsonify({
                    'success': True,
                    'content': None
                })
                
    except Exception as e:
        logger.error(f"Error getting generated content: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/update-queue-status', methods=['POST'])
def update_queue_status():
    """Update queue item status and scheduling."""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        status = data.get('status')
        
        if not item_id or not status:
            return jsonify({
                'success': False,
                'error': 'Item ID and status are required'
            }), 400
        
        with db_manager.get_connection() as conn:
            cur = conn.cursor()
            
            # Get the current item to determine platform and content_type
            cur.execute("""
                SELECT product_id, content_type FROM posting_queue WHERE id = %s
            """, (item_id,))
            item = cur.fetchone()
            
            if not item:
                return jsonify({
                    'success': False,
                    'error': 'Item not found'
                }), 404
            
            # If status is 'ready', calculate next posting slot
            if status == 'ready':
                from blueprints.launchpad_scheduling import get_next_posting_slot
                next_slot = get_next_posting_slot(cur, 'facebook', item['content_type'])
                
                if next_slot:
                    cur.execute("""
                        UPDATE posting_queue
                        SET status = %s, scheduled_date = %s, scheduled_time = %s,
                            scheduled_timestamp = %s, schedule_name = %s, timezone = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (status, next_slot['scheduled_date'], next_slot['scheduled_time'],
                          next_slot['scheduled_timestamp'], next_slot['schedule_name'],
                          next_slot['timezone'], item_id))
                else:
                    cur.execute("""
                        UPDATE posting_queue
                        SET status = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (status, item_id))
            else:
                cur.execute("""
                    UPDATE posting_queue
                    SET status = %s, updated_at = NOW()
                    WHERE id = %s
                """, (status, item_id))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Queue status updated successfully'
            })
    except Exception as e:
        logger.error(f"Error updating queue status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/llm-prompts/<int:process_id>')
def get_llm_prompts(process_id):
    """Get LLM prompts for a content process."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, prompt_template, model_name, temperature, max_tokens
                FROM llm_prompts
                WHERE process_id = %s
                ORDER BY created_at DESC
            """, (process_id,))
            prompts = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'prompts': prompts
            })
    except Exception as e:
        logger.error(f"Error getting LLM prompts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/llm-prompts/<int:process_id>', methods=['PUT'])
def update_llm_prompt(process_id):
    """Update LLM prompt for a content process."""
    try:
        data = request.get_json()
        
        required_fields = ['prompt_template', 'model_name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check if prompt exists
                cursor.execute("""
                    SELECT id FROM llm_prompts WHERE process_id = %s
                """, (process_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing prompt
                    cursor.execute("""
                        UPDATE llm_prompts
                        SET prompt_template = %s, model_name = %s, temperature = %s, max_tokens = %s, updated_at = NOW()
                        WHERE process_id = %s
                    """, (data['prompt_template'], data['model_name'], 
                          data.get('temperature', 0.7), data.get('max_tokens', 500), process_id))
                else:
                    # Insert new prompt
                    cursor.execute("""
                        INSERT INTO llm_prompts (process_id, prompt_template, model_name, temperature, max_tokens, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                    """, (process_id, data['prompt_template'], data['model_name'],
                          data.get('temperature', 0.7), data.get('max_tokens', 500)))
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'LLM prompt updated successfully'
                })
    except Exception as e:
        logger.error(f"Error updating LLM prompt: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/categories')
def get_categories():
    """Get product categories."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, parent_id, level
                FROM clan_categories
                ORDER BY level, name
            """)
            
            categories = cursor.fetchall()
            
            category_list = []
            for category in categories:
                category_dict = dict(category)
                category_list.append(category_dict)
            
            return jsonify({
                'success': True,
                'categories': category_list
            })
    except Exception as e:
        logger.error(f"Error in get_categories: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/products')
def get_products():
    """Get all products for browsing."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, sku, price, description, image_url, url, printable_design_type,
                       category_ids
                FROM clan_products
                ORDER BY name
            """)
            
            products = cursor.fetchall()
            
            product_list = []
            for product in products:
                product_dict = dict(product)
                # Parse category_ids if it's a JSON string
                if product_dict.get('category_ids') and isinstance(product_dict['category_ids'], str):
                    try:
                        product_dict['category_ids'] = json.loads(product_dict['category_ids'])
                    except:
                        pass
                product_list.append(product_dict)
            
            return jsonify({
                'success': True,
                'products': product_list
            })
    except Exception as e:
        logger.error(f"Error in get_products: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/last-updated')
def get_last_updated():
    """Get last updated timestamp and product count."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM clan_products
            """)
            result = cursor.fetchone()
            product_count = result['count']
            
            # For now, just return current time as last updated
            from datetime import datetime
            last_updated = datetime.now()
            
            return jsonify({
                'success': True,
                'total_products': product_count,
                'last_updated': last_updated.isoformat()
            })
    except Exception as e:
        logger.error(f"Error in get_last_updated: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/select-product', methods=['POST'])
def select_random_product():
    """Select a random product for syndication."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, sku, price, description, image_url, url
                FROM clan_products
                ORDER BY RANDOM()
                LIMIT 1
            """)
            product = cursor.fetchone()
            
            if product:
                return jsonify({
                    'success': True,
                    'product': product
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No products found'
                })
    except Exception as e:
        logger.error(f"Error selecting random product: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/update-products', methods=['POST'])
def update_products():
    """Update product data."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # This would typically sync with external product data
                # For now, just return success
                return jsonify({
                    'success': True,
                    'message': 'Products updated successfully'
                })
    except Exception as e:
        logger.error(f"Error updating products: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/selected-product', methods=['GET'])
def get_current_product():
    """Get the currently selected product - SIMPLE VERSION."""
    try:
        with db_manager.get_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # Get the most recent selected product
            cur.execute("""
                SELECT state_value FROM ui_session_state 
                WHERE state_key = 'selected_product_id' 
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            
            result = cur.fetchone()
            
            if result and result['state_value']:
                product_id = result['state_value']
                
                # Get product details
                cur.execute("""
                    SELECT id, name, sku, price, description, image_url, url
                    FROM clan_products
                    WHERE id = %s
                """, (product_id,))
                
                product = cur.fetchone()
                return jsonify({'product': product})
            
            return jsonify({'product': None})
            
    except Exception as e:
        logger.error(f"Error getting selected product: {e}")
        return jsonify({'product': None}), 500

@bp.route('/api/selected-product', methods=['POST'])
def set_current_product():
    """Set the currently selected product - SIMPLE VERSION."""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        
        if not product_id:
            return jsonify({'error': 'product_id required'}), 400
        
        with db_manager.get_connection() as conn:
            cur = conn.cursor()
            
            # Delete old selection
            cur.execute("DELETE FROM ui_session_state WHERE state_key = 'selected_product_id'")
            
            # Insert new selection
            cur.execute("""
                INSERT INTO ui_session_state (state_key, state_value, created_at, updated_at)
                VALUES ('selected_product_id', %s, NOW(), NOW())
            """, (str(product_id),))
            
            conn.commit()
            
            return jsonify({'success': True})
            
    except Exception as e:
        logger.error(f"Error setting selected product: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/syndication/generate-social-content', methods=['POST'])
def generate_social_content():
    """Generate social media content using LLM."""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        content_type = data.get('content_type', 'product')
        
        if not product_id:
            return jsonify({
                'success': False,
                'error': 'Product ID is required'
            }), 400
        
        # Get product details
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT name, sku, price, description, image_url, url
                FROM clan_products
                WHERE id = %s
            """, (product_id,))
            product = cursor.fetchone()
            
            if not product:
                return jsonify({
                    'success': False,
                    'error': 'Product not found'
                }), 404
            
            # Get LLM prompt template
            cursor.execute("""
                SELECT prompt_template, model_name, temperature, max_tokens
                FROM llm_prompts
                WHERE process_id = 1
                ORDER BY updated_at DESC
                LIMIT 1
            """)
            prompt_config = cursor.fetchone()
            
            if not prompt_config:
                return jsonify({
                    'success': False,
                    'error': 'No LLM prompt configuration found'
                }), 404
            
            # Format the prompt with product data
            prompt_template = prompt_config['prompt_template']
            formatted_prompt = prompt_template.format(
                product_name=product['name'],
                product_sku=product['url'],  # Use URL as the call-to-action
                product_description=product['description'],
                product_price=product['price']
            )
            
            # Call LLM service
            from blueprints.llm_actions import LLMService
            llm_service = LLMService()
            
            response = llm_service.generate_content(
                prompt=formatted_prompt,
                model=prompt_config['model_name'],
                temperature=prompt_config.get('temperature', 0.7),
                max_tokens=prompt_config.get('max_tokens', 500)
            )
            
            if response and 'content' in response:
                generated_content = response['content']
                
                # Save the generated content
                cursor.execute("""
                    INSERT INTO posting_queue (product_id, content_type, generated_content, status, created_at, updated_at)
                    VALUES (%s, %s, %s, 'draft', NOW(), NOW())
                    ON CONFLICT (product_id, content_type) 
                    DO UPDATE SET generated_content = %s, updated_at = NOW()
                """, (product_id, content_type, generated_content, generated_content))
                
                return jsonify({
                    'success': True,
                    'content': generated_content,
                    'product': product
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to generate content'
                }), 500
                
    except Exception as e:
        logger.error(f"Error generating social content: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500