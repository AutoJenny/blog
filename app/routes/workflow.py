from flask import Blueprint, render_template, request, jsonify
from modules.nav.services import get_workflow_stages, get_workflow_context, get_all_posts
from app.db import get_db_conn
import json
from psycopg2.extras import Json

workflow_bp = Blueprint('workflow', __name__, url_prefix='/workflow')

@workflow_bp.route('/')
@workflow_bp.route('/posts/<int:post_id>')
@workflow_bp.route('/posts/<int:post_id>/<stage>')
@workflow_bp.route('/posts/<int:post_id>/<stage>/<substage>')
@workflow_bp.route('/posts/<int:post_id>/<stage>/<substage>/<step>')
def workflow_index(post_id=None, stage='planning', substage='idea', step='basic_idea'):
    """Main workflow route that handles all workflow navigation."""
    # Get all posts for the selector
    all_posts = get_all_posts()
    
    # If no post_id provided or the provided post_id doesn't exist, use the first post
    if not all_posts:
        return "No posts found", 404
        
    if post_id is None or not any(p['id'] == post_id for p in all_posts):
        post_id = all_posts[0]['id']
    
    # Get the workflow context first
    workflow_ctx = get_workflow_context()
    
    # Get step configuration from workflow_step_entity
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT wse.config
                FROM workflow_step_entity wse
                JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                WHERE wsse.name = %s AND wse.name = %s
            """, (substage, step))
            result = cur.fetchone()
            step_config = result['config'] if result else {}
    
    # If no config exists yet, use default configuration
    if not step_config:
        step_config = {
            'inputs': {
                'basic_idea': {
                    'type': 'textarea',
                    'db_field': 'idea_seed',
                    'db_table': 'post_development'
                }
            },
            'outputs': {
                'refined_idea': {
                    'type': 'textarea',
                    'db_field': 'basic_idea',
                    'db_table': 'post_development'
                }
            },
            'settings': {
                'llm': {
                    'model': 'mistral',
                    'task_prompt': 'Refine the basic idea into a more detailed concept.',
                    'input_mapping': {
                        'basic_idea': 'idea_seed'
                    },
                    'parameters': {
                        'temperature': 0.7,
                        'max_tokens': 1000,
                        'top_p': 1.0,
                        'frequency_penalty': 0.0,
                        'presence_penalty': 0.0
                    }
                }
            }
        }
    
    # Get input/output values from post_development table
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Get all fields that are mapped in the config
            fields = []
            for section in ['inputs', 'outputs']:
                if section in step_config:
                    fields.extend(f['db_field'] for f in step_config[section].values())
            
            if fields:
                field_list = ', '.join(fields)
                cur.execute(f"""
                    SELECT {field_list}
                    FROM post_development
                    WHERE post_id = %s
                """, (post_id,))
                row = cur.fetchone()
                if row:
                    values = dict(row)
                    input_values = {k: values[v['db_field']] for k, v in step_config.get('inputs', {}).items()}
                    output_values = {k: values[v['db_field']] for k, v in step_config.get('outputs', {}).items()}
                else:
                    input_values = {k: '' for k in step_config.get('inputs', {})}
                    output_values = {k: '' for k in step_config.get('outputs', {})}
            else:
                input_values = {k: '' for k in step_config.get('inputs', {})}
                output_values = {k: '' for k in step_config.get('outputs', {})}
    
    # Build context with current navigation state
    context = {
        'post_id': post_id,
        'current_post_id': post_id,
        'all_posts': all_posts,
        'workflow_ready': True,
        'llm_actions_data': None,  # Placeholder for future context
        'substage': substage,  # Required by llm_actions/panels.html
        'post': {'id': post_id},  # Required by llm_actions/panels.html
        'step_config': step_config,
        'input_values': input_values,
        'output_values': output_values
    }
    
    # Update with workflow context
    context.update(workflow_ctx)
    
    # Override with current navigation state
    context.update({
        'current_stage': stage,
        'current_substage': substage,
        'current_step': step
    })
    
    return render_template('workflow/index.html', **context)

@workflow_bp.route('/api/field_mappings/')
def get_field_mappings():
    """Get all available fields from post_development table with proper stage/substage grouping."""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # First get all mapped fields with their stage/substage info
                cur.execute("""
                    SELECT wfm.field_name, ws.name as stage_name, wss.name as substage_name
                    FROM workflow_field_mapping wfm
                    JOIN workflow_stage_entity ws ON wfm.stage_id = ws.id
                    JOIN workflow_sub_stage_entity wss ON wfm.substage_id = wss.id
                    ORDER BY ws.stage_order, wss.sub_stage_order, wfm.order_index
                """)
                mapped_fields = cur.fetchall()
                
                # Then get all fields from post_development
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'post_development'
                    AND column_name NOT IN ('id', 'post_id')
                    ORDER BY ordinal_position;
                """)
                all_fields = cur.fetchall()
                
                # Create mappings list
                mappings = []
                mapped_field_names = set(m['field_name'] for m in mapped_fields)
                
                # Add mapped fields first
                for field in mapped_fields:
                    mappings.append({
                        'stage_name': field['stage_name'],
                        'substage_name': field['substage_name'],
                        'field_name': field['field_name'],
                        'display_name': field['field_name'].replace('_', ' ').title()
                    })
                
                # Add unmapped fields under "Unmapped" stage
                for field in all_fields:
                    field_name = field['column_name']
                    if field_name not in mapped_field_names:
                        mappings.append({
                            'stage_name': 'Unmapped',
                            'substage_name': 'Available Fields',
                            'field_name': field_name,
                            'display_name': field_name.replace('_', ' ').title()
                        })
                
                return jsonify(mappings)
    except Exception as e:
        print(f"Error in get_field_mappings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/api/update_field_mapping/', methods=['POST'])
def update_field_mapping():
    """Update the field mapping for a textarea in the workflow_step_entity config."""
    data = request.get_json()
    target_id = data.get('target_id')
    old_field = data.get('old_field')
    new_field = data.get('new_field')
    stage = data.get('stage')
    substage = data.get('substage')
    step = data.get('step')
    section = data.get('section')  # 'inputs' or 'outputs'
    
    if not all([target_id, old_field, new_field, stage, substage, step, section]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Get the current config
            cur.execute("""
                SELECT wse.id, wse.config
                FROM workflow_step_entity wse
                JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                WHERE wsse.name = %s AND wse.name = %s
            """, (substage, step))
            result = cur.fetchone()
            
            if not result:
                return jsonify({'error': 'Step not found'}), 404
            
            step_id = result['id']
            config = result['config']
            
            # Update the field mapping in the config
            if section in config and target_id in config[section]:
                config[section][target_id]['db_field'] = new_field
                
                # Update the config in the database using psycopg2.extras.Json
                cur.execute("""
                    UPDATE workflow_step_entity
                    SET config = %s
                    WHERE id = %s
                """, (Json(config), step_id))
                conn.commit()
                
                return jsonify({'status': 'success'})
            else:
                return jsonify({'error': 'Invalid section or target_id'}), 400 