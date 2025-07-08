from flask import render_template, current_app, jsonify, redirect, url_for, request, session, send_from_directory, flash
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
from flask import Response
import requests
from app import db
from app.utils.decorators import deprecated_endpoint

# Load DATABASE_URL from assistant_config.env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assistant_config.env'))
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_conn():
    config = dotenv_values(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assistant_config.env'))
    db_url = config.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

@bp.route("/")
def index():
    """Homepage with workflow stages."""
    # Get the latest post
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.id, pd.idea_seed
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.status != 'deleted'
                ORDER BY p.updated_at DESC, p.id DESC
                LIMIT 1
            """)
            latest_post = cur.fetchone()
    
    return render_template("main/index.html", latest_post=latest_post)


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
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                health_status["components"]["database"] = {
                    "status": "healthy",
                    "type": "postgresql"
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
    providers = []
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM llm_provider ORDER BY id')
            providers = cur.fetchall()
    return render_template('main/llm_providers.html', providers=providers)

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
                SELECT id, name, prompt_json
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
                        'prompt_json': row[2],
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

@bp.route('/api/settings/field-mapping', methods=['GET'])
@deprecated_endpoint(message="This endpoint is deprecated. Use /api/workflow/fields/mappings instead.")
def api_get_field_mapping():
    """Deprecated field mapping endpoint."""
    return jsonify({'error': 'This endpoint is deprecated'}), 410

@bp.route('/api/settings/field-mapping', methods=['POST'])
@deprecated_endpoint(message="This endpoint is deprecated. Use /api/workflow/fields/mappings instead.")
def api_update_field_mapping():
    """Deprecated field mapping update endpoint."""
    return jsonify({'error': 'This endpoint is deprecated'}), 410

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
    return render_template('docs/live_field_mapping.html', mappings=mappings)

@bp.route('/api/v1/llm/providers/start', methods=['POST'])
def api_start_ollama():
    """Start Ollama LLM provider."""
    try:
        # Check if Ollama is already running
        import subprocess
        import socket
        
        # Try to connect to Ollama's default port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 11434))
        sock.close()
        
        if result == 0:
            return jsonify({'status': 'already_running', 'message': 'Ollama is already running'})
        
        # Try to start Ollama
        try:
            # Start Ollama in the background
            subprocess.Popen(['ollama', 'serve'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            # Wait a moment for it to start
            import time
            time.sleep(2)
            
            # Check if it started successfully
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 11434))
            sock.close()
            
            if result == 0:
                return jsonify({'status': 'started', 'message': 'Ollama started successfully'})
            else:
                return jsonify({'status': 'error', 'message': 'Failed to start Ollama - service not responding'}), 500
                
        except FileNotFoundError:
            return jsonify({'status': 'error', 'message': 'Ollama not found - please install Ollama first'}), 404
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Failed to start Ollama: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Unexpected error: {str(e)}'}), 500

@bp.route('/api/v1/llm/providers/<int:provider_id>/test', methods=['POST'])
@deprecated_endpoint(message="This endpoint is deprecated. Use /api/llm/providers/{provider_id}/test instead.")
def api_test_provider(provider_id):
    """Deprecated LLM provider test endpoint."""
    return jsonify({'error': 'This endpoint is deprecated'}), 410

@bp.route('/structure/')
def structure_stub():
    return render_template('main/structure_stub.html')
