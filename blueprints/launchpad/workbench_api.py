# blueprints/launchpad/workbench_api.py
"""Phase H-3: Workbench prompt persistence and generation run recording. API-only, no UI."""

from flask import Blueprint, jsonify, request, current_app
import logging
import json
from datetime import datetime
from config.database import db_manager

bp = Blueprint('workbench_api', __name__)
logger = logging.getLogger(__name__)


def _get_current_prompt(content_ref, platform, channel_type):
    """Return current prompt for workbench item or None. Does not consult legacy prompts."""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT text_prompt, image_prompt, updated_at
            FROM workbench_prompts
            WHERE content_ref = %s AND platform = %s AND channel_type = %s
        """, (content_ref, platform, channel_type))
        row = cursor.fetchone()
    return dict(row) if row else None


def _upsert_current_prompt(content_ref, platform, channel_type, text_prompt, image_prompt=None):
    """Overwrite current prompt for workbench item. Returns updated row."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO workbench_prompts (content_ref, platform, channel_type, text_prompt, image_prompt, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (content_ref, platform, channel_type)
                DO UPDATE SET text_prompt = EXCLUDED.text_prompt, image_prompt = EXCLUDED.image_prompt, updated_at = NOW()
                RETURNING id, content_ref, platform, channel_type, text_prompt, image_prompt, updated_at
            """, (content_ref, platform, channel_type, text_prompt or '', image_prompt))
            row = cur.fetchone()
        conn.commit()
    return dict(row) if row else None


# --- Group B: Prompt APIs (item-scoped) ---

@bp.route('/api/workbench/prompt', methods=['GET'])
def get_workbench_prompt():
    """Get current prompt for workbench item. Inputs: content_ref, platform, channel_type (query)."""
    try:
        content_ref = request.args.get('content_ref', type=int)
        platform = request.args.get('platform', 'facebook')
        channel_type = request.args.get('channel_type') or request.args.get('content_type', 'blog_post')
        if content_ref is None:
            return jsonify({'success': False, 'error': 'content_ref is required'}), 400
        prompt = _get_current_prompt(content_ref, platform, channel_type)
        if not prompt:
            return jsonify({
                'success': True,
                'text_prompt': None,
                'image_prompt': None,
                'updated_at': None,
                'message': 'No current prompt set for this item'
            })
        return jsonify({
            'success': True,
            'text_prompt': prompt.get('text_prompt'),
            'image_prompt': prompt.get('image_prompt'),
            'updated_at': prompt['updated_at'].isoformat() if prompt.get('updated_at') else None
        })
    except Exception as e:
        logger.error(f"Error in get_workbench_prompt: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/workbench/prompt', methods=['PUT'])
def update_workbench_prompt():
    """Update current prompt for workbench item. Inputs: content_ref, platform, channel_type, prompt payload (body)."""
    try:
        data = request.get_json() or {}
        content_ref = data.get('content_ref')
        if content_ref is None:
            return jsonify({'success': False, 'error': 'content_ref is required'}), 400
        platform = data.get('platform', 'facebook')
        channel_type = data.get('channel_type') or data.get('content_type', 'blog_post')
        text_prompt = data.get('text_prompt', '')
        image_prompt = data.get('image_prompt')
        row = _upsert_current_prompt(content_ref, platform, channel_type, text_prompt, image_prompt)
        if not row:
            return jsonify({'success': False, 'error': 'Failed to upsert prompt'}), 500
        return jsonify({
            'success': True,
            'text_prompt': row.get('text_prompt'),
            'image_prompt': row.get('image_prompt'),
            'updated_at': row['updated_at'].isoformat() if row.get('updated_at') else None
        })
    except Exception as e:
        logger.error(f"Error in update_workbench_prompt: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# --- Group C: Run APIs ---

def _create_run_record(content_ref, platform, channel_type, engine_id, trigger, prompt_snapshot, slot_identifier=None):
    """Insert run with status=started; return run_id. slot_identifier default primary for blog_post."""
    snap_json = json.dumps(prompt_snapshot) if prompt_snapshot is not None else None
    slot = slot_identifier if slot_identifier is not None else 'primary'
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO generation_runs (content_ref, platform, channel_type, engine_id, trigger, status, prompt_snapshot, slot_identifier)
                VALUES (%s, %s, %s, %s, %s, 'started', %s, %s)
                RETURNING id
            """, (content_ref, platform, channel_type, engine_id, trigger, snap_json, slot))
            row = cur.fetchone()
        conn.commit()
    return row['id'] if row else None


def _complete_run_record(run_id, status, output_refs=None, error_message=None):
    """Set finished_at, status, output_refs, error_message for run. Single update for completion."""
    refs_json = json.dumps(output_refs) if output_refs is not None else None
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE generation_runs
                SET finished_at = NOW(), status = %s, output_refs = %s, error_message = %s
                WHERE id = %s
            """, (status, refs_json, error_message, run_id))
        conn.commit()


@bp.route('/api/workbench/run', methods=['POST'])
def create_workbench_run():
    """
    Create generation run: resolve current prompt, persist run, call existing generator, persist output refs.
    Inputs: content_ref, platform, channel_type, engine_id, optional slot_identifier, optional trigger (default: user).
    Does not change generator internals; wraps existing generate-blog-content for blog_post.
    """
    try:
        data = request.get_json() or {}
        content_ref = data.get('content_ref')
        platform = data.get('platform', 'facebook')
        channel_type = data.get('channel_type') or data.get('content_type', 'blog_post')
        engine_id = data.get('engine_id', 'text/ollama-mistral')
        slot_identifier = data.get('slot_identifier', 'primary')
        trigger = data.get('trigger', 'user')
        if content_ref is None:
            return jsonify({'success': False, 'error': 'content_ref is required'}), 400

        # 1) Resolve current prompt for item (workbench path only)
        prompt = _get_current_prompt(content_ref, platform, channel_type)
        prompt_snapshot = None
        if prompt:
            prompt_snapshot = {
                'text_prompt': prompt.get('text_prompt'),
                'image_prompt': prompt.get('image_prompt')
            }

        # 2) Persist run record before generation
        run_id = _create_run_record(content_ref, platform, channel_type, engine_id, trigger, prompt_snapshot, slot_identifier)
        if not run_id:
            return jsonify({'success': False, 'error': 'Failed to create run record'}), 500

        # 3) Call existing generator (unchanged). For blog_post we POST to existing endpoint.
        output_refs = None
        outputs = []
        err_msg = None
        try:
            with current_app.test_client() as client:
                resp = client.post(
                    '/launchpad/api/syndication/generate-blog-content',
                    json={
                        'post_id': content_ref,
                        'platform': platform,
                        'channel_type': channel_type,
                        'content_type': 'blog_post'
                    },
                    content_type='application/json'
                )
            if resp.status_code == 200:
                j = resp.get_json()
                if j and j.get('success'):
                    queue_item_id = j.get('queue_item_id')
                    content = j.get('content')
                    output_refs = {'posting_queue_id': queue_item_id}
                    outputs = [{'posting_queue_id': queue_item_id, 'content_preview': (content[:200] + '...') if content and len(content) > 200 else content}]
                    _complete_run_record(run_id, 'success', output_refs=output_refs, error_message=None)
                else:
                    err_msg = j.get('error', 'Generation returned success=false') if j else 'Unknown error'
                    _complete_run_record(run_id, 'failed', output_refs=None, error_message=err_msg)
            else:
                err_msg = f"Generator returned {resp.status_code}"
                try:
                    j = resp.get_json()
                    if j:
                        err_msg = j.get('error', err_msg)
                except Exception:
                    pass
                _complete_run_record(run_id, 'failed', output_refs=None, error_message=err_msg)
        except Exception as e:
            logger.error(f"Error during workbench run generation: {e}", exc_info=True)
            err_msg = str(e)
            _complete_run_record(run_id, 'failed', output_refs=None, error_message=err_msg)

        # 4) Return run_id + outputs (and success/failure from run status)
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, content_ref, platform, channel_type, engine_id, trigger,
                       started_at, finished_at, status, prompt_snapshot, output_refs, error_message, slot_identifier
                FROM generation_runs WHERE id = %s
            """, (run_id,))
            run_row = cursor.fetchone()
        run_dict = dict(run_row) if run_row else {}
        for k in ('started_at', 'finished_at'):
            if run_dict.get(k):
                run_dict[k] = run_dict[k].isoformat()

        return jsonify({
            'success': run_dict.get('status') == 'success',
            'run_id': run_id,
            'run': run_dict,
            'outputs': outputs
        })
    except Exception as e:
        logger.error(f"Error in create_workbench_run: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/workbench/runs', methods=['GET'])
def list_workbench_runs():
    """List runs for workbench item. Inputs: content_ref, platform, channel_type (query), optional slot_identifier."""
    try:
        content_ref = request.args.get('content_ref', type=int)
        platform = request.args.get('platform', 'facebook')
        channel_type = request.args.get('channel_type') or request.args.get('content_type', 'blog_post')
        slot_identifier = request.args.get('slot_identifier')
        if content_ref is None:
            return jsonify({'success': False, 'error': 'content_ref is required'}), 400

        with db_manager.get_cursor() as cursor:
            if slot_identifier:
                cursor.execute("""
                    SELECT id, content_ref, platform, channel_type, engine_id, trigger,
                           started_at, finished_at, status, prompt_snapshot, output_refs, error_message, slot_identifier
                    FROM generation_runs
                    WHERE content_ref = %s AND platform = %s AND channel_type = %s AND slot_identifier = %s
                    ORDER BY started_at DESC
                    LIMIT 100
                """, (content_ref, platform, channel_type, slot_identifier))
            else:
                cursor.execute("""
                    SELECT id, content_ref, platform, channel_type, engine_id, trigger,
                           started_at, finished_at, status, prompt_snapshot, output_refs, error_message, slot_identifier
                    FROM generation_runs
                    WHERE content_ref = %s AND platform = %s AND channel_type = %s
                    ORDER BY started_at DESC
                    LIMIT 100
                """, (content_ref, platform, channel_type))
            rows = cursor.fetchall()

        runs = []
        for r in rows:
            d = dict(r)
            for k in ('started_at', 'finished_at'):
                if d.get(k):
                    d[k] = d[k].isoformat()
            runs.append(d)

        return jsonify({
            'success': True,
            'runs': runs,
            'count': len(runs)
        })
    except Exception as e:
        logger.error(f"Error in list_workbench_runs: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# --- Phase H-5: Engine discovery & current output ---

WORKBENCH_ENGINES = [
    {'engine_id': 'text/ollama-mistral', 'label': 'Default (Ollama Mistral)'},
    {'engine_id': 'text/default', 'label': 'Default'},
    {'engine_id': 'image/image-1', 'label': 'Image-1'},
    {'engine_id': 'image/sdxl', 'label': 'SDXL'},
]


@bp.route('/api/workbench/engines', methods=['GET'])
def get_workbench_engines():
    """Return available engines (parameters only; no engine-specific UI branching)."""
    return jsonify(WORKBENCH_ENGINES)


@bp.route('/api/workbench/current-output', methods=['GET'])
def get_workbench_current_output():
    """Get current run + output refs for the slot. Inputs: content_ref, platform, channel_type, slot_identifier (query, default primary)."""
    try:
        content_ref = request.args.get('content_ref', type=int)
        platform = request.args.get('platform', 'facebook')
        channel_type = request.args.get('channel_type') or request.args.get('content_type', 'blog_post')
        slot_identifier = request.args.get('slot_identifier', 'primary')
        if content_ref is None:
            return jsonify({'success': False, 'error': 'content_ref is required'}), 400

        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT run_id, updated_at FROM workbench_current_outputs
                WHERE content_ref = %s AND platform = %s AND channel_type = %s AND slot_identifier = %s
            """, (content_ref, platform, channel_type, slot_identifier))
            row = cursor.fetchone()
        if not row:
            return jsonify({'success': True, 'run_id': None, 'run': None, 'output_refs': None})

        run_id = row['run_id']
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, content_ref, platform, channel_type, engine_id, trigger,
                       started_at, finished_at, status, prompt_snapshot, output_refs, error_message, slot_identifier
                FROM generation_runs WHERE id = %s
            """, (run_id,))
            run_row = cursor.fetchone()
        run_dict = dict(run_row) if run_row else None
        if run_dict:
            for k in ('started_at', 'finished_at'):
                if run_dict.get(k):
                    run_dict[k] = run_dict[k].isoformat()

        return jsonify({
            'success': True,
            'run_id': run_id,
            'run': run_dict,
            'output_refs': run_dict.get('output_refs') if run_dict else None,
            'updated_at': row['updated_at'].isoformat() if row.get('updated_at') else None
        })
    except Exception as e:
        logger.error(f"Error in get_workbench_current_output: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/workbench/current-output', methods=['POST'])
def set_workbench_current_output():
    """Set current output for the slot. Body: content_ref, platform, channel_type, slot_identifier (default primary), run_id. Upsert."""
    try:
        data = request.get_json() or {}
        content_ref = data.get('content_ref')
        run_id = data.get('run_id')
        if content_ref is None or run_id is None:
            return jsonify({'success': False, 'error': 'content_ref and run_id are required'}), 400
        platform = data.get('platform', 'facebook')
        channel_type = data.get('channel_type') or data.get('content_type', 'blog_post')
        slot_identifier = data.get('slot_identifier', 'primary')

        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO workbench_current_outputs (content_ref, platform, channel_type, slot_identifier, run_id, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (content_ref, platform, channel_type, slot_identifier)
                    DO UPDATE SET run_id = EXCLUDED.run_id, updated_at = NOW()
                    RETURNING run_id, updated_at
                """, (content_ref, platform, channel_type, slot_identifier, run_id))
                row = cur.fetchone()
            conn.commit()

        return jsonify({
            'success': True,
            'run_id': row['run_id'],
            'updated_at': row['updated_at'].isoformat() if row.get('updated_at') else None
        })
    except Exception as e:
        logger.error(f"Error in set_workbench_current_output: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
