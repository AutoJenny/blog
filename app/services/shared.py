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
    """Get all workflow stages and their substages from the database."""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Query workflow steps using the normalized schema with a single JOIN
                cur.execute("""
                    SELECT 
                        s.name as stage_name,
                        ss.name as substage_name,
                        ws.name as step_name
                    FROM workflow_stage_entity s
                    JOIN workflow_sub_stage_entity ss ON ss.stage_id = s.id
                    JOIN workflow_step_entity ws ON ws.sub_stage_id = ss.id
                    ORDER BY s.stage_order, ss.sub_stage_order, ws.step_order
                """)
                
                stages = {}
                for row in cur.fetchall():
                    stage, substage, step = row['stage_name'], row['substage_name'], row['step_name']
                    if stage not in stages:
                        stages[stage] = {}
                    if substage not in stages[stage]:
                        stages[stage][substage] = []
                    if step not in stages[stage][substage]:
                        stages[stage][substage].append(step)
                
                return stages
                
    except Exception as e:
        return get_workflow_stages_fallback()

def get_workflow_stages_fallback():
    """Return fallback workflow stages data if database is unavailable."""
    return {
        "Planning": {
            "Idea": ["Basic Idea", "Provisional Title"],
            "Research": ["Concepts", "Facts"],
            "Structure": ["Outline", "Allocate Facts"]
        },
        "Writing": {
            "Content": ["Sections"],
            "Meta Info": ["Meta Info"],
            "Images": ["Images"]
        },
        "Publishing": {
            "Preflight": ["Preflight"],
            "Launch": ["Launch"],
            "Syndication": ["Syndication"]
        }
    }

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