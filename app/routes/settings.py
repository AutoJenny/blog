from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
import os
import json
from app.db import get_db_conn
import psycopg2.extras

bp = Blueprint('settings', __name__, url_prefix='/settings')

@bp.route('/')
def index():
    """Settings index page."""
    return render_template('settings/index.html')

@bp.route('/workflow_prompts', methods=['GET', 'POST'])
def workflow_prompts():
    """View and edit workflow prompts."""
    prompts_dir = os.path.join('app', 'data', 'prompts')
    prompts = {}
    
    # Load all JSON files from prompts directory
    for filename in os.listdir(prompts_dir):
        if filename.endswith('.json'):
            with open(os.path.join(prompts_dir, filename)) as f:
                prompts[filename[:-5]] = json.load(f)
    
    if request.method == 'POST':
        prompt_name = request.form.get('prompt_name')
        if prompt_name:
            # Extract fields for this prompt
            prompt_data = {}
            for key, value in request.form.items():
                if key.startswith(f"{prompt_name}__"):
                    field_name = key.split('__')[1]
                    prompt_data[field_name] = value
            
            # Save to file
            with open(os.path.join(prompts_dir, f"{prompt_name}.json"), 'w') as f:
                json.dump(prompt_data, f, indent=2)
            
            # Reload prompts
            with open(os.path.join(prompts_dir, f"{prompt_name}.json")) as f:
                prompts[prompt_name] = json.load(f)
    
    return render_template('settings/workflow_prompts.html', prompts=prompts)

@bp.route('/workflow_field_mapping')
def workflow_field_mapping():
    """View and edit workflow field mappings."""
    with get_db_conn() as conn:
        # Use DictCursor to get results as dictionaries
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get stages ordered by stage_order
        cur.execute("""
            SELECT id, name 
            FROM workflow_stage_entity 
            ORDER BY stage_order
        """)
        stages = [dict(row) for row in cur.fetchall()]
        
        # Get substages ordered by stage_order and sub_stage_order
        cur.execute("""
            SELECT wse.id, wse.name, wse.stage_id 
            FROM workflow_sub_stage_entity wse
            JOIN workflow_stage_entity ws ON ws.id = wse.stage_id
            ORDER BY ws.stage_order, wse.sub_stage_order
        """)
        substages = [dict(row) for row in cur.fetchall()]
        
        # Get field mappings ordered by stage_order, sub_stage_order, and order_index
        cur.execute("""
            SELECT wfm.id, wfm.field_name, wfm.stage_id, wfm.substage_id, 
                   wfm.order_index, wfm.accordion_type, wfm.target_id
            FROM workflow_field_mapping wfm
            JOIN workflow_stage_entity ws ON ws.id = wfm.stage_id
            JOIN workflow_sub_stage_entity wss ON wss.id = wfm.substage_id
            ORDER BY ws.stage_order, wss.sub_stage_order, wfm.order_index
        """)
        field_mappings = [dict(row) for row in cur.fetchall()]
    
    return render_template('settings/workflow_field_mapping.html',
                         stages=stages,
                         substages=substages,
                         field_mappings=field_mappings)

@bp.route('/planning_steps')
def planning_steps():
    """View planning steps configuration."""
    config_path = os.path.join('modules', 'llm_panel', 'config', 'planning_steps.json')
    with open(config_path) as f:
        raw_config = json.load(f)
    
    # Transform the nested JSON into a flatter structure for the template
    config = {}
    for stage_name, stage_data in raw_config.items():
        config[stage_name] = []
        for substage_name, substage_data in stage_data.items():
            for step_name, step_data in substage_data.items():
                step = {
                    'name': step_name,
                    'description': step_data.get('description', ''),
                    'inputs': list(step_data.get('inputs', {}).keys()),
                    'outputs': list(step_data.get('outputs', {}).keys())
                }
                config[stage_name].append(step)
    
    return render_template('settings/planning_steps.html', config=config)

# API endpoint for updating field mappings
@bp.route('/api/field-mapping', methods=['POST'])
def update_field_mapping():
    """Update a field mapping."""
    data = request.get_json()
    mapping_id = data.get('mapping_id')
    order_index = data.get('order_index')
    
    if not mapping_id or order_index is None:
        return jsonify({'error': 'Missing required fields'}), 400
    
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE workflow_field_mapping
            SET order_index = %s
            WHERE id = %s
            RETURNING id
        """, (order_index, mapping_id))
        
        if cur.rowcount == 0:
            return jsonify({'error': 'Mapping not found'}), 404
        
        conn.commit()
    
    return jsonify({'message': 'Mapping updated successfully'}) 