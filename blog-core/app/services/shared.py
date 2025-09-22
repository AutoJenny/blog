"""
Shared services layer providing uniform database access across the application.
This is the ONE place that should handle core data access patterns used by multiple modules.
"""

from db import get_db_conn
from psycopg.rows import dict_row

def get_all_posts_from_db():
    """Get all non-deleted posts from the database."""
    with get_db_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
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
            with conn.cursor(row_factory=dict_row) as cur:
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
                    # Use lowercase substage name to match URL format
                    substage_lower = substage.lower()
                    if substage_lower not in stages[stage]:
                        stages[stage][substage_lower] = []
                    if step not in stages[stage][substage_lower]:
                        stages[stage][substage_lower].append(step)
                
                return stages
                
    except Exception as e:
        return get_workflow_stages_fallback()

def get_workflow_stages_fallback():
    """Return fallback workflow stages data if database is unavailable."""
    return {
        "Planning": {
            "Idea": ["Initial Concept", "Provisional Title"],
            "Research": ["Interesting Facts", "Topics To Cover"],
            "Structure": ["Section Headings", "Section Order", "Allocate Facts"]
        },
        "Writing": {
            "Content": ["Ideas to include", "Author First Drafts", "FIX language"],
            "Meta": ["Main"],
            "Images": ["IMAGES section concept", "IMAGES section LLM prompt"]
        },
        "Publishing": {
            "Preflight": ["Final Check", "Peer Review", "SEO Optimization", "Self Review", "Tartans Products"],
            "Launch": ["Deployment", "Scheduling", "Verification"],
            "Syndication": ["Content Adaptation", "Content Distribution", "Content Updates", "Engagement Tracking", "Test New Step"]
        }
    }

def get_post_and_idea_seed(post_id):
    """Get a post and its idea seed."""
    with get_db_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
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
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT p.*, pd.idea_seed
                FROM post p
                LEFT JOIN post_development pd ON pd.post_id = p.id
                WHERE p.status != 'deleted'
                ORDER BY p.created_at DESC
            """)
            return [dict(row) for row in cur.fetchall()]

def get_workflow_field_mappings(stage_name=None, substage_name=None, step_name=None):
    """Get field mappings for the current workflow stage/substage/step."""
    try:
        with get_db_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Build the query based on provided parameters
                query = """
                    SELECT 
                        wfm.id,
                        wfm.field_name,
                        wfm.field_type,
                        wfm.table_name,
                        wfm.column_name,
                        wfm.display_name,
                        wfm.is_required,
                        wfm.default_value,
                        wfm.validation_rules,
                        wfm.order_index,
                        s.name as stage_name,
                        ss.name as substage_name,
                        ws.name as step_name
                    FROM workflow_field_mapping wfm
                    LEFT JOIN workflow_stage_entity s ON wfm.stage_id = s.id
                    LEFT JOIN workflow_sub_stage_entity ss ON wfm.substage_id = ss.id
                    LEFT JOIN workflow_step_entity ws ON wfm.workflow_step_id = ws.id
                    WHERE 1=1
                """
                params = []
                
                if stage_name:
                    query += " AND s.name = %s"
                    params.append(stage_name)
                
                if substage_name:
                    query += " AND ss.name = %s"
                    params.append(substage_name)
                
                if step_name:
                    query += " AND ws.name = %s"
                    params.append(step_name)
                
                query += " ORDER BY wfm.order_index, wfm.field_name"
                
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
                
    except Exception as e:
        print(f"Error getting workflow field mappings: {e}")
        return [] 