from flask import render_template, current_app, jsonify, redirect, url_for
from app.main import bp
from app.models import Post, Category
import psutil
import time
import sqlalchemy
from sqlalchemy import create_engine
import redis


@bp.route("/")
def index():
    """Home page with direct access to admin features."""
    # Get all posts without filtering
    posts = Post.query.order_by(Post.created_at.desc()).all()

    # Get all categories
    categories = Category.query.order_by(Category.name).all()

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
