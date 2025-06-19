"""Navigation services for workflow module."""

from flask import current_app
import os

def get_workflow_stages():
    """Get all workflow stages and their substages."""
    try:
        # Try to use shared services if available
        from app.services.shared import get_workflow_stages as get_shared_stages
        return get_shared_stages()
    except ImportError:
        return get_workflow_stages_fallback()

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
    try:
        # Try to use shared services if available
        from app.services.shared import get_all_posts as get_shared_posts
        return get_shared_posts()
    except ImportError:
        return get_all_posts_fallback()

def get_all_posts_fallback():
    """Return fallback posts data."""
    return [
        {'id': 1, 'title': 'Demo Post (Standalone Mode)'},
        {'id': 2, 'title': 'Second Post (Standalone Mode)'}
    ]

def validate_context(context):
    """Validate that all required context variables are present."""
    required = ['current_stage', 'current_substage', 'current_step', 'post_id']
    missing = [var for var in required if var not in context]
    if missing:
        raise ValueError(f"Missing required context variables: {missing}")

def get_workflow_context(stage=None, substage=None, step=None):
    """Get workflow context for the current stage/substage/step."""
    try:
        # Try to use shared services if available
        from app.services.shared import get_workflow_context as get_shared_context
        context = get_shared_context(stage, substage, step)
    except ImportError:
        # Fallback to standalone mode
        context = {
            'current_stage': stage or 'planning',
            'current_substage': substage or 'idea',
            'current_step': step or 'basic_idea',
            'stages': get_workflow_stages(),
            'all_posts': get_all_posts(),
            'post_id': 1  # Default post ID for standalone mode
        }
    
    try:
        validate_context(context)
    except ValueError as e:
        current_app.logger.warning(f"Invalid workflow context: {e}")
        # Add missing variables with defaults
        if 'current_stage' not in context:
            context['current_stage'] = 'planning'
        if 'current_substage' not in context:
            context['current_substage'] = 'idea'
        if 'current_step' not in context:
            context['current_step'] = 'basic_idea'
        if 'post_id' not in context:
            context['post_id'] = 1
    
    return context 