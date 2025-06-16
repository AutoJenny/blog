from app.utils.db import get_db_conn

def get_action_status(action_id):
    """Get the current status of an action"""
    conn = get_db_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT status FROM llm_action 
            WHERE id = %s
        """, (action_id,))
        result = cur.fetchone()
        return result[0] if result else None

def update_action_status(action_id, status):
    """Update the status of an action"""
    conn = get_db_conn()
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE llm_action 
            SET status = %s 
            WHERE id = %s
        """, (status, action_id))
        conn.commit()
        return True 