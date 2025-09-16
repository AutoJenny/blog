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

from db import get_db_conn

@bp.route("/")
def index():
    """Database management interface."""
    logging.basicConfig(level=logging.DEBUG)
    stats = {}
    backup_files = []
    current_db_name = "unknown"
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Get current database name
                cur.execute("SELECT current_database();")
                result = cur.fetchone()
                current_db_name = result['current_database'] if result else "unknown"
                
                cur.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM post) as post_count,
                        (SELECT COUNT(*) FROM image) as image_count,
                        (SELECT COUNT(*) FROM workflow) as workflow_count,
                        (SELECT COUNT(*) FROM llm_interaction) as llm_count
                """)
                stats = dict(cur.fetchone())
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
    return render_template("db/index.html", stats=stats, backup_files=backup_files, current_db_name=current_db_name)

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
    # Pagination for post table
    post_page = int(request.args.get('post_page', 1))
    post_page_size = 20
    post_offset = (post_page - 1) * post_page_size
    total_post_count = 0
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
                    if table == 'post':
                        # Get total count for pagination
                        cur.execute('SELECT COUNT(*) FROM post;')
                        total_post_count = cur.fetchone()['count']
                        # Get paginated, ordered rows
                        cur.execute('SELECT * FROM post ORDER BY updated_at DESC NULLS LAST, id DESC LIMIT %s OFFSET %s;', (post_page_size, post_offset))
                        rows = cur.fetchall()
                        table_data[table] = {'name': table, 'columns': columns, 'rows': rows, 'total_count': total_post_count, 'page': post_page, 'page_size': post_page_size}
                    else:
                        cur.execute(f'SELECT * FROM {table} LIMIT 20;')
                        rows = cur.fetchall()
                        table_data[table] = {'name': table, 'columns': columns, 'rows': rows}
                logging.debug(f"[DEBUG] table_data keys: {list(table_data.keys())}")
                # Flat list for compatibility
                tables = list(table_data.values())
                # Grouping logic
                group_defs = [
                    ("Image Related", ["image", "image_format", "image_setting", "image_style", "image_prompt_example", "images", "image_processing_jobs", "image_processing_status", "image_processing_steps"]),
                    ("LLM Related", [
                        "llm_action", "llm_action_history", "llm_provider", "llm_model", "llm_interaction", "llm_prompt",
                        "llm_prompt_part", "post_workflow_step_action", "llm_config", "llm_format_template"
                    ]),
                    ("Blog/Post Related", ["post", "post_section", "post_development", "category", "tag", "post_tags", "post_categories", "post_workflow_stage", "post_workflow_sub_stage", "post_images", "post_section_elements"]),
                    ("User/Workflow", ["user", "workflow", "workflow_stage_entity", "workflow_sub_stage_entity", "workflow_steps", "workflow_step_entity", "workflow_step_input", "workflow_step_prompt", "workflow_format_template", "workflow_post_format", "workflow_field_mapping", "workflow_field_mappings", "workflow_table_preferences", "substage_action_default"]),
                    ("Social Media", ["social_media_platforms", "social_media_platform_specs", "social_media_content_processes", "social_media_process_configs", "social_media_process_executions"]),
                    ("Credentials & Services", ["credentials", "credential_services", "credential_channels", "credential_usage_history"]),
                    ("Clan System", ["clan_cache_metadata", "clan_categories", "clan_products"]),
                ]
                logging.debug(f"[DEBUG] group_defs: {group_defs}")
                logging.debug(f"[DEBUG] table_data keys: {list(table_data.keys())}")
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

@bp.route("/search")
def db_search():
    """Search across all database tables for a given term"""
    search_term = request.args.get('q', '').strip()
    if not search_term:
        return jsonify({"error": "No search term provided"}), 400
    
    results = []
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Get all tables
                cur.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """)
                table_names = [row['table_name'] for row in cur.fetchall()]
                
                # Search each table
                for table_name in table_names:
                    # Get columns for this table
                    cur.execute("""
                        SELECT column_name, data_type
                        FROM information_schema.columns
                        WHERE table_name = %s AND table_schema = 'public'
                    """, (table_name,))
                    columns = [{'name': r['column_name'], 'type': r['data_type']} for r in cur.fetchall()]
                    
                    # Build search query for text columns only
                    text_columns = [col['name'] for col in columns if 'text' in col['type'].lower() or 'varchar' in col['type'].lower() or 'char' in col['type'].lower()]
                    
                    if text_columns:
                        # Create WHERE clause for text columns
                        where_conditions = []
                        for col in text_columns:
                            where_conditions.append(f'"{col}" ILIKE %s')
                        
                        where_clause = " OR ".join(where_conditions)
                        search_pattern = f"%{search_term}%"
                        
                        # Execute search
                        cur.execute(f"""
                            SELECT * FROM "{table_name}" 
                            WHERE {where_clause}
                            LIMIT 50
                        """, [search_pattern] * len(text_columns))
                        
                        rows = cur.fetchall()
                        if rows:
                            results.append({
                                'table': table_name,
                                'columns': columns,
                                'rows': rows,
                                'count': len(rows)
                            })
                            
    except Exception as e:
        logging.error(f"Error in database search: {e}")
        return jsonify({"error": str(e)}), 500
    
    return jsonify({
        "search_term": search_term,
        "results": results,
        "total_tables_searched": len(table_names),
        "tables_with_matches": len(results)
    })

@bp.route("/debug")
def db_debug():
    debug_info = {}
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
            with conn.cursor() as cur:
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
