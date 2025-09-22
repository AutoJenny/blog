# blueprints/core.py
from flask import Blueprint, render_template, jsonify, request, redirect
import logging
import json
from config.database import db_manager

bp = Blueprint('core', __name__)
logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    """Main page with header and workflow navigation."""
    try:
        # Get the latest post ID for workflow links
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id
                FROM post p
                WHERE p.status != 'deleted'
                ORDER BY p.updated_at DESC, p.id DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            first_post_id = result['id'] if result else 1
            
            # Get stats for the dashboard
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM post WHERE status != 'deleted') as post_count,
                    (SELECT COUNT(*) FROM image) as image_count,
                    (SELECT COUNT(*) FROM workflow) as workflow_count,
                    (SELECT COUNT(*) FROM llm_interaction) as llm_count
            """)
            stats = cursor.fetchone()
            
    except Exception as e:
        logger.warning(f"Could not fetch data: {e}")
        first_post_id = 1
        stats = {'post_count': 0, 'image_count': 0, 'workflow_count': 0, 'llm_count': 0}
    
    return render_template('index.html', 
                         first_post_id=first_post_id,
                         post_count=stats['post_count'],
                         image_count=stats['image_count'],
                         workflow_count=stats['workflow_count'],
                         llm_count=stats['llm_count'],
                         blueprint_name='core')

@bp.route('/workflow/')
def workflow_redirect():
    """Redirect to default workflow page."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id
                FROM post p
                WHERE p.status != 'deleted'
                ORDER BY p.updated_at DESC, p.id DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            post_id = result['id'] if result else 1
    except Exception as e:
        logger.warning(f"Could not fetch latest post: {e}")
        post_id = 1
    
    return redirect(f'/workflow/posts/{post_id}/planning/idea/initial_concept')

@bp.route('/workflow/posts/<int:post_id>')
def workflow_post_redirect(post_id):
    """Redirect to default stage/substage/step for a post."""
    return redirect(f'/workflow/posts/{post_id}/planning/idea/initial_concept')

@bp.route('/workflow/posts/<int:post_id>/<stage>')
def workflow_stage_redirect(post_id, stage):
    """Redirect to default substage/step for a stage."""
    return redirect(f'/workflow/posts/{post_id}/{stage}/idea/initial_concept')

@bp.route('/workflow/posts/<int:post_id>/<stage>/<substage>')
def workflow_substage_redirect(post_id, stage, substage):
    """Redirect to default step for a substage."""
    # Redirect old meta_info URLs to post_info
    if substage == 'meta_info':
        return redirect(f'/workflow/posts/{post_id}/{stage}/post_info')
    
    # Get the first step for this substage
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT wse.name
                FROM workflow_step_entity wse
                JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                WHERE wst.name ILIKE %s AND wsse.name ILIKE %s
                ORDER BY wse.step_order ASC
                LIMIT 1
            """, (stage, substage))
            first_step_result = cursor.fetchone()
            if first_step_result:
                step = first_step_result['name'].lower().replace(' ', '_')
            else:
                step = 'initial_concept'  # fallback
    except Exception as e:
        logger.warning(f"Error getting first step: {e}")
        step = 'initial_concept'  # fallback
    
    return redirect(f'/workflow/posts/{post_id}/{stage}/{substage}/{step}')

@bp.route('/workflow/posts/<int:post_id>/<stage>/<substage>/<step>')
def workflow_main(post_id=None, stage=None, substage=None, step=None):
    """Main workflow page with navigation."""
    # Redirect old meta_info URLs to post_info
    if substage == 'meta_info':
        return redirect(f'/workflow/posts/{post_id}/{stage}/post_info/{step}')
    
    # Set defaults if not provided
    if not post_id:
        post_id = 1
    if not stage:
        stage = 'planning'
    if not substage:
        substage = 'idea'
    
    # Get step from URL path - default to first step in substage
    if not step:
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT wse.name
                    FROM workflow_step_entity wse
                    JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                    JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                    WHERE wst.name ILIKE %s AND wsse.name ILIKE %s
                    ORDER BY wse.step_order ASC
                    LIMIT 1
                """, (stage, substage))
                first_step_result = cursor.fetchone()
                if first_step_result:
                    step = first_step_result['name'].lower().replace(' ', '_')
                else:
                    step = 'initial_concept'  # fallback
        except Exception as e:
            logger.warning(f"Error getting first step: {e}")
            step = 'initial_concept'  # fallback
    
    # Validate step exists - if not, redirect to first valid step
    if step:
        try:
            with db_manager.get_cursor() as cursor:
                # Convert step name from URL format to database format
                db_step_name = step.replace('_', ' ').title()
                
                cursor.execute("""
                    SELECT wse.name
                    FROM workflow_step_entity wse
                    JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                    JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                    WHERE wst.name ILIKE %s AND wsse.name ILIKE %s
                    AND wse.name ILIKE %s
                """, (stage, substage, db_step_name))
                step_exists = cursor.fetchone()
                
                if not step_exists:
                    # Step doesn't exist, redirect to first valid step
                    cursor.execute("""
                        SELECT wse.name
                        FROM workflow_step_entity wse
                        JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                        JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                        WHERE wst.name ILIKE %s AND wsse.name ILIKE %s
                        ORDER BY wse.step_order ASC
                        LIMIT 1
                    """, (stage, substage))
                    first_step_result = cursor.fetchone()
                    if first_step_result:
                        valid_step = first_step_result['name'].lower().replace(' ', '_')
                        return redirect(f'/workflow/posts/{post_id}/{stage}/{substage}/{valid_step}')
                    else:
                        step = 'initial_concept'  # fallback
        except Exception as e:
            logger.warning(f"Error validating step: {e}")
            step = 'initial_concept'  # fallback
    
    # Get step_id and step configuration from database
    step_id = None
    step_name = None
    step_description = None
    step_config = None
    
    try:
        with db_manager.get_cursor() as cursor:
            # Convert URL format (lowercase with underscores) to DB format (title case with spaces)
            db_step_name = step.replace('_', ' ').title()
            
            cursor.execute("""
                SELECT wse.config, wse.name as step_name, wse.id as step_id, wse.description
                FROM workflow_step_entity wse
                JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                WHERE wst.name ILIKE %s AND wsse.name ILIKE %s
                AND wse.name ILIKE %s
            """, (stage, substage, db_step_name))
            result = cursor.fetchone()
            if result:
                step_id = result['step_id']
                step_name = result['step_name']
                step_description = result['description']
                
                # Parse step configuration
                if result['config']:
                    try:
                        if isinstance(result['config'], str):
                            step_config = json.loads(result['config'])
                        else:
                            step_config = result['config']
                    except json.JSONDecodeError:
                        step_config = {}
                else:
                    step_config = {}
            else:
                # If step not found, get the first step for this substage
                cursor.execute("""
                    SELECT wse.name, wse.id
                    FROM workflow_step_entity wse
                    JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                    JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                    WHERE wst.name ILIKE %s AND wsse.name ILIKE %s
                    ORDER BY wse.step_order ASC
                    LIMIT 1
                """, (stage, substage))
                first_step_result = cursor.fetchone()
                if first_step_result:
                    step = first_step_result['name'].lower().replace(' ', '_')
                    step_id = first_step_result['id']
                    step_name = first_step_result['name']
                    step_config = {}
                else:
                    step = 'initial_concept'
                    step_id = None
                    step_name = 'Initial Concept'
                    step_config = {}
    except Exception as e:
        logger.warning(f"Error getting step configuration: {e}")
        step_id = None
        step_name = step.replace('_', ' ').title()
        step_config = {}
    
    # Get all posts for navigation
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at
                FROM post p
                WHERE p.status != 'deleted'
                ORDER BY p.updated_at DESC, p.id DESC
            """)
            all_posts = cursor.fetchall()
    except Exception as e:
        logger.warning(f"Error getting posts: {e}")
        all_posts = []
    
    # Get workflow structure for navigation
    stages = {}
    try:
        with db_manager.get_cursor() as cursor:
            # Get all stages, substages, and steps
            cursor.execute("""
                SELECT 
                    wst.name as stage_name,
                    wsse.name as substage_name,
                    wse.name as step_name,
                    wse.step_order
                FROM workflow_stage_entity wst
                JOIN workflow_sub_stage_entity wsse ON wsse.stage_id = wst.id
                JOIN workflow_step_entity wse ON wse.sub_stage_id = wsse.id
                ORDER BY wst.name, wsse.name, wse.step_order
            """)
            workflow_data = cursor.fetchall()
            
            # Build the stages structure
            for row in workflow_data:
                stage_name = row['stage_name'].lower()
                substage_name = row['substage_name'].lower()
                step_name = row['step_name']
                
                if stage_name not in stages:
                    stages[stage_name] = {}
                if substage_name not in stages[stage_name]:
                    stages[stage_name][substage_name] = []
                
                stages[stage_name][substage_name].append(step_name)
                
    except Exception as e:
        logger.warning(f"Error getting workflow structure: {e}")
        # Provide fallback structure
        stages = {
            'planning': {
                'idea': ['Initial Concept', 'Research', 'Structure']
            },
            'writing': {
                'content': ['Sections', 'Post Info', 'Images']
            }
        }
    
    # Render the workflow template
    return render_template('workflow.html', 
                         post_id=post_id,
                         stage=stage,
                         substage=substage,
                         step=step,
                         step_id=step_id,
                         step_name=step_name,
                         step_description=step_description,
                         step_config=step_config,
                         all_posts=all_posts,
                         stages=stages)

@bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "core"})

@bp.route('/api/posts')
def api_posts():
    """API endpoint to get all posts."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                       pd.idea_seed
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.status != 'deleted'
                ORDER BY p.updated_at DESC, p.id DESC
            """)
            posts = cursor.fetchall()
        
        return jsonify({"posts": posts})
    except Exception as e:
        logger.error(f"Error fetching posts: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/llm-actions/content')
def llm_actions_content():
    """Proxy endpoint to fetch LLM-actions content with context."""
    try:
        # Get context parameters from request
        stage = request.args.get('stage', 'planning')
        substage = request.args.get('substage', 'idea')
        step = request.args.get('step', 'basic_idea')
        post_id = request.args.get('post_id', '1')
        
        # Get step_id from database
        step_id = None
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT wse.id
                    FROM workflow_step_entity wse
                    JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                    JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                    WHERE wst.name ILIKE %s AND wsse.name ILIKE %s
                    AND wse.name ILIKE %s
                """, (stage, substage, step.replace('_', ' ').title()))
                result = cursor.fetchone()
                if result:
                    step_id = result['id']
        except Exception as e:
            logger.warning(f"Could not get step_id: {e}")
        
        # For now, return a simple response
        # In the full implementation, this would proxy to the LLM actions service
        return jsonify({
            "stage": stage,
            "substage": substage,
            "step": step,
            "post_id": post_id,
            "step_id": step_id,
            "content": "LLM Actions content placeholder"
        })
    except Exception as e:
        logger.error(f"Error in llm_actions_content: {e}")
        return jsonify({"error": str(e)}), 500
