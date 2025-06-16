from app.utils.db import get_db_conn

def get_substage_status(substage_id):
    """Get the current status of a substage"""
    conn = get_db_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT status FROM workflow_substage 
            WHERE id = %s
        """, (substage_id,))
        result = cur.fetchone()
        return result[0] if result else None

def update_substage_status(substage_id, status):
    """Update the status of a substage"""
    conn = get_db_conn()
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE workflow_substage 
            SET status = %s 
            WHERE id = %s
        """, (status, substage_id))
        conn.commit()
        return True 