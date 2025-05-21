from flask import render_template, current_app, jsonify, redirect, url_for, request, session
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

@bp.route('/workflow/planning/', methods=['GET', 'POST'])
def workflow_planning():
    # Define the three main stages
    stages = [
        {'id': 1, 'name': 'planning', 'label': 'Planning'},
        {'id': 2, 'name': 'authoring', 'label': 'Authoring'},
        {'id': 3, 'name': 'publishing', 'label': 'Publishing'},
    ]
    # Define all nine substages, grouped by stage
    substages = [
        # Planning
        {'id': 1, 'stage_id': 1, 'name': 'idea', 'label': 'Idea', 'icon': 'fa-lightbulb', 'color': 'purple', 'url': '/workflow/planning/?step=0'},
        {'id': 2, 'stage_id': 1, 'name': 'research', 'label': 'Research', 'icon': 'fa-search', 'color': 'blue', 'url': '/workflow/planning/?step=1'},
        {'id': 3, 'stage_id': 1, 'name': 'structure', 'label': 'Structure', 'icon': 'fa-bars', 'color': 'yellow', 'url': '/workflow/planning/?step=2'},
        # Authoring
        {'id': 4, 'stage_id': 2, 'name': 'content', 'label': 'Content', 'icon': 'fa-pen-nib', 'color': 'indigo', 'url': '/workflow/authoring/?step=0'},
        {'id': 5, 'stage_id': 2, 'name': 'meta_info', 'label': 'Meta Info', 'icon': 'fa-info-circle', 'color': 'cyan', 'url': '/workflow/authoring/?step=1'},
        {'id': 6, 'stage_id': 2, 'name': 'images', 'label': 'Images', 'icon': 'fa-image', 'color': 'pink', 'url': '/workflow/authoring/?step=2'},
        # Publishing
        {'id': 7, 'stage_id': 3, 'name': 'preflight', 'label': 'Preflight', 'icon': 'fa-plane-departure', 'color': 'green', 'url': '/workflow/publishing/?step=0'},
        {'id': 8, 'stage_id': 3, 'name': 'launch', 'label': 'Launch', 'icon': 'fa-rocket', 'color': 'orange', 'url': '/workflow/publishing/?step=1'},
        {'id': 9, 'stage_id': 3, 'name': 'syndication', 'label': 'Syndication', 'icon': 'fa-share-nodes', 'color': 'teal', 'url': '/workflow/publishing/?step=2'},
    ]
    # Canonical sub-stages for Planning (for the card content)
    sub_stages = [
        {
            'name': 'idea',
            'label': 'Idea',
            'icon': 'fa-lightbulb',
            'color': 'purple',
            'description': 'Initial concept',
            'instructions': 'Describe the core idea for your post. What is it about? Why does it matter?',
            'required': True,
        },
        {
            'name': 'research',
            'label': 'Research',
            'icon': 'fa-search',
            'color': 'blue',
            'description': 'Research and fact-finding',
            'instructions': 'Add research notes, links, or files that support your idea.',
            'required': True,
        },
        {
            'name': 'structure',
            'label': 'Structure',
            'icon': 'fa-bars',
            'color': 'yellow',
            'description': 'Outline and structure',
            'instructions': 'Outline the main sections and flow of your post.',
            'required': True,
        },
    ]
    current_idx = int(request.args.get('step', 0))
    if request.method == 'POST':
        if 'next' in request.form and current_idx < len(sub_stages) - 1:
            current_idx += 1
        elif 'prev' in request.form and current_idx > 0:
            current_idx -= 1
        elif 'goto' in request.form:
            try:
                goto_idx = int(request.form['goto'])
                if 0 <= goto_idx < len(sub_stages):
                    current_idx = goto_idx
            except Exception:
                pass
        return redirect(url_for('main.workflow_planning', step=current_idx))
    current_substage = sub_stages[current_idx] if sub_stages else None
    # Find the global substage id for the current planning substage
    current_substage_id = next((s['id'] for s in substages if s['name'] == current_substage['name']), 1) if current_substage else 1
    return render_template('workflow/planning/index.html', sub_stages=sub_stages, current_substage=current_substage, current_idx=current_idx, total=len(sub_stages), stages=stages, substages=substages, current_substage_id=current_substage_id)

@bp.route('/workflow/authoring/')
def workflow_authoring():
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM workflow_stage_entity ORDER BY stage_order ASC;")
            stages = cur.fetchall()
            cur.execute("SELECT * FROM workflow_sub_stage_entity ORDER BY stage_id, sub_stage_order ASC;")
            substages = cur.fetchall()
            cur.execute("SELECT * FROM workflow_sub_stage_entity WHERE stage_id = (SELECT id FROM workflow_stage_entity WHERE name = 'authoring') ORDER BY sub_stage_order ASC;")
            sub_stages = cur.fetchall()
    current_substage = sub_stages[0]['id'] if sub_stages else None
    return render_template('workflow/authoring/index.html', stages=stages, substages=substages, sub_stages=sub_stages, current_stage='authoring', current_substage=current_substage)

@bp.route('/workflow/publishing/')
def workflow_publishing():
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM workflow_stage_entity ORDER BY stage_order ASC;")
            stages = cur.fetchall()
            cur.execute("SELECT * FROM workflow_sub_stage_entity ORDER BY stage_id, sub_stage_order ASC;")
            substages = cur.fetchall()
            cur.execute("SELECT * FROM workflow_sub_stage_entity WHERE stage_id = (SELECT id FROM workflow_stage_entity WHERE name = 'publishing') ORDER BY sub_stage_order ASC;")
            sub_stages = cur.fetchall()
    current_substage = sub_stages[0]['id'] if sub_stages else None
    return render_template('workflow/publishing/index.html', stages=stages, substages=substages, sub_stages=sub_stages, current_stage='publishing', current_substage=current_substage)
