from flask import (
    render_template,
    flash,
    redirect,
    url_for,
    request,
    current_app,
    jsonify,
    Blueprint
)
import subprocess
import os
import json
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv, dotenv_values
import logging
import sys

bp = Blueprint("db", __name__, url_prefix="/db")

# Load DATABASE_URL from assistant_config.env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assistant_config.env'))
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_conn():
    # Always reload assistant_config.env and ignore pre-existing env
    config = dotenv_values(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assistant_config.env'))
    db_url = config.get('DATABASE_URL')
    if not db_url or db_url.strip() == '':
        print("[ERROR] DATABASE_URL is not set or is empty! Please check your assistant_config.env or environment variables.")
        raise RuntimeError("DATABASE_URL is not set or is empty! Please check your assistant_config.env or environment variables.")
    print(f"[DEBUG] DATABASE_URL used: {db_url}")
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

@bp.route("/")
def index():
    """Database management interface."""
    logging.basicConfig(level=logging.DEBUG)
    stats = {}
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM post) as post_count,
                        (SELECT COUNT(*) FROM image) as image_count,
                        (SELECT COUNT(*) FROM workflow) as workflow_count,
                        (SELECT COUNT(*) FROM llm_interaction) as llm_count
                """)
                stats = dict(cur.fetchone())
    except Exception as e:
        logging.error(f"Error fetching database stats: {str(e)}")
        flash(f"Error fetching database stats: {str(e)}", "error")
    logging.debug(f"/db/ stats: {stats}")
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
    """Database tables interface."""
    logging.basicConfig(level=logging.DEBUG)
    tables = []
    groups = []
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Get table names
                cur.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """)
                table_names = [row['table_name'] for row in cur.fetchall()]
                logging.debug(f"[DEBUG] table_names: {table_names}")
                table_data = {}
                for table in table_names:
                    # Get columns
                    cur.execute(f"""
                        SELECT column_name, data_type
                        FROM information_schema.columns
                        WHERE table_name = %s
                        ORDER BY ordinal_position
                    """, (table,))
                    columns = [{'name': r['column_name'], 'type': r['data_type']} for r in cur.fetchall()]
                    # Get up to 20 rows
                    cur.execute(f'SELECT * FROM {table} LIMIT 20;')
                    rows = cur.fetchall()
                    table_data[table] = {'name': table, 'columns': columns, 'rows': rows}
                logging.debug(f"[DEBUG] table_data keys: {list(table_data.keys())}")
                # Flat list for compatibility
                tables = list(table_data.values())
                # Grouping logic
                group_defs = [
                    ("Image Related", ["image", "image_format", "image_setting", "image_style", "image_prompt_example"]),
                    ("LLM Related", ["llm_action", "llm_action_history", "llm_provider", "llm_model", "llm_interaction", "llm_prompt"]),
                    ("Blog/Post Related", ["post", "post_section", "post_development", "category", "tag", "post_tags", "post_categories", "post_workflow_stage", "post_workflow_sub_stage"]),
                    ("User/Workflow", ["user", "workflow", "workflow_stage_entity", "workflow_sub_stage_entity"]),
                ]
                grouped_tables = set()
                for group_name, table_list in group_defs:
                    group_tables = [table_data[t] for t in table_list if t in table_data]
                    if group_tables:
                        groups.append({"group": group_name, "tables": group_tables})
                        grouped_tables.update([t["name"] for t in group_tables])
                # Add any remaining tables to 'Other'
                other_tables = [table_data[t] for t in table_data if t not in grouped_tables]
                if other_tables:
                    groups.append({"group": "Other", "tables": other_tables})
                # Sort groups alphabetically by group name
                groups.sort(key=lambda g: g["group"].lower())
    except Exception as e:
        logging.error(f"Exception in /db/tables: {e}")
        flash(f"Error fetching tables: {str(e)}", "error")
        tables = []
        groups = []
    # Always return both for compatibility
    logging.debug(f"/db/tables response: tables={len(tables)}, groups={len(groups)}")
    if groups:
        return jsonify({"tables": tables, "groups": groups})
    else:
        return jsonify({"tables": tables})

@bp.route("/debug")
def db_debug():
    debug_info = {}
    debug_info['DATABASE_URL'] = DATABASE_URL
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """)
                table_names = [row['table_name'] for row in cur.fetchall()]
                debug_info['table_names'] = table_names
    except Exception as e:
        debug_info['error'] = str(e)
    return debug_info

@bp.route("/raw")
def db_raw():
    return render_template("db/raw.html")

@bp.route('/backup', methods=['POST'])
def backup():
    """Trigger a database backup and return the backup file path or error."""
    try:
        result = subprocess.run([sys.executable, 'scripts/db_backup.py'], capture_output=True, text=True)
        if result.returncode == 0:
            # Try to find the latest backup file
            from pathlib import Path
            backup_dir = Path('backups')
            backups = sorted(backup_dir.glob('blog_backup_*.sql'))
            latest = str(backups[-1]) if backups else None
            return jsonify({'success': True, 'backup': latest, 'stdout': result.stdout})
        else:
            return jsonify({'success': False, 'error': result.stderr or result.stdout}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route("/debug/routes")
def debug_db_routes():
    from flask import current_app, jsonify
    output = []
    for rule in current_app.url_map.iter_rules():
        if rule.rule.startswith("/db"):
            output.append({
                "endpoint": rule.endpoint,
                "rule": rule.rule,
                "methods": sorted([m for m in rule.methods if m not in ("HEAD", "OPTIONS")]),
            })
    return jsonify(sorted(output, key=lambda x: x["rule"])), 200
