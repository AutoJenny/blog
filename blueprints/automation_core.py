"""
Automation Core Module
Main blueprint that imports and orchestrates all automation modules
"""

from flask import Blueprint, jsonify, request
import json
from datetime import datetime
from config.database import db_manager
from utils.output_channel_resolver import (
    validate_substage_for_output,
    get_available_output_channels_for_post
)
import logging

logger = logging.getLogger(__name__)

# Import execution functions
from blueprints.automation_execute import (
    execute_topic_allocation,
    execute_section_titling,
    execute_topic_brainstorming,
    execute_section_structure,
    execute_author_first_drafts,
    execute_image_concepts,
    execute_image_prompts,
    execute_image_captions
)

# Import other modules
from blueprints.automation_calendar import bp as calendar_bp
from blueprints.automation_pipeline import bp as pipeline_bp
from blueprints.automation_settings import bp as settings_bp

# Create main blueprint
bp = Blueprint('automation_core', __name__, url_prefix='/launchpad/one-click-publication/api')

# Register sub-blueprints
bp.register_blueprint(calendar_bp)
bp.register_blueprint(pipeline_bp)
bp.register_blueprint(settings_bp)

@bp.route('/week-worklist', methods=['GET'])
def get_week_worklist():
    """
    W2-FIX-9.2 Part C: Get posts to process for a week (calendar-driven selection).
    Respects week automation_enabled and locked. Returns ordered worklist.
    """
    try:
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)
        if not year or not week:
            return jsonify({
                "success": False,
                "error": "year and week query parameters are required",
            }), 400

        from utils.calendar.week_controls import get_week_controls
        from utils.automation.calendar_driver import get_posts_for_week

        controls = get_week_controls(year, week)
        if controls.get("locked"):
            return jsonify({
                "success": False,
                "error": f"Week {year}/W{week} is locked.",
                "week_locked": True,
                "year": year,
                "week_number": week,
            }), 409
        if not controls.get("automation_enabled", True):
            return jsonify({
                "success": True,
                "year": year,
                "week_number": week,
                "posts": [],
                "skipped": True,
                "reason": "automation_disabled",
            })

        posts = get_posts_for_week(year, week, only_automation_enabled=True)
        return jsonify({
            "success": True,
            "year": year,
            "week_number": week,
            "posts": posts,
            "week_controls": controls,
        })
    except Exception as e:
        logger.error(f"get_week_worklist failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/run-week-automation', methods=['POST'])
def run_week_automation():
    """
    W2-FIX-9.2 Part C: Run automation for a week. Picks target week(s), skips locked/disabled.
    Returns worklist; actual execution is per-post via execute_substage (caller or future batch).
    """
    try:
        data = request.get_json() or {}
        year = data.get("year")
        week = data.get("week")
        if year is None or week is None:
            from datetime import date
            y, w, _ = date.today().isocalendar()
            year = year if year is not None else y
            week = week if week is not None else w
        year = int(year)
        week = int(week)

        from utils.calendar.week_controls import get_week_controls
        from utils.automation.calendar_driver import get_posts_for_week

        controls = get_week_controls(year, week)
        if controls.get("locked"):
            return jsonify({
                "success": False,
                "error": f"Week {year}/W{week} is locked. Automation cannot run.",
                "week_locked": True,
                "year": year,
                "week_number": week,
            }), 409
        if not controls.get("automation_enabled", True):
            return jsonify({
                "success": True,
                "year": year,
                "week_number": week,
                "posts": [],
                "message": "Week automation disabled; no posts processed.",
                "skipped": True,
            })

        posts = get_posts_for_week(year, week, only_automation_enabled=True)
        return jsonify({
            "success": True,
            "year": year,
            "week_number": week,
            "posts": posts,
            "message": f"Worklist: {len(posts)} posts. Call execute-substage per post with target_year/target_week.",
        })
    except Exception as e:
        logger.error(f"run_week_automation failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/execute-substage/<stage>/<substage>', methods=['POST'])
def execute_substage(stage, substage):
    """Main router for substage execution, optionally filtered by output channel"""
    try:
        data = request.get_json() or {}
        post_id = data.get('post_id')
        output_channel = data.get('output', 'blog').lower()  # Get output channel from request
        
        if not post_id:
            return jsonify({"success": False, "error": "Post ID is required"}), 400
        
        # Validate output channel
        valid_channels = ['blog', 'facebook', 'instagram', 'twitter', 'newsletter']
        if output_channel not in valid_channels:
            output_channel = 'blog'
        
        # Validate that substage is valid for this output channel
        if not validate_substage_for_output(post_id, stage, substage, output_channel):
            available_channels = get_available_output_channels_for_post(post_id)
            return jsonify({
                "success": False,
                "error": f"Substage '{substage}' is not valid for output channel '{output_channel}'. Available channels: {', '.join(available_channels)}"
            }), 400

        # W2-FIX-9.1 Part B: Verify calendar_seed exists before automation advances
        from utils.posts.calendar_seed import verify_calendar_seed_for_automation
        target_year = data.get("target_year")  # Optional: for week-driven automation
        target_week = data.get("target_week")
        ok, err, code = verify_calendar_seed_for_automation(post_id, target_year, target_week)
        if not ok:
            return jsonify({**err, "success": False}), code

        # W2-FIX-9.2 Part D: If target week provided and week is locked, block
        if target_year is not None and target_week is not None:
            from utils.calendar.week_controls import is_week_locked
            if is_week_locked(target_year, target_week):
                return jsonify({
                    "success": False,
                    "error": f"Week {target_year}/W{target_week} is locked. Automation cannot modify posts for this week.",
                    "week_locked": True,
                    "year": target_year,
                    "week_number": target_week,
                }), 409
        
        # Add output_channel to data for execution functions (for future channel-specific logic)
        data['output_channel'] = output_channel
        
        # Route to appropriate execution function
        # Note: Most execution functions currently don't use output_channel, but it's available
        # for future channel-specific implementations (e.g., format_for_facebook, publish_to_instagram)
        if stage == 'planning':
            if substage == 'topic_brainstorming':
                result = execute_topic_brainstorming(post_id, data)
            elif substage == 'section_structure':
                result = execute_section_structure(post_id, data)
            elif substage == 'topic_allocation':
                result = execute_topic_allocation(post_id, data)
            elif substage == 'section_titling':
                result = execute_section_titling(post_id, data)
            else:
                return jsonify({"success": False, "error": f"Unknown planning substage: {substage}"}), 400
        elif stage == 'authoring':
            if substage == 'author_first_drafts':
                result = execute_author_first_drafts(post_id, data)
            elif substage == 'image_concepts':
                result = execute_image_concepts(post_id, data)
            elif substage == 'image_prompts':
                result = execute_image_prompts(post_id, data)
            elif substage == 'image_captions':
                result = execute_image_captions(post_id, data)
            else:
                return jsonify({"success": False, "error": f"Unknown authoring substage: {substage}"}), 400
        elif stage == 'content':
            # Channel-specific content formatting substages
            if substage == 'format_for_facebook':
                from blueprints.automation_execute import execute_format_for_facebook
                result = execute_format_for_facebook(post_id, data)
            elif substage == 'add_translation':
                from blueprints.automation_execute import execute_add_translation
                result = execute_add_translation(post_id, data)
            elif substage == 'add_hashtags':
                from blueprints.automation_execute import execute_add_hashtags
                result = execute_add_hashtags(post_id, data)
            elif substage == 'generate_caption':
                from blueprints.automation_execute import execute_generate_caption
                result = execute_generate_caption(post_id, data)
            elif substage.startswith('format_for_') or substage.startswith('add_'):
                # For other channels, return a placeholder - these will be implemented later
                return jsonify({
                    "success": False,
                    "error": f"Substage '{substage}' for stage '{stage}' is not yet implemented. This is a channel-specific substage that requires custom logic."
                }), 501  # Not Implemented
            else:
                return jsonify({"success": False, "error": f"Unknown content substage: {substage}"}), 400
        elif stage == 'syndication':
            # Syndication substages (extract_summary, format_for_*, publish_to_*)
            if substage.startswith('extract_') or substage.startswith('format_for_') or substage.startswith('publish_to_'):
                # For now, return a placeholder - these will be implemented later
                return jsonify({
                    "success": False,
                    "error": f"Substage '{substage}' for stage '{stage}' is not yet implemented. This is a syndication substage that requires custom logic."
                }), 501  # Not Implemented
            else:
                return jsonify({"success": False, "error": f"Unknown syndication substage: {substage}"}), 400
        elif stage == 'imaging':
            # Imaging substages (may have channel-specific variants)
            if substage == 'optimize_for_facebook':
                from blueprints.automation_execute import execute_optimize_for_facebook
                result = execute_optimize_for_facebook(post_id, data)
            elif substage.startswith('optimize_for_') or substage.startswith('create_'):
                # For other channels, return a placeholder - these will be implemented later
                return jsonify({
                    "success": False,
                    "error": f"Substage '{substage}' for stage '{stage}' is not yet implemented. This is a channel-specific imaging substage."
                }), 501  # Not Implemented
            else:
                return jsonify({"success": False, "error": f"Unknown imaging substage: {substage}"}), 400
        elif stage == 'publish':
            # Publish substages (publish_to_*)
            if substage == 'publish_to_facebook':
                # ⚠️ FACEBOOK POSTING DISABLED
                logger.error(f"BLOCKED: publish_to_facebook substage called for post_id={post_id} - Facebook posting is DISABLED")
                return jsonify({
                    "success": False,
                    "error": "Facebook posting has been disabled"
                }), 403
                from blueprints.automation_execute import execute_publish_to_facebook
                result = execute_publish_to_facebook(post_id, data)
            elif substage.startswith('publish_to_'):
                # For other channels, return a placeholder - these will be implemented later
                return jsonify({
                    "success": False,
                    "error": f"Substage '{substage}' for stage '{stage}' is not yet implemented. This is a publication substage that requires custom logic."
                }), 501  # Not Implemented
            else:
                return jsonify({"success": False, "error": f"Unknown publish substage: {substage}"}), 400
        else:
            return jsonify({"success": False, "error": f"Unknown stage: {stage}"}), 400
        
        # Add output_channel to response for tracking
        if isinstance(result, tuple):
            response_data, status_code = result
            if isinstance(response_data, dict):
                response_data['output_channel'] = output_channel
            return jsonify(response_data), status_code
        else:
            if isinstance(result, dict):
                result['output_channel'] = output_channel
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Error executing substage: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/settings', methods=['GET'])
def get_settings():
    """Get automation settings"""
    try:
        # Return empty settings if table doesn't exist
        return jsonify({
            "success": True,
            "settings": {}
        })
            
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/settings', methods=['POST'])
def save_settings():
    """Save automation settings"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        with db_manager.get_cursor() as cursor:
            for key, value in data.items():
                cursor.execute("""
                    INSERT INTO automation_settings (setting_key, setting_value)
                    VALUES (%s, %s)
                    ON CONFLICT (setting_key) 
                    DO UPDATE SET 
                        setting_value = EXCLUDED.setting_value,
                        updated_at = NOW()
                """, (key, str(value)))
            
            return jsonify({
                "success": True,
                "message": "Settings saved successfully"
            })
            
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/pause-post/<int:post_id>', methods=['POST'])
def pause_post(post_id):
    """Pause automation for a post. Uses extra_settings.paused (W2-FIX-4: no status write)."""
    try:
        from utils.posts.status_transitions import set_post_paused
        ok, err = set_post_paused(post_id, paused=True)
        if not ok:
            return jsonify({"success": False, "error": err or "Failed to pause"}), 404
        return jsonify({"success": True, "message": "Post paused successfully"})
    except Exception as e:
        logger.error(f"Error pausing post: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/resume-post/<int:post_id>', methods=['POST'])
def resume_post(post_id):
    """Resume automation for a post. Clears extra_settings.paused (W2-FIX-4: no status write)."""
    try:
        from utils.posts.status_transitions import set_post_paused
        ok, err = set_post_paused(post_id, paused=False)
        if not ok:
            return jsonify({"success": False, "error": err or "Failed to resume"}), 404
        return jsonify({"success": True, "message": "Post resumed successfully"})
    except Exception as e:
        logger.error(f"Error resuming post: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/delete-post/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    """
    Delete a post. Uses canonical status transition (W2-FIX-4).
    Consolidated posts management is in blueprints/posts.api_update_post_status().
    """
    try:
        from utils.posts.status_transitions import transition_post_status
        ok, err = transition_post_status(post_id, 'deleted', actor='automation_delete')
        if not ok:
            return jsonify({"success": False, "error": err or "Delete failed"}), 400 if "not allowed" in (err or "").lower() or "not found" not in (err or "").lower() else 404
        return jsonify({"success": True, "message": "Post deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting post: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/create-post', methods=['POST'])
def create_post():
    """Create a new post"""
    try:
        import re
        data = request.get_json()
        title = data.get('title')
        idea_seed = data.get('idea_seed')
        
        if not title:
            return jsonify({"success": False, "error": "Title is required"}), 400
        
        with db_manager.get_cursor() as cursor:
            # W2-FIX-1: Generate slug (required by schema)
            base = re.sub(r"[^a-z0-9\-]+", '-', (title or '').lower().strip().replace(' ', '-'))
            base = re.sub(r"-+", '-', base).strip('-') or 'post'
            slug = base
            suffix = 1
            while True:
                cursor.execute("SELECT 1 FROM post WHERE slug = %s LIMIT 1", (slug,))
                if not cursor.fetchone():
                    break
                suffix += 1
                slug = f"{base}-{suffix}"

            cursor.execute("""
                INSERT INTO post (title, slug, status, created_at, updated_at)
                VALUES (%s, %s, 'draft', NOW(), NOW())
                RETURNING id
            """, (title, slug))
            
            post_id = cursor.fetchone()['id']
            
            # Create post_development entry
            cursor.execute("""
                INSERT INTO post_development (post_id, idea_seed, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW())
            """, (post_id, idea_seed or ''))

            # W2-FIX-1: Ensure default sections for immediate authoring
            from utils.posts.post_factory import ensure_default_sections
            ensure_default_sections(post_id, variant='generic', template_name='default_generic')
            # W2-FIX-5: New post starts at workflow_stage=idea
            from utils.posts.workflow_stage import ensure_workflow_stage_idea
            ensure_workflow_stage_idea(post_id)
            # W2-FIX-9.1: Posts without calendar linkage get type=manual
            from utils.posts.calendar_seed import ensure_manual_seed
            ensure_manual_seed(post_id, actor="create_post")
            return jsonify({
                "success": True,
                "post_id": post_id,
                "message": "Post created successfully"
            })
            
    except Exception as e:
        logger.error(f"Error creating post: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/calendar-item', methods=['GET'])
def get_calendar_item():
    """Get calendar item data by category and item_id, or resolve by week if item_id missing"""
    try:
        category = request.args.get('category')
        item_id = request.args.get('item_id')
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)
        output_channel = request.args.get('output', 'blog')
        
        if not category:
            return jsonify({"success": False, "error": "category is required"}), 400
        
        # Use calendar resolver to get item data
        from utils.calendar_resolver import resolve_item_for_week, get_category_config
        from datetime import date
        
        item = None
        
        # If year and week provided, try to resolve for that week first (may get override)
        if year and week:
            # For weekly content, need to pass classification
            classification = None
            if category in ('weekly_word', 'weekly_phrase', 'weekly_insult'):
                classification = category
            
            item = resolve_item_for_week(category, year, week, classification=classification)
            # If resolved, use the resolved item's ID
            if item and item.get('id'):
                item_id = str(item.get('id'))
        
        # If we still don't have an item, try to get by item_id
        if not item and item_id:
            cfg = get_category_config(category)
            table = cfg["table"]
            id_col = cfg["id_column"]
            extra_filter = cfg["extra_filter"]
            
            with db_manager.get_cursor() as cursor:
                sql = f"SELECT * FROM {table} WHERE {id_col} = %s"
                params = [int(item_id)]
                
                if extra_filter:
                    cond, extra_params = extra_filter
                    sql += f" AND {cond}"
                    params.extend(extra_params)
                
                cursor.execute(sql, tuple(params))
                row = cursor.fetchone()
                item = dict(row) if row else None
        
        # If still no item and we have year/week, try resolving again (fallback)
        if not item and year and week:
            classification = None
            if category in ('weekly_word', 'weekly_phrase', 'weekly_insult'):
                classification = category
            item = resolve_item_for_week(category, year, week, classification=classification)
        
        if not item:
            return jsonify({"success": False, "error": "Item not found. Please provide item_id or year+week"}), 404
        
        # Check if post exists for this item (improved with week/year context)
        post_id = None
        with db_manager.get_cursor() as cursor:
            if category == 'theme':
                # For themes, prefer week/year context if available, fallback to title match
                if year and week:
                    # First try: Check calendar_week_posts_v2 for same year/week + theme match
                    cursor.execute("""
                        SELECT DISTINCT p.id
                        FROM calendar_week_posts_v2 cwp
                        JOIN post p ON cwp.post_id = p.id
                        LEFT JOIN post_development pd ON p.id = pd.post_id
                        WHERE cwp.year = %s 
                          AND cwp.week_number = %s
                          AND p.recipe_id IS NULL
                          AND p.profile_category_id IS NULL
                          AND (p.generated_source_type IS NULL OR p.generated_source_type = '')
                          AND p.status IN ('draft', 'in_process')
                          AND (pd.idea_seed ILIKE %s OR p.title ILIKE %s)
                        ORDER BY p.created_at DESC
                        LIMIT 1
                    """, (year, week, f'%{item.get("theme_title") or item.get("title", "")}%', f'%{item.get("theme_title") or item.get("title", "")}%'))
                    result = cursor.fetchone()
                    if result:
                        post_id = result['id']
                
                # Fallback: If no week/year match, try title match only
                # Only reuse posts in workflow states, never published
                if not post_id:
                    cursor.execute("""
                        SELECT p.id, p.status FROM post p
                        JOIN post_development pd ON p.id = pd.post_id
                        WHERE pd.idea_seed ILIKE %s 
                          AND p.status IN ('draft', 'in_process')
                        ORDER BY p.created_at DESC
                        LIMIT 1
                    """, (f'%{item.get("theme_title") or item.get("title", "")}%',))
                    result = cursor.fetchone()
                    if result:
                        post_id = result['id']
            elif category == 'recipe':
                # For recipes, use recipe_id (most reliable)
                # Only reuse posts in workflow states, never published
                cursor.execute("""
                    SELECT id, status FROM post
                    WHERE recipe_id = %s 
                      AND status IN ('draft', 'in_process')
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (item.get("id"),))
                result = cursor.fetchone()
                if result:
                    post_id = result['id']
                    logger.info(f"Reusing recipe post {post_id} with status '{result['status']}'")
            elif category in ('weekly_word', 'weekly_phrase', 'weekly_insult'):
                # For weekly content, prefer week/year context if available
                if year and week:
                    # First try: Check calendar_week_posts_v2 for same year/week + title match
                    cursor.execute("""
                        SELECT DISTINCT p.id, p.status
                        FROM calendar_week_posts_v2 cwp
                        JOIN post p ON cwp.post_id = p.id
                        LEFT JOIN post_development pd ON p.id = pd.post_id
                        WHERE cwp.year = %s 
                          AND cwp.week_number = %s
                          AND p.recipe_id IS NULL
                          AND p.profile_category_id IS NULL
                          AND p.status IN ('draft', 'in_process')
                          AND (pd.idea_seed ILIKE %s OR p.title ILIKE %s)
                        ORDER BY p.created_at DESC
                        LIMIT 1
                    """, (year, week, f'%{item.get("idea_title") or item.get("title", "")}%', f'%{item.get("idea_title") or item.get("title", "")}%'))
                    result = cursor.fetchone()
                    if result:
                        post_id = result['id']
                
                # Fallback: If no week/year match, try title match only
                # Only reuse posts in workflow states, never published
                if not post_id:
                    cursor.execute("""
                        SELECT p.id, p.status FROM post p
                        JOIN post_development pd ON p.id = pd.post_id
                        WHERE pd.idea_seed ILIKE %s 
                          AND p.status IN ('draft', 'in_process')
                        ORDER BY p.created_at DESC
                        LIMIT 1
                    """, (f'%{item.get("idea_title") or item.get("title", "")}%',))
                    result = cursor.fetchone()
                    if result:
                        post_id = result['id']
            elif category == 'profile':
                # Profile items already have post_id
                post_id = item.get("post_id")
        
        # Build response
        response_data = {
            "title": item.get("theme_title") or item.get("idea_title") or item.get("title", ""),
            "description": item.get("theme_description") or item.get("idea_description") or item.get("description", ""),
            "item_id": item.get("id"),
            "post_id": post_id,
            "category": category,
            "year": year,
            "week": week
        }
        
        # Add category-specific fields
        if category in ('weekly_word', 'weekly_phrase', 'weekly_insult'):
            response_data["translation"] = item.get("translation", "")
            response_data["usage1"] = item.get("usage1", "")
            response_data["usage2"] = item.get("usage2", "")
            if category == 'weekly_phrase':
                response_data["notes"] = item.get("notes", "")
            elif category == 'weekly_insult':
                response_data["provenance"] = item.get("notes", "")  # Insults use notes field for provenance
        
        return jsonify({
            "success": True,
            "data": response_data
        })
        
    except Exception as e:
        logger.error(f"Error getting calendar item: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/create-post-from-item', methods=['POST'])
def create_post_from_item():
    """Create a post from a calendar item, respecting channel assignment rules"""
    try:
        data = request.get_json()
        category = data.get('category')
        item_id = data.get('item_id')
        year = data.get('year')
        week = data.get('week')
        output_channel = data.get('output_channel', 'blog')
        
        if not category or not item_id:
            return jsonify({"success": False, "error": "category and item_id are required"}), 400
        
        # Validate item_id can be converted to int
        try:
            item_id_int = int(item_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid item_id: {item_id} (type: {type(item_id)})")
            return jsonify({"success": False, "error": f"Invalid item_id: {item_id}. Must be a number."}), 400
        
        # Get calendar item data
        from utils.calendar_resolver import get_category_config
        from utils.channel_assignment import (
            should_create_blog_post, 
            get_content_format,
            get_channels_for_post_type
        )
        from config.channel_content_formats import requires_post
        
        try:
            cfg = get_category_config(category)
        except Exception as e:
            logger.error(f"Error getting category config for '{category}': {e}")
            return jsonify({"success": False, "error": f"Invalid category: {category}"}), 400
        
        table = cfg.get("table")
        id_col = cfg.get("id_column")
        extra_filter = cfg.get("extra_filter")
        
        if not table or not id_col:
            logger.error(f"Invalid category config for '{category}': missing table or id_column")
            return jsonify({"success": False, "error": f"Invalid category configuration: {category}"}), 500
        
        # W2-FIX-9.1 Part D: Fail fast — require year+week for calendar-driven types before fetching item
        if category in ("theme", "weekly_word", "weekly_phrase", "weekly_insult"):
            if not year or not week:
                return jsonify({
                    "success": False,
                    "error": "year and week are required for calendar-driven post creation. Provide year and week to link post to calendar.",
                    "calendar_seed_required": True,
                }), 400
        
        with db_manager.get_cursor() as cursor:
            # Get item data
            sql = f"SELECT * FROM {table} WHERE {id_col} = %s"
            params = [item_id_int]
            
            if extra_filter:
                cond, extra_params = extra_filter
                sql += f" AND {cond}"
                params.extend(extra_params)
            
            cursor.execute(sql, tuple(params))
            item = cursor.fetchone()
            
            if not item:
                return jsonify({"success": False, "error": "Calendar item not found"}), 404
            
            item_dict = dict(item)
            
            # Determine post type and title
            post_type = None
            title = None
            recipe_id = None  # Initialize recipe_id for scope
            
            if category == 'theme':
                post_type = 'themed'
                title = item_dict.get('theme_title') or item_dict.get('title', '')
            elif category == 'recipe':
                post_type = 'recipe'
                title = item_dict.get('recipe_title') or item_dict.get('title', '')
                recipe_id = item_dict.get('id') or item_dict.get('recipe_id')
                if not recipe_id:
                    logger.error(f"Recipe ID not found in item_dict. Keys: {list(item_dict.keys())}")
                    return jsonify({"success": False, "error": "Recipe ID not found in calendar item"}), 400
            elif category == 'weekly_word':
                post_type = 'weekly_word'
                title = item_dict.get('idea_title') or item_dict.get('title', '')
            elif category == 'weekly_phrase':
                post_type = 'weekly_phrase'
                title = item_dict.get('idea_title') or item_dict.get('title', '')
            elif category == 'weekly_insult':
                post_type = 'weekly_insult'
                title = item_dict.get('idea_title') or item_dict.get('title', '')
            elif category == 'profile':
                # Profile already has a post_id
                post_id = item_dict.get('post_id')
                if post_id:
                    return jsonify({
                        "success": True,
                        "post_id": post_id,
                        "message": "Post already exists for this profile"
                    })
                return jsonify({"success": False, "error": "Profile item has no associated post"}), 400
            
            if not title:
                return jsonify({"success": False, "error": "Could not determine title for item"}), 400
            
            # CRITICAL: Check for existing post before creating (duplicate prevention)
            existing_post_id = None
            existing_post_status = None
            
            if category == 'recipe':
                # For recipes, check by recipe_id (most reliable)
                # Only reuse posts in workflow states, never published
                if not recipe_id:
                    logger.error(f"recipe_id is None for category='recipe', item_id={item_id}")
                    return jsonify({"success": False, "error": "Recipe ID not found"}), 400
                cursor.execute("""
                    SELECT id, status FROM post
                    WHERE recipe_id = %s 
                      AND status IN ('draft', 'in_process')
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (recipe_id,))
                result = cursor.fetchone()
                if result:
                    existing_post_id = result['id']
                    existing_post_status = result['status']
                    logger.info(f"Reusing recipe post {existing_post_id} with status '{existing_post_status}'")
            elif category == 'theme' and year and week:
                # For themes, check canonical week→post mapping (ID-only, no title matching).
                # Only reuse posts in workflow states, never published
                cursor.execute("""
                    SELECT DISTINCT p.id, p.status
                    FROM calendar_week_posts_v2 cwp
                    JOIN post p ON cwp.post_id = p.id
                    WHERE cwp.year = %s 
                      AND cwp.week_number = %s
                      AND p.recipe_id IS NULL
                      AND p.profile_category_id IS NULL
                      AND (p.generated_source_type IS NULL OR p.generated_source_type = '')
                      AND p.status IN ('draft', 'in_process')
                    ORDER BY cwp.created_at DESC
                    LIMIT 1
                """, (year, week))
                result = cursor.fetchone()
                if result:
                    existing_post_id = result['id']
                    existing_post_status = result['status']
                    logger.info(f"Reusing theme post {existing_post_id} with status '{existing_post_status}' for week {year}/{week}")
            
            # If existing post found, return it instead of creating new
            if existing_post_id:
                logger.info(f"Existing post found for {category} item {item_id}: post_id={existing_post_id}, status={existing_post_status}")
                # Check channel assignment rules for response
                content_format = get_content_format(post_type, output_channel)
                return jsonify({
                    "success": True,
                    "post_id": existing_post_id,
                    "message": f"Post already exists for this {category} item",
                    "channel": output_channel,
                    "content_format": content_format or 'article',
                    "existing": True
                })
            
            # Check channel assignment rules
            content_format = get_content_format(post_type, output_channel)
            
            # If output_channel is 'blog', check if blog posts are allowed for this post type
            if output_channel == 'blog':
                if not should_create_blog_post(post_type):
                    # This post type doesn't go to blog - return available channels
                    channels = get_channels_for_post_type(post_type)
                    return jsonify({
                        "success": False,
                        "error": f"Post type '{post_type}' does not publish to blog",
                        "available_channels": [
                            {
                                "channel": ch['channel'],
                                "content_format": ch['content_format'],
                                "is_primary": ch.get('is_primary', False)
                            }
                            for ch in channels
                        ],
                        "message": f"Use one of the available channels: {', '.join([ch['channel'] for ch in channels])}"
                    }), 400
            
            # Check if this format requires a blog post (for non-blog channels)
            if output_channel != 'blog':
                if content_format and not requires_post(output_channel, content_format):
                    # This is a social media-only format (e.g., word_of_day on Facebook)
                    # For weekly content, create a posting_queue row with proper idea_id linkage
                    if category in ('weekly_word', 'weekly_phrase', 'weekly_insult'):
                        from utils.posting_queue_helpers import create_weekly_social_post
                        
                        # Extract idea_id from item_id (for weekly content, item_id IS calendar_ideas.id)
                        idea_id = int(item_id)
                        
                        # Extract platform from output_channel
                        platform = output_channel.lower()  # e.g., 'facebook', 'instagram', 'twitter'
                        
                        # Generate basic content from item description
                        description = item_dict.get('idea_description') or item_dict.get('description') or ''
                        generated_content = f"{title}\n\n{description}".strip() if description else title
                        
                        # Create posting_queue row with idea_id
                        queue_id = create_weekly_social_post(
                            idea_id=idea_id,
                            content_type=category,  # 'weekly_word', 'weekly_phrase', or 'weekly_insult'
                            platform=platform,
                            generated_content=generated_content,
                            status='draft',
                            cursor=cursor
                        )
                        
                        logger.info(f"Created weekly social post: queue_id={queue_id}, idea_id={idea_id}, category={category}, platform={platform}")
                        
                        return jsonify({
                            "success": True,
                            "post_id": None,
                            "queue_id": queue_id,
                            "message": f"Weekly social post created for {output_channel} ({content_format} format). No blog post needed.",
                            "channel": output_channel,
                            "content_format": content_format,
                            "requires_blog_post": False,
                            "item_data": {
                                "title": title,
                                "description": description
                            }
                        })
                    else:
                        # Non-weekly social-only format (e.g., product posts handled elsewhere)
                        return jsonify({
                            "success": True,
                            "post_id": None,
                            "message": f"Content ready for {output_channel} ({content_format} format). No blog post needed.",
                            "channel": output_channel,
                            "content_format": content_format,
                            "requires_blog_post": False,
                            "item_data": {
                                "title": title,
                                "description": item_dict.get('theme_description') or item_dict.get('idea_description') or item_dict.get('description', '')
                            }
                        })
                elif not content_format:
                    # No format found - this shouldn't happen, but handle gracefully
                    logger.warning(f"No content format found for {post_type}/{output_channel}")
                    return jsonify({
                        "success": False,
                        "error": f"No content format configuration found for {post_type} on {output_channel}"
                    }), 400
            
            # Generate slug from title
            import re
            import time
            try:
                from slugify import slugify
                base_slug = slugify(title)
            except (ImportError, Exception) as e:
                logger.warning(f"Error using slugify, falling back to regex: {e}")
                # Fallback slug generation if slugify not available
                base_slug = re.sub(r"[^a-z0-9\-]+", '-', title.lower().strip().replace(' ', '-'))
                base_slug = re.sub(r"-+", '-', base_slug).strip('-') or 'post'
            
            # Ensure we have a valid slug
            if not base_slug or len(base_slug.strip()) == 0:
                base_slug = f"post-{int(time.time())}"
            
            # Ensure slug uniqueness
            slug = base_slug
            suffix = 1
            while True:
                cursor.execute("SELECT 1 FROM post WHERE slug = %s LIMIT 1", (slug,))
                if not cursor.fetchone():
                    break
                suffix += 1
                slug = f"{base_slug}-{suffix}"
            
            # Validate slug before insert
            if not slug or len(slug.strip()) == 0:
                logger.error(f"Generated empty slug from title: {title}")
                slug = f"post-{int(time.time())}"
            
            logger.info(f"Creating post with title: {title}, slug: {slug}, format: {content_format}")
            
            # Create post (only if blog post is needed)
            idea_seed = item_dict.get('theme_description') or item_dict.get('idea_description') or item_dict.get('description', '')
            
            cursor.execute("""
                INSERT INTO post (title, slug, status, created_at, updated_at)
                VALUES (%s, %s, 'draft', NOW(), NOW())
                RETURNING id
            """, (title, slug))
            
            result = cursor.fetchone()
            if not result or 'id' not in result:
                return jsonify({"success": False, "error": "Failed to create post - no ID returned"}), 500
            post_id = result['id']
            
            # Link to calendar item based on category
            if category == 'recipe':
                if not recipe_id:
                    logger.error(f"recipe_id is None when trying to link post {post_id} to recipe")
                    return jsonify({"success": False, "error": "Recipe ID not found when linking post"}), 500
                cursor.execute("""
                    UPDATE post SET recipe_id = %s WHERE id = %s
                """, (recipe_id, post_id))
            # For themes and weekly content, link via idea_seed in post_development
            
            # Create post_development entry
            cursor.execute("""
                INSERT INTO post_development (post_id, idea_seed)
                VALUES (%s, %s)
            """, (post_id, idea_seed))

            # W2-FIX-1: Ensure default sections for immediate authoring
            from utils.posts.post_factory import ensure_default_sections
            section_variant = 'recipe' if category == 'recipe' else 'generic'
            ensure_default_sections(post_id, variant=section_variant)
            # W2-FIX-5: New post starts at workflow_stage=idea
            from utils.posts.workflow_stage import ensure_workflow_stage_idea
            ensure_workflow_stage_idea(post_id)
            # W2-FIX-9.1: Record calendar_seed for traceability
            from utils.posts.calendar_seed import set_calendar_seed
            from datetime import date
            iso_year, iso_week, _ = date.today().isocalendar()
            seed_year = year if year is not None else iso_year
            seed_week = week
            if seed_week is None and category == "recipe":
                seed_week = item_dict.get("week_number") or item_dict.get("recipe_week_number")
            elif seed_week is None and category in ("weekly_word", "weekly_phrase", "weekly_insult"):
                seed_week = item_dict.get("week_number")
            set_calendar_seed(post_id, {
                "type": category,
                "year": seed_year,
                "week_number": seed_week,
                "item_id": int(item_id),
                "category": category,
            }, actor="create_post_from_item", cursor=cursor)
            # Link post to week in canonical week‑persistence table if year and week provided.
            # For themed blog posts this mirrors confirm_calendar_idea, writing into calendar_week_items
            # so that calendar_week_posts_v2 exposes the mapping.
            if year and week and category == 'theme':
                try:
                    from blueprints.post_type_config import get_publication_day_for_post_type
                    themed_config = get_publication_day_for_post_type('themed', cursor)
                    default_weekday = themed_config['day'] if themed_config else 3  # Wednesday fallback

                    cursor.execute("""
                        INSERT INTO calendar_week_items (
                            item_type, item_id, year, week_number, weekday, 
                            scheduled_date, scheduled_at, is_active, is_selected, priority, metadata, created_at, updated_at
                        )
                        VALUES (
                            'profile', %s, %s, %s, %s,
                            NULL, NOW(), TRUE, FALSE, 'normal', '{}'::jsonb, NOW(), NOW()
                        )
                        ON CONFLICT (year, week_number, item_type, item_id) DO UPDATE SET
                            weekday = EXCLUDED.weekday,
                            updated_at = NOW()
                    """, (post_id, year, week, default_weekday))
                    db_manager.conn.commit()
                    logger.info(f"Linked themed post {post_id} to week {year}/{week} in calendar_week_items")
                except Exception as e:
                    logger.warning(f"Could not link themed post {post_id} to week {year}/{week}: {e}")
                    # Don't fail the whole operation if calendar linking fails
            
            # Return response with format information
            response_data = {
                "success": True,
                "post_id": post_id,
                "message": "Post created successfully from calendar item",
                "channel": output_channel,
                "content_format": content_format or 'article'
            }
            
            # If this is for a non-blog channel, include format info
            if output_channel != 'blog' and content_format:
                response_data["format_info"] = {
                    "format": content_format,
                    "requires_blog_post": requires_post(output_channel, content_format)
                }
            
            return jsonify(response_data)
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error creating post from item: {e}\n{error_trace}")
        return jsonify({"success": False, "error": str(e), "traceback": error_trace}), 500
