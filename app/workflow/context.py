"""Workflow context module."""

from app.database import get_db_conn
import psycopg2.extras

def get_workflow_stages():
    """Get all workflow stages from the database."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, description, stage_order 
                FROM workflow_stage_entity 
                ORDER BY stage_order
            """)
            return [dict(row) for row in cur.fetchall()]

def get_workflow_substages():
    """Get all workflow substages from the database."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, stage_id, name, description, sub_stage_order 
                FROM workflow_sub_stage_entity 
                ORDER BY stage_id, sub_stage_order
            """)
            return [dict(row) for row in cur.fetchall()]

def get_workflow_steps():
    """Get all workflow steps from the database."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, sub_stage_id, name, description, step_order 
                FROM workflow_step_entity 
                ORDER BY sub_stage_id, step_order
            """)
            return [dict(row) for row in cur.fetchall()]

def get_workflow_context(stage=None, substage=None, step=None):
    """Get workflow context for the current stage/substage/step."""
    # Get stages and substages data
    stages = get_workflow_stages()
    substages = get_workflow_substages()
    steps = get_workflow_steps()
    
    # Convert stages to a dict for easier lookup
    stages_dict = {stage['name']: stage for stage in stages}
    substages_dict = {substage['name']: substage for substage in substages}
    steps_dict = {step['name']: step for step in steps}
    
    # Return context with default values
    return {
        'current_stage': stage or 'planning',
        'current_substage': substage or 'idea',
        'current_step': step or 'initial',
        'stages': stages_dict,
        'substages': substages_dict,
        'steps': steps_dict
    }

def get_step_context(post_id, stage_name, substage_name, step_name):
    """Get the context for a workflow step."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get step configuration
            cur.execute("""
                SELECT wse.config
                FROM workflow_step_entity wse
                JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                WHERE wst.name ILIKE %s
                AND wsse.name ILIKE %s
                AND wse.name ILIKE %s
            """, (stage_name, substage_name, step_name))
            
            step_config = cur.fetchone()
            if not step_config:
                return {}
                
            config = step_config[0]
            
            # Get input values
            input_values = {}
            for input_id, input_config in config.get('inputs', {}).items():
                db_field = input_config.get('db_field')
                if db_field:
                    cur.execute(f"""
                        SELECT {db_field}
                        FROM post_development
                        WHERE post_id = %s
                    """, (post_id,))
                    value = cur.fetchone()
                    if value:
                        input_values[input_id] = value[0]
            
            # Get output values
            output_values = {}
            for output_id, output_config in config.get('outputs', {}).items():
                db_field = output_config.get('db_field')
                if db_field:
                    cur.execute(f"""
                        SELECT {db_field}
                        FROM post_development
                        WHERE post_id = %s
                    """, (post_id,))
                    value = cur.fetchone()
                    if value:
                        output_values[output_id] = value[0]
            
            return {
                'step_config': config,
                'input_values': input_values,
                'output_values': output_values,
                'post_id': post_id,
                'current_stage': stage_name,
                'current_substage': substage_name,
                'current_step': step_name
            } 