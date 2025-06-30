"""Workflow services module."""

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

def get_workflow_actions(substage_id):
    """Get all workflow actions for a substage."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.* 
                FROM llm_action a
                JOIN workflow_sub_stage_entity s ON s.id = a.substage_id
                WHERE s.id = %s
                ORDER BY a.order
            """, (substage_id,))
            return [dict(row) for row in cur.fetchall()]

def get_workflow_action(action_id):
    """Get a workflow action by ID."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM llm_action WHERE id = %s
            """, (action_id,))
            row = cur.fetchone()
            if row:
                return dict(row)
            return None

def get_workflow_action_history(post_id, action_id):
    """Get workflow action history for a post."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM llm_action_history 
                WHERE post_id = %s AND action_id = %s
                ORDER BY created_at DESC
            """, (post_id, action_id))
            return [dict(row) for row in cur.fetchall()]

def save_workflow_action_history(post_id, action_id, input_text, output_text):
    """Save workflow action history."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO llm_action_history (post_id, action_id, input_text, output_text)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (post_id, action_id, input_text, output_text))
            conn.commit()
            return cur.fetchone()['id']

def get_workflow_step_actions(post_id, step_id):
    """Get all workflow step actions for a post."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM post_workflow_step_action 
                WHERE post_id = %s AND step_id = %s
                ORDER BY button_order
            """, (post_id, step_id))
            return [dict(row) for row in cur.fetchall()]

def save_workflow_step_action(post_id, step_id, action_id, input_field, output_field, button_label, button_order):
    """Save workflow step action."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO post_workflow_step_action (post_id, step_id, action_id, input_field, output_field, button_label, button_order)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (post_id, step_id, action_id, input_field, output_field, button_label, button_order))
            conn.commit()
            return cur.fetchone()['id'] 