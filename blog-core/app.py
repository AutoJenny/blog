from flask import Flask, render_template, jsonify, request, redirect
from flask_cors import CORS
import requests
import os
import logging
from datetime import datetime
from datetime import datetime
import pytz
from humanize import naturaltime
from db import get_db_conn
import psycopg.rows

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('blog-core.log')
    ]
)

app = Flask(__name__, template_folder="templates", static_folder="static")

# Set secret key for sessions
app.secret_key = 'your-secret-key-here-change-in-production'

# Enable CORS for cross-origin requests from microservices
CORS(app, origins=["http://localhost:5002", "http://localhost:5005"], supports_credentials=True)

# Configuration for microservices (keeping for future use)
SERVICES = {}

@app.route('/')
def index():
    """Main page with header and workflow navigation."""
    from app.services.shared import get_all_posts_from_db
    all_posts = get_all_posts_from_db()
    first_post_id = all_posts[0]['id'] if all_posts else 1
    return render_template('index.html', first_post_id=first_post_id)

@app.route('/workflow/')
def workflow_redirect():
    """Redirect to default workflow page."""
    from app.services.shared import get_all_posts_from_db
    all_posts = get_all_posts_from_db()
    post_id = all_posts[0]['id'] if all_posts else 1
    return redirect(f'/workflow/posts/{post_id}/planning/idea/initial_concept')

@app.route('/workflow/posts/<int:post_id>')
def workflow_post_redirect(post_id):
    """Redirect to default stage/substage/step for a post."""
    return redirect(f'/workflow/posts/{post_id}/planning/idea/initial_concept')

@app.route('/workflow/posts/<int:post_id>/<stage>')
def workflow_stage_redirect(post_id, stage):
    """Redirect to default substage/step for a stage."""
    return redirect(f'/workflow/posts/{post_id}/{stage}/idea/initial_concept')

@app.route('/workflow/posts/<int:post_id>/<stage>/<substage>')
def workflow_substage_redirect(post_id, stage, substage):
    """Redirect to default step for a substage."""
    # Redirect old meta_info URLs to post_info
    if substage == 'meta_info':
        return redirect(f'/workflow/posts/{post_id}/{stage}/post_info')
    
    # Get the first step for this substage
    from db import get_db_conn
    import psycopg.rows
    
    try:
        with get_db_conn() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute("""
                    SELECT wse.name
                    FROM workflow_step_entity wse
                    JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                    JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                    WHERE wst.name ILIKE %s AND wsse.name ILIKE %s
                    ORDER BY wse.step_order ASC
                    LIMIT 1
                """, (stage, substage))
                first_step_result = cur.fetchone()
                if first_step_result:
                    step = first_step_result['name'].lower().replace(' ', '_')
                else:
                    step = 'initial_concept'  # fallback
    except Exception as e:
        print(f"Error getting first step: {e}")
        step = 'initial_concept'  # fallback
    
    return redirect(f'/workflow/posts/{post_id}/{stage}/{substage}/{step}')

@app.route('/workflow/posts/<int:post_id>/<stage>/<substage>/<step>')
def workflow_main(post_id=None, stage=None, substage=None, step=None):
    """Main workflow page with navigation."""
    # Redirect old meta_info URLs to post_info
    if substage == 'meta_info':
        return redirect(f'/workflow/posts/{post_id}/{stage}/post_info/{step}')
    
    # Get workflow context
    from modules.nav.services import get_workflow_context
    from app.services.shared import get_all_posts_from_db
    from db import get_db_conn
    import psycopg.rows
    import json
    
    all_posts = get_all_posts_from_db()
    
    # Set defaults if not provided
    if not post_id and all_posts:
        post_id = all_posts[0]['id']
    elif not post_id:
        post_id = 1
    
    if not stage:
        stage = 'planning'
    if not substage:
        substage = 'idea'
    
    # Get step from URL path - default to first step in substage
    # If no step specified, get the first step for this substage
    if not step:
        try:
            with get_db_conn() as conn:
                with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                    cur.execute("""
                        SELECT wse.name
                        FROM workflow_step_entity wse
                        JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                        JOIN workflow_stage_entity wst ON wse.stage_id = wst.id
                        WHERE wst.name ILIKE %s AND wsse.name ILIKE %s
                        ORDER BY wse.step_order ASC
                        LIMIT 1
                    """, (stage, substage))
                    first_step_result = cur.fetchone()
                    if first_step_result:
                        step = first_step_result['name'].lower().replace(' ', '_')
                    else:
                        step = 'initial_concept'  # fallback
        except Exception as e:
            print(f"Error getting first step: {e}")
            step = 'initial_concept'  # fallback
    
    # Get step_id and step configuration from database
    step_id = None
    step_name = None
    step_description = None
    step_config = None
    
    try:
        from db import get_db_conn
        import psycopg.rows
        
        with get_db_conn() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                # Convert URL format (lowercase with underscores) to DB format (title case with spaces)
                display_step = step.replace('_', ' ').title()
                
                # Get step configuration using ILIKE for case-insensitive match
                # Convert URL format (lowercase with underscores) to DB format (title case with spaces)
                db_step_name = step.replace('_', ' ').title()
                
                cur.execute("""
                    SELECT wse.config, wse.name as step_name, wse.id as step_id, wse.description
                    FROM workflow_step_entity wse
                    JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                    JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                    WHERE wst.name ILIKE %s AND wsse.name ILIKE %s
                    AND wse.name ILIKE %s
                """, (stage, substage, db_step_name))
                result = cur.fetchone()
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
                    cur.execute("""
                        SELECT wse.name, wse.id
                        FROM workflow_step_entity wse
                        JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                        JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                        WHERE wst.name ILIKE %s AND wsse.name ILIKE %s
                        ORDER BY wse.step_order ASC
                        LIMIT 1
                    """, (stage, substage))
                    first_step_result = cur.fetchone()
                    if first_step_result:
                        step = first_step_result['name'].lower().replace(' ', '_')
                        step_id = first_step_result['id']
                        step_name = first_step_result['name']
    except Exception as e:
        print(f"Error getting step configuration: {e}")
        step_id = None
        step_name = step.replace('_', ' ').title()
    
    # Get proper workflow context with stages data
    workflow_context = get_workflow_context(stage, substage, step)
    
    def get_step_template(step_config):
        """Determine the appropriate template based on step configuration."""
        if not step_config:
            return 'workflow.html'  # Default template
        
        script_config = step_config.get('script_config', {})
        script_type = script_config.get('type', 'llm_action')
        
        # Template mapping based on script type
        template_map = {
            'image_generation': 'workflow/steps/image_generation.html',  # New template for blog-images service
            'llm_action': 'workflow.html',  # Use default template for LLM actions
            'custom_script': 'workflow/steps/custom_script.html'
        }
        
        return template_map.get(script_type, 'workflow.html')
    
    # Select template based on step configuration
    template_name = get_step_template(step_config)
    
    # Merge with our specific context
    context = {
        'current_stage': stage,
        'current_substage': substage,
        'current_step': step,
        'step_id': step_id,
        'step_name': step_name,
        'step_description': step_description,
        'step_config': step_config,
        'all_posts': all_posts,
        'current_post_id': post_id,
        'stages': workflow_context.get('stages', {})
    }
    
    return render_template(template_name, **context)

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'blog-core'})

@app.route('/posts')
def posts_listing():
    """Posts listing page with full functionality."""
    import logging
    import psycopg.rows
    logger = logging.getLogger("blog_debug")
    posts = []
    substages = {}
    show_deleted = request.args.get('show_deleted', '0') == '1'
    debug = request.args.get('debug', '0') == '1'
    
    try:
        with get_db_conn() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                # Get all substages
                cur.execute("SELECT id, name FROM workflow_sub_stage_entity ORDER BY id;")
                substages = {row['id']: row['name'] for row in cur.fetchall()}
                
                # Get posts with substage_id and clan status, filter by deleted status
                if show_deleted:
                    logger.info("[DEBUG] posts_listing: fetching DELETED posts only")
                    cur.execute("""
                        SELECT id, title, status, created_at, updated_at, slug, substage_id
                        FROM post
                        WHERE status = 'deleted'
                        ORDER BY created_at DESC
                    """)
                else:
                    logger.info("[DEBUG] posts_listing: fetching NON-DELETED posts only")
                    cur.execute("""
                        SELECT id, title, status, created_at, updated_at, slug, substage_id
                        FROM post
                        WHERE status != 'deleted'
                        ORDER BY created_at DESC
                    """)
                posts = cur.fetchall()
                # Convert to regular dictionaries so we can modify them
                posts = [dict(post) for post in posts]
                
        logger.info(f"[DEBUG] posts_listing: fetched {len(posts)} posts, show_deleted={show_deleted}")
        for post in posts:
            # Use the status directly since we've unified everything
            post['display_status'] = post['status']
            
            logger.info(f"[DEBUG] post {post['id']}: status='{post['status']}', display_status='{post['display_status']}'")
    except Exception as e:
        logger.error(f"[DEBUG] posts_listing: exception {e}")
        posts = []
    
    # Format dates as 'ago' using humanize, with Europe/London timezone
    london = pytz.timezone('Europe/London')
    now = datetime.now(london)
    for post in posts:
        created = post['created_at']
        updated = post['updated_at']
        if created and created.tzinfo is None:
            created = london.localize(created)
        if updated and updated.tzinfo is None:
            updated = london.localize(updated)
        post['created_ago'] = naturaltime(now - created) if created else ''
        post['updated_ago'] = naturaltime(now - updated) if updated else ''
    
    if debug:
        return jsonify({"posts": posts, "substages": substages, "show_deleted": show_deleted})
    
    return render_template('posts_list.html', posts=posts, substages=substages, show_deleted=show_deleted)

@app.route('/posts/<int:post_id>')
def post_public(post_id):
    """Public-facing post preview."""
    # For now, redirect to a simple preview page
    # In the future, this could be enhanced to show the full post content
    try:
        with get_db_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT p.*, pd.idea_seed, pd.provisional_title, pd.intro_blurb
                    FROM post p
                    LEFT JOIN post_development pd ON p.id = pd.post_id
                    WHERE p.id = %s
                """, (post_id,))
                post = cur.fetchone()
                
                if not post:
                    return "Post not found", 404
                
                # Get post sections if they exist
                cur.execute("""
                    SELECT * FROM post_section 
                    WHERE post_id = %s 
                    ORDER BY section_order
                """, (post_id,))
                sections = cur.fetchall()
                
                return render_template('post_preview.html', post=post, sections=sections)
    except Exception as e:
        return f"Error loading post: {str(e)}", 500

@app.route('/api/workflow/posts/<int:post_id>/fields/status', methods=['POST'])
def update_post_status(post_id):
    """Update post status (for delete/restore functionality)."""
    try:
        data = request.get_json()
        status = data.get('value', 'draft')
        
        with get_db_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    UPDATE post SET status = %s, updated_at = NOW() 
                    WHERE id = %s
                """, (status, post_id))
                conn.commit()
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/docs/', defaults={'req_path': ''})
@app.route('/docs/<path:req_path>')
def docs(req_path):
    """Serve documentation files."""
    import markdown
    import re
    
    docs_root = os.path.join(os.path.dirname(__file__), 'docs')
    abs_path = os.path.join(docs_root, req_path)

    # If path is a file and ends with .md, render it
    if os.path.isfile(abs_path) and abs_path.endswith('.md'):
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        html = markdown.markdown(content, extensions=['fenced_code', 'tables'])
        # For navigation, show the tree from root
        tree = build_docs_tree(docs_root)
        rel_file = os.path.relpath(abs_path, docs_root)
        return render_template('docs_browser.html', tree=tree, file_html=html, file_path=rel_file)

    # If path is a directory, list its contents
    if os.path.isdir(abs_path):
        tree = build_docs_tree(docs_root)
        return render_template('docs_browser.html', tree=tree, file_html=None, file_path=None)

    # Not found
    return "Not found", 404

def build_docs_tree(root):
    """Recursively build a tree of .md files and directories for navigation."""
    tree = []
    for entry in sorted(os.listdir(root)):
        path = os.path.join(root, entry)
        if os.path.isdir(path):
            subtree = build_docs_tree(path)
            if subtree:
                tree.append({'type': 'dir', 'name': entry, 'children': subtree})
        elif entry.endswith('.md'):
            tree.append({'type': 'file', 'name': entry, 'path': os.path.relpath(path, root)})
    return tree

@app.route('/docs/nav/')
def docs_nav():
    """Serve docs navigation."""
    docs_root = os.path.join(os.path.dirname(__file__), 'docs')
    tree = build_docs_tree(docs_root)
    file_path = None
    return render_template('docs_nav.html', tree=tree, file_path=file_path)

@app.route('/docs/view/<path:file_path>')
def docs_content(file_path):
    """Serve individual docs content."""
    import markdown
    import re
    
    docs_root = os.path.join(os.path.dirname(__file__), 'docs')
    abs_path = os.path.join(docs_root, file_path)
    if not os.path.isfile(abs_path) or not abs_path.endswith('.md'):
        return "Not found", 404
    with open(abs_path, 'r', encoding='utf-8') as f:
        content = f.read()
    html = markdown.markdown(content, extensions=['fenced_code', 'tables'])
    # Post-process Mermaid code blocks
    def mermaid_replacer(match):
        code = match.group(1)
        return f'<div class="mermaid">{code}</div>'
    html = re.sub(r'<pre><code class="language-mermaid">([\s\S]*?)</code></pre>', mermaid_replacer, html)
    return render_template('docs_content.html', file_html=html, file_path=file_path)

# Import settings functionality
from settings import bp as settings_bp
app.register_blueprint(settings_bp)

# Import database functionality
from app.database.routes import bp as db_bp
app.register_blueprint(db_bp)

# Import workflow navigation functionality
from modules.nav import bp as nav_bp
app.register_blueprint(nav_bp, url_prefix='/workflow')

@app.route('/api/llm-actions/content')
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
            from db import get_db_conn
            import psycopg.rows
            
            with get_db_conn() as conn:
                with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                    # Convert URL format to DB format
                    display_step = step.replace('_', ' ').title()
                    
                    # Get step_id from database
                    # Convert URL format (lowercase with underscores) to DB format (title case with spaces)
                    db_step_name = step.replace('_', ' ').title()
                    
                    cur.execute("""
                        SELECT wse.id as step_id
                        FROM workflow_step_entity wse
                        JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                        JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                        WHERE wst.name ILIKE %s AND wsse.name ILIKE %s
                        AND wse.name ILIKE %s
                    """, (stage, substage, db_step_name))
                    result = cur.fetchone()
                    if result:
                        step_id = result['step_id']
        except Exception as e:
            print(f"Error getting step_id in proxy: {e}")
        
        # Build URL for LLM Actions service - use the full page
        llm_actions_url = f"http://localhost:5002/?stage={stage}&substage={substage}&step={step}&post_id={post_id}"
        if step_id:
            llm_actions_url += f"&step_id={step_id}"
        
        response = requests.get(llm_actions_url, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            return f"<div class='p-6 text-red-400'>LLM Actions service returned status {response.status_code}</div>", 500
    except requests.exceptions.RequestException as e:
        return f"<div class='p-6 text-red-400'>LLM Actions service unavailable: {str(e)}</div>", 503

@app.route('/api/llm-actions/execute/<int:action_id>', methods=['POST'])
def llm_actions_execute(action_id):
    """Proxy endpoint to execute LLM actions."""
    try:
        # Forward the request to LLM-actions service
        llm_actions_url = f"http://localhost:5002/api/llm/actions/{action_id}/execute"
        
        # Get the request data
        data = request.get_json()
        
        response = requests.post(llm_actions_url, json=data, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({'error': f'LLM Actions service returned status {response.status_code}'}), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'LLM Actions service unavailable: {str(e)}'}), 503

@app.route('/api/llm-actions/config')
def llm_actions_config():
    """Proxy endpoint to get LLM configuration."""
    try:
        response = requests.get("http://localhost:5002/api/llm/config", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({'error': f'LLM Actions service returned status {response.status_code}'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'LLM Actions service unavailable: {str(e)}'}), 503

@app.route('/api/llm-actions/actions')
def llm_actions_list():
    """Proxy endpoint to get available LLM actions."""
    try:
        response = requests.get("http://localhost:5002/api/llm/actions", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({'error': f'LLM Actions service returned status {response.status_code}'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'LLM Actions service unavailable: {str(e)}'}), 503

@app.route('/api/llm-actions/test', methods=['POST'])
def llm_actions_test():
    """Proxy endpoint to test LLM connection."""
    try:
        data = request.get_json()
        response = requests.post("http://localhost:5002/api/llm/test", json=data, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({'error': f'LLM Actions service returned status {response.status_code}'}), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'LLM Actions service unavailable: {str(e)}'}), 503

@app.route('/api/llm-actions/field-mappings')
def llm_actions_field_mappings():
    """Proxy endpoint to get field mappings."""
    try:
        # Get context parameters from request
        stage = request.args.get('stage', 'planning')
        substage = request.args.get('substage', 'idea')
        step = request.args.get('step', 'basic_idea')
        
        # Build URL with context parameters
        llm_actions_url = f"http://localhost:5002/api/workflow/field-mappings?stage={stage}&substage={substage}&step={step}"
        
        response = requests.get(llm_actions_url, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({'error': f'LLM Actions service returned status {response.status_code}'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'LLM Actions service unavailable: {str(e)}'}), 503

@app.route('/api/workflow/prompts/all', methods=['GET'])
def get_all_prompts():
    """Get all prompts from the llm_prompt table."""
    from db import get_db_conn
    import psycopg.rows
    
    with get_db_conn() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("""
                SELECT id, name, 
                       COALESCE(system_prompt, prompt_text) as prompt_text,
                       CASE 
                           WHEN system_prompt IS NOT NULL AND system_prompt != ''
                           THEN 'system' 
                           ELSE 'task' 
                       END as type
                FROM llm_prompt
                ORDER BY name
            """)
            prompts = cur.fetchall()
            
            return jsonify([dict(prompt) for prompt in prompts])

@app.route('/api/llm/system-prompts', methods=['GET'])
def get_system_prompts():
    """Get system prompts from the llm_prompt table."""
    from db import get_db_conn
    import psycopg.rows
    
    with get_db_conn() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("""
                SELECT id, name, description, prompt_text, system_prompt
                FROM llm_prompt
                WHERE system_prompt IS NOT NULL AND system_prompt != ''
                ORDER BY name
            """)
            prompts = cur.fetchall()
            
            return jsonify([dict(prompt) for prompt in prompts])

@app.route('/api/workflow/steps/<int:step_id>/prompts', methods=['GET'])
def get_step_prompts(step_id):
    """Get prompts for a specific step."""
    from db import get_db_conn
    import psycopg.rows
    
    with get_db_conn() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("""
                SELECT 
                    wsp.system_prompt_id,
                    wsp.task_prompt_id,
                    sys_prompt.name as system_prompt_name,
                    sys_prompt.system_prompt as system_prompt_content,
                    task_prompt.name as task_prompt_name,
                    task_prompt.prompt_text as task_prompt_content
                FROM workflow_step_prompt wsp
                LEFT JOIN llm_prompt sys_prompt ON wsp.system_prompt_id = sys_prompt.id
                LEFT JOIN llm_prompt task_prompt ON wsp.task_prompt_id = task_prompt.id
                WHERE wsp.step_id = %s
            """, (step_id,))
            result = cur.fetchone()
            
            if result:
                return jsonify({
                    'system_prompt_id': result['system_prompt_id'],
                    'system_prompt_name': result['system_prompt_name'],
                    'system_prompt_content': result['system_prompt_content'],
                    'task_prompt_id': result['task_prompt_id'],
                    'task_prompt_name': result['task_prompt_name'],
                    'task_prompt_content': result['task_prompt_content']
                })
            else:
                return jsonify({})

@app.route('/api/workflow/steps/<int:step_id>/prompts', methods=['POST'])
def save_step_prompts(step_id):
    """Save prompts for a specific step."""
    from db import get_db_conn
    from flask import request
    
    data = request.get_json()
    if not data or not all(key in data for key in ['system_prompt_id', 'task_prompt_id']):
        from flask import abort
        abort(400, "Missing required fields")
    
    with get_db_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            # Delete existing prompts for this step
            cur.execute("""
                DELETE FROM workflow_step_prompt
                WHERE step_id = %s
            """, (step_id,))
            
            # Insert new prompts
            cur.execute("""
                INSERT INTO workflow_step_prompt (step_id, system_prompt_id, task_prompt_id)
                VALUES (%s, %s, %s)
            """, (step_id, data['system_prompt_id'], data['task_prompt_id']))
            
            conn.commit()
            return jsonify({'status': 'success'})

@app.route('/api/workflow/posts/<int:post_id>/development', methods=['GET'])
def get_post_development(post_id):
    """Get all development fields for a post."""
    from db import get_db_conn
    import psycopg.rows
    
    with get_db_conn() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            # Get column names from post_development table
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'post_development' 
                AND column_name NOT IN ('id', 'post_id')
            """)
            columns = [row[0] for row in cur.fetchall()]
            
            # Get field values for the post
            if columns:
                column_list = ', '.join(columns)
                cur.execute(f"""
                    SELECT {column_list}
                    FROM post_development
                    WHERE post_id = %s
                """, (post_id,))
                row = cur.fetchone()
                if row:
                    return jsonify({col: row[col] for col in columns})
    return jsonify({})

@app.route('/api/workflow/fields/available', methods=['GET'])
def get_available_fields():
    """Get all available fields from post_development table."""
    from db import get_db_conn
    import psycopg.rows
    from flask import request
    
    step_id = request.args.get('step_id', type=int)
    substage_id = request.args.get('substage_id', type=int)
    stage_id = request.args.get('stage_id', type=int)
    
    with get_db_conn() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            # Get post_development fields
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'post_development'
                AND column_name NOT IN ('id', 'post_id', 'created_at', 'updated_at')
                ORDER BY ordinal_position
            """)
            dev_fields = [
                {
                    'field_name': row['column_name'],
                    'display_name': row['column_name'].replace('_', ' ').title(),
                    'db_table': 'post_development',
                    'db_field': row['column_name'],
                    'description': ''
                }
                for row in cur.fetchall()
            ]
            
            # For now, return post_development fields only
            # In the future, this could be expanded to include other tables based on step configuration
            return jsonify({
                'fields': dev_fields,
                'groups': []  # Empty groups for now
            })

@app.route('/api/workflow/execute-step', methods=['POST'])
def execute_step():
    """Centralized script execution endpoint."""
    try:
        data = request.get_json()
        step_id = data.get('step_id')
        post_id = data.get('post_id')
        
        # Handle both old format (context object) and new format (flat structure)
        if 'context' in data:
            context = data.get('context', {})
            # Merge top-level section_ids with context if they exist
            if 'section_ids' in data:
                context['section_ids'] = data.get('section_ids', [])
        else:
            # New format: section_ids and task_prompt are at the top level
            context = {
                'section_ids': data.get('section_ids', []),
                'task_prompt': data.get('task_prompt', ''),
                'inputs': data.get('inputs', {})
            }
        
        if not step_id:
            return jsonify({
                "success": False,
                "error": "step_id is required"
            }), 400
        
        if not post_id:
            return jsonify({
                "success": False,
                "error": "post_id is required"
            }), 400
        
        # Import and execute the script
        from app.workflow.scripts import execute_step_script
        result = execute_step_script(step_id, post_id, context)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Script execution failed"
        }), 500

@app.route('/api/services/status')
def services_status():
    """Check status of all microservices."""
    status = {}
    
    # Docs is now integrated directly
    status['docs'] = {
        'status': 'integrated',
        'url': 'http://localhost:5001/docs/'
    }
    
    # Settings is now integrated directly
    status['settings'] = {
        'status': 'integrated',
        'url': 'http://localhost:5001/settings/'
    }
    
    # Database is now integrated directly
    status['db'] = {
        'status': 'integrated',
        'url': 'http://localhost:5001/db/'
    }
    
    # Check other microservices
    for service_name, service_url in SERVICES.items():
        try:
            response = requests.get(f"{service_url}/health", timeout=3)
            status[service_name] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'url': service_url
            }
        except requests.RequestException:
            status[service_name] = {
                'status': 'unavailable',
                'url': service_url
            }
    return jsonify(status)

@app.route('/api/workflow/persist-step-settings', methods=['GET', 'POST'])
def persist_step_settings():
    """Get or persist workflow step settings (task prompt and system prompt) to database."""
    from db import get_db_conn
    import psycopg.rows
    import json
    import logging
    
    if request.method == 'GET':
        # Get step settings from workflow_step_prompt table
        step_id = request.args.get('step_id', type=int)
        if not step_id:
            return jsonify({'error': 'step_id required'}), 400
        
        try:
            with get_db_conn() as conn:
                with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                    cur.execute("""
                        SELECT task_prompt_id, system_prompt_id
                        FROM workflow_step_prompt
                        WHERE step_id = %s
                    """, (step_id,))
                    result = cur.fetchone()
                    
                    if result:
                        return jsonify({
                            'success': True,
                            'task_prompt_id': result['task_prompt_id'],
                            'system_prompt_id': result['system_prompt_id']
                        })
                    else:
                        return jsonify({
                            'success': True,
                            'task_prompt_id': None,
                            'system_prompt_id': None
                        })
                        
        except Exception as e:
            logging.error(f"Error getting step settings: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    elif request.method == 'POST':
        # Save step settings to workflow_step_prompt table
        data = request.get_json()
        step_id = data.get('step_id')
        task_prompt_id = data.get('task_prompt_id')
        system_prompt_id = data.get('system_prompt_id')
        
        if not step_id:
            return jsonify({'error': 'step_id required'}), 400
        
        try:
            with get_db_conn() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    # Check if entry exists for this step
                    cur.execute("SELECT id FROM workflow_step_prompt WHERE step_id = %s", (step_id,))
                    existing = cur.fetchone()
                    
                    if existing:
                        # Update existing entry
                        cur.execute("""
                            UPDATE workflow_step_prompt 
                            SET task_prompt_id = %s, system_prompt_id = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE step_id = %s
                        """, (task_prompt_id, system_prompt_id, step_id))
                    else:
                        # Insert new entry
                        cur.execute("""
                            INSERT INTO workflow_step_prompt (step_id, task_prompt_id, system_prompt_id)
                            VALUES (%s, %s, %s)
                        """, (step_id, task_prompt_id, system_prompt_id))
                    
                    conn.commit()
                    
                    return jsonify({
                        'success': True, 
                        'message': 'Settings saved successfully',
                        'step_id': step_id,
                        'task_prompt_id': task_prompt_id,
                        'system_prompt_id': system_prompt_id
                    })
                    
        except Exception as e:
            logging.error(f"Error saving step settings: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/workflow/optimize-images', methods=['POST'])
def optimize_images():
    """Run image optimization script for a specific post."""
    import subprocess
    import json
    
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        
        if not post_id:
            return jsonify({'error': 'post_id required'}), 400
        
        # Path to the image processing script
        script_path = "/Users/nickfiddes/Code/projects/blog/blog-images/scripts/process_images.py"
        
        # Check if script exists
        if not os.path.exists(script_path):
            return jsonify({'error': 'Image processing script not found'}), 500
        
        # Run the script with the specific post ID
        result = subprocess.run([
            'python3', script_path,
            '--post-id', str(post_id),
            '--base-path', '/Users/nickfiddes/Code/projects/blog/blog-images/static/content'
        ], capture_output=True, text=True, cwd=os.path.dirname(script_path))
        
        if result.returncode == 0:
            # Parse the output to get processed count
            output_lines = result.stdout.split('\n')
            processed_count = 0
            
            for line in output_lines:
                if 'Successfully processed:' in line:
                    try:
                        processed_count = int(line.split(':')[1].strip())
                    except:
                        processed_count = 0
                    break
            
            return jsonify({
                'success': True,
                'message': 'Image optimization completed successfully',
                'processed_count': processed_count,
                'output': result.stdout
            })
        else:
            return jsonify({
                'error': f'Script execution failed: {result.stderr}',
                'output': result.stdout
            }), 500
            
    except Exception as e:
        logging.error(f"Error running image optimization: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/workflow/posts/<int:post_id>/sections-panel')
def sections_panel(post_id):
    """Serve the sections panel HTML for embedding in iframes."""
    return render_template('sections_panel.html', post_id=post_id)

@app.route('/api/sections/<int:post_id>')
def proxy_sections(post_id):
    """Proxy endpoint to fetch sections from blog-post-sections microservice."""
    try:
        import requests
        response = requests.get(f'http://localhost:5003/api/sections/{post_id}', timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({'error': f'Failed to fetch sections: {response.status_code}'}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to connect to sections service: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/api/workflow/step-id')
def get_step_id():
    """Get step ID from stage, substage, and step names."""
    stage = request.args.get('stage')
    substage = request.args.get('substage')
    step = request.args.get('step')
    
    if not all([stage, substage, step]):
        return jsonify({'error': 'Missing required parameters: stage, substage, step'}), 400
    
    try:
        with get_db_conn() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                # Convert URL format (lowercase with underscores) to DB format (title case with spaces)
                db_step_name = step.replace('_', ' ').title()
                
                # Debug logging
                print(f"Looking for: stage='{stage}', substage='{substage}', step='{db_step_name}'")
                
                cur.execute("""
                    SELECT wse.id
                    FROM workflow_step_entity wse
                    JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                    JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                    WHERE wst.name ILIKE %s 
                      AND wsse.name ILIKE %s 
                      AND wse.name ILIKE %s
                """, (stage, substage, db_step_name))
                
                result = cur.fetchone()
                if result:
                    return jsonify({'step_id': result['id']})
                else:
                    return jsonify({'error': f'Step not found for: stage={stage}, substage={substage}, step={db_step_name}'}), 404
    except Exception as e:
        print(f"Database error in get_step_id: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/ollama/start', methods=['POST'])
def start_ollama():
    """Start the Ollama server if not already running."""
    import socket
    import subprocess
    import time
    
    # Check if Ollama is already running on localhost:11434
    def is_ollama_running():
        try:
            with socket.create_connection(("localhost", 11434), timeout=2):
                return True
        except Exception:
            return False
    
    if is_ollama_running():
        return jsonify({"success": True, "message": "Ollama already running."})
    
    try:
        # Start Ollama in the background
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Wait briefly and check again
        time.sleep(2)
        if is_ollama_running():
            return jsonify({"success": True, "message": "Ollama started."})
        else:
            return jsonify({"success": False, "error": "Ollama did not start."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/llm/providers', methods=['GET'])
def get_llm_providers():
    """Get available LLM providers from database."""
    try:
        conn = get_db_conn()
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        cur.execute("SELECT id, name, type, api_url FROM llm_provider ORDER BY name")
        providers = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"providers": [dict(p) for p in providers]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/llm/models', methods=['GET'])
def get_llm_models():
    """Get available LLM models from database."""
    try:
        conn = get_db_conn()
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        cur.execute("""
            SELECT m.id, m.name, m.provider_id, p.name as provider_name 
            FROM llm_model m 
            JOIN llm_provider p ON m.provider_id = p.id 
            ORDER BY p.name, m.name
        """)
        models = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"models": [dict(m) for m in models]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/step/<int:step_id>/llm-settings', methods=['GET', 'PUT'])
def step_llm_settings(step_id):
    """Get or update LLM settings for a workflow step."""
    try:
        conn = get_db_conn()
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        
        if request.method == 'GET':
            cur.execute("SELECT config FROM workflow_step_entity WHERE id = %s", (step_id,))
            result = cur.fetchone()
            if result:
                config = result['config'] or {}
                llm_settings = config.get('settings', {}).get('llm', {})
                return jsonify({"llm_settings": llm_settings})
            return jsonify({"llm_settings": {}})
        
        elif request.method == 'PUT':
            new_settings = request.json.get('llm_settings', {})
            cur.execute("SELECT config FROM workflow_step_entity WHERE id = %s", (step_id,))
            result = cur.fetchone()
            if result:
                config = result['config'] or {}
                if 'settings' not in config:
                    config['settings'] = {}
                config['settings']['llm'] = new_settings
                cur.execute("UPDATE workflow_step_entity SET config = %s WHERE id = %s", 
                          (json.dumps(config), step_id))
                conn.commit()
                cur.close()
                conn.close()
                return jsonify({"success": True, "llm_settings": new_settings})
            return jsonify({"error": "Step not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Import and register blueprints
from modules.servers import bp as servers_bp
app.register_blueprint(servers_bp)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
