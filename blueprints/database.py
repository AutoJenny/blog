# blueprints/database.py
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from config.database import db_manager
import logging
import json
import os
from pathlib import Path
from datetime import datetime

bp = Blueprint('database', __name__, url_prefix='/db')
logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    """Database management interface."""
    stats = {}
    backup_files = []
    current_db_name = "blog"
    
    try:
        with db_manager.get_cursor() as cursor:
            # Get basic statistics
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM post) as post_count,
                    (SELECT COUNT(*) FROM image) as image_count,
                    (SELECT COUNT(*) FROM workflow) as workflow_count,
                    (SELECT COUNT(*) FROM llm_interaction) as llm_count
            """)
            stats = cursor.fetchone()
            
    except Exception as e:
        logger.error(f"Database error: {e}")
        stats = {"error": str(e)}
    
    # Find all .sql backups in backups/
    backup_dir = Path("backups")
    if backup_dir.exists():
        backup_files = list(backup_dir.glob("blog_backup_*.sql"))
        # Remove duplicates, sort by mtime desc, use relative paths
        backup_files = sorted(set(backup_files), key=lambda x: x.stat().st_mtime, reverse=True)
        backup_files = [str(f.relative_to(Path("."))) for f in backup_files]
    
    return render_template('database/index.html', 
                         stats=stats, 
                         backup_files=backup_files,
                         current_db_name=current_db_name)

@bp.route('/tables')
def list_tables():
    """List all database tables with full column info and sample data, grouped logically."""
    try:
        with db_manager.get_cursor() as cursor:
            # Get all tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            all_tables = [row['table_name'] for row in cursor.fetchall()]
            
            # Define table groups
            table_groups = {
                "Core Content": [
                    "post", "post_categories", "post_images", "post_performance", 
                    "post_section", "post_section_elements", "post_tags", 
                    "post_workflow_stage", "post_workflow_step_action", 
                    "post_workflow_sub_stage", "post_development", "daily_posts"
                ],
                "Image Management": [
                    "image", "image_format", "image_processing_jobs", 
                    "image_processing_status", "image_processing_steps", 
                    "image_prompt_example", "image_setting", "image_style", 
                    "images", "section_image_mappings"
                ],
                "Workflow System": [
                    "workflow", "workflow_stage_entity", "workflow_sub_stage_entity", 
                    "workflow_step_entity", "workflow_step_context_config", 
                    "workflow_step_input", "workflow_step_prompt", "workflow_steps", 
                    "workflow_field_mapping", "workflow_field_mappings", 
                    "workflow_format_template", "workflow_post_format", 
                    "workflow_stage_format", "workflow_step_format", 
                    "workflow_table_preferences"
                ],
                "LLM & AI": [
                    "llm_action", "llm_action_history", "llm_config", 
                    "llm_format_template", "llm_interaction", "llm_model", 
                    "llm_prompt", "llm_prompt_part", "llm_provider"
                ],
                "Platforms & Syndication": [
                    "platforms", "platform_capabilities", "platform_channel_support", 
                    "platform_credentials", "channel_types", "channel_requirements", 
                    "content_processes", "content_priorities", "syndication_progress", 
                    "posting_queue", "product_content_templates", "process_configurations"
                ],
                "Credentials & Security": [
                    "credentials", "active_credentials", "credential_channels", 
                    "credential_services", "credential_usage_history", "user"
                ],
                "Clan API Integration": [
                    "clan_cache_metadata", "clan_categories", "clan_products"
                ],
                "UI & Configuration": [
                    "ui_display_rules", "ui_menu_items", "ui_sections", 
                    "ui_session_state", "ui_user_preferences", "config_categories", 
                    "priority_factors", "substage_action_default"
                ],
                "Categories & Tags": [
                    "category", "tag", "requirement_categories"
                ],
                "Backup Tables": [
                    "post_development_backup_20250804_080448", 
                    "post_section_backup_20250109", 
                    "workflow_step_entity_backup"
                ]
            }
            
            # Process each group
            groups = []
            for group_name, table_names in table_groups.items():
                group_tables = []
                for table_name in table_names:
                    if table_name in all_tables:
                        try:
                            # Get column information
                            cursor.execute("""
                                SELECT column_name, data_type, is_nullable, column_default
                                FROM information_schema.columns
                                WHERE table_name = %s AND table_schema = 'public'
                                ORDER BY ordinal_position
                            """, (table_name,))
                            columns = cursor.fetchall()
                            
                            # Get sample data (limit to 5 rows)
                            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                            sample_data = cursor.fetchall()
                            
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
                            
                            converted_sample_data = convert_datetime(sample_data)
                            
                            group_tables.append({
                                "name": table_name,
                                "columns": [
                                    {
                                        "name": col["column_name"],
                                        "type": col["data_type"],
                                        "nullable": col["is_nullable"] == "YES",
                                        "default": col["column_default"]
                                    } for col in columns
                                ],
                                "rows": converted_sample_data,
                                "row_count": len(converted_sample_data)
                            })
                            
                        except Exception as e:
                            logger.warning(f"Error processing table {table_name}: {e}")
                            group_tables.append({
                                "name": table_name,
                                "columns": [],
                                "rows": [],
                                "row_count": 0,
                                "error": str(e)
                            })
                
                if group_tables:  # Only include groups that have tables
                    groups.append({
                        "group": group_name,
                        "tables": group_tables
                    })
            
            return jsonify({
                "groups": groups,
                "total_tables": len(all_tables),
                "total_groups": len(groups)
            })
            
    except Exception as e:
        logger.error(f"Error listing tables: {e}")
        return jsonify({"error": str(e), "groups": []}), 500

@bp.route('/tables/<table_name>')
def table_data(table_name):
    """Get data from a specific table."""
    try:
        with db_manager.get_cursor() as cursor:
            # Get table structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """, (table_name,))
            columns = cursor.fetchall()
            
            # Get sample data (limit to 100 rows)
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
            rows = cursor.fetchall()
            
            return jsonify({
                "table_name": table_name,
                "columns": columns,
                "rows": rows,
                "row_count": len(rows)
            })
    except Exception as e:
        logger.error(f"Error getting table data for {table_name}: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/search')
def search_database():
    """Search across all database tables."""
    try:
        search_term = request.args.get('q', '').strip()
        if not search_term:
            return jsonify({"error": "No search term provided"}), 400
        
        with db_manager.get_cursor() as cursor:
            # Get all tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row['table_name'] for row in cursor.fetchall()]
            
            results = []
            for table in tables:
                # Get text columns for this table
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public' 
                    AND data_type IN ('text', 'character varying', 'character')
                """, (table,))
                text_columns = [row['column_name'] for row in cursor.fetchall()]
                
                if text_columns:
                    # Search in text columns
                    where_clause = " OR ".join([f"{col} ILIKE %s" for col in text_columns])
                    search_pattern = f"%{search_term}%"
                    params = [search_pattern] * len(text_columns)
                    
                    cursor.execute(f"""
                        SELECT * FROM {table} 
                        WHERE {where_clause} 
                        LIMIT 10
                    """, params)
                    rows = cursor.fetchall()
                    
                    if rows:
                        results.append({
                            "table": table,
                            "rows": rows,
                            "count": len(rows)
                        })
            
            return jsonify({"results": results, "search_term": search_term})
            
    except Exception as e:
        logger.error(f"Error searching database: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/query', methods=['POST'])
def execute_query():
    """Execute a custom SQL query."""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "No query provided"}), 400
        
        # Basic safety check - only allow SELECT statements
        if not query.upper().startswith('SELECT'):
            return jsonify({"error": "Only SELECT queries are allowed"}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return jsonify({
                "query": query,
                "rows": rows,
                "row_count": len(rows)
            })
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/backup', methods=['POST'])
def create_backup():
    """Create a database backup."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"blog_database_backup_{timestamp}.sql"
        backup_path = os.path.join('backups', backup_filename)
        
        # Ensure backup directory exists
        os.makedirs('backups', exist_ok=True)
        
        # Create backup using pg_dump
        import subprocess
        result = subprocess.run([
            'pg_dump', 
            'postgresql://autojenny@localhost:5432/blog',
            '-f', backup_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({
                "status": "success", 
                "message": "Backup created successfully",
                "filename": backup_filename,
                "path": backup_path
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Backup failed",
                "error": result.stderr
            }), 500
            
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/health')
def health():
    """Health check endpoint."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        return jsonify({"status": "healthy", "service": "database", "test_result": result})
    except Exception as e:
        return jsonify({"status": "unhealthy", "service": "database", "error": str(e)}), 500