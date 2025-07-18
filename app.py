from flask import Flask, make_response, send_from_directory, jsonify, redirect, url_for
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from config import get_config
import redis
import psutil
import time

def create_app():
    # Load environment variables
    load_dotenv()

    # Initialize Flask app
    app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
    app.config.from_object(get_config())

    # Ensure logs directory exists
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configure logging
    handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10000,
        backupCount=3
    )
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application startup')

    # Register blueprints - SIMPLIFIED FOR BLOG-WORKFLOW
    # from app.main import bp as main_bp
    # app.register_blueprint(main_bp)
    # from app.blog import bp as blog_bp
    # app.register_blueprint(blog_bp, url_prefix='/blog')
    # from app.llm import bp as llm_bp
    # app.register_blueprint(llm_bp, url_prefix='/llm')
    
    # Initialize workflow module (includes workflow_bp and api_workflow_bp registration)
    from app.workflow import init_workflow
    init_workflow(app)

    @app.route('/health')
    def health_check():
        """Basic health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'timestamp': time.time()
        })

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                'favicon.ico', mimetype='image/vnd.microsoft.icon')

    @app.route('/apple-touch-icon.png')
    def apple_touch_icon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                'apple-touch-icon.png', mimetype='image/png')

    @app.route('/apple-touch-icon-precomposed.png')
    def apple_touch_icon_precomposed():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                'apple-touch-icon.png', mimetype='image/png')

    @app.route('/')
    def index():
        return redirect(url_for('blog.latest'))
    
    @app.route('/test-simple')
    def test_simple():
        """Simple test route to check if Flask is working."""
        return jsonify({'message': 'Flask is working', 'status': 'ok'})

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error(f'Page not found: {error}')
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {error}')
        return jsonify({'error': 'Internal server error'}), 500

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    app.run(host=os.getenv('HOST', '127.0.0.1'), port=port)