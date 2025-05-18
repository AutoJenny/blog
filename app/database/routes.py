from flask import (
    Blueprint,
    render_template,
    flash,
    redirect,
    url_for,
    request,
    current_app,
)
from app import db
from sqlalchemy import text, inspect
import subprocess
import os
import json
from pathlib import Path

bp = Blueprint("db", __name__, url_prefix="/db")


@bp.route("/")
def index():
    """Database management interface."""
    # Get database stats
    stats = {}
    try:
        result = db.session.execute(
            text(
                """
            SELECT 
                (SELECT COUNT(*) FROM post) as post_count,
                (SELECT COUNT(*) FROM image) as image_count,
                (SELECT COUNT(*) FROM workflow_status) as workflow_count,
                (SELECT COUNT(*) FROM llm_interaction) as llm_count
        """
            )
        )
        stats = dict(result.fetchone())
    except Exception as e:
        flash(f"Error fetching database stats: {str(e)}", "error")

    return render_template("db/index.html", stats=stats)


@bp.route("/restore")
def restore():
    """Database restore interface."""
    # Get list of available backups
    backup_dir = Path(
        current_app.config.get("BACKUP_DIR", os.path.expanduser("~/.blog_backups"))
    )
    backups = []
    if backup_dir.exists():
        backups = sorted(
            [f for f in backup_dir.glob("*.db.gz")],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )
    return render_template("db/restore.html", backups=backups)


@bp.route("/stats")
def stats():
    """Database statistics interface."""
    # Get detailed database stats
    try:
        result = db.session.execute(
            text(
                """
            SELECT 
                schemaname, 
                relname, 
                n_live_tup as row_count,
                pg_size_pretty(pg_total_relation_size(relid)) as total_size
            FROM pg_stat_user_tables
            ORDER BY n_live_tup DESC
        """
            )
        )
        table_stats = [dict(row) for row in result]
    except Exception as e:
        flash(f"Error fetching table statistics: {str(e)}", "error")
        table_stats = []

    return render_template("db/stats.html", table_stats=table_stats)


@bp.route("/logs")
def logs():
    """Database logs interface."""
    # Get recent database logs
    log_file = Path(current_app.instance_path) / "logs" / "db.log"
    recent_logs = []
    if log_file.exists():
        try:
            with open(log_file) as f:
                recent_logs = f.readlines()[-100:]  # Last 100 lines
        except Exception as e:
            flash(f"Error reading log file: {str(e)}", "error")

    return render_template("db/logs.html", logs=recent_logs)


@bp.route("/migrations")
def migrations():
    """Database migrations interface."""
    # Get migration history
    try:
        result = db.session.execute(
            text(
                """
            SELECT 
                version_num,
                description,
                created_at
            FROM alembic_version_log
            ORDER BY created_at DESC
        """
            )
        )
        migrations = [dict(row) for row in result]
    except Exception as e:
        flash(f"Error fetching migration history: {str(e)}", "error")
        migrations = []

    return render_template("db/migrations.html", migrations=migrations)


@bp.route("/replication")
def replication():
    """Database replication interface."""
    status_file = Path(current_app.instance_path) / "replication_status.json"
    status = {}
    config = {"check_interval": 60}  # Default config

    if status_file.exists():
        try:
            with open(status_file) as f:
                status = json.load(f)
        except json.JSONDecodeError:
            flash("Error reading replication status", "error")

    config_file = Path(current_app.instance_path) / "replication_config.json"
    if config_file.exists():
        try:
            with open(config_file) as f:
                config = json.load(f)
        except json.JSONDecodeError:
            flash("Error reading replication configuration", "error")

    return render_template("db/replication.html", status=status, config=config)


@bp.route("/tables")
def list_tables():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names(schema="public")
    result = []
    for table in tables:
        columns = [
            {"name": col["name"], "type": str(col["type"])}
            for col in inspector.get_columns(table, schema="public")
        ]
        # Fetch up to 20 rows of data
        try:
            rows = db.session.execute(text(f'SELECT * FROM "{table}" LIMIT 20')).fetchall()
            row_dicts = [dict(row) for row in rows]
        except Exception as e:
            row_dicts = []
        result.append({
            "name": table,
            "columns": columns,
            "rows": row_dicts
        })
    return {"tables": result}
