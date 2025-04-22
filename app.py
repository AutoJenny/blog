from flask import Flask, make_response, send_from_directory, jsonify, redirect, url_for
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from config import get_config
import sqlalchemy
from sqlalchemy import create_engine
import redis
import psutil
import time

def create_app():
    # Load environment variables
    load_dotenv()

    # Initialize Flask app
    app = Flask(__name__)
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

    # Register blueprints
    from app.blog import bp as blog_bp
    app.register_blueprint(blog_bp, url_prefix='/blog')

    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy'}), 200

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
    port = int(os.getenv('PORT', 3000))
    app.run(host=os.getenv('HOST', '127.0.0.1'), port=port)