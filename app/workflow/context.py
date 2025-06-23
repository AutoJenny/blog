"""Workflow context module."""

from app.database import get_db_conn

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