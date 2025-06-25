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

@bp.route('/workflow_prompts', methods=['GET', 'POST', 'DELETE'])
def workflow_prompts():
    """View and edit workflow prompts."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if request.method == 'POST':
                if 'delete' in request.form:
                    # Handle prompt deletion
                    prompt_id = request.form.get('prompt_id')
                    if prompt_id:
                        cur.execute("DELETE FROM llm_prompt WHERE id = %s", (prompt_id,))
                        conn.commit()
                        return jsonify({'success': True})
                elif 'new' in request.form:
                    # Handle new prompt creation
                    prompt_type = request.form.get('prompt_type')
                    stage = request.form.get('stage')
                    substage = request.form.get('substage')
                    
                    cur.execute("""
                        INSERT INTO llm_prompt (
                            name, prompt_text, prompt_type, stage, substage, step
                        ) VALUES (
                            'New Prompt', '', %s, %s, %s, 'new_step'
                        ) RETURNING id
                    """, (prompt_type, stage if prompt_type == 'task' else None, 
                         substage if prompt_type == 'task' else None))
                    new_id = cur.fetchone()['id']
                    conn.commit()
                    return jsonify({'success': True, 'id': new_id})
                else:
                    # Handle prompt update
                    prompt_id = request.form.get('prompt_id')
                    if prompt_id:
                        name = request.form.get('name')
                        prompt_text = request.form.get('prompt_text')
                        
                        cur.execute("""
                            UPDATE llm_prompt 
                            SET name = %s, prompt_text = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (name, prompt_text, prompt_id))
                        conn.commit()
            
            # Get system prompts
            cur.execute("""
                SELECT id, name, prompt_text, prompt_type
                FROM llm_prompt
                WHERE prompt_type = 'system'
                ORDER BY name
            """)
            system_prompts = cur.fetchall()

            # Get task prompts organized by workflow
            cur.execute("""
                SELECT id, name, prompt_text, prompt_type, stage, substage, step
                FROM llm_prompt
                WHERE prompt_type = 'task' AND stage IS NOT NULL
                ORDER BY 
                    stage,
                    substage,
                    step,
                    name
            """)
            task_prompts = cur.fetchall()

            # Organize task prompts into a hierarchical structure
            tasks_by_stage = {}
            for prompt in task_prompts:
                stage = prompt['stage']
                substage = prompt['substage']
                
                if stage not in tasks_by_stage:
                    tasks_by_stage[stage] = {'substages': {}}
                
                if substage not in tasks_by_stage[stage]['substages']:
                    tasks_by_stage[stage]['substages'][substage] = {'prompts': []}
                
                tasks_by_stage[stage]['substages'][substage]['prompts'].append(prompt)
    
    return render_template('settings/workflow_prompts.html', 
                         system_prompts=system_prompts,
                         tasks_by_stage=tasks_by_stage)

@bp.route('/workflow_field_mapping')
def workflow_field_mapping():
    """View and edit workflow field mappings from step configurations."""
    with get_db_conn() as conn:
        # Use DictCursor to get results as dictionaries
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get stages ordered by stage_order
        cur.execute("""
            SELECT id, name, description 
            FROM workflow_stage_entity 
            ORDER BY stage_order
        """)
        stages = [dict(row) for row in cur.fetchall()]
        
        # Get substages with their steps and configs
        cur.execute("""
            SELECT DISTINCT ON (wsse.id)
                wsse.id as substage_id,
                wsse.stage_id,
                wsse.name as substage_name,
                wsse.description as substage_description,
                wse.name as step_name,
                wse.config
            FROM workflow_sub_stage_entity wsse
            LEFT JOIN workflow_step_entity wse ON wse.sub_stage_id = wsse.id
            ORDER BY wsse.id, wsse.sub_stage_order
        """)
        substages = [dict(row) for row in cur.fetchall()]
        
        # Get all steps with their configs
        cur.execute("""
            SELECT 
                id,
                sub_stage_id as substage_id,
                name,
                config
            FROM workflow_step_entity
            ORDER BY step_order
        """)
        steps = [dict(row) for row in cur.fetchall()]
        
        return render_template('settings/workflow_field_mapping.html',
                             stages=stages,
                             substages=substages,
                             steps=steps)

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