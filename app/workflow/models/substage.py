from app.utils.db import get_db_conn
from psycopg2.extras import RealDictCursor

class SubstageModel:
    def __init__(self, substage_id=None):
        self.substage_id = substage_id

    def get_substage(self):
        """Get substage details by ID"""
        if not self.substage_id:
            return None
        
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM workflow_substage 
                    WHERE id = %s
                """, (self.substage_id,))
                return cur.fetchone()

    def get_substages_by_stage(self, stage_id):
        """Get all substages for a stage"""
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM workflow_substage 
                    WHERE stage_id = %s 
                    ORDER BY substage_order
                """, (stage_id,))
                return cur.fetchall()

    def create_substage(self, data):
        """Create a new substage"""
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO workflow_substage 
                    (stage_id, name, description, substage_order, status) 
                    VALUES (%s, %s, %s, %s, %s) 
                    RETURNING id
                """, (data.get('stage_id'), data.get('name'), 
                      data.get('description'), data.get('substage_order'),
                      data.get('status', 'draft')))
                self.substage_id = cur.fetchone()[0]
                conn.commit()
                return self.substage_id

    def update_substage(self, data):
        """Update substage details"""
        if not self.substage_id:
            return False
        
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE workflow_substage 
                    SET name = %s, description = %s, 
                        substage_order = %s, status = %s 
                    WHERE id = %s
                """, (data.get('name'), data.get('description'),
                      data.get('substage_order'), data.get('status'),
                      self.substage_id))
                conn.commit()
                return True

    def delete_substage(self):
        """Delete a substage"""
        if not self.substage_id:
            return False
        
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM workflow_substage 
                    WHERE id = %s
                """, (self.substage_id,))
                conn.commit()
                return True 