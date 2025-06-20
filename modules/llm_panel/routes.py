from flask import render_template, request
from . import bp

@bp.route('/test')
def test():
    """Test route that returns just TEST text."""
    return "TEST"

@bp.route('/panels')
def panels():
    """Render the LLM panels."""
    post_id = request.args.get('post_id')
    substage = request.args.get('substage', 'idea')
    
    if not post_id:
        return "Post ID is required", 400
        
    # Example step configuration - this should come from your database
    step_config = {
        'inputs': {
            'basic_idea': {
                'db_field': 'basic_idea',
                'db_table': 'post_development'
            }
        },
        'outputs': {
            'refined_idea': {
                'db_field': 'refined_idea',
                'db_table': 'post_development'
            }
        },
        'settings': {
            'llm': {
                'model': 'mistral',
                'task_prompt': 'Refine the basic idea into a more detailed concept.',
                'parameters': {
                    'temperature': 0.7,
                    'max_tokens': 1000
                }
            }
        }
    }
        
    return render_template('panel.html', 
        step_config=step_config,
        substage=substage,
        post={'id': post_id}
    ) 