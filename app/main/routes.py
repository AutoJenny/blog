from flask import render_template, current_app, jsonify, redirect, url_for, request, session, send_from_directory
from app.main import bp
from app.models import Post, Category
import psutil
import time
import sqlalchemy
from sqlalchemy import create_engine
import redis
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv, dotenv_values
import markdown

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
    post_id = request.args.get('post_id', type=int)
    if post_id:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM post WHERE id = %s", (post_id,))
                post = cur.fetchone()
    return render_template('workflow/planning/idea/index.html', post=post, **workflow_context('idea'))

@bp.route('/workflow/research/')
def workflow_research():
    return render_template('workflow/planning/research/index.html', **workflow_context('research'))

@bp.route('/workflow/structure/')
def workflow_structure():
    return render_template('workflow/planning/structure/index.html', **workflow_context('structure'))

@bp.route('/workflow/content/')
def workflow_content():
    return render_template('workflow/authoring/content/index.html', **workflow_context('content'))

@bp.route('/workflow/meta_info/')
def workflow_meta_info():
    return render_template('workflow/authoring/meta_info/index.html', **workflow_context('meta_info'))

@bp.route('/workflow/images/')
def workflow_images():
    return render_template('workflow/authoring/images/index.html', **workflow_context('images'))

@bp.route('/workflow/preflight/')
def workflow_preflight():
    return render_template('workflow/publishing/preflight/index.html', **workflow_context('preflight'))

@bp.route('/workflow/launch/')
def workflow_launch():
    return render_template('workflow/publishing/launch/index.html', **workflow_context('launch'))

@bp.route('/workflow/syndication/')
def workflow_syndication():
    return render_template('workflow/publishing/syndication/index.html', **workflow_context('syndication'))

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
