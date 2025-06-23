"""
Shared services layer providing uniform database access across the application.
This is the ONE place that should handle core data access patterns used by multiple modules.
"""

from app.database import get_db_conn

def get_all_posts_from_db():
    """Get all non-deleted posts from the database."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, title 
                FROM post 
                WHERE status != 'deleted'
                ORDER BY created_at DESC
            """)
            return [dict(row) for row in cur.fetchall()]

def get_workflow_stages_from_db():
    """Get the complete workflow structure from the database."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Get stages
            cur.execute("""
                SELECT id, name, description, stage_order 
                FROM workflow_stage_entity 
                ORDER BY stage_order
            """)
            stages = [dict(row) for row in cur.fetchall()]

            # Get substages
            cur.execute("""
                SELECT id, stage_id, name, description, sub_stage_order 
                FROM workflow_sub_stage_entity 
                ORDER BY stage_id, sub_stage_order
            """)
            substages = [dict(row) for row in cur.fetchall()]

            # Get steps
            cur.execute("""
                SELECT id, sub_stage_id, name, description, step_order 
                FROM workflow_step_entity 
                ORDER BY sub_stage_id, step_order
            """)
            steps = [dict(row) for row in cur.fetchall()]

            # Build the hierarchical structure
            workflow_structure = {}
            for stage in stages:
                stage_substages = [s for s in substages if s['stage_id'] == stage['id']]
                workflow_structure[stage['name']] = {}
                
                for substage in stage_substages:
                    substage_steps = [s['name'] for s in steps if s['sub_stage_id'] == substage['id']]
                    workflow_structure[stage['name']][substage['name']] = substage_steps

            return workflow_structure

def get_post_and_idea_seed(post_id):
    """Get a post and its idea seed."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.*, pd.idea_seed
                FROM post p
                LEFT JOIN post_development pd ON pd.post_id = p.id
                WHERE p.id = %s
            """, (post_id,))
            row = cur.fetchone()
            if row:
                return dict(row)
            return None

def get_all_posts():
    """Get all posts."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.*, pd.idea_seed
                FROM post p
                LEFT JOIN post_development pd ON pd.post_id = p.id
                WHERE p.status != 'deleted'
                ORDER BY p.created_at DESC
            """)
            return [dict(row) for row in cur.fetchall()] 