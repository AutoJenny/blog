from flask import current_app, abort
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

    def get_stage_by_name(self, stage_name):
        """Get a specific stage by name."""
        return next((s for s in self.stages if s['name'] == stage_name), None)

    def get_substage(self, substage_id):
        """Get a specific substage by ID."""
        return next((s for s in self.substages if s['id'] == substage_id), None)

    def get_substage_by_name(self, stage_name, substage_name):
        """Get a specific substage by name, validating stage."""
        stage = self.get_stage_by_name(stage_name)
        if not stage:
            return None
        return next((s for s in self.substages 
                    if s['stage_id'] == stage['id'] and s['name'] == substage_name), None)

    def get_step(self, step_id):
        """Get a specific step by ID."""
        return next((s for s in self.steps if s['id'] == step_id), None)

    def get_step_by_name(self, stage_name, substage_name, step_name):
        """Get a specific step by name, validating full path."""
        substage = self.get_substage_by_name(stage_name, substage_name)
        if not substage:
            return None
        return next((s for s in self.steps 
                    if s['sub_stage_id'] == substage['id'] and s['name'] == step_name), None)

    def validate_path(self, stage_name, substage_name, step_name):
        """Validate that a stage/substage/step path exists."""
        step = self.get_step_by_name(stage_name, substage_name, step_name)
        if not step:
            current_app.logger.error(f"Invalid path: {stage_name}/{substage_name}/{step_name}")
            abort(404)
        return step

    def get_substages_for_stage(self, stage_id):
        """Get all substages for a specific stage."""
        return [s for s in self.substages if s['stage_id'] == stage_id]

    def get_steps_for_substage(self, substage_id):
        """Get all steps for a specific substage."""
        return [s for s in self.steps if s['sub_stage_id'] == substage_id]

    def get_next_step(self, current_stage_name, current_substage_name, current_step_name):
        """Get the next step in the workflow, handling transitions between substages/stages."""
        current_step = self.get_step_by_name(current_stage_name, current_substage_name, current_step_name)
        if not current_step:
            return None

        # Get current substage and its steps
        current_substage = next(s for s in self.substages if s['id'] == current_step['sub_stage_id'])
        substage_steps = sorted(self.get_steps_for_substage(current_substage['id']), 
                              key=lambda x: x['step_order'])
        
        # Try next step in current substage
        current_step_index = next(i for i, s in enumerate(substage_steps) if s['id'] == current_step['id'])
        if current_step_index < len(substage_steps) - 1:
            return substage_steps[current_step_index + 1]

        # Try first step of next substage in current stage
        current_stage = next(s for s in self.stages if s['id'] == current_substage['stage_id'])
        stage_substages = sorted(self.get_substages_for_stage(current_stage['id']), 
                               key=lambda x: x['sub_stage_order'])
        current_substage_index = next(i for i, s in enumerate(stage_substages) 
                                    if s['id'] == current_substage['id'])
        if current_substage_index < len(stage_substages) - 1:
            next_substage = stage_substages[current_substage_index + 1]
            next_substage_steps = sorted(self.get_steps_for_substage(next_substage['id']), 
                                       key=lambda x: x['step_order'])
            if next_substage_steps:
                return next_substage_steps[0]

        # Try first step of first substage of next stage
        stages = sorted(self.stages, key=lambda x: x['stage_order'])
        current_stage_index = next(i for i, s in enumerate(stages) if s['id'] == current_stage['id'])
        if current_stage_index < len(stages) - 1:
            next_stage = stages[current_stage_index + 1]
            next_stage_substages = sorted(self.get_substages_for_stage(next_stage['id']), 
                                        key=lambda x: x['sub_stage_order'])
            if next_stage_substages:
                first_substage = next_stage_substages[0]
                first_substage_steps = sorted(self.get_steps_for_substage(first_substage['id']), 
                                            key=lambda x: x['step_order'])
                if first_substage_steps:
                    return first_substage_steps[0]

        return None

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