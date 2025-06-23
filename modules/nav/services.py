"""Navigation services for workflow module."""

# Import shared services from MAIN_HUB
try:
    from app.services.shared import get_all_posts_from_db
except ImportError as e:
    # If shared services are not available, this is a critical error
    raise ImportError(f"Shared services not available: {e}. This indicates a configuration problem.")

from app.database import get_db_conn

def get_workflow_stages():
    """Get all workflow stages from the database."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, description, stage_order 
                FROM workflow_stage_entity 
                ORDER BY stage_order
            """)
            return [dict(row) for row in cur.fetchall()]

def get_workflow_substages():
    """Get all workflow substages from the database."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, stage_id, name, description, sub_stage_order 
                FROM workflow_sub_stage_entity 
                ORDER BY stage_id, sub_stage_order
            """)
            return [dict(row) for row in cur.fetchall()]

def get_workflow_stages_fallback():
    """Return fallback workflow stages data."""
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

def get_all_posts():
    """Get all posts from the database for the post selector."""
    # Use shared service from MAIN_HUB
    return get_all_posts_from_db()

def validate_context(context):
    """Validate that all required context variables are present."""
    required = ['current_stage', 'current_substage', 'current_step', 'post_id']
    missing = [var for var in required if var not in context]
    if missing:
        raise ValueError(f"Missing required context variables: {missing}")

def get_workflow_context(stage=None, substage=None, step=None):
    """Get workflow context for the current stage/substage/step."""
    # Get all posts to find a default post_id
    all_posts = get_all_posts()
    default_post_id = all_posts[0]['id'] if all_posts else None
    
    # Get stages and substages data
    stages = get_workflow_stages()
    substages = get_workflow_substages()
    
    # Return context with default post_id and stages data
    return {
        'current_stage': stage or 'planning',
        'current_substage': substage or 'idea',
        'current_step': step or 'basic_idea',
        'stages': stages,
        'substages': substages,
        'all_posts': all_posts,
        'post_id': default_post_id
    } 