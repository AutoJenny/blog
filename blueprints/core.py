# blueprints/core.py
from flask import Blueprint, render_template, jsonify, request, redirect
import logging
import json
from datetime import date, timedelta
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
    Governance summary for current week.
    scheduled_slots: non-idea week items
    blog_candidates: idea week items
    """
    try:
        from datetime import datetime
        now = datetime.now()
        current_year = now.isocalendar()[0]
        current_week = now.isocalendar()[1]
        scheduled_slots = []
        blog_candidates = []
        ready_count = 0
        blocked_count = 0
        no_post_count = 0
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT cwi.id, cwi.item_type, cwi.item_id, cwi.is_primary, cwi.is_selected, cwi.weekday, cwi.scheduled_date,
                           cwi.metadata, cwi.created_at, cwi.updated_at, cwi.position,
                           p.id AS post_id, p.status AS post_status,
                           p.summary AS post_summary, p.profile_standfirst AS post_standfirst, p.subtitle AS post_subtitle,
                           p.extra_settings->>'workflow_stage' AS workflow_stage_raw,
                           COALESCE((p.extra_settings->'automation'->>'enabled') IS DISTINCT FROM 'false', TRUE) AS automation_enabled_raw
                    FROM calendar_week_items cwi
                    LEFT JOIN post p ON p.id = cwi.item_id AND cwi.item_type IN ('recipe', 'profile', 'theme')
                    WHERE cwi.year = %s AND cwi.week_number = %s
                      AND cwi.is_active = TRUE
                    ORDER BY COALESCE(cwi.weekday, 0), cwi.position, cwi.id
                """, (current_year, current_week))
                rows = cursor.fetchall() or []

            def _non_empty(*vals):
                for v in vals:
                    if v is not None and str(v).strip():
                        return str(v).strip()
                return None

            scheduled_rows = [r for r in rows if r.get('item_type') != 'idea']
            # Idea candidates: include all idea rows for the week regardless of is_active
            # (create-post-from-item may deactivate the source row; we still show it as candidate)
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT cwi.id, cwi.item_type, cwi.item_id, cwi.is_primary, cwi.is_selected, cwi.weekday, cwi.scheduled_date,
                           cwi.metadata, cwi.created_at, cwi.updated_at, cwi.position, cwi.is_active
                    FROM calendar_week_items cwi
                    WHERE cwi.year = %s AND cwi.week_number = %s AND cwi.item_type = 'idea'
                    ORDER BY COALESCE(cwi.weekday, 0), cwi.position, cwi.id
                """, (current_year, current_week))
                candidate_rows = cursor.fetchall() or []

            # Map scheduled item_type -> post_type aligned to create-from-item categories.
            item_type_to_post_type = {
                'theme': 'themed',
                'recipe': 'recipe',
                'profile': 'profile',
                'weekly_word': 'weekly_word',
                'weekly_phrase': 'weekly_phrase',
                'weekly_insult': 'weekly_insult',
            }

            required_post_types = sorted({
                item_type_to_post_type[r['item_type']]
                for r in scheduled_rows
                if r.get('item_type') in item_type_to_post_type
            })
            channels_by_post_type = {}
            enabled_channels = {'blog', 'facebook', 'instagram'}
            if required_post_types:
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT post_type, channel, content_format, is_primary, is_required
                        FROM post_type_channel_config
                        WHERE is_active = TRUE
                          AND post_type = ANY(%s)
                        ORDER BY post_type, is_primary DESC, channel, content_format
                    """, (required_post_types,))
                    cfg_rows = cursor.fetchall() or []
                for cfg in cfg_rows:
                    channel_name = str(cfg.get('channel') or '').strip().lower()
                    if channel_name not in enabled_channels:
                        continue
                    channels_by_post_type.setdefault(cfg['post_type'], []).append({
                        "channel": channel_name,
                        "content_format": cfg['content_format'],
                        "is_primary": bool(cfg.get('is_primary')),
                        "is_required": bool(cfg.get('is_required')),
                    })

            # Preload source summaries/titles for rendering.
            weekly_ids = sorted({
                r['item_id'] for r in scheduled_rows
                if r.get('item_type') in ('weekly_word', 'weekly_phrase', 'weekly_insult')
            })
            theme_ids = sorted({r['item_id'] for r in scheduled_rows if r.get('item_type') == 'theme'})
            recipe_ids = sorted({r['item_id'] for r in scheduled_rows if r.get('item_type') == 'recipe'})
            profile_ids = sorted({r['item_id'] for r in scheduled_rows if r.get('item_type') == 'profile'})
            idea_ids = sorted({r['item_id'] for r in candidate_rows if r.get('item_type') == 'idea'})

            weekly_summary_by_id = {}
            if weekly_ids:
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT id, idea_title, idea_description
                        FROM calendar_ideas
                        WHERE id = ANY(%s)
                    """, (weekly_ids,))
                    for s in cursor.fetchall() or []:
                        # Weekly rows should display the actual word/phrase, not translation/provenance text.
                        weekly_summary_by_id[s['id']] = _non_empty(
                            s.get('idea_title'),
                            s.get('idea_description'),
                        )

            idea_title_by_id = {}
            idea_summary_by_id = {}
            if idea_ids:
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT id, idea_title, idea_description
                        FROM calendar_ideas
                        WHERE id = ANY(%s)
                    """, (idea_ids,))
                    for s in cursor.fetchall() or []:
                        idea_title_by_id[s['id']] = _non_empty(s.get('idea_title'))
                        idea_summary_by_id[s['id']] = _non_empty(s.get('idea_description'))

            theme_summary_by_id = {}
            if theme_ids:
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT id, theme_description, seasonal_context, important_notes
                        FROM calendar_themes
                        WHERE id = ANY(%s)
                    """, (theme_ids,))
                    for s in cursor.fetchall() or []:
                        note_text = None
                        if isinstance(s.get('important_notes'), list) and s['important_notes']:
                            first = s['important_notes'][0]
                            if isinstance(first, dict):
                                note_text = first.get('text')
                        theme_summary_by_id[s['id']] = _non_empty(
                            s.get('theme_description'),
                            s.get('seasonal_context'),
                            note_text
                        )

            recipe_seed_summary_by_id = {}
            if recipe_ids:
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT id, recipe_description, seasonal_context
                        FROM calendar_recipes
                        WHERE id = ANY(%s)
                    """, (recipe_ids,))
                    for s in cursor.fetchall() or []:
                        recipe_seed_summary_by_id[s['id']] = _non_empty(
                            s.get('recipe_description'),
                            s.get('seasonal_context')
                        )

            profile_seed_summary_by_id = {}
            if profile_ids:
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT cps.post_id, p.profile_standfirst, p.summary, p.subtitle
                        FROM calendar_profile_sequence cps
                        LEFT JOIN post p ON p.id = cps.post_id
                        WHERE cps.post_id = ANY(%s)
                    """, (profile_ids,))
                    for s in cursor.fetchall() or []:
                        profile_seed_summary_by_id[s['post_id']] = _non_empty(
                            s.get('profile_standfirst'),
                            s.get('summary'),
                            s.get('subtitle')
                        )

            for row in scheduled_rows:
                post_id = row.get('post_id')
                item_type = row.get('item_type')
                item_id = row.get('item_id')

                mapped_post_type = item_type_to_post_type.get(item_type)
                channels = channels_by_post_type.get(mapped_post_type, []) if mapped_post_type else []

                # Summary + provisional flag by type (no fabrication / no guess).
                summary = None
                is_provisional = True
                if item_type in ('weekly_word', 'weekly_phrase', 'weekly_insult'):
                    summary = weekly_summary_by_id.get(item_id)
                    is_provisional = True
                elif item_type == 'theme':
                    # For blog slot, derive summary from post title/summary/subtitle when linked.
                    if post_id is not None:
                        try:
                            with db_manager.get_cursor() as cursor:
                                cursor.execute("""
                                    SELECT COALESCE(title, summary, subtitle) AS display_text
                                    FROM post
                                    WHERE id = %s
                                """, (post_id,))
                                row_post = cursor.fetchone()
                        except Exception as e:
                            logger.warning(f"Theme summary resolution failed for post {post_id}: {e}")
                            row_post = None
                        summary = (row_post['display_text'] if row_post and isinstance(row_post, dict)
                                   else row_post[0] if row_post and not isinstance(row_post, dict)
                                   else None)
                        is_provisional = False
                    else:
                        summary = theme_summary_by_id.get(item_id)
                        is_provisional = True
                elif item_type == 'recipe':
                    if post_id is not None:
                        summary = _non_empty(
                            row.get('post_standfirst'),
                            row.get('post_summary'),
                            row.get('post_subtitle')
                        )
                        if summary:
                            is_provisional = False
                        else:
                            summary = recipe_seed_summary_by_id.get(item_id)
                            is_provisional = True
                    else:
                        summary = recipe_seed_summary_by_id.get(item_id)
                        is_provisional = True
                elif item_type == 'profile':
                    if post_id is not None:
                        summary = _non_empty(
                            row.get('post_standfirst'),
                            row.get('post_summary'),
                            row.get('post_subtitle')
                        )
                        if summary:
                            is_provisional = False
                        else:
                            summary = profile_seed_summary_by_id.get(item_id)
                            is_provisional = True
                    else:
                        summary = profile_seed_summary_by_id.get(item_id)
                        is_provisional = True
                else:
                    # Stop condition fallback for item types with no clean mapping.
                    channels = []
                    summary = None
                    is_provisional = True

                slot = {
                    "slot_id": row['id'],
                    "item_type": row['item_type'],
                    "item_id": row['item_id'],
                    "role": row['item_type'],
                    "weekday": row['weekday'] if row['weekday'] is not None else None,
                    "scheduled_date": row['scheduled_date'].isoformat() if row.get('scheduled_date') else None,
                    "metadata": row['metadata'] if isinstance(row.get('metadata'), dict) else ({} if row.get('metadata') is None else {}),
                    "created_at": row['created_at'].isoformat().replace('+00:00', 'Z') if row.get('created_at') else None,
                    "updated_at": row['updated_at'].isoformat().replace('+00:00', 'Z') if row.get('updated_at') else None,
                    "channels": channels,
                    "summary": summary,
                    "is_provisional": is_provisional,
                    "post_id": post_id,
                    "post_status": row.get('post_status') if post_id is not None else None,
                    "workflow_stage": (row.get('workflow_stage_raw') or 'idea').strip() if post_id is not None else None,
                    "automation_enabled": bool(row.get('automation_enabled_raw') if row.get('automation_enabled_raw') is not None else True) if post_id is not None else None,
                    "output_ready": None,
                    "preflight_ok": None,
                    "automation_blocked_reason": None,
                }
                if item_type == 'theme':
                    # Display-only scheduled date: ISO Monday for the slot's ISO week.
                    try:
                        from datetime import date as _date
                        iso_monday = _date.fromisocalendar(current_year, current_week, 1)
                        slot["scheduled_date"] = iso_monday.isoformat()
                    except Exception as e:
                        logger.warning(f"Could not compute ISO Monday for theme slot {row['id']}: {e}")

                if post_id is not None:
                    block_reason = None
                    output_ok = None
                    preflight_ok = None
                    # For theme slots, do not auto-derive stage_blocked in governance summary.
                    if item_type != 'theme':
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
                scheduled_slots.append(slot)

            for row in sorted(candidate_rows, key=lambda r: (r.get('created_at') is None, r.get('created_at'))):
                idea_id = row.get('item_id')
                title = _non_empty(idea_title_by_id.get(idea_id), f'Idea #{idea_id}')
                summary = idea_summary_by_id.get(idea_id)
                meta = row.get('metadata') or {}
                if not isinstance(meta, dict):
                    meta = {}
                post_id_from_meta = meta.get('post_id')
                if post_id_from_meta is not None:
                    try:
                        post_id_from_meta = int(post_id_from_meta)
                    except (TypeError, ValueError):
                        post_id_from_meta = None
                blog_candidates.append({
                    "week_item_id": row['id'],
                    "item_id": idea_id,
                    "title": title,
                    "summary": summary,
                    "is_primary": bool(row.get('is_primary')),
                    "is_selected": bool(row.get('is_selected')),
                    "metadata": meta,
                    "post_id": post_id_from_meta,
                    "is_active": bool(row.get('is_active')),
                })

            # Active blog slot: candidate with is_selected and metadata.post_id → surface as one scheduled_slots row
            active_blog = next((c for c in blog_candidates if c.get('is_selected') and c.get('post_id')), None)
            if active_blog:
                post_id = active_blog['post_id']
                try:
                    from datetime import date as _date
                    iso_monday = _date.fromisocalendar(current_year, current_week, 1)
                    scheduled_date_iso = iso_monday.isoformat()
                except Exception:
                    scheduled_date_iso = None
                post_status = None
                workflow_stage = None
                try:
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT p.status, p.extra_settings->>'workflow_stage' AS workflow_stage
                            FROM post p WHERE p.id = %s
                        """, (post_id,))
                        pr = cursor.fetchone()
                        if pr:
                            post_status = pr.get('status')
                            workflow_stage = (pr.get('workflow_stage') or '').strip() or None
                except Exception:
                    pass
                scheduled_slots.append({
                    "slot_id": active_blog["week_item_id"],
                    "item_type": "idea",
                    "item_id": active_blog["item_id"],
                    "role": "blog",
                    "weekday": None,
                    "scheduled_date": scheduled_date_iso,
                    "metadata": active_blog.get("metadata") or {},
                    "created_at": None,
                    "updated_at": None,
                    "channels": [{"channel": "blog", "content_format": "article", "is_primary": True, "is_required": True}],
                    "summary": active_blog.get("title") or "",
                    "is_provisional": False,
                    "post_id": post_id,
                    "post_status": post_status,
                    "workflow_stage": workflow_stage,
                    "automation_enabled": None,
                    "output_ready": None,
                    "preflight_ok": None,
                    "automation_blocked_reason": None,
                })

        except Exception as db_err:
            logger.warning(f"Governance summary query failed (calendar_week_items may not exist): {db_err}")
        return jsonify({
            "current_week": current_week,
            "year": current_year,
            "scheduled_slots": scheduled_slots,
            "blog_candidates": blog_candidates,
            "automation_summary": {
                "ready_count": ready_count,
                "blocked_count": blocked_count,
                "no_post_count": no_post_count,
                "total_slots": len(scheduled_slots),
            },
        })
    except Exception as e:
        logger.error(f"Governance summary failed: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route('/api/home/governance/override-idea', methods=['POST'])
def api_home_governance_override_idea():
    """Create a new idea + week item and make it the default blog candidate for the current week."""
    try:
        data = request.get_json(silent=True) or {}
        title = (data.get('title') or '').strip()
        summary = (data.get('summary') or '').strip()
        classification = (data.get('classification') or 'blog_article').strip()
        if not title:
            return jsonify({"success": False, "error": "Title is required"}), 400

        from datetime import datetime
        now = datetime.now()
        year = int(data.get('year') or now.isocalendar()[0])
        week = int(data.get('week') or now.isocalendar()[1])

        with db_manager.get_connection() as conn:
            conn.autocommit = False
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = 'calendar_ideas'
                    """)
                    existing_columns = {row['column_name'] for row in (cursor.fetchall() or [])}

                    fields = ['week_number', 'idea_title']
                    values = [week, title]
                    if 'idea_description' in existing_columns and summary:
                        fields.append('idea_description')
                        values.append(summary)
                    if 'item_classification' in existing_columns:
                        fields.append('item_classification')
                        values.append('idea')
                    if 'content_type' in existing_columns:
                        fields.append('content_type')
                        values.append(classification)

                    placeholders = ', '.join(['%s'] * len(values))
                    cursor.execute(
                        f"INSERT INTO calendar_ideas ({', '.join(fields)}) VALUES ({placeholders}) RETURNING id",
                        tuple(values)
                    )
                    row = cursor.fetchone()
                    if not row:
                        raise RuntimeError("Failed to create calendar idea")
                    idea_id = int(row['id'])

                    # Clear previous default flags for this week.
                    cursor.execute("""
                        UPDATE calendar_week_items
                        SET metadata = COALESCE(metadata, '{}'::jsonb) - 'is_default_blog_candidate',
                            updated_at = NOW()
                        WHERE year = %s
                          AND week_number = %s
                          AND item_type = 'idea'
                          AND is_active = TRUE
                    """, (year, week))

                    candidate_metadata = {"is_default_blog_candidate": True, "classification": classification}
                    cursor.execute("""
                        INSERT INTO calendar_week_items (
                            item_type, item_id, year, week_number, weekday, scheduled_date,
                            is_selected, priority, position, metadata, notes, is_active,
                            created_at, updated_at
                        ) VALUES (
                            'idea', %s, %s, %s, NULL, NULL,
                            FALSE, 'normal', 0, %s::jsonb, NULL, TRUE,
                            NOW(), NOW()
                        )
                        ON CONFLICT (year, week_number, item_type, item_id)
                        DO UPDATE SET
                            metadata = EXCLUDED.metadata,
                            is_active = TRUE,
                            updated_at = NOW()
                        RETURNING id
                    """, (idea_id, year, week, json.dumps(candidate_metadata)))
                    week_item_row = cursor.fetchone()
                    week_item_id = int(week_item_row['id']) if week_item_row else None

                conn.commit()
            except Exception:
                conn.rollback()
                raise

        return jsonify({
            "success": True,
            "candidate": {
                "week_item_id": week_item_id,
                "item_id": idea_id,
                "title": title,
                "summary": summary or None,
                "is_default": True
            }
        })
    except Exception as e:
        logger.error(f"Governance override idea failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/home/governance/mark-candidate-converted', methods=['POST'])
def api_home_governance_mark_candidate_converted():
    """Persist converted post linkage for an idea week-item."""
    try:
        data = request.get_json(silent=True) or {}
        week_item_id = data.get('week_item_id')
        post_id = data.get('post_id')
        if week_item_id is None or post_id is None:
            return jsonify({"success": False, "error": "week_item_id and post_id are required"}), 400
        try:
            week_item_id = int(week_item_id)
            post_id = int(post_id)
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "week_item_id and post_id must be integers"}), 400

        with db_manager.get_connection() as conn:
            conn.autocommit = False
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE calendar_week_items
                        SET metadata = COALESCE(metadata, '{}'::jsonb)
                            || jsonb_build_object(
                                'converted_post_id', %s,
                                'converted_at', NOW()::text
                            ),
                            updated_at = NOW()
                        WHERE id = %s
                          AND item_type = 'idea'
                          AND is_active = TRUE
                    """, (post_id, week_item_id))
                    updated = cursor.rowcount > 0
                conn.commit()
            except Exception:
                conn.rollback()
                raise

        if not updated:
            return jsonify({"success": False, "error": "Idea candidate not found"}), 404
        return jsonify({"success": True, "week_item_id": week_item_id, "post_id": post_id})
    except Exception as e:
        logger.error(f"Mark candidate converted failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/home/upcoming-items', methods=['GET'])
def api_home_upcoming_items():
    """
    W2-OPS-9: Upcoming scheduled items across channels.
    Read-only; no schema changes.
    """
    try:
        start_date = date.today()
        end_date = start_date + timedelta(days=14)

        with db_manager.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    cwi.id AS week_item_id,
                    cwi.item_type,
                    cwi.item_id,
                    cwi.year,
                    cwi.week_number,
                    cwi.scheduled_date,
                    CASE
                        WHEN cwi.item_type = 'theme' THEN (
                            SELECT ct.theme_title
                            FROM calendar_themes ct
                            WHERE ct.id = cwi.item_id
                            LIMIT 1
                        )
                        WHEN cwi.item_type IN ('idea', 'weekly_word', 'weekly_phrase', 'weekly_insult') THEN (
                            SELECT ci.idea_title
                            FROM calendar_ideas ci
                            WHERE ci.id = cwi.item_id
                            LIMIT 1
                        )
                        WHEN cwi.item_type = 'profile' THEN (
                            SELECT COALESCE(p2.title, cps.profile_type || ' profile')
                            FROM calendar_profile_sequence cps
                            LEFT JOIN post p2 ON p2.id = cps.post_id
                            WHERE cps.post_id = cwi.item_id
                            ORDER BY cps.updated_at DESC
                            LIMIT 1
                        )
                        WHEN cwi.item_type IN ('annual_event', 'special_event') THEN (
                            SELECT ce.event_title
                            FROM calendar_events ce
                            WHERE ce.id = cwi.item_id
                            LIMIT 1
                        )
                        WHEN cwi.item_type = 'recipe' THEN (
                            SELECT p3.title
                            FROM post p3
                            WHERE p3.id = cwi.item_id
                            LIMIT 1
                        )
                        ELSE NULL
                    END AS title,
                    CASE
                        WHEN cwi.item_type = 'theme' THEN (
                            SELECT COALESCE(
                                NULLIF(ct.theme_description, ''),
                                NULLIF(ct.seasonal_context, ''),
                                NULLIF(ct.important_notes->0->>'text', '')
                            )
                            FROM calendar_themes ct
                            WHERE ct.id = cwi.item_id
                            LIMIT 1
                        )
                        WHEN cwi.item_type IN ('idea', 'weekly_word', 'weekly_phrase', 'weekly_insult') THEN (
                            SELECT COALESCE(
                                NULLIF(ci.idea_description, ''),
                                NULLIF(ci.seasonal_context, ''),
                                NULLIF(ci.important_notes->0->>'text', '')
                            )
                            FROM calendar_ideas ci
                            WHERE ci.id = cwi.item_id
                            LIMIT 1
                        )
                        WHEN cwi.item_type = 'recipe' THEN (
                            SELECT COALESCE(
                                NULLIF(cr.recipe_description, ''),
                                NULLIF(cr.seasonal_context, '')
                            )
                            FROM calendar_recipes cr
                            WHERE cr.id = cwi.item_id
                            LIMIT 1
                        )
                        WHEN cwi.item_type = 'profile' THEN (
                            SELECT COALESCE(
                                NULLIF(p2.profile_standfirst, ''),
                                NULLIF(p2.summary, ''),
                                NULLIF(p2.subtitle, '')
                            )
                            FROM calendar_profile_sequence cps
                            LEFT JOIN post p2 ON p2.id = cps.post_id
                            WHERE cps.post_id = cwi.item_id
                            ORDER BY cps.updated_at DESC
                            LIMIT 1
                        )
                        ELSE NULL
                    END AS summary,
                    p.id AS post_id
                FROM calendar_week_items cwi
                LEFT JOIN post p ON p.id = cwi.item_id AND cwi.item_type IN ('recipe', 'profile')
                WHERE cwi.is_active = TRUE
                  AND cwi.scheduled_date IS NOT NULL
                  AND cwi.scheduled_date >= %s
                  AND cwi.scheduled_date <= %s
                ORDER BY cwi.scheduled_date ASC, cwi.id ASC
                """,
                (start_date, end_date)
            )
            rows = cursor.fetchall() or []

        # Map item_type -> post_type using the same shape as create-from-item
        item_type_to_post_type = {
            'theme': 'themed',
            'recipe': 'recipe',
            'profile': 'profile',
            'weekly_word': 'weekly_word',
            'weekly_phrase': 'weekly_phrase',
            'weekly_insult': 'weekly_insult',
        }
        required_post_types = sorted({
            item_type_to_post_type[r['item_type']]
            for r in rows
            if r.get('item_type') in item_type_to_post_type
        })

        channels_by_post_type = {}
        if required_post_types:
            with db_manager.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT post_type, channel, content_format, is_primary, is_required
                    FROM post_type_channel_config
                    WHERE is_active = TRUE
                      AND post_type = ANY(%s)
                    ORDER BY post_type, is_primary DESC, channel, content_format
                    """,
                    (required_post_types,)
                )
                cfg_rows = cursor.fetchall() or []
            for cfg in cfg_rows:
                channels_by_post_type.setdefault(cfg['post_type'], []).append({
                    "channel": cfg['channel'],
                    "content_format": cfg['content_format'],
                    "is_primary": bool(cfg.get('is_primary')),
                    "is_required": bool(cfg.get('is_required')),
                })

        items = []
        for row in rows:
            item_type = row['item_type']
            mapped_post_type = item_type_to_post_type.get(item_type)
            summary = row.get('summary')
            is_provisional = bool(summary) and item_type in (
                'theme', 'recipe', 'idea', 'weekly_word', 'weekly_phrase', 'weekly_insult', 'annual_event', 'special_event'
            )
            items.append({
                "week_item_id": row['week_item_id'],
                "item_type": item_type,
                "item_id": row['item_id'],
                "year": row['year'],
                "week_number": row['week_number'],
                "date": row['scheduled_date'].isoformat() if row.get('scheduled_date') else None,
                "title": row.get('title'),
                "summary": summary,
                "is_provisional": is_provisional,
                "channels": channels_by_post_type.get(mapped_post_type, []),
                # Safe linkage only for recipe/profile in this step
                "post_id": row.get('post_id') if item_type in ('recipe', 'profile') else None,
            })

        return jsonify({"items": items})
    except Exception as e:
        logger.error(f"Upcoming items failed: {e}")
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
