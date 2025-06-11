from flask import render_template, redirect, url_for, abort, request, jsonify
from app.workflow import workflow
from .navigation import navigator
from app.db import get_db_conn
import json
import os
import subprocess
import sys

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
    # First try loading from the config file
    config_path = os.path.join(os.path.dirname(__file__), 'config', f'{stage_name}_steps.json')
    print(f"DEBUG: Loading config from {config_path}")
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            result = config.get(stage_name, {}).get(substage_name, {}).get(step_name, {})
            print(f"DEBUG: Config for {stage_name}/{substage_name}/{step_name}: {result}")
            
            # Check for a custom prompt file
            prompt_file = get_prompt_file_path(step_name, substage_name, stage_name)
            if os.path.exists(prompt_file):
                try:
                    with open(prompt_file, 'r') as f:
                        prompt_config = json.load(f)
                        if 'prompt' in prompt_config:
                            # Update the prompt in the config
                            if 'settings' in result and 'llm' in result['settings']:
                                result['settings']['llm']['task_prompt'] = prompt_config['prompt']
                            else:
                                result['prompt'] = {'template': prompt_config['prompt']}
                            print(f"DEBUG: Updated config with custom prompt: {result}")
                except Exception as e:
                    print(f"DEBUG: Error reading prompt file: {e}")
            
            return result
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"DEBUG: Error loading config: {e}")
        return {}

@workflow.route('/')
def index():
    latest = get_latest_post()
    if not latest:
        abort(404, "No posts found.")
    return redirect(url_for('workflow.stages', post_id=latest['id']))

@workflow.route('/<int:post_id>/')
def stages(post_id):
    navigator.load_navigation()
    stages = navigator.stages
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    all_posts = get_all_posts()
    return render_template('workflow/index.html', stages=stages, post=post, post_id=post_id, all_posts=all_posts, current_stage=None, current_substage=None, current_step=None)

@workflow.route('/<int:post_id>/<stage_name>/')
def stage(post_id, stage_name: str):
    navigator.load_navigation()
    stage = next((s for s in navigator.stages if s['name'] == stage_name), None)
    if not stage:
        abort(404, f"Stage '{stage_name}' not found.")
    substages = navigator.get_substages_for_stage(stage['id'])
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    all_posts = get_all_posts()
    return render_template('workflow/stage.html', stage=stage, substages=substages, post=post, post_id=post_id, all_posts=all_posts, current_stage=stage_name, current_substage=None, current_step=None)

@workflow.route('/<int:post_id>/<stage_name>/<substage_name>/')
def substage(post_id, stage_name: str, substage_name: str):
    navigator.load_navigation()
    stage = next((s for s in navigator.stages if s['name'] == stage_name), None)
    if not stage:
        abort(404, f"Stage '{stage_name}' not found.")
    substages = navigator.get_substages_for_stage(stage['id'])
    substage = next((s for s in substages if s['name'] == substage_name), None)
    if not substage:
        abort(404, f"Substage '{substage_name}' not found in stage '{stage_name}'.")
    steps = navigator.get_steps_for_substage(substage['id'])
    if not steps:
        abort(404, f"No steps found for substage '{substage_name}'.")
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    all_posts = get_all_posts()
    # Redirect to first step
    return redirect(url_for('workflow.step', post_id=post_id, stage_name=stage_name, substage_name=substage_name, step_name=steps[0]['name']))

@workflow.route('/<int:post_id>/<stage_name>/<substage_name>/<step_name>/')
def step(post_id, stage_name: str, substage_name: str, step_name: str):
    print(f"DEBUG: step route called with post_id={post_id}, stage_name={stage_name}, substage_name={substage_name}, step_name={step_name}")
    navigator.load_navigation()
    stage = next((s for s in navigator.stages if s['name'] == stage_name), None)
    if not stage:
        abort(404, f"Stage '{stage_name}' not found.")
    substages = navigator.get_substages_for_stage(stage['id'])
    substage = next((s for s in substages if s['name'] == substage_name), None)
    if not substage:
        abort(404, f"Substage '{substage_name}' not found in stage '{stage_name}'.")
    steps = navigator.get_steps_for_substage(substage['id'])
    step = next((s for s in steps if s['name'] == step_name), None)
    if not step:
        abort(404, f"Step '{step_name}' not found in substage '{substage_name}'.")
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    all_posts = get_all_posts()

    # Load step configuration
    step_config = load_step_config(stage_name, substage_name, step_name)
    
    # Load input and output values from database
    input_values = {}
    output_values = {}
    if step_config:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Load input values
                if 'inputs' in step_config:
                    for input_id, input_config in step_config['inputs'].items():
                        cur.execute(f"SELECT {input_config['db_field']} FROM {input_config['db_table']} WHERE post_id = %s", (post_id,))
                        result = cur.fetchone()
                        if result is not None and input_config['db_field'] in result and result[input_config['db_field']] is not None:
                            input_values[input_id] = result[input_config['db_field']]
                
                # Load output values
                if 'outputs' in step_config:
                    for output_id, output_config in step_config['outputs'].items():
                        cur.execute(f"SELECT {output_config['db_field']} FROM {output_config['db_table']} WHERE post_id = %s", (post_id,))
                        result = cur.fetchone()
                        if result is not None and output_config['db_field'] in result and result[output_config['db_field']] is not None:
                            output_values[output_id] = result[output_config['db_field']]

    # Debug print statements
    print(f"DEBUG: step_config for {stage_name}/{substage_name}/{step_name}: {step_config}")
    print(f"DEBUG: input_values for post_id={post_id}: {input_values}")
    print(f"DEBUG: output_values for post_id={post_id}: {output_values}")

    # Parse output as JSON array if possible (for outputs like provisional_title)
    output_titles = None
    if 'outputs' in step_config:
        for output_id in step_config['outputs']:
            val = output_values.get(output_id)
            if val and isinstance(val, str) and val.strip().startswith('[') and val.strip().endswith(']'):
                try:
                    output_titles = json.loads(val)
                except Exception:
                    output_titles = None

    return render_template(
        f'workflow/steps/{step_name}.html',
        stage=stage,
        substage=substage,
        step=step,
        post=post,
        post_id=post_id,
        all_posts=all_posts,
        current_stage=stage_name,
        current_substage=substage_name,
        current_step=step_name,
        step_config=step_config,
        input_values=input_values,
        output_values=output_values,
        output_titles=output_titles
    )

# Redirect old URLs to new format with post_id
def _redirect_to_new(post_id, *args):
    return redirect(url_for(request.endpoint, post_id=post_id, **request.view_args))

@workflow.route('/<stage_name>/<substage_name>/<step_name>/')
def legacy_step(stage_name, substage_name, step_name):
    latest = get_latest_post()
    if not latest:
        abort(404, "No posts found.")
    return redirect(url_for('workflow.step', post_id=latest['id'], stage_name=stage_name, substage_name=substage_name, step_name=step_name))

@workflow.route('/api/run_llm/', methods=['POST'])
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

@workflow.route('/<int:post_id>/<stage_name>/<substage_name>/test/')
def test_step(post_id, stage_name: str, substage_name: str):
    return f"Test route: post_id={post_id}, stage_name={stage_name}, substage_name={substage_name}"

# Ensure prompts directory exists
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'prompts')
os.makedirs(PROMPTS_DIR, exist_ok=True)

def get_prompt_file_path(step_name, substage_name, stage_name):
    """Get the path to the prompt file for a given step."""
    return os.path.join(PROMPTS_DIR, f"{stage_name}_{substage_name}_{step_name}.json")

@workflow.route('/api/update_prompt/', methods=['POST'])
def update_prompt():
    try:
        # Log raw request data
        print("DEBUG: Raw request data:", request.get_data())
        print("DEBUG: Request headers:", dict(request.headers))
        
        data = request.get_json()
        if not data:
            print("DEBUG: No JSON data received")
            return jsonify({'success': False, 'error': 'No JSON data received'}), 400
            
        print(f"DEBUG: Received data: {data}")
        
        # Validate required fields
        required_fields = ['post_id', 'step_name', 'substage_name', 'stage_name', 'prompt']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            print(f"DEBUG: Missing fields: {missing_fields}")
            return jsonify({'success': False, 'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        post_id = data.get('post_id')
        step_name = data.get('step_name')
        substage_name = data.get('substage_name')
        stage_name = data.get('stage_name')
        new_prompt = data.get('prompt')

        print(f"DEBUG: Parsed values - post_id: {post_id}, step: {step_name}, substage: {substage_name}, stage: {stage_name}")
        print(f"DEBUG: New prompt: {new_prompt}")

        # Get the prompt file path
        prompt_file = get_prompt_file_path(step_name, substage_name, stage_name)
        print(f"DEBUG: Prompt file path: {prompt_file}")

        # Read existing config if it exists
        current_config = {}
        if os.path.exists(prompt_file):
            try:
                with open(prompt_file, 'r') as f:
                    current_config = json.load(f)
                print(f"DEBUG: Current config: {current_config}")
            except Exception as e:
                print(f"DEBUG: Error reading existing config: {str(e)}")
                current_config = {}

        # Update the config
        current_config['prompt'] = new_prompt
        print(f"DEBUG: New config: {current_config}")

        # Write the updated config
        try:
            with open(prompt_file, 'w') as f:
                json.dump(current_config, f, indent=2)
            print("DEBUG: Config written successfully")
            return jsonify({'success': True})
        except Exception as write_error:
            print(f"DEBUG: Write error: {str(write_error)}")
            import traceback
            print(f"DEBUG: Write error traceback: {traceback.format_exc()}")
            return jsonify({'success': False, 'error': f'Error writing config: {str(write_error)}'}), 500

    except Exception as e:
        print(f"DEBUG: General error: {str(e)}")
        import traceback
        print(f"DEBUG: Error traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500 

@workflow.route('/api/update_title_order/', methods=['POST'])
def update_title_order():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data received'}), 400
            
        post_id = data.get('post_id')
        titles = data.get('titles')
        
        if not post_id or not titles:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            
        # Convert titles list to JSON string
        titles_json = json.dumps(titles)
        
        # Update the provisional_title field in post_development
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE post_development 
                    SET provisional_title = %s 
                    WHERE post_id = %s
                """, (titles_json, post_id))
                conn.commit()
                
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"DEBUG: Error updating title order: {str(e)}")
        import traceback
        print(f"DEBUG: Error traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500 