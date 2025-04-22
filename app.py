from flask import Flask, make_response, send_from_directory, jsonify
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
def hello():
    app.logger.info('Home page accessed')
    html_content = '''
    <!DOCTYPE html>
    <html>
        <head>
            <title>Test Page</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link rel="icon" type="image/x-icon" href="/favicon.ico">
            <link rel="apple-touch-icon" href="/apple-touch-icon.png">
        </head>
        <body>
            <h1>Test Page</h1>
            <p>This is a different test page served by Flask + Gunicorn</p>
        </body>
    </html>
    '''
    
    response = make_response(html_content)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['Content-Length'] = str(len(html_content))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Accept-Ranges'] = 'bytes'
    response.headers['Connection'] = 'keep-alive'
    
    return response

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f'Page not found: {error}')
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 3000))
    app.run(host=os.getenv('HOST', '127.0.0.1'), port=port)