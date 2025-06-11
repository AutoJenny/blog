from flask import current_app
from app.database import get_db_conn

class WorkflowNavigator:
    def __init__(self):
        self.stages = []
        self.substages = []
        self.steps = []

    def load_navigation(self):
        """Load the complete navigation structure from the database."""
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Load stages
                cur.execute("""
                    SELECT id, name, description, stage_order 
                    FROM workflow_stage_entity 
                    ORDER BY stage_order
                """)
                self.stages = [dict(row) for row in cur.fetchall()]
                current_app.logger.debug(f"Loaded stages: {self.stages}")

                # Load substages
                cur.execute("""
                    SELECT id, stage_id, name, description, sub_stage_order 
                    FROM workflow_sub_stage_entity 
                    ORDER BY sub_stage_order
                """)
                self.substages = [dict(row) for row in cur.fetchall()]
                current_app.logger.debug(f"Loaded substages: {self.substages}")

                # Load steps
                cur.execute("""
                    SELECT id, sub_stage_id, name, description, step_order 
                    FROM workflow_step_entity 
                    ORDER BY step_order
                """)
                self.steps = [dict(row) for row in cur.fetchall()]
                current_app.logger.debug(f"Loaded steps: {self.steps}")

    def get_stage(self, stage_id):
        """Get a specific stage by ID."""
        return next((s for s in self.stages if s['id'] == stage_id), None)

    def get_substage(self, substage_id):
        """Get a specific substage by ID."""
        return next((s for s in self.substages if s['id'] == substage_id), None)

    def get_step(self, step_id):
        """Get a specific step by ID."""
        return next((s for s in self.steps if s['id'] == step_id), None)

    def get_substages_for_stage(self, stage_id):
        """Get all substages for a specific stage."""
        return [s for s in self.substages if s['stage_id'] == stage_id]

    def get_steps_for_substage(self, substage_id):
        """Get all steps for a specific substage."""
        return [s for s in self.steps if s['sub_stage_id'] == substage_id]

    def get_navigation_context(self, current_stage_id=None, current_substage_id=None, current_step_id=None):
        """Get the complete navigation context for rendering."""
        return {
            'stages': self.stages,
            'substages': self.substages,
            'steps': self.steps,
            'current_stage_id': current_stage_id,
            'current_substage_id': current_substage_id,
            'current_step_id': current_step_id
        }

def seed_default_steps():
    """Seed each substage with a default 'Main' step."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Get all substages
            cur.execute("SELECT id FROM workflow_sub_stage_entity")
            substages = cur.fetchall()
            
            # Add 'Main' step to each substage if it doesn't exist
            for substage in substages:
                cur.execute("""
                    INSERT INTO workflow_step_entity (sub_stage_id, name, description, step_order)
                    SELECT %s, 'Main', 'Main step for this substage', 1
                    WHERE NOT EXISTS (
                        SELECT 1 FROM workflow_step_entity 
                        WHERE sub_stage_id = %s AND name = 'Main'
                    )
                """, (substage['id'], substage['id']))
            conn.commit()

# Initialize the navigator
navigator = WorkflowNavigator()

def init_app(app):
    """Initialize the navigator within the application context."""
    with app.app_context():
        navigator.load_navigation()
        seed_default_steps() 