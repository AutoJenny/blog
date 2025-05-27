from flask import render_template, current_app, jsonify, redirect, url_for, request, session, send_from_directory
from app.main import bp
import psutil
import time
import redis
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv, dotenv_values
import markdown
import re
from flask import abort
import subprocess
from flask import Blueprint
from app.database.routes import get_db_conn

# Load DATABASE_URL from assistant_config.env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assistant_config.env'))
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_conn():
    config = dotenv_values(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assistant_config.env'))
    db_url = config.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

@bp.route("/")
def index():
    # Only show published or in-process posts (not deleted/draft)
    posts = []
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM post
                    WHERE (published = TRUE OR status = 'in_process')
                    AND deleted = FALSE
                    ORDER BY created_at DESC
                """)
                posts = cur.fetchall()
    except Exception as e:
        posts = []
    return render_template("blog/index.html", posts=posts)


@bp.route("/health")
def health_check():
    """Basic health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": time.time(),
            "uptime": time.time() - psutil.boot_time(),
        }
    )


@bp.route("/health/detailed")
def detailed_health_check():
    """Detailed health check including all system components."""
    health_status = {"status": "healthy", "timestamp": time.time(), "components": {}}

    # Check database connection
    try:
        engine = create_engine(current_app.config["SQLALCHEMY_DATABASE_URI"])
        engine.connect()
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": engine.name,
        }
    except Exception as e:
        current_app.logger.error(f"Database health check failed: {e}")
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "degraded"

    # Check Redis connection if configured
    if current_app.config.get("REDIS_URL"):
        try:
            redis_client = redis.from_url(current_app.config["REDIS_URL"])
            redis_client.ping()
            health_status["components"]["redis"] = {"status": "healthy"}
        except Exception as e:
            current_app.logger.error(f"Redis health check failed: {e}")
            health_status["components"]["redis"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_status["status"] = "degraded"

    # System resources
    health_status["components"]["system"] = {
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage("/").percent,
    }

    return jsonify(health_status)


@bp.route("/dashboard")
def dashboard():
    return render_template("main/dashboard.html")


@bp.route('/modern')
def modern_index():
    return render_template('main/modern_index.html')

# --- Workflow Substage Routes ---
# Shared workflow context
WORKFLOW_STAGES = [
    {'id': 1, 'name': 'planning', 'label': 'Planning'},
    {'id': 2, 'name': 'authoring', 'label': 'Authoring'},
    {'id': 3, 'name': 'publishing', 'label': 'Publishing'},
]
WORKFLOW_SUBSTAGES = [
    # Planning
    {'id': 1, 'stage_id': 1, 'name': 'idea', 'label': 'Idea', 'icon': 'fa-lightbulb', 'color': 'purple', 'url': '/workflow/idea/'},
    {'id': 2, 'stage_id': 1, 'name': 'research', 'label': 'Research', 'icon': 'fa-search', 'color': 'blue', 'url': '/workflow/research/'},
    {'id': 3, 'stage_id': 1, 'name': 'structure', 'label': 'Structure', 'icon': 'fa-bars', 'color': 'yellow', 'url': '/workflow/structure/'},
    # Authoring
    {'id': 4, 'stage_id': 2, 'name': 'content', 'label': 'Content', 'icon': 'fa-pen-nib', 'color': 'indigo', 'url': '/workflow/content/'},
    {'id': 5, 'stage_id': 2, 'name': 'meta_info', 'label': 'Meta Info', 'icon': 'fa-info-circle', 'color': 'cyan', 'url': '/workflow/meta_info/'},
    {'id': 6, 'stage_id': 2, 'name': 'images', 'label': 'Images', 'icon': 'fa-image', 'color': 'pink', 'url': '/workflow/images/'},
    # Publishing
    {'id': 7, 'stage_id': 3, 'name': 'preflight', 'label': 'Preflight', 'icon': 'fa-plane-departure', 'color': 'green', 'url': '/workflow/preflight/'},
    {'id': 8, 'stage_id': 3, 'name': 'launch', 'label': 'Launch', 'icon': 'fa-rocket', 'color': 'orange', 'url': '/workflow/launch/'},
    {'id': 9, 'stage_id': 3, 'name': 'syndication', 'label': 'Syndication', 'icon': 'fa-share-nodes', 'color': 'teal', 'url': '/workflow/syndication/'},
]

# Helper to get substage id by name
substage_id_by_name = {s['name']: s['id'] for s in WORKFLOW_SUBSTAGES}

def workflow_context(substage_name):
    return {
        'substages': WORKFLOW_SUBSTAGES,
        'stages': WORKFLOW_STAGES,
        'current_substage_id': substage_id_by_name.get(substage_name)
    }

@bp.route('/workflow/idea/')
def workflow_idea():
    post = None
    llm_actions = []
    post_development = None
    mapped_fields = []
    post_id = request.args.get('post_id', type=int)
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Get mapped fields for idea substage (id=1)
            cur.execute("SELECT field_name FROM workflow_field_mapping WHERE substage_id = 1 ORDER BY order_index;")
            mapped_fields = [row['field_name'].lower().replace(' ', '_') for row in cur.fetchall()]
            if post_id:
                cur.execute("SELECT * FROM post WHERE id = %s", (post_id,))
                post = cur.fetchone()
                cur.execute("SELECT * FROM post_development WHERE post_id = %s", (post_id,))
                post_development = cur.fetchone()
            cur.execute("SELECT * FROM llm_action ORDER BY id")
            llm_actions = cur.fetchall()
    return render_template('workflow/planning/idea/index.html', post=post, llm_actions=llm_actions, post_development=post_development, mapped_fields=mapped_fields, **workflow_context('idea'))

@bp.route('/workflow/research/')
def workflow_research():
    post = None
    post_development = None
    mapped_fields = []
    post_id = request.args.get('post_id', type=int)
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Get mapped fields for research substage (id=2)
            cur.execute("SELECT field_name FROM workflow_field_mapping WHERE substage_id = 2 ORDER BY order_index;")
            mapped_fields = [row['field_name'].lower().replace(' ', '_') for row in cur.fetchall()]
            if post_id:
                cur.execute("SELECT * FROM post WHERE id = %s", (post_id,))
                post = cur.fetchone()
                cur.execute("SELECT * FROM post_development WHERE post_id = %s", (post_id,))
                post_development = cur.fetchone()
    return render_template('workflow/planning/research/index.html', post=post, post_development=post_development, mapped_fields=mapped_fields, **workflow_context('research'))

@bp.route('/workflow/structure/')
def workflow_structure():
    post = None
    post_development = None
    mapped_fields = []
    post_id = request.args.get('post_id', type=int)
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Get mapped fields for structure substage (id=3)
            cur.execute("SELECT field_name FROM workflow_field_mapping WHERE substage_id = 3 ORDER BY order_index;")
            mapped_fields = [row['field_name'].lower().replace(' ', '_') for row in cur.fetchall()]
            if post_id:
                cur.execute("SELECT * FROM post WHERE id = %s", (post_id,))
                post = cur.fetchone()
                cur.execute("SELECT * FROM post_development WHERE post_id = %s", (post_id,))
                post_development = cur.fetchone()
    return render_template('workflow/planning/structure/index.html', post=post, post_development=post_development, mapped_fields=mapped_fields, **workflow_context('structure'))

@bp.route('/workflow/content/')
def workflow_content():
    post = None
    post_development = None
    mapped_fields = []
    post_id = request.args.get('post_id', type=int)
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Get mapped fields for content substage (id=4)
            cur.execute("SELECT field_name FROM workflow_field_mapping WHERE substage_id = 4 ORDER BY order_index;")
            mapped_fields = [row['field_name'].lower().replace(' ', '_') for row in cur.fetchall()]
            if post_id:
                cur.execute("SELECT * FROM post WHERE id = %s", (post_id,))
                post = cur.fetchone()
                cur.execute("SELECT * FROM post_development WHERE post_id = %s", (post_id,))
                post_development = cur.fetchone()
    return render_template('workflow/authoring/content/index.html', post=post, post_development=post_development, mapped_fields=mapped_fields, **workflow_context('content'))

@bp.route('/workflow/meta_info/')
def workflow_meta_info():
    post = None
    post_development = None
    mapped_fields = []
    post_id = request.args.get('post_id', type=int)
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Get mapped fields for meta_info substage (id=5)
            cur.execute("SELECT field_name FROM workflow_field_mapping WHERE substage_id = 5 ORDER BY order_index;")
            mapped_fields = [row['field_name'].lower().replace(' ', '_') for row in cur.fetchall()]
            if post_id:
                cur.execute("SELECT * FROM post WHERE id = %s", (post_id,))
                post = cur.fetchone()
                cur.execute("SELECT * FROM post_development WHERE post_id = %s", (post_id,))
                post_development = cur.fetchone()
    return render_template('workflow/authoring/meta_info/index.html', post=post, post_development=post_development, mapped_fields=mapped_fields, **workflow_context('meta_info'))

@bp.route('/workflow/images/')
def workflow_images():
    post = None
    post_development = None
    mapped_fields = []
    post_id = request.args.get('post_id', type=int)
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Get mapped fields for images substage (id=6)
            cur.execute("SELECT field_name FROM workflow_field_mapping WHERE substage_id = 6 ORDER BY order_index;")
            mapped_fields = [row['field_name'].lower().replace(' ', '_') for row in cur.fetchall()]
            if post_id:
                cur.execute("SELECT * FROM post WHERE id = %s", (post_id,))
                post = cur.fetchone()
                cur.execute("SELECT * FROM post_development WHERE post_id = %s", (post_id,))
                post_development = cur.fetchone()
    return render_template('workflow/authoring/images/index.html', post=post, post_development=post_development, mapped_fields=mapped_fields, **workflow_context('images'))

@bp.route('/workflow/preflight/')
def workflow_preflight():
    post = None
    post_development = None
    mapped_fields = []
    post_id = request.args.get('post_id', type=int)
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Get mapped fields for preflight substage (id=7)
            cur.execute("SELECT field_name FROM workflow_field_mapping WHERE substage_id = 7 ORDER BY order_index;")
            mapped_fields = [row['field_name'].lower().replace(' ', '_') for row in cur.fetchall()]
            if post_id:
                cur.execute("SELECT * FROM post WHERE id = %s", (post_id,))
                post = cur.fetchone()
                cur.execute("SELECT * FROM post_development WHERE post_id = %s", (post_id,))
                post_development = cur.fetchone()
    return render_template('workflow/publishing/preflight/index.html', post=post, post_development=post_development, mapped_fields=mapped_fields, **workflow_context('preflight'))

@bp.route('/workflow/launch/')
def workflow_launch():
    post = None
    post_development = None
    mapped_fields = []
    post_id = request.args.get('post_id', type=int)
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Get mapped fields for launch substage (id=8)
            cur.execute("SELECT field_name FROM workflow_field_mapping WHERE substage_id = 8 ORDER BY order_index;")
            mapped_fields = [row['field_name'].lower().replace(' ', '_') for row in cur.fetchall()]
            if post_id:
                cur.execute("SELECT * FROM post WHERE id = %s", (post_id,))
                post = cur.fetchone()
                cur.execute("SELECT * FROM post_development WHERE post_id = %s", (post_id,))
                post_development = cur.fetchone()
    return render_template('workflow/publishing/launch/index.html', post=post, post_development=post_development, mapped_fields=mapped_fields, **workflow_context('launch'))

@bp.route('/workflow/syndication/')
def workflow_syndication():
    post = None
    post_development = None
    mapped_fields = []
    post_id = request.args.get('post_id', type=int)
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Get mapped fields for syndication substage (id=9)
            cur.execute("SELECT field_name FROM workflow_field_mapping WHERE substage_id = 9 ORDER BY order_index;")
            mapped_fields = [row['field_name'].lower().replace(' ', '_') for row in cur.fetchall()]
            if post_id:
                cur.execute("SELECT * FROM post WHERE id = %s", (post_id,))
                post = cur.fetchone()
                cur.execute("SELECT * FROM post_development WHERE post_id = %s", (post_id,))
                post_development = cur.fetchone()
    return render_template('workflow/publishing/syndication/index.html', post=post, post_development=post_development, mapped_fields=mapped_fields, **workflow_context('syndication'))

@bp.route('/docs/', defaults={'req_path': ''})
@bp.route('/docs/<path:req_path>')
def docs(req_path):
    docs_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'docs')
    abs_path = os.path.join(docs_root, req_path)

    # If path is a file and ends with .md, render it
    if os.path.isfile(abs_path) and abs_path.endswith('.md'):
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        html = markdown.markdown(content, extensions=['fenced_code', 'tables'])
        # For navigation, show the tree from root
        tree = build_docs_tree(docs_root)
        rel_file = os.path.relpath(abs_path, docs_root)
        return render_template('main/docs_browser.html', tree=tree, file_html=html, file_path=rel_file)

    # If path is a directory, list its contents
    if os.path.isdir(abs_path):
        tree = build_docs_tree(docs_root)
        return render_template('main/docs_browser.html', tree=tree, file_html=None, file_path=None)

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

@bp.route('/docs/nav/')
def docs_nav():
    docs_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'docs')
    tree = build_docs_tree(docs_root)
    file_path = None
    return render_template('main/docs_nav.html', tree=tree, file_path=file_path)

@bp.route('/docs/view/<path:file_path>')
def docs_content(file_path):
    docs_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'docs')
    abs_path = os.path.join(docs_root, file_path)
    if not os.path.isfile(abs_path) or not abs_path.endswith('.md'):
        return "Not found", 404
    with open(abs_path, 'r', encoding='utf-8') as f:
        content = f.read()
    import markdown
    html = markdown.markdown(content, extensions=['fenced_code', 'tables'])
    # Post-process Mermaid code blocks
    def mermaid_replacer(match):
        code = match.group(1)
        return f'<div class="mermaid">{code}</div>'
    html = re.sub(r'<pre><code class="language-mermaid">([\s\S]*?)</code></pre>', mermaid_replacer, html)
    return render_template('main/docs_content.html', file_html=html, file_path=file_path)

@bp.route('/mermaid-standalone')
def mermaid_standalone():
    return render_template('main/mermaid_standalone.html')

@bp.route('/llm/')
def llm_dashboard():
    """LLM Admin Dashboard: main entry for all LLM management."""
    return render_template('main/llm_dashboard.html')

@bp.route('/llm/providers')
def llm_providers():
    return render_template('main/llm_providers.html')

@bp.route('/llm/models')
def llm_models():
    return render_template('llm/llm_models.html')

@bp.route('/llm/prompts')
def llm_prompts():
    # Fetch prompt data from the database
    prompts = []
    prompt_parts = []
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT id, name, prompt_text
                FROM llm_prompt
                ORDER BY ("order" IS NULL), "order", id
            ''')
            rows = cur.fetchall()
            for row in rows:
                if isinstance(row, dict):
                    prompts.append(row)
                else:
                    prompts.append({
                        'id': row[0],
                        'name': row[1],
                        'prompt_text': row[2],
                    })
            # Fetch prompt parts
            cur.execute('''
                SELECT id, name, type, content, tags, "order", created_at, updated_at, action_id
                FROM llm_prompt_part
                ORDER BY "order", id
            ''')
            part_rows = cur.fetchall()
            for row in part_rows:
                if isinstance(row, dict):
                    prompt_parts.append(row)
                else:
                    prompt_parts.append({
                        'id': row[0],
                        'name': row[1],
                        'type': row[2],
                        'content': row[3],
                        'tags': row[4],
                        'order': row[5],
                        'created_at': row[6],
                        'updated_at': row[7],
                        'action_id': row[8],
                    })
    return render_template('main/llm_prompts.html', prompts=prompts, prompt_parts=prompt_parts)

@bp.route('/llm/actions')
def llm_actions():
    actions = []
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT id, field_name, input_field, output_field, llm_model, prompt_template, prompt_template_id, max_tokens, temperature, "order"
                FROM llm_action
                ORDER BY "order", id
            ''')
            rows = cur.fetchall()
            for row in rows:
                if isinstance(row, dict):
                    actions.append(row)
                else:
                    actions.append({
                        'id': row[0],
                        'field_name': row[1],
                        'input_field': row[2],
                        'output_field': row[3],
                        'llm_model': row[4],
                        'prompt_template': row[5],
                        'prompt_template_id': row[6],
                        'max_tokens': row[7],
                        'temperature': row[8],
                        'order': row[9],
                    })
    return render_template('main/llm_actions.html', actions=actions)

@bp.route('/llm/logs')
def llm_logs():
    return render_template('main/llm_logs.html')

@bp.route('/llm/settings')
def llm_settings():
    return render_template('main/llm_settings.html')

@bp.route('/db/restore', methods=['POST'])
def db_restore():
    data = request.get_json() or {}
    file = data.get('file')
    # List of allowed backup files (root and backups/)
    allowed_files = [
        'blog_backup_20250523_082634.sql',
        'blog_backup_20250524_151434.sql',
        'blog_backup_20250522_190110.sql',
        'blog_backup_20250522_190041.sql',
        'blog_backup_20250521_141125_postrestore.sql',
        'blog_backup_20250518_184147.sql',
        'blog_backup_20250518_172746.sql',
        'blog_backup_20250518_172740.sql',
        'blog_backup_20250518_103247.sql',
        'blog_llm_prompt_action_current.sql',
    ]
    # Check root and backups/
    file_path = None
    if file in allowed_files and os.path.isfile(file):
        file_path = file
    elif file in allowed_files and os.path.isfile(os.path.join('backups', file)):
        file_path = os.path.join('backups', file)
    if not file_path:
        return jsonify({'error': 'Invalid or missing backup file'}), 400
    try:
        # Terminate all connections
        subprocess.run(["psql", "blog", "-c", "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'blog' AND pid <> pg_backend_pid();"], check=True)
        # Drop and recreate
        subprocess.run(["dropdb", "blog"], check=True)
        subprocess.run(["createdb", "blog"], check=True)
        # Restore
        with open(file_path, 'rb') as f:
            subprocess.run(["psql", "blog"], stdin=f, check=True)
        return jsonify({'restored': file})
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Restore failed: {e}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/settings')
def settings_panel():
    field_mappings = []
    stages = []
    substages = []
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT wfm.id, wfm.field_name, wfm.stage_id, wfm.substage_id, wfm.order_index
                FROM workflow_field_mapping wfm
                ORDER BY wfm.order_index ASC, wfm.field_name ASC
            ''')
            field_mappings = cur.fetchall()
            cur.execute('SELECT id, name FROM workflow_stage_entity ORDER BY stage_order')
            stages = cur.fetchall()
            cur.execute('SELECT id, stage_id, name FROM workflow_sub_stage_entity ORDER BY sub_stage_order')
            substages = cur.fetchall()
    return render_template('main/settings.html', field_mappings=field_mappings, stages=stages, substages=substages)

@bp.route('/api/settings/field-mapping', methods=['GET'])
def api_get_field_mapping():
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT wfm.id, wfm.field_name, wfm.stage_id, wfm.substage_id, wfm.order_index,
                       ws.name as stage_name, wss.name as substage_name
                FROM workflow_field_mapping wfm
                LEFT JOIN workflow_stage_entity ws ON wfm.stage_id = ws.id
                LEFT JOIN workflow_sub_stage_entity wss ON wfm.substage_id = wss.id
                ORDER BY wfm.order_index ASC, wfm.field_name ASC
            ''')
            mappings = cur.fetchall()
    return jsonify([dict(row) for row in mappings])

@bp.route('/api/settings/field-mapping', methods=['POST'])
def api_update_field_mapping():
    data = request.get_json()
    mapping_id = data.get('id')
    stage_id = data.get('stage_id')
    substage_id = data.get('substage_id')
    order_index = data.get('order_index')
    if not mapping_id or not stage_id or not substage_id:
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE workflow_field_mapping
                SET stage_id = %s, substage_id = %s, order_index = %s
                WHERE id = %s
            ''', (stage_id, substage_id, order_index, mapping_id))
            conn.commit()
    return jsonify({'status': 'success'})

@bp.route('/api/workflow/stages', methods=['GET'])
def api_get_workflow_stages():
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT id, name FROM workflow_stage_entity ORDER BY stage_order')
            stages = cur.fetchall()
            cur.execute('SELECT id, stage_id, name FROM workflow_sub_stage_entity ORDER BY sub_stage_order')
            substages = cur.fetchall()
    return jsonify({
        'stages': [dict(row) for row in stages],
        'substages': [dict(row) for row in substages]
    })

@bp.route('/docs/view/database/schema.md')
def docs_live_field_mapping():
    # Render the markdown content first
    docs_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'docs')
    schema_md_path = os.path.join(docs_root, 'database', 'schema.md')
    with open(schema_md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
    # Fetch the live mapping table
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT wfm.field_name, ws.name as stage_name, wss.name as substage_name, wfm.order_index
                FROM workflow_field_mapping wfm
                LEFT JOIN workflow_stage_entity ws ON wfm.stage_id = ws.id
                LEFT JOIN workflow_sub_stage_entity wss ON wfm.substage_id = wss.id
                ORDER BY wfm.order_index ASC, wfm.field_name ASC
            ''')
            mappings = cur.fetchall()
    return render_template('docs/live_field_mapping.html', file_html=html_content, mappings=mappings)

@bp.route('/api/v1/post_development/<int:post_id>/update_field', methods=['POST'])
def api_update_post_development_field(post_id):
    data = request.get_json()
    field = data.get('field')
    value = data.get('value')
    # Only allow updating fields that exist in post_development
    allowed_fields = [
        'basic_idea','provisional_title','idea_scope','topics_to_cover','interesting_facts','tartans_products','section_planning','section_headings','section_order','main_title','subtitle','intro_blurb','conclusion','basic_metadata','tags','categories','image_captions','seo_optimization','self_review','peer_review','final_check','scheduling','deployment','verification','feedback_collection','content_updates','version_control','platform_selection','content_adaptation','distribution','engagement_tracking','summary'
    ]
    if field not in allowed_fields:
        return jsonify({'status': 'error', 'message': 'Invalid field'}), 400
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"UPDATE post_development SET {field} = %s WHERE post_id = %s", (value, post_id))
                conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
