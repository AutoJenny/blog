from flask import render_template, current_app, jsonify, redirect, url_for
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
from dotenv import load_dotenv

# Load DATABASE_URL from assistant_config.env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assistant_config.env'))
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@bp.route("/")
def index():
    """Home page with direct access to admin features."""
    posts = []
    categories = []
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM post ORDER BY created_at DESC")
                posts = cur.fetchall()
                cur.execute("SELECT * FROM category ORDER BY name ASC")
                categories = cur.fetchall()
    except Exception as e:
        posts = []
        categories = []
    return render_template(
        "main/index.html",
        title="Home",
        posts=posts,
        categories=categories,
        show_admin=True,  # Always show admin features
    )


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
