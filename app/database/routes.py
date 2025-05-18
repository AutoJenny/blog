from flask import (
    render_template,
    flash,
    redirect,
    url_for,
    request,
    current_app,
)
import subprocess
import os
import json
from pathlib import Path
from app.database.__init__ import bp
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
    """Database management interface."""
    stats = {}
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM post) as post_count,
                        (SELECT COUNT(*) FROM image) as image_count,
                        (SELECT COUNT(*) FROM workflow_status) as workflow_count,
                        (SELECT COUNT(*) FROM llm_interaction) as llm_count
                """)
                stats = dict(cur.fetchone())
    except Exception as e:
        flash(f"Error fetching database stats: {str(e)}", "error")
    return render_template("db/index.html", stats=stats)

@bp.route("/restore")
def restore():
    """Database restore interface."""
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
    table_stats = []
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        schemaname, 
                        relname, 
                        n_live_tup as row_count,
                        pg_size_pretty(pg_total_relation_size(relid)) as total_size
                    FROM pg_stat_user_tables
                    ORDER BY n_live_tup DESC
                """)
                table_stats = cur.fetchall()
    except Exception as e:
        flash(f"Error fetching table statistics: {str(e)}", "error")
        table_stats = []
    return render_template("db/stats.html", table_stats=table_stats)

@bp.route("/logs")
def logs():
    """Database logs interface."""
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
    migrations = []
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        version_num,
                        description,
                        created_at
                    FROM alembic_version_log
                    ORDER BY created_at DESC
                """)
                migrations = cur.fetchall()
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
    result = []
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Get table names
                cur.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """)
                tables = [row['table_name'] for row in cur.fetchall()]
                for table in tables:
                    # Get columns
                    cur.execute(f"""
                        SELECT column_name, data_type
                        FROM information_schema.columns
                        WHERE table_name = %s AND table_schema = 'public'
                    """, (table,))
                    columns = [
                        {"name": col["column_name"], "type": col["data_type"]}
                        for col in cur.fetchall()
                    ]
                    # Get up to 20 rows
                    try:
                        cur.execute(f'SELECT * FROM "{table}" LIMIT 20')
                        row_dicts = cur.fetchall()
                    except Exception:
                        row_dicts = []
                    result.append({
                        "name": table,
                        "columns": columns,
                        "rows": row_dicts
                    })
    except Exception as e:
        flash(f"Error fetching tables: {str(e)}", "error")
    return {"tables": result}
