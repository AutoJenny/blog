"""
Routes for the workflow module.
"""

import json
import psycopg2
import psycopg2.extras
from flask import render_template, request, jsonify, abort, redirect, url_for, Blueprint, current_app
from app.db import get_db_conn
from app.api.workflow.decorators import deprecated_endpoint
from . import bp, api_workflow_bp

# Use proper nav module instead
from modules.nav.services import get_workflow_context
from app.services.shared import get_workflow_stages_from_db, get_all_posts_from_db
import subprocess
import sys
import os
from app.llm.services import execute_llm_request

# Mapping of substage names to Font Awesome icons
SUBSTAGE_ICONS = {
    'idea': 'lightbulb',
    'research': 'search',
    'structure': 'sitemap',
    'content': 'pen',
    'meta_info': 'tags',
    'images': 'image',
    'preflight': 'check-circle',
    'launch': 'rocket',
    'syndication': 'share-alt'
}

# Helper to get the most recent, non-deleted post
def get_latest_post():
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.id, pd.idea_seed
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.status != 'deleted'
                ORDER BY p.updated_at DESC, p.id DESC
                LIMIT 1
            """)
            return cur.fetchone()

def get_post_and_idea_seed(post_id):
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT p.id, pd.idea_seed FROM post p LEFT JOIN post_development pd ON p.id = pd.post_id WHERE p.id = %s", (post_id,))
            row = cur.fetchone()
            if row:
                # Convert to dict and ensure id is accessible as post.id
                return dict(row)
            return None

def get_all_posts():
    """Get all posts for the workflow navigation."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, title
                FROM post
                ORDER BY title ASC
            """)
            return cur.fetchall()

def load_step_config(stage_name: str, substage_name: str, step_name: str):
    config_path = os.path.join(os.path.dirname(__file__), 'config', f'{stage_name}_steps.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get(stage_name, {}).get(substage_name, {}).get(step_name, {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def get_post_development_fields(post_id):
    """Get all field values from post_development for a given post."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Get column names from post_development table
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'post_development' 
                AND column_name NOT IN ('id', 'post_id')
            """)
            columns = [row['column_name'] for row in cur.fetchall()]
            
            # Get field values for the post
            if columns:
                column_list = ', '.join(columns)
                cur.execute(f"""
                    SELECT {column_list}
                    FROM post_development
                    WHERE post_id = %s
                """, (post_id,))
                row = cur.fetchone()
                if row:
                    return {col: row[col] for col in columns}
    return {}

@bp.route('/')
def index():
    """Workflow index page."""
    all_posts = get_all_posts_from_db()
    if not all_posts:
        abort(404, "No posts found.")
    return redirect(url_for('workflow.stages', post_id=all_posts[0]['id']))

@bp.route('/posts/<int:post_id>/<stage>/<substage>')
@bp.route('/posts/<int:post_id>')
def workflow_index(post_id, stage=None, substage=None):
    """Main workflow page."""
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    
    # If no stage/substage provided, redirect to planning/idea
    if not stage or not substage:
        return redirect(url_for('workflow.workflow_index', 
            post_id=post_id, 
            stage='planning',
            substage='idea',
            step='initial_concept'
        ))
    
    # Get step from query parameters, keeping original format for database lookup
    step = request.args.get('step', 'initial_concept')
    # Convert URL format (lowercase with underscores) to DB format (title case with spaces)
    display_step = step.replace('_', ' ').title()
    
    # Get workflow context from the nav module
    context = get_workflow_context(stage, substage, display_step)
    if not context:
        # If no context found, redirect to the first stage/substage
        stages = get_workflow_stages_from_db()
        if stages:
            first_stage = next(iter(stages))
            first_substage = next(iter(stages[first_stage]))
            first_step = stages[first_stage][first_substage][0]
            step_url = first_step.lower().replace(' ', '_')
            return redirect(f"/workflow/posts/{post_id}/{first_stage}/{first_substage}?step={step_url}")
        abort(404, "No workflow stages found")
    
    # Get step configuration and field values
    step_config = {
        'inputs': {},
        'outputs': {},
        'settings': {
            'llm': {
                'provider': 'ollama',
                'model': 'mistral',
                'parameters': {
                    'temperature': 0.7,
                    'max_tokens': 1000
                }
            }
        }
    }
    
    result = None
    step_id = None
    step_name = None
    step_description = None
    if stage and substage:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Get step configuration using ILIKE for case-insensitive match
                cur.execute("""
                    SELECT wse.config, wse.name as step_name, wse.id as step_id, wse.description
                    FROM workflow_step_entity wse
                    JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                    JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                    WHERE wst.name ILIKE %s AND wsse.name ILIKE %s
                    AND wse.name ILIKE %s
                """, (stage, substage, display_step))
                result = cur.fetchone()
                if result:
                    config_json, step_name, step_id, step_description = result['config'], result['step_name'], result['step_id'], result['description']
                    # Convert DB step name to URL format for consistency
                    url_step_name = step_name.lower().replace(' ', '_')
                    if config_json:
                        try:
                            # Parse config_json if it's a string
                            if isinstance(config_json, str):
                                config_json = json.loads(config_json)
                            # Update step configuration with stored config
                            step_config = config_json
                        except json.JSONDecodeError:
                            current_app.logger.error(f"Failed to parse step configuration: {config_json}")
                        
                        # Ensure field_mapping is properly structured for all steps
                        if 'field_mapping' not in step_config:
                            step_config['field_mapping'] = []
                            if 'inputs' in step_config:
                                for input_id, input_config in step_config['inputs'].items():
                                    if isinstance(input_config, dict) and 'db_field' in input_config:
                                        step_config['field_mapping'].append({
                                            'field_name': input_config['db_field'],
                                            'order_index': len(step_config['field_mapping'])
                                        })
                            if 'outputs' in step_config:
                                for output_id, output_config in step_config['outputs'].items():
                                    if isinstance(output_config, dict) and 'db_field' in output_config:
                                        step_config['field_mapping'].append({
                                            'field_name': output_config['db_field'],
                                            'order_index': len(step_config['field_mapping'])
                                        })
                else:
                    # Step not found in database, try to load from JSON configuration
                    current_app.logger.warning(f"Step '{display_step}' not found in database for {stage}/{substage}, trying JSON config")
                    json_config = load_step_config(stage, substage, step)
                    if json_config:
                        step_config.update(json_config)
                        step_name = display_step
                        current_app.logger.info(f"Loaded step configuration from JSON for {stage}/{substage}/{step}")
                    else:
                        current_app.logger.error(f"Step '{step}' not found in JSON config for {stage}/{substage}")
    
    # Get field values from post_development
    field_values = get_post_development_fields(post_id)
    
    # Add step configuration and field values to context
    context.update({
        'step_config': step_config,
        'field_values': field_values,
        'step_id': step_id,
        'current_stage': stage,
        'current_substage': substage,
        'current_step': step,
        'current_post_id': post_id,
        'all_posts': get_all_posts(),
        'post': post,
        'step': {
            'name': step_name or display_step,
            'description': step_description
        }
    })
    
    template = 'workflow/index.html'
    return render_template(template, **context)

@bp.route('/posts/<int:post_id>/')
def stages(post_id):
    """Workflow stages index page."""
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    # Always redirect to the default stage/substage/step
    return redirect(url_for('workflow.workflow_index', 
        post_id=post_id, 
        stage='planning',
        substage='idea',
        step='initial_concept'
    ))

@bp.route('/posts/<int:post_id>/<stage>/')
def stage(post_id, stage: str):
    """Workflow stage page."""
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    
    context = get_workflow_context(stage)
    if not context:
        abort(404, f"Stage {stage} not found.")
    
    context.update({
        'post': post,
        'post_id': post_id,
        'current_post_id': post_id,
        'all_posts': get_all_posts()
    })
    
    return render_template('workflow/index.html', **context)

# Deprecated API routes - these should be removed after frontend migration
@api_workflow_bp.route('/llm/', methods=['POST'])
@deprecated_endpoint(message="This endpoint is deprecated. Use /api/workflow/posts/<post_id>/<stage>/<substage>/llm instead.")
def deprecated_llm():
    """Deprecated LLM endpoint."""
    return jsonify({'error': 'This endpoint is deprecated'}), 410

@api_workflow_bp.route('/run_llm/', methods=['POST'])
@deprecated_endpoint(message="This endpoint is deprecated. Use /api/workflow/posts/<post_id>/<stage>/<substage>/llm instead.")
def deprecated_run_llm():
    """Deprecated run LLM endpoint."""
    return jsonify({'error': 'This endpoint is deprecated'}), 410

@bp.route('/api/workflow/titles/order', methods=['POST'])
@deprecated_endpoint(message="This endpoint is deprecated. Use /api/workflow/posts/<post_id>/title_order instead.")
def api_update_title_order():
    """Deprecated title order endpoint."""
    return jsonify({'error': 'This endpoint is deprecated'}), 410

@bp.route('/api/field_mappings/', methods=['GET'])
@deprecated_endpoint(message="This endpoint is deprecated. Use /api/workflow/steps/<step_id>/field_mappings instead.")
def get_field_mappings_deprecated():
    """Get field mappings for a step (deprecated)."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT field_name, order_index
                FROM field_mapping
                ORDER BY order_index ASC
            """)
            mappings = cur.fetchall()
            return jsonify(mappings)

@bp.route('/api/update_field_mapping/', methods=['POST'])
@deprecated_endpoint(message="This endpoint is deprecated. Use /api/workflow/steps/<step_id>/field_mappings instead.")
def update_field_mapping_deprecated():
    """Update field mapping for a step (deprecated)."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Clear existing mappings
            cur.execute("DELETE FROM field_mapping")
            
            # Insert new mappings
            for mapping in data:
                cur.execute("""
                    INSERT INTO field_mapping (field_name, order_index)
                    VALUES (%s, %s)
                """, (mapping['field_name'], mapping['order_index']))
            conn.commit()
            return jsonify({'success': True})

@bp.route('/api/prompts/', methods=['GET'])
@deprecated_endpoint(message="This endpoint is deprecated. Use /api/workflow/prompts instead.")
def get_prompts_deprecated():
    """Get prompts for a step (deprecated)."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, content, type
                FROM prompt_template
                ORDER BY name ASC
            """)
            prompts = cur.fetchall()
            return jsonify(prompts)

@bp.route('/api/step_prompts/<int:post_id>/<int:step_id>', methods=['GET'])
@deprecated_endpoint(message="This endpoint is deprecated. Use /api/workflow/steps/<step_id>/prompts/<post_id> instead.")
def get_step_prompts_deprecated(post_id, step_id):
    """Get prompts for a specific step and post (deprecated)."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT sp.id, sp.prompt_id, sp.content, pt.name, pt.type
                FROM step_prompt sp
                JOIN prompt_template pt ON sp.prompt_id = pt.id
                WHERE sp.post_id = %s AND sp.step_id = %s
                ORDER BY sp.id ASC
            """, (post_id, step_id))
            prompts = cur.fetchall()
            return jsonify(prompts)

@bp.route('/api/step_prompts/<int:post_id>/<int:step_id>', methods=['POST'])
@deprecated_endpoint(message="This endpoint is deprecated. Use /api/workflow/steps/<step_id>/prompts/<post_id> instead.")
def save_step_prompts_deprecated(post_id, step_id):
    """Save prompts for a specific step and post (deprecated)."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Clear existing prompts for this step and post
            cur.execute("""
                DELETE FROM step_prompt
                WHERE post_id = %s AND step_id = %s
            """, (post_id, step_id))
            
            # Insert new prompts
            for prompt in data:
                cur.execute("""
                    INSERT INTO step_prompt (post_id, step_id, prompt_id, content)
                    VALUES (%s, %s, %s, %s)
                """, (post_id, step_id, prompt['prompt_id'], prompt['content']))
            conn.commit()
            return jsonify({'success': True})

@api_workflow_bp.route('/fields/mappings', methods=['GET'])
def get_field_mappings():
    """Get field mappings for the current stage and substage."""
    stage = request.args.get('stage')
    substage = request.args.get('substage')
    
    if not stage or not substage:
        abort(400, "Missing stage or substage parameter")
    
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # First get the stage and substage IDs
            cur.execute("""
                SELECT wst.id as stage_id, wst.name as stage_name,
                       wsse.id as substage_id, wsse.name as substage_name
                FROM workflow_stage_entity wst
                JOIN workflow_sub_stage_entity wsse ON wsse.stage_id = wst.id
                WHERE wst.name = %s AND wsse.name = %s
            """, (stage, substage))
            stage_info = cur.fetchone()
            
            if not stage_info:
                abort(404, "Stage or substage not found")
            
            # Get field mappings for the stage and substage
            cur.execute("""
                SELECT wfm.id, wfm.field_name, wfm.order_index
                FROM workflow_field_mapping wfm
                WHERE wfm.stage_id = %s AND wfm.substage_id = %s
                ORDER BY wfm.order_index
            """, (stage_info['stage_id'], stage_info['substage_id']))
            mappings = cur.fetchall()
            
            # Convert to response format
            result = []
            for mapping in mappings:
                result.append({
                    'id': mapping['id'],
                    'field_name': mapping['field_name'],
                    'order_index': mapping['order_index'],
                    'stage_id': stage_info['stage_id'],
                    'stage_name': stage_info['stage_name'],
                    'substage_id': stage_info['substage_id'],
                    'substage_name': stage_info['substage_name']
                })
            
            return jsonify(result)

@api_workflow_bp.route('/fields/mappings', methods=['POST'])
def update_field_mapping():
    """Update field mapping order and associations."""
    data = request.get_json()
    if not data or not all(key in data for key in ['field_name', 'stage_id', 'substage_id', 'order_index']):
        abort(400, "Missing required fields")
    
    print(f"[DEBUG] Field mapping request: {data}")
    
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # First, delete any existing mapping for this specific order_index in this stage/substage
            cur.execute("""
                DELETE FROM workflow_field_mapping
                WHERE stage_id = %s AND substage_id = %s AND order_index = %s
            """, (data['stage_id'], data['substage_id'], data['order_index']))
            
            deleted_count = cur.rowcount
            print(f"[DEBUG] Deleted {deleted_count} rows for order_index {data['order_index']}")
            
            # Also delete any existing mapping for this field_name in this stage/substage (to avoid duplicates)
            cur.execute("""
                DELETE FROM workflow_field_mapping
                WHERE stage_id = %s AND substage_id = %s AND field_name = %s
            """, (data['stage_id'], data['substage_id'], data['field_name']))
            
            deleted_count2 = cur.rowcount
            print(f"[DEBUG] Deleted {deleted_count2} rows for field_name {data['field_name']}")
            
            # Create new mapping
            cur.execute("""
                INSERT INTO workflow_field_mapping (stage_id, substage_id, field_name, order_index)
                VALUES (%s, %s, %s, %s)
            """, (data['stage_id'], data['substage_id'], data['field_name'], data['order_index']))
            
            print(f"[DEBUG] Inserted new mapping for {data['field_name']} at order_index {data['order_index']}")
            
            conn.commit()
            return jsonify({'status': 'success'})

@bp.route('/api/workflow/prompts/<prompt_type>', methods=['GET'])
def get_prompts(prompt_type):
    """Get prompts of a specific type (system or task)."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT id, name, prompt_text as content, 'system' as type
                FROM llm_prompt
                WHERE system_prompt IS NOT NULL
                ORDER BY name
            """)
            prompts = cur.fetchall()
            
            return jsonify([dict(prompt) for prompt in prompts])

@bp.route('/api/workflow/steps/<int:step_id>/prompts', methods=['GET'])
def get_step_prompts(step_id):
    """Get prompts for a specific step."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT 
                    wsp.system_prompt_id,
                    wsp.task_prompt_id,
                    sys_prompt.name as system_prompt_name,
                    sys_prompt.system_prompt as system_prompt_content,
                    task_prompt.name as task_prompt_name,
                    task_prompt.prompt_text as task_prompt_content
                FROM workflow_step_prompt wsp
                LEFT JOIN llm_prompt sys_prompt ON wsp.system_prompt_id = sys_prompt.id
                LEFT JOIN llm_prompt task_prompt ON wsp.task_prompt_id = task_prompt.id
                WHERE wsp.step_id = %s
            """, (step_id,))
            result = cur.fetchone()
            
            if result:
                return jsonify({
                    'system_prompt_id': result['system_prompt_id'],
                    'system_prompt_name': result['system_prompt_name'],
                    'system_prompt_content': result['system_prompt_content'],
                    'task_prompt_id': result['task_prompt_id'],
                    'task_prompt_name': result['task_prompt_name'],
                    'task_prompt_content': result['task_prompt_content']
                })
            else:
                return jsonify({})

@bp.route('/api/workflow/steps/<int:step_id>/prompts', methods=['POST'])
def save_step_prompts(step_id):
    """Save prompts for a specific step."""
    data = request.get_json()
    if not data or not all(key in data for key in ['system_prompt_id', 'task_prompt_id']):
        abort(400, "Missing required fields")
    
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Delete existing prompts for this step
            cur.execute("""
                DELETE FROM workflow_step_prompt
                WHERE step_id = %s
            """, (step_id,))
            
            # Insert new prompts
            cur.execute("""
                INSERT INTO workflow_step_prompt (step_id, system_prompt_id, task_prompt_id)
                VALUES (%s, %s, %s)
            """, (step_id, data['system_prompt_id'], data['task_prompt_id']))
            
            conn.commit()
            return jsonify({'status': 'success'})

@api_workflow_bp.route('/prompts', methods=['GET'])
def get_prompts_redirect():
    """Redirect /prompts to /prompts/all for backward compatibility."""
    return redirect('/api/workflow/prompts/all')

@api_workflow_bp.route('/prompts/all', methods=['GET'])
def get_all_prompts():
    """Get all prompts."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT id, name, 
                       COALESCE(system_prompt, prompt_text) as prompt_text,
                       CASE 
                           WHEN system_prompt IS NOT NULL AND system_prompt != ''
                           THEN 'system' 
                           ELSE 'task' 
                       END as type
                FROM llm_prompt
                ORDER BY name
            """)
            prompts = cur.fetchall()
            
            return jsonify([dict(prompt) for prompt in prompts])

@api_workflow_bp.route('/posts/<int:post_id>/development', methods=['GET'])
def get_post_development(post_id):
    """Get all development fields for a post."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get column names from post_development table
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'post_development' 
                AND column_name NOT IN ('id', 'post_id')
            """)
            columns = [row[0] for row in cur.fetchall()]
            
            # Get field values for the post
            if columns:
                column_list = ', '.join(columns)
                cur.execute(f"""
                    SELECT {column_list}
                    FROM post_development
                    WHERE post_id = %s
                """, (post_id,))
                row = cur.fetchone()
                if row:
                    return jsonify({col: row[col] for col in columns})
    return jsonify({})

@api_workflow_bp.route('/steps/<int:step_id>/prompts', methods=['GET'])
def get_step_prompts(step_id):
    """Get prompts for a specific step."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT 
                    wsp.system_prompt_id,
                    wsp.task_prompt_id,
                    sys_prompt.name as system_prompt_name,
                    sys_prompt.system_prompt as system_prompt_content,
                    task_prompt.name as task_prompt_name,
                    task_prompt.prompt_text as task_prompt_content
                FROM workflow_step_prompt wsp
                LEFT JOIN llm_prompt sys_prompt ON wsp.system_prompt_id = sys_prompt.id
                LEFT JOIN llm_prompt task_prompt ON wsp.task_prompt_id = task_prompt.id
                WHERE wsp.step_id = %s
            """, (step_id,))
            result = cur.fetchone()
            
            if result:
                return jsonify({
                    'system_prompt_id': result['system_prompt_id'],
                    'system_prompt_name': result['system_prompt_name'],
                    'system_prompt_content': result['system_prompt_content'],
                    'task_prompt_id': result['task_prompt_id'],
                    'task_prompt_name': result['task_prompt_name'],
                    'task_prompt_content': result['task_prompt_content']
                })
            else:
                return jsonify({})

@api_workflow_bp.route('/steps/<int:step_id>/prompts', methods=['POST'])
def save_step_prompts(step_id):
    """Save prompts for a specific step."""
    data = request.get_json()
    if not data or not all(key in data for key in ['system_prompt_id', 'task_prompt_id']):
        abort(400, "Missing required fields")
    
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Delete existing prompts for this step
            cur.execute("""
                DELETE FROM workflow_step_prompt
                WHERE step_id = %s
            """, (step_id,))
            
            # Insert new prompts
            cur.execute("""
                INSERT INTO workflow_step_prompt (step_id, system_prompt_id, task_prompt_id)
                VALUES (%s, %s, %s)
            """, (step_id, data['system_prompt_id'], data['task_prompt_id']))
            
            conn.commit()
            return jsonify({'status': 'success'})

@api_workflow_bp.route('/fields/available', methods=['GET'])
def get_available_fields():
    """Get all available fields organized by stage/substage/step."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get all fields with their stage/substage/step context
            cur.execute("""
                WITH field_mappings AS (
                    SELECT DISTINCT 
                        wse.id as step_id,
                        wse.name as step_name,
                        wse.step_order,
                        wsse.id as substage_id,
                        wsse.name as substage_name,
                        wsse.sub_stage_order,
                        wst.id as stage_id,
                        wst.name as stage_name,
                        wst.stage_order,
                        fm->>'field_name' as field_name,
                        (fm->>'order_index')::int as order_index
                    FROM workflow_step_entity wse
                    JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                    JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id,
                    jsonb_array_elements(CASE 
                        WHEN wse.config->>'field_mapping' IS NOT NULL 
                        THEN wse.config->'field_mapping' 
                        ELSE '[]'::jsonb 
                    END) as fm
                    WHERE fm->>'field_name' IS NOT NULL
                )
                SELECT 
                    field_name,
                    json_agg(
                        json_build_object(
                            'step_id', step_id,
                            'step_name', step_name,
                            'step_order', step_order,
                            'substage_id', substage_id,
                            'substage_name', substage_name,
                            'sub_stage_order', sub_stage_order,
                            'stage_id', stage_id,
                            'stage_name', stage_name,
                            'stage_order', stage_order,
                            'order_index', order_index
                        ) ORDER BY stage_order, sub_stage_order, step_order, order_index
                    ) as mappings
                FROM field_mappings
                GROUP BY field_name
                ORDER BY (
                    SELECT MIN(stage_order * 10000 + sub_stage_order * 100 + step_order * 10 + order_index)
                    FROM field_mappings fm2
                    WHERE fm2.field_name = field_mappings.field_name
                )
            """)
            fields = [dict(row) for row in cur.fetchall()]
            
            # Get stage/substage/step hierarchy for grouping
            cur.execute("""
                SELECT 
                    wst.id as stage_id,
                    wst.name as stage_name,
                    wst.stage_order,
                    wsse.id as substage_id,
                    wsse.name as substage_name,
                    wsse.sub_stage_order,
                    wse.id as step_id,
                    wse.name as step_name,
                    wse.step_order
                FROM workflow_stage_entity wst
                JOIN workflow_sub_stage_entity wsse ON wsse.stage_id = wst.id
                JOIN workflow_step_entity wse ON wse.sub_stage_id = wsse.id
                ORDER BY wst.stage_order, wsse.sub_stage_order, wse.step_order
            """)
            hierarchy = [dict(row) for row in cur.fetchall()]
            
            # Build groups array
            result = {
                'fields': fields,
                'groups': []
            }
            
            current_stage = None
            current_substage = None
            for row in hierarchy:
                if current_stage is None or current_stage['id'] != row['stage_id']:
                    current_stage = {
                        'id': row['stage_id'],
                        'name': row['stage_name'],
                        'order': row['stage_order'],
                        'substages': []
                    }
                    result['groups'].append(current_stage)
                    current_substage = None
                
                if current_substage is None or current_substage['id'] != row['substage_id']:
                    current_substage = {
                        'id': row['substage_id'],
                        'name': row['substage_name'],
                        'order': row['sub_stage_order'],
                        'steps': []
                    }
                    current_stage['substages'].append(current_substage)
                
                current_substage['steps'].append({
                    'id': row['step_id'],
                    'name': row['step_name'],
                    'order': row['step_order']
                })
            
            return jsonify(result) 

@api_workflow_bp.route('/steps/<int:step_id>/llm_settings', methods=['POST'])
def update_llm_settings(step_id):
    """Update LLM settings for a workflow step (isolated)."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    # Validate fields
    model = data.get('model')
    temperature = data.get('temperature')
    max_tokens = data.get('max_tokens')
    top_p = data.get('top_p')
    frequency_penalty = data.get('frequency_penalty')
    presence_penalty = data.get('presence_penalty')
    timeout = data.get('timeout')

    errors = {}
    if not isinstance(model, str) or not model.strip():
        errors['model'] = 'Model must be a non-empty string.'
    for field, value, minv, maxv, typ in [
        ('temperature', temperature, 0.0, 1.0, float),
        ('top_p', top_p, 0.0, 1.0, float),
        ('frequency_penalty', frequency_penalty, 0.0, 1.0, float),
        ('presence_penalty', presence_penalty, 0.0, 1.0, float)
    ]:
        try:
            v = typ(value)
            if not (minv <= v <= maxv):
                errors[field] = f'{field} must be between {minv} and {maxv}.'
        except Exception:
            errors[field] = f'{field} must be a {typ.__name__}.'
    try:
        max_tokens = int(max_tokens)
        if not (1 <= max_tokens <= 32768):
            errors['max_tokens'] = 'max_tokens must be between 1 and 32768.'
    except Exception:
        errors['max_tokens'] = 'max_tokens must be an integer.'
    try:
        timeout = int(timeout)
        if not (1 <= timeout <= 600):
            errors['timeout'] = 'timeout must be between 1 and 600 seconds.'
    except Exception:
        errors['timeout'] = 'timeout must be an integer.'
    if errors:
        return jsonify({'success': False, 'errors': errors}), 400

    # Update DB (only LLM settings)
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT config FROM workflow_step_entity WHERE id = %s', (step_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({'success': False, 'error': 'Step not found'}), 404
            import json
            config = row['config'] or {}
            if isinstance(config, str):
                config = json.loads(config)
            if 'settings' not in config:
                config['settings'] = {}
            if 'llm' not in config['settings']:
                config['settings']['llm'] = {}
            config['settings']['llm'].update({
                'model': model,
                'timeout': timeout,
                'parameters': {
                    'temperature': float(temperature),
                    'max_tokens': int(max_tokens),
                    'top_p': float(top_p),
                    'frequency_penalty': float(frequency_penalty),
                    'presence_penalty': float(presence_penalty)
                }
            })
            cur.execute('UPDATE workflow_step_entity SET config = %s WHERE id = %s', (json.dumps(config), step_id))
            conn.commit()
    return jsonify({'success': True}) 