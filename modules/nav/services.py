"""Navigation services for workflow module."""

def get_workflow_stages():
    """Get all workflow stages and their substages."""
    return {
        'planning': {
            'idea': ['basic_idea', 'provisional_title'],
            'research': ['concepts', 'facts'],
            'structure': ['outline', 'allocate_facts']
        },
        'writing': {
            'content': ['sections'],
            'meta_info': ['metadata'],
            'images': ['image_plan']
        },
        'publishing': {
            'preflight': ['review'],
            'launch': ['publish'],
            'syndication': ['syndicate']
        }
    }

def get_workflow_context(stage=None, substage=None, step=None):
    """Get workflow navigation context for templates."""
    stages = get_workflow_stages()
    
    context = {
        'stages': stages,
        'current_stage': stage,
        'current_substage': substage,
        'current_step': step,
        'steps': stages.get(stage, {}).get(substage, []) if stage and substage else []
    }
    
    return context 