from flask import render_template, redirect, url_for, abort, request, jsonify
from app.workflow import workflow
# DISABLED - DO NOT USE TOXIC DUPLICATE
# from .navigation import navigator

# Use proper nav module instead
from modules.nav.services import get_workflow_context
from app.services.shared import get_workflow_stages_from_db, get_all_posts_from_db
from app.database import get_db_conn
import subprocess
import sys
import json
import os

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
        with conn.cursor() as cur:
            cur.execute("SELECT p.id, pd.idea_seed FROM post p LEFT JOIN post_development pd ON p.id = pd.post_id WHERE p.id = %s", (post_id,))
            return cur.fetchone()

def get_all_posts():
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT p.id, COALESCE(pd.idea_seed, p.title, 'Untitled') AS title FROM post p LEFT JOIN post_development pd ON p.id = pd.post_id WHERE p.status != 'deleted' ORDER BY p.updated_at DESC, p.id DESC")
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

@workflow.route('/')
def index():
    """Workflow index page."""
    all_posts = get_all_posts_from_db()
    if not all_posts:
        abort(404, "No posts found.")
    return redirect(url_for('workflow.stages', post_id=all_posts[0]['id']))

@workflow.route('/posts/<int:post_id>/<stage>/<substage>')
@workflow.route('/posts/<int:post_id>')
def workflow_index(post_id, stage=None, substage=None):
    """Main workflow page."""
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    
    # Get step from query parameters, keeping original format for database lookup
    step = request.args.get('step', 'initial')
    # Convert URL format (lowercase with underscores) to DB format (title case with spaces)
    display_step = step.replace('_', ' ').title()
    
    context = get_workflow_context(stage, substage, display_step)
    
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
    if stage and substage:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Get step configuration using ILIKE for case-insensitive match
                cur.execute("""
                    SELECT wse.config, wse.name as step_name
                    FROM workflow_step_entity wse
                    JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                    JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                    WHERE wst.name ILIKE %s AND wsse.name ILIKE %s
                    AND wse.name ILIKE %s
                """, (stage, substage, display_step))
                result = cur.fetchone()
                if result:
                    config_json, step_name = result['config'], result['step_name']
                    # Convert DB step name to URL format for consistency
                    url_step_name = step_name.lower().replace(' ', '_')
                    if config_json:
                        # Update step configuration with stored config
                        step_config.update(config_json)
    
    # Get field values from post_development
    field_values = get_post_development_fields(post_id)
    
    # Prepare input and output values based on step configuration
    input_values = {}
    output_values = {}
    
    if step_config.get('inputs'):
        for input_id, input_config in step_config['inputs'].items():
            if isinstance(input_config, dict) and 'db_field' in input_config:
                input_values[input_id] = field_values.get(input_config['db_field'], '')
            
    if step_config.get('outputs'):
        for output_id, output_config in step_config['outputs'].items():
            if isinstance(output_config, dict) and 'db_field' in output_config:
                output_values[output_id] = field_values.get(output_config['db_field'], '')
    
    context.update({
        'post': post,
        'post_id': post_id,
        'current_post_id': post_id,
        'all_posts': get_all_posts(),
        'substage_icons': SUBSTAGE_ICONS,
        'current_stage': stage,
        'current_substage': substage,
        'current_step': url_step_name if result else step,  # Use URL format for step name
        'step_config': step_config,
        'input_values': input_values,
        'output_values': output_values
    })
    return render_template('workflow/index.html', **context)

@workflow.route('/posts/<int:post_id>/')
def stages(post_id):
    """Workflow stages index page."""
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    
    # Get workflow context from the nav module
    context = get_workflow_context()
    context.update({
        'post': post,
        'post_id': post_id,
        'current_post_id': post_id,
        'all_posts': get_all_posts(),
        'substage_icons': SUBSTAGE_ICONS,
        'current_stage': None,
        'current_substage': None,
        'current_step': None
    })
    
    return render_template('workflow/index.html', **context)

@workflow.route('/posts/<int:post_id>/<stage>/')
def stage(post_id, stage: str):
    """Stage view page."""
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    
    # Get workflow context from the nav module
    context = get_workflow_context(stage)
    context.update({
        'post': post,
        'post_id': post_id,
        'current_post_id': post_id,
        'all_posts': get_all_posts(),
        'substage_icons': SUBSTAGE_ICONS,
        'current_stage': stage,
        'current_substage': None,
        'current_step': None
    })
    
    return render_template('workflow/index.html', **context)

@workflow.route('/posts/<int:post_id>/<stage>/<substage>/')
def substage(post_id, stage: str, substage: str):
    """Substage view page."""
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    
    # Get workflow context from the nav module
    context = get_workflow_context(stage, substage)
    if not context:
        abort(404, f"Invalid path: {stage}/{substage}")
    
    context.update({
        'post': post,
        'post_id': post_id,
        'current_post_id': post_id,
        'all_posts': get_all_posts(),
        'substage_icons': SUBSTAGE_ICONS,
        'current_stage': stage,
        'current_substage': substage,
        'current_step': None
    })
    
    return render_template('workflow/index.html', **context)

@workflow.route('/posts/<int:post_id>/<stage>/<substage>/<step>/')
def step(post_id, stage: str, substage: str, step: str):
    """Handle old URL format and redirect to new format."""
    # Get workflow context to validate the path
    context = get_workflow_context(stage, substage, step)
    if not context:
        abort(404, f"Invalid path: {stage}/{substage}/{step}")
    return redirect(url_for('workflow.workflow_index', post_id=post_id, stage=stage, substage=substage))

@workflow.route('/api/v1/workflow/llm/', methods=['POST'])
def api_run_llm():
    data = request.get_json()
    post_id = data.get('post_id')
    stage_name = data.get('stage_name')
    substage_name = data.get('substage_name')
    step_name = data.get('step_name')
    if not all([post_id, stage_name, substage_name, step_name]):
        return jsonify({'error': 'Missing required parameters'}), 400
    try:
        # Run the backend script
        result = subprocess.run(
            [
                sys.executable,
                'app/workflow/scripts/llm_processor.py',
                str(post_id),
                stage_name,
                substage_name,
                step_name
            ],
            capture_output=True,
            text=True,
            cwd='/Users/nickfiddes/Code/projects/blog'
        )
        if result.returncode == 0:
            return jsonify({'status': 'success', 'output': result.stdout})
        else:
            return jsonify({'status': 'error', 'error': result.stderr}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@workflow.route('/api/v1/workflow/title_order/', methods=['POST'])
def api_update_title_order():
    data = request.get_json()
    post_id = data.get('post_id')
    titles = data.get('titles')
    if not all([post_id, titles]):
        return jsonify({'error': 'Missing required parameters'}), 400
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE post_development SET title_order = %s WHERE post_id = %s", (json.dumps(titles), post_id))
                conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@workflow.route('/api/field_mappings/', methods=['GET'])
def get_field_mappings():
    """Get all field mappings."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT wfm.field_name, wst.name as stage, wsse.name as substage
                FROM workflow_field_mapping wfm
                JOIN workflow_sub_stage_entity wsse ON wfm.substage_id = wsse.id
                JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                ORDER BY wst.name, wsse.name, wfm.field_name
            """)
            mappings = cur.fetchall()
            
            # Group by stage and substage
            result = {}
            for mapping in mappings:
                stage = mapping['stage']
                substage = mapping['substage']
                if stage not in result:
                    result[stage] = {}
                if substage not in result[stage]:
                    result[stage][substage] = []
                result[stage][substage].append({
                    'field_name': mapping['field_name'],
                    'display_name': mapping['field_name']  # Use field_name as display_name
                })
            
            return jsonify(result)

@workflow.route('/api/update_field_mapping/', methods=['POST'])
def update_field_mapping():
    """Update a field mapping."""
    data = request.get_json()
    target_id = data.get('target_id')
    field_name = data.get('field_name')
    section = data.get('section')
    stage = data.get('stage')
    substage = data.get('substage')
    
    if not all([target_id, field_name, section]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # If stage/substage not provided in request, try to get from referrer
                if not stage or not substage:
                    if request.referrer:
                        path_parts = request.referrer.split('/')
                        try:
                            post_id = path_parts[path_parts.index('posts') + 1]
                            stage = path_parts[path_parts.index('posts') + 2]
                            substage = path_parts[path_parts.index('posts') + 3] if len(path_parts) > path_parts.index('posts') + 3 else None
                        except (ValueError, IndexError):
                            return jsonify({'error': 'Could not determine stage/substage from URL'}), 400
                    else:
                        # Default to 'planning/idea' if no stage/substage provided
                        stage = 'planning'
                        substage = 'idea'

                # Get stage_id and substage_id
                cur.execute("""
                    SELECT wst.id as stage_id, wsse.id as substage_id
                    FROM workflow_stage_entity wst
                    JOIN workflow_sub_stage_entity wsse ON wsse.stage_id = wst.id
                    WHERE wst.name = %s AND wsse.name = %s
                """, (stage, substage))
                ids = cur.fetchone()
                if not ids:
                    return jsonify({'error': 'Stage or substage not found'}), 404
                
                stage_id = ids['stage_id']
                substage_id = ids['substage_id']

                # Get next order_index for this substage
                cur.execute("""
                    SELECT MAX(order_index) as max_order
                    FROM workflow_field_mapping 
                    WHERE substage_id = %s
                """, (substage_id,))
                result = cur.fetchone()
                order_index = (result['max_order'] or 0) + 1

                # Upsert the field mapping
                cur.execute("""
                    INSERT INTO workflow_field_mapping 
                        (field_name, stage_id, substage_id, order_index)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (field_name, substage_id)
                    DO UPDATE SET stage_id = EXCLUDED.stage_id
                    RETURNING field_name
                """, (field_name, stage_id, substage_id, order_index))
                conn.commit()
                
                mapping = cur.fetchone()
                if not mapping:
                    return jsonify({'error': 'Failed to update field mapping'}), 500
                
                return jsonify({
                    'field_name': mapping['field_name'],
                    'table_name': 'post_development'  # Hardcode since all fields are in post_development
                })
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500 