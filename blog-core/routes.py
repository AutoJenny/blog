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
import psycopg
from psycopg.rows import dict_row
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
    return psycopg.connect(db_url)

@bp.route("/")
def index():
    """Database management interface."""
    logging.basicConfig(level=logging.DEBUG)
    stats = {}
    backup_files = []
    try:
        with get_db_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM post) as post_count,
                        (SELECT COUNT(*) FROM image) as image_count,
                        (SELECT COUNT(*) FROM workflow) as workflow_count,
                        (SELECT COUNT(*) FROM llm_interaction) as llm_count
                """)
                stats = cur.fetchone()
        # Find all .sql backups in backups/
        backup_dir = Path("backups")
        backup_files = []
        if backup_dir.exists():
            backup_files += list(backup_dir.glob("blog_backup_*.sql"))
        # Remove duplicates, sort by mtime desc, use relative paths
        backup_files = sorted(set(backup_files), key=lambda x: x.stat().st_mtime, reverse=True)
        backup_files = [str(f.relative_to(Path("."))) for f in backup_files]
    except Exception as e:
        logging.error(f"Error fetching database stats or backup files: {str(e)}")
        flash(f"Error fetching database stats or backup files: {str(e)}", "error")
    logging.debug(f"/db/ stats: {stats}")
    return render_template("db/index.html", stats=stats, backup_files=backup_files)

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
            with conn.cursor(row_factory=dict_row) as cur:
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
            with conn.cursor(row_factory=dict_row) as cur:
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
    """Simple database tables interface - bypasses all migration issues."""
    try:
        import psycopg
        from psycopg.rows import dict_row
        
        # Direct connection - no migration issues
        conn = psycopg.connect('postgresql://autojenny@localhost:5432/blog')
        
        with conn.cursor(row_factory=dict_row) as cur:
            # Get all tables
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = cur.fetchall()
            
            # Get sample data from each table
            table_data = []
            for table in tables[:10]:  # Limit to first 10 tables for performance
                table_name = table['table_name']
                try:
                    cur.execute(f"SELECT * FROM {table_name} LIMIT 5")
                    sample_data = cur.fetchall()
                    table_data.append({
                        'name': table_name,
                        'sample_data': sample_data,
                        'row_count': len(sample_data)
                    })
                except Exception as e:
                    table_data.append({
                        'name': table_name,
                        'sample_data': [],
                        'row_count': 0,
                        'error': str(e)
                    })
        
        # Convert datetime objects to strings for JSON serialization
        from datetime import datetime, date, time
        
        def convert_datetime(obj):
            if isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            elif isinstance(obj, (datetime, date, time)):
                return obj.isoformat()
            else:
                return obj
        
        converted_data = convert_datetime(table_data)
        return jsonify({"tables": converted_data, "total_tables": len(tables)})
        
    except Exception as e:
        return jsonify({"error": str(e), "tables": []})

@bp.route("/debug")
def db_debug():
    """Simple debug endpoint - bypasses all migration issues."""
    try:
        import psycopg
        from psycopg.rows import dict_row
        conn = psycopg.connect('postgresql://autojenny@localhost:5432/blog')
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            table_names = [row['table_name'] for row in cur.fetchall()]
            return {"table_names": table_names, "count": len(table_names)}
    except Exception as e:
        return {"error": str(e)}

@bp.route("/raw")
def db_raw():
    return render_template("db/raw.html")

@bp.route("/simple")
def db_simple():
    """Completely new simple database interface - no dependencies."""
    try:
        import psycopg
        from psycopg.rows import dict_row
        conn = psycopg.connect('postgresql://autojenny@localhost:5432/blog')
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = cur.fetchall()
            return jsonify({"tables": [t['table_name'] for t in tables], "count": len(tables)})
    except Exception as e:
        return jsonify({"error": str(e), "tables": []})

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

@bp.route('/update-cell', methods=['POST'])
def update_cell():
    """Update a single cell in a database table."""
    try:
        data = request.get_json()
        table_name = data.get('table')
        row_id = data.get('row_id')
        column = data.get('column')
        value = data.get('value')
        
        if not all([table_name, row_id, column, value is not None]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Validate table name to prevent SQL injection
        with get_db_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Check if table exists
                cur.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE' AND table_name = %s
                """, (table_name,))
                if not cur.fetchone():
                    return jsonify({'error': f'Table {table_name} not found'}), 404
                
                # Check if column exists
                cur.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = %s AND column_name = %s
                """, (table_name, column))
                if not cur.fetchone():
                    return jsonify({'error': f'Column {column} not found in table {table_name}'}), 404
                
                # Update the cell
                cur.execute(f'UPDATE {table_name} SET {column} = %s WHERE id = %s', (value, row_id))
                
                if cur.rowcount == 0:
                    return jsonify({'error': f'Row with id {row_id} not found'}), 404
                
                conn.commit()
                return jsonify({'success': True, 'message': 'Cell updated successfully'})
                
    except Exception as e:
        logging.error(f"Error updating cell: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500

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
