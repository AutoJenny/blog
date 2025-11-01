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
    
    # Add response headers to prevent HTML caching
    @app.after_request
    def add_header(response):
        # Don't cache HTML pages
        if response.content_type and 'text/html' in response.content_type:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response
    
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
    
    # Register posts management blueprint (consolidated post listing and status management)
    from blueprints.posts import bp as posts_bp
    app.register_blueprint(posts_bp)
    
    # Register modular launchpad blueprints
    from blueprints.launchpad import bp as launchpad_bp
    app.register_blueprint(launchpad_bp, url_prefix='/launchpad')
    
    from blueprints.launchpad_content import bp as launchpad_content_bp
    app.register_blueprint(launchpad_content_bp, url_prefix='/launchpad')
    
    from blueprints.launchpad_scheduling import bp as launchpad_scheduling_bp
    app.register_blueprint(launchpad_scheduling_bp, url_prefix='/launchpad')
    
    from blueprints.launchpad.blog_post_syndication import bp as blog_post_syndication_bp
    app.register_blueprint(blog_post_syndication_bp, url_prefix='/launchpad')
    
    from blueprints.launchpad.instagram_carousel import bp as instagram_carousel_bp
    app.register_blueprint(instagram_carousel_bp, url_prefix='/launchpad')
    
    from blueprints.automation_core import bp as automation_bp
    app.register_blueprint(automation_bp)

    # Newsletter top-level blueprint
    from blueprints.newsletter import bp as newsletter_bp
    app.register_blueprint(newsletter_bp)
    
    from blueprints.llm_actions import bp as llm_actions_bp
    app.register_blueprint(llm_actions_bp, url_prefix='/llm-actions')
    
    from blueprints.post_sections import bp as post_sections_bp
    app.register_blueprint(post_sections_bp, url_prefix='/post-sections')
    
    from blueprints.post_info import bp as post_info_bp
    app.register_blueprint(post_info_bp, url_prefix='/post-info')
    
    from blueprints.images import bp as images_bp
    app.register_blueprint(images_bp, url_prefix='/images')
    
    # Register image generation module
    from modules.image_generation.api import bp as image_generation_bp
    app.register_blueprint(image_generation_bp, url_prefix='/authoring')
    
    # Register imaging blueprint
    from blueprints.imaging import bp as imaging_bp
    app.register_blueprint(imaging_bp)
    
    # Register new dedicated workflow blueprints
    from blueprints.planning import bp as planning_bp
    app.register_blueprint(planning_bp)
    
    # Register taxonomy API blueprints
    from blueprints.taxonomy_api import bp as taxonomy_api_bp
    app.register_blueprint(taxonomy_api_bp)
    
    from blueprints.planning_api_taxonomy import bp as planning_taxonomy_api_bp
    app.register_blueprint(planning_taxonomy_api_bp)
    
    from blueprints.authoring_api_photography import bp as authoring_photography_bp
    app.register_blueprint(authoring_photography_bp)
    
    # Register settings blueprint
    from blueprints.settings import bp as settings_bp
    app.register_blueprint(settings_bp, url_prefix='/settings')
    
    # TEMPORARY: Test route for Authoring template preview
    @app.route('/test-authoring/<int:post_id>')
    def test_authoring_preview(post_id):
        """Temporary route to preview the Authoring template"""
        try:
            with db_manager.get_cursor() as cursor:
                # Get post details
                cursor.execute("""
                    SELECT id, title, status, created_at, updated_at
                    FROM post 
                    WHERE id = %s
                """, (post_id,))
                post = cursor.fetchone()
                
                if not post:
                    return "Post not found", 404
                
                return render_template('authoring/sections/drafting.html', 
                                     post_id=post_id,
                                     post=post,
                                     page_title="Authoring Preview")
                
        except Exception as e:
            return f"Error: {e}", 500
    
    from blueprints.authoring import bp as authoring_bp
    app.register_blueprint(authoring_bp)
    
    # Register new authoring imaging blueprint
    from blueprints.authoring_api_imaging import bp as authoring_imaging_bp
    app.register_blueprint(authoring_imaging_bp, url_prefix='/authoring')

    # Register new authoring content blueprint
    from blueprints.authoring_api_content import bp as authoring_content_bp
    app.register_blueprint(authoring_content_bp, url_prefix='/authoring')

    # Register new micro-modules for authoring
    from blueprints.authoring_api_styles import bp as authoring_styles_bp
    app.register_blueprint(authoring_styles_bp, url_prefix='/authoring')

    from blueprints.authoring_api_concepts import bp as authoring_concepts_bp
    app.register_blueprint(authoring_concepts_bp, url_prefix='/authoring')

    from blueprints.authoring_api_prompts import bp as authoring_prompts_bp
    app.register_blueprint(authoring_prompts_bp, url_prefix='/authoring')

    from blueprints.authoring_api_sections import bp as authoring_sections_bp
    app.register_blueprint(authoring_sections_bp, url_prefix='/authoring')

    from blueprints.header import bp as header_bp
    app.register_blueprint(header_bp)

    from blueprints.ui_state import ui_state_bp
    app.register_blueprint(ui_state_bp)

    from blueprints.clan_api import bp as clan_api_bp
    app.register_blueprint(clan_api_bp, url_prefix='/clan-api')

    # Register side projects blueprint
    from blueprints.side_projects import bp as side_projects_bp
    app.register_blueprint(side_projects_bp)

    # Additional blueprints will be added in Phase 2
    from blueprints.database import bp as database_bp
    app.register_blueprint(database_bp)

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
                "test_result": result['test']
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
    
    # Test route for state manager
    @app.route('/test_state_manager.html')
    def test_state_manager():
        return app.send_static_file('test_state_manager.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
