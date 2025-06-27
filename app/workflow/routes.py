"""
Routes for the workflow module.
"""

import json
import psycopg2.extras
from flask import render_template, request, jsonify, abort, redirect, url_for
from app.db import get_db_conn
from app.api.workflow.decorators import deprecated_endpoint
from . import bp
from app.api.workflow import bp as api_workflow_bp

# Use proper nav module instead
from modules.nav.services import get_workflow_context
from app.services.shared import get_workflow_stages_from_db, get_all_posts_from_db
import subprocess
import sys
import os
from app.llm.services import execute_llm_request
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
    
    # Get step from query parameters, keeping original format for database lookup
    step = request.args.get('step', 'initial')
    # Convert URL format (lowercase with underscores) to DB format (title case with spaces)
    display_step = step.replace('_', ' ').title()
    
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
    
    # Add step configuration and field values to context
    context.update({
        'post': post,
        'step_config': step_config,
        'field_values': field_values,
        'step_id': step_id,
        'current_stage': stage,
        'current_substage': substage,
        'current_step': display_step,
        'current_post_id': post_id,
        'all_posts': get_all_posts(),
        'step': {
            'name': step_name or display_step,
            'description': step_description
        }
    })
    
    return render_template('workflow/steps/planning_step.html', **context)

@bp.route('/posts/<int:post_id>/')
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
        'all_posts': get_all_posts()
    })
    
    return render_template('workflow/index.html', **context)

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

@bp.route('/posts/<int:post_id>/<stage>/<substage>/')
def substage(post_id, stage: str, substage: str):
    """Workflow substage page."""
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    
    context = get_workflow_context(stage, substage)
    if not context:
        abort(404, f"Stage {stage} or substage {substage} not found.")
    
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

@bp.route('/api/v1/workflow/title_order/', methods=['POST'])
@deprecated_endpoint(message="This endpoint is deprecated. Use /api/workflow/posts/<post_id>/title_order instead.")
def api_update_title_order():
    """Deprecated title order endpoint."""
    return jsonify({'error': 'This endpoint is deprecated'}), 410

@bp.route('/api/field_mappings/', methods=['GET'])
@deprecated_endpoint(message="This endpoint is deprecated. Use /api/workflow/steps/<step_id>/field_mappings instead.")
def get_field_mappings():
    """Deprecated field mappings endpoint."""
    return jsonify({'error': 'This endpoint is deprecated'}), 410

@bp.route('/api/update_field_mapping/', methods=['POST'])
@deprecated_endpoint(message="This endpoint is deprecated. Use /api/workflow/steps/<step_id>/field_mappings instead.")
def update_field_mapping():
    """Deprecated field mapping update endpoint."""
    return jsonify({'error': 'This endpoint is deprecated'}), 410

@bp.route('/api/prompts/', methods=['GET'])
@deprecated_endpoint(message="This endpoint is deprecated. Use /api/workflow/prompts instead.")
def get_prompts():
    """Deprecated prompts endpoint."""
    return jsonify({'error': 'This endpoint is deprecated'}), 410

@bp.route('/api/step_prompts/<int:post_id>/<int:step_id>', methods=['GET'])
@deprecated_endpoint(message="This endpoint is deprecated. Use /api/workflow/steps/<step_id>/prompts/<post_id> instead.")
def get_step_prompts(post_id, step_id):
    """Deprecated step prompts endpoint."""
    return jsonify({'error': 'This endpoint is deprecated'}), 410

@bp.route('/api/step_prompts/<int:post_id>/<int:step_id>', methods=['POST'])
@deprecated_endpoint(message="This endpoint is deprecated. Use /api/workflow/steps/<step_id>/prompts/<post_id> instead.")
def save_step_prompts(post_id, step_id):
    """Deprecated step prompts save endpoint."""
    return jsonify({'error': 'This endpoint is deprecated'}), 410 