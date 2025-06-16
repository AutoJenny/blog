from app.utils.db import get_db_conn
from psycopg2.extras import RealDictCursor

class StageModel:
    def __init__(self, stage_id=None):
        self.stage_id = stage_id

    def get_stage(self):
        """Get stage details by ID"""
        if not self.stage_id:
            return None
        
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM workflow_stage 
                    WHERE id = %s
                """, (self.stage_id,))
                return cur.fetchone()

    def get_stages_by_workflow(self, workflow_id):
        """Get all stages for a workflow"""
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM workflow_stage 
                    WHERE workflow_id = %s 
                    ORDER BY stage_order
                """, (workflow_id,))
                return cur.fetchall()

    def create_stage(self, data):
        """Create a new stage"""
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO workflow_stage 
                    (workflow_id, name, description, stage_order, status) 
                    VALUES (%s, %s, %s, %s, %s) 
                    RETURNING id
                """, (data.get('workflow_id'), data.get('name'), 
                      data.get('description'), data.get('stage_order'),
                      data.get('status', 'draft')))
                self.stage_id = cur.fetchone()[0]
                conn.commit()
                return self.stage_id

    def update_stage(self, data):
        """Update stage details"""
        if not self.stage_id:
            return False
        
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE workflow_stage 
                    SET name = %s, description = %s, 
                        stage_order = %s, status = %s 
                    WHERE id = %s
                """, (data.get('name'), data.get('description'),
                      data.get('stage_order'), data.get('status'),
                      self.stage_id))
                conn.commit()
                return True

    def delete_stage(self):
        """Delete a stage"""
        if not self.stage_id:
            return False
        
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM workflow_stage 
                    WHERE id = %s
                """, (self.stage_id,))
                conn.commit()
                return True 