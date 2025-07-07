from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
import os
import json
from app.db import get_db_conn
import psycopg2.extras
from psycopg2.extras import RealDictCursor

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
                    
                    if prompt_type == 'system':
                        # Create system prompt - populate system_prompt, leave prompt_text empty
                        cur.execute("""
                            INSERT INTO llm_prompt (
                                name, system_prompt, prompt_text
                            ) VALUES (
                                'New System Prompt', 'You are a helpful assistant.', ''
                            ) RETURNING id
                        """)
                    else:
                        # Create task prompt - populate prompt_text, leave system_prompt empty
                        cur.execute("""
                            INSERT INTO llm_prompt (
                                name, prompt_text, system_prompt
                            ) VALUES (
                                'New Task Prompt', 'Enter your task prompt here.', ''
                            ) RETURNING id
                        """)
                    
                    new_id = cur.fetchone()['id']
                    conn.commit()
                    return jsonify({'success': True, 'id': new_id})
                else:
                    # Handle prompt update
                    prompt_id = request.form.get('prompt_id')
                    if prompt_id:
                        name = request.form.get('name')
                        prompt_text = request.form.get('prompt_text')
                        
                        # Check if this is a system prompt (has system_prompt content)
                        cur.execute("""
                            SELECT system_prompt FROM llm_prompt WHERE id = %s
                        """, (prompt_id,))
                        result = cur.fetchone()
                        
                        if result and result['system_prompt']:
                            # Update system prompt
                            cur.execute("""
                                UPDATE llm_prompt 
                                SET name = %s, system_prompt = %s, updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, (name, prompt_text, prompt_id))
                        else:
                            # Update task prompt
                            cur.execute("""
                                UPDATE llm_prompt 
                                SET name = %s, prompt_text = %s, updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, (name, prompt_text, prompt_id))
                        
                        conn.commit()
            
            # Get system prompts - those with system_prompt column populated
            cur.execute("""
                SELECT id, name, description, 
                       COALESCE(system_prompt, '') as system_prompt,
                       COALESCE(prompt_text, '') as prompt_text
                FROM llm_prompt
                WHERE system_prompt IS NOT NULL AND system_prompt != ''
                ORDER BY name
            """)
            system_prompts = cur.fetchall()

            # Get task prompts - those without system_prompt column
            cur.execute("""
                SELECT id, name, description, 
                       COALESCE(system_prompt, '') as system_prompt,
                       COALESCE(prompt_text, '') as prompt_text
                FROM llm_prompt
                WHERE system_prompt IS NULL OR system_prompt = ''
                ORDER BY name
            """)
            task_prompts = cur.fetchall()

            # Get workflow stages and substages for the modal dropdowns
            cur.execute("""
                SELECT id, name, description, stage_order
                FROM workflow_stage_entity
                ORDER BY stage_order
            """)
            stages = cur.fetchall()

            cur.execute("""
                SELECT id, stage_id, name, description, sub_stage_order
                FROM workflow_sub_stage_entity
                ORDER BY stage_id, sub_stage_order
            """)
            substages = cur.fetchall()

            # Organize task prompts by stage/substage (for now, put them all under 'all' since we don't have stage/substage data in llm_prompt)
            tasks_by_stage = {'all': {'substages': {'all': {'prompts': task_prompts}}}}
    
    return render_template('settings/workflow_prompts.html', 
                         system_prompts=system_prompts,
                         tasks_by_stage=tasks_by_stage,
                         stages=stages,
                         substages=substages)

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
        
        # DEBUG: Log the data being passed to template
        with open('logs/debug_workflow_data.txt', 'w') as f:
            f.write(f"[DEBUG] Stages: {len(stages)}\n")
            for stage in stages:
                f.write(f"  Stage {stage['id']}: {stage['name']}\n")
            
            f.write(f"[DEBUG] Substages: {len(substages)}\n")
            for substage in substages:
                f.write(f"  Substage {substage['substage_id']}: {substage['substage_name']} (stage {substage['stage_id']})\n")
            
            f.write(f"[DEBUG] Steps: {len(steps)}\n")
            for step in steps:
                f.write(f"  Step {step['id']}: {step['name']} (substage {step['substage_id']})\n")
        
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

@bp.route('/format_templates')
def format_templates():
    """Format templates management page"""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT id, name, description, fields, llm_instructions, created_at, updated_at 
                FROM workflow_format_template 
                ORDER BY name
            """)
            templates = cur.fetchall()
            
            # Transform the data to include format details
            formatted_templates = []
            for template in templates:
                import json
                fields_data = template['fields']
                if isinstance(fields_data, str):
                    fields_data_obj = json.loads(fields_data)
                else:
                    fields_data_obj = fields_data
                
                # Extract format type and fields using the same logic as the API
                format_type = fields_data_obj.get('type', 'output') if isinstance(fields_data_obj, dict) else 'output'
                
                # Extract fields using the same logic as _extract_fields_from_jsonb
                fields = []
                if isinstance(fields_data_obj, list):
                    # New format: direct array
                    fields = fields_data_obj
                elif isinstance(fields_data_obj, dict) and 'schema' in fields_data_obj:
                    # Old format: schema dict
                    schema = fields_data_obj['schema']
                    if isinstance(schema, dict) and 'properties' in schema:
                        for field_name, field_spec in schema['properties'].items():
                            if not isinstance(field_spec, dict):
                                continue
                            field = {
                                'name': field_name,
                                'type': field_spec.get('type', 'string'),
                                'required': field_name in schema.get('required', [])
                            }
                            if 'description' in field_spec:
                                field['description'] = field_spec['description']
                            fields.append(field)
                
                formatted_template = {
                    'id': template['id'],
                    'name': template['name'],
                    'description': template['description'],
                    'format_type': format_type,
                    'fields': fields,
                    'llm_instructions': template.get('llm_instructions', ''),
                    'created_at': template['created_at'],
                    'updated_at': template['updated_at']
                }
                formatted_templates.append(formatted_template)
            
            # Organize templates by type
            input_templates = [t for t in formatted_templates if t['format_type'] == 'input']
            output_templates = [t for t in formatted_templates if t['format_type'] == 'output']
            bidirectional_templates = [t for t in formatted_templates if t['format_type'] == 'bidirectional']
    
    return render_template('settings/format_templates.html', 
                         input_templates=input_templates,
                         output_templates=output_templates,
                         bidirectional_templates=bidirectional_templates)

@bp.route('/workflow_step_formats')
def workflow_step_formats():
    """Workflow step format configuration page"""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get stages ordered by stage_order
            cur.execute("""
                SELECT id, name, description 
                FROM workflow_stage_entity 
                ORDER BY stage_order
            """)
            stages = cur.fetchall()
            
            # Get substages with their steps and configs
            cur.execute("""
                SELECT DISTINCT ON (wsse.id)
                    wsse.id as substage_id,
                    wsse.stage_id,
                    wsse.name as substage_name,
                    wsse.description as substage_description
                FROM workflow_sub_stage_entity wsse
                ORDER BY wsse.id, wsse.sub_stage_order
            """)
            substages = cur.fetchall()
            
            # Get all steps with their format configurations
            cur.execute("""
                SELECT 
                    wse.id,
                    wse.sub_stage_id as substage_id,
                    wse.name,
                    wsf.input_format_id,
                    wsf.output_format_id,
                    input_fmt.name as input_format_name,
                    output_fmt.name as output_format_name
                FROM workflow_step_entity wse
                LEFT JOIN workflow_step_format wsf ON wsf.step_id = wse.id
                LEFT JOIN llm_format_template input_fmt ON wsf.input_format_id = input_fmt.id
                LEFT JOIN llm_format_template output_fmt ON wsf.output_format_id = output_fmt.id
                ORDER BY wse.step_order
            """)
            steps = cur.fetchall()
            
            # Add format information to steps
            for step in steps:
                step['input_format'] = {
                    'id': step['input_format_id'],
                    'name': step['input_format_name']
                } if step['input_format_id'] else None
                
                step['output_format'] = {
                    'id': step['output_format_id'],
                    'name': step['output_format_name']
                } if step['output_format_id'] else None
            
            return render_template('settings/workflow_step_formats.html',
                                stages=stages,
                                substages=substages,
                                steps=steps)

# API endpoint for saving step order
@bp.route('/api/step-order', methods=['POST'])
def save_step_order():
    """Save the order of steps within a substage."""
    data = request.get_json()
    substage_id = data.get('substage_id')
    steps = data.get('steps', [])
    
    if not substage_id or not steps:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    try:
        with get_db_conn() as conn:
            cur = conn.cursor()
            
            # Update step order for each step
            for step_data in steps:
                step_id = step_data.get('step_id')
                order = step_data.get('order')
                
                if step_id and order is not None:
                    cur.execute("""
                        UPDATE workflow_step_entity 
                        SET step_order = %s 
                        WHERE id = %s AND sub_stage_id = %s
                    """, (order, step_id, substage_id))
            
            conn.commit()
            
        return jsonify({'success': True, 'message': 'Step order saved successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error saving step order: {str(e)}'}), 500

@bp.route('/api/step', methods=['POST'])
def save_step():
    """Save or update a workflow step."""
    try:
        data = request.get_json()
        
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Parse config JSON if provided
                config = {}
                if data.get('config'):
                    try:
                        config = json.loads(data['config'])
                    except json.JSONDecodeError:
                        return jsonify({'success': False, 'message': 'Invalid JSON in config field'})
                
                # Update the step
                cur.execute("""
                    UPDATE workflow_step_entity 
                    SET name = %s, sub_stage_id = %s, config = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (data['name'], data['substage_id'], json.dumps(config), data['id']))
                
                if cur.rowcount == 0:
                    return jsonify({'success': False, 'message': 'Step not found'})
                
                conn.commit()
                return jsonify({'success': True})
                
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/step', methods=['PUT'])
def create_step():
    """Create a new workflow step."""
    try:
        data = request.get_json()
        
        if not data.get('name') or not data.get('substage_id'):
            return jsonify({'success': False, 'message': 'Missing required fields: name and substage_id'})
        
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Parse config JSON if provided
                config = {}
                if data.get('config'):
                    try:
                        config = json.loads(data['config'])
                    except json.JSONDecodeError:
                        return jsonify({'success': False, 'message': 'Invalid JSON in config field'})
                
                # Get the next order number for this substage
                cur.execute("""
                    SELECT COALESCE(MAX(step_order), 0) + 1 as next_order
                    FROM workflow_step_entity 
                    WHERE sub_stage_id = %s
                """, (data['substage_id'],))
                
                result = cur.fetchone()
                next_order = result['next_order']
                
                # Create the new step
                cur.execute("""
                    INSERT INTO workflow_step_entity 
                    (name, sub_stage_id, step_order, config)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (data['name'], data['substage_id'], next_order, json.dumps(config)))
                
                new_step_id = cur.fetchone()['id']
                conn.commit()
                
                return jsonify({'success': True, 'step_id': new_step_id, 'message': f'Step "{data["name"]}" created successfully'})
                
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/step/<int:step_id>', methods=['DELETE'])
def delete_step(step_id):
    """Delete a workflow step."""
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # First, check if the step exists and get its details
                cur.execute("""
                    SELECT id, name, sub_stage_id 
                    FROM workflow_step_entity 
                    WHERE id = %s
                """, (step_id,))
                
                step = cur.fetchone()
                if not step:
                    return jsonify({'success': False, 'message': 'Step not found'})
                
                # Check if there are any dependent records (like workflow_step_prompt)
                cur.execute("""
                    SELECT COUNT(*) as count 
                    FROM workflow_step_prompt 
                    WHERE step_id = %s
                """, (step_id,))
                
                prompt_count = cur.fetchone()['count']
                
                # Check for other potential dependencies
                cur.execute("""
                    SELECT COUNT(*) as count 
                    FROM workflow_step_format 
                    WHERE step_id = %s
                """, (step_id,))
                
                format_count = cur.fetchone()['count']
                
                # Check for post workflow step actions
                cur.execute("""
                    SELECT COUNT(*) as count 
                    FROM post_workflow_step_action 
                    WHERE step_id = %s
                """, (step_id,))
                
                action_count = cur.fetchone()['count']
                
                # If there are dependencies, warn the user
                if prompt_count > 0 or format_count > 0 or action_count > 0:
                    dependencies = []
                    if prompt_count > 0:
                        dependencies.append(f"{prompt_count} prompt association(s)")
                    if format_count > 0:
                        dependencies.append(f"{format_count} format association(s)")
                    if action_count > 0:
                        dependencies.append(f"{action_count} workflow action(s)")
                    
                    return jsonify({
                        'success': False, 
                        'message': f'Cannot delete step "{step["name"]}" because it has dependencies: {", ".join(dependencies)}. Please remove these associations first.'
                    })
                
                # Delete the step
                cur.execute("DELETE FROM workflow_step_entity WHERE id = %s", (step_id,))
                
                if cur.rowcount == 0:
                    return jsonify({'success': False, 'message': 'Step not found'})
                
                conn.commit()
                return jsonify({'success': True, 'message': f'Step "{step["name"]}" deleted successfully'})
                
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/step/<int:step_id>/force-delete', methods=['DELETE'])
def force_delete_step(step_id):
    """Force delete a workflow step by removing all dependencies first."""
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # First, check if the step exists and get its details
                cur.execute("""
                    SELECT id, name, sub_stage_id 
                    FROM workflow_step_entity 
                    WHERE id = %s
                """, (step_id,))
                
                step = cur.fetchone()
                if not step:
                    return jsonify({'success': False, 'message': 'Step not found'})
                
                # Count dependencies before deletion for reporting
                cur.execute("""
                    SELECT COUNT(*) as count 
                    FROM workflow_step_prompt 
                    WHERE step_id = %s
                """, (step_id,))
                prompt_count = cur.fetchone()['count']
                
                cur.execute("""
                    SELECT COUNT(*) as count 
                    FROM workflow_step_format 
                    WHERE step_id = %s
                """, (step_id,))
                format_count = cur.fetchone()['count']
                
                cur.execute("""
                    SELECT COUNT(*) as count 
                    FROM post_workflow_step_action 
                    WHERE step_id = %s
                """, (step_id,))
                action_count = cur.fetchone()['count']
                
                # Delete all dependencies first
                deleted_items = []
                
                if prompt_count > 0:
                    cur.execute("DELETE FROM workflow_step_prompt WHERE step_id = %s", (step_id,))
                    deleted_items.append(f"{prompt_count} prompt association(s)")
                
                if format_count > 0:
                    cur.execute("DELETE FROM workflow_step_format WHERE step_id = %s", (step_id,))
                    deleted_items.append(f"{format_count} format association(s)")
                
                if action_count > 0:
                    cur.execute("DELETE FROM post_workflow_step_action WHERE step_id = %s", (step_id,))
                    deleted_items.append(f"{action_count} workflow action(s)")
                
                # Now delete the step itself
                cur.execute("DELETE FROM workflow_step_entity WHERE id = %s", (step_id,))
                
                if cur.rowcount == 0:
                    return jsonify({'success': False, 'message': 'Step not found'})
                
                conn.commit()
                
                # Build success message
                if deleted_items:
                    message = f'Step "{step["name"]}" force deleted successfully. Removed: {", ".join(deleted_items)}.'
                else:
                    message = f'Step "{step["name"]}" deleted successfully.'
                
                return jsonify({'success': True, 'message': message})
                
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})



# API endpoint for getting substages by stage
@bp.route('/api/substages')
def get_substages():
    """Get substages for a specific stage."""
    stage_id = request.args.get('stage_id')
    
    if not stage_id:
        return jsonify({'success': False, 'message': 'Missing stage_id parameter'}), 400
    
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cur.execute("""
                SELECT id, name, description
                FROM workflow_sub_stage_entity
                WHERE stage_id = %s
                ORDER BY sub_stage_order
            """, (stage_id,))
            
            substages = [dict(row) for row in cur.fetchall()]
            
        return jsonify({'success': True, 'substages': substages})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching substages: {str(e)}'}), 500 

# API endpoint to update llm_available_tables for a stage
@bp.route('/api/stage/<int:stage_id>/llm_tables', methods=['POST'])
def update_stage_llm_tables(stage_id):
    data = request.get_json()
    tables = data.get('llm_available_tables', [])
    if not isinstance(tables, list):
        return jsonify({'success': False, 'message': 'Invalid tables list'}), 400
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT config FROM workflow_stage_entity WHERE id = %s", (stage_id,))
        row = cur.fetchone()
        config = row[0] if row and row[0] else {}
        if isinstance(config, str):
            config = json.loads(config)
        config['llm_available_tables'] = tables
        cur.execute("UPDATE workflow_stage_entity SET config = %s WHERE id = %s", (json.dumps(config), stage_id))
        conn.commit()
    return jsonify({'success': True})

# API endpoint to update llm_available_tables for a substage
@bp.route('/api/substage/<int:substage_id>/llm_tables', methods=['POST'])
def update_substage_llm_tables(substage_id):
    data = request.get_json()
    tables = data.get('llm_available_tables', [])
    if not isinstance(tables, list):
        return jsonify({'success': False, 'message': 'Invalid tables list'}), 400
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT config FROM workflow_sub_stage_entity WHERE id = %s", (substage_id,))
        row = cur.fetchone()
        config = row[0] if row and row[0] else {}
        if isinstance(config, str):
            config = json.loads(config)
        config['llm_available_tables'] = tables
        cur.execute("UPDATE workflow_sub_stage_entity SET config = %s WHERE id = %s", (json.dumps(config), substage_id))
        conn.commit()
    return jsonify({'success': True})

# API endpoint to update llm_available_tables for a step
@bp.route('/api/step/<int:step_id>/llm_tables', methods=['POST'])
def update_step_llm_tables(step_id):
    data = request.get_json()
    tables = data.get('llm_available_tables', [])
    if not isinstance(tables, list):
        return jsonify({'success': False, 'message': 'Invalid tables list'}), 400
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT config FROM workflow_step_entity WHERE id = %s", (step_id,))
        row = cur.fetchone()
        config = row[0] if row and row[0] else {}
        if isinstance(config, str):
            config = json.loads(config)
        config['llm_available_tables'] = tables
        cur.execute("UPDATE workflow_step_entity SET config = %s WHERE id = %s", (json.dumps(config), step_id))
        conn.commit()
    return jsonify({'success': True})

# API endpoint to get llm_available_tables for a stage
@bp.route('/api/stage/<int:stage_id>/llm_tables', methods=['GET'])
def get_stage_llm_tables(stage_id):
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT config FROM workflow_stage_entity WHERE id = %s", (stage_id,))
        row = cur.fetchone()
        config = row[0] if row and row[0] else {}
        if isinstance(config, str):
            config = json.loads(config)
        tables = config.get('llm_available_tables', [])
    return jsonify({'llm_available_tables': tables})

# API endpoint to get llm_available_tables for a substage
@bp.route('/api/substage/<int:substage_id>/llm_tables', methods=['GET'])
def get_substage_llm_tables(substage_id):
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT config FROM workflow_sub_stage_entity WHERE id = %s", (substage_id,))
        row = cur.fetchone()
        config = row[0] if row and row[0] else {}
        if isinstance(config, str):
            config = json.loads(config)
        tables = config.get('llm_available_tables', [])
    return jsonify({'llm_available_tables': tables})

# API endpoint to get llm_available_tables for a step
@bp.route('/api/step/<int:step_id>/llm_tables', methods=['GET'])
def get_step_llm_tables(step_id):
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT config FROM workflow_step_entity WHERE id = %s", (step_id,))
        row = cur.fetchone()
        config = row[0] if row and row[0] else {}
        if isinstance(config, str):
            config = json.loads(config)
        tables = config.get('llm_available_tables', [])
    return jsonify({'llm_available_tables': tables}) 