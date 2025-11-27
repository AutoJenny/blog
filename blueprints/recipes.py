# blueprints/recipes.py
"""Scottish Recipe Series routes and API endpoints."""

from flask import Blueprint, render_template, jsonify, request
import logging
from config.database import db_manager

bp = Blueprint('recipes', __name__)
logger = logging.getLogger(__name__)

@bp.route('/recipes')
def index():
    """Scottish Recipe Series index page - lists all 52 recipes in week order."""
    try:
        with db_manager.get_cursor() as cursor:
            # Get all recipe definitions from calendar_recipes, ordered by week_number
            cursor.execute("""
                SELECT 
                    cr.id,
                    cr.week_number,
                    cr.recipe_title,
                    cr.recipe_description,
                    cr.seasonal_context,
                    cr.priority,
                    cr.tags,
                    cr.recipe_category,
                    cr.created_at,
                    cr.updated_at,
                    p.id as post_id,
                    p.title as post_title,
                    p.slug as post_slug,
                    p.status as post_status,
                    i.id as header_image_id,
                    i.file_path as header_image_path,
                    i.filename as header_image_filename
                FROM calendar_recipes cr
                LEFT JOIN post p ON p.recipe_id = cr.id AND p.status != 'deleted'
                LEFT JOIN images i ON p.header_image_id = i.id
                ORDER BY cr.week_number ASC
            """)
            
            recipes = cursor.fetchall()
            
            # Format recipes for template
            formatted_recipes = []
            all_categories = set()
            for recipe in recipes:
                category = recipe.get('recipe_category')
                if category:
                    all_categories.add(category)
                    
                formatted_recipe = {
                    'id': recipe['id'],
                    'week_number': recipe['week_number'],
                    'recipe_title': recipe['recipe_title'],
                    'recipe_description': recipe.get('recipe_description'),
                    'seasonal_context': recipe.get('seasonal_context'),
                    'priority': recipe.get('priority', 'random'),
                    'tags': recipe.get('tags'),
                    'recipe_category': category,
                    'has_post': recipe.get('post_id') is not None,
                    'post_id': recipe.get('post_id'),
                    'post_title': recipe.get('post_title'),
                    'post_slug': recipe.get('post_slug'),
                    'post_status': recipe.get('post_status'),
                    'header_image_path': recipe.get('header_image_path'),
                    'header_image_filename': recipe.get('header_image_filename')
                }
                formatted_recipes.append(formatted_recipe)
            
            # Get unique categories for filter
            categories = sorted(list(all_categories))
            
            # Get category info for display
            cursor.execute("""
                SELECT id, name, slug, description
                FROM category
                WHERE slug = 'scottish-recipes'
                LIMIT 1
            """)
            category = cursor.fetchone()
            
            return render_template('recipes/index.html',
                                recipes=formatted_recipes,
                                category=category,
                                categories=categories,
                                total_recipes=len(formatted_recipes))
            
    except Exception as e:
        logger.error(f"Error loading recipes index: {e}")
        import traceback
        traceback.print_exc()
        return render_template('recipes/index.html',
                            recipes=[],
                            category=None,
                            categories=[],
                            total_recipes=0,
                            error=str(e))

@bp.route('/api/recipes')
def api_recipes():
    """API endpoint to get all recipes as JSON."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    cr.id,
                    cr.week_number,
                    cr.recipe_title,
                    cr.recipe_description,
                    cr.seasonal_context,
                    cr.priority,
                    cr.tags,
                    cr.recipe_category,
                    p.id as post_id,
                    p.title as post_title,
                    p.slug as post_slug,
                    p.status as post_status,
                    i.file_path as header_image_path
                FROM calendar_recipes cr
                LEFT JOIN post p ON p.recipe_id = cr.id AND p.status != 'deleted'
                LEFT JOIN images i ON p.header_image_id = i.id
                ORDER BY cr.week_number ASC
            """)
            
            recipes = cursor.fetchall()
            
            # Convert to list of dicts
            recipes_list = []
            for recipe in recipes:
                recipes_list.append({
                    'id': recipe['id'],
                    'week_number': recipe['week_number'],
                    'recipe_title': recipe['recipe_title'],
                    'recipe_description': recipe.get('recipe_description'),
                    'seasonal_context': recipe.get('seasonal_context'),
                    'priority': recipe.get('priority'),
                    'tags': recipe.get('tags'),
                    'recipe_category': recipe.get('recipe_category'),
                    'has_post': recipe.get('post_id') is not None,
                    'post_id': recipe.get('post_id'),
                    'post_title': recipe.get('post_title'),
                    'post_slug': recipe.get('post_slug'),
                    'post_status': recipe.get('post_status'),
                    'header_image_path': recipe.get('header_image_path')
                })
            
            return jsonify({'recipes': recipes_list, 'total': len(recipes_list)})
            
    except Exception as e:
        logger.error(f"Error fetching recipes API: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/recipes/reorder', methods=['POST'])
def api_reorder_recipes():
    """
    Reorder recipes by updating their week_number values.
    
    Request JSON:
    {
        "recipe_orders": [
            {"recipe_id": 1, "week_number": 1},
            {"recipe_id": 2, "week_number": 2},
            ...
        ]
    }
    
    This will update the week_number for each recipe, which will change
    where they appear in the calendar.
    """
    try:
        data = request.get_json()
        if not data or 'recipe_orders' not in data:
            return jsonify({
                'success': False,
                'error': 'recipe_orders array is required'
            }), 400
        
        recipe_orders = data['recipe_orders']
        if not isinstance(recipe_orders, list):
            return jsonify({
                'success': False,
                'error': 'recipe_orders must be an array'
            }), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Temporarily disable the unique constraint to allow swaps
                # We'll re-enable it after the updates
                cursor.execute("ALTER TABLE calendar_recipes DROP CONSTRAINT calendar_recipes_week_number_key")
                
                # Validate all recipe IDs exist and get current week_numbers
                recipe_ids = [r['recipe_id'] for r in recipe_orders]
                cursor.execute("""
                    SELECT id, week_number FROM calendar_recipes WHERE id = ANY(%s)
                """, (recipe_ids,))
                
                existing_recipes = {row['id']: row['week_number'] for row in cursor.fetchall()}
                
                if len(existing_recipes) != len(recipe_ids):
                    return jsonify({
                        'success': False,
                        'error': 'Some recipe IDs not found'
                    }), 400
                
                # Check for duplicate week_numbers
                new_week_numbers = [r['week_number'] for r in recipe_orders]
                if len(new_week_numbers) != len(set(new_week_numbers)):
                    return jsonify({
                        'success': False,
                        'error': 'Duplicate week_numbers not allowed'
                    }), 400
                
                # Validate week_numbers are in range 1-52
                for order in recipe_orders:
                    week_num = order.get('week_number')
                    if not isinstance(week_num, int) or week_num < 1 or week_num > 52:
                        return jsonify({
                            'success': False,
                            'error': f'Invalid week_number: {week_num}. Must be 1-52'
                        }), 400
                
                # Build mapping of all recipe updates
                recipe_updates = []
                for order in recipe_orders:
                    recipe_id = order['recipe_id']
                    new_week = order['week_number']
                    old_week = existing_recipes.get(recipe_id)
                    if old_week != new_week:
                        recipe_updates.append((recipe_id, new_week, old_week))
                
                if not recipe_updates:
                    # No changes needed
                    return jsonify({
                        'success': True,
                        'message': 'No reordering needed'
                    })
                
                # Update ALL recipes in a single UPDATE statement
                # This ensures constraint checking happens after all updates
                values_list = ','.join(['(%s, %s)' for _ in recipe_updates])
                recipe_ids_list = [r[0] for r in recipe_updates]
                new_weeks_list = [r[1] for r in recipe_updates]
                
                # Build the VALUES clause
                values_params = []
                for recipe_id, new_week, _ in recipe_updates:
                    values_params.extend([recipe_id, new_week])
                
                cursor.execute(f"""
                    UPDATE calendar_recipes AS cr
                    SET week_number = v.new_week, updated_at = NOW()
                    FROM (VALUES {values_list}) AS v(id, new_week)
                    WHERE cr.id = v.id
                """, tuple(values_params))
                
                # Update posts for all recipes that moved
                # Update recipe_week_number for backward compatibility, but recipe_id stays the same
                for recipe_id, new_week, old_week in recipe_updates:
                    cursor.execute("""
                        UPDATE post
                        SET recipe_week_number = %s
                        WHERE recipe_id = %s AND status != 'deleted'
                    """, (new_week, recipe_id))
                
                # Re-add the constraint
                cursor.execute("""
                    ALTER TABLE calendar_recipes 
                    ADD CONSTRAINT calendar_recipes_week_number_key 
                    UNIQUE (week_number) DEFERRABLE INITIALLY DEFERRED
                """)
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Reordered {len(recipe_orders)} recipes'
                })
                
    except Exception as e:
        logger.error(f"Error reordering recipes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/recipes/<int:recipe_week_number>/create-post', methods=['POST'])
def api_create_recipe_post(recipe_week_number):
    """
    Create a recipe post from a calendar recipe definition.
    
    Request JSON:
    {
        "year": int (optional, for scheduling),
        "week_number": int (optional, for scheduling),
        "weekday": int (optional, 1-7, for scheduling)
    }
    
    Returns:
    {
        "success": true,
        "post_id": int,
        "recipe_week_number": int,
        "message": str
    }
    """
    try:
        data = request.get_json() or {}
        year = data.get('year')
        week_number = data.get('week_number')
        
        # Get default publication day from post_type_config for recipes
        from blueprints.post_type_config import get_publication_day_for_post_type
        recipe_config = get_publication_day_for_post_type('recipe')
        default_weekday = recipe_config['day'] if recipe_config else 1  # Fallback to Monday
        weekday = data.get('weekday', default_weekday)
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Get recipe definition
                cursor.execute("""
                    SELECT id, week_number, recipe_title, recipe_description, seasonal_context
                    FROM calendar_recipes
                    WHERE week_number = %s
                    LIMIT 1
                """, (recipe_week_number,))
                
                recipe = cursor.fetchone()
                if not recipe:
                    return jsonify({
                        'success': False,
                        'error': f'Recipe for week {recipe_week_number} not found'
                    }), 404
                
                recipe_id = recipe['id'] if isinstance(recipe, dict) else recipe[0]
                recipe_title = recipe['recipe_title'] if isinstance(recipe, dict) else recipe[2]
                recipe_description = recipe.get('recipe_description') if isinstance(recipe, dict) else (recipe[3] if len(recipe) > 3 else None)
                seasonal_context = recipe.get('seasonal_context') if isinstance(recipe, dict) else (recipe[4] if len(recipe) > 4 else None)
                
                recipe_definition_id = recipe['id'] if isinstance(recipe, dict) else recipe[0]
                
                # Check if post already exists for this recipe (by recipe_id, not week_number)
                cursor.execute("""
                    SELECT id FROM post
                    WHERE recipe_id = %s AND status != 'deleted'
                    LIMIT 1
                """, (recipe_definition_id,))
                
                existing = cursor.fetchone()
                if existing:
                    existing_id = existing['id'] if isinstance(existing, dict) else existing[0]
                    return jsonify({
                        'success': False,
                        'error': f'Post already exists for recipe "{recipe_title}"',
                        'post_id': existing_id
                    }), 409
                
                # Generate slug from recipe title
                import re
                base_slug = re.sub(r"[^a-z0-9\-]+", '-', recipe_title.lower().strip().replace(' ', '-'))
                base_slug = re.sub(r"-+", '-', base_slug).strip('-') or 'recipe'
                slug = base_slug
                
                # Ensure slug uniqueness
                suffix = 1
                while True:
                    cursor.execute("SELECT 1 FROM post WHERE slug = %s LIMIT 1", (slug,))
                    if not cursor.fetchone():
                        break
                    suffix += 1
                    slug = f"{base_slug}-{suffix}"
                
                # Get Scottish Recipes category ID
                cursor.execute("SELECT id FROM category WHERE slug = 'scottish-recipes' LIMIT 1")
                category_row = cursor.fetchone()
                category_id = category_row['id'] if category_row and isinstance(category_row, dict) else (category_row[0] if category_row else None)
                
                if not category_id:
                    logger.warning("Scottish Recipes category not found, creating post without category")
                
                # Validate that recipe_week_number matches the recipe title
                if recipe_title != recipe['recipe_title']:
                    logger.error(f"Recipe title mismatch: expected '{recipe['recipe_title']}' but got '{recipe_title}'")
                    return jsonify({
                        'success': False,
                        'error': f'Recipe title mismatch for week {recipe_week_number}'
                    }), 500
                
                # Get Marion MacLeod as default author for recipe posts
                cursor.execute("""
                    SELECT id FROM author WHERE name = 'Marion MacLeod' LIMIT 1
                """)
                author_row = cursor.fetchone()
                author_id = author_row['id'] if author_row and isinstance(author_row, dict) else (author_row[0] if author_row else None)
                
                if not author_id:
                    logger.warning("Marion MacLeod author not found, creating recipe post without author")
                
                # Create post - use recipe_id (unique recipe definition ID) instead of recipe_week_number
                cursor.execute("""
                    INSERT INTO post (
                        title, slug, subtitle, recipe_id, recipe_week_number, author_id, status, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, 'draft', NOW(), NOW())
                    RETURNING id
                """, (recipe_title, slug, recipe_description, recipe_definition_id, recipe_week_number, author_id))
                
                post_result = cursor.fetchone()
                post_id = post_result['id'] if isinstance(post_result, dict) else post_result[0]
                
                # Assign category
                if category_id:
                    cursor.execute("""
                        INSERT INTO post_categories (post_id, category_id)
                        VALUES (%s, %s)
                        ON CONFLICT (post_id, category_id) DO NOTHING
                    """, (post_id, category_id))
                
                # Get and assign required tags
                cursor.execute("""
                    SELECT id FROM tag WHERE slug IN ('scottish-recipes', 'traditional-food', 'seasonal-cooking')
                """)
                tag_rows = cursor.fetchall()
                tag_ids = [row['id'] if isinstance(row, dict) else row[0] for row in tag_rows]
                
                for tag_id in tag_ids:
                    cursor.execute("""
                        INSERT INTO post_tags (post_id, tag_id)
                        VALUES (%s, %s)
                        ON CONFLICT (post_id, tag_id) DO NOTHING
                    """, (post_id, tag_id))
                
                # Create post_development entry
                idea_seed = f"{recipe_title}"
                if seasonal_context:
                    idea_seed += f": {seasonal_context}"
                
                cursor.execute("""
                    INSERT INTO post_development (post_id, idea_seed, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW())
                    ON CONFLICT (post_id) DO UPDATE SET idea_seed = EXCLUDED.idea_seed
                """, (post_id, idea_seed))
                
                # Create initial recipe sections
                recipe_sections = [
                    ('recipe_background', 'Background', 'The historic and cultural background of this recipe'),
                    ('recipe_ingredients', 'Ingredients', 'List of ingredients needed'),
                    ('recipe_method', 'Method', 'Step-by-step cooking instructions'),
                    ('recipe_variants', 'Variations', 'Optional twists and regional variations'),
                    ('recipe_serving', 'Serving Suggestions', 'How Scots traditionally serve this dish'),
                    ('recipe_further_reading', 'Further Reading', 'Authoritative sources for background information (cultural/heritage sites, Wikipedia, historical sources, ingredient provenance sites, tourism/heritage organizations). Avoid competing recipe sites.')
                ]
                
                for section_order, (section_type, section_heading, section_description) in enumerate(recipe_sections, start=1):
                    cursor.execute("""
                        INSERT INTO post_section (
                            post_id, section_order, section_type, section_heading, 
                            section_description, status, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, 'draft', NOW(), NOW())
                    """, (post_id, section_order, section_type, section_heading, section_description))
                
                # Schedule in calendar if year/week provided
                if year and week_number:
                    try:
                        # DUAL-WRITE: Write to calendar_week_posts (old table)
                        cursor.execute("""
                            INSERT INTO calendar_week_posts (
                                year, week_number, post_id, weekday, created_at
                            )
                            VALUES (%s, %s, %s, %s, NOW())
                            ON CONFLICT (year, week_number, post_id) DO UPDATE SET
                                weekday = EXCLUDED.weekday,
                                updated_at = NOW()
                        """, (year, week_number, post_id, weekday))
                        
                        # DUAL-WRITE: Also write to calendar_week_items (new unified table)
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_schema = 'public' 
                                AND table_name = 'calendar_week_items'
                            )
                        """)
                        has_week_items = cursor.fetchone()['exists']
                        
                        if has_week_items:
                            # Get recipe definition ID for metadata
                            cursor.execute("""
                                SELECT recipe_id, recipe_week_number
                                FROM post
                                WHERE id = %s
                            """, (post_id,))
                            recipe_info = cursor.fetchone()
                            
                            metadata = {}
                            if recipe_info:
                                if recipe_info.get('recipe_id'):
                                    metadata['recipe_definition_id'] = recipe_info['recipe_id']
                                if recipe_info.get('recipe_week_number'):
                                    metadata['recipe_week_number'] = recipe_info['recipe_week_number']
                            
                            cursor.execute("""
                                INSERT INTO calendar_week_items (
                                    item_type, item_id, year, week_number, weekday,
                                    is_active, metadata, created_at, updated_at
                                ) VALUES (
                                    'recipe', %s, %s, %s, %s, TRUE, %s, NOW(), NOW()
                                )
                                ON CONFLICT (year, week_number, item_type, item_id)
                                DO UPDATE SET
                                    weekday = EXCLUDED.weekday,
                                    metadata = EXCLUDED.metadata,
                                    updated_at = NOW()
                            """, (post_id, year, week_number, weekday, metadata))
                    except Exception as schedule_error:
                        logger.warning(f"Could not schedule recipe post in calendar: {schedule_error}")
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'post_id': post_id,
                    'recipe_week_number': recipe_week_number,
                    'recipe_title': recipe_title,
                    'message': f'Recipe post created successfully for week {recipe_week_number}'
                })
                
    except Exception as e:
        logger.error(f"Error creating recipe post: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
