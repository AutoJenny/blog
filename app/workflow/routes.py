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
from app.llm.services import execute_llm_request
import psycopg2.extras
from flask import current_app

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
            cur.execute("SELECT id, title FROM post WHERE status != 'deleted' ORDER BY updated_at DESC, id DESC")
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
    
    # If stage and substage are provided but no step, redirect to first step
    if stage and substage and not request.args.get('step'):
        # Get all stages data
        stages = get_workflow_stages_from_db()
        
        # Convert names to lowercase for URL matching
        stage_lower = stage.lower()
        substage_lower = substage.lower()
        
        # Find matching stage/substage (case-insensitive)
        for db_stage, substages in stages.items():
            if db_stage.lower() == stage_lower:
                for db_substage, steps in substages.items():
                    if db_substage.lower() == substage_lower:
                        # Get first step (they're ordered by step_order)
                        first_step = steps[0]
                        # Convert step name to URL format (lowercase with underscores)
                        step_url = first_step.lower().replace(' ', '_')
                        # Redirect to the first step using query parameter format
                        return redirect(f"/workflow/posts/{post_id}/{stage}/{substage}?step={step_url}")
    
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
    step_id = None
    if stage and substage:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Get step configuration using ILIKE for case-insensitive match
                cur.execute("""
                    SELECT wse.config, wse.name as step_name, wse.id as step_id
                    FROM workflow_step_entity wse
                    JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                    JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                    WHERE wst.name ILIKE %s AND wsse.name ILIKE %s
                    AND wse.name ILIKE %s
                """, (stage, substage, display_step))
                result = cur.fetchone()
                if result:
                    config_json, step_name, step_id = result['config'], result['step_name'], result['step_id']
                    # Convert DB step name to URL format for consistency
                    url_step_name = step_name.lower().replace(' ', '_')
                    if config_json:
                        # Update step configuration with stored config
                        step_config.update(config_json)
                        
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
        'output_values': output_values,
        'step_id': step_id  # Add step_id to the context
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
    """Redirect to first substage of the stage."""
    # Get all stages data
    stages = get_workflow_stages_from_db()
    
    # Convert stage name to lowercase for URL matching
    stage_lower = stage.lower()
    
    # Find matching stage (case-insensitive)
    for db_stage, substages in stages.items():
        if db_stage.lower() == stage_lower:
            # Get first substage (they're ordered by sub_stage_order)
            first_substage = next(iter(substages))
            # Redirect to the first substage
            return redirect(url_for('workflow.substage', 
                post_id=post_id,
                stage=stage,
                substage=first_substage))
    
    # If stage not found, 404
    abort(404, f"Stage {stage} not found")

@workflow.route('/posts/<int:post_id>/<stage>/<substage>/')
def substage(post_id, stage: str, substage: str):
    """Redirect to first step of the substage."""
    # Get all stages data
    stages = get_workflow_stages_from_db()
    
    # Convert names to lowercase for URL matching
    stage_lower = stage.lower()
    substage_lower = substage.lower()
    
    # Find matching stage/substage (case-insensitive)
    for db_stage, substages in stages.items():
        if db_stage.lower() == stage_lower:
            for db_substage, steps in substages.items():
                if db_substage.lower() == substage_lower:
                    # Get first step (they're ordered by step_order)
                    first_step = steps[0]
                    # Convert step name to URL format (lowercase with underscores)
                    step_url = first_step.lower().replace(' ', '_')
                    # Redirect to the first step using query parameter format
                    return redirect(f"/workflow/posts/{post_id}/{stage}/{substage}?step={step_url}")
    
    # If stage/substage not found, 404
    abort(404, f"Stage {stage} or substage {substage} not found")

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
            # Get all available fields from post_development
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'post_development'
                AND column_name NOT IN ('id', 'post_id', 'updated_at')
                ORDER BY ordinal_position
            """)
            all_fields = [row['column_name'] for row in cur.fetchall()]
            
            # Get workflow structure for grouping
            cur.execute("""
                SELECT 
                    wst.name as stage_name,
                    wsse.name as substage_name,
                    wse.name as step_name,
                    wse.config
                FROM workflow_stage_entity wst
                JOIN workflow_sub_stage_entity wsse ON wsse.stage_id = wst.id
                JOIN workflow_step_entity wse ON wse.sub_stage_id = wsse.id
                ORDER BY wst.id, wsse.id, wse.id
            """)
            workflow_structure = cur.fetchall()
            
            # Initialize result structure with all stages/substages
            result = {}
            for row in workflow_structure:
                stage = row['stage_name'].lower()
                substage = row['substage_name'].lower()
                if stage not in result:
                    result[stage] = {}
                if substage not in result[stage]:
                    result[stage][substage] = {
                        'inputs': [],
                        'outputs': []
                    }
            
            # Get current step's config
            current_stage = request.args.get('stage', 'planning')
            current_substage = request.args.get('substage', 'idea')
            current_step = request.args.get('step', 'Initial')
            
            # Add all available fields to the current stage/substage
            result[current_stage][current_substage]['inputs'] = [
                {
                    'field_name': field,
                    'display_name': field.replace('_', ' ').title()
                }
                for field in all_fields
            ]
            
            result[current_stage][current_substage]['outputs'] = [
                {
                    'field_name': field,
                    'display_name': field.replace('_', ' ').title()
                }
                for field in all_fields
            ]
            
            return jsonify(result)

@workflow.route('/api/update_field_mapping/', methods=['POST'])
def update_field_mapping():
    """Update a field mapping in the step config."""
    data = request.get_json()
    target_id = data.get('target_id')
    field_name = data.get('field_name')
    section = data.get('section')  # 'inputs' or 'outputs'
    stage = data.get('stage')
    substage = data.get('substage')
    step = data.get('step', 'initial')  # Default to 'initial' if not provided
    
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
                            stage = path_parts[path_parts.index('posts') + 2]
                            substage = path_parts[path_parts.index('posts') + 3]
                        except (ValueError, IndexError):
                            return jsonify({'error': 'Could not determine stage/substage from URL'}), 400
                    else:
                        stage = 'planning'
                        substage = 'idea'

                # Get the current step config
                cur.execute("""
                    SELECT wse.id, wse.config
                    FROM workflow_step_entity wse
                    JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                    JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                    WHERE wst.name ILIKE %s AND wsse.name ILIKE %s
                    AND wse.name ILIKE %s
                """, (stage, substage, step))
                
                result = cur.fetchone()
                if not result:
                    return jsonify({'error': 'Step not found'}), 404
                
                step_id = result['id']
                config = result['config'] or {}
                
                # Ensure the section exists in config
                if section not in config:
                    config[section] = {}
                
                # Update or add the field mapping
                if target_id in config[section]:
                    config[section][target_id]['db_field'] = field_name
                else:
                    config[section][target_id] = {
                        'db_field': field_name,
                        'db_table': 'post_development'
                    }
                
                # Update the step config
                cur.execute("""
                    UPDATE workflow_step_entity 
                    SET config = %s
                    WHERE id = %s
                    RETURNING id
                """, (json.dumps(config), step_id))
                
                conn.commit()
                
                return jsonify({
                    'field_name': field_name,
                    'section': section,
                    'table_name': 'post_development'
                })
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow.route('/posts/<int:post_id>/<stage>/<substage>/<step>')
def workflow_step(post_id, stage, substage, step):
    """Render a workflow step."""
    context = get_step_context(post_id, stage, substage, step)
    if not context:
        abort(404)
    
    return render_template('workflow/steps/planning_step.html', **context)

@workflow.route('/api/v1/workflow/run_llm/', methods=['POST'])
def run_workflow_llm():
    """Execute LLM processing for the current workflow step."""
    data = request.get_json()
    post_id = data.get('post_id')
    stage = data.get('stage')
    substage = data.get('substage')
    step = data.get('step')
    
    current_app.logger.info(f"[Workflow LLM] Processing request for post {post_id}, stage {stage}, substage {substage}, step {step}")
    
    try:
        # Get step configuration
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT wse.config
                    FROM workflow_step_entity wse
                    JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                    JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                    WHERE wst.name ILIKE %s
                    AND wsse.name ILIKE %s
                    AND wse.name ILIKE %s
                """, (stage, substage, step))
                
                step_config = cur.fetchone()
                current_app.logger.info(f"[Workflow LLM] Step config: {step_config}")
                
                if not step_config:
                    current_app.logger.error("[Workflow LLM] No step configuration found")
                    return jsonify({"success": False, "error": "No step configuration found"})
                
                config = step_config[0]
                current_app.logger.info(f"[Workflow LLM] Config: {config}")
                
                # Get input values
                cur.execute("""
                    SELECT idea_seed
                    FROM post_development
                    WHERE post_id = %s
                """, (post_id,))
                
                input_values = cur.fetchone()
                current_app.logger.info(f"[Workflow LLM] Input values: {input_values}")
                
                if not input_values:
                    current_app.logger.error("[Workflow LLM] No input values found")
                    return jsonify({"success": False, "error": "No input values found"})
                
                # Get LLM settings from config
                llm_settings = config.get('settings', {}).get('llm', {})
                prompt = llm_settings.get('task_prompt', '').replace('[data:idea_seed]', input_values['idea_seed'])
                
                # Execute LLM request
                llm_response = execute_llm_request(
                    provider=llm_settings.get('provider', 'ollama'),
                    model=llm_settings.get('model', 'llama3.1:70b'),
                    prompt=prompt,
                    temperature=llm_settings.get('parameters', {}).get('temperature', 0.7),
                    max_tokens=llm_settings.get('parameters', {}).get('max_tokens', 1000),
                    api_endpoint='http://localhost:11434/api/generate'
                )
                current_app.logger.info(f"[Workflow LLM] LLM response: {llm_response}")
                
                if not llm_response:
                    current_app.logger.error("[Workflow LLM] No response from LLM")
                    return jsonify({"success": False, "error": "No response from LLM"})
                
                # Update output field
                cur.execute("""
                    UPDATE post_development
                    SET basic_idea = %s
                    WHERE post_id = %s
                    RETURNING basic_idea
                """, (llm_response, post_id))
                
                updated = cur.fetchone()
                current_app.logger.info(f"[Workflow LLM] Updated value: {updated}")
                
                conn.commit()
                
                return jsonify({
                    "success": True,
                    "result": llm_response
                })
                
    except Exception as e:
        current_app.logger.error(f"[Workflow LLM] Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@workflow.route('/api/prompts/', methods=['GET'])
def get_prompts():
    """Get available prompts filtered by type."""
    prompt_type = request.args.get('prompt_type', 'system')
    
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if prompt_type == 'system':
                cur.execute("""
                    SELECT id, name, prompt_text
                    FROM llm_prompt
                    WHERE prompt_type = 'system'
                    ORDER BY name
                """)
            else:
                cur.execute("""
                    SELECT id, name, prompt_text, stage, substage, step
                    FROM llm_prompt
                    WHERE prompt_type = 'task'
                    ORDER BY stage, substage, step, name
                """)
            prompts = cur.fetchall()
            return jsonify(prompts)

@workflow.route('/api/step_prompts/<int:post_id>/<int:step_id>', methods=['GET'])
def get_step_prompts(post_id, step_id):
    """Get the currently selected prompts for a specific workflow step."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    wsp.system_prompt_id,
                    wsp.task_prompt_id,
                    sp.name as system_prompt_name,
                    sp.prompt_text as system_prompt_text,
                    tp.name as task_prompt_name,
                    tp.prompt_text as task_prompt_text
                FROM workflow_step_prompt wsp
                LEFT JOIN llm_prompt sp ON wsp.system_prompt_id = sp.id
                LEFT JOIN llm_prompt tp ON wsp.task_prompt_id = tp.id
                WHERE wsp.step_id = %s
            """, (step_id,))
            result = cur.fetchone()
            return jsonify(result if result else {})

@workflow.route('/api/step_prompts/<int:post_id>/<int:step_id>', methods=['POST'])
def save_step_prompts(post_id, step_id):
    """Save or update prompt selections for a specific workflow step."""
    data = request.get_json()
    system_prompt_id = data.get('system_prompt_id')
    task_prompt_id = data.get('task_prompt_id')
    
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # First check if a record exists
            cur.execute("""
                SELECT 1 FROM workflow_step_prompt 
                WHERE step_id = %s
            """, (step_id,))
            exists = cur.fetchone() is not None

            if exists:
                # Update only the fields that were provided
                update_fields = []
                params = []
                if system_prompt_id is not None:
                    update_fields.append("system_prompt_id = %s")
                    params.append(system_prompt_id)
                if task_prompt_id is not None:
                    update_fields.append("task_prompt_id = %s")
                    params.append(task_prompt_id)
                
                if update_fields:
                    update_fields.append("updated_at = CURRENT_TIMESTAMP")
                    sql = f"""
                        UPDATE workflow_step_prompt 
                        SET {', '.join(update_fields)}
                        WHERE step_id = %s
                    """
                    params.append(step_id)
                    cur.execute(sql, params)
            else:
                # Insert new record with only the provided fields
                fields = ['step_id']
                values = [step_id]
                if system_prompt_id is not None:
                    fields.append('system_prompt_id')
                    values.append(system_prompt_id)
                if task_prompt_id is not None:
                    fields.append('task_prompt_id')
                    values.append(task_prompt_id)
                
                placeholders = ', '.join(['%s'] * len(values))
                sql = f"""
                    INSERT INTO workflow_step_prompt 
                        ({', '.join(fields)})
                    VALUES ({placeholders})
                """
                cur.execute(sql, values)
            
            conn.commit()
            return jsonify({'status': 'success'}) 