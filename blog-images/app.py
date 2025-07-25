#!/usr/bin/env python3
"""
Blog Images - Image Generation and Management Application
"""

import os
from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()

def create_app():
    """Application factory for blog-images."""
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql://localhost/blog')
    app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for the images application."""
        return jsonify({
            'status': 'healthy',
            'service': 'blog-images',
            'version': '1.0.0'
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG']) 