<<<<<<< Updated upstream
from flask import Flask, render_template, request
import psycopg2
=======
from flask import Flask, make_response, send_from_directory, jsonify, redirect, url_for, render_template
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from config import get_config
import redis
import psutil
import time
from app.workflow import workflow
>>>>>>> Stashed changes

app = Flask(__name__)

def get_db_conn():
    return psycopg2.connect("dbname=blog user=nickfiddes host=localhost port=5432 password=your_password")

def get_posts():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM post ORDER BY updated_at DESC")
    posts = [{"id": row[0], "title": row[1]} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return posts

def get_post(post_id):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM post WHERE id = %s", (post_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return {"id": row[0], "title": row[1]}
    return None

def get_post_development(post_id):
    conn = get_db_conn()
    cur = conn.cursor()
    # Get all column names except id and post_id
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'post_development' AND column_name NOT IN ('id', 'post_id') ORDER BY ordinal_position;")
    columns = [row[0] for row in cur.fetchall()]
    # Build dynamic SQL
    sql = f"SELECT {', '.join(columns)} FROM post_development WHERE post_id = %s"
    cur.execute(sql, (post_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return dict(zip(columns, row))
    return None

<<<<<<< Updated upstream
@app.route('/')
def llm_actions():
    post_id = request.args.get('post_id', default=22, type=int)
    post = get_post(post_id)
    if not post:
        post = get_post(22)  # fallback to post 22 if not found
    posts = get_posts()
    post_dev = get_post_development(post_id)
    return render_template('llm_actions.html', posts=posts, post=post, post_dev=post_dev)
=======
    @app.route('/test')
    def test():
        """Test route to verify basic functionality."""
        return render_template('nav/test.html')

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
        return jsonify({"status": "ok", "message": "Server is running"})

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
>>>>>>> Stashed changes

if __name__ == '__main__':
    app.run(debug=True, port=5000) 