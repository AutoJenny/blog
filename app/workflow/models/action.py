from app.utils.db import get_db_conn
from psycopg2.extras import RealDictCursor

class ActionModel:
    def __init__(self, action_id=None):
        self.action_id = action_id

    def get_action(self):
        """Get action details by ID"""
        if not self.action_id:
            return None
        
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM llm_action 
                    WHERE id = %s
                """, (self.action_id,))
                return cur.fetchone()

    def get_actions_by_substage(self, substage_id):
        """Get all actions for a substage"""
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM llm_action 
                    WHERE substage_id = %s 
                    ORDER BY action_order
                """, (substage_id,))
                return cur.fetchall()

    def create_action(self, data):
        """Create a new action"""
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO llm_action 
                    (substage_id, name, description, action_order, 
                     prompt_template, status) 
                    VALUES (%s, %s, %s, %s, %s, %s) 
                    RETURNING id
                """, (data.get('substage_id'), data.get('name'), 
                      data.get('description'), data.get('action_order'),
                      data.get('prompt_template'), data.get('status', 'draft')))
                self.action_id = cur.fetchone()[0]
                conn.commit()
                return self.action_id

    def update_action(self, data):
        """Update action details"""
        if not self.action_id:
            return False
        
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE llm_action 
                    SET name = %s, description = %s, 
                        action_order = %s, prompt_template = %s,
                        status = %s 
                    WHERE id = %s
                """, (data.get('name'), data.get('description'),
                      data.get('action_order'), data.get('prompt_template'),
                      data.get('status'), self.action_id))
                conn.commit()
                return True

    def delete_action(self):
        """Delete an action"""
        if not self.action_id:
            return False
        
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM llm_action 
                    WHERE id = %s
                """, (self.action_id,))
                conn.commit()
                return True 