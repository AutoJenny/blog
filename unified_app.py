# unified_app.py
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import logging
from datetime import datetime
from config.unified_config import get_config
from config.database import db_manager

def create_app(config_name=None):
    app = Flask(__name__, 
                template_folder="templates", 
                static_folder="static")
    
    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    # Enable CORS for all routes
    CORS(app, origins=config_class.CORS_ORIGINS, supports_credentials=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config_class.LOG_LEVEL),
        format=config_class.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(config_class.LOG_FILE)
        ]
    )
    
    # Register blueprints
    from blueprints.core import bp as core_bp
    app.register_blueprint(core_bp)
    
    # Register modular launchpad blueprints
    from blueprints.launchpad_core import bp as launchpad_core_bp
    app.register_blueprint(launchpad_core_bp, url_prefix='/launchpad')
    
    from blueprints.launchpad_queue import bp as launchpad_queue_bp
    app.register_blueprint(launchpad_queue_bp, url_prefix='/launchpad')
    
    from blueprints.launchpad_scheduling import bp as launchpad_scheduling_bp
    app.register_blueprint(launchpad_scheduling_bp, url_prefix='/launchpad')
    
    from blueprints.launchpad_content import bp as launchpad_content_bp
    app.register_blueprint(launchpad_content_bp, url_prefix='/launchpad')
    
    from blueprints.launchpad_syndication import bp as launchpad_syndication_bp
    app.register_blueprint(launchpad_syndication_bp, url_prefix='/launchpad')
    
    from blueprints.llm_actions import bp as llm_actions_bp
    app.register_blueprint(llm_actions_bp, url_prefix='/llm-actions')
    
    from blueprints.post_sections import bp as post_sections_bp
    app.register_blueprint(post_sections_bp, url_prefix='/post-sections')
    
    from blueprints.post_info import bp as post_info_bp
    app.register_blueprint(post_info_bp, url_prefix='/post-info')
    
    from blueprints.images import bp as images_bp
    app.register_blueprint(images_bp, url_prefix='/images')
    
    from blueprints.clan_api import bp as clan_api_bp
    app.register_blueprint(clan_api_bp, url_prefix='/clan-api')
    
    # Additional blueprints will be added in Phase 2
    from blueprints.database import bp as database_bp
    app.register_blueprint(database_bp)
    # from blueprints.settings import bp as settings_bp
    
    # app.register_blueprint(core_bp, url_prefix='/core')
    # app.register_blueprint(launchpad_bp, url_prefix='/launchpad')
    # app.register_blueprint(llm_actions_bp, url_prefix='/llm_actions')
    # app.register_blueprint(post_sections_bp, url_prefix='/post_sections')
    # app.register_blueprint(post_info_bp, url_prefix='/post_info')
    # app.register_blueprint(images_bp, url_prefix='/images')
    # app.register_blueprint(clan_api_bp, url_prefix='/clan_api')
    # app.register_blueprint(database_bp, url_prefix='/db')
    # app.register_blueprint(settings_bp, url_prefix='/settings')
    
    # Homepage route is now handled by the core blueprint
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy",
            "service": "unified_app",
            "timestamp": datetime.now().isoformat()
        })
        
    # Database test endpoint
    @app.route('/db/test')
    def db_test():
        try:
            # Test database connection
            with db_manager.get_cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
            
            return jsonify({
                "status": "success",
                "message": "Database connection successful",
                "test_result": result
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Database connection failed: {str(e)}"
            }), 500
    
    # Simple database endpoint
    @app.route('/db/simple')
    def db_simple():
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
                tables = cursor.fetchall()
                return jsonify({"tables": [t['table_name'] for t in tables], "count": len(tables)})
        except Exception as e:
            return jsonify({"error": str(e), "tables": []}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
