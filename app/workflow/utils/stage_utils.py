from app.utils.db import get_db_conn

def get_stage_status(stage_id):
    """Get the current status of a stage"""
    conn = get_db_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT status FROM workflow_stage 
            WHERE id = %s
        """, (stage_id,))
        result = cur.fetchone()
        return result[0] if result else None

def update_stage_status(stage_id, status):
    """Update the status of a stage"""
    conn = get_db_conn()
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE workflow_stage 
            SET status = %s 
            WHERE id = %s
        """, (status, stage_id))
        conn.commit()
        return True 