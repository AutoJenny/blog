"""Navigation services for workflow module.
Handles navigation-specific logic while using shared services for data access.
"""

from app.services.shared import get_workflow_stages_from_db, get_all_posts_from_db

def validate_context(context):
    """Validate that all required context variables are present."""
    required = ['current_stage', 'current_substage', 'current_step', 'post_id']
    missing = [var for var in required if var not in context]
    if missing:
        raise ValueError(f"Missing required context variables: {missing}")

def get_workflow_context(stage=None, substage=None, step=None):
    """Get workflow context for the current stage/substage/step."""
    # Get all posts to find a default post_id
    all_posts = get_all_posts_from_db()
    default_post_id = all_posts[0]['id'] if all_posts else None
    
    # Get stages data from shared service
    stages = get_workflow_stages_from_db()
    
    # Return navigation-specific context
    return {
        'current_stage': stage or 'planning',
        'current_substage': substage or 'idea',
        'current_step': step or 'basic_idea',
        'stages': stages,
        'all_posts': all_posts,
        'post_id': default_post_id
    } 