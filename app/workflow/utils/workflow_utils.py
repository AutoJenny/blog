from app.utils.db import get_db_conn

def get_workflow_status(workflow_id):
    """Get the current status of a workflow"""
    conn = get_db_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT status FROM workflow_step_entity 
            WHERE id = %s
        """, (workflow_id,))
        result = cur.fetchone()
        return result[0] if result else None

def update_workflow_status(workflow_id, status):
    """Update the status of a workflow"""
    conn = get_db_conn()
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE workflow_step_entity 
            SET status = %s 
            WHERE id = %s
        """, (status, workflow_id))
        conn.commit()
        return True 