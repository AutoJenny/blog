import json
from psycopg2.extras import RealDictCursor
from app.utils.db import get_db_conn
import logging

logger = logging.getLogger(__name__)

class WorkflowModel:
    def __init__(self, workflow_id=None):
        self.workflow_id = workflow_id

    def get_workflow(self):
        """Get workflow details by ID"""
        if not self.workflow_id:
            return None
        
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM workflow_step_entity 
                    WHERE id = %s
                """, (self.workflow_id,))
                result = cur.fetchone()
                logger.info(f"Workflow data: {result}")
                return result

    def get_all_workflows(self):
        """Get all workflows"""
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM workflow_step_entity 
                    ORDER BY id DESC
                """)
                results = cur.fetchall()
                logger.info(f"All workflows data: {results}")
                return results

    def create_workflow(self, data):
        """Create a new workflow"""
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Convert config dict to JSON string
                config_json = json.dumps(data.get('config', {}))
                cur.execute("""
                    INSERT INTO workflow_step_entity 
                    (name, description, step_order, config) 
                    VALUES (%s, %s, %s, %s) 
                    RETURNING id
                """, (data.get('name'), data.get('description'), 
                      data.get('step_order'), config_json))
                self.workflow_id = cur.fetchone()[0]
                conn.commit()
                return self.workflow_id

    def update_workflow(self, data):
        """Update workflow details"""
        if not self.workflow_id:
            return False
        
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Convert config dict to JSON string
                config_json = json.dumps(data.get('config', {}))
                cur.execute("""
                    UPDATE workflow_step_entity 
                    SET name = %s, description = %s, 
                        step_order = %s, config = %s
                    WHERE id = %s
                """, (data.get('name'), data.get('description'), 
                      data.get('step_order'), config_json,
                      self.workflow_id))
                conn.commit()
                return True

    def delete_workflow(self):
        """Delete a workflow"""
        if not self.workflow_id:
            return False
        
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM workflow_step_entity 
                    WHERE id = %s
                """, (self.workflow_id,))
                conn.commit()
                return True 