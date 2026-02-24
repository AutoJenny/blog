# blueprints/core.py
from flask import Blueprint, render_template, jsonify, request, redirect
import logging
import json
from config.database import db_manager

bp = Blueprint('core', __name__)
logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    """Main page with header and workflow navigation."""
    try:
        from datetime import datetime
        
        # Get current week
        now = datetime.now()
        current_year = now.isocalendar()[0]
        current_week = now.isocalendar()[1]
        
        # Try to get post for current week first
        with db_manager.get_cursor() as cursor:
            # Check if calendar_week_posts_v2 exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'calendar_week_posts_v2'
                )
            """)
            has_v2_table = cursor.fetchone()['exists']
            
            first_post_id = None
            
            if has_v2_table:
                # Get post scheduled for current week (excluding deleted posts)
                cursor.execute("""
                    SELECT cwp.post_id
                    FROM calendar_week_posts_v2 cwp
                    INNER JOIN post p ON cwp.post_id = p.id
                    WHERE cwp.year = %s 
                      AND cwp.week_number = %s
                      AND p.status != 'deleted'
                    ORDER BY cwp.created_at DESC, cwp.post_id DESC
                    LIMIT 1
                """, (current_year, current_week))
                result = cursor.fetchone()
                if result:
                    first_post_id = result['post_id']
            
            # Fallback to latest post if no current week post found
            if not first_post_id:
                cursor.execute("""
                    SELECT p.id
                    FROM post p
                    WHERE p.status != 'deleted'
                    ORDER BY p.updated_at DESC, p.id DESC
                    LIMIT 1
                """)
                result = cursor.fetchone()
                first_post_id = result['id'] if result else 1
            
            # Get stats for the dashboard
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM post WHERE status != 'deleted') as post_count,
                    (SELECT COUNT(*) FROM images) as image_count,
                    (SELECT COUNT(*) FROM workflow) as workflow_count,
                    (SELECT COUNT(*) FROM llm_interaction) as llm_count
            """)
            stats = cursor.fetchone()
            
    except Exception as e:
        logger.warning(f"Could not fetch data: {e}")
        first_post_id = 1
        current_year = datetime.now().isocalendar()[0]
        current_week = datetime.now().isocalendar()[1]
        stats = {'post_count': 0, 'image_count': 0, 'workflow_count': 0, 'llm_count': 0}
    
    return render_template('index.html', 
                         first_post_id=first_post_id,
                         current_year=current_year,
                         current_week=current_week,
                         post_count=stats['post_count'],
                         image_count=stats['image_count'],
                         workflow_count=stats['workflow_count'],
                         llm_count=stats['llm_count'],
                         blueprint_name='core')

# ARCHIVED: Old workflow routes have been moved to ARCHIVED_OLD_WORKFLOW/routes/workflow_routes.py
# The following routes were removed:
# - /workflow/
# - /workflow/posts/<post_id>
# - /workflow/posts/<post_id>/<stage>
# - /workflow/posts/<post_id>/<stage>/<substage>
# - /workflow/posts/<post_id>/<stage>/<substage>/<step>
# - /api/llm-actions/content
# 
# These routes are replaced by the unified system:
# - /planning/posts/<post_id>/calendar/week-view
# - /planning/posts/<post_id>/calendar/ideas
# - /authoring/posts/<post_id>/sections/drafting
# - /imaging/posts/<post_id>/sections/image-generation
# 
# See ARCHIVED_OLD_WORKFLOW/README.md for migration details.

@bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "core"})

@bp.route('/api/ollama/status')
def ollama_status():
    """Check if Ollama is running"""
    try:
        from modules.llm_service import LLMService
        llm_service = LLMService()
        
        # Try to get available models (quick check)
        models = llm_service.get_available_models('ollama')
        
        return jsonify({
            'success': True,
            'is_running': True,
            'models': models,
            'base_url': 'http://localhost:11434'
        })
    except Exception as e:
        logger.error(f"Ollama status check failed: {e}")
        return jsonify({
            'success': True,
            'is_running': False,
            'error': str(e),
            'base_url': 'http://localhost:11434'
        })

@bp.route('/api/home/governance-summary', methods=['GET'])
def api_home_governance_summary():
    """
    W2-GOV-7: Governance summary for current week.
    Read-only. Returns slots from calendar_week_items with post/governance fields.
    """
    try:
        from datetime import datetime
        now = datetime.now()
        current_year = now.isocalendar()[0]
        current_week = now.isocalendar()[1]
        slots = []
        ready_count = 0
        blocked_count = 0
        no_post_count = 0
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT cwi.id, cwi.item_type, cwi.item_id, cwi.weekday, cwi.scheduled_date,
                           cwi.metadata, cwi.created_at, cwi.updated_at, cwi.position,
                           p.id AS post_id, p.status AS post_status,
                           p.extra_settings->>'workflow_stage' AS workflow_stage_raw,
                           COALESCE((p.extra_settings->'automation'->>'enabled') IS DISTINCT FROM 'false', TRUE) AS automation_enabled_raw
                    FROM calendar_week_items cwi
                    LEFT JOIN post p ON p.id = cwi.item_id AND cwi.item_type IN ('recipe', 'profile')
                    WHERE cwi.year = %s AND cwi.week_number = %s
                      AND cwi.is_active = TRUE
                    ORDER BY COALESCE(cwi.weekday, 0), cwi.position, cwi.id
                """, (current_year, current_week))
                rows = cursor.fetchall() or []
            for row in rows:
                post_id = row.get('post_id')
                slot = {
                    "slot_id": row['id'],
                    "item_type": row['item_type'],
                    "item_id": row['item_id'],
                    "weekday": row['weekday'] if row['weekday'] is not None else None,
                    "scheduled_date": row['scheduled_date'].isoformat() if row.get('scheduled_date') else None,
                    "metadata": row['metadata'] if isinstance(row.get('metadata'), dict) else ({} if row.get('metadata') is None else {}),
                    "created_at": row['created_at'].isoformat().replace('+00:00', 'Z') if row.get('created_at') else None,
                    "updated_at": row['updated_at'].isoformat().replace('+00:00', 'Z') if row.get('updated_at') else None,
                    "post_id": post_id,
                    "post_status": row.get('post_status') if post_id is not None else None,
                    "workflow_stage": (row.get('workflow_stage_raw') or 'idea').strip() if post_id is not None else None,
                    "automation_enabled": bool(row.get('automation_enabled_raw') if row.get('automation_enabled_raw') is not None else True) if post_id is not None else None,
                    "output_ready": None,
                    "preflight_ok": None,
                    "automation_blocked_reason": None,
                }
                if post_id is not None:
                    block_reason = None
                    output_ok = None
                    preflight_ok = None
                    try:
                        from utils.posts.automation_helpers import is_automation_enabled
                        if not is_automation_enabled(post_id):
                            block_reason = "automation_blocked"
                        else:
                            from utils.posts.workflow_stage import get_workflow_stage, STAGES
                            stage = get_workflow_stage(post_id, persist_if_missing=False, validate=False)
                            req_idx = STAGES.index('essentials_complete') if 'essentials_complete' in STAGES else 4
                            curr_idx = STAGES.index(stage) if stage in STAGES else -1
                            if curr_idx < req_idx:
                                block_reason = "stage_blocked"
                            else:
                                from utils.posts.output_readiness import get_output_readiness
                                readiness = get_output_readiness(post_id, output_channel='blog')
                                output_ok = bool(readiness.get('ok'))
                                if not output_ok:
                                    block_reason = "output_blocked"
                                else:
                                    from utils.publishing.validators import validate_post_for_clan_publish
                                    preflight = validate_post_for_clan_publish(post_id)
                                    preflight_ok = bool(preflight.get('ok'))
                                    if not preflight_ok:
                                        block_reason = "preflight_failed"
                    except Exception as helper_err:
                        logger.warning(f"Governance checks for post {post_id}: {helper_err}")
                    slot["output_ready"] = output_ok
                    slot["preflight_ok"] = preflight_ok
                    slot["automation_blocked_reason"] = block_reason
                    if block_reason is None:
                        ready_count += 1
                    else:
                        blocked_count += 1
                else:
                    no_post_count += 1
                slots.append(slot)
        except Exception as db_err:
            logger.warning(f"Governance summary query failed (calendar_week_items may not exist): {db_err}")
        return jsonify({
            "current_week": current_week,
            "year": current_year,
            "slots": slots,
            "automation_summary": {
                "ready_count": ready_count,
                "blocked_count": blocked_count,
                "no_post_count": no_post_count,
                "total_slots": len(slots),
            },
        })
    except Exception as e:
        logger.error(f"Governance summary failed: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route('/api/posts')
def api_posts():
    """
    API endpoint to get all posts.
    
    TODO: DEPRECATED - Use blueprints.posts.api_posts() instead.
    This endpoint is maintained for backward compatibility but should be replaced.
    The new consolidated endpoint is at /api/posts (blueprints/posts.py).
    This endpoint will be removed in a future refactor.
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                       pd.idea_seed
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.status != 'deleted'
                ORDER BY p.updated_at DESC, p.id DESC
            """)
            posts = cursor.fetchall()
        
        return jsonify({"posts": posts})
    except Exception as e:
        logger.error(f"Error fetching posts: {e}")
        return jsonify({"error": str(e)}), 500
